import { createFileRoute, useRouter } from "@tanstack/react-router";
import { CalendarPlus, Lock } from "lucide-react";
import { useState } from "react";

import { CHAMP_ADMIN, Champ, DialogueFormulaire } from "@/components/admin/DialogueFormulaire";
import { ServiceIndisponible } from "@/components/ServiceIndisponible";
import { Button } from "@/components/ui/button";
import { peut } from "@/lib/admin";
import {
  adminCloturerAnnee,
  adminCreerAnnee,
  adminListerAnnees,
  type AnneeAdmin,
} from "@/lib/api/client";

export const Route = createFileRoute("/_connecte/admin/points/annees")({
  loader: () => adminListerAnnees(),
  gcTime: 0,
  errorComponent: ServiceIndisponible,
  component: Annees,
});

const jour = (iso: string) =>
  new Date(`${iso}T00:00:00Z`).toLocaleDateString("fr-FR", {
    day: "numeric",
    month: "long",
    year: "numeric",
    timeZone: "UTC",
  });

// Les années académiques (spec 034, lot 4) : septembre à juillet, dates fixées par l'équipe. Les compteurs annuels
// repartent de zéro à chaque année, sans rien effacer ; la clôture fige le classement régional annuel.
function Annees() {
  const { admin } = Route.useRouteContext();
  const annees = Route.useLoaderData();
  const modifiable = peut(admin, "points", "modifier") && admin.perimetre_dre === null;
  const [nouvelle, setNouvelle] = useState(false);
  const [aCloturer, setACloturer] = useState<AnneeAdmin | null>(null);

  return (
    <div className="space-y-5">
      <p className="max-w-3xl text-sm font-medium text-muted-foreground">
        Chaque point gagné est rattaché à l'année en cours. Une année se clôture une fois sa date de
        fin passée : cela fige son classement régional (pseudonyme et club seulement). Rien n'est
        jamais effacé.
      </p>
      {modifiable && (
        <Button
          onClick={() => setNouvelle(true)}
          className="btn-fx h-11 rounded-full px-5 font-bold"
        >
          <CalendarPlus className="size-4" /> Nouvelle année
        </Button>
      )}
      {annees.length === 0 ? (
        <p className="rounded-3xl bg-white p-6 font-medium text-muted-foreground ring-1 ring-border">
          Aucune année pour l'instant : les points comptent seulement dans le total des élèves.
        </p>
      ) : (
        <ul className="grid gap-3">
          {annees.map((a) => (
            <li
              key={a.id}
              className="flex flex-wrap items-center gap-4 rounded-3xl bg-white p-5 shadow-sm ring-1 ring-border"
            >
              <div className="min-w-0 flex-1">
                <p className="flex flex-wrap items-center gap-2 font-extrabold text-logo-blue">
                  {a.libelle}
                  {a.cloturee_le && (
                    <span className="rounded-full bg-mist-soft px-2.5 py-0.5 text-xs font-extrabold text-muted-foreground">
                      Clôturée le {jour(a.cloturee_le)}
                    </span>
                  )}
                </p>
                <p className="mt-1 text-sm font-medium text-muted-foreground">
                  Du {jour(a.debut)} au {jour(a.fin)}
                </p>
              </div>
              {modifiable && !a.cloturee_le && (
                <button
                  type="button"
                  onClick={() => setACloturer(a)}
                  className="inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-bold ring-1 ring-border transition hover:bg-mist-soft"
                >
                  <Lock className="size-3.5" /> Clôturer
                </button>
              )}
            </li>
          ))}
        </ul>
      )}
      {nouvelle && <FormulaireAnnee fermer={() => setNouvelle(false)} />}
      {aCloturer && <Cloture annee={aCloturer} fermer={() => setACloturer(null)} />}
    </div>
  );
}

function FormulaireAnnee({ fermer }: { fermer: () => void }) {
  const router = useRouter();
  const [libelle, setLibelle] = useState("");
  const [debut, setDebut] = useState("");
  const [fin, setFin] = useState("");
  return (
    <DialogueFormulaire
      ouvert
      onOuvert={(o) => !o && fermer()}
      titre="Nouvelle année académique"
      description="De septembre à juillet ; deux années ne peuvent pas se chevaucher."
      bouton="Créer l'année"
      onEnvoie={async () => {
        await adminCreerAnnee({ libelle, debut, fin });
        fermer();
        await router.invalidate();
      }}
    >
      <Champ libelle="Libellé (par exemple 2027-2028)">
        <input
          className={CHAMP_ADMIN}
          required
          pattern="\d{4}-\d{4}"
          value={libelle}
          onChange={(e) => setLibelle(e.target.value)}
        />
      </Champ>
      <Champ libelle="Début">
        <input
          type="date"
          required
          className={CHAMP_ADMIN}
          value={debut}
          onChange={(e) => setDebut(e.target.value)}
        />
      </Champ>
      <Champ libelle="Fin">
        <input
          type="date"
          required
          className={CHAMP_ADMIN}
          value={fin}
          onChange={(e) => setFin(e.target.value)}
        />
      </Champ>
    </DialogueFormulaire>
  );
}

function Cloture({ annee, fermer }: { annee: AnneeAdmin; fermer: () => void }) {
  const router = useRouter();
  return (
    <DialogueFormulaire
      ouvert
      onOuvert={(o) => !o && fermer()}
      titre={`Clôturer l'année ${annee.libelle} ?`}
      description="Le classement régional de l'année est figé, une seule fois : ce n'est pas réversible. Possible seulement après sa date de fin."
      bouton="Clôturer et figer le classement"
      danger
      onEnvoie={async () => {
        await adminCloturerAnnee(annee.id);
        fermer();
        await router.invalidate();
      }}
    />
  );
}
