import { describe, expect, it } from "vitest";

import { dureeLisible } from "@/lib/admin";

describe("dureeLisible", () => {
  it("écrit les secondes au dixième sous une minute", () => {
    expect(dureeLisible(45)).toBe("45 s");
    expect(dureeLisible(4.2)).toBe("4,2 s");
    expect(dureeLisible(0)).toBe("0 s");
  });

  it("passe aux minutes, aux heures puis aux jours", () => {
    expect(dureeLisible(65)).toBe("1 min 05 s");
    expect(dureeLisible(2 * 3600 + 10 * 60)).toBe("2 h 10 min");
    expect(dureeLisible(3600)).toBe("1 h");
    expect(dureeLisible(3 * 86400 + 4 * 3600 + 59)).toBe("3 j 4 h");
    expect(dureeLisible(86400)).toBe("1 j");
  });

  it("montre un tiret sans durée", () => {
    expect(dureeLisible(null)).toBe("—");
    expect(dureeLisible(undefined)).toBe("—");
  });
});
