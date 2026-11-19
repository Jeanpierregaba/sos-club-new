import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { SuiviCertification } from "@/components/admin/SuiviCertification";
import type { StatistiquesCertification } from "@/lib/api/client";

const NOMS = ["Ambassadeur", "Pair Éducateur", "Sentinelle", "Champion", "Maître"];

function stats(autres: Partial<StatistiquesCertification> = {}): StatistiquesCertification {
  return {
    totaux: {
      candidats: 0,
      actifs_30_jours: 0,
      certifies: 0,
      badges: NOMS.map((nom, i) => ({ rang: i + 1, nom, nombre: 0 })),
    },
    entonnoir: Array.from({ length: 20 }, (_, i) => ({
      place: i + 1,
      quiz_publie: true,
      tentes: 0,
      reussis: 0,
      taux_reussite: null,
      tentatives_avant_reussite: null,
    })),
    par_dre: [],
    par_semaine: Array.from({ length: 12 }, (_, i) => ({
      debut: `2026-09-${String(i + 1).padStart(2, "0")}`,
      candidats: 0,
      certifies: 0,
    })),
    ...autres,
  };
}

describe("SuiviCertification", () => {
  it("montre les totaux, les badges, l'entonnoir et les DRE", () => {
    const base = stats();
    render(
      <SuiviCertification
        stats={stats({
          totaux: {
            candidats: 1240,
            actifs_30_jours: 300,
            certifies: 12,
            badges: NOMS.map((nom, i) => ({ rang: i + 1, nom, nombre: 5 - i })),
          },
          entonnoir: base.entonnoir.map((e) =>
            e.place === 1
              ? {
                  ...e,
                  tentes: 40,
                  reussis: 10,
                  taux_reussite: 0.25,
                  tentatives_avant_reussite: 3.5,
                }
              : e.place === 20
                ? { ...e, quiz_publie: false }
                : e,
          ),
          par_dre: [{ code: "kara", dre: "Kara", candidats: 7, badges: 3, certifies: 1 }],
        })}
      />,
    );

    const tuile = (libelle: string) =>
      screen.getAllByText(libelle)[0]!.nextSibling?.textContent?.replace(/\s/g, " ");
    expect(tuile("Candidats")).toBe("1 240");
    expect(tuile("Badges délivrés")).toBe("15");
    expect(screen.getByText("Ambassadeur : 5")).toBeTruthy();
    const places = within(screen.getByRole("list", { name: "Candidats par place" })).getAllByRole(
      "listitem",
    );
    expect(places).toHaveLength(20);
    expect(places[0]!.textContent).toContain("40 tentés · 10 réussis · 25 %");
    expect(places[0]!.textContent).toContain("3,5 essais");
    expect(places[19]!.textContent).toContain("Pas de quiz publié");
    expect(screen.getByRole("cell", { name: "Kara" })).toBeTruthy();
  });

  it("dit qu'il n'y a encore aucun candidat", () => {
    render(<SuiviCertification stats={stats()} />);

    expect(screen.getByText("Aucun candidat.")).toBeTruthy();
    expect(
      within(screen.getByRole("list", { name: /par semaine/ })).getAllByRole("listitem"),
    ).toHaveLength(12);
  });
});
