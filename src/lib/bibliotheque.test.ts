import { describe, expect, it } from "vitest";

import { estCategorie, tailleLisible, telechargements } from "./bibliotheque";

describe("bibliothèque", () => {
  it("écrit la taille d'un fichier en Ko ou en Mo", () => {
    expect(tailleLisible(512_000)).toBe("500 Ko");
    expect(tailleLisible(200)).toBe("1 Ko");
    expect(tailleLisible(4_404_019)).toBe("4,2 Mo");
    expect(tailleLisible(20 * 1024 * 1024)).toBe("20 Mo");
  });

  it("accorde le nombre de téléchargements", () => {
    expect(telechargements(0)).toBe("0 téléchargement");
    expect(telechargements(1)).toBe("1 téléchargement");
    expect(telechargements(1234).replace(/\s/g, " ")).toBe("1 234 téléchargements");
  });

  it("reconnaît une catégorie de l'API", () => {
    expect(estCategorie("magazine")).toBe(true);
    expect(estCategorie("video")).toBe(false);
    expect(estCategorie(undefined)).toBe(false);
  });
});
