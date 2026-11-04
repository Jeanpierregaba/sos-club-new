import { describe, expect, it } from "vitest";

import { erreurPseudonyme } from "./pseudonyme";

describe("erreurPseudonyme", () => {
  it.each(["Aya", "  Kofi   le   Grand ", "Éléonore.T", "Ama-2010"])("accepte « %s »", (saisie) => {
    expect(erreurPseudonyme(saisie)).toBeNull();
  });

  it.each([
    ["Ay", "caractères"],
    ["A".repeat(31), "caractères"],
    ["aya@mail.tg", "lettres"],
    ["Aya_K", "lettres"],
    ["123456", "au moins une lettre"],
    ["Kofi 90 12 34 56", "téléphone"],
    ["Аya Kossi", "lettres"],
  ])("refuse « %s »", (saisie, motif) => {
    expect(erreurPseudonyme(saisie)).toContain(motif);
  });
});
