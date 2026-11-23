import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ecart, formater } from "@/lib/activite-admin";
import type { BlocActivite as Bloc } from "@/lib/api/client";

import { BlocActivite } from "./BlocActivite";

function bloc(contenu: Partial<Bloc> = {}): Bloc {
  return {
    bloc: "audience",
    du: "2026-11-01",
    au: "2026-11-03",
    precedent_du: "2026-10-29",
    precedent_au: "2026-10-31",
    chiffres: [],
    series: [],
    tableaux: [],
    grilles: [],
    notes: [],
    ...contenu,
  };
}

describe("mise en forme", () => {
  it("écrit les nombres, pourcentages et durées en français", () => {
    expect(formater(1234)).toBe("1 234");
    expect(formater(12.5, "pourcent")).toBe("12,5 %");
    expect(formater(95, "secondes")).toBe("1 min 35 s");
    expect(formater(null)).toBe("—");
  });

  it("compare à la période précédente, en points pour un pourcentage", () => {
    expect(ecart({ cle: "v", libelle: "", valeur: 150, precedent: 100, unite: "nombre" })).toEqual({
      texte: "+50 %",
      sens: "hausse",
    });
    expect(ecart({ cle: "v", libelle: "", valeur: 40, precedent: 50, unite: "pourcent" })).toEqual({
      texte: "-10 pts",
      sens: "baisse",
    });
    expect(ecart({ cle: "v", libelle: "", valeur: 3, precedent: 0, unite: "nombre" })?.texte).toBe(
      "nouveau",
    );
    expect(
      ecart({ cle: "v", libelle: "", valeur: 3, precedent: null, unite: "nombre" }),
    ).toBeNull();
  });
});

describe("BlocActivite", () => {
  it("dit qu'il n'y a pas encore de données sur une période vide", () => {
    render(
      <BlocActivite titre="Audience" bloc={bloc({ notes: ["Une note"] })} urlExport="/x.csv" />,
    );
    expect(screen.getByText("Pas encore de données sur cette période.")).toBeInTheDocument();
    expect(screen.getByText("Une note")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /CSV/ })).toHaveAttribute("href", "/x.csv");
  });

  it("affiche chiffres, courbe, tableau et heatmap", () => {
    render(
      <BlocActivite
        titre="Audience"
        urlExport="/x.csv"
        bloc={bloc({
          chiffres: [
            { cle: "visiteurs", libelle: "Visiteurs", valeur: 30, precedent: 20, unite: "nombre" },
          ],
          series: [
            {
              cle: "visiteurs",
              libelle: "Visiteurs par jour",
              points: [
                { jour: "2026-11-01", valeur: 10 },
                { jour: "2026-11-02", valeur: 20 },
              ],
            },
          ],
          tableaux: [
            {
              cle: "pages",
              titre: "Pages les plus vues",
              colonnes: [
                { cle: "chemin", libelle: "Page", unite: "texte" },
                { cle: "vues", libelle: "Vues", unite: "nombre" },
              ],
              lignes: [{ chemin: "/jeux", vues: 12 }],
            },
          ],
          grilles: [
            {
              cle: "pages",
              titre: "Pages vues par heure",
              valeurs: Array.from({ length: 7 }, () => Array.from({ length: 24 }, () => 1)),
            },
          ],
        })}
      />,
    );
    expect(screen.getByRole("heading", { name: "Audience" })).toBeInTheDocument();
    expect(screen.getByText("+50 %")).toBeInTheDocument();
    expect(screen.getByRole("img", { name: "Visiteurs par jour par jour" })).toBeInTheDocument();
    const tableau = screen.getByRole("table");
    expect(within(tableau).getByText("/jeux")).toBeInTheDocument();
    expect(within(tableau).getByText("12")).toBeInTheDocument();
    expect(screen.getByText("Pages vues par heure")).toBeInTheDocument();
  });
});
