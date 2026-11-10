import { useCallback, useEffect, useState, type CSSProperties, type ReactNode } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import {
  ArrowLeft,
  ArrowRight,
  Check,
  Loader2,
  Lock,
  Play,
  RotateCcw,
  Share2,
  UserPlus,
} from "lucide-react";

import mascotteMedias from "@/assets/mascotte-medias.webp";
import { useMoi } from "@/hooks/use-moi";
import {
  commencerQuelAxe,
  ErreurApi,
  etatQuelAxe,
  MESSAGE_INDISPONIBLE,
  repondreQuelAxe,
  terminerQuelAxe,
  type EtatQuelAxe,
  type PartieQuelAxe,
  type QuestionQuelAxe,
} from "@/lib/api/client";
import { axeDecouverte, partagerAxe, type AxeDecouverte } from "@/lib/axes-decouverte";

// L'adresse de retour après la connexion : l'accueil, qui rouvre le test (voir `QuelAxe`).
const RETOUR = "/?test=quel-axe#quel-axe";

type Acces = "chargement" | "visiteur" | "reserve" | "eleve" | "indisponible";

// Le contenu de la fenêtre du test (specs 021 et 032) : les cas du document (élève connecté, visiteur, autre
// profil), puis le jeu de l'élève : 7 questions, 3 participations gardées par l'API.
export function QuelAxeTest() {
  const { data: moi, isPending, isError } = useMoi();
  const [refus, setRefus] = useState<Acces | null>(null);
  const acces: Acces =
    refus ??
    (isPending
      ? "chargement"
      : isError
        ? "indisponible"
        : !moi
          ? "visiteur"
          : moi.role === "eleve"
            ? "eleve"
            : "reserve");

  // L'API a le dernier mot : une session expirée (401) ou un profil refusé (403) change l'écran.
  const surErreur = useCallback(
    (e: unknown) =>
      setRefus(
        e instanceof ErreurApi && e.statut === 401
          ? "visiteur"
          : e instanceof ErreurApi && e.statut === 403
            ? "reserve"
            : "indisponible",
      ),
    [],
  );

  if (acces === "chargement") return <Chargement />;
  if (acces === "visiteur") return <Visiteur />;
  if (acces === "reserve")
    return (
      <Message titre="Ce jeu est réservé aux élèves inscrits.">
        Il se joue depuis un compte Élève. Les sept axes restent ouverts à tous sur la page{" "}
        <a href="/les-7-axes" className="font-bold text-logo-blue underline">
          Les 7 axes
        </a>
        .
      </Message>
    );
  if (acces === "indisponible")
    return <Message titre="Le test est indisponible">{MESSAGE_INDISPONIBLE}</Message>;
  return <Jeu surErreur={surErreur} />;
}

const LIMITE_ATTEINTE =
  "Tu as utilisé tes 3 participations ! Tu peux revoir tes résultats et découvrir les 7 axes des Clubs Santé.";

const pluriel = (n: number) => `${n} partie${n > 1 ? "s" : ""} restante${n > 1 ? "s" : ""}`;

const date = (iso: string) =>
  new Date(iso).toLocaleDateString("fr-FR", { day: "numeric", month: "long", year: "numeric" });

type Ecran =
  | { nom: "accueil" }
  | { nom: "partie"; partie: PartieQuelAxe }
  | { nom: "resultat"; partie: PartieQuelAxe };

