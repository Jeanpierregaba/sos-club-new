import { createFileRoute, Link, redirect, useRouter } from "@tanstack/react-router";
import { Check, Crown, MapPin, Search, X } from "lucide-react";
import { useState } from "react";

import { DialogueFormulaire } from "@/components/admin/DialogueFormulaire";
import { DialogueMotif } from "@/components/admin/DialogueMotif";
import { EnTeteAdmin } from "@/components/admin/EnTeteAdmin";
import { FileMembres } from "@/components/admin/FileMembres";
import { SuiviClubs } from "@/components/admin/SuiviClubs";
import { ServiceIndisponible } from "@/components/ServiceIndisponible";
import { Button } from "@/components/ui/button";
import { peut } from "@/lib/admin";
import {
  adminDeciderDesistement,
  adminFileAffiliations,
  adminFileDesistements,
  adminFilePassations,
  adminRefuserPassation,
  adminSeuilsClubs,
  adminSuiviClubs,
  adminValiderPassation,
  type FileDesistements,
  type Passation,
  type RegionScolaire,
  type SignalementAdmin,
  type StatutClub,
} from "@/lib/api/client";
import { dateCourte } from "@/lib/dates";

type Onglet = "suivi" | "desistements" | "affiliations" | "passations";
const AUTRES_ONGLETS: Onglet[] = ["desistements", "affiliations", "passations"];
const STATUTS: StatutClub[] = ["en_constitution", "actif", "en_regularisation", "suspendu"];
const REGIONS: RegionScolaire[] = ["maritime", "plateaux", "centrale", "kara", "savanes"];

type Recherche = {
  etat?: Onglet;
  statut?: StatutClub;
  region?: RegionScolaire;
  q?: string;
  page?: number;
};

const texte = (v: unknown) =>
  typeof v === "string" && v.trim() ? v.trim().slice(0, 100) : undefined;

export const Route = createFileRoute("/_connecte/admin/clubs")({
  validateSearch: (search: Record<string, unknown>): Recherche => {
    const resultat: Recherche = {};
    if (AUTRES_ONGLETS.includes(search["etat"] as Onglet)) resultat.etat = search["etat"] as Onglet;
    if (STATUTS.includes(search["statut"] as StatutClub))
      resultat.statut = search["statut"] as StatutClub;
    if (REGIONS.includes(search["region"] as RegionScolaire))
      resultat.region = search["region"] as RegionScolaire;
    const q = texte(search["q"]);
    if (q) resultat.q = q;
    const page = Number(search["page"]);
    if (Number.isInteger(page) && page > 1) resultat.page = page;
    return resultat;
  },
  beforeLoad: ({ context }) => {
    if (!peut(context.admin, "clubs", "consulter")) throw redirect({ to: "/admin" });
  },
  loaderDeps: ({ search }) => search,
  loader: async ({ deps }) => {
    const etat = deps.etat ?? "suivi";
    if (etat === "passations") return { passations: await adminFilePassations() };
    if (etat === "affiliations") return { affiliations: await adminFileAffiliations() };
    if (etat === "desistements") return { desistements: await adminFileDesistements() };
    const [page, seuils] = await Promise.all([
      adminSuiviClubs({
        statut: deps.statut,
        region: deps.region,
        recherche: deps.q,
        page: deps.page,
      }),
      adminSeuilsClubs(),
    ]);
    return { suivi: { page, seuils } };
  },
  gcTime: 0,
  errorComponent: ServiceIndisponible,
  component: Clubs,
});

const ONGLETS: { etat: Onglet; libelle: string }[] = [
  { etat: "suivi", libelle: "Suivi des clubs" },
  { etat: "desistements", libelle: "Désistements" },
  { etat: "affiliations", libelle: "Affiliations" },
  { etat: "passations", libelle: "Présidents" },
];

