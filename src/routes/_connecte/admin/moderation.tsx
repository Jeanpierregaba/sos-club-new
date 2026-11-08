import { createFileRoute, Link, redirect, useNavigate, useRouter } from "@tanstack/react-router";
import { Check, EyeOff, Loader2, PenLine, X } from "lucide-react";
import { useEffect, useState } from "react";

import { DialogueFormulaire } from "@/components/admin/DialogueFormulaire";
import { DialogueMotif } from "@/components/admin/DialogueMotif";
import { EnTeteAdmin } from "@/components/admin/EnTeteAdmin";
import { EtatContenu } from "@/components/articles/EtatContenu";
import { TexteArticle } from "@/components/articles/TexteArticle";
import { ServiceIndisponible } from "@/components/ServiceIndisponible";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { peut, peutVoirInscrits } from "@/lib/admin";
import {
  chargerApercuModeration,
  chargerAxes,
  chargerFileModeration,
  deciderModeration,
  ErreurApi,
  MESSAGE_INDISPONIBLE,
  type ApercuModeration,
  urlPhotoModeration,
  type EtatContenu as Etat,
} from "@/lib/api/client";
import { dateCourte } from "@/lib/dates";

type Recherche = {
  etat?: Etat | undefined;
  type?: "article" | "commentaire" | undefined;
  axe?: string | undefined;
  profil?: "eleve" | "encadreur" | undefined;
  dre?: string | undefined;
};
type Decision = "corriger" | "refuser" | "depublier";

const ONGLETS: { etat: Etat; libelle: string }[] = [
  { etat: "en_attente", libelle: "À modérer" },
  { etat: "publie", libelle: "Publiés" },
  { etat: "a_corriger", libelle: "À corriger" },
  { etat: "refuse", libelle: "Refusés" },
  { etat: "depublie", libelle: "Retirés" },
];
const ETATS = new Set<string>(ONGLETS.map((o) => o.etat));

const CHAMPS: { cle: string; libelle: string }[] = [
  { cle: "titre", libelle: "Titre" },
  { cle: "chapo", libelle: "Chapô" },
  { cle: "axe_code", libelle: "Axe" },
  { cle: "texte", libelle: "Texte" },
  { cle: "afficher_club", libelle: "Club affiché" },
];

const DECISIONS: Record<Decision, { titre: string; bouton: string; aide: string }> = {
  corriger: {
    titre: "Demander une correction ?",
    bouton: "Demander la correction",
    aide: "L'auteur lit ce message, corrige son article et le soumet de nouveau.",
  },
  refuser: {
    titre: "Refuser ce contenu ?",
    bouton: "Refuser",
    aide: "L'auteur lit ce motif. Un contenu jamais publié est alors clos ; pour une nouvelle version, la version en ligne reste.",
  },
  depublier: {
    titre: "Retirer ce contenu du site ?",
    bouton: "Retirer du site",
    aide: "Le contenu disparaît du site tout de suite. L'auteur lit ce motif ; ses points restent acquis.",
  },
};

export const Route = createFileRoute("/_connecte/admin/moderation")({
  validateSearch: (search: Record<string, unknown>): Recherche => {
    const etat =
      typeof search["etat"] === "string" && ETATS.has(search["etat"]) ? search["etat"] : null;
    const axe = typeof search["axe"] === "string" ? search["axe"] : null;
    const dre = typeof search["dre"] === "string" ? search["dre"] : null;
    const profil =
      search["profil"] === "eleve" || search["profil"] === "encadreur" ? search["profil"] : null;
    const type =
      search["type"] === "article" || search["type"] === "commentaire" ? search["type"] : null;
    return {
      ...(etat && etat !== "en_attente" ? { etat: etat as Etat } : {}),
      ...(type ? { type } : {}),
      ...(axe ? { axe } : {}),
      ...(profil ? { profil } : {}),
      ...(dre ? { dre } : {}),
    };
  },
  beforeLoad: ({ context }) => {
    if (!peut(context.admin, "moderation", "consulter")) throw redirect({ to: "/admin" });
  },
  loaderDeps: ({ search }) => search,
  loader: async ({ deps }) => {
    const [file, axes] = await Promise.all([
      chargerFileModeration({
        etat: deps.etat ?? "en_attente",
        type: deps.type,
        axe: deps.axe,
        profil: deps.profil,
        dre: deps.dre,
      }),
      chargerAxes().catch(() => []),
    ]);
    return { file, axes };
  },
  gcTime: 0,
  errorComponent: ServiceIndisponible,
  component: Moderation,
});

