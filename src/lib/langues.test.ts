import { describe, expect, it } from "vitest";

import {
  estTraduite,
  langueDeLAdresse,
  liensHreflang,
  localiser,
  pageSansLangue,
  redirectionLangue as rediriger,
  sansBarreFinale,
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
    const existe = (page: string) => page !== "/page-inconnue";
    const redirectionLangue = (chemin: string) => rediriger(chemin, existe);
    expect(redirectionLangue("/fr")).toBe("/");
    expect(redirectionLangue("/fr/jeux")).toBe("/jeux");
    expect(redirectionLangue("/en/mon-espace")).toBe("/mon-espace");
    expect(redirectionLangue("/de/admin/activite")).toBe("/admin/activite");
    // Rien à faire sur une page traduite, une page française ou un préfixe inconnu.
    expect(redirectionLangue("/en/jeux")).toBeNull();
    expect(redirectionLangue("/jeux")).toBeNull();
    expect(redirectionLangue("/es/jeux")).toBeNull();
    // Une page inconnue sous un préfixe reste une 404, dans la langue du préfixe.
    expect(redirectionLangue("/en/page-inconnue")).toBeNull();
    // Plusieurs barres d'affilée n'ouvrent jamais un autre site.
    expect(redirectionLangue("/fr//site.com")).toBe("/site.com");
    expect(redirectionLangue("/en//site.com/x")).toBe("/site.com/x");
  });

  it("retire la barre finale d'une adresse anglaise ou allemande, que Paraglide ne reconnaîtrait pas", () => {
    expect(sansBarreFinale("/en/")).toBe("/en");
    expect(sansBarreFinale("/de/jeux/")).toBe("/de/jeux");
    expect(sansBarreFinale("/en/articles/mon-article//")).toBe("/en/articles/mon-article");
    expect(sansBarreFinale("/en//jeux/")).toBe("/en/jeux");
    expect(sansBarreFinale("/en/jeux")).toBeNull();
    expect(sansBarreFinale("/jeux/")).toBeNull();
    expect(sansBarreFinale("/english/")).toBeNull();
    expect(sansBarreFinale("/")).toBeNull();
  });

  it("déclare les trois versions d'une page traduite, et aucune pour une page française seulement", () => {
    const site = "https://club.example";
    expect(liensHreflang("/articles/mon-article", "?page=2", site)).toEqual([
      { hreflang: "fr", href: "https://club.example/articles/mon-article?page=2" },
      { hreflang: "en", href: "https://club.example/en/articles/mon-article?page=2" },
      { hreflang: "de", href: "https://club.example/de/articles/mon-article?page=2" },
      { hreflang: "x-default", href: "https://club.example/articles/mon-article?page=2" },
    ]);
    expect(liensHreflang("/", "", site)).toContainEqual({
      hreflang: "en",
      href: "https://club.example/en",
    });
    expect(liensHreflang("/mon-espace", "", site)).toEqual([]);
  });
});

describe("routeur et suivi d'activité (spec 051)", () => {
  it("ne prend pas une sous-adresse inconnue d'une page pour cette page (sa 404 garde la langue)", async () => {
    const { createMemoryHistory, createRootRoute, createRoute, createRouter } =
      await import("@tanstack/react-router");
    const { pageDuRouteur } = await import("./langues");
    const racine = createRootRoute();
    const jeux = createRoute({ getParentRoute: () => racine, path: "/jeux" });
    const espace = createRoute({ getParentRoute: () => racine, path: "/mon-espace" });
    const article = createRoute({ getParentRoute: () => racine, path: "/articles/$adresse" });
    const routeur = createRouter({
      routeTree: racine.addChildren([jeux, espace, article]),
      history: createMemoryHistory({ initialEntries: ["/"] }),
    });
    expect(pageDuRouteur(routeur, "/jeux")).toBe(true);
    expect(pageDuRouteur(routeur, "/mon-espace")).toBe(true);
    expect(pageDuRouteur(routeur, "/articles/mon-article")).toBe(true);
    expect(pageDuRouteur(routeur, "/jeux/xyz")).toBe(false);
    expect(pageDuRouteur(routeur, "/articles/a/b")).toBe(false);
    expect(pageDuRouteur(routeur, "/page-inconnue")).toBe(false);
    // Avec le vrai routeur : `/en/jeux/xyz` n'est pas renvoyé vers le français.
    expect(rediriger("/en/jeux/xyz", (page) => pageDuRouteur(routeur, page))).toBeNull();
  });

  it("une page ouverte en allemand se résout sur le gabarit français, que le suivi compte tel quel", async () => {
    const { createMemoryHistory, createRootRoute, createRoute, createRouter } =
      await import("@tanstack/react-router");
    const { pageVue } = await import("./activite");
    const { REECRITURE_LANGUES } = await import("./langues");
    const racine = createRootRoute();
    const jeux = createRoute({ getParentRoute: () => racine, path: "/jeux" });
    const routeur = createRouter({
      routeTree: racine.addChildren([jeux]),
      history: createMemoryHistory({ initialEntries: ["/de/jeux"] }),
      rewrite: REECRITURE_LANGUES,
    });
    await routeur.load();
    const page = routeur.state.matches.at(-1);
    expect(page?.routeId).toBe("/jeux");
    expect(routeur.state.location.pathname).toBe("/jeux");
    expect(pageVue({ fullPath: jeux.fullPath, params: {} }, null)?.chemin).toBe("/jeux");
  });
});
