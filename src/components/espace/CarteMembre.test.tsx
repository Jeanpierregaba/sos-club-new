import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { CarteMembre } from "./CarteMembre";
import type { ProgressionJeux } from "@/lib/api/client";

const progression = (etoiles: number): ProgressionJeux => ({
  quiz_reussis: 42,
  niveaux: (["debutant", "intermediaire", "avance", "expert"] as const).map((niveau, i) => ({
    niveau,
    reussis: 1,
    total: 1,
    etoile: i < etoiles,
  })),
  niveau_courant: "debutant",
  points_quiz: 0,
  points_etoiles: 0,
  total: 0,
  gold: etoiles === 4,
  reussis: [],
});

describe("CarteMembre", () => {
  it("montre les quiz réussis et les étoiles obtenues", () => {
    render(<CarteMembre pseudonyme="Ama" club={null} jeux={progression(2)} />);
    expect(screen.getByText("Non affilié")).toBeInTheDocument();
    expect(screen.getByText("42")).toBeInTheDocument();
    expect(screen.getAllByLabelText(/obtenue$/)).toHaveLength(2);
    expect(screen.getByText("Membre")).toBeInTheDocument();
  });

  it("passe Gold avec les 4 étoiles", () => {
    render(
      <CarteMembre pseudonyme="Ama" club="Club Santé — Lycée de Tokoin" jeux={progression(4)} />,
    );
    expect(screen.getByText("GOLD")).toBeInTheDocument();
    expect(screen.getByText(/tirage au sort/)).toBeInTheDocument();
  });
});
