import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  createMemoryHistory,
  createRootRoute,
  createRouter,
  RouterProvider,
} from "@tanstack/react-router";
import { act, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { MesPartages } from "./MesPartages";
import type { PartageAuteur } from "@/lib/api/client";

const api = vi.hoisted(() => ({ chargerMesPartages: vi.fn() }));
vi.mock("@/lib/api/client", async (original) => ({
  ...(await original<typeof import("@/lib/api/client")>()),
  ...api,
}));

const base: PartageAuteur = {
  id: "p1",
  article_titre: "Le lavage des mains",
  article_adresse: "lavage",
  reseau: "facebook",
  lien: "https://facebook.com/ama/posts/1",
  nature: "partage",
  etat: "approuve",
  motif: null,
  points: 50,
  declare_le: "2026-11-19T10:00:00Z",
};

async function afficher() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const route = createRootRoute({
    component: () => (
      <QueryClientProvider client={client}>
        <MesPartages />
      </QueryClientProvider>
    ),
  });
  const router = createRouter({
    routeTree: route,
    history: createMemoryHistory({ initialEntries: ["/"] }),
  });
  render(<RouterProvider router={router} />);
  await act(() => router.load());
}

beforeEach(() => vi.clearAllMocks());

describe("MesPartages", () => {
  it("invite à partager quand la liste est vide", async () => {
    api.chargerMesPartages.mockResolvedValue({ partages: [] });
    await afficher();

    expect(await screen.findByText(/déclare le lien de ta publication/)).toBeInTheDocument();
  });

  it("montre l'état, les points et le motif d'un refus", async () => {
    api.chargerMesPartages.mockResolvedValue({
      partages: [
        base,
        {
          ...base,
          id: "p2",
          nature: "republication",
          reseau: "tiktok",
          etat: "refuse",
          points: null,
          motif: "Le lien ne s'ouvre pas.",
          article_adresse: null,
        },
        { ...base, id: "p3", reseau: "instagram", etat: "en_attente", points: null },
      ],
    });
    await afficher();

    expect(await screen.findByText("Validé · +50")).toBeInTheDocument();
    expect(screen.getByText("Partage sur Facebook")).toBeInTheDocument();
    expect(screen.getByText("Republication sur TikTok")).toBeInTheDocument();
    expect(screen.getByText("Motif : Le lien ne s'ouvre pas.")).toBeInTheDocument();
    expect(screen.getByText("En vérification")).toBeInTheDocument();
  });
});
