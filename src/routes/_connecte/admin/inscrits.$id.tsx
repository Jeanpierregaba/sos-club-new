import { createFileRoute, Link, useRouter } from "@tanstack/react-router";
import { ArrowLeft, Pause, Play } from "lucide-react";
import { useState } from "react";

import { BadgeStatut } from "@/components/admin/BadgeStatut";
import { DialogueMotif } from "@/components/admin/DialogueMotif";
import { ServiceIndisponible } from "@/components/ServiceIndisponible";
import { Button } from "@/components/ui/button";
import { ACTIONS_JOURNAL, PROFILS, dateCourte, dateHeure, peut } from "@/lib/admin";
import { chargerInscrit, changerStatutInscrit } from "@/lib/api/client";

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

      <section className="rounded-3xl bg-white p-6 shadow-sm ring-1 ring-border">
        <h2 className="text-xl text-logo-blue">Historique du statut</h2>
        {inscrit.historique.length === 0 ? (
          <p className="mt-2 text-sm font-medium text-muted-foreground">
            Aucun changement de statut.
          </p>
        ) : (
          <ol className="mt-3 divide-y">
            {inscrit.historique.map((e) => (
              <li key={e.id} className="py-3 text-sm">
                <p className="font-bold">
                  {ACTIONS_JOURNAL[e.action] ?? e.action}
                  <span className="font-medium text-muted-foreground"> · {dateHeure(e.quand)}</span>
                </p>
                <p className="text-muted-foreground">
                  Par {e.auteur_libelle ?? "—"} · Motif : {String(e.details["motif"] ?? "—")}
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