// Le jeu de l'élève (spec 032) : l'API garde ses parties, 3 au plus. L'accueil du jeu montre le compteur, la
// partie à reprendre et l'historique ; chaque réponse est enregistrée dès qu'elle est choisie.
function Jeu({ surErreur }: { surErreur: (e: unknown) => void }) {
  const client = useQueryClient();
  const etat = useQuery({ queryKey: ["quel-axe"], queryFn: etatQuelAxe, retry: false });
  const [ecran, setEcran] = useState<Ecran>({ nom: "accueil" });
  const [demarrage, setDemarrage] = useState(false);
  const [erreurDemarrage, setErreurDemarrage] = useState<string | null>(null);

  useEffect(() => {
    if (etat.isError) surErreur(etat.error);
  }, [etat.isError, etat.error, surErreur]);

  if (etat.isPending || etat.isError) return <Chargement />;
  const donnees = etat.data;
  const rafraichir = () => client.invalidateQueries({ queryKey: ["quel-axe"] });

  const commencer = async () => {
    setDemarrage(true);
    setErreurDemarrage(null);
    try {
      setEcran({ nom: "partie", partie: await commencerQuelAxe() });
    } catch (e) {
      // Plus de participation (une partie lancée ailleurs, par exemple) : le compteur à jour le dira.
      if (e instanceof ErreurApi && e.statut === 403) {
        const suite = await etat.refetch();
        if (suite.isError) surErreur(suite.error);
        setEcran({ nom: "accueil" });
      } else if (e instanceof ErreurApi && e.statut === 401) surErreur(e);
      else setErreurDemarrage("La partie n’a pas pu commencer. Vérifie ta connexion et réessaie.");
    } finally {
      setDemarrage(false);
      void rafraichir();
    }
  };

  if (ecran.nom === "partie")
    return (
      <Questionnaire
        questions={donnees.questions}
        limite={donnees.limite}
        partieInitiale={ecran.partie}
        surErreur={surErreur}
        // La copie en cache suit chaque réponse : rouvrir le jeu reprend au bon endroit, même avant rechargement.
        onReponse={(partie) =>
          client.setQueryData<EtatQuelAxe>(["quel-axe"], (avant) =>
            avant?.en_cours?.id === partie.id ? { ...avant, en_cours: partie } : avant,
          )
        }
        // Partie terminée ailleurs (autre appareil) : retour à l'accueil du jeu, à jour.
        onPerimee={() => {
          void rafraichir();
          setEcran({ nom: "accueil" });
        }}
        onFin={(partie) => {
          void rafraichir();
          setEcran({ nom: "resultat", partie });
        }}
      />
    );
  if (ecran.nom === "resultat") {
    // Le compteur vient de l'API ; terminer une partie ne le change pas. Une autre partie en cours se reprend
    // depuis l'accueil du jeu : pas de « Rejouer » ici.
    const autreEnCours = donnees.en_cours !== null && donnees.en_cours.id !== ecran.partie.id;
    return (
      <Resultat
        partie={ecran.partie}
        restantes={autreEnCours ? 0 : donnees.restantes}
        epuise={!autreEnCours && donnees.restantes === 0}
        demarrage={demarrage}
        onRejouer={commencer}
        onRetour={() => setEcran({ nom: "accueil" })}
      />
    );
  }

  const enCours = donnees.en_cours;
  const repondues = enCours ? enCours.reponses.filter(Boolean).length : 0;
  return (
    <div className="p-6 md:p-10">
      <p className="font-hand text-2xl text-logo-red">Quel axe est fait pour toi&#8239;?</p>
      <p className="mt-1 font-display text-3xl leading-tight text-ink">
        7 questions, <span className="text-grape">3 participations</span>
      </p>
      <dl className="mt-6 grid grid-cols-2 gap-3">
        <div className="rounded-2xl bg-grape/10 p-4">
          <dt className="text-sm font-bold text-ink/70">Participations utilisées</dt>
          <dd className="font-display text-3xl text-grape">
            {donnees.utilisees}/{donnees.limite}
          </dd>
        </div>
        <div className="rounded-2xl bg-mist p-4">
          <dt className="text-sm font-bold text-ink/70">Participations restantes</dt>
          <dd className="font-display text-3xl text-ink">{donnees.restantes}</dd>
        </div>
      </dl>

      <div className="mt-6">
        {enCours ? (
          <button
            type="button"
            disabled={etat.isFetching}
            onClick={() => setEcran({ nom: "partie", partie: enCours })}
            className="btn-fx inline-flex items-center gap-2 rounded-full bg-grape px-7 py-3 font-bold text-white disabled:opacity-60"
          >
            <Play className="size-4" /> Reprendre la partie ({repondues}/{enCours.reponses.length})
          </button>
        ) : donnees.restantes > 0 ? (
          <button
            type="button"
            disabled={demarrage}
            onClick={commencer}
            className="btn-fx inline-flex items-center gap-2 rounded-full bg-grape px-7 py-3 font-bold text-white disabled:opacity-60"
          >
            {demarrage ? <Loader2 className="size-4 animate-spin" /> : <Play className="size-4" />}
            Commencer
          </button>
        ) : (
          <div role="status" className="rounded-2xl border-2 border-grape/30 p-4">
            <p className="font-bold text-ink">{LIMITE_ATTEINTE}</p>
            <a
              href="/les-7-axes"
              className="mt-3 inline-flex items-center gap-2 font-bold text-grape underline"
            >
              Découvrir les axes <ArrowRight className="size-4" />
            </a>
          </div>
        )}
        {erreurDemarrage && (
          <p role="alert" className="mt-3 text-sm font-bold text-destructive">
            {erreurDemarrage}
          </p>
        )}
        {!enCours && donnees.restantes > 0 && (
          <p className="mt-2 text-sm font-medium text-muted-foreground">
            Une participation compte dès que tu commences. Tu pourras toujours reprendre ta partie.
          </p>
        )}
      </div>

      {donnees.historique.length > 0 && (
        <section className="mt-8">
          <h3 className="text-sm font-extrabold uppercase tracking-widest text-muted-foreground">
            Mes résultats
          </h3>
          <ul className="mt-3 space-y-2">
            {donnees.historique.map((p) => (
              <LigneHistorique
                key={p.id}
                partie={p}
                onVoir={() => setEcran({ nom: "resultat", partie: p })}
              />
            ))}
          </ul>
        </section>
      )}
      <p className="mt-8 text-xs font-medium text-muted-foreground">
        Tes réponses et tes résultats sont gardés pour ton historique et ton compteur. Ils ne
        rapportent aucun point et sont effacés avec ton compte.
      </p>
    </div>
  );
}

