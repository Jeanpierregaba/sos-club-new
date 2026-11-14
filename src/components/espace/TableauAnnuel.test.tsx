import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { PointsClub, TableauAnnuel } from "./TableauAnnuel";
import type { PointsDuClub, TableauGamification } from "@/lib/api/client";

const tableau: TableauGamification = {
  annee: { libelle: "2026-2027", debut: "2026-09-01", fin: "2027-07-31" },
  total_annuel: 555,
  total_historique: 1255,
  apport_club: 277.5,
  rang_regional: 3,
  region: "maritime",
  place_club: 1,
  parcours: { certification: 50, jeux: 500, vie: 5 },
  certification: {
    quiz_valides: 1,
    badges: 0,
    certificat: false,
    points_quiz: 50,
    points_badges: 0,
    points_certificat: 0,
  },
  jeux: {
    quiz_reussis: 0,
    niveaux: [],
    niveau_courant: "debutant",
    points_quiz: 0,
    points_etoiles: 500,
    total: 500,
    gold: false,
    reussis: [],
  },
  vie: { en_attente: 2, approuvees: 1, points: 5 },
  archives: [{ libelle: "2025-2026", points: 700, region: "maritime", rang: 4 }],
  ancien_eleve: false,
};

describe("TableauAnnuel", () => {
  it("montre l'année, la part du club, le rang et les archives", () => {
    render(<TableauAnnuel tableau={tableau} />);
    expect(screen.getByText("Année 2026-2027")).toBeInTheDocument();
    expect(screen.getByText("277,5")).toBeInTheDocument();
    expect(screen.getByText("Rang · Maritime")).toBeInTheDocument();
    expect(screen.getByText("2 en attente de modération")).toBeInTheDocument();
    expect(screen.getByText("2025-2026")).toBeInTheDocument();
  });
});

describe("PointsClub", () => {
  it("sépare les points des quiz et des étoiles", () => {
    const points: PointsDuClub = {
      annee: null,
      total_annuel: 252.5,
      total_historique: 252.5,
      parcours: { certification: 0, jeux: 250, vie: 2.5 },
      jeux_quiz: 0,
      jeux_etoiles: 250,
    };
    render(<PointsClub points={points} />);
    expect(screen.getByText("Jeux · étoiles").nextSibling).toHaveTextContent("250");
    expect(screen.getAllByText("252,5")).toHaveLength(2);
  });
});
