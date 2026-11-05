import { createFileRoute, Link, redirect, useRouter } from "@tanstack/react-router";
import { Check, Crown, Mail, MapPin, Phone, Users, X } from "lucide-react";
import { useState } from "react";

import { DialogueFormulaire } from "@/components/admin/DialogueFormulaire";
import { DialogueMotif } from "@/components/admin/DialogueMotif";
import { EnTeteAdmin } from "@/components/admin/EnTeteAdmin";
import { FileMembres } from "@/components/admin/FileMembres";
import { ServiceIndisponible } from "@/components/ServiceIndisponible";
import { Button } from "@/components/ui/button";
import { peut } from "@/lib/admin";
import {
  adminActiverClub,
  adminFileAffiliations,
  adminFileClubs,
  adminFilePassations,
  adminFileRattachements,
  adminRefuserClub,
  adminRefuserPassation,
  adminValiderPassation,
  chargerAxes,
  type DemandeClub,
  type Passation,
} from "@/lib/api/client";
import { dateCourte } from "@/lib/dates";
import { libelleAxes, libellesDesAxes } from "@/lib/clubs";

type Onglet = "en_attente" | "refuse" | "passations" | "affiliations" | "rattachements";
const AUTRES_ONGLETS: Onglet[] = ["refuse", "passations", "affiliations", "rattachements"];

export const Route = createFileRoute("/_connecte/admin/clubs")({
  validateSearch: (search: Record<string, unknown>): { etat?: Onglet } =>
    AUTRES_ONGLETS.includes(search["etat"] as Onglet) ? { etat: search["etat"] as Onglet } : {},
  beforeLoad: ({ context }) => {
    if (!peut(context.admin, "clubs", "consulter")) throw redirect({ to: "/admin" });
  },
  loaderDeps: ({ search }) => ({ etat: search.etat ?? "en_attente" }),
  loader: async ({ deps }) => {
    const axes = await chargerAxes().catch(() => []);
    if (deps.etat === "passations") {
      return { axes, passations: await adminFilePassations() };
    }
    // Spec 020 : les affiliations et rattachements confirmés par un président.
    if (deps.etat === "affiliations") return { axes, affiliations: await adminFileAffiliations() };
    if (deps.etat === "rattachements")
      return { axes, rattachements: await adminFileRattachements() };
    return { axes, file: await adminFileClubs(deps.etat) };
  },
  gcTime: 0,
  errorComponent: ServiceIndisponible,
  component: Clubs,
});

const ONGLETS: { etat: Onglet; libelle: string }[] = [
  { etat: "en_attente", libelle: "À vérifier" },
  { etat: "refuse", libelle: "Refusés" },
  { etat: "passations", libelle: "Passations" },
  { etat: "affiliations", libelle: "Affiliations" },
  { etat: "rattachements", libelle: "Rattachements" },
];