function LigneHistorique({ partie, onVoir }: { partie: PartieQuelAxe; onVoir: () => void }) {
  const axe = axeDecouverte(partie.resultat!.principal);
  return (
    <li>
      <button
        type="button"
        onClick={onVoir}
        style={{ "--axe": axe.couleur } as CSSProperties}
        className="flex w-full items-center gap-3 rounded-2xl border-2 border-(color:--axe)/40 p-3 text-left transition hover:-translate-y-0.5 hover:shadow-card"
      >
        <span className="size-12 shrink-0 overflow-hidden rounded-xl bg-(color:--axe)">
          <img
            src={axe.img}
            alt=""
            width={1414}
            height={2000}
            className="size-full scale-150 object-cover object-top"
          />
        </span>
        <span className="flex-1">
          <span className="block text-xs font-bold text-muted-foreground">
            Partie {partie.numero} · {date(partie.terminee_le!)}
          </span>
          <span className="block font-bold text-ink">{axe.nom}</span>
          <span className="block text-xs font-semibold text-ink/65">
            À explorer aussi :{" "}
            {partie.resultat!.autres.map((code) => axeDecouverte(code).nom).join(" · ")}
          </span>
        </span>
        <span className="text-sm font-bold text-grape">Voir</span>
      </button>
    </li>
  );
}

