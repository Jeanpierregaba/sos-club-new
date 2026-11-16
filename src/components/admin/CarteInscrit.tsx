import { useRouter } from "@tanstack/react-router";
import { BadgeCheck, Pause, Play, ShieldAlert } from "lucide-react";
import { useState } from "react";

import { DialogueMotif } from "@/components/admin/DialogueMotif";
import { Button } from "@/components/ui/button";
import { reactiverCarte, suspendreCarte, type CarteAdmin } from "@/lib/api/client";
import { CAUSES_ADMIN, TYPES_CARTE } from "@/lib/cartes";
import { dateCourte, dateHeure } from "@/lib/dates";

const EVENEMENTS: Record<CarteAdmin["historique"][number]["action"], string> = {
  carte_delivree: "Carte délivrée",
  carte_suspendue: "Suspendue par l'équipe",
  carte_reactivee: "Réactivée par l'équipe",
};

// La carte numérique dans la fiche d'un inscrit (spec 040) : statut, cause, historique, et la suspension ou la
// réactivation par l'équipe, toujours motivée (10 à 200 caractères).
export function CarteInscrit({
  utilisateurId,
  carte,
  gerable,
}: {
  utilisateurId: string;
  carte: CarteAdmin;
  gerable: boolean;
}) {
  const router = useRouter();
  const [dialogue, setDialogue] = useState(false);
  const suspendue = carte.suspendue_le !== null;
  return (
    <section
      aria-label="Carte numérique"
      className="rounded-3xl bg-white p-6 shadow-sm ring-1 ring-border md:p-8"
    >
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2 className="text-xl text-logo-blue">{TYPES_CARTE[carte.type]}</h2>
          <p className="mt-1 font-mono font-bold">{carte.numero}</p>
        </div>
        <p
          className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-sm font-bold ${
            carte.valide ? "bg-primary/15 text-primary" : "bg-logo-red/10 text-logo-red"
          }`}
        >
          {carte.valide ? (
            <BadgeCheck aria-hidden className="size-4" />
          ) : (
            <ShieldAlert aria-hidden className="size-4" />
          )}
          {carte.valide ? "Valide" : `Non valide · ${carte.cause ? CAUSES_ADMIN[carte.cause] : ""}`}
        </p>
      </div>
      <dl className="mt-4 grid gap-4 text-sm sm:grid-cols-3">
        <div>
          <dt className="text-xs font-extrabold uppercase tracking-wider text-muted-foreground">
            Club
          </dt>
          <dd className="font-semibold">{carte.club ?? "Non affilié"}</dd>
        </div>
        <div>
          <dt className="text-xs font-extrabold uppercase tracking-wider text-muted-foreground">
            Délivrée le
          </dt>
          <dd className="font-semibold">{dateCourte(carte.delivree_le)}</dd>
        </div>
        {carte.motif_suspension && (
          <div>
            <dt className="text-xs font-extrabold uppercase tracking-wider text-muted-foreground">
              Motif de la suspension
            </dt>
            <dd className="font-semibold">{carte.motif_suspension}</dd>
          </div>
        )}
      </dl>
      <ol className="mt-4 divide-y text-sm">
        {carte.historique.map((e) => (
          <li key={`${e.action}-${e.le}`} className="py-2">
            <span className="font-bold">{EVENEMENTS[e.action]}</span>
            <span className="text-muted-foreground"> · {dateHeure(e.le)}</span>
            {e.motif && <span className="block text-muted-foreground">Motif : {e.motif}</span>}
          </li>
        ))}
      </ol>
      {gerable && (
        <Button
          variant="outline"
          onClick={() => setDialogue(true)}
          className="mt-4 rounded-full font-bold"
        >
          {suspendue ? <Play className="size-4" /> : <Pause className="size-4" />}
          {suspendue ? "Réactiver la carte" : "Suspendre la carte"}
        </Button>
      )}
      <DialogueMotif
        ouvert={dialogue}
        onOuvert={setDialogue}
        titre={suspendue ? "Réactiver cette carte" : "Suspendre cette carte"}
        description={
          suspendue
            ? "La carte redevient valide si rien d'autre ne l'en empêche. Le titulaire est prévenu."
            : "La carte apparaît « Non valide » à toute vérification, jusqu'à ce que l'équipe la réactive. Le titulaire est prévenu, sans ton nom."
        }
        bouton={suspendue ? "Réactiver" : "Suspendre"}
        danger={!suspendue}
        longueurMin={10}
        longueurMax={200}
        onConfirme={async (motif) => {
          await (suspendue ? reactiverCarte : suspendreCarte)(utilisateurId, motif);
          await router.invalidate();
        }}
      />
    </section>
  );
}
