import { createFileRoute, Link, useRouter } from "@tanstack/react-router";
import {
  ArrowLeft,
  ClipboardList,
  Copy,
  KeyRound,
  Loader2,
  Pause,
  Play,
  UserPen,
} from "lucide-react";
import { useState } from "react";

import { BadgeStatut } from "@/components/admin/BadgeStatut";
import { CHAMP_ADMIN, Champ, DialogueFormulaire } from "@/components/admin/DialogueFormulaire";
import { DialogueMotif } from "@/components/admin/DialogueMotif";
import { ServiceIndisponible } from "@/components/ServiceIndisponible";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";
import { ACTIONS_JOURNAL, PROFILS, dateCourte, dateHeure, peut } from "@/lib/admin";
import {
  adminVoirFicheEleve,
  chargerInscrit,
  ErreurApi,
  MESSAGE_INDISPONIBLE,
  type FicheSortie,
  changerStatutInscrit,
  imposerPseudonyme,
  reinitialiserMotDePasse,
  type InscritDetail,
  type ProfilEleveAdmin,
  type ProfilEncadreurAdmin,
  type ResumePoints,
} from "@/lib/api/client";
import { libelleClasse } from "@/lib/classes";
import { LIBELLES_VERIFICATION, libelleFonction } from "@/lib/fonctions";

export const Route = createFileRoute("/_connecte/admin/inscrits/$id")({
  loader: ({ params }) => chargerInscrit(params.id),
  gcTime: 0,
  errorComponent: ServiceIndisponible,
  component: FicheInscrit,
});

function FicheInscrit() {
  const { admin } = Route.useRouteContext();
  const inscrit = Route.useLoaderData();
  const router = useRouter();
  const [dialogue, setDialogue] = useState(false);
  const suspendu = inscrit.statut === "suspendu";
  const gerable = peut(admin, "inscrits", "modifier") && inscrit.role !== "admin";

  const champs: [string, string][] = [
    ["Identifiant", inscrit.identifiant],
    ["Profil", PROFILS[inscrit.role]],
    ["E-mail", inscrit.email ?? "—"],
    ["Téléphone", inscrit.telephone ?? "—"],
    ["Inscription", dateCourte(inscrit.cree_le)],
    [
      "Consentement",
      inscrit.consentement_le ? dateCourte(inscrit.consentement_le) : "Non renseigné",
    ],
  ];

  return (
    <div className="space-y-6">
      <Link
        to="/admin/inscrits"
        className="inline-flex items-center gap-1.5 text-sm font-bold text-logo-blue hover:underline"
      >
        <ArrowLeft className="size-4" /> Tous les inscrits
      </Link>

      <section className="rounded-3xl bg-white p-6 shadow-sm ring-1 ring-border md:p-8">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 className="text-3xl text-logo-blue">
              {inscrit.prenom} {inscrit.nom}
            </h1>
            <div className="mt-2">
              <BadgeStatut statut={inscrit.statut} />
            </div>
          </div>
          {gerable && inscrit.statut !== "revoque" && (
            <Button
              variant="outline"
              onClick={() => setDialogue(true)}
              className="rounded-full font-bold"
            >
              {suspendu ? <Play className="size-4" /> : <Pause className="size-4" />}
              {suspendu ? "Réactiver" : "Suspendre"}
            </Button>
          )}
        </div>
        <dl className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {champs.map(([libelle, valeur]) => (
            <div key={libelle} className="flex flex-col-reverse">
              <dd className="mt-0.5 break-all font-semibold">{valeur}</dd>
              <dt className="text-xs font-extrabold uppercase tracking-wider text-muted-foreground">
                {libelle}
              </dt>
            </div>
          ))}
        </dl>
      </section>

      {inscrit.eleve && <SectionEleve inscrit={inscrit} eleve={inscrit.eleve} gerable={gerable} />}
      {inscrit.eleve && peut(admin, "fiches_eleves", "consulter") && (
        <SectionFiche id={inscrit.id} />
      )}
      {inscrit.encadreur && <SectionEncadreur encadreur={inscrit.encadreur} />}

      <section className="rounded-3xl bg-white p-6 shadow-sm ring-1 ring-border">
        <h2 className="text-xl text-logo-blue">Historique du compte</h2>
        {inscrit.historique.length === 0 ? (
          <p className="mt-2 text-sm font-medium text-muted-foreground">Aucun événement.</p>
        ) : (
          <ol className="mt-3 divide-y">
            {inscrit.historique.map((e) => (
              <li key={e.id} className="py-3 text-sm">
                <p className="font-bold">
                  {ACTIONS_JOURNAL[e.action] ?? e.action}
                  <span className="font-medium text-muted-foreground"> · {dateHeure(e.quand)}</span>
                </p>
                <p className="text-muted-foreground">
                  Par {e.auteur_libelle ?? "—"}
                  {e.details["motif"] ? ` · Motif : ${String(e.details["motif"])}` : ""}
                </p>
              </li>
            ))}
          </ol>
        )}
      </section>

      <DialogueMotif
        ouvert={dialogue}
        onOuvert={setDialogue}
        titre={suspendu ? "Réactiver ce compte" : "Suspendre ce compte"}
        description={
          suspendu
            ? "Le compte pourra de nouveau se connecter."
            : "Le compte est déconnecté immédiatement et ne peut plus se connecter."
        }
        bouton={suspendu ? "Réactiver" : "Suspendre"}
        danger={!suspendu}
        onConfirme={async (motif) => {
          await changerStatutInscrit(inscrit.id, suspendu ? "reactiver" : "suspendre", motif);
          await router.invalidate();
        }}
      />
    </div>
  );
}

