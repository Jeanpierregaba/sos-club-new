import { describe, expect, it } from "vitest";

import { normaliserTelephone, telephoneValide } from "./telephone";

describe("telephone", () => {
  it.each([
    ["+228 90 12 34 56", "+22890123456"],
    ["90-12-34-56", "90123456"],
    ["(228) 90.12.34.56", "22890123456"],
  ])("normalise « %s »", (saisi, attendu) => {
    expect(normaliserTelephone(saisi)).toBe(attendu);
    expect(telephoneValide(saisi)).toBe(true);
  });

  it("accepte un champ vide, puisqu'il est facultatif", () => {
    expect(telephoneValide("  ")).toBe(true);
  });

  it.each(["1234567", "+228 90 12 34 56 78 90 12", "90 12 AB 56", "++22890123456"])(
    "refuse « %s »",
    (saisi) => {
      expect(telephoneValide(saisi)).toBe(false);
    },
  );
});
