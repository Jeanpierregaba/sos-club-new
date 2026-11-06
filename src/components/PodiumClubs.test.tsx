import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  createMemoryHistory,
  createRootRoute,
  createRouter,
  RouterProvider,
} from "@tanstack/react-router";
import { act, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { PodiumClubs } from "./PodiumClubs";
import type { ClubPodium } from "@/lib/api/client";

const api = vi.hoisted(() => ({ chargerPodiumClubs: vi.fn() }));
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

beforeEach(() => vi.clearAllMocks());

describe("PodiumClubs", () => {
  it("montre les trois clubs avec leurs points et un lien vers les jeux", async () => {
    api.chargerPodiumClubs.mockResolvedValue([
      club(1, "Club Tokoin", 15800),
      club(2, "Club Kpalimé", 12450),
      club(3, "Club Kara", 10200),
    ]);
    await afficher();

    const lignes = await screen.findAllByRole("listitem");
    expect(lignes).toHaveLength(3);
    expect(lignes[0]).toHaveTextContent("Club Tokoin");
    expect(lignes[0]).toHaveTextContent(/15\s800\s*pts/);
    expect(screen.getByRole("link", { name: /Club Tokoin/ })).toHaveAttribute(
      "href",
      "/clubs/club-1",
    );
    expect(screen.getByRole("link", { name: /Découvrir les jeux/ })).toHaveAttribute(
      "href",
      "/jeux",
    );
  });

  it("annonce le classement tant qu'aucun club n'a de points", async () => {
    api.chargerPodiumClubs.mockResolvedValue([]);
    await afficher();

    expect(screen.getByText("Le classement démarre bientôt !")).toBeInTheDocument();
    expect(screen.queryByRole("listitem")).not.toBeInTheDocument();
  });

  it("garde l'état vide si l'API ne répond pas", async () => {
    api.chargerPodiumClubs.mockRejectedValue(new Error("hors ligne"));
    await afficher();

    expect(screen.getByText("Le classement démarre bientôt !")).toBeInTheDocument();
  });
});