// Profil d'élève (spec 017) : pseudonyme, établissement et registre des points.
function SectionEleve({
  inscrit,
  eleve,
  gerable,
}: {
  inscrit: InscritDetail;
  eleve: ProfilEleveAdmin;
  gerable: boolean;
}) {
  const router = useRouter();
  const [pseudonyme, setPseudonyme] = useState(false);
  const [reinitialiser, setReinitialiser] = useState(false);
  const [provisoire, setProvisoire] = useState<string | null>(null);
  const { points } = eleve;

  const champs: [string, React.ReactNode][] = [
    ["Pseudonyme", eleve.pseudonyme],
    ["Classe", libelleClasse(eleve.classe)],
    [
      "Établissement",
      <>
        {eleve.etablissement.nom}
        {eleve.etablissement.statut !== "actif" && (
          <span className="ml-2 rounded-full bg-sun/30 px-2 py-0.5 text-xs font-extrabold">
            {eleve.etablissement.statut === "propose" ? "Proposé" : "Désactivé"}
          </span>
        )}
      </>,
    ],
    ["IESG et DRE", `${eleve.etablissement.iesg} · ${eleve.etablissement.dre}`],
    ["Charte acceptée", eleve.charte_version],
    ["Points", `${points.points_semestre} ce semestre · ${points.total} au total`],
  ];

  return (
    <section className="rounded-3xl bg-white p-6 shadow-sm ring-1 ring-border md:p-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <h2 className="text-xl text-logo-blue">Profil d'élève</h2>
        {gerable && (
          <div className="flex flex-wrap gap-2">
            <Button
              variant="outline"
              onClick={() => setPseudonyme(true)}
              className="rounded-full font-bold"
            >
              <UserPen className="size-4" /> Imposer un pseudonyme
            </Button>
            <Button
              variant="outline"
              onClick={() => setReinitialiser(true)}
              className="rounded-full font-bold"
            >
              <KeyRound className="size-4" /> Réinitialiser le mot de passe
            </Button>
          </div>
        )}
      </div>
      <dl className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {champs.map(([libelle, valeur]) => (
          <div key={libelle} className="flex flex-col-reverse">
            <dd className="mt-0.5 font-semibold">{valeur}</dd>
            <dt className="text-xs font-extrabold uppercase tracking-wider text-muted-foreground">
              {libelle}
            </dt>
          </div>
        ))}
      </dl>
      <RegistrePoints points={points} />

      {pseudonyme && (
        <DialoguePseudonyme
          inscrit={inscrit}
          actuel={eleve.pseudonyme}
          fermer={() => setPseudonyme(false)}
        />
      )}
      <DialogueMotif
        ouvert={reinitialiser}
        onOuvert={setReinitialiser}
        titre="Réinitialiser le mot de passe"
        description="Un mot de passe provisoire est créé et l'élève est déconnecté partout. Transmets-le lui en personne ou par son encadreur, et invite-le à le changer."
        bouton="Réinitialiser"
        danger
        onConfirme={async (motif) => {
          const { mot_de_passe } = await reinitialiserMotDePasse(inscrit.id, motif);
          setProvisoire(mot_de_passe);
          await router.invalidate();
        }}
      />
      <Dialog open={provisoire !== null} onOpenChange={(o) => !o && setProvisoire(null)}>
        <DialogContent className="rounded-3xl">
          <DialogHeader>
            <DialogTitle className="text-2xl text-logo-blue">Mot de passe provisoire</DialogTitle>
            <DialogDescription>
              Il ne s'affichera plus : note-le maintenant. Identifiant : {inscrit.identifiant}
            </DialogDescription>
          </DialogHeader>
          <div className="flex items-center gap-3 rounded-2xl bg-mist-soft p-4">
            <code className="flex-1 font-mono text-xl font-bold tracking-wider">{provisoire}</code>
            <Button
              variant="outline"
              className="rounded-full font-bold"
              onClick={() => provisoire && void navigator.clipboard?.writeText(provisoire)}
            >
              <Copy className="size-4" /> Copier
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </section>
  );
}