function Questionnaire({
  questions: liste,
  limite,
  partieInitiale,
  surErreur,
  onReponse,
  onPerimee,
  onFin,
}: {
  questions: QuestionQuelAxe[];
  limite: number;
  partieInitiale: PartieQuelAxe;
  surErreur: (e: unknown) => void;
  onReponse: (partie: PartieQuelAxe) => void;
  onPerimee: () => void;
  onFin: (partie: PartieQuelAxe) => void;
}) {
  const [partie, setPartie] = useState(partieInitiale);
  // On reprend à la première question sans réponse.
  const [etape, setEtape] = useState(() => {
    const i = partieInitiale.reponses.findIndex((r) => r === null);
    return i === -1 ? liste.length - 1 : i;
  });
  const [envoi, setEnvoi] = useState<"reponse" | "fin" | null>(null);
  const [erreur, setErreur] = useState<string | null>(null);

  // Une session expirée ou un profil refusé change l'écran ; une autre erreur se réessaie sur place.
  const echec = (e: unknown, message: string) => {
    if (e instanceof ErreurApi && (e.statut === 401 || e.statut === 403)) surErreur(e);
    else if (e instanceof ErreurApi && (e.statut === 404 || e.statut === 409)) onPerimee();
    else setErreur(message);
  };

  const question = liste[etape]!;
  const choisie = partie.reponses[etape] ?? undefined;
  const derniere = etape === liste.length - 1;

  const choisir = async (lettre: string) => {
    setEnvoi("reponse");
    setErreur(null);
    try {
      const suite = await repondreQuelAxe(partie.id, question.numero, lettre);
      setPartie(suite);
      onReponse(suite);
    } catch (e) {
      echec(e, "Ta réponse n’a pas été enregistrée. Vérifie ta connexion et réessaie.");
    } finally {
      setEnvoi(null);
    }
  };

  const suivant = async () => {
    if (!choisie) return;
    if (!derniere) return setEtape(etape + 1);
    setEnvoi("fin");
    setErreur(null);
    try {
      onFin(await terminerQuelAxe(partie.id));
    } catch (e) {
      echec(e, "Ton résultat n’a pas pu être calculé. Réessaie dans un instant.");
    } finally {
      setEnvoi(null);
    }
  };

  return (
    <div className="p-6 md:p-10">
      <div aria-hidden className="flex gap-1.5 pr-8">
        {liste.map((q) => (
          <span
            key={q.numero}
            className={`h-2 flex-1 rounded-full transition-colors duration-500 ${q.numero <= etape + 1 ? "bg-grape" : "bg-mist"}`}
          />
        ))}
      </div>
      <div key={etape} className="animate-in fade-in slide-in-from-right-4">
        <p className="mt-6 text-sm font-extrabold uppercase tracking-widest text-grape">
          Question {etape + 1} sur {liste.length}
          <span className="ml-2 font-bold normal-case tracking-normal text-muted-foreground">
            · Partie {partie.numero}/{limite}
          </span>
        </p>
        <p className="mt-2 font-display text-2xl leading-tight text-ink md:text-3xl">
          {question.libelle}
        </p>
        <Reponses
          question={question}
          choisie={choisie}
          desactive={envoi !== null}
          onChoisir={choisir}
        />
      </div>
      {erreur && (
        <p role="alert" className="mt-4 text-sm font-bold text-destructive">
          {erreur}
        </p>
      )}
      <div className="mt-8 flex items-center justify-between gap-3">
        <button
          type="button"
          disabled={etape === 0 || envoi !== null}
          onClick={() => setEtape(etape - 1)}
          className="inline-flex items-center gap-2 rounded-full px-4 py-2.5 font-bold text-muted-foreground transition hover:text-grape disabled:invisible"
        >
          <ArrowLeft className="size-4" /> Précédent
        </button>
        <button
          type="button"
          disabled={!choisie || envoi !== null}
          onClick={suivant}
          className="btn-fx inline-flex items-center gap-2 rounded-full bg-grape px-7 py-3 font-bold text-white disabled:cursor-not-allowed disabled:opacity-40"
        >
          {envoi ? <Loader2 className="size-4 animate-spin" /> : null}
          {derniere ? "Voir mon axe" : "Suivant"} <ArrowRight className="size-4" />
        </button>
      </div>
    </div>
  );
}