function Moderation() {
  const { admin, catalogue } = Route.useRouteContext();
  const { file, axes } = Route.useLoaderData();
  const recherche = Route.useSearch();
  const etat = recherche.etat ?? "en_attente";
  const navigate = useNavigate({ from: "/admin/moderation" });
  const [ouvert, setOuvert] = useState<string | null>(null);
  const libelleAxe = (code: string | null | undefined) =>
    axes.find((a) => a.code === code)?.libelle ?? code ?? "";

  return (
    <div className="space-y-6">
      <EnTeteAdmin sur="Publications" bleu="Centre de" vert="modération">
        Relis chaque contenu avant sa publication : rien n'est visible sur le site sans ta
        validation. L'approbation crédite les points de l'auteur, une seule fois.
        {admin.perimetre_dre &&
          ` Tu vois les contenus des auteurs de la DRE ${catalogue.dre[admin.perimetre_dre]}.`}
      </EnTeteAdmin>

      <nav aria-label="États" className="flex flex-wrap gap-2">
        {ONGLETS.map((o) => (
          <Link
            key={o.etat}
            to="/admin/moderation"
            search={{ ...recherche, etat: o.etat === "en_attente" ? undefined : o.etat }}
            className={`rounded-full px-4 py-2 text-sm font-bold ring-1 transition ${
              etat === o.etat
                ? "bg-night text-white ring-night"
                : "bg-white ring-border hover:ring-night/30"
            }`}
          >
            {o.libelle}
            {etat === o.etat && ` (${file.total})`}
          </Link>
        ))}
      </nav>

      <div className="flex flex-wrap gap-3">
        <select
          aria-label="Filtrer par type"
          value={recherche.type ?? ""}
          onChange={(e) =>
            void navigate({
              search: {
                ...recherche,
                type: (e.target.value || undefined) as Recherche["type"],
              },
            })
          }
          className="h-10 rounded-full border bg-white px-4 text-sm font-semibold"
        >
          <option value="">Articles et commentaires</option>
          <option value="article">Articles</option>
          <option value="commentaire">Commentaires</option>
        </select>
        <select
          aria-label="Filtrer par axe"
          value={recherche.axe ?? ""}
          onChange={(e) =>
            void navigate({ search: { ...recherche, axe: e.target.value || undefined } })
          }
          className="h-10 rounded-full border bg-white px-4 text-sm font-semibold"
        >
          <option value="">Tous les axes</option>
          {axes.map((a) => (
            <option key={a.code} value={a.code}>
              {a.libelle}
            </option>
          ))}
        </select>
        <select
          aria-label="Filtrer par profil"
          value={recherche.profil ?? ""}
          onChange={(e) =>
            void navigate({
              search: {
                ...recherche,
                profil: (e.target.value || undefined) as Recherche["profil"],
              },
            })
          }
          className="h-10 rounded-full border bg-white px-4 text-sm font-semibold"
        >
          <option value="">Élèves et encadreurs</option>
          <option value="eleve">Élèves</option>
          <option value="encadreur">Encadreurs</option>
        </select>
        {/* Un collaborateur de DRE ne voit que la sienne : le filtre ne sert qu'au niveau national. */}
        {!admin.perimetre_dre && (
          <select
            aria-label="Filtrer par DRE"
            value={recherche.dre ?? ""}
            onChange={(e) =>
              void navigate({ search: { ...recherche, dre: e.target.value || undefined } })
            }
            className="h-10 rounded-full border bg-white px-4 text-sm font-semibold"
          >
            <option value="">Toutes les DRE</option>
            {Object.entries(catalogue.dre).map(([code, nom]) => (
              <option key={code} value={code}>
                {nom}
              </option>
            ))}
          </select>
        )}
      </div>

      {file.contenus.length === 0 ? (
        <p className="rounded-3xl bg-white p-6 font-medium text-muted-foreground ring-1 ring-border">
          {etat === "en_attente" ? "Aucun contenu à modérer pour l'instant." : "Aucun contenu ici."}
        </p>
      ) : (
        <ul className="grid gap-3">
          {file.contenus.map((c) => (
            <li key={c.id}>
              <button
                type="button"
                onClick={() => setOuvert(c.id)}
                className="w-full rounded-3xl bg-white p-5 text-left shadow-sm ring-1 ring-border transition hover:ring-night/30"
              >
                <div className="flex flex-wrap items-center gap-2">
                  <EtatContenu etat={c.etat} enLigne={c.en_ligne} />
                  {c.nouvelle_version && (
                    <span className="rounded-full bg-sky/15 px-2.5 py-0.5 text-xs font-bold text-logo-blue">
                      Nouvelle version
                    </span>
                  )}
                  {c.type === "commentaire" && (
                    <span className="rounded-full bg-lilac px-2.5 py-0.5 text-xs font-bold text-ink">
                      Commentaire
                    </span>
                  )}
                  <span className="text-xs font-semibold text-muted-foreground">
                    {libelleAxe(c.axe_code)}
                  </span>
                </div>
                <p className="mt-2 text-lg font-extrabold text-logo-blue">{c.titre}</p>
                {c.parent && (
                  <p className="text-sm font-semibold text-muted-foreground">
                    Sur l'article « {c.parent.titre} »
                  </p>
                )}
                <p className="text-sm font-semibold text-ink">
                  {c.auteur.nom}{" "}
                  <span className="font-medium text-muted-foreground">
                    · {c.auteur.profil === "eleve" ? "élève" : "encadreur"}
                    {c.auteur.etablissement && ` · ${c.auteur.etablissement}`}
                    {c.auteur.dre_code &&
                      ` · ${catalogue.dre[c.auteur.dre_code] ?? c.auteur.dre_code}`}
                  </span>
                </p>
                <p className="mt-1 text-xs font-semibold text-muted-foreground">
                  {c.soumis_le
                    ? `Soumis le ${dateCourte(c.soumis_le)}`
                    : `Modifié le ${dateCourte(c.modifie_le)}`}
                </p>
              </button>
            </li>
          ))}
        </ul>
      )}

      <Apercu
        id={ouvert}
        onFerme={() => setOuvert(null)}
        libelleAxe={libelleAxe}
        decideur={peut(admin, "moderation", "approuver")}
        depublieur={peut(admin, "moderation", "depublier")}
        ficheVisible={peutVoirInscrits(admin)}
      />
    </div>
  );
}

