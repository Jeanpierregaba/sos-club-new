// Les textes de l'interface (spec 052) : chaque clé existe dans les trois langues, sans valeur vide, avec les mêmes
// paramètres. Une traduction oubliée ou un paramètre mal recopié se voit ici, pas sur le site.
import { readFileSync } from "node:fs";
import path from "node:path";

import { describe, expect, it } from "vitest";

const LANGUES = ["fr", "en", "de"] as const;

function lire(langue: string): Record<string, string> {
  const fichier = path.resolve(__dirname, "../../messages", `${langue}.json`);
  const { $schema: _schema, ...messages } = JSON.parse(readFileSync(fichier, "utf8")) as Record<
    string,
    string
  >;
  return messages;
}

const parametres = (texte: string) =>
  [...texte.matchAll(/\{(\w+)\}/g)].map(([, nom]) => nom).sort();

describe("textes de l'interface", () => {
  const messages = { fr: lire("fr"), en: lire("en"), de: lire("de") };
  const cles = Object.keys(messages.fr).sort();

  it("il y a des textes", () => {
    expect(cles.length).toBeGreaterThan(0);
  });

  it.each(["en", "de"] as const)("%s a exactement les clés du français", (langue) => {
    expect(Object.keys(messages[langue]).sort()).toEqual(cles);
  });

  it.each(LANGUES)("aucun texte vide en %s", (langue) => {
    const vides = Object.entries(messages[langue]).filter(
      ([, texte]) => typeof texte !== "string" || !texte.trim(),
    );
    expect(vides).toEqual([]);
  });

  it.each(["en", "de"] as const)("%s garde les paramètres du français", (langue) => {
    const ecarts = cles.filter(
      (cle) =>
        JSON.stringify(parametres(messages.fr[cle] ?? "")) !==
        JSON.stringify(parametres(messages[langue][cle] ?? "")),
    );
    expect(ecarts).toEqual([]);
  });

  it("les clés sont en minuscules, sans accent, préfixées par leur page", () => {
    expect(cles.filter((cle) => !/^[a-z0-9]+(_[a-z0-9]+)+$/.test(cle))).toEqual([]);
  });
});
