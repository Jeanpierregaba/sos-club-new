import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { DetailTentative } from "@/components/admin/fiche-inscrit/DetailTentative";
import type { DetailTentative as Detail } from "@/lib/api/client";

const detail = {
  tentative: {
    id: "t1",
    quiz_titre: "Hygiène des mains",
    axe: "Hygiène",
    parcours: "jeux",
    place: null,
    niveau: "debutant",
    commencee_le: "2026-11-09T10:00:00Z",
    terminee_le: "2026-11-09T10:01:05Z",
    etat: "terminee",
    essai: false,
    score: 1,
    nb_questions: 3,
    reussie: false,
    duree_s: 65,
    abandonnee: false,
    points: null,
  },
  temps_imparti_s: 15,
  questions: [
    { rang: 1, enonce: "Question 1 ?", etat: "juste", reponse: "Juste 1", secondes: 4.2 },
    { rang: 2, enonce: "Question 2 ?", etat: "temps_ecoule", reponse: null, secondes: 15 },
    { rang: 3, enonce: "Question 3 ?", etat: "non_posee", reponse: null, secondes: null },
  ],
} satisfies Detail;

vi.mock("@/lib/api/client", () => ({
  chargerTentativeInscrit: vi.fn(() => Promise.resolve(detail)),
}));

describe("DetailTentative", () => {
  it("montre chaque question, son état et le temps mis", async () => {
    render(<DetailTentative id="u1" tentativeId="t1" fermer={() => {}} />);

    expect(await screen.findByText("1. Question 1 ?")).toBeTruthy();
    expect(screen.getByText("Réponse : Juste 1")).toBeTruthy();
    expect(screen.getByText("4,2 s")).toBeTruthy();
    expect(screen.getByText("Temps écoulé")).toBeTruthy();
    expect(screen.getByText("15 s")).toBeTruthy();
    expect(screen.getByText("Non posée")).toBeTruthy();
    expect(screen.getByText(/temps de jeu 1 min 05 s/)).toBeTruthy();
  });
});
