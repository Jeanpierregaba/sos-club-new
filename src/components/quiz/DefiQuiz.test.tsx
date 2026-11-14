import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  createMemoryHistory,
  createRootRoute,
  createRouter,
  RouterProvider,
} from "@tanstack/react-router";
import { act, fireEvent, render, screen } from "@testing-library/react";
import { useState } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { DefiQuiz, type Defi } from "./DefiQuiz";
import { ErreurApi, type CatalogueQuiz, type EtatPartie, type Moi } from "@/lib/api/client";

const api = vi.hoisted(() => ({
  chargerMoi: vi.fn(),
  chargerQuiz: vi.fn(),
  lancerQuiz: vi.fn(),
  lancerQuizOuvert: vi.fn(),
}));
vi.mock("@/lib/api/client", async (original) => ({
  ...(await original<typeof import("@/lib/api/client")>()),
  ...api,
}));

const quiz = {
  id: "q-1",
  titre: "IST et VIH/SIDA",
  description: "Lot 4 — EVSS · questions 1 à 40.",
  axe_code: "sante-sexuelle-evss",
  nb_questions_reserve: 40,
  numero: 42,
  niveau: "debutant" as const,
};
const defi: Defi = { titre: "Prévenir les IST", numero: 42, quiz };

const catalogue = (connecte: boolean): CatalogueQuiz => ({
  nb_questions: 15,
  seuil: 12,
  temps_ms: 20000,
  limite: 3,
  restants: connecte ? null : 3,
  connecte,
  quiz: [quiz],
});

const premiere: EtatPartie = {
  tentative_id: "t-1",
  quiz_id: "q-1",
  titre: quiz.titre,
  total: 15,
  question: {
    rang: 1,
    enonce: "Comment se transmet le VIH ?",
    choix: ["A", "B", "C"],
    temps_ms: 20000,
    restant_ms: 20000,
  },
  resultat: null,
};

const eleve: Moi = { id: "u-1", identifiant: "ama", prenom: "Ama", nom: "K", role: "eleve" };

const autre: Defi = {
  titre: "Le préservatif",
  numero: 43,
  quiz: { ...quiz, id: "q-2", titre: "Contraception" },
};

// Le défi ouvert peut changer depuis le test, comme quand on ferme la fenêtre pour en ouvrir une autre.
let changerDefi: (d: Defi | null) => void = () => undefined;

function Page({ connecte }: { connecte: boolean }) {
  const [courant, setCourant] = useState<Defi | null>(defi);
  changerDefi = setCourant;
  return (
    <DefiQuiz defi={courant} catalogue={catalogue(connecte)} onFermer={() => setCourant(null)} />
  );
}

async function afficher(connecte: boolean) {
  const clientRequetes = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const route = createRootRoute({
    component: () => (
      <QueryClientProvider client={clientRequetes}>
        <Page connecte={connecte} />
      </QueryClientProvider>
    ),
  });
  const router = createRouter({
    routeTree: route,
    history: createMemoryHistory({ initialEntries: ["/jeux"] }),
  });
  render(<RouterProvider router={router} />);
  await act(() => router.load());
}

beforeEach(() => {
  vi.clearAllMocks();
  api.chargerQuiz.mockResolvedValue({ nb_questions: 15, seuil: 12, quiz: [] });
});

