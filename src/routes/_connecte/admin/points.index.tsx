import { createFileRoute, useRouter } from "@tanstack/react-router";
import { CalendarPlus, Pencil } from "lucide-react";
import { useState } from "react";

import { CHAMP_ADMIN, Champ, DialogueFormulaire } from "@/components/admin/DialogueFormulaire";
import { ServiceIndisponible } from "@/components/ServiceIndisponible";
import { Button } from "@/components/ui/button";
import { peut } from "@/lib/admin";
import {
  adminCreerSemestre,
  adminListerSemestres,
  adminModifierSemestre,
  type SemestreAdmin,
} from "@/lib/api/client";

export const Route = createFileRoute("/_connecte/admin/points/")({
  loader: () => adminListerSemestres(),
  gcTime: 0,
  errorComponent: ServiceIndisponible,
  component: Semestres,
});

const ETATS: Record<SemestreAdmin["etat"], { libelle: string; classe: string }> = {
  a_venir: { libelle: "À venir", classe: "bg-sky/30 text-ink" },
  en_cours: { libelle: "En cours", classe: "bg-primary/15 text-primary" },
  termine: { libelle: "Terminé", classe: "bg-mist-soft text-muted-foreground" },
};

const jour = (iso: string) =>
  new Date(`${iso}T00:00:00Z`).toLocaleDateString("fr-FR", {
    day: "numeric",
    month: "long",
    year: "numeric",
    timeZone: "UTC",
  });

function Semestres() {
  const { admin } = Route.useRouteContext();
  const semestres = Route.useLoaderData();
  const modifiable = peut(admin, "points", "modifier") && admin.perimetre_dre === null;
  const [edition, setEdition] = useState<SemestreAdmin | "nouveau" | null>(null);
  const enCours = semestres.find((s) => s.etat === "en_cours");

  return (
    <div className="space-y-5">
      {!enCours && (
        <p
          role="status"
          className="max-w-3xl rounded-2xl bg-sun/25 px-4 py-3 text-sm font-semibold text-ink"
        >
          Aucun semestre en cours : les points gagnés aujourd'hui comptent dans le total des élèves,
          mais dans aucun classement de semestre.
        </p>
      )}
      <p className="max-w-3xl text-sm font-medium text-muted-foreground">
        Un semestre commence aujourd'hui au plus tôt, pour ne pas laisser de points hors de leur
        semestre. Une fois commencé, seule sa date de fin peut être repoussée.
      </p>
      {modifiable && (
        <Button
          onClick={() => setEdition("nouveau")}
          className="btn-fx h-11 rounded-full px-5 font-bold"
        >
          <CalendarPlus className="size-4" /> Nouveau semestre
        </Button>
      )}

      {semestres.length === 0 ? (
        <p className="rounded-3xl bg-white p-6 font-medium text-muted-foreground ring-1 ring-border">
          Aucun semestre pour l'instant.
        </p>
      ) : (
        <ul className="grid gap-3">
          {semestres.map((s) => (
            <li
              key={s.id}
              className="flex flex-wrap items-center gap-4 rounded-3xl bg-white p-5 shadow-sm ring-1 ring-border"
            >
              <div className="min-w-0 flex-1">
                <p className="flex flex-wrap items-center gap-2 font-extrabold text-logo-blue">
                  {s.libelle}
                  <span
                    className={`rounded-full px-2.5 py-0.5 text-xs font-extrabold ${ETATS[s.etat].classe}`}
                  >
                    {ETATS[s.etat].libelle}
                  </span>
                </p>
                <p className="mt-1 text-sm font-medium text-muted-foreground">
                  Du {jour(s.debut)} au {jour(s.fin)}
                </p>
              </div>
              {modifiable && (
                <button
                  type="button"
                  onClick={() => setEdition(s)}
                  className="inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-bold ring-1 ring-border transition hover:bg-mist-soft"
                >
                  <Pencil className="size-3.5" /> Modifier
                </button>
              )}
            </li>
          ))}
        </ul>
      )}

      {edition && (
        <FormulaireSemestre
          key={edition === "nouveau" ? "nouveau" : edition.id}
          semestre={edition === "nouveau" ? null : edition}
          fermer={() => setEdition(null)}
        />
      )}
    </div>
  );
}

function FormulaireSemestre({
  semestre,
  fermer,
}: {
  semestre: SemestreAdmin | null;
  fermer: () => void;
}) {
  const router = useRouter();
  const [libelle, setLibelle] = useState(semestre?.libelle ?? "");
  const [debut, setDebut] = useState(semestre?.debut ?? "");
  const [fin, setFin] = useState(semestre?.fin ?? "");
  const commence = semestre !== null && semestre.etat !== "a_venir";

  return (
    <DialogueFormulaire
      ouvert
      onOuvert={(o) => !o && fermer()}
      titre={semestre ? `Modifier ${semestre.libelle}` : "Nouveau semestre"}
      description={
        semestre?.etat === "en_cours"
          ? "Ce semestre a commencé : tu peux le renommer ou repousser sa date de fin."
          : semestre?.etat === "termine"
            ? "Ce semestre est terminé : seul son libellé peut changer."
            : "Les dates sont celles de Lomé. Deux semestres ne peuvent pas se chevaucher."
      }
      bouton="Enregistrer"
      onEnvoie={async () => {
        if (semestre)
          await adminModifierSemestre(semestre.id, {
            version: semestre.version,
            libelle,
            ...(commence ? {} : { debut }),
            ...(semestre.etat === "termine" ? {} : { fin }),
          });
        else await adminCreerSemestre({ libelle, debut, fin });
        await router.invalidate();
      }}
    >
      <Champ libelle="Libellé">
        <input
          required
          value={libelle}
          onChange={(e) => setLibelle(e.target.value)}
          maxLength={60}
          placeholder="ex. 2026-2027, semestre 1"
          className={CHAMP_ADMIN}
        />
      </Champ>
      <div className="grid gap-4 sm:grid-cols-2">
        <Champ libelle="Début">
          <input
            type="date"
            required
            value={debut}
            onChange={(e) => setDebut(e.target.value)}
            disabled={commence}
            className={CHAMP_ADMIN}
          />
        </Champ>
        <Champ libelle="Fin">
          <input
            type="date"
            required
            value={fin}
            min={commence ? semestre?.fin : debut || undefined}
            onChange={(e) => setFin(e.target.value)}
            disabled={semestre?.etat === "termine"}
            className={CHAMP_ADMIN}
          />
        </Champ>
      </div>
    </DialogueFormulaire>
  );
}