function Apercu({
  id,
  onFerme,
  libelleAxe,
  decideur,
  depublieur,
  ficheVisible,
}: {
  id: string | null;
  onFerme: () => void;
  libelleAxe: (code: string | null | undefined) => string;
  decideur: boolean;
  depublieur: boolean;
  ficheVisible: boolean;
}) {
  const router = useRouter();
  const [apercu, setApercu] = useState<ApercuModeration | null>(null);
  const [erreur, setErreur] = useState<string | null>(null);
  const [approbation, setApprobation] = useState(false);
  const [decision, setDecision] = useState<Decision | null>(null);

  useEffect(() => {
    setApercu(null);
    setErreur(null);
    if (!id) return;
    let actif = true;
    chargerApercuModeration(id)
      .then((a) => actif && setApercu(a))
      .catch(
        (e: unknown) =>
          actif && setErreur(e instanceof ErreurApi ? e.message : MESSAGE_INDISPONIBLE),
      );
    return () => {
      actif = false;
    };
  }, [id]);

  const apres = async (nouveau: ApercuModeration) => {
    setApercu(nouveau);
    await router.invalidate();
  };

  const soumise = apercu?.soumise as Record<string, string> | null | undefined;
  const publiee = apercu?.publiee as Record<string, string> | null | undefined;
  const enAttente = apercu?.etat === "en_attente";
  // Un commentaire (spec 025) : un texte simple, jugé avec l'article qu'il commente.
  const commentaire = apercu?.type === "commentaire";
  // En attente : la version soumise. Sinon : ce qui est en ligne (le modérateur qui dépublie lit ce qui est publié).
  const affichee = enAttente ? soumise : (publiee ?? soumise);
  // Les photos de la version affichée, et ce qui change par rapport à la version en ligne (spec 024).
  const photosAffichees = apercu
    ? enAttente || !publiee
      ? apercu.photos_soumises
      : apercu.photos_publiees
    : [];
  const enLigneIds = new Set(apercu?.photos_publiees.map((p) => p.id) ?? []);
  const soumisesIds = new Set(apercu?.photos_soumises.map((p) => p.id) ?? []);
  const comparer = Boolean(apercu?.nouvelle_version && enAttente);
  const ajoutees = comparer ? apercu!.photos_soumises.filter((p) => !enLigneIds.has(p.id)) : [];
  const retirees = comparer ? apercu!.photos_publiees.filter((p) => !soumisesIds.has(p.id)) : [];
  const changements =
    soumise && publiee ? CHAMPS.filter((c) => soumise[c.cle] !== publiee[c.cle]) : [];
  const valeur = (cle: string, champs: Record<string, string> | null | undefined) => {
    const v: unknown = champs?.[cle];
    if (cle === "axe_code") return libelleAxe(typeof v === "string" ? v : null);
    if (typeof v === "boolean") return v ? "Oui" : "Non";
    return typeof v === "string" ? v : "";
  };

  return (
    <Dialog open={id !== null} onOpenChange={(o) => !o && onFerme()}>
      <DialogContent className="max-h-[92dvh] w-full max-w-3xl overflow-y-auto sm:rounded-[2rem]">
        <DialogHeader>
          <DialogTitle className="pr-6 text-2xl text-logo-blue">
            {commentaire ? "Commentaire" : (affichee?.["titre"] ?? "Aperçu")}
          </DialogTitle>
          <DialogDescription>
            {apercu
              ? `${apercu.auteur.nom} · ${apercu.auteur.profil === "eleve" ? "élève" : "encadreur"}${apercu.auteur.etablissement ? ` · ${apercu.auteur.etablissement}` : ""}`
              : "Chargement du contenu."}
          </DialogDescription>
        </DialogHeader>

        {erreur && (
          <Alert variant="destructive">
            <AlertDescription>{erreur}</AlertDescription>
          </Alert>
        )}
        {!apercu && !erreur && <Loader2 className="mx-auto size-6 animate-spin text-logo-blue" />}

        {apercu && affichee && (
          <div className="space-y-5">
            <div className="flex flex-wrap items-center gap-2 text-sm">
              <EtatContenu etat={apercu.etat} enLigne={apercu.en_ligne} />
              <span className="font-semibold text-muted-foreground">
                {libelleAxe(affichee["axe_code"])}
              </span>
              {ficheVisible && (
                <Link
                  to="/admin/inscrits/$id"
                  params={{ id: apercu.auteur.id }}
                  className="font-bold text-logo-blue underline-offset-4 hover:underline"
                >
                  Fiche de l'auteur
                </Link>
              )}
              {apercu.parent && (
                <span className="font-semibold">
                  Sur{" "}
                  {apercu.parent.adresse ? (
                    <a
                      href={`/articles/${apercu.parent.adresse}`}
                      target="_blank"
                      rel="noreferrer"
                      className="font-bold text-logo-blue underline-offset-4 hover:underline"
                    >
                      « {apercu.parent.titre} »
                    </a>
                  ) : (
                    `« ${apercu.parent.titre} »`
                  )}
                </span>
              )}
              {apercu.en_ligne && apercu.adresse && (
                <a
                  href={`/articles/${apercu.adresse}`}
                  target="_blank"
                  rel="noreferrer"
                  className="font-bold text-logo-blue underline-offset-4 hover:underline"
                >
                  Voir en ligne
                </a>
              )}
            </div>

            {changements.length > 0 && (
              <section className="space-y-3 rounded-2xl bg-sky/10 p-4 ring-1 ring-sky/30">
                <h3 className="font-extrabold text-logo-blue">
                  Ce qui change par rapport à la version en ligne
                </h3>
                {changements.map((c) => (
                  <div key={c.cle} className="grid gap-2 text-sm sm:grid-cols-2">
                    <div>
                      <p className="text-xs font-extrabold uppercase text-muted-foreground">
                        {c.libelle} · avant
                      </p>
                      <p className="mt-1 max-h-48 overflow-y-auto whitespace-pre-line rounded-xl bg-white p-3">
                        {valeur(c.cle, publiee)}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs font-extrabold uppercase text-muted-foreground">
                        {c.libelle} · après
                      </p>
                      <p className="mt-1 max-h-48 overflow-y-auto whitespace-pre-line rounded-xl bg-white p-3 ring-2 ring-sky/40">
                        {valeur(c.cle, soumise)}
                      </p>
                    </div>
                  </div>
                ))}
              </section>
            )}

            {commentaire ? (
              <p className="whitespace-pre-line break-words rounded-2xl bg-carnet p-5 text-ink">
                {affichee["texte"]}
              </p>
            ) : (
              <article className="rounded-2xl bg-carnet p-5">
                <p className="text-lg font-semibold text-ink/80">{affichee["chapo"]}</p>
                <TexteArticle texte={affichee["texte"] ?? ""} className="mt-4" />
              </article>
            )}

            {photosAffichees.length > 0 && (
              <section>
                <h3 className="font-extrabold text-logo-blue">Photos ({photosAffichees.length})</h3>
                <ul className="mt-2 grid gap-3 sm:grid-cols-2">
                  {photosAffichees.map((p) => (
                    <li key={p.id} className="rounded-2xl bg-white p-3 ring-1 ring-border">
                      {p.effacee ? (
                        <p className="flex aspect-[4/3] items-center justify-center rounded-xl bg-mist text-sm text-muted-foreground">
                          Photo effacée
                        </p>
                      ) : (
                        <a
                          href={urlPhotoModeration(apercu.id, p.id, "grande")}
                          target="_blank"
                          rel="noreferrer"
                        >
                          <img
                            src={urlPhotoModeration(apercu.id, p.id, "grande")}
                            alt={p.legende ?? "Photo soumise"}
                            width={p.largeur}
                            height={p.hauteur}
                            loading="lazy"
                            className="w-full rounded-xl object-contain"
                          />
                        </a>
                      )}
                      <p className="mt-2 flex flex-wrap gap-2 text-xs font-bold">
                        {p.couverture && (
                          <span className="rounded-full bg-sun/30 px-2 py-0.5">Couverture</span>
                        )}
                        {ajoutees.some((a) => a.id === p.id) && (
                          <span className="rounded-full bg-sky/20 px-2 py-0.5 text-logo-blue">
                            Ajoutée
                          </span>
                        )}
                      </p>
                      {p.legende && <p className="mt-1 text-sm">{p.legende}</p>}
                      <p className="mt-1 text-xs text-muted-foreground">
                        Attestée le {dateCourte(p.attestee_le)} : « {p.attestation} »
                      </p>
                    </li>
                  ))}
                </ul>
                {retirees.length > 0 && (
                  <p className="mt-2 text-sm font-semibold text-muted-foreground">
                    {retirees.length} photo{retirees.length > 1 ? "s" : ""} de la version en ligne
                    retirée{retirees.length > 1 ? "s" : ""} dans cette version
                    {retirees.some((r) => r.legende)
                      ? ` : ${retirees
                          .map((r) => r.legende)
                          .filter(Boolean)
                          .join(", ")}`
                      : ""}
                    .
                  </p>
                )}
              </section>
            )}

            {apercu.decisions.length > 0 && (
              <section>
                <h3 className="font-extrabold text-logo-blue">Historique</h3>
                <ul className="mt-2 space-y-1 text-sm">
                  {apercu.decisions.map((d, i) => (
                    <li key={i}>
                      <strong>{LIBELLES_DECISIONS[d.decision]}</strong> le {dateCourte(d.decide_le)}
                      {d.decide_par && ` par ${d.decide_par}`}
                      {d.motif && <span className="text-muted-foreground"> : {d.motif}</span>}
                    </li>
                  ))}
                </ul>
              </section>
            )}

            <div className="flex flex-wrap gap-2 border-t pt-4">
              {decideur && enAttente && (
                <>
                  <Button className="rounded-full font-bold" onClick={() => setApprobation(true)}>
                    <Check className="size-4" /> Approuver
                  </Button>
                  {apercu.correction_possible && (
                    <Button
                      variant="outline"
                      className="rounded-full font-bold"
                      onClick={() => setDecision("corriger")}
                    >
                      <PenLine className="size-4" /> Demander une correction
                    </Button>
                  )}
                  <Button
                    variant="outline"
                    className="rounded-full font-bold"
                    onClick={() => setDecision("refuser")}
                  >
                    <X className="size-4" /> Refuser
                  </Button>
                </>
              )}
              {depublieur && apercu.en_ligne && (
                <Button
                  variant="outline"
                  className="rounded-full font-bold text-logo-red"
                  onClick={() => setDecision("depublier")}
                >
                  <EyeOff className="size-4" /> Retirer du site
                </Button>
              )}
            </div>
          </div>
        )}

        <DialogueFormulaire
          ouvert={approbation}
          onOuvert={setApprobation}
          titre="Approuver et publier ?"
          description={
            apercu?.nouvelle_version
              ? "Cette nouvelle version remplace la version en ligne. Aucun point n'est crédité de nouveau."
              : apercu?.type === "commentaire"
                ? "Le commentaire apparaît sous l'article. Son auteur reçoit +5 points, dans la limite de 5 commentaires rémunérés par jour."
                : "L'article est publié sur le site et l'auteur reçoit ses points."
          }
          bouton="Approuver"
          onEnvoie={async () => {
            if (!apercu) return;
            await apres(await deciderModeration(apercu.id, "approuver", apercu.version));
          }}
        />
        <DialogueMotif
          ouvert={decision !== null}
          onOuvert={(o) => !o && setDecision(null)}
          titre={decision ? DECISIONS[decision].titre : ""}
          description={decision ? DECISIONS[decision].aide : ""}
          bouton={decision ? DECISIONS[decision].bouton : ""}
          danger={decision !== "corriger"}
          onConfirme={async (motif) => {
            if (!apercu || !decision) return;
            await apres(await deciderModeration(apercu.id, decision, apercu.version, motif));
          }}
        />
      </DialogContent>
    </Dialog>
  );
}

const LIBELLES_DECISIONS: Record<ApercuModeration["decisions"][number]["decision"], string> = {
  approuver: "Approuvé",
  corriger: "Correction demandée",
  refuser: "Refusé",
  depublier: "Retiré du site",
};
