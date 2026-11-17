import { useState } from "react";
import { createFileRoute, redirect, useRouter } from "@tanstack/react-router";
import { CalendarPlus } from "lucide-react";

import { CarteEvenement } from "@/components/agenda/CarteEvenement";
import { FormulaireEvenement } from "@/components/agenda/FormulaireEvenement";
import { DialogueMotif } from "@/components/admin/DialogueMotif";
import { ServiceIndisponible } from "@/components/ServiceIndisponible";
import { Button } from "@/components/ui/button";
import {
  adminAnnulerEvenement,
  adminChargerAgenda,
  adminCreerEvenement,
  adminModifierEvenement,
  chargerAxes,
  chargerDre,
} from "@/lib/api/client";
import type { EvenementPublic } from "@/lib/api/client";
import { peut } from "@/lib/admin";

type Niveau = "national" | "regional";

// L'agenda pour l'équipe (spec 041) : les événements nationaux et régionaux, publiés dès leur création. Les
// événements des clubs se décident dans la file de modération ; ici, on les voit et on peut les annuler.
export const Route = createFileRoute("/_connecte/admin/agenda")({
  beforeLoad: ({ context }) => {
    if (!context.admin || !peut(context.admin, "agenda", "consulter"))
      throw redirect({ to: "/admin" });
  },
  loader: async () => {
    const [avenir, axes, dre] = await Promise.all([
      adminChargerAgenda(),
      chargerAxes(),
      chargerDre(),
    ]);
    return { avenir, axes, dre };
  },
  head: () => ({
    meta: [{ title: "Agenda — Administration" }, { name: "robots", content: "noindex" }],
  }),
  errorComponent: ServiceIndisponible,
  component: AgendaAdmin,
});

function AgendaAdmin() {
  const { avenir, axes, dre } = Route.useLoaderData();
  const { admin } = Route.useRouteContext();
  const router = useRouter();
  const [edition, setEdition] = useState<EvenementPublic | "nouveau" | null>(null);
  const [niveau, setNiveau] = useState<Niveau>(admin?.perimetre_dre ? "regional" : "national");
  const [dreCode, setDreCode] = useState<string>(admin?.perimetre_dre ?? "");
  const [annulation, setAnnulation] = useState<EvenementPublic | null>(null);
  const createur = admin ? peut(admin, "agenda", "creer") : false;
  const editeur = admin ? peut(admin, "agenda", "modifier") : false;
  const gardien = admin ? peut(admin, "agenda", "depublier") : false;

  function ouvrir(cible: EvenementPublic | "nouveau") {
    setEdition(cible);
    if (cible !== "nouveau" && cible.niveau !== "club") {
      setNiveau(cible.niveau);
      setDreCode(cible.dre_code ?? "");
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-3xl text-logo-blue">Agenda</h1>
          <p className="text-sm font-medium text-muted-foreground">
            Les événements de l'équipe sont publiés dès leur création. Ceux des clubs passent par la
            modération.
          </p>
        </div>
        {createur && (
          <Button className="h-11 rounded-full px-5 font-bold" onClick={() => ouvrir("nouveau")}>
            <CalendarPlus className="size-4" /> Nouvel événement
          </Button>
        )}
      </div>

      {edition && (
        <section className="space-y-4 rounded-[1.75rem] bg-white p-5 shadow-card">
          <h2 className="text-xl text-logo-blue">
            {edition === "nouveau" ? "Nouvel événement" : `Modifier « ${edition.titre} »`}
          </h2>
          <div className="flex flex-wrap gap-4">
            <label className="text-sm font-bold">
              Niveau
              <select
                value={niveau}
                disabled={Boolean(admin?.perimetre_dre)}
                onChange={(e) => setNiveau(e.target.value as Niveau)}
                className="mt-1 block h-11 rounded-xl border bg-white px-3 font-medium"
              >
                <option value="national">National (Secrétariat technique permanent)</option>
                <option value="regional">Régional (Comité)</option>
              </select>
            </label>
            {niveau === "regional" && (
              <label className="text-sm font-bold">
                DRE
                <select
                  value={dreCode}
                  disabled={Boolean(admin?.perimetre_dre)}
                  onChange={(e) => setDreCode(e.target.value)}
                  className="mt-1 block h-11 rounded-xl border bg-white px-3 font-medium"
                >
                  <option value="">Choisis une DRE</option>
                  {dre.map((d) => (
                    <option key={d.code} value={d.code}>
                      {d.nom}
                    </option>
                  ))}
                </select>
              </label>
            )}
          </div>
          <FormulaireEvenement
            key={edition === "nouveau" ? "nouveau" : edition.id}
            initial={edition === "nouveau" ? null : (edition as unknown as Record<string, unknown>)}
            axes={axes}
            axeObligatoire={false}
            bouton={edition === "nouveau" ? "Publier l'événement" : "Enregistrer"}
            onEnvoi={async (champs) => {
              const corps = {
                niveau,
                dre_code: niveau === "regional" ? dreCode || null : null,
                champs,
              };
              if (edition === "nouveau") await adminCreerEvenement(corps);
              else await adminModifierEvenement(edition.id, corps);
              setEdition(null);
              await router.invalidate();
            }}
          />
          <Button variant="outline" className="rounded-full" onClick={() => setEdition(null)}>
            Fermer
          </Button>
        </section>
      )}

      {avenir.length === 0 ? (
        <p className="rounded-[1.75rem] border border-dashed p-8 text-center font-semibold text-muted-foreground">
          Aucun événement à venir.
        </p>
      ) : (
        <ul className="grid gap-4">
          {avenir.map((e) => (
            <li key={e.id} className="space-y-2">
              <CarteEvenement evenement={e} />
              {!e.annule && (
                <div className="flex flex-wrap gap-2">
                  {editeur && e.niveau !== "club" && (
                    <Button
                      variant="outline"
                      className="rounded-full font-bold"
                      onClick={() => ouvrir(e)}
                    >
                      Modifier ou reporter
                    </Button>
                  )}
                  {(e.niveau === "club" ? gardien : editeur) && (
                    <Button
                      variant="outline"
                      className="rounded-full font-bold text-logo-red"
                      onClick={() => setAnnulation(e)}
                    >
                      Annuler
                    </Button>
                  )}
                </div>
              )}
            </li>
          ))}
        </ul>
      )}

      <DialogueMotif
        ouvert={annulation !== null}
        onOuvert={(ouvert) => !ouvert && setAnnulation(null)}
        titre="Annuler l'événement"
        description="L'événement reste dans l'agenda, marqué « Annulé » ; les membres invités d'un club sont prévenus avec ce motif."
        bouton="Annuler l'événement"
        danger
        longueurMin={10}
        longueurMax={200}
        onConfirme={async (motif) => {
          if (!annulation) return;
          await adminAnnulerEvenement(annulation.id, motif);
          setAnnulation(null);
          await router.invalidate();
        }}
      />
    </div>
  );
}
