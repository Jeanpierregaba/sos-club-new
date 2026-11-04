import { createFileRoute, Link, redirect, useRouter } from "@tanstack/react-router";
import { Check, Mail, Phone, X } from "lucide-react";
import { useState } from "react";

import { DialogueFormulaire } from "@/components/admin/DialogueFormulaire";
import { DialogueMotif } from "@/components/admin/DialogueMotif";
import { EnTeteAdmin } from "@/components/admin/EnTeteAdmin";
import { ServiceIndisponible } from "@/components/ServiceIndisponible";
import { Button } from "@/components/ui/button";
import { peut, peutVoirInscrits } from "@/lib/admin";
import {
  adminActiverEncadreur,
  adminFileEncadreurs,
  adminRefuserEncadreur,
  type DemandeEncadreur,
} from "@/lib/api/client";
import { dateCourte } from "@/lib/dates";
import { libelleFonction } from "@/lib/fonctions";

type Onglet = "en_attente" | "refuse";

export const Route = createFileRoute("/_connecte/admin/encadreurs")({
  validateSearch: (search: Record<string, unknown>): { etat?: Onglet } =>
    search["etat"] === "refuse" ? { etat: "refuse" } : {},
  beforeLoad: ({ context }) => {
    if (!peut(context.admin, "encadreurs", "consulter")) throw redirect({ to: "/admin" });
  },
  loaderDeps: ({ search }) => ({ etat: search.etat ?? "en_attente" }),
  loader: ({ deps }) => adminFileEncadreurs(deps.etat),
  gcTime: 0,
  errorComponent: ServiceIndisponible,
  component: Encadreurs,
});

const ONGLETS: { etat: Onglet; libelle: string }[] = [
  { etat: "en_attente", libelle: "À vérifier" },
  { etat: "refuse", libelle: "Refusés" },
];

function Encadreurs() {
  const { admin, catalogue } = Route.useRouteContext();
  const file = Route.useLoaderData();
  const { etat = "en_attente" } = Route.useSearch();
  const decideur = peut(admin, "encadreurs", "approuver");
  const [activation, setActivation] = useState<DemandeEncadreur | null>(null);
  const [refus, setRefus] = useState<DemandeEncadreur | null>(null);
  const router = useRouter();

  return (
    <div className="space-y-6">
      <EnTeteAdmin sur="Comptes encadreurs" bleu="Encadreurs" vert="à vérifier">
        Vérifie le nom, la fonction et l'établissement de chaque personne avant d'activer son
        compte. L'activation crédite ses points de bienvenue.
        {admin.perimetre_dre &&
          ` Tu vois les demandes de la DRE ${catalogue.dre[admin.perimetre_dre]}.`}
      </EnTeteAdmin>

      <nav aria-label="Demandes" className="flex flex-wrap gap-2">
        {ONGLETS.map((o) => (
          <Link
            key={o.etat}
            to="/admin/encadreurs"
            search={o.etat === "en_attente" ? {} : { etat: o.etat }}
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

      {file.total > file.demandes.length && (
        <p className="text-sm font-semibold text-muted-foreground">
          Les {file.demandes.length} demandes les{" "}
          {etat === "en_attente" ? "plus anciennes" : "plus récentes"} sont affichées sur{" "}
          {file.total}.
        </p>
      )}

      {file.demandes.length === 0 ? (
        <p className="rounded-3xl bg-white p-6 font-medium text-muted-foreground ring-1 ring-border">
          {etat === "en_attente"
            ? "Aucune demande à vérifier pour l'instant."
            : "Aucune demande refusée."}
        </p>
      ) : (
        <ul className="grid gap-3">
          {file.demandes.map((d) => (
            <li key={d.id} className="rounded-3xl bg-white p-5 shadow-sm ring-1 ring-border">
              <div className="flex flex-wrap items-start gap-4">
                <div className="min-w-0 flex-1 space-y-1">
                  <p className="text-lg font-extrabold text-logo-blue">
                    {peutVoirInscrits(admin) ? (
                      <Link
                        to="/admin/inscrits/$id"
                        params={{ id: d.id }}
                        className="underline-offset-4 hover:underline"
                      >
                        {d.prenom} {d.nom}
                      </Link>
                    ) : (
                      `${d.prenom} ${d.nom}`
                    )}
                  </p>
                  <p className="font-semibold text-ink">
                    {libelleFonction(d.fonction, d.fonction_precision)}
                  </p>
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
                  <p className="flex flex-wrap gap-x-4 gap-y-1 pt-1 text-sm font-semibold">
                    {d.email && (
                      <a
                        href={`mailto:${d.email}`}
                        className="inline-flex min-w-0 items-center gap-1.5 break-all text-logo-blue hover:underline"
                      >
                        <Mail aria-hidden className="size-4 shrink-0" /> {d.email}
                      </a>
                    )}
                    {d.telephone && (
                      <a
                        href={`tel:${d.telephone}`}
                        className="inline-flex items-center gap-1.5 text-logo-blue hover:underline"
                      >
                        <Phone aria-hidden className="size-4 shrink-0" /> {d.telephone}
                      </a>
                    )}
                  </p>
                  <p className="text-xs font-semibold text-muted-foreground">
                    Demande du {dateCourte(d.demande_le)} · identifiant {d.identifiant}
                  </p>
                  {d.motif_refus && (
                    <p className="mt-2 rounded-2xl bg-logo-red/10 px-3 py-2 text-sm font-semibold text-ink">
                      Refusé{d.decide_le ? ` le ${dateCourte(d.decide_le)}` : ""} : {d.motif_refus}
                    </p>
                  )}
                </div>
                {decideur && d.etat === "en_attente" && (
                  <div className="flex w-full flex-wrap gap-2 sm:w-auto">
                    <Button
                      onClick={() => setActivation(d)}
                      className="flex-1 rounded-full font-bold sm:flex-none"
                    >
                      <Check className="size-4" /> Activer
                    </Button>
                    <Button
                      variant="outline"
                      onClick={() => setRefus(d)}
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
      )}

      <DialogueFormulaire
        ouvert={activation !== null}
        onOuvert={(o) => !o && setActivation(null)}
        titre="Activer ce compte encadreur ?"
        description={
          activation &&
          `${activation.prenom} ${activation.nom}, ${activation.etablissement.nom}. Ses points de bienvenue sont crédités et un email lui est envoyé.`
        }
        bouton="Activer"
        onEnvoie={async () => {
          if (!activation) return;
          await adminActiverEncadreur(activation.id, activation.version);
          await router.invalidate();
        }}
      />
      <DialogueMotif
        ouvert={refus !== null}
        onOuvert={(o) => !o && setRefus(null)}
        titre="Refuser cette demande ?"
        description={
          refus &&
          `${refus.prenom} ${refus.nom} lira ce motif dans son espace et pourra corriger son profil avant de renvoyer sa demande.`
        }
        bouton="Refuser"
        danger
        onConfirme={async (motif) => {
          if (!refus) return;
          await adminRefuserEncadreur(refus.id, refus.version, motif);
          await router.invalidate();
        }}
      />
    </div>
  );
}
