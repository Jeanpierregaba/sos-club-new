import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

import { niveauParNumero, poles } from "./quiz";

// Le catalogue de l'API (migration de la spec 034) et celui du site doivent dire la même chose.
const defis: { numero: number; titre: string; niveau: string }[] = JSON.parse(
  readFileSync(resolve(__dirname, "../../backend/alembic/donnees/defis_jeux.json"), "utf8"),
);

describe("les 100 défis (spec 034)", () => {
  it("se répartissent en 40, 30, 20 et 10 quiz par niveau", () => {
    const parNiveau: Record<string, number> = {};
    for (const n of niveauParNumero.values()) parNiveau[n] = (parNiveau[n] ?? 0) + 1;
    expect(parNiveau).toEqual({ debutant: 40, intermediaire: 30, avance: 20, expert: 10 });
  });

  it("ont le même titre et le même niveau sur le site et dans l'API", () => {
    const titres = poles.flatMap((p) => p.quiz.map(([t]) => t));
    expect(defis).toHaveLength(100);
    for (const d of defis) {
      expect(titres[d.numero - 1]).toBe(d.titre);
      expect(niveauParNumero.get(d.numero)).toBe(d.niveau);
    }
  });
});