function DialoguePseudonyme({
  inscrit,
  actuel,
  fermer,
}: {
  inscrit: InscritDetail;
  actuel: string;
  fermer: () => void;
}) {
  const router = useRouter();
  const [pseudonyme, setPseudonyme] = useState("");
  const [motif, setMotif] = useState("");

  return (
    <DialogueFormulaire
      ouvert
      onOuvert={(o) => !o && fermer()}
      titre="Imposer un pseudonyme"
      description={`Pseudonyme actuel : ${actuel}. Le nouveau suit les mêmes règles qu'à l'inscription.`}
      bouton="Imposer"
      onEnvoie={async () => {
        await imposerPseudonyme(inscrit.id, pseudonyme, motif);
        await router.invalidate();
      }}
    >
      <Champ libelle="Nouveau pseudonyme">
        <input
          required
          value={pseudonyme}
          onChange={(e) => setPseudonyme(e.target.value)}
          minLength={3}
          maxLength={30}
          className={CHAMP_ADMIN}
        />
      </Champ>
      <Champ libelle="Motif (inscrit au journal)">
        <Textarea
          required
          value={motif}
          onChange={(e) => setMotif(e.target.value)}
          minLength={3}
          maxLength={500}
          rows={3}
          className="font-medium"
        />
      </Champ>
    </DialogueFormulaire>
  );
}

function RegistrePoints({ points }: { points: ResumePoints }) {
  return (
    <>
      <h3 className="mt-8 text-sm font-extrabold uppercase tracking-wider text-muted-foreground">
        Registre des points
      </h3>
      {points.lignes.length === 0 ? (
        <p className="mt-2 text-sm font-medium text-muted-foreground">Aucune ligne.</p>
      ) : (
        <ol className="mt-2 divide-y text-sm">
          {points.lignes.map((ligne, rang) => (
            <li key={rang} className="flex items-center justify-between gap-4 py-2.5">
              <span className="min-w-0">
                <span className="font-bold">{ligne.libelle}</span>
                <span className="block text-muted-foreground">
                  {dateHeure(ligne.cree_le)} · {ligne.semestre ?? "hors semestre"}
                </span>
              </span>
              <span className="shrink-0 font-extrabold tabular-nums text-primary">
                {ligne.montant > 0 ? `+${ligne.montant}` : ligne.montant}
              </span>
            </li>
          ))}
        </ol>
      )}
    </>
  );
}

// Profil d'encadreur (spec 018) : fonction, établissement, vérification et registre des points.
function SectionEncadreur({ encadreur }: { encadreur: ProfilEncadreurAdmin }) {
  const { admin } = Route.useRouteContext();
  const champs: [string, React.ReactNode][] = [
    ["Vérification", LIBELLES_VERIFICATION[encadreur.etat]],
    ["Fonction", libelleFonction(encadreur.fonction, encadreur.fonction_precision)],
    ["Discipline", encadreur.discipline ?? "—"],
    ["Ville", encadreur.etablissement.localite ?? "—"],
    [
      "Établissement",
      <>
        {encadreur.etablissement.nom}
        {encadreur.etablissement.statut !== "actif" && (
          <span className="ml-2 rounded-full bg-sun/30 px-2 py-0.5 text-xs font-extrabold">
            {encadreur.etablissement.statut === "propose" ? "Proposé" : "Désactivé"}
          </span>
        )}
      </>,
    ],
    ["IESG et DRE", `${encadreur.etablissement.iesg} · ${encadreur.etablissement.dre}`],
    ["Demande", dateHeure(encadreur.demande_le)],
    [
      "Décision",
      encadreur.decide_le
        ? `${dateHeure(encadreur.decide_le)}${encadreur.decide_par ? ` · ${encadreur.decide_par}` : ""}`
        : "En attente",
    ],
    ["Charte acceptée", encadreur.charte_version],
    [
      "Points",
      `${encadreur.points.points_semestre} ce semestre · ${encadreur.points.total} au total`,
    ],
  ];

  return (
    <section className="rounded-3xl bg-white p-6 shadow-sm ring-1 ring-border md:p-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <h2 className="text-xl text-logo-blue">Profil d'encadreur</h2>
        {encadreur.etat === "en_attente" && peut(admin, "encadreurs", "consulter") && (
          <Link
            to="/admin/encadreurs"
            className="rounded-full px-4 py-2 text-sm font-bold text-logo-blue ring-1 ring-border hover:ring-night/30"
          >
            Voir la file de vérification
          </Link>
        )}
      </div>
      {encadreur.motif_refus && (
        <p className="mt-4 rounded-2xl bg-logo-red/10 px-4 py-3 text-sm font-semibold text-ink">
          Motif du refus : {encadreur.motif_refus}
        </p>
      )}
      <dl className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {champs.map(([libelle, valeur]) => (
          <div key={libelle} className="flex flex-col-reverse">
            <dd className="mt-0.5 font-semibold">{valeur}</dd>
            <dt className="text-xs font-extrabold uppercase tracking-wider text-muted-foreground">
              {libelle}
            </dt>
          </div>
        ))}
      </dl>
      <RegistrePoints points={encadreur.points} />
    </section>
  );
}

