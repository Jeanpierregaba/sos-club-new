import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  createMemoryHistory,
  createRootRoute,
  createRouter,
  RouterProvider,
} from "@tanstack/react-router";
import { act, fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { Commentaires } from "./Commentaires";
import {
  ErreurApi,
  type CommentaireAuteur,
  type CommentairesPublics,
  type Moi,
} from "@/lib/api/client";

const api = vi.hoisted(() => ({
  chargerMoi: vi.fn(),
  chargerCommentaires: vi.fn(),
  chargerMesCommentaires: vi.fn(),
  commenterArticle: vi.fn(),
}));
vi.mock("@/lib/api/client", async (original) => ({
  ...(await original<typeof import("@/lib/api/client")>()),
  ...api,
}));

const eleve: Moi = { id: "u-1", identifiant: "ama", prenom: "Ama", nom: "K", role: "eleve" };
const aucun: CommentairesPublics = { commentaires: [], page: 1, pages: 1, total: 0 };
const piege = '<img src=x onerror="alert(1)"> **gras**';
const un: CommentairesPublics = {
  commentaires: [
    {
      id: "c1",
      texte: piege,
      signature: { profil: "eleve", nom: "Kofi des Plateaux", club: "Club Santé", fonction: null },
      publie_le: "2026-11-08T10:00:00Z",
    },
  ],
  page: 1,
  pages: 1,
  total: 1,
};
const envoye: CommentaireAuteur = {
  id: "c2",
  texte: "Bravo !",
  etat: "en_attente",
  cree_le: "2026-11-08T10:00:00Z",
  publie_le: null,
  article: { adresse: "lavage", titre: "Le lavage des mains" },
  motif: null,
};

async function afficher() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const route = createRootRoute({
    component: () => (
      <QueryClientProvider client={client}>
        <Commentaires adresse="lavage" />
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

// La case de Radix mesure sa taille dans un formulaire ; jsdom n'a pas ResizeObserver.
globalThis.ResizeObserver ??= class {
  observe() {}
  unobserve() {}
  disconnect() {}
};

beforeEach(() => {
  vi.clearAllMocks();
  api.chargerMesCommentaires.mockResolvedValue({ commentaires: [] });
});

describe("Commentaires", () => {
  it("invite un visiteur à se connecter, sans champ", async () => {
    api.chargerMoi.mockResolvedValue(null);
    api.chargerCommentaires.mockResolvedValue(aucun);
    await afficher();

    expect(await screen.findByRole("link", { name: "Connecte-toi" })).toHaveAttribute(
      "href",
      "/connexion",
    );
    expect(screen.queryByLabelText("Ton commentaire")).not.toBeInTheDocument();
    expect(screen.getByText(/Personne n'a encore commenté/)).toBeInTheDocument();
  });

  it("affiche le texte tel quel, sans l'interpréter", async () => {
    api.chargerMoi.mockResolvedValue(null);
    api.chargerCommentaires.mockResolvedValue(un);
    const { container } = await afficher();

    expect(await screen.findByText(piege)).toBeInTheDocument();
    expect(screen.getByText("Kofi des Plateaux · Club Santé")).toBeInTheDocument();
    expect(container.querySelector("img")).toBeNull();
    expect(container.querySelector("strong")?.textContent).toBe("Kofi des Plateaux · Club Santé");
  });

  it("confirme l'envoi d'un élève et montre son commentaire en attente", async () => {
    api.chargerMoi.mockResolvedValue(eleve);
    api.chargerCommentaires.mockResolvedValue(aucun);
    api.commenterArticle.mockResolvedValue(envoye);
    await afficher();

    const champ = await screen.findByLabelText("Ton commentaire");
    const bouton = screen.getByRole("button", { name: /Envoyer/ });
    expect(bouton).toBeDisabled();
    fireEvent.change(champ, { target: { value: "Bravo !" } });
    api.chargerMesCommentaires.mockResolvedValue({ commentaires: [envoye] });
    await act(async () => fireEvent.click(bouton));

    expect(api.commenterArticle).toHaveBeenCalledWith("lavage", "Bravo !", true);
    expect(await screen.findByRole("status")).toHaveTextContent(
      "Merci ! Ton commentaire sera visible après sa validation.",
    );
    expect(await screen.findByText(/en attente de validation/)).toBeInTheDocument();
    expect(champ).toHaveValue("");
  });

  it("explique le plafond du jour", async () => {
    api.chargerMoi.mockResolvedValue(eleve);
    api.chargerCommentaires.mockResolvedValue(aucun);
    api.commenterArticle.mockRejectedValue(
      new ErreurApi(429, "Tu as déjà envoyé 20 commentaires aujourd'hui : réessaie demain."),
    );
    await afficher();

    fireEvent.change(await screen.findByLabelText("Ton commentaire"), {
      target: { value: "Encore un" },
    });
    await act(async () => fireEvent.click(screen.getByRole("button", { name: /Envoyer/ })));

    expect(await screen.findByText(/20 commentaires aujourd'hui/)).toBeInTheDocument();
  });

  it("n'offre pas de champ à un collaborateur de l'équipe", async () => {
    api.chargerMoi.mockResolvedValue({ ...eleve, role: "admin" });
    api.chargerCommentaires.mockResolvedValue(aucun);
    await afficher();

    await screen.findByText(/Personne n'a encore commenté/);
    expect(screen.queryByLabelText("Ton commentaire")).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Connecte-toi" })).not.toBeInTheDocument();
  });

  it("laisse un élève masquer son club", async () => {
    api.chargerMoi.mockResolvedValue(eleve);
    api.chargerCommentaires.mockResolvedValue(aucun);
    api.commenterArticle.mockResolvedValue(envoye);
    await afficher();

    fireEvent.change(await screen.findByLabelText("Ton commentaire"), {
      target: { value: "Bravo !" },
    });
    fireEvent.click(screen.getByRole("checkbox", { name: /Afficher mon club/ }));
    await act(async () => fireEvent.click(screen.getByRole("button", { name: /Envoyer/ })));

    expect(api.commenterArticle).toHaveBeenCalledWith("lavage", "Bravo !", false);
  });

  it("explique à un encadreur non vérifié qu'il ne peut pas encore commenter", async () => {
    api.chargerMoi.mockResolvedValue({ ...eleve, role: "encadreur" });
    api.chargerCommentaires.mockResolvedValue(aucun);
    api.chargerMesCommentaires.mockRejectedValue(
      new ErreurApi(
        403,
        "Ton compte encadreur doit d'abord être vérifié par l'équipe des Clubs Santé.",
      ),
    );
    await afficher();

    expect(await screen.findByText(/doit d'abord être vérifié/)).toBeInTheDocument();
    expect(screen.queryByLabelText("Ton commentaire")).not.toBeInTheDocument();
    expect(screen.queryByRole("checkbox")).not.toBeInTheDocument();
  });
});
