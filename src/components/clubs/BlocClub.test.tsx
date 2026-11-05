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
import type { AxePublic, ClubPublic, ClubResume, EtablissementRattache } from "@/lib/api/client";

const etablissement: EtablissementRattache = {
  id: "etab-1",
  nom: "Lycée de Tokoin I",
  statut: "actif",
  iesg: "IESG Golfe",
  dre_code: "grand-lome",
  dre: "Grand Lomé",
};

const clubActifEtablissement: ClubPublic = {
  id: "club-existant",
  nom: "Club Santé Tokoin",
  etablissement,
  axes: ["sante-environnement"],
  actif_le: "2026-11-04T10:00:00Z",
};

const axes: AxePublic[] = [];

async function afficher(element: React.ReactElement) {
  const route = createRootRoute({
    component: () => element,
  });
  const router = createRouter({
    routeTree: route,
    history: createMemoryHistory({ initialEntries: ["/"] }),
    context: { queryClient: new QueryClient() },
  });
  render(<RouterProvider router={router} />);
  await act(() => router.load());
}

const rafraichir = vi.fn().mockResolvedValue(undefined);

describe("BlocClub — état vide", () => {
  it("propose le formulaire quand son établissement n'a pas de club", async () => {
    await afficher(
      <BlocClub
        club={null}
        passation={null}
        etablissement={etablissement}
        axes={axes}
        clubEtablissement={null}
        onRafraichir={rafraichir}
      />,
    );
    expect(screen.getByRole("button", { name: "Ouvrir l'espace de mon club" })).toBeInTheDocument();
  });

  it("ne propose pas le formulaire si un autre club est déjà actif", async () => {
    await afficher(
      <BlocClub
        club={null}
        passation={null}
        etablissement={etablissement}
        axes={axes}
        clubEtablissement={clubActifEtablissement}
        onRafraichir={rafraichir}
      />,
    );
    expect(
      screen.queryByRole("button", { name: "Ouvrir l'espace de mon club" }),
    ).not.toBeInTheDocument();
    expect(screen.getByText("Club Santé Tokoin")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /fiche publique/ })).toBeInTheDocument();
  });
});

describe("BlocClub — demande refusée", () => {
  const club: ClubResume = {
    id: "club-1",
    nom: "Club Santé de Tokoin",
    description: null,
    etablissement,
    axes: [],
    etat: "refuse",
    president: false,
    motif_refus: "Nom déjà pris dans cet établissement.",
    version: 2,
  };

  it("affiche le motif du refus", async () => {
    await afficher(
      <BlocClub
        club={club}
        passation={null}
        etablissement={etablissement}
        axes={axes}
        clubEtablissement={null}
        onRafraichir={rafraichir}
      />,
    );
    expect(screen.getByText(/Nom déjà pris dans cet établissement\./)).toBeInTheDocument();
  });
});