function Clubs() {
  const { admin, catalogue } = Route.useRouteContext();
  const donnees = Route.useLoaderData();
  const recherche = Route.useSearch();
  const etat = recherche.etat ?? "suivi";
  const decideur = peut(admin, "clubs", "approuver");
  const [validation, setValidation] = useState<Passation | null>(null);
  const [refusPassation, setRefusPassation] = useState<Passation | null>(null);
  const router = useRouter();

  const total =
    "passations" in donnees
      ? donnees.passations.total
      : "affiliations" in donnees
        ? donnees.affiliations.total
        : "desistements" in donnees
          ? donnees.desistements.total
          : donnees.suivi.page.total;

  return (
    <div className="space-y-6">
      <EnTeteAdmin sur="Clubs Santé" bleu="Suivi" vert="des clubs">
        Un club s'active tout seul dès qu'il réunit 3 encadreurs et 21 élèves confirmés, et passe en
        régularisation pour 15 jours s'il descend sous ce seuil. Ici, tu suis les statuts, tu
        confirmes les désistements signalés par les encadreurs, tu confirmes les élèves sans
        encadreur et tu valides les présidents.
        {admin.perimetre_dre &&
          ` Tu vois les clubs de la DRE ${catalogue.dre[admin.perimetre_dre]}.`}
      </EnTeteAdmin>

      <nav aria-label="Rubriques des clubs" className="flex flex-wrap gap-2">
        {ONGLETS.map((o) => (
          <Link
            key={o.etat}
            to="/admin/clubs"
            search={o.etat === "suivi" ? {} : { etat: o.etat }}
            className={`rounded-full px-4 py-2 text-sm font-bold ring-1 transition ${
              etat === o.etat
                ? "bg-night text-white ring-night"
                : "bg-white ring-border hover:ring-night/30"
            }`}
          >
            {o.libelle}
            {etat === o.etat && ` (${total})`}
          </Link>
        ))}
      </nav>

      {"suivi" in donnees ? (
        <SuiviClubs
          page={donnees.suivi.page}
          seuils={donnees.suivi.seuils}
          filtres={recherche}
          decideur={decideur}
        />
      ) : "affiliations" in donnees ? (
        <FileMembres
          demandes={donnees.affiliations.demandes}
          decideur={decideur}
          onRafraichir={() => router.invalidate()}
        />
      ) : "desistements" in donnees ? (
        <Desistements
          file={donnees.desistements}
          decideur={decideur}
          onRafraichir={() => router.invalidate()}
        />
      ) : (
        <Passations
          passations={donnees.passations}
          decideur={decideur}
          onValider={setValidation}
          onRefuser={setRefusPassation}
        />
      )}

      <DialogueFormulaire
        ouvert={validation !== null}
        onOuvert={(o) => !o && setValidation(null)}
        titre="Valider ce président ?"
        description={
          validation &&
          (validation.president_sortant_pseudonyme
            ? `${validation.successeur_pseudonyme} devient président de « ${validation.club_nom} ». ${validation.president_sortant_pseudonyme} perd la gestion du club.`
            : `${validation.successeur_pseudonyme} devient le premier président de « ${validation.club_nom} ».`)
        }
        bouton="Valider"
        onEnvoie={async () => {
          if (!validation) return;
          await adminValiderPassation(validation.id, validation.version);
          await router.invalidate();
        }}
      />
      <DialogueMotif
        ouvert={refusPassation !== null}
        onOuvert={(o) => !o && setRefusPassation(null)}
        titre="Refuser cette proposition ?"
        description={
          refusPassation &&
          `La présidence de « ${refusPassation.club_nom} » ne change pas ; l'auteur de la proposition lira ce motif.`
        }
        bouton="Refuser"
        danger
        onConfirme={async (motif) => {
          if (!refusPassation) return;
          await adminRefuserPassation(refusPassation.id, refusPassation.version, motif);
          await router.invalidate();
        }}
      />
    </div>
  );
}

