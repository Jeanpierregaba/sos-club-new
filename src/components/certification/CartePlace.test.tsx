import {
  createMemoryHistory,
  createRootRoute,
  createRouter,
  RouterProvider,
} from "@tanstack/react-router";
import { act, render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { describe, expect, it } from "vitest";

import type { BadgeParcours, PlaceParcours } from "@/lib/api/client";

import { BadgesParcours } from "./BadgesParcours";
import { CartePlace } from "./CartePlace";

async function afficher(contenu: ReactNode) {
  const router = createRouter({
    routeTree: createRootRoute({ component: () => <ol>{contenu}</ol> }),
    history: createMemoryHistory({ initialEntries: ["/"] }),
  });
  render(<RouterProvider router={router} />);
  await act(() => router.load());
}

const place = (champs: Partial<PlaceParcours>): PlaceParcours => ({
  place: 4,
  etat: "ouverte",
  quiz_id: "quiz-4",
  titre: "Les gestes barrières",
  description: null,
  contenu_de_test: false,
  fascicule: null,
  meilleur_score: null,
  tentatives_restantes: 10,
  tentative_en_cours: null,
  ...champs,
});

describe("CartePlace", () => {
  it("propose de jouer une place ouverte, et le fascicule à lire avant", async () => {
    await afficher(
      <CartePlace place={place({ fascicule: { id: "f1", titre: "Fascicule 4" } })} seuil={12} />,
    );

    expect(screen.getByRole("link", { name: /Jouer le quiz 4/ })).toHaveAttribute(
      "href",
      "/certification/parcours/4",
    );
    expect(screen.getByRole("link", { name: /Lire le fascicule : Fascicule 4/ })).toHaveAttribute(
      "href",
      "/api/bibliotheque/f1/fichier",
    );
  });

  it("explique une place verrouillée, sans bouton pour jouer", async () => {
    await afficher(<CartePlace place={place({ etat: "verrouillee" })} seuil={12} />);

    expect(screen.getByText("Réussis d'abord le quiz 3 pour l'ouvrir.")).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /Jouer/ })).not.toBeInTheDocument();
  });

  it("annonce une place sans quiz publié", async () => {
    await afficher(
      <CartePlace place={place({ etat: "bientot", quiz_id: null, titre: null })} seuil={12} />,
    );

    expect(screen.getByText("Bientôt disponible")).toBeInTheDocument();
    expect(screen.getByText("Quiz à venir")).toBeInTheDocument();
  });

  it("propose de rejouer une place réussie, avec le meilleur score", async () => {
    await afficher(
      <CartePlace place={place({ etat: "reussie", meilleur_score: 14 })} seuil={12} />,
    );

    expect(screen.getByText("Meilleur score : 14 (réussite à 12)")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Rejouer le quiz 4/ })).toBeInTheDocument();
  });
});

describe("BadgesParcours", () => {
  it("montre le palier des badges à venir", async () => {
    const badges: BadgeParcours[] = [
      { rang: 1, nom: "Bronze", palier: 3, obtenu_le: "2026-11-09T10:00:00Z" },
      { rang: 2, nom: "Argent", palier: 5, obtenu_le: null },
    ];

    await afficher(<BadgesParcours badges={badges} />);

    expect(screen.getByText("Après 5 quiz réussis")).toBeInTheDocument();
    expect(screen.getByText(/^Obtenu le/)).toBeInTheDocument();
  });
});
