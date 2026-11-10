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
import {
  ErreurApi,
  type EtatQuelAxe,
  type Moi,
  type PartieQuelAxe,
  type QuestionQuelAxe,
} from "@/lib/api/client";

const api = vi.hoisted(() => ({
  chargerMoi: vi.fn(),
  etatQuelAxe: vi.fn(),
  commencerQuelAxe: vi.fn(),
  repondreQuelAxe: vi.fn(),
  terminerQuelAxe: vi.fn(),
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

const questions: QuestionQuelAxe[] = [1, 2, 3, 4, 5, 6, 7].map((numero) => ({
  numero,
  libelle: `Question numéro ${numero}`,
  reponses: (["A", "B", "C", "D"] as const).map((id) => ({
    id,
    libelle: `Réponse ${id}${numero}`,
  })),
}));

const terminee = (numero: number, principal: "TV" | "SE"): PartieQuelAxe => ({
  id: `p-${numero}`,
  numero,
  reponses: Array(7).fill("A"),
  commencee_le: "2026-11-10T10:00:00Z",
  terminee_le: "2026-11-10T10:05:00Z",
  resultat: { principal, autres: ["EVSS", "LM"] },
});

// Un faux serveur : les parties de l'élève, gardées comme le ferait l'API.
let parties: PartieQuelAxe[] = [];
const etat = (): EtatQuelAxe => {
  const enCours = parties.find((p) => p.terminee_le === null) ?? null;
  return {
    questions,
    limite: 3,
    utilisees: parties.length,
    restantes: 3 - parties.length,
    en_cours: enCours,
    historique: parties.filter((p) => p.terminee_le !== null).reverse(),
  };
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
  parties = [];
  api.etatQuelAxe.mockImplementation(async () => etat());
  api.commencerQuelAxe.mockImplementation(async () => {
    const enCours = parties.find((p) => p.terminee_le === null);
    if (enCours) return enCours;
    if (parties.length >= 3) throw new ErreurApi(403, "Tu as utilisé tes 3 participations !");
    const partie: PartieQuelAxe = {
      id: `p-${parties.length + 1}`,
      numero: parties.length + 1,
      reponses: Array(7).fill(null),
      commencee_le: "2026-11-10T10:00:00Z",
      terminee_le: null,
      resultat: null,
    };
    parties.push(partie);
    return partie;
  });
  api.repondreQuelAxe.mockImplementation(
    async (id: string, numero: number, lettre: "A" | "B" | "C" | "D") => {
      const partie = parties.find((p) => p.id === id)!;
      partie.reponses = partie.reponses.map((r, i) => (i === numero - 1 ? lettre : r));
      return { ...partie };
    },
  );
  api.terminerQuelAxe.mockImplementation(async (id: string) => {
    const partie = parties.find((p) => p.id === id)!;
    partie.terminee_le = "2026-11-10T10:05:00Z";
    partie.resultat = { principal: "TV", autres: ["EVSS", "LM"] };
    return { ...partie };
  });
});

const choisir = async (libelle: string) => {
  await act(async () => fireEvent.click(screen.getByRole("radio", { name: new RegExp(libelle) })));
};
const suivant = async () => {
  await act(async () =>
    fireEvent.click(screen.getByRole("button", { name: /Suivant|Voir mon axe/ })),
  );
};

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
    expect(api.etatQuelAxe).not.toHaveBeenCalled();
  });

  it("réserve le jeu aux élèves", async () => {
    api.chargerMoi.mockResolvedValue(moi("encadreur"));
    await afficher();

    expect(await screen.findByText("Ce jeu est réservé aux élèves inscrits.")).toBeInTheDocument();
    expect(api.etatQuelAxe).not.toHaveBeenCalled();
  });

  it("suit le refus de l'API si la session a expiré", async () => {
    api.chargerMoi.mockResolvedValue(moi("eleve"));
    api.etatQuelAxe.mockRejectedValue(new ErreurApi(401, "Connecte-toi pour continuer."));
    await afficher();

    expect(
      await screen.findByText("Connecte-toi à ton compte Élève pour découvrir ton axe !"),
    ).toBeInTheDocument();
  });

  it("montre le compteur sans rien décompter tant que l'élève ne commence pas", async () => {
    api.chargerMoi.mockResolvedValue(moi("eleve"));
    await afficher();

    expect(await screen.findByText("Participations utilisées")).toBeInTheDocument();
    expect(document.body).toHaveTextContent("0/3");
    expect(screen.getByRole("button", { name: /Commencer/ })).toBeInTheDocument();
    expect(api.commencerQuelAxe).not.toHaveBeenCalled();
    expect(document.body).not.toHaveTextContent(/cinq questions|5 questions/i);
  });

  it("enregistre chaque réponse, permet de revenir en arrière et affiche le résultat de l'API", async () => {
    api.chargerMoi.mockResolvedValue(moi("eleve"));
    await afficher();
    await act(async () =>
      fireEvent.click(await screen.findByRole("button", { name: /Commencer/ })),
    );

    expect(await screen.findByText(/Question 1 sur 7/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Suivant/ })).toBeDisabled();
    await choisir("Réponse B1");
    expect(api.repondreQuelAxe).toHaveBeenLastCalledWith("p-1", 1, "B");
    await suivant();
    expect(screen.getByText(/Question 2 sur 7/)).toBeInTheDocument();

    // Retour à la question 1 : la réponse est gardée, et on peut la changer.
    fireEvent.click(screen.getByRole("button", { name: /Précédent/ }));
    expect(screen.getByRole("radio", { name: /Réponse B1/ })).toHaveAttribute(
      "aria-checked",
      "true",
    );
    await choisir("Réponse A1");
    expect(api.repondreQuelAxe).toHaveBeenLastCalledWith("p-1", 1, "A");
    for (let n = 1; n <= 7; n++) {
      if (n > 1) await choisir(`Réponse A${n}`);
      await suivant();
    }

    expect(api.terminerQuelAxe).toHaveBeenCalledWith("p-1");
    const titre = await screen.findByRole("status");
    expect(titre).toHaveTextContent("Ton axe principal");
    expect(titre).toHaveTextContent("Production TV & Médias");
    expect(document.body).toHaveTextContent("Ta force : La créativité");
    expect(screen.getByRole("link", { name: /Découvrir cet axe/ })).toHaveAttribute(
      "href",
      "/les-7-axes#axe-3",
    );
    expect(
      await screen.findByRole("button", { name: /Rejouer \(2 parties restantes\)/ }),
    ).toBeInTheDocument();
    expect(document.body).not.toHaveTextContent(/Refaire le test/);
  });

  it("propose de reprendre une partie en cours au lieu d'en commencer une autre", async () => {
    api.chargerMoi.mockResolvedValue(moi("eleve"));
    parties = [
      {
        ...terminee(1, "SE"),
        terminee_le: null,
        resultat: null,
        reponses: ["A", "B", "C", null, null, null, null],
      },
    ];
    await afficher();

    await act(async () =>
      fireEvent.click(await screen.findByRole("button", { name: /Reprendre la partie \(3\/7\)/ })),
    );

    // Reprise à la première question sans réponse, sans nouveau démarrage.
    expect(screen.getByText(/Question 4 sur 7/)).toBeInTheDocument();
    expect(api.commencerQuelAxe).not.toHaveBeenCalled();
  });

  it("après 3 parties, plus de Rejouer : les résultats restent consultables", async () => {
    api.chargerMoi.mockResolvedValue(moi("eleve"));
    parties = [terminee(1, "TV"), terminee(2, "SE"), terminee(3, "TV")];
    await afficher();

    expect(await screen.findByText(/Tu as utilisé tes 3 participations !/)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Commencer/ })).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Découvrir les axes/ })).toHaveAttribute(
      "href",
      "/les-7-axes",
    );

    fireEvent.click(screen.getByRole("button", { name: /Partie 2/ }));

    expect(await screen.findByRole("status")).toHaveTextContent("Santé mentale & Environnement");
    expect(screen.queryByRole("button", { name: /Rejouer/ })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Partager mon résultat/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Voir mes résultats/ })).toBeInTheDocument();
  });

  it("garde l'élève sur la question si la réponse n'a pas été enregistrée", async () => {
    api.chargerMoi.mockResolvedValue(moi("eleve"));
    api.repondreQuelAxe.mockRejectedValueOnce(new ErreurApi(0, "Indisponible"));
    await afficher();
    await act(async () =>
      fireEvent.click(await screen.findByRole("button", { name: /Commencer/ })),
    );

    await choisir("Réponse A1");

    expect(screen.getByRole("alert")).toHaveTextContent("Ta réponse n’a pas été enregistrée.");
    expect(screen.getByRole("button", { name: /Suivant/ })).toBeDisabled();
  });

  it("ne montre aucun résultat tant que l'API n'a pas terminé la partie", async () => {
    api.chargerMoi.mockResolvedValue(moi("eleve"));
    api.terminerQuelAxe.mockRejectedValueOnce(new ErreurApi(0, "Indisponible"));
    await afficher();
    await act(async () =>
      fireEvent.click(await screen.findByRole("button", { name: /Commencer/ })),
    );
    for (let n = 1; n <= 7; n++) {
      await choisir(`Réponse A${n}`);
      await suivant();
    }

    expect(screen.getByRole("alert")).toHaveTextContent("Ton résultat n’a pas pu être calculé.");
    expect(screen.queryByText("Ton axe principal")).not.toBeInTheDocument();
    expect(screen.getByText(/Question 7 sur 7/)).toBeInTheDocument();
  });

  it("revient à l'accueil du jeu si la partie a été terminée sur un autre appareil", async () => {
    api.chargerMoi.mockResolvedValue(moi("eleve"));
    await afficher();
    await act(async () =>
      fireEvent.click(await screen.findByRole("button", { name: /Commencer/ })),
    );
    parties[0] = terminee(1, "TV");
    api.repondreQuelAxe.mockRejectedValueOnce(new ErreurApi(409, "Cette partie est terminée."));

    await choisir("Réponse A1");

    expect(await screen.findByText(/Partie 1 · 10 novembre 2026/)).toBeInTheDocument();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });
});
