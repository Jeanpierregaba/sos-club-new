import { act, fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  createMemoryHistory,
  createRootRoute,
  createRouter,
  RouterProvider,
} from "@tanstack/react-router";
import type { ReactNode } from "react";

import { CarteInscrit } from "@/components/admin/CarteInscrit";
import { ApercuCarte } from "@/components/cartes/ApercuCarte";
import { VerificationCarte } from "@/components/cartes/VerificationCarte";
import { Verifier } from "@/components/cartes/Verifier";
import type { CarteAdmin, MaCarte } from "@/lib/api/client";

const api = vi.hoisted(() => ({
  verifierCarte: vi.fn(),
  suspendreCarte: vi.fn(),
  reactiverCarte: vi.fn(),
}));
vi.mock("@/lib/api/client", async (original) => ({
  ...(await original<typeof import("@/lib/api/client")>()),
  ...api,
}));

beforeEach(() => vi.clearAllMocks());

const carte: MaCarte = {
  type: "membre",
  numero: "CS-M-000123",
  prenom: "Ama",
  nom: "Mensah",
  role: "membre",
  etablissement: "Lycée de Tokoin I",
  club: "Club Santé Tokoin",
  delivree_le: "2026-11-16T10:00:00Z",
  valide: true,
  cause: null,
  adresse_verification: "https://exemple.tg/carte/abc",
};

async function afficher(contenu: ReactNode) {
  const route = createRootRoute({ component: () => <>{contenu}</> });
  const router = createRouter({
    routeTree: route,
    history: createMemoryHistory({ initialEntries: ["/"] }),
  });
  render(<RouterProvider router={router} />);
  await act(() => router.load());
  await act(async () => {});
}

describe("ApercuCarte (spec 040)", () => {
  it("montre la carte valide, ses deux téléchargements et l'avertissement", () => {
    render(<ApercuCarte carte={carte} />);

    expect(screen.getByRole("status")).toHaveTextContent("Valide");
    expect(screen.getByRole("img")).toHaveAttribute("src", "/api/cartes/moi.png");
    expect(screen.getByRole("link", { name: /Télécharger en PDF/ })).toHaveAttribute(
      "href",
      "/api/cartes/moi.pdf",
    );
    expect(screen.getByRole("link", { name: /Télécharger en image/ })).toBeInTheDocument();
    expect(screen.getByText(/ne la publie pas sur les réseaux/)).toBeInTheDocument();
  });

  it("une carte non valide ne se télécharge pas et dit quoi faire", () => {
    render(
      <ApercuCarte
        carte={{
          ...carte,
          type: "encadreur",
          role: "encadreur",
          club: null,
          valide: false,
          cause: "sans_rattachement",
        }}
      />,
    );

    expect(screen.getByRole("status")).toHaveTextContent("Non valide");
    expect(screen.getByText(/dès que tu seras rattaché à un Club Santé/)).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /Télécharger/ })).toBeNull();
    expect(screen.queryByRole("img")).toBeNull();
  });
});

describe("VerificationCarte (spec 040)", () => {
  it("affiche le type, le numéro, le club et le statut, sans nom", () => {
    render(
      <VerificationCarte
        resultat={{
          type: "membre",
          numero: "CS-M-000123",
          club: null,
          valide: false,
          verifiee_le: "2026-11-16T10:00:00Z",
        }}
      />,
    );

    expect(screen.getByTestId("statut-carte")).toHaveTextContent("Non valide");
    expect(screen.getByText("CS-M-000123")).toBeInTheDocument();
    expect(screen.getByText("Non affilié")).toBeInTheDocument();
  });

  it("dit qu'une carte inconnue n'existe pas", () => {
    render(<VerificationCarte resultat={null} />);
    expect(screen.getByText("Cette carte n'existe pas")).toBeInTheDocument();
  });

  it("vérifie le code dans le navigateur et traite le 404 comme une carte inconnue", async () => {
    const { ErreurApi } = await import("@/lib/api/client");
    api.verifierCarte.mockRejectedValue(new ErreurApi(404, "Cette carte n'existe pas."));

    await act(async () => {
      render(<Verifier code="abc" />);
    });

    expect(api.verifierCarte).toHaveBeenCalledWith("abc");
    expect(screen.getByText("Cette carte n'existe pas")).toBeInTheDocument();
  });

  it("affiche une carte valide renvoyée par l'API", async () => {
    api.verifierCarte.mockResolvedValue({
      type: "encadreur",
      numero: "CS-E-000045",
      club: "Club Santé Tokoin",
      valide: true,
      verifiee_le: "2026-11-16T10:00:00Z",
    });

    await act(async () => {
      render(<Verifier code="abc" />);
    });

    expect(screen.getByTestId("statut-carte")).toHaveTextContent("Valide");
    expect(screen.getByText("Carte encadreur")).toBeInTheDocument();
  });
});

describe("CarteInscrit (spec 040)", () => {
  const admin: CarteAdmin = {
    type: "membre",
    numero: "CS-M-000123",
    valide: true,
    cause: null,
    club: null,
    delivree_le: "2026-11-16T10:00:00Z",
    suspendue_le: null,
    motif_suspension: null,
    historique: [{ action: "carte_delivree", le: "2026-11-16T10:00:00Z", motif: null }],
  };

  it("suspend la carte avec un motif d'au moins 10 caractères", async () => {
    api.suspendreCarte.mockResolvedValue(admin);
    await afficher(<CarteInscrit utilisateurId="u-1" carte={admin} gerable />);

    fireEvent.click(screen.getByRole("button", { name: /Suspendre la carte/ }));
    fireEvent.change(screen.getByRole("textbox"), { target: { value: "Fraude" } });
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Suspendre" }));
    });
    expect(api.suspendreCarte).not.toHaveBeenCalled();

    fireEvent.change(screen.getByRole("textbox"), {
      target: { value: "Carte prêtée à un tiers." },
    });
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Suspendre" }));
    });
    expect(api.suspendreCarte).toHaveBeenCalledWith("u-1", "Carte prêtée à un tiers.");
  });

  it("sans le droit de modifier, aucun bouton", async () => {
    await afficher(
      <CarteInscrit
        utilisateurId="u-1"
        carte={{ ...admin, valide: false, cause: "suspendue_par_l_equipe" }}
        gerable={false}
      />,
    );

    expect(screen.getByText(/Suspendue par l'équipe/)).toBeInTheDocument();
    expect(screen.queryByRole("button")).toBeNull();
  });
});