function Reponses({
  question,
  choisie,
  desactive,
  onChoisir,
}: {
  question: QuestionQuelAxe;
  choisie: string | undefined;
  desactive: boolean;
  onChoisir: (id: string) => void;
}) {
  return (
    <div role="radiogroup" aria-label={question.libelle} className="mt-6 grid gap-3 sm:grid-cols-2">
      {question.reponses.map((r) => {
        const active = r.id === choisie;
        return (
          <button
            key={r.id}
            type="button"
            role="radio"
            aria-checked={active}
            disabled={desactive}
            onClick={() => onChoisir(r.id)}
            className={`flex h-full items-start gap-3 rounded-2xl border-2 p-4 text-left font-semibold transition duration-200 hover:-translate-y-0.5 hover:shadow-card ${
              active ? "border-grape bg-grape/5 text-ink" : "border-border bg-white text-ink/85"
            }`}
          >
            <span
              className={`inline-flex size-8 shrink-0 items-center justify-center rounded-full font-display text-lg ${
                active ? "bg-grape text-white" : "bg-mist text-grape"
              }`}
            >
              {active ? <Check className="size-4" /> : r.id}
            </span>
            {r.libelle}
          </button>
        );
      })}
    </div>
  );
}

function Resultat({
  partie,
  restantes,
  epuise,
  demarrage,
  onRejouer,
  onRetour,
}: {
  partie: PartieQuelAxe;
  restantes: number;
  epuise: boolean;
  demarrage: boolean;
  onRejouer: () => void;
  onRetour: () => void;
}) {
  const resultat = partie.resultat!;
  const axe = axeDecouverte(resultat.principal);
  const autres = resultat.autres.map(axeDecouverte);
  const [partage, setPartage] = useState<string | null>(null);

  const partager = async () => setPartage(await partagerAxe(axe.nom));

  return (
    <div
      style={{ "--axe": axe.couleur } as CSSProperties}
      className="animate-in fade-in zoom-in-95"
    >
      <div className="relative overflow-hidden bg-(color:--axe) px-6 pb-6 pt-10 md:px-10">
        <div className="grid items-end gap-4 sm:grid-cols-[auto_1fr]">
          <img
            src={axe.img}
            alt={`La mascotte de l’axe ${axe.nom}`}
            width={1414}
            height={2000}
            className="mx-auto h-44 w-auto drop-shadow-2xl motion-safe:animate-float sm:h-52"
          />
          {/* Seul le titre est annoncé aux lecteurs d'écran, pas tout l'écran de résultat. */}
          <div role="status" className={axe.encre}>
            <p className="text-sm font-extrabold uppercase tracking-widest opacity-90">
              Ton axe principal
            </p>
            <p className="mt-1 font-display text-3xl leading-tight md:text-4xl">{axe.nom}</p>
          </div>
        </div>
      </div>
      <div className="p-6 md:p-10">
        <p className="font-display text-2xl text-ink">{axe.titre}</p>
        <p className="mt-2 font-medium text-ink/80">{axe.texte}</p>
        <p className="mt-3 inline-flex rounded-full bg-(color:--axe)/15 px-4 py-1.5 font-bold text-ink">
          Ta force : {axe.force}
        </p>

        <p className="mt-8 text-sm font-extrabold uppercase tracking-widest text-muted-foreground">
          Deux autres axes à explorer
        </p>
        <ul className="mt-3 grid gap-3 sm:grid-cols-2">
          {autres.map((a) => (
            <AutreAxe key={a.code} axe={a} />
          ))}
        </ul>

        <div className="mt-8 flex flex-wrap gap-3">
          <a
            href={`/les-7-axes#axe-${axe.n}`}
            className="btn-fx inline-flex items-center gap-2 rounded-full bg-grape px-6 py-3 font-bold text-white"
          >
            Découvrir cet axe <ArrowRight className="size-4" />
          </a>
          <button
            type="button"
            onClick={partager}
            className="inline-flex items-center gap-2 rounded-full border-2 border-grape px-6 py-3 font-bold text-grape transition hover:bg-grape hover:text-white"
          >
            <Share2 className="size-4" /> Partager mon résultat
          </button>
          {restantes > 0 && (
            <button
              type="button"
              disabled={demarrage}
              onClick={onRejouer}
              className="inline-flex items-center gap-2 rounded-full px-4 py-3 font-bold text-muted-foreground transition hover:text-grape disabled:opacity-60"
            >
              {demarrage ? (
                <Loader2 className="size-4 animate-spin" />
              ) : (
                <RotateCcw className="size-4" />
              )}{" "}
              Rejouer ({pluriel(restantes)})
            </button>
          )}
        </div>
        {partage && <p className="mt-3 text-sm font-semibold text-ink">{partage}</p>}
        {epuise && (
          <p className="mt-6 rounded-2xl bg-mist p-4 font-bold text-ink">{LIMITE_ATTEINTE}</p>
        )}
        <button
          type="button"
          onClick={onRetour}
          className="mt-4 inline-flex items-center gap-2 font-bold text-grape underline"
        >
          <ArrowLeft className="size-4" /> Voir mes résultats
        </button>
        <p className="mt-6 text-sm font-medium text-muted-foreground">
          Ce test t’oriente, il ne te classe pas : les sept axes te restent ouverts.
        </p>
      </div>
    </div>
  );
}

