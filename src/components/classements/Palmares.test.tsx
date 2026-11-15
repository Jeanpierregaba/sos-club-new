import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Palmares } from "./Palmares";

describe("Palmares (spec 037)", () => {
  it("montre les lauréats avec leur distinction, leur club et leur DRE", () => {
    render(
      <Palmares
        palmares={{
          semestres: [
            {
              libelle: "S1 2026",
              debut: "2026-02-01",
              fin: "2026-06-30",
              laureats: [
                {
                  place: 1,
                  distinction: "Grand Champion",
                  pseudonyme: "Ama",
                  club: "Club Santé Tokoin",
                  dre: "Grand Lomé",
                  points: 300,
                },
                {
                  place: 2,
                  distinction: "Vice-Champion",
                  pseudonyme: "Kofi",
                  club: null,
                  dre: "Maritime",
                  points: 200,
                },
              ],
            },
          ],
        }}
      />,
    );

    expect(screen.getByText("Grand Champion")).toBeInTheDocument();
    expect(screen.getByText("Ama")).toBeInTheDocument();
    expect(screen.getByText("Club Santé Tokoin · Grand Lomé")).toBeInTheDocument();
    expect(screen.getByText("Maritime")).toBeInTheDocument();
    expect(screen.getByText(/atteint son total le premier/)).toBeInTheDocument();
  });

  it("annonce le premier palmarès quand rien n'est publié", () => {
    render(<Palmares palmares={{ semestres: [] }} />);

    expect(
      screen.getByText("Le premier palmarès sera publié à la fin du semestre."),
    ).toBeInTheDocument();
  });
});