const SEXES_FICHE = { feminin: "Féminin", masculin: "Masculin" } as const;
const RESEAUX_FICHE = {
  facebook: "Facebook",
  tiktok: "TikTok",
  instagram: "Instagram",
  autre: "Autre",
} as const;

// La fiche d'adhésion (spec 030) : données personnelles d'un mineur. Elle n'est chargée qu'à la demande,
// car chaque lecture est inscrite au journal d'audit.
function SectionFiche({ id }: { id: string }) {
  const [fiche, setFiche] = useState<FicheSortie | null>(null);
  const [erreur, setErreur] = useState<string | null>(null);
  const [enCours, setEnCours] = useState(false);

  const afficher = async () => {
    setErreur(null);
    setEnCours(true);
    try {
      setFiche(await adminVoirFicheEleve(id));
    } catch (e) {
      setErreur(
        e instanceof ErreurApi && e.statut === 404
          ? "Fiche introuvable : pas encore remplie, ou hors de ton périmètre."
          : e instanceof ErreurApi
            ? e.message
            : MESSAGE_INDISPONIBLE,
      );
    } finally {
      setEnCours(false);
    }
  };

  const parent = (p: FicheSortie["pere"]) =>
    p ? [p.nom, p.profession, p.telephone].filter(Boolean).join(" · ") : "—";
  const champs: [string, string][] = fiche
    ? [
        ["Année scolaire", fiche.annee_scolaire],
        ["N° d'adhésion", fiche.numero_adhesion ?? "—"],
        [
          "Préfecture · commune · canton",
          [fiche.prefecture, fiche.commune, fiche.canton].filter(Boolean).join(" · ") || "—",
        ],
        ["Sexe", fiche.sexe ? SEXES_FICHE[fiche.sexe] : "—"],
        [
          "Naissance",
          `${fiche.date_naissance ? dateCourte(fiche.date_naissance) : "—"} à ${fiche.lieu_naissance ?? "—"}`,
        ],
        ["Contact de l'élève", fiche.telephone ?? "—"],
        ["Père", parent(fiche.pere)],
        ["Mère", parent(fiche.mere)],
        [
          "Parent ou tuteur responsable",
          fiche.responsable ? `${fiche.responsable.nom} · ${fiche.responsable.telephone}` : "—",
        ],
        ["Axes choisis", fiche.axes.join(", ") || "—"],
        [
          "Années antérieures",
          fiche.parcours
            .map((p) => `${p.annee} : ${p.etablissement}${p.iesg ? ` (${p.iesg})` : ""}`)
            .join(" ; ") || "—",
        ],
        [
          "Réseaux sociaux",
          fiche.reseaux
            .map((r) => (r === "autre" ? (fiche.reseau_autre ?? "Autre") : RESEAUX_FICHE[r]))
            .join(", ") || "—",
        ],
        ["Engagement", fiche.engagement_le ? dateCourte(fiche.engagement_le) : "—"],
      ]
    : [];

  return (
    <section className="rounded-3xl bg-white p-6 shadow-sm ring-1 ring-border md:p-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <h2 className="text-xl text-logo-blue">Fiche d'adhésion</h2>
        {!fiche && (
          <Button variant="outline" onClick={() => void afficher()} disabled={enCours}>
            {enCours ? (
              <Loader2 className="size-4 animate-spin" />
            ) : (
              <ClipboardList className="size-4" />
            )}
            Afficher la fiche
          </Button>
        )}
      </div>
      <p className="mt-2 text-sm font-medium text-muted-foreground">
        Données personnelles d'un élève : chaque consultation est inscrite au journal d'audit.
      </p>
      {erreur && (
        <p role="alert" className="mt-4 text-sm font-semibold text-destructive">
          {erreur}
        </p>
      )}
      {fiche && (
        <dl className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {champs.map(([libelle, valeur]) => (
            <div key={libelle} className="flex flex-col-reverse">
              <dd className="mt-0.5 break-words font-semibold">{valeur}</dd>
              <dt className="text-xs font-extrabold uppercase tracking-wider text-muted-foreground">
                {libelle}
              </dt>
            </div>
          ))}
        </dl>
      )}
    </section>
  );
}