function AutreAxe({ axe }: { axe: AxeDecouverte }) {
  return (
    <li>
      <a
        href={`/les-7-axes#axe-${axe.n}`}
        style={{ "--axe": axe.couleur } as CSSProperties}
        className="flex items-center gap-3 rounded-2xl border-2 border-(color:--axe)/40 p-3 font-bold text-ink transition hover:-translate-y-0.5 hover:shadow-card"
      >
        <span className="size-12 shrink-0 overflow-hidden rounded-xl bg-(color:--axe)">
          <img
            src={axe.img}
            alt=""
            width={1414}
            height={2000}
            className="size-full scale-150 object-cover object-top"
          />
        </span>
        {axe.nom}
      </a>
    </li>
  );
}

function Visiteur() {
  return (
    <Message titre="Connecte-toi à ton compte Élève pour découvrir ton axe !">
      <span className="mt-5 flex flex-wrap justify-center gap-3">
        <Link
          to="/connexion"
          search={{ redirection: RETOUR }}
          className="btn-fx inline-flex items-center gap-2 rounded-full bg-grape px-6 py-3 font-bold text-white"
        >
          <Lock className="size-4" /> Se connecter
        </Link>
        <Link
          to="/inscription"
          search={{ profil: "eleve" }}
          className="inline-flex items-center gap-2 rounded-full border-2 border-grape px-6 py-3 font-bold text-grape transition hover:bg-grape hover:text-white"
        >
          <UserPlus className="size-4" /> Créer mon compte Élève
        </Link>
      </span>
    </Message>
  );
}

function Message({ titre, children }: { titre: string; children: ReactNode }) {
  return (
    <div role="status" className="p-8 text-center md:p-12">
      <img
        src={mascotteMedias}
        alt=""
        width={1414}
        height={2000}
        className="mx-auto h-40 w-auto drop-shadow-xl"
      />
      <p className="mt-4 font-display text-2xl leading-tight text-grape md:text-3xl">{titre}</p>
      <div className="mt-3 font-medium text-ink/80">{children}</div>
    </div>
  );
}

function Chargement() {
  return (
    <div className="flex justify-center p-16" aria-label="Chargement">
      <Loader2 className="size-8 animate-spin text-grape" />
    </div>
  );
}
