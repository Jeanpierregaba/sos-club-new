import {
  createMemoryHistory,
  createRootRoute,
  createRouter,
  RouterProvider,
} from "@tanstack/react-router";
import { act, render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ClassementDuClub, RangsPersonnels } from "./MesClassements";
import { type ClassementClubInterne, type ClassementPersonnel } from "@/lib/api/client";

const api = vi.hoisted(() => ({ chargerClassementMonClub: vi.fn() }));
vi.mock("@/lib/api/client", async (original) => ({
  ...(await original<typeof import("@/lib/api/client")>()),
  ...api,
}));

async function afficher(contenu: ReactNode) {
  const route = createRootRoute({ component: () => <>{contenu}</> });
  const router = createRouter({
    routeTree: route,
    history: createMemoryHistory({ initialEntries: ["/"] }),
  });
  render(<RouterProvider router={router} />);
  await act(() => router.load());
  await act(async () => {});
}

const classement = (club: boolean, classe: boolean, enCours = true): ClassementPersonnel => ({
  categorie: "eleves",
  club: club ? { id: "c1", nom: "Club Santé Tokoin" } : null,
  semestre_en_cours: enCours ? { libelle: "S1", debut: "2026-11-01", fin: "2027-04-30" } : null,
  distinctions: [],
  semestre: {
    points: classe ? 120 : 0,
    rang_club: club && classe ? 2 : null,
    rang_dre: classe ? 5 : null,
    rang_national: classe ? 1 : null,
    classe,
  },
  historique: {
    points: 300,
    rang_club: club ? 1 : null,
    rang_dre: 3,
    rang_national: 10,
    classe: true,
  },
});

describe("RangsPersonnels (spec 036)", () => {
  it("montre les rangs du club, de la DRE et du pays", async () => {
    await afficher(<RangsPersonnels classement={classement(true, true)} />);

    expect(screen.getByText("Semestre en cours · S1")).toBeInTheDocument();
    expect(screen.getAllByText("1er")).toHaveLength(2);
    expect(screen.getByText("2e")).toBeInTheDocument();
    expect(screen.getByText("10e")).toBeInTheDocument();
  });

  it("dit « Pas encore classé » plutôt que d'inventer un rang", async () => {
    await afficher(<RangsPersonnels classement={classement(true, false)} />);

    expect(screen.getByText("Pas encore classé")).toBeInTheDocument();
  });

  it("dit « Aucun semestre en cours » entre deux semestres", async () => {
    await afficher(<RangsPersonnels classement={classement(true, false, false)} />);

    expect(screen.getByText("Aucun semestre en cours")).toBeInTheDocument();
    expect(screen.queryByText("Pas encore classé")).not.toBeInTheDocument();
  });

  it("affiche les distinctions du lauréat", async () => {
    await afficher(
      <RangsPersonnels
        classement={{
          ...classement(true, true),
          distinctions: [
            { semestre: "S1 2026", place: 1, distinction: "Grand Champion", points: 300 },
          ],
        }}
      />,
    );

    expect(screen.getByText("Mes distinctions")).toBeInTheDocument();
    expect(screen.getByText(/Grand Champion du semestre S1 2026/)).toBeInTheDocument();
  });

  it("n'a pas de bloc de distinctions sans distinction", async () => {
    await afficher(<RangsPersonnels classement={classement(true, true)} />);

    expect(screen.queryByText("Mes distinctions")).not.toBeInTheDocument();
  });

  it("n'a pas de rang de club sans club", async () => {
    await afficher(<RangsPersonnels classement={classement(false, true)} />);

    expect(screen.getAllByText("Sans club")).toHaveLength(2);
  });
});

describe("ClassementDuClub (spec 036)", () => {
  beforeEach(() => api.chargerClassementMonClub.mockReset());

  it("met en évidence la ligne de l'utilisateur", async () => {
    const reponse: ClassementClubInterne = {
      club: { id: "c1", nom: "Club Santé Tokoin" },
      categorie: "eleves",
      periode: "semestre",
      semestre: { libelle: "S1", debut: "2026-11-01", fin: "2027-04-30" },
      page: 1,
      par_page: 50,
      total: 2,
      lignes: [
        { rang: 1, nom: "Ama", points: 300, est_moi: false },
        { rang: 2, nom: "Kofi", points: 100, est_moi: true },
      ],
    };
    api.chargerClassementMonClub.mockResolvedValue(reponse);

    await afficher(<ClassementDuClub />);

    expect(screen.getByText("Visible des seuls membres du club")).toBeInTheDocument();
    expect(screen.getByText("Toi")).toBeInTheDocument();
    expect(screen.getByText("Kofi")).toBeInTheDocument();
  });
});
