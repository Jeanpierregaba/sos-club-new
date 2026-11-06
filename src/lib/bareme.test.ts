import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

import { BAREME, points } from "./bareme";

const source = (chemin: string) => readFileSync(resolve(__dirname, "..", chemin), "utf8");

describe("barème affiché (spec 022)", () => {
  it("suit le référentiel du 2026-11-05", () => {
    expect(BAREME).toEqual({
      quiz: { eleve: 50, club: 25 },
      questionDuJour: { eleve: 20, club: 10 },
      badge: { eleve: 500, club: 200 },
      certification: { eleve: 1000, club: 500 },
    });
  });

  it("écrit les milliers avec une espace fine", () => {
    expect(points(1000)).toBe("+1 000");
    expect(points(50)).toBe("+50");
  });

  it("ne garde aucune ancienne mention de points sur les pages", () => {
    for (const page of ["routes/certification.tsx", "routes/jeux.tsx", "routes/club-sante.tsx"]) {
      const texte = source(page);
      expect(texte).not.toMatch(/palier/i);
      expect(texte).not.toMatch(/\+150|\+250|pts: (150|250)/);
      expect(texte).not.toMatch(/60–65 pts|70–75 pts|80–100 pts/);
    }
  });
});
