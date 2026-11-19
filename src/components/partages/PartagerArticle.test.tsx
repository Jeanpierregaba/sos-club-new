import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { PartagerArticle } from "./PartagerArticle";
import {
  ErreurApi,
  type EtatPartagesArticle,
  type Moi,
  type PartageAuteur,
} from "@/lib/api/client";

const api = vi.hoisted(() => ({
  chargerMoi: vi.fn(),
  chargerEtatPartages: vi.fn(),
  declarerPartage: vi.fn(),
}));
vi.mock("@/lib/api/client", async (original) => ({
  ...(await original<typeof import("@/lib/api/client")>()),
  ...api,
}));

const eleve: Moi = {
  id: "u-1",
  identifiant: "ama",
  prenom: "Ama",
  nom: "K",
  role: "eleve",
  mot_de_passe_provisoire: false,
};
const libre: EtatPartagesArticle = {
  nature: "partage",
  reseaux_declares: [],
  restantes_aujourdhui: 3,
};
const declare: PartageAuteur = {
  id: "p1",
  article_titre: "Le lavage des mains",
  article_adresse: "lavage",
  reseau: "facebook",
  lien: "https://facebook.com/ama/posts/1",
  nature: "partage",
  etat: "en_attente",
  motif: null,
  points: null,
  declare_le: "2026-11-19T10:00:00Z",
};

async function afficher() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const rendu = render(
    <QueryClientProvider client={client}>
      <PartagerArticle adresse="lavage" titre="Le lavage des mains" />
    </QueryClientProvider>,
  );
  await act(async () => {});
  return rendu;
}

beforeEach(() => {
  vi.clearAllMocks();
  api.chargerEtatPartages.mockResolvedValue(libre);
});

describe("PartagerArticle", () => {
  it("propose les liens de partage à un visiteur, sans formulaire", async () => {
    api.chargerMoi.mockResolvedValue(null);
    await afficher();

    const facebook = await screen.findByRole("link", { name: "Facebook" });
    expect(facebook.getAttribute("href")).toContain("facebook.com/sharer/sharer.php?u=");
    expect(facebook).toHaveAttribute("rel", "noopener noreferrer");
    expect(screen.getByRole("button", { name: /Copier le lien/ })).toBeInTheDocument();
    expect(screen.queryByLabelText("Lien de ta publication")).not.toBeInTheDocument();
    expect(api.chargerEtatPartages).not.toHaveBeenCalled();
  });

  it("annonce +50 par réseau à l'autrice et déclare son partage", async () => {
    api.chargerMoi.mockResolvedValue(eleve);
    api.declarerPartage.mockResolvedValue(declare);
    await afficher();

    expect(await screen.findByText(/\+50 points par réseau/)).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Réseau"), { target: { value: "facebook" } });
    fireEvent.change(screen.getByLabelText("Lien de ta publication"), {
      target: { value: "  https://facebook.com/ama/posts/1 " },
    });
    api.chargerEtatPartages.mockResolvedValue({
      ...libre,
      reseaux_declares: ["facebook"],
      restantes_aujourdhui: 2,
    });
    await act(async () => fireEvent.click(screen.getByRole("button", { name: /Déclarer/ })));

    expect(api.declarerPartage).toHaveBeenCalledWith(
      "lavage",
      "facebook",
      "https://facebook.com/ama/posts/1",
    );
    expect(await screen.findByRole("status")).toHaveTextContent(/vérifié par l'équipe/);
    expect(await screen.findByText(/Déjà déclaré : Facebook/)).toBeInTheDocument();
    expect(screen.queryByRole("option", { name: "Facebook" })).not.toBeInTheDocument();
  });

  it("annonce +10 pour relayer l'article d'un autre, une seule fois", async () => {
    api.chargerMoi.mockResolvedValue(eleve);
    api.chargerEtatPartages.mockResolvedValue({
      nature: "republication",
      reseaux_declares: ["instagram"],
      restantes_aujourdhui: 2,
    });
    await afficher();

    expect(await screen.findByText(/\+10 points une fois/)).toBeInTheDocument();
    expect(screen.getByText(/republication de cet article est déjà déclarée/)).toBeInTheDocument();
    expect(screen.queryByLabelText("Lien de ta publication")).not.toBeInTheDocument();
  });

  it("explique le plafond du jour", async () => {
    api.chargerMoi.mockResolvedValue(eleve);
    api.chargerEtatPartages.mockResolvedValue({ ...libre, restantes_aujourdhui: 0 });
    await afficher();

    expect(await screen.findByText(/3 déclarations du jour/)).toBeInTheDocument();
  });

  it("montre le refus de l'API", async () => {
    api.chargerMoi.mockResolvedValue(eleve);
    api.declarerPartage.mockRejectedValue(
      new ErreurApi(422, "Ce lien n'est pas une publication Facebook."),
    );
    await afficher();

    fireEvent.change(await screen.findByLabelText("Réseau"), { target: { value: "facebook" } });
    fireEvent.change(screen.getByLabelText("Lien de ta publication"), {
      target: { value: "https://tiktok.com/@ama/video/1" },
    });
    await act(async () => fireEvent.click(screen.getByRole("button", { name: /Déclarer/ })));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Ce lien n'est pas une publication Facebook.",
    );
  });

  it("explique à un encadreur non vérifié pourquoi il ne déclare pas", async () => {
    api.chargerMoi.mockResolvedValue({ ...eleve, role: "encadreur" });
    api.chargerEtatPartages.mockRejectedValue(
      new ErreurApi(
        403,
        "Ton compte encadreur doit d'abord être vérifié par l'équipe des Clubs Santé.",
      ),
    );
    await afficher();

    expect(await screen.findByText(/doit d'abord être vérifié/)).toBeInTheDocument();
  });
});
