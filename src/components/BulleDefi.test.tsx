import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  createMemoryHistory,
  createRootRoute,
  createRouter,
  RouterProvider,
} from "@tanstack/react-router";
import { act, fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { BulleDefi } from "./BulleDefi";
import { ErreurApi, type CorrectionDefi, type DefiDuJour, type Moi } from "@/lib/api/client";

const api = vi.hoisted(() => ({
  chargerMoi: vi.fn(),
  chargerDefiDuJour: vi.fn(),
  corrigerDefi: vi.fn(),
}));
vi.mock("@/lib/api/client", async (original) => ({
  ...(await original<typeof import("@/lib/api/client")>()),
  ...api,
}));

const defi: DefiDuJour = {
  id: "defi-1",
  categorie: "Hygiène",
  question: "Combien de temps faut-il se laver les mains ?",
  options: ["Cinq secondes", "Au moins 20 secondes, avec du savon", "Une seconde"],
  ma_reponse: null,
};

const correction = (extra: Partial<CorrectionDefi>): CorrectionDefi => ({
  choix: 1,
  correcte: true,
  bonne_reponse: 1,
  explication: "Frotter 20 secondes élimine la plupart des microbes.",
  points: 0,
  deja_repondu: false,
  ...extra,
});

const eleve: Moi = { id: "u-1", identifiant: "ama", prenom: "Ama", nom: "K", role: "eleve" };

async function afficher() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const route = createRootRoute({
    component: () => (
      <QueryClientProvider client={client}>
        <BulleDefi />
      </QueryClientProvider>
    ),
  });
  const router = createRouter({
    routeTree: route,
    history: createMemoryHistory({ initialEntries: ["/"] }),
  });
  const rendu = render(<RouterProvider router={router} />);
  await act(() => router.load());
  return rendu;
}

async function ouvrir() {
  fireEvent.click(await screen.findByRole("button", { name: "Ouvrir le défi du jour" }));
}

beforeEach(() => vi.clearAllMocks());

describe("BulleDefi", () => {
  it("crédite un élève et le lui dit", async () => {
    api.chargerMoi.mockResolvedValue(eleve);
    api.chargerDefiDuJour.mockResolvedValue(defi);
    api.corrigerDefi.mockResolvedValue(correction({ points: 20 }));
    await afficher();

    await ouvrir();
    expect(screen.getByText(/\+20 points/)).toBeInTheDocument();
    expect(screen.getByText(/\+10 pour ton club/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /Au moins 20 secondes/ }));
    await act(async () => fireEvent.click(screen.getByRole("button", { name: "Valider" })));

    expect(api.corrigerDefi).toHaveBeenCalledWith("defi-1", 1);
    expect(screen.getByRole("status")).toHaveTextContent("Bravo ! +20 points pour toi.");
    expect(screen.getByText(/élimine la plupart des microbes/)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Valider" })).not.toBeInTheDocument();
  });

  it("montre la réponse déjà donnée aujourd'hui, sans pouvoir rejouer", async () => {
    api.chargerMoi.mockResolvedValue(eleve);
    api.chargerDefiDuJour.mockResolvedValue({
      ...defi,
      ma_reponse: correction({ points: 20, deja_repondu: true }),
    });
    await afficher();

    await ouvrir();

    expect(screen.getByRole("status")).toHaveTextContent("déjà récompensée, +20 points");
    expect(screen.getByRole("button", { name: /Au moins 20 secondes/ })).toBeDisabled();
    expect(screen.queryByRole("button", { name: "Valider" })).not.toBeInTheDocument();
  });

  it("invite un visiteur à se connecter pour gagner des points", async () => {
    api.chargerMoi.mockResolvedValue(null);
    api.chargerDefiDuJour.mockResolvedValue(defi);
    api.corrigerDefi.mockResolvedValue(correction({ correcte: false, choix: 0 }));
    await afficher();

    await ouvrir();
    expect(
      screen.getByRole("link", { name: /Connecte-toi à ton compte Élève/ }),
    ).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /Cinq secondes/ }));
    await act(async () => fireEvent.click(screen.getByRole("button", { name: "Valider" })));

    expect(screen.getByRole("status")).toHaveTextContent(
      "la bonne réponse est « Au moins 20 secondes, avec du savon »",
    );
    expect(
      screen.getByRole("button", { name: /Au moins 20 secondes.*\(bonne réponse\)/ }),
    ).toHaveClass("bg-leaf");
    expect(
      screen.getByRole("button", { name: /Cinq secondes.*\(ta réponse\)/ }),
    ).toBeInTheDocument();
  });

  it("ne s'affiche pas sans défi", async () => {
    api.chargerMoi.mockResolvedValue(null);
    api.chargerDefiDuJour.mockRejectedValue(new ErreurApi(404, "Aucun défi."));
    await afficher();
    await act(async () => {});

    expect(
      screen.queryByRole("button", { name: "Ouvrir le défi du jour" }),
    ).not.toBeInTheDocument();
  });
});