describe("DefiQuiz", () => {
  it("ouvre le défi dans une fenêtre avec le chrono de 20 secondes, sans compteur d'essai", async () => {
    api.chargerMoi.mockRejectedValue(new ErreurApi(401, "Non connecté"));
    await afficher(false);

    expect(screen.getByRole("dialog")).toBeTruthy();
    expect(screen.getByText("Prévenir les IST")).toBeTruthy();
    expect(screen.getByText(/20 secondes pour chacune/)).toBeTruthy();
    expect(screen.queryByText(/il t'en reste/i)).toBeNull();
  });

  it("fait jouer un joueur sans compte à l'essai", async () => {
    api.chargerMoi.mockRejectedValue(new ErreurApi(401, "Non connecté"));
    api.lancerQuizOuvert.mockResolvedValue(premiere);
    await afficher(false);

    await act(async () => fireEvent.click(screen.getByRole("button", { name: /Commencer/ })));

    expect(api.lancerQuizOuvert).toHaveBeenCalledWith("q-1");
    expect(api.lancerQuiz).not.toHaveBeenCalled();
    expect(screen.getByText("Comment se transmet le VIH ?")).toBeTruthy();
  });

  it("annonce la fin de la période d'essai et invite à créer un compte", async () => {
    api.chargerMoi.mockRejectedValue(new ErreurApi(401, "Non connecté"));
    api.lancerQuizOuvert.mockRejectedValue(
      new ErreurApi(403, "Tu as joué tes 3 quiz gratuits.", "fin-essai"),
    );
    await afficher(false);

    await act(async () => fireEvent.click(screen.getByRole("button", { name: /Commencer/ })));

    expect(screen.getByText("Ta période d'essai est terminée")).toBeTruthy();
    expect(screen.getByRole("link", { name: /Créer mon compte/ }).getAttribute("href")).toBe(
      "/inscription",
    );
    expect(screen.getByRole("link", { name: /J'ai déjà un compte/ })).toBeTruthy();
  });

  it("garde le message de l'API pour un 429, qui n'est pas la fin de l'essai", async () => {
    api.chargerMoi.mockRejectedValue(new ErreurApi(401, "Non connecté"));
    api.lancerQuizOuvert.mockRejectedValue(
      new ErreurApi(429, "Trop de parties sans compte depuis ce réseau : crée ton compte."),
    );
    await afficher(false);

    await act(async () => fireEvent.click(screen.getByRole("button", { name: /Commencer/ })));

    expect(screen.getByText(/Trop de parties sans compte/)).toBeTruthy();
    expect(screen.queryByText("Ta période d'essai est terminée")).toBeNull();
  });

  it("un autre refus 403 n'est pas une fin d'essai (bug du 2026-11-10)", async () => {
    api.chargerMoi.mockRejectedValue(new ErreurApi(401, "Non connecté"));
    api.lancerQuizOuvert.mockRejectedValue(
      new ErreurApi(403, "Cette action ne peut venir que du site."),
    );
    await afficher(false);

    await act(async () => fireEvent.click(screen.getByRole("button", { name: /Commencer/ })));

    expect(screen.queryByText("Ta période d'essai est terminée")).toBeNull();
    expect(screen.getByText(/ne peut venir que du site/)).toBeInTheDocument();
  });

  it("affiche une erreur réseau au lancement sans quitter l'écran d'accueil", async () => {
    api.chargerMoi.mockRejectedValue(new ErreurApi(401, "Non connecté"));
    api.lancerQuizOuvert.mockRejectedValue(new TypeError("Failed to fetch"));
    await afficher(false);

    await act(async () => fireEvent.click(screen.getByRole("button", { name: /Commencer/ })));

    expect(screen.getByRole("alert")).toBeTruthy();
    expect(screen.getByRole("button", { name: /Commencer/ })).toBeTruthy();
  });

  it("repart de l'accueil quand on ouvre un autre défi, et ignore une réponse arrivée trop tard", async () => {
    api.chargerMoi.mockRejectedValue(new ErreurApi(401, "Non connecté"));
    let repondre: (etat: EtatPartie) => void = () => undefined;
    api.lancerQuizOuvert.mockReturnValue(new Promise<EtatPartie>((r) => (repondre = r)));
    await afficher(false);

    await act(async () => fireEvent.click(screen.getByRole("button", { name: /Commencer/ })));
    await act(async () => changerDefi(null));
    await act(async () => changerDefi(autre));
    await act(async () => repondre(premiere));

    expect(screen.getByText("Le préservatif")).toBeTruthy();
    expect(screen.queryByText("Comment se transmet le VIH ?")).toBeNull();
    expect((screen.getByRole("button", { name: /Commencer/ }) as HTMLButtonElement).disabled).toBe(
      false,
    );
  });

  it("explique à un compte qui ne peut pas jouer pourquoi, au lieu de proposer de commencer", async () => {
    api.chargerMoi.mockResolvedValue({ ...eleve, role: "admin" });
    api.chargerQuiz.mockRejectedValue(
      new ErreurApi(403, "Les quiz sont réservés aux comptes inscrits."),
    );
    await afficher(true);

    expect(await screen.findByText(/jouent en mode test, depuis l'espace admin/)).toBeTruthy();
    expect(screen.queryByRole("button", { name: /Commencer/ })).toBeNull();
  });

  it("fait jouer un compte connecté sa partie habituelle", async () => {
    api.chargerMoi.mockResolvedValue(eleve);
    api.lancerQuiz.mockResolvedValue(premiere);
    await afficher(true);
    await act(async () => undefined);

    await act(async () => fireEvent.click(screen.getByRole("button", { name: /Commencer/ })));

    expect(api.lancerQuiz).toHaveBeenCalledWith("q-1");
    expect(api.lancerQuizOuvert).not.toHaveBeenCalled();
    expect(screen.getByText("Comment se transmet le VIH ?")).toBeTruthy();
  });

  it("propose à un compte connecté de reprendre sa partie en cours", async () => {
    api.chargerMoi.mockResolvedValue(eleve);
    api.chargerQuiz.mockResolvedValue({
      nb_questions: 15,
      seuil: 12,
      quiz: [{ ...quiz, tentative_en_cours: "t-9" }],
    });
    await afficher(true);

    expect(await screen.findByRole("button", { name: /Reprendre ma partie/ })).toBeTruthy();
  });
});
