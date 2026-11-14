import { QueryClient } from "@tanstack/react-query";
import {
  createMemoryHistory,
  createRootRoute,
  createRouter,
  RouterProvider,
} from "@tanstack/react-router";
import { act, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { BlocClub } from "./BlocClub";
import type { AdhesionResume, ClubResume, EtablissementRattache } from "@/lib/api/client";

const etablissement: EtablissementRattache = {
  id: "etab-1",
  nom: "Lycée de Tokoin I",
  statut: "actif",
  iesg: "IESG Golfe",
  dre_code: "grand-lome",
  dre: "Grand Lomé",
};

const club = (changements: Partial<ClubResume> = {}): ClubResume => ({
  id: "club-1",
  nom: "Club Santé — Lycée de Tokoin I",
  description: null,
  etablissement,
  axes: [],
  statut: "en_constitution",
  actif_le: null,
  regularisation_jusquau: null,
  president: false,
  version: 1,
  ...changements,
});

const affiliation = (changements: Partial<AdhesionResume> = {}): AdhesionResume => ({
  id: "adh-1",
  club_id: "club-1",
  club_nom: "Club Santé — Lycée de Tokoin I",
  etat: "en_attente_validation",
  demande_le: "2026-11-10T08:00:00Z",
  version: 1,
  ...changements,
});

async function afficher(element: React.ReactElement) {
  const route = createRootRoute({ component: () => element });
  const router = createRouter({
    routeTree: route,
    history: createMemoryHistory({ initialEntries: ["/"] }),
    context: { queryClient: new QueryClient() },
  });
  render(<RouterProvider router={router} />);
  await act(() => router.load());
}

const rafraichir = vi.fn().mockResolvedValue(undefined);

describe("BlocClub (spec 033)", () => {
  it("n'offre plus de demande de création : le club s'ouvre tout seul", async () => {
    await afficher(
      <BlocClub club={null} affiliation={null} passation={null} onRafraichir={rafraichir} />,
    );
    expect(screen.getByText(/Il s'ouvre tout seul/)).toBeInTheDocument();
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });

  it("explique le seuil d'un club en constitution et l'affiliation à confirmer", async () => {
    await afficher(
      <BlocClub
        club={club()}
        affiliation={affiliation()}
        passation={null}
        onRafraichir={rafraichir}
      />,
    );
    expect(screen.getByText("En constitution")).toBeInTheDocument();
    expect(screen.getByText(/3 encadreurs et 21 élèves/)).toBeInTheDocument();
    expect(screen.getByText(/attend la confirmation d'un encadreur/)).toBeInTheDocument();
  });

  it("annonce l'échéance d'une régularisation", async () => {
    await afficher(
      <BlocClub
        club={club({
          statut: "en_regularisation",
          actif_le: "2026-10-01T08:00:00Z",
          regularisation_jusquau: "2026-11-25T08:00:00Z",
        })}
        affiliation={affiliation({ etat: "active" })}
        passation={null}
        onRafraichir={rafraichir}
      />,
    );
    expect(screen.getByText("En régularisation")).toBeInTheDocument();
    expect(screen.getByText(/jusqu'au 25/)).toBeInTheDocument();
    expect(screen.getByText(/membre confirmé/)).toBeInTheDocument();
  });

  it("dit qu'un club suspendu garde les points de l'élève", async () => {
    await afficher(
      <BlocClub
        club={club({ statut: "suspendu", actif_le: "2026-10-01T08:00:00Z" })}
        affiliation={affiliation({ etat: "active" })}
        passation={null}
        onRafraichir={rafraichir}
      />,
    );
    expect(screen.getByText(/Tes points à toi restent/)).toBeInTheDocument();
  });

  it("montre le motif d'une affiliation refusée", async () => {
    await afficher(
      <BlocClub
        club={club()}
        affiliation={affiliation({ etat: "refusee", motif_refus: "Pas inscrit ici." })}
        passation={null}
        onRafraichir={rafraichir}
      />,
    );
    expect(screen.getByText("Affiliation refusée")).toBeInTheDocument();
    expect(screen.getByText(/Pas inscrit ici/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Redemander mon affiliation" })).toBeInTheDocument();
  });

  it("laisse le président d'un club actif passer la main et gérer son club", async () => {
    await afficher(
      <BlocClub
        club={club({ statut: "actif", actif_le: "2026-10-01T08:00:00Z", president: true })}
        affiliation={affiliation({ etat: "active" })}
        passation={null}
        onRafraichir={rafraichir}
      />,
    );
    expect(screen.getByRole("button", { name: /Passer la présidence/ })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Gérer mon club/ })).toBeInTheDocument();
  });
});