function Clubs() {
  const { admin, catalogue } = Route.useRouteContext();
  const donnees = Route.useLoaderData();
  const { axes } = donnees;
  const { etat = "en_attente" } = Route.useSearch();
  const decideur = peut(admin, "clubs", "approuver");
  const libelles = libellesDesAxes(axes);
  const [activation, setActivation] = useState<DemandeClub | null>(null);
  const [refus, setRefus] = useState<DemandeClub | null>(null);
  const [validation, setValidation] = useState<Passation | null>(null);
  const [refusPassation, setRefusPassation] = useState<Passation | null>(null);
  const router = useRouter();

  const total =
    "passations" in donnees
      ? donnees.passations.total
      : "affiliations" in donnees
        ? donnees.affiliations.total
        : "rattachements" in donnees
          ? donnees.rattachements.total
          : donnees.file.total;

  return (
    <div className="space-y-6">
      <EnTeteAdmin sur="Clubs Santé" bleu="Clubs" vert="à valider">
        Vérifie le nom du club, son établissement et le demandeur avant d'activer. Une passation
        change le président du club, jamais le compte des élèves. Les affiliations et les
        rattachements arrivent ici une fois confirmés par le président du club.
        {admin.perimetre_dre &&
          ` Tu vois les demandes de la DRE ${catalogue.dre[admin.perimetre_dre]}.`}
      </EnTeteAdmin>

      <nav aria-label="File des clubs" className="flex flex-wrap gap-2">
        {ONGLETS.map((o) => (
          <Link
            key={o.etat}
            to="/admin/clubs"
            search={o.etat === "en_attente" ? {} : { etat: o.etat }}
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

      {"affiliations" in donnees ? (
        <FileMembres
          type="affiliations"
          demandes={donnees.affiliations.demandes}
          decideur={decideur}
          onRafraichir={() => router.invalidate()}
        />
      ) : "rattachements" in donnees ? (
        <FileMembres
          type="rattachements"
          demandes={donnees.rattachements.demandes}
          decideur={decideur}
          onRafraichir={() => router.invalidate()}
        />
      ) : etat === "passations" && "passations" in donnees ? (
        <Passations
          passations={donnees.passations}
          decideur={decideur}
          onValider={setValidation}
          onRefuser={setRefusPassation}
        />
      ) : "file" in donnees ? (
        <Demandes
          file={donnees.file}
          etat={etat}
          libelles={libelles}
          decideur={decideur}
          onActiver={setActivation}
          onRefuser={setRefus}
        />
      ) : null}

      <DialogueFormulaire
        ouvert={activation !== null}
        onOuvert={(o) => !o && setActivation(null)}
        titre="Activer ce club ?"
        description={
          activation &&
          `« ${activation.nom} » à ${activation.etablissement.nom}. ${activation.demandeur_pseudonyme} devient président du club et le club apparaît sur la carte publique.`
        }
        bouton="Activer"
        onEnvoie={async () => {
          if (!activation) return;
          await adminActiverClub(activation.id, activation.version);
          await router.invalidate();
        }}
      />
      <DialogueMotif
        ouvert={refus !== null}
        onOuvert={(o) => !o && setRefus(null)}
        titre="Refuser cette demande de club ?"
        description={
          refus &&
          `${refus.demandeur_pseudonyme} lira ce motif dans son espace et pourra renvoyer sa demande.`
        }
        bouton="Refuser"
        danger
        onConfirme={async (motif) => {
          if (!refus) return;
          await adminRefuserClub(refus.id, refus.version, motif);
          await router.invalidate();
        }}
      />
      <DialogueFormulaire
        ouvert={validation !== null}
        onOuvert={(o) => !o && setValidation(null)}
        titre="Valider cette passation ?"
        description={
          validation &&
          `${validation.successeur_pseudonyme} devient président de « ${validation.club_nom} ». ${validation.president_sortant_pseudonyme} perd la gestion du club.`
        }
        bouton="Valider la passation"
        onEnvoie={async () => {
          if (!validation) return;
          await adminValiderPassation(validation.id, validation.version);
          await router.invalidate();
        }}
      />
      <DialogueMotif
        ouvert={refusPassation !== null}
        onOuvert={(o) => !o && setRefusPassation(null)}
        titre="Refuser cette passation ?"
        description={
          refusPassation &&
          `${refusPassation.president_sortant_pseudonyme} reste président de « ${refusPassation.club_nom} » et lira ce motif.`
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

function Demandes({
  file,
  etat,
  libelles,
  decideur,
  onActiver,
  onRefuser,
}: {
  file: Awaited<ReturnType<typeof adminFileClubs>>;
  etat: Onglet;
  libelles: Map<string, string>;
  decideur: boolean;
  onActiver: (demande: DemandeClub) => void;
  onRefuser: (demande: DemandeClub) => void;
}) {
  if (file.demandes.length === 0) {
    return (
      <p className="rounded-3xl bg-white p-6 font-medium text-muted-foreground ring-1 ring-border">
        {etat === "en_attente" ? "Aucune demande de club à vérifier." : "Aucun club refusé."}
      </p>
    );
  }

  return (
    <>
      {file.total > file.demandes.length && (
        <p className="text-sm font-semibold text-muted-foreground">
          Les {file.demandes.length} demandes les{" "}
          {etat === "en_attente" ? "plus anciennes" : "plus récentes"} sont affichées sur{" "}
          {file.total}.
        </p>
      )}
      <ul className="grid gap-3">
        {file.demandes.map((d) => (
          <li key={d.id} className="rounded-3xl bg-white p-5 shadow-sm ring-1 ring-border">
            <div className="flex flex-wrap items-start gap-4">
              <div className="min-w-0 flex-1 space-y-2">
                <div>
                  <p className="text-lg font-extrabold text-logo-blue">{d.nom}</p>
                  <p className="text-sm font-semibold text-ink">
                    {d.etablissement.nom}
                    {d.etablissement.statut === "propose" && (
                      <span className="ml-2 rounded-full bg-sun/30 px-2 py-0.5 text-xs font-extrabold">
                        Proposé
                      </span>
                    )}
                    <span className="block font-medium text-muted-foreground">
                      {d.etablissement.iesg} · {d.etablissement.dre}
                    </span>
                  </p>
                </div>
                <p className="text-sm font-semibold text-ink">
                  Demandeur : {d.demandeur_pseudonyme}
                  <span className="block text-xs font-medium text-muted-foreground">
                    Demande du {dateCourte(d.demande_le)}
                  </span>
                </p>
                {d.description && (
                  <p className="text-sm font-medium text-ink/80">{d.description}</p>
                )}
                {d.axes.length > 0 && (
                  <p className="flex flex-wrap gap-1.5">
                    {d.axes.map((code) => (
                      <span
                        key={code}
                        className="rounded-full bg-mist-soft px-2.5 py-0.5 text-xs font-bold text-ink"
                      >
                        {libelleAxes([code], libelles)}
                      </span>
                    ))}
                  </p>
                )}
                {d.encadreurs_associes.length > 0 && (
                  <div className="rounded-2xl bg-mist-soft p-3">
                    <p className="flex items-center gap-1.5 text-xs font-extrabold uppercase tracking-wide text-muted-foreground">
                      <Users aria-hidden className="size-3.5" /> Encadreurs associés (déclaratif)
                    </p>
                    <ul className="mt-2 grid gap-1 text-sm font-semibold text-ink">
                      {d.encadreurs_associes.map((personne, index) => (
                        <li key={index} className="flex flex-wrap items-baseline gap-x-3">
                          <span>{personne.nom}</span>
                          {personne.email && (
                            <a
                              href={`mailto:${personne.email}`}
                              className="inline-flex items-center gap-1 text-logo-blue hover:underline"
                            >
                              <Mail aria-hidden className="size-3.5" /> {personne.email}
                            </a>
                          )}
                          {personne.telephone && (
                            <a
                              href={`tel:${personne.telephone}`}
                              className="inline-flex items-center gap-1 text-logo-blue hover:underline"
                            >
                              <Phone aria-hidden className="size-3.5" /> {personne.telephone}
                            </a>
                          )}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {d.motif_refus && (
                  <p className="rounded-2xl bg-logo-red/10 px-3 py-2 text-sm font-semibold text-ink">
                    Refusé{d.decide_le ? ` le ${dateCourte(d.decide_le)}` : ""} : {d.motif_refus}
                  </p>
                )}
              </div>
              {decideur && d.etat === "en_attente" && (
                <div className="flex w-full flex-wrap gap-2 sm:w-auto">
                  <Button
                    onClick={() => onActiver(d)}
                    className="flex-1 rounded-full font-bold sm:flex-none"
                  >
                    <Check className="size-4" /> Activer
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => onRefuser(d)}
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
                  De <strong>{p.president_sortant_pseudonyme}</strong> vers{" "}
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
