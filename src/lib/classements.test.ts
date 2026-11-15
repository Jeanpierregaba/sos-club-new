import { describe, expect, it } from "vitest";

import {
  estCategorie,
  estPeriode,
  formaterPoints,
  formaterRang,
  nombreDePages,
  rangOuNonClasse,
  sousTitre,
} from "./classements";

describe("classements (spec 036)", () => {
  it("écrit les scores de club avec leur décimale, sans arrondi", () => {
    expect(formaterPoints(2.5)).toBe("2,5");
    expect(formaterPoints(202.5)).toBe("202,5");
    expect(formaterPoints(1200)).toBe("1 200");
    expect(formaterPoints(-40)).toBe("-40");
  });

  it("écrit les rangs à la française", () => {
    expect(formaterRang(1)).toBe("1er");
    expect(formaterRang(2)).toBe("2e");
    expect(formaterRang(10)).toBe("10e");
  });

  it("n'invente pas de rang", () => {
    expect(rangOuNonClasse(null)).toBe("Pas encore classé");
    expect(rangOuNonClasse(undefined)).toBe("Pas encore classé");
    expect(rangOuNonClasse(3)).toBe("3e");
  });

  it("compte les pages", () => {
    expect(nombreDePages(0, 50)).toBe(1);
    expect(nombreDePages(50, 50)).toBe(1);
    expect(nombreDePages(51, 50)).toBe(2);
  });

  it("reconnaît les filtres de l'adresse", () => {
    expect(estCategorie("clubs")).toBe(true);
    expect(estCategorie("club")).toBe(false);
    expect(estPeriode("historique")).toBe(true);
    expect(estPeriode("annee")).toBe(false);
  });
});

describe("sous-titre d'une ligne", () => {
  it("montre le club et la DRE d'une personne, l'établissement d'un club", () => {
    expect(
      sousTitre({ rang: 1, nom: "Ama", club: "Club Tokoin", dre: "Grand Lomé", points: 10 }),
    ).toBe("Club Tokoin · Grand Lomé");
    expect(sousTitre({ rang: 1, nom: "Yao", club: null, dre: "Kara", points: 10 })).toBe(
      "Sans club · Kara",
    );
    expect(
      sousTitre({
        rang: 1,
        club_id: "x",
        nom: "Club",
        etablissement: "Lycée de Kara",
        dre: "Kara",
        points: 2.5,
      }),
    ).toBe("Lycée de Kara · Kara");
  });
});
