import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

import { NIVEAUX_JEUX, TOTAL_QUIZ_JEUX } from "./bareme";
import { niveauParNumero, poles } from "./quiz";

// Le catalogue de l'API (migration de la spec 050) et celui du site doivent dire la même chose.
const jeux: { numero: number; titre: string; niveau: string }[] = JSON.parse(
  readFileSync(resolve(__dirname, "../../backend/alembic/donnees/jeux_100.json"), "utf8"),
);

describe("les 100 quiz Jeux de la banque officielle (spec 050)", () => {
  it("se répartissent en 40, 30, 20 et 10 quiz par niveau", () => {
    const parNiveau: Record<string, number> = {};
    for (const n of niveauParNumero.values()) parNiveau[n] = (parNiveau[n] ?? 0) + 1;
    expect(parNiveau).toEqual({ debutant: 40, intermediaire: 30, avance: 20, expert: 10 });
    expect(Object.fromEntries(NIVEAUX_JEUX.map((n) => [n.code, n.quiz]))).toEqual(parNiveau);
    expect(TOTAL_QUIZ_JEUX).toBe(100);
  });

  it("ont le même titre, le même numéro et le même niveau sur le site et dans l'API", () => {
    const site = new Map(poles.flatMap((p) => p.quiz.map((q) => [q.n, q] as const)));
    expect(jeux).toHaveLength(100);
    expect(site.size).toBe(100);
    for (const q of jeux) {
      expect(site.get(q.numero)?.t).toBe(q.titre);
      expect(site.get(q.numero)?.niveau).toBe(q.niveau);
    }
  });
});