function Desistements({
  file,
  decideur,
  onRafraichir,
}: {
  file: FileDesistements;
  decideur: boolean;
  onRafraichir: () => Promise<unknown>;
}) {
  const [aConfirmer, setAConfirmer] = useState<SignalementAdmin | null>(null);
  const [aRejeter, setARejeter] = useState<SignalementAdmin | null>(null);

  if (file.signalements.length === 0)
    return (
      <p className="rounded-3xl bg-white p-6 font-medium text-muted-foreground ring-1 ring-border">
        Aucun désistement signalé n'attend ta décision.
      </p>
    );

  return (
    <>
      <ul className="grid gap-3">
        {file.signalements.map((s) => (
          <li key={s.id} className="rounded-3xl bg-white p-5 shadow-sm ring-1 ring-border">
            <div className="flex flex-wrap items-start gap-4">
              <div className="min-w-0 flex-1 space-y-1">
                <p className="text-lg font-extrabold text-logo-blue">
                  {s.encadreur_prenom} {s.encadreur_nom}
                </p>
                <p className="flex items-center gap-1.5 text-sm font-semibold text-ink">
                  <MapPin aria-hidden className="size-4" /> {s.club_nom}
                  <span className="font-medium text-muted-foreground">· DRE {s.dre}</span>
                </p>
                <p className="text-sm font-medium text-ink/80">« {s.motif} »</p>
                <p className="text-xs font-medium text-muted-foreground">
                  Signalé {s.signale_par ? `par ${s.signale_par} ` : ""}le{" "}
                  {dateCourte(s.signale_le)}
                </p>
              </div>
              {decideur && (
                <div className="flex w-full flex-wrap gap-2 sm:w-auto">
                  <Button
                    onClick={() => setAConfirmer(s)}
                    className="flex-1 rounded-full font-bold sm:flex-none"
                  >
                    <Check className="size-4" /> Confirmer le départ
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => setARejeter(s)}
                    className="flex-1 rounded-full font-bold sm:flex-none"
                  >
                    <X className="size-4" /> Rejeter
                  </Button>
                </div>
              )}
            </div>
          </li>
        ))}
      </ul>
      <DialogueFormulaire
        ouvert={aConfirmer !== null}
        onOuvert={(o) => !o && setAConfirmer(null)}
        titre="Confirmer ce départ ?"
        description={
          aConfirmer &&
          `${aConfirmer.encadreur_prenom} ${aConfirmer.encadreur_nom} ne fera plus partie de « ${aConfirmer.club_nom} ». Son compte et ses contributions restent. S'il manque un encadreur, le club entre en régularisation pour 15 jours.`
        }
        bouton="Confirmer"
        onEnvoie={async () => {
          if (!aConfirmer) return;
          await adminDeciderDesistement(aConfirmer.id, "confirmer", aConfirmer.version);
          await onRafraichir();
        }}
      />
      <DialogueMotif
        ouvert={aRejeter !== null}
        onOuvert={(o) => !o && setARejeter(null)}
        titre="Rejeter ce signalement ?"
        description="Rien ne change pour le club. L'encadreur qui a signalé lira ton motif ; l'encadreur visé n'est pas prévenu."
        bouton="Rejeter"
        danger
        onConfirme={async (motif) => {
          if (!aRejeter) return;
          await adminDeciderDesistement(aRejeter.id, "rejeter", aRejeter.version, motif);
          await onRafraichir();
        }}
      />
    </>
  );
}

function Passations({
  passations,
  decideur,
  onValider,
  onRefuser,
}: {
  passations: Awaited<ReturnType<typeof adminFilePassations>>;
  decideur: boolean;
  onValider: (passation: Passation) => void;
  onRefuser: (passation: Passation) => void;
}) {
  if (passations.passations.length === 0) {
    return (
      <p className="rounded-3xl bg-white p-6 font-medium text-muted-foreground ring-1 ring-border">
        Aucune passation en attente.
      </p>
    );
  }

  return (
    <>
      {passations.total > passations.passations.length && (
        <p className="text-sm font-semibold text-muted-foreground">
          Les {passations.passations.length} passations les plus anciennes sont affichées sur{" "}
          {passations.total}.
        </p>
      )}
      <ul className="grid gap-3">
        {passations.passations.map((p) => (
          <li key={p.id} className="rounded-3xl bg-white p-5 shadow-sm ring-1 ring-border">
            <div className="flex flex-wrap items-start gap-4">
              <div className="min-w-0 flex-1 space-y-1">
                <p className="flex items-center gap-2 text-lg font-extrabold text-logo-blue">
                  <Crown aria-hidden className="size-5" /> {p.club_nom}
                </p>
                <p className="flex items-center gap-1.5 text-sm font-semibold text-ink">
                  <MapPin aria-hidden className="size-4" /> {p.etablissement.nom}
                  <span className="font-medium text-muted-foreground">
                    · {p.etablissement.iesg} · {p.etablissement.dre}
                  </span>
                </p>
                <p className="text-sm font-semibold text-ink">
                  {p.president_sortant_pseudonyme ? (
                    <>
                      De <strong>{p.president_sortant_pseudonyme}</strong> vers{" "}
                    </>
                  ) : (
                    "Premier président, proposé par un encadreur : "
                  )}
                  <strong>{p.successeur_pseudonyme}</strong>
                  <span className="block text-xs font-medium text-muted-foreground">
                    Proposée le {dateCourte(p.propose_le)}
                  </span>
                </p>
              </div>
              {decideur && p.etat === "en_attente" && (
                <div className="flex w-full flex-wrap gap-2 sm:w-auto">
                  <Button
                    onClick={() => onValider(p)}
                    className="flex-1 rounded-full font-bold sm:flex-none"
                  >
                    <Check className="size-4" /> Valider
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => onRefuser(p)}
                    className="flex-1 rounded-full font-bold sm:flex-none"
                  >
                    <X className="size-4" /> Refuser
                  </Button>
                </div>
              )}
            </div>
          </li>
        ))}
      </ul>
    </>
  );
}
