import { describe, expect, it } from "vitest";

import type { DreAnnuaire } from "@/lib/api/client";
import { chercher, compterParType, indexer, normaliser } from "./carte-des-clubs";

const annuaire: DreAnnuaire[] = [
  {
    code: "grand-lome",
    nom: "Grand Lomé",
    nom_complet: "Direction Régionale de l’Éducation du Grand Lomé",
    nb_etablissements: 3,
    iesg: [
      {
        id: "golfe",
        nom: "IESG Golfe",
        zone: "Golfe (Lomé)",
        nb_etablissements: 2,
        etablissements: [
          { id: "1", nom: "Lycée de Tokoin I", type: "lycee" },
          { id: "2", nom: "Collège Saint Joseph", type: "college" },
        ],
      },
      {
        id: "agoe",
        nom: "IESG Agoényivé",
        zone: "Agoényivé",
        nb_etablissements: 1,
        etablissements: [{ id: "3", nom: "Lycée Agoè Centre", type: "lycee" }],
      },
    ],
  },
];

describe("carte des clubs", () => {
  it("normalise accents, majuscules et apostrophes", () => {
    expect(normaliser("Lycée d’Agoè")).toBe("lycee d'agoe");
  });

  it("indexe chaque établissement avec son IESG et sa DRE", () => {
    const index = indexer(annuaire);
    expect(index).toHaveLength(3);
    expect(index[2]).toMatchObject({ nom: "Lycée Agoè Centre", iesg: { id: "agoe" } });
    expect(index[2]?.dre.code).toBe("grand-lome");
  });

  it("cherche mot à mot, sans accents ni majuscules", () => {
    const index = indexer(annuaire);
    expect(chercher(index, "LYCEE agoe").map((e) => e.id)).toEqual(["3"]);
    expect(chercher(index, "tokoin lycée").map((e) => e.id)).toEqual(["1"]);
    expect(chercher(index, "l")).toEqual([]);
    expect(chercher(index, "   ")).toEqual([]);
  });

  it("compte les types présents, dans l'ordre demandé", () => {
    const liste = indexer(annuaire);
    expect(compterParType(liste, ["lycee", "college", "complexe", "autre"])).toEqual([
      { t: "lycee", n: 2 },
      { t: "college", n: 1 },
    ]);
  });
});
