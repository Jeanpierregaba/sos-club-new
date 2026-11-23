import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

import { NIVEAUX_JEUX, TOTAL_QUIZ_JEUX } from "./bareme";
import { niveauParNumero, poles } from "./quiz";

// Le catalogue de l'API (migration de la spec 049) et celui du site doivent dire la même chose.
const banque: { jeux: { numero: number; titre: string; niveau: string }[] } = JSON.parse(
  readFileSync(resolve(__dirname, "../../backend/alembic/donnees/banque_officielle.json"), "utf8"),
);

describe("les 80 quiz Jeux de la banque officielle (spec 049)", () => {
  it("se répartissent en 32, 24, 16 et 8 quiz par niveau", () => {
    const parNiveau: Record<string, number> = {};
    for (const n of niveauParNumero.values()) parNiveau[n] = (parNiveau[n] ?? 0) + 1;
    expect(parNiveau).toEqual({ debutant: 32, intermediaire: 24, avance: 16, expert: 8 });
    expect(Object.fromEntries(NIVEAUX_JEUX.map((n) => [n.code, n.quiz]))).toEqual(parNiveau);
    expect(TOTAL_QUIZ_JEUX).toBe(80);
  });

  it("ont le même titre, le même numéro et le même niveau sur le site et dans l'API", () => {
    const site = new Map(poles.flatMap((p) => p.quiz.map((q) => [q.n, q] as const)));
    expect(banque.jeux).toHaveLength(80);
    expect(site.size).toBe(80);
    for (const q of banque.jeux) {
      expect(site.get(q.numero)?.t).toBe(q.titre);
      expect(site.get(q.numero)?.niveau).toBe(q.niveau);
    }
  });
});
