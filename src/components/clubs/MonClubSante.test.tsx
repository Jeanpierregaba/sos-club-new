import { QueryClient } from "@tanstack/react-query";
import {
  createMemoryHistory,
  createRootRoute,
  createRouter,
  RouterProvider,
} from "@tanstack/react-router";
import { act, fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { EspaceClubSante, ResumeClubSante } from "./MonClubSante";
import type { AffiliationsDuClub, MonClubSante } from "@/lib/api/client";

const api = vi.hoisted(() => ({
  deciderAffiliation: vi.fn(),
  signalerDesistement: vi.fn(),
  proposerPresident: vi.fn(),
}));
vi.mock("@/lib/api/client", async (original) => ({
  ...(await original<typeof import("@/lib/api/client")>()),
  ...api,
}));

const club = (changements: Partial<MonClubSante> = {}): MonClubSante => ({
  id: "club-1",
  nom: "Club Santé — Lycée de Tokoin I",
  etablissement: {
    id: "etab-1",
    nom: "Lycée de Tokoin I",
    statut: "actif",
    iesg: "IESG Golfe",
    dre_code: "grand-lome",
    dre: "Grand Lomé",
    region: "Maritime",
  },
  statut: "en_constitution",
  actif_le: null,
  regularisation_jusquau: null,
  declare_terrain: false,
  seuils: { encadreurs: 3, eleves: 21, delai_jours: 15 },
  nb_encadreurs: 2,
  nb_eleves: 20,
  a_confirmer: 1,
  equipe: [
    {
      utilisateur_id: "moi",
      prenom: "Afi",
      nom: "Mensah",
      fonction: "enseignant",
      moi: true,
      signalement_en_attente: false,
    },
    {
      utilisateur_id: "kossi",
      prenom: "Kossi",
      nom: "Adjo",
      fonction: "sante",
      moi: false,
      signalement_en_attente: false,
    },
  ],
  president_pseudonyme: null,
  president_propose: null,
  passations_a_confirmer: [],
  mes_signalements: [],
  ...changements,
});

const affiliations: AffiliationsDuClub = {
  a_confirmer: [
    {
      id: "a-1",
      pseudonyme: "Kofi",
      classe: "2nde",
      etat: "en_attente_validation",
      demande_le: "2026-11-10T08:00:00Z",
      depuis: null,
      president: false,
      version: 1,
    },
  ],
  confirmees: [
    {
      id: "a-2",
      pseudonyme: "Ama",
      classe: "1re",
      etat: "active",
      demande_le: "2026-11-01T08:00:00Z",
      depuis: "2026-11-02T08:00:00Z",
      president: false,
      version: 2,
    },
  ],
};

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

beforeEach(() => vi.clearAllMocks());

describe("ResumeClubSante", () => {
  it("montre les effectifs par rapport aux seuils et les élèves à confirmer", async () => {
    await afficher(<ResumeClubSante club={club()} />);
    expect(screen.getByRole("progressbar", { name: "Encadreurs" })).toHaveAttribute(
      "aria-valuenow",
      "2",
    );
    expect(screen.getByText("20 / 21")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /1 élève à confirmer/ })).toBeInTheDocument();
  });
});

describe("EspaceClubSante", () => {
  it("confirme un élève d'un clic", async () => {
    api.deciderAffiliation.mockResolvedValue(affiliations);
    await afficher(
      <EspaceClubSante club={club()} affiliations={affiliations} onRafraichir={rafraichir} />,
    );

    await act(async () => fireEvent.click(screen.getByRole("button", { name: "Confirmer Kofi" })));

    expect(api.deciderAffiliation).toHaveBeenCalledWith("a-1", "confirmer", 1);
    expect(rafraichir).toHaveBeenCalled();
  });

  it("signale le départ d'un autre encadreur avec un motif, jamais le sien", async () => {
    api.signalerDesistement.mockResolvedValue({});
    await afficher(
      <EspaceClubSante club={club()} affiliations={affiliations} onRafraichir={rafraichir} />,
    );

    expect(screen.getAllByRole("button", { name: /Signaler un départ/ })).toHaveLength(1);
    fireEvent.click(screen.getByRole("button", { name: /Signaler un départ/ }));
    fireEvent.change(screen.getByRole("textbox"), { target: { value: "Muté à Kara." } });
    await act(async () => fireEvent.click(screen.getByRole("button", { name: "Signaler" })));

    expect(api.signalerDesistement).toHaveBeenCalledWith("kossi", "Muté à Kara.");
  });

  it("ne propose un président que si le club est actif", async () => {
    await afficher(
      <EspaceClubSante club={club()} affiliations={affiliations} onRafraichir={rafraichir} />,
    );
    expect(screen.queryByRole("button", { name: /Proposer un président/ })).not.toBeInTheDocument();
    expect(screen.getByText(/dès que le club sera actif/)).toBeInTheDocument();
  });

  it("propose un élève confirmé comme président d'un club actif", async () => {
    api.proposerPresident.mockResolvedValue(club());
    await afficher(
      <EspaceClubSante
        club={club({ statut: "actif", nb_encadreurs: 3, nb_eleves: 21 })}
        affiliations={affiliations}
        onRafraichir={rafraichir}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /Proposer un président/ }));
    fireEvent.change(screen.getByRole("combobox"), { target: { value: "a-2" } });
    await act(async () => fireEvent.click(screen.getByRole("button", { name: "Proposer" })));

    expect(api.proposerPresident).toHaveBeenCalledWith("a-2");
  });
});
