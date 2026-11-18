import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { FusionEtablissements } from "@/components/admin/FusionEtablissements";
import type { ApercuFusion, FicheDoublon } from "@/lib/api/client";
import { prefereGarder } from "@/lib/fusion";

const api = vi.hoisted(() => ({
  adminApercuFusion: vi.fn(),
  adminFusionnerEtablissements: vi.fn(),
}));
vi.mock("@/lib/api/client", async (original) => ({
  ...(await original<typeof import("@/lib/api/client")>()),
  ...api,
}));

beforeEach(() => vi.clearAllMocks());

const fiche = (id: string, nom: string, autres: Partial<FicheDoublon> = {}): FicheDoublon => ({
  id,
  nom,
  type: "lycee",
  localite: null,
  statut: "actif",
  version: 3,
  iesg_id: "i1",
  iesg: "IESG Golfe",
  dre_code: "grand-lome",
  dre: "Grand Lomé",
  modifie_le: "2026-11-18T10:00:00Z",
  prefecture: null,
  ordre: null,
  import_source: null,
  nb_eleves: 0,
  nb_encadreurs: 0,
  fusionne_dans: null,
  club: null,
  ...autres,
});

const ANNUAIRE = fiche("0001", "Lycée de Tokoin I", { nb_eleves: 12 });
const IMPORT = fiche("0002", "Lycée Tokoin I", {
  prefecture: "Golfe",
  import_source: "secondaire-1-2026",
  nb_eleves: 2,
  version: 1,
});

function apercu(garde: FicheDoublon, absorbe: FicheDoublon, refus: string | null = null) {
  return {
    garde,
    absorbe,
    effet: `${absorbe.nb_eleves} élèves et 0 encadreur rejoindront « ${garde.nom} ».`,
    refus,
  } satisfies ApercuFusion;
}

function repondre(refus: string | null = null) {
  api.adminApercuFusion.mockImplementation(async (g: string) =>
    g === ANNUAIRE.id ? apercu(ANNUAIRE, IMPORT, refus) : apercu(IMPORT, ANNUAIRE, refus),
  );
}

async function ouvrir(apresFusion = vi.fn().mockResolvedValue(undefined)) {
  await act(async () => {
    render(
      <FusionEtablissements
        depart={{ id: IMPORT.id, nom: IMPORT.nom }}
        autre={{ id: ANNUAIRE.id }}
        fermer={() => {}}
        apresFusion={apresFusion}
      />,
    );
  });
  await screen.findByRole("status");
  return apresFusion;
}

describe("prefereGarder", () => {
  it("garde l'établissement actif, puis le vrai club, puis le plus d'inscrits, puis le plus ancien", () => {
    expect(prefereGarder(fiche("b", "B"), fiche("a", "A", { statut: "propose" }))).toBe(true);
    const club = { id: "c", nom: "Club", etat: "actif", membres_actifs: 21 };
    expect(prefereGarder(fiche("a", "A", { nb_eleves: 40 }), fiche("b", "B", { club }))).toBe(
      false,
    );
    expect(prefereGarder(ANNUAIRE, IMPORT)).toBe(true);
    expect(prefereGarder(fiche("b", "B"), fiche("a", "A"))).toBe(false);
  });
});

describe("FusionEtablissements", () => {
  it("garde par défaut l'établissement qui a le plus d'inscrits et annonce l'effet", async () => {
    repondre();
    await ouvrir();

    expect(api.adminApercuFusion).toHaveBeenLastCalledWith(ANNUAIRE.id, IMPORT.id);
    expect(screen.getByRole("status").textContent).toContain("2 élèves et 0 encadreur");
    expect(screen.getByRole("status").textContent).toContain("s'appellera « Lycée de Tokoin I »");
  });

  it("inverse les rôles et reprend le nom choisi à la confirmation", async () => {
    repondre();
    const apresFusion = await ouvrir();

    await act(async () => fireEvent.click(screen.getByRole("button", { name: /Inverser/ })));
    await waitFor(() =>
      expect(api.adminApercuFusion).toHaveBeenLastCalledWith(IMPORT.id, ANNUAIRE.id),
    );
    await act(async () =>
      fireEvent.click(screen.getByRole("radio", { name: "Lycée de Tokoin I" })),
    );
    await act(async () => fireEvent.click(screen.getByRole("button", { name: "Fusionner" })));

    expect(api.adminFusionnerEtablissements).toHaveBeenCalledWith(IMPORT.id, {
      absorbe_id: ANNUAIRE.id,
      version_garde: 1,
      version_absorbe: 3,
      nom: "absorbe",
    });
    expect(apresFusion).toHaveBeenCalledOnce();
  });

  it("montre le refus avant la confirmation", async () => {
    repondre("Les deux établissements ont chacun un vrai club.");
    await act(async () => {
      render(
        <FusionEtablissements
          depart={{ id: IMPORT.id, nom: IMPORT.nom }}
          autre={{ id: ANNUAIRE.id }}
          fermer={() => {}}
          apresFusion={vi.fn()}
        />,
      );
    });

    expect((await screen.findByRole("alert")).textContent).toContain("chacun un vrai club");
    expect(screen.queryByRole("status")).toBeNull();
    expect((screen.getByRole("button", { name: "Fusionner" }) as HTMLButtonElement).disabled).toBe(
      true,
    );
    expect(screen.getByRole("button", { name: /Inverser/ })).toBeTruthy();
  });

  it("depuis une proposition, garde l'établissement actif malgré le refus du premier aperçu", async () => {
    const proposition = fiche("0003", "Lycee Tokoin 1", { statut: "propose", nb_eleves: 1 });
    api.adminApercuFusion.mockImplementation(async (g: string) =>
      g === proposition.id
        ? apercu(
            proposition,
            ANNUAIRE,
            "L'établissement gardé doit être actif : inverse les rôles ou réactive-le.",
          )
        : apercu(ANNUAIRE, proposition),
    );
    await act(async () => {
      render(
        <FusionEtablissements
          depart={{ id: proposition.id, nom: proposition.nom }}
          autre={{ id: ANNUAIRE.id }}
          fermer={() => {}}
          apresFusion={vi.fn()}
        />,
      );
    });

    await screen.findByRole("status");
    expect(api.adminApercuFusion).toHaveBeenLastCalledWith(ANNUAIRE.id, proposition.id);
    expect((screen.getByRole("button", { name: "Fusionner" }) as HTMLButtonElement).disabled).toBe(
      false,
    );
  });
});
