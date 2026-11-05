import { QueryClient } from "@tanstack/react-query";
import {
  createMemoryHistory,
  createRootRoute,
  createRouter,
  RouterProvider,
} from "@tanstack/react-router";
import { act, fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { MesClubsEncadreur } from "./MesClubsEncadreur";
import type { ClubPublic, MembresDuClub, MesClubs, RattachementResume } from "@/lib/api/client";

const api = vi.hoisted(() => ({
  demanderRattachement: vi.fn(),
  confirmerPassationEncadreur: vi.fn(),
}));
vi.mock("@/lib/api/client", async (original) => ({
  ...(await original<typeof import("@/lib/api/client")>()),
  ...api,
}));

const clubEtablissement: ClubPublic = {
  id: "club-1",
  nom: "Club Santé Tokoin",
  etablissement: {
    id: "etab-1",
    nom: "Lycée de Tokoin I",
    statut: "actif",
    iesg: "IESG Golfe",
    dre_code: "grand-lome",
    dre: "Grand Lomé",
  },
  axes: [],
  actif_le: "2026-11-04T10:00:00Z",
};

const rattachement = (
  etat: RattachementResume["etat"],
  extra: Partial<RattachementResume> = {},
) => ({
  id: `rat-${etat}`,
  club_id: "club-1",
  club_nom: "Club Santé Tokoin",
  etat,
  supplementaire: false,
  demande_le: "2026-11-05T10:00:00Z",
  version: 1,
  ...extra,
});

const membres: MembresDuClub = {
  membres: [
    { id: "a-1", pseudonyme: "Zoé", depuis: "2026-11-01T10:00:00Z", president: true, version: 1 },
  ],
  encadreurs: [],
};

async function afficher(
  mesClubs: MesClubs,
  autres: Partial<Parameters<typeof MesClubsEncadreur>[0]> = {},
) {
  const element = (
    <MesClubsEncadreur
      mesClubs={mesClubs}
      clubEtablissement={clubEtablissement}
      membres={{}}
      onRafraichir={vi.fn().mockResolvedValue(undefined)}
      {...autres}
    />
  );
  const route = createRootRoute({ component: () => element });
  const router = createRouter({
    routeTree: route,
    history: createMemoryHistory({ initialEntries: ["/"] }),
    context: { queryClient: new QueryClient() },
  });
  render(<RouterProvider router={router} />);
  await act(() => router.load());
}

beforeEach(() => vi.clearAllMocks());

describe("MesClubsEncadreur", () => {
  it("propose de se rattacher au club de son établissement", async () => {
    api.demanderRattachement.mockResolvedValue(rattachement("en_attente_president"));
    await afficher({ rattachements: [], passations: [] });

    fireEvent.click(screen.getByRole("button", { name: /Demander mon rattachement/ }));
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Envoyer ma demande" }));
    });

    expect(api.demanderRattachement).toHaveBeenCalledWith("club-1");
  });

  it("ne repropose pas un club déjà demandé, et signale un club supplémentaire", async () => {
    await afficher({
      rattachements: [rattachement("en_attente_validation", { supplementaire: true })],
      passations: [],
    });

    expect(
      screen.queryByRole("button", { name: /Demander mon rattachement/ }),
    ).not.toBeInTheDocument();
    expect(screen.getByText(/l'équipe nationale doit l'autoriser/)).toBeInTheDocument();
    expect(screen.getByText("Attend la validation")).toBeInTheDocument();
  });

  it("montre les membres d'un club encadré, en lecture seule", async () => {
    await afficher(
      { rattachements: [rattachement("actif")], passations: [] },
      { membres: { "club-1": membres } },
    );

    fireEvent.click(screen.getByRole("button", { name: /Voir les membres \(1\)/ }));

    expect(screen.getByText("Zoé")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Retirer/ })).not.toBeInTheDocument();
  });

  it("fait confirmer le nouveau président (Q19)", async () => {
    api.confirmerPassationEncadreur.mockResolvedValue({});
    await afficher({
      rattachements: [rattachement("actif")],
      passations: [
        {
          id: "pass-1",
          club_id: "club-1",
          club_nom: "Club Santé Tokoin",
          successeur_pseudonyme: "Kofi Curieux",
          president_sortant_pseudonyme: "Zoé",
          propose_le: "2026-11-05T10:00:00Z",
          version: 4,
        },
      ],
    });

    expect(screen.getByText(/Zoé propose/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Confirmer" }));
    await act(async () => {
      fireEvent.click(screen.getAllByRole("button", { name: "Confirmer" }).at(-1)!);
    });

    expect(api.confirmerPassationEncadreur).toHaveBeenCalledWith("club-1", 4);
  });
});
