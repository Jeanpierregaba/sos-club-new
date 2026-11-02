import { describe, expect, it } from "vitest";

import { cheminSur, PAGE_APRES_CONNEXION } from "./redirection";

describe("cheminSur", () => {
  it.each(["/mon-espace", "/agenda?region=kara#mai", "/clubs/12"])("garde la page %s", (chemin) => {
    expect(cheminSur(chemin)).toBe(chemin);
  });

  it.each([
    undefined,
    null,
    42,
    "",
    "mon-espace",
    "https://autre-site.tg",
    "//autre-site.tg",
    "/\\autre-site.tg",
    "/\t/autre-site.tg",
    "/.//autre-site.tg",
    "javascript:alert(1)",
    "/connexion",
    "/connexion?redirection=/connexion",
  ])("refuse %j", (valeur) => {
    expect(cheminSur(valeur)).toBe(PAGE_APRES_CONNEXION);
  });
});
