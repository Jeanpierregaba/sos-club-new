import { useNavigate, useRouter } from "@tanstack/react-router";
import { Bold, Eye, Heading2, Italic, List, PenLine, Send, Trash2, Undo2 } from "lucide-react";
import { useRef, useState, type ReactNode } from "react";

import { EtatContenu } from "@/components/articles/EtatContenu";
import { Photos } from "@/components/articles/Photos";
import { TexteArticle } from "@/components/articles/TexteArticle";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  creerArticle,
  ErreurApi,
  MESSAGE_INDISPONIBLE,
  modifierArticle,
  retirerArticle,
  soumettreArticle,
  supprimerArticle,
  type ArticleAuteur,
  type AxePublic,
  type ChampsArticle,
} from "@/lib/api/client";
import { LIMITES } from "@/lib/articles";
import { dateCourte } from "@/lib/dates";

const VIDE: ChampsArticle = { titre: "", chapo: "", texte: "", axe_code: "", afficher_club: true };

const MOTIFS = {
  corriger: "L'équipe te demande une correction",
  refuser: "Ton article n'a pas été retenu",
  depublier: "Ton article a été retiré du site",
} as const;

// L'éditeur d'un article (spec 023) : champs, barre d'outils Markdown, aperçu, puis enregistrer, soumettre,
// retirer de la file ou supprimer un brouillon. L'API garde la main : elle refuse ce que l'état ne permet pas.
export function Editeur({
  article,
  axes,
  eleve,
}: {
  article: ArticleAuteur | null;
  axes: AxePublic[];
  eleve: boolean;
}) {
  const navigate = useNavigate();
  const router = useRouter();
  const [champs, setChamps] = useState<ChampsArticle>(article?.champs ?? VIDE);
  const [actuel, setActuel] = useState(article);
  const [apercu, setApercu] = useState(false);
  const [erreur, setErreur] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);
  const [enCours, setEnCours] = useState(false);
  const texte = useRef<HTMLTextAreaElement>(null);

  const modifiable = actuel ? actuel.modifiable : true;
  const modifie = JSON.stringify(champs) !== JSON.stringify(actuel?.champs ?? VIDE);
  const changer = <K extends keyof ChampsArticle>(cle: K, valeur: ChampsArticle[K]) => {
    setChamps((c) => ({ ...c, [cle]: valeur }));
    setInfo(null);
  };

  async function agir(action: () => Promise<void>) {
    setErreur(null);
    setInfo(null);
    setEnCours(true);
    try {
      await action();
    } catch (e) {
      setErreur(e instanceof ErreurApi ? e.message : MESSAGE_INDISPONIBLE);
    } finally {
      setEnCours(false);
    }
  }

  async function enregistrer(): Promise<ArticleAuteur> {
    if (!actuel) {
      const cree = await creerArticle(champs);
      setActuel(cree);
      return cree;
    }
    if (!modifie && actuel.soumettable) return actuel;
    const enregistre = await modifierArticle(actuel.id, { ...champs, version: actuel.version });
    setActuel(enregistre);
    setChamps(enregistre.champs);
    return enregistre;
  }

  const sauver = () =>
    agir(async () => {
      const nouveau = !actuel;
      const enregistre = await enregistrer();
      if (nouveau)
        await navigate({ to: "/mes-articles/$id", params: { id: enregistre.id }, replace: true });
      else setInfo("Brouillon enregistré.");
    });

  const soumettre = () =>
    agir(async () => {
      const nouveau = !actuel;
      const enregistre = await enregistrer();
      const soumis = await soumettreArticle(enregistre.id, enregistre.version);
      if (nouveau) {
        await navigate({ to: "/mes-articles/$id", params: { id: soumis.id }, replace: true });
        return;
      }
      setActuel(soumis);
      setChamps(soumis.champs);
      setInfo(
        "Ton article est envoyé à l'équipe : tu recevras sa décision dans tes notifications.",
      );
    });

  const retirer = () =>
    agir(async () => {
      if (!actuel) return;
      const retire = await retirerArticle(actuel.id, actuel.version);
      setActuel(retire);
      setInfo("Ton article est retiré de la file : tu peux le modifier.");
    });

  const supprimer = () =>
    agir(async () => {
      if (!actuel || !window.confirm("Supprimer ce brouillon ? Il ne pourra pas être récupéré."))
        return;
      await supprimerArticle(actuel.id);
      await router.invalidate();
      await navigate({ to: "/mes-articles" });
    });

  // Insère une marque Markdown autour de la sélection, ou en début de ligne.
  function inserer(avant: string, apres = "", debutDeLigne = false) {
    const zone = texte.current;
    if (!zone) return;
    const { selectionStart: debut, selectionEnd: fin, value } = zone;
    const choisi = value.slice(debut, fin);
    const prefixe = debutDeLigne && debut > 0 && value[debut - 1] !== "\n" ? "\n" : "";
    const nouveau = `${value.slice(0, debut)}${prefixe}${avant}${choisi}${apres}${value.slice(fin)}`;
    changer("texte", nouveau.slice(0, LIMITES.texte));
    requestAnimationFrame(() => {
      zone.focus();
      const curseur = debut + prefixe.length + avant.length + choisi.length;
      zone.setSelectionRange(curseur, curseur);
    });
  }

  const decision = actuel?.derniere_decision;
  const motif =
    decision && decision.decision !== "approuver" && actuel && actuel.etat !== "en_attente"
      ? decision
      : null;

  return (
    <div className="space-y-6">
      {actuel && (
        <div className="flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
          <EtatContenu etat={actuel.etat} enLigne={actuel.en_ligne} />
          {actuel.publie_le && <span>Publié le {dateCourte(actuel.publie_le)}</span>}
          {actuel.en_ligne && actuel.adresse && (
            <a
              href={`/articles/${actuel.adresse}`}
              className="font-bold text-logo-blue underline-offset-4 hover:underline"
            >
              Voir la version en ligne
            </a>
          )}
        </div>
      )}

      {motif?.motif && (
        <Alert className="border-tangerine/40 bg-tangerine/10">
          <AlertDescription>
            <strong className="block text-ink">
              {MOTIFS[motif.decision as keyof typeof MOTIFS]}
            </strong>
            <span className="mt-1 block whitespace-pre-line">{motif.motif}</span>
          </AlertDescription>
        </Alert>
      )}
      {actuel?.etat === "en_attente" && (
        <Alert className="border-sun/50 bg-sun/15">
          <AlertDescription>
            L'équipe des Clubs Santé relit ton article. Pour le modifier, retire-le d'abord de la
            file.
          </AlertDescription>
        </Alert>
      )}
      {actuel?.en_ligne && modifiable && actuel.etat === "brouillon" && (
        <Alert>
          <AlertDescription>
            Ta nouvelle version reste invisible jusqu'à sa validation : la version publiée reste en
            ligne d'ici là.
          </AlertDescription>
        </Alert>
      )}

      {modifiable && !apercu ? (
        <div className="space-y-5 rounded-3xl bg-card p-5 shadow-card sm:p-7">
          <Bloc label="Titre" id="titre" compte={champs.titre.length} max={LIMITES.titre}>
            <Input
              id="titre"
              value={champs.titre}
              maxLength={LIMITES.titre}
              onChange={(e) => changer("titre", e.target.value)}
              placeholder="Ex. : Trois points d'eau dans notre cour"
              className="h-12 text-base"
            />
          </Bloc>
          <Bloc label="Chapô" id="chapo" compte={champs.chapo.length} max={LIMITES.chapo}>
            <Textarea
              id="chapo"
              value={champs.chapo}
              maxLength={LIMITES.chapo}
              rows={2}
              onChange={(e) => changer("chapo", e.target.value)}
              placeholder="En une ou deux phrases, ce que ton lecteur va découvrir."
            />
          </Bloc>
          <div className="space-y-2">
            <Label htmlFor="axe">Axe</Label>
            <select
              id="axe"
              value={champs.axe_code}
              onChange={(e) => changer("axe_code", e.target.value)}
              className="h-12 w-full rounded-md border bg-background px-3 text-base"
            >
              <option value="">Choisis l'axe de ton article</option>
              {axes.map((a) => (
                <option key={a.code} value={a.code}>
                  {a.libelle}
                </option>
              ))}
            </select>
          </div>
          <Bloc label="Texte" id="texte" compte={champs.texte.length} max={LIMITES.texte}>
            <div className="flex flex-wrap gap-1 rounded-t-md border border-b-0 bg-mist-soft p-1">
              <Outil titre="Intertitre" onClick={() => inserer("## ", "", true)}>
                <Heading2 className="size-4" />
              </Outil>
              <Outil titre="Gras" onClick={() => inserer("**", "**")}>
                <Bold className="size-4" />
              </Outil>
              <Outil titre="Italique" onClick={() => inserer("_", "_")}>
                <Italic className="size-4" />
              </Outil>
              <Outil titre="Liste" onClick={() => inserer("- ", "", true)}>
                <List className="size-4" />
              </Outil>
            </div>
            <Textarea
              id="texte"
              ref={texte}
              value={champs.texte}
              maxLength={LIMITES.texte}
              rows={14}
              onChange={(e) => changer("texte", e.target.value)}
              placeholder={
                "Raconte ton action ou explique ton sujet.\n\n## Un intertitre\n\nDu **gras**, de l'_italique_ et des listes :\n- un point\n- un autre"
              }
              className="rounded-t-none font-mono text-sm"
            />
          </Bloc>
          {eleve && (
            <label className="flex items-start gap-3 text-sm">
              <Checkbox
                checked={champs.afficher_club}
                onCheckedChange={(v) => changer("afficher_club", v === true)}
                className="mt-0.5"
              />
              <span>
                Afficher mon club avec mon pseudonyme
                <span className="block text-muted-foreground">
                  Ton nom n'apparaît jamais : seulement ton pseudonyme, et ton club si tu le
                  choisis.
                </span>
              </span>
            </label>
          )}
        </div>
      ) : (
        <article className="rounded-3xl bg-card p-5 shadow-card sm:p-8">
          <h2 className="font-display text-3xl leading-tight text-ink">
            {champs.titre || "Sans titre"}
          </h2>
          <p className="mt-3 text-lg font-semibold text-ink/75">{champs.chapo}</p>
          <TexteArticle texte={champs.texte} className="mt-6" />
        </article>
      )}

      <Photos article={actuel} modifiable={modifiable} onArticle={setActuel} />

      {erreur && (
        <Alert variant="destructive">
          <AlertDescription>{erreur}</AlertDescription>
        </Alert>
      )}
      {info && (
        <Alert className="border-leaf/40 bg-leaf/10">
          <AlertDescription>{info}</AlertDescription>
        </Alert>
      )}

      <div className="flex flex-wrap gap-3">
        {modifiable && (
          <>
            <Button
              variant="outline"
              className="h-11 rounded-full px-5 font-bold"
              onClick={() => setApercu((a) => !a)}
            >
              {apercu ? <PenLine className="size-4" /> : <Eye className="size-4" />}
              {apercu ? "Modifier" : "Aperçu"}
            </Button>
            <Button
              variant="outline"
              className="h-11 rounded-full px-5 font-bold"
              disabled={enCours || (!modifie && !!actuel)}
              onClick={sauver}
            >
              Enregistrer le brouillon
            </Button>
            <Button
              className="h-11 rounded-full px-6 font-bold"
              disabled={enCours || (!!actuel && !actuel.soumettable && !modifie)}
              onClick={soumettre}
            >
              <Send className="size-4" /> Soumettre à l'équipe
            </Button>
          </>
        )}
        {actuel?.etat === "en_attente" && (
          <Button
            variant="outline"
            className="h-11 rounded-full px-5 font-bold"
            disabled={enCours}
            onClick={retirer}
          >
            <Undo2 className="size-4" /> Retirer de la file
          </Button>
        )}
        {actuel?.supprimable && (
          <Button
            variant="ghost"
            className="h-11 rounded-full px-5 font-bold text-logo-red"
            disabled={enCours}
            onClick={supprimer}
          >
            <Trash2 className="size-4" /> Supprimer le brouillon
          </Button>
        )}
      </div>
    </div>
  );
}

function Bloc({
  label,
  id,
  compte,
  max,
  children,
}: {
  label: string;
  id: string;
  compte: number;
  max: number;
  children: ReactNode;
}) {
  return (
    <div className="space-y-2">
      <div className="flex items-baseline justify-between gap-2">
        <Label htmlFor={id}>{label}</Label>
        <span
          className={`text-xs ${compte > max * 0.9 ? "font-bold text-logo-red" : "text-muted-foreground"}`}
        >
          {compte} / {max}
        </span>
      </div>
      <div>{children}</div>
    </div>
  );
}

function Outil({
  titre,
  onClick,
  children,
}: {
  titre: string;
  onClick: () => void;
  children: ReactNode;
}) {
  return (
    <button
      type="button"
      title={titre}
      aria-label={titre}
      onClick={onClick}
      className="inline-flex size-9 items-center justify-center rounded-md text-ink/80 hover:bg-white"
    >
      {children}
    </button>
  );
}
