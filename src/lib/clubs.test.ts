import { describe, expect, it } from "vitest";

import { clubsParEtablissement, libelleAxes, libellesDesAxes } from "./clubs";
import type { AxePublic, ClubPublic } from "./api/client";

const etablissement = {
  id: "etab-1",
  nom: "Lycée de Tokoin I",
  statut: "actif",
  iesg: "IESG Golfe",
  dre_code: "grand-lome",
  dre: "Grand Lomé",
} as const;

const club: ClubPublic = {
  id: "club-1",
  nom: "Club Santé de Tokoin",
  etablissement,
  axes: ["sante-environnement"],
  statut: "actif",
  actif_le: "2026-11-04T10:00:00Z",
};

const axes: AxePublic[] = [
  {
    code: "sante-environnement",
    libelle: "Santé et environnement",
    description: "Protéger son cadre de vie.",
  },
];

describe("clubsParEtablissement", () => {
  it("indexe les clubs actifs par leur établissement", () => {
    expect(clubsParEtablissement([club]).get(etablissement.id)).toEqual(club);
  });

  it("laisse un établissement sans club hors de l'index", () => {
    expect(clubsParEtablissement([club]).get("etab-2")).toBeUndefined();
    expect(clubsParEtablissement([]).size).toBe(0);
  });
});

describe("libelleAxes", () => {
  it("rend les libellés du référentiel, séparés par un point médian", () => {
    expect(libelleAxes(["sante-environnement"], libellesDesAxes(axes))).toBe(
      "Santé et environnement",
    );
  });

  it("garde le code quand l'axe n'est plus au référentiel", () => {
    expect(libelleAxes(["axe-retire"], libellesDesAxes(axes))).toBe("axe-retire");
  });
});
