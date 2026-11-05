import { describe, expect, it } from "vitest";

import { editionDe, editions, ordinal } from "./genie-imhotep-editions";

describe("éditions du Génie Imhotep", () => {
  it("affiche par défaut la dernière édition terminée", () => {
    expect(editionDe(undefined).id).toBe("2025-2026");
    expect(editionDe("inconnue").id).toBe("2025-2026");
  });

  it("retrouve l'édition demandée", () => {
    expect(editionDe("2026-2027").statut).toBe("a-venir");
  });

  it("donne une date de coup d'envoi valide à chaque édition à venir", () => {
    for (const e of editions.filter((x) => x.statut === "a-venir"))
      expect(Number.isNaN(new Date(e.debut ?? "").getTime())).toBe(false);
  });

  it("écrit les ordinaux en français", () => {
    expect(ordinal(1)).toBe("1re");
    expect(ordinal(2)).toBe("2e");
  });
});
