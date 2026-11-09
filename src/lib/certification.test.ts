import { describe, expect, it } from "vitest";

import type { BadgeParcours, PlaceParcours } from "@/lib/api/client";

import { fondBadge, FONDS_BADGES, jouable, prochainBadge, quizRestants } from "./certification";

const place = (etat: PlaceParcours["etat"], quiz_id: string | null = "q"): PlaceParcours => ({
  place: 1,
  etat,
  quiz_id,
  titre: null,
  description: null,
  contenu_de_test: false,
  fascicule: null,
  meilleur_score: null,
  tentatives_restantes: null,
  tentative_en_cours: null,
});

const badge = (rang: number, palier: number, obtenu = false): BadgeParcours => ({
  rang,
  nom: `Badge ${rang}`,
  palier,
  obtenu_le: obtenu ? "2026-11-09T10:00:00Z" : null,
});

describe("jouable", () => {
  it("ouvre une place ouverte ou réussie qui a un quiz publié", () => {
    expect(jouable(place("ouverte"))).toBe(true);
    expect(jouable(place("reussie"))).toBe(true);
  });

  it("ferme une place verrouillée, bientôt disponible, ou réussie sur un quiz retiré", () => {
    expect(jouable(place("verrouillee"))).toBe(false);
    expect(jouable(place("bientot", null))).toBe(false);
    expect(jouable(place("reussie", null))).toBe(false);
  });
});

describe("prochainBadge", () => {
  const badges = [badge(1, 3, true), badge(2, 5), badge(3, 7), badge(4, 9), badge(5, 12)];

  it("donne le premier badge non obtenu et ce qui manque", () => {
    expect(prochainBadge(badges, 4)).toEqual({ badge: badges[1], manquent: 1 });
  });

  it("ne descend jamais sous zéro (palier abaissé, en attente du rattrapage)", () => {
    expect(prochainBadge(badges, 6)?.manquent).toBe(0);
  });

  it("renvoie null quand tous les badges sont obtenus", () => {
    expect(
      prochainBadge(
        badges.map((b) => ({ ...b, obtenu_le: "x" })),
        12,
      ),
    ).toBeNull();
  });
});

describe("libellés", () => {
  it("accorde le nombre de quiz", () => {
    expect(quizRestants(1)).toBe("1 quiz");
    expect(quizRestants(3)).toBe("3 quiz");
  });

  it("donne un dégradé à chaque badge, même hors limites", () => {
    expect(fondBadge(5)).toBe(FONDS_BADGES[4]);
    expect(fondBadge(9)).toBe(FONDS_BADGES[0]);
  });
});
