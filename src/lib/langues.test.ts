import { describe, expect, it } from "vitest";

import {
  estTraduite,
  langueDeLAdresse,
  liensHreflang,
  localiser,
  pageSansLangue,
  redirectionLangue,
} from "./langues";

describe("adresses des langues (spec 052)", () => {
  it("lit la langue dans le préfixe, le français sans préfixe", () => {
    expect(langueDeLAdresse("/")).toBe("fr");
    expect(langueDeLAdresse("/jeux")).toBe("fr");
    expect(langueDeLAdresse("/en")).toBe("en");
    expect(langueDeLAdresse("/en/jeux")).toBe("en");
    expect(langueDeLAdresse("/de/articles/mon-article")).toBe("de");
    // Une page non traduite ou inconnue sous un préfixe : sa 404 suit le préfixe.
    expect(langueDeLAdresse("/de/page-inconnue")).toBe("de");
    expect(langueDeLAdresse("/es/jeux")).toBe("fr");
    expect(langueDeLAdresse("/english")).toBe("fr");
  });

  it("retire le préfixe pour retrouver la page", () => {
    expect(pageSansLangue("/en")).toBe("/");
    expect(pageSansLangue("/en/jeux")).toBe("/jeux");
    expect(pageSansLangue("/de/genie-imhotep/palmares/2025")).toBe("/genie-imhotep/palmares/2025");
    expect(pageSansLangue("/jeux")).toBe("/jeux");
  });

  it("connaît les pages traduites, paramètres compris", () => {
    for (const page of [
      "/",
      "/jeux",
      "/articles",
      "/articles/mon-article",
      "/clubs/abc",
      "/mot-de-passe/nouveau",
    ]) {
      expect(estTraduite(page), page).toBe(true);
    }
    for (const page of [
      "/mon-espace",
      "/admin/activite",
      "/quiz/123",
      "/certification/parcours/3",
      "/maintenance",
    ]) {
      expect(estTraduite(page), page).toBe(false);
    }
  });

  it("localise les liens : pages publiques préfixées, espaces connectés en français", () => {
    expect(localiser("/jeux", "en")).toBe("/en/jeux");
    expect(localiser("/", "de")).toBe("/de");
    expect(localiser("/articles/mon-article?page=2", "de")).toBe("/de/articles/mon-article?page=2");
    expect(localiser("/jeux", "fr")).toBe("/jeux");
    expect(localiser("/mon-espace", "en")).toBe("/mon-espace");
    expect(localiser("/admin/activite", "de")).toBe("/admin/activite");
  });

  it("redirige /fr vers l'adresse sans préfixe et une page non traduite vers le français", () => {
    expect(redirectionLangue("/fr")).toBe("/");
    expect(redirectionLangue("/fr/jeux")).toBe("/jeux");
    expect(redirectionLangue("/en/mon-espace")).toBe("/mon-espace");
    expect(redirectionLangue("/de/admin/activite")).toBe("/admin/activite");
    // Rien à faire sur une page traduite, une page française ou un préfixe inconnu.
    expect(redirectionLangue("/en/jeux")).toBeNull();
    expect(redirectionLangue("/jeux")).toBeNull();
    expect(redirectionLangue("/es/jeux")).toBeNull();
  });

  it("déclare les trois versions d'une page traduite, et aucune pour une page française seulement", () => {
    expect(liensHreflang("/articles/mon-article", "?page=2")).toEqual([
      { hreflang: "fr", href: "/articles/mon-article?page=2" },
      { hreflang: "en", href: "/en/articles/mon-article?page=2" },
      { hreflang: "de", href: "/de/articles/mon-article?page=2" },
      { hreflang: "x-default", href: "/articles/mon-article?page=2" },
    ]);
    expect(liensHreflang("/", "")).toContainEqual({ hreflang: "en", href: "/en" });
    expect(liensHreflang("/mon-espace", "")).toEqual([]);
  });
});
