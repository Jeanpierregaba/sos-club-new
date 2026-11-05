import { describe, expect, it } from "vitest";

import { editions, libelleSaison, ordinal, trouverEdition } from "./genie-imhotep-editions";

describe("éditions du Génie Imhotep", () => {
  it("retrouve une édition par son identifiant, rien pour une édition inconnue", () => {
    expect(trouverEdition("2025-2026")?.statut).toBe("terminee");
    expect(trouverEdition("2026-2027")?.statut).toBe("a-venir");
    expect(trouverEdition("inconnue")).toBeUndefined();
  });

  it("fait démarrer l'édition 2026-2027 le 1er mars 2027", () => {
    expect(trouverEdition("2026-2027")?.debut).toBe("2027-03-01T00:00:00Z");
  });

  it("donne une date valide à chaque édition à venir et un champion à chaque édition terminée", () => {
    for (const e of editions) {
      if (e.statut === "a-venir")
        expect(Number.isNaN(new Date(e.debut ?? "").getTime())).toBe(false);
      else expect(e.champion).toBeTruthy();
    }
  });

  it("écrit les ordinaux et les saisons en français", () => {
    expect(ordinal(1)).toBe("1re");
    expect(ordinal(2)).toBe("2e");
    expect(libelleSaison("2025-2026")).toBe("2025 – 2026");
  });
});
