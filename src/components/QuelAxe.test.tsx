import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  createMemoryHistory,
  createRootRoute,
  createRouter,
  RouterProvider,
} from "@tanstack/react-router";
import { act, fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { QuelAxeTest } from "./QuelAxeTest";
import { ErreurApi, type Moi, type QuestionnaireQuelAxe } from "@/lib/api/client";

const api = vi.hoisted(() => ({
  chargerMoi: vi.fn(),
  chargerQuelAxe: vi.fn(),
  calculerQuelAxe: vi.fn(),
}));
vi.mock("@/lib/api/client", async (original) => ({
  ...(await original<typeof import("@/lib/api/client")>()),
  ...api,
}));

const moi = (role: Moi["role"]): Moi => ({
  id: "u-1",
  identifiant: "ama",
  prenom: "Ama",
  nom: "K",
  role,
});

const questionnaire: QuestionnaireQuelAxe = {
  questions: [1, 2, 3, 4, 5].map((numero) => ({
    numero,
    libelle: `Question numéro ${numero}`,
    reponses: (["A", "B", "C", "D"] as const).map((id) => ({
      id,
      libelle: `Réponse ${id}${numero}`,
    })),
  })),
};

async function afficher() {
  const clientRequetes = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const route = createRootRoute({
    component: () => (
      <QueryClientProvider client={clientRequetes}>
        <QuelAxeTest />
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

beforeEach(() => {
  vi.clearAllMocks();
  api.chargerQuelAxe.mockResolvedValue(questionnaire);
});

const choisir = (libelle: string) =>
  fireEvent.click(screen.getByRole("radio", { name: new RegExp(libelle) }));
const suivant = () => fireEvent.click(screen.getByRole("button", { name: /Suivant|Voir mon axe/ }));

describe("Quel axe est fait pour toi ?", () => {
  it("invite un visiteur à se connecter, puis à revenir au test", async () => {
    api.chargerMoi.mockResolvedValue(null);
    await afficher();

    expect(
      await screen.findByText("Connecte-toi à ton compte Élève pour découvrir ton axe !"),
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Se connecter/ })).toHaveAttribute(
      "href",
      expect.stringContaining("redirection=%2F%3Ftest%3Dquel-axe%23quel-axe"),
    );
    expect(screen.getByRole("link", { name: /Créer mon compte Élève/ })).toHaveAttribute(
      "href",
      "/inscription?profil=eleve",
    );
    expect(api.chargerQuelAxe).not.toHaveBeenCalled();
  });

  it("réserve le jeu aux élèves", async () => {
    api.chargerMoi.mockResolvedValue(moi("encadreur"));
    await afficher();

    expect(await screen.findByText("Ce jeu est réservé aux élèves inscrits.")).toBeInTheDocument();
    expect(api.chargerQuelAxe).not.toHaveBeenCalled();
  });

  it("suit le refus de l'API si la session a expiré", async () => {
    api.chargerMoi.mockResolvedValue(moi("eleve"));
    api.chargerQuelAxe.mockRejectedValue(new ErreurApi(401, "Connecte-toi pour continuer."));
    await afficher();

    expect(
      await screen.findByText("Connecte-toi à ton compte Élève pour découvrir ton axe !"),
    ).toBeInTheDocument();
  });

  it("exige une réponse, permet de revenir en arrière et affiche le résultat de l'API", async () => {
    api.chargerMoi.mockResolvedValue(moi("eleve"));
    api.calculerQuelAxe.mockResolvedValue({
      principal: "TV",
      autres: ["EVSS", "LM"],
      scores: { GI: 0, EVSS: 6, TV: 11, SS: 0, GB: 1, LM: 2, SE: 0 },
    });
    await afficher();

    expect(await screen.findByText("Question 1 / 5")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Suivant/ })).toBeDisabled();
    choisir("Réponse B1");
    suivant();
    expect(screen.getByText("Question 2 / 5")).toBeInTheDocument();

    // Retour à la question 1 : la réponse est gardée, et on peut la changer.
    fireEvent.click(screen.getByRole("button", { name: /Précédent/ }));
    expect(screen.getByRole("radio", { name: /Réponse B1/ })).toHaveAttribute(
      "aria-checked",
      "true",
    );
    choisir("Réponse A1");
    suivant();
    choisir("Réponse A2");
    suivant();
    choisir("Réponse A3");
    suivant();
    choisir("Réponse D4");
    suivant();
    choisir("Réponse B5");
    await act(async () => suivant());

    expect(api.calculerQuelAxe).toHaveBeenCalledWith(["A", "A", "A", "D", "B"]);
    const resultat = await screen.findByRole("status");
    expect(resultat).toHaveTextContent("Ton axe principal");
    expect(resultat).toHaveTextContent("Production TV & Médias");
    expect(resultat).toHaveTextContent("Ta force : La créativité");
    expect(resultat).toHaveTextContent("Éducation aux Valeurs et à la Santé Sexuelle");
    expect(resultat).toHaveTextContent("Leadership & Masculinité positive");
    expect(resultat).not.toHaveTextContent(/univers/i);
    expect(screen.getByRole("link", { name: /Découvrir cet axe/ })).toHaveAttribute(
      "href",
      "/les-7-axes#axe-3",
    );

    fireEvent.click(screen.getByRole("button", { name: /Refaire le test/ }));
    expect(screen.getByText("Question 1 / 5")).toBeInTheDocument();
  });
});
