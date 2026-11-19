import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  createMemoryHistory,
  createRootRoute,
  createRouter,
  RouterProvider,
} from "@tanstack/react-router";
import { act, render, screen, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { PodiumClubs } from "./PodiumClubs";
import type { ClubPodium } from "@/lib/api/client";

const api = vi.hoisted(() => ({ chargerPodiumClubs: vi.fn(), chargerClassementPublic: vi.fn() }));
vi.mock("@/lib/api/client", async (original) => ({
  ...(await original<typeof import("@/lib/api/client")>()),
  ...api,
}));

async function afficher() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const route = createRootRoute({
    component: () => (
      <QueryClientProvider client={client}>
        <PodiumClubs />
      </QueryClientProvider>
    ),
  });
  const router = createRouter({
    routeTree: route,
    history: createMemoryHistory({ initialEntries: ["/"] }),
  });
  render(<RouterProvider router={router} />);
  await act(() => router.load());
  await act(async () => {});
}

const club = (rang: number, nom: string, points: number): ClubPodium => ({
  rang,
  id: `club-${rang}`,
  nom,
  etablissement: `Lycée ${rang}`,
  dre: "Grand Lomé",
  points,
});

const eleves = (lignes: { rang: number; nom: string; points: number }[]) => ({
  categorie: "eleves",
  niveau: "national",
  dre: null,
  periode: "semestre",
  semestre: null,
  page: 1,
  par_page: 3,
  total: lignes.length,
  lignes: lignes.map((l) => ({ ...l, club: "Club Tokoin", dre: "Grand Lomé" })),
});

beforeEach(() => {
  vi.clearAllMocks();
  api.chargerClassementPublic.mockResolvedValue(eleves([]));
});

describe("PodiumClubs", () => {
  it("montre les trois clubs avec leurs points et un lien vers les jeux", async () => {
    api.chargerPodiumClubs.mockResolvedValue([
      club(1, "Club Tokoin", 15800),
      club(2, "Club Kpalimé", 12450),
      club(3, "Club Kara", 10200),
    ]);
    await afficher();

    const lycees = await screen.findByRole("list", { name: "Top 3 des lycées" });
    const lignes = within(lycees).getAllByRole("listitem");
    expect(lignes).toHaveLength(3);
    expect(lignes[0]).toHaveTextContent("Lycée 1");
    expect(lignes[0]).toHaveTextContent("Club Tokoin");
    expect(lignes[0]).toHaveTextContent(/15\s800\s*pts/);
    expect(screen.getByRole("link", { name: /Lycée 1/ })).toHaveAttribute("href", "/clubs/club-1");
    expect(screen.getByRole("link", { name: /Découvrir les jeux/ })).toHaveAttribute(
      "href",
      "/jeux",
    );
    expect(screen.getByRole("link", { name: "Découvrir le classement" })).toHaveAttribute(
      "href",
      "/hall-of-fame",
    );
    expect(screen.queryByRole("img")).not.toBeInTheDocument();
  });

  it("montre les trois meilleurs élèves par leur pseudonyme", async () => {
    api.chargerPodiumClubs.mockResolvedValue([]);
    api.chargerClassementPublic.mockResolvedValue(
      eleves([
        { rang: 1, nom: "Ama du Golfe", points: 900 },
        { rang: 2, nom: "Kofi", points: 700 },
        { rang: 3, nom: "Yawa", points: 650 },
      ]),
    );
    await afficher();

    const top = await screen.findByRole("list", { name: "Top 3 des élèves" });
    const lignes = within(top).getAllByRole("listitem");
    expect(lignes).toHaveLength(3);
    expect(lignes[0]).toHaveTextContent("Ama du Golfe");
    expect(lignes[0]).toHaveTextContent("Club Tokoin · Grand Lomé");
    expect(api.chargerClassementPublic).toHaveBeenCalledWith({
      categorie: "eleves",
      niveau: "national",
      periode: "semestre",
      par_page: 3,
    });
  });

  it("annonce le classement tant qu'aucun club n'a de points", async () => {
    api.chargerPodiumClubs.mockResolvedValue([]);
    await afficher();

    expect(screen.getAllByText("Le classement arrive bientôt !")).toHaveLength(2);
    expect(screen.queryByRole("listitem")).not.toBeInTheDocument();
  });

  it("garde l'état vide si l'API ne répond pas", async () => {
    api.chargerPodiumClubs.mockRejectedValue(new Error("hors ligne"));
    api.chargerClassementPublic.mockRejectedValue(new Error("hors ligne"));
    await afficher();

    expect(screen.getAllByText("Le classement arrive bientôt !")).toHaveLength(2);
  });
});
