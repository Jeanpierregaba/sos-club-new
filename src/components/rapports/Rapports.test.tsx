import {
  createMemoryHistory,
  createRootRoute,
  createRouter,
  RouterProvider,
} from "@tanstack/react-router";
import { act, fireEvent, render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AFaireRapports } from "./AFaireRapports";
import { ChampsRapport } from "./ChampsRapport";
import { FormulaireRapport } from "./FormulaireRapport";
import { ListeRapports } from "./ListeRapports";
import type { RapportDetail, RapportResume } from "@/lib/api/client";

const api = vi.hoisted(() => ({
  modifierRapport: vi.fn(),
  soumettreRapport: vi.fn(),
  envoyerPieceRapport: vi.fn(),
}));
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

const resume = (options: Partial<RapportResume> = {}): RapportResume => ({
  id: "r-1",
  modele: "activite",
  reference: "RA-2026-000001",
  etat: "soumis",
  titre: "Causerie sur le paludisme",
  periode: "12/03/2026",
  club: { id: "c-1", nom: "Club Santé Tokoin" },
  auteur: "Kossi Agbeko",
  mien: true,
  soumis_le: "2026-03-13T08:00:00Z",
  modifie_le: "2026-03-13T08:00:00Z",
  points: null,
  doublon_de: null,
  doublons: [],
  lectures: [],
  ...options,
});

const detail = (options: Partial<RapportDetail> = {}): RapportDetail => ({
  ...resume({ etat: "brouillon", reference: null }),
  version: 1,
  donnees: {},
  photos: [],
  documents: [],
  historique: [],
  modifiable: true,
  doublons_probables: [],
  ...options,
});

beforeEach(() => vi.clearAllMocks());

describe("ListeRapports (spec 038)", () => {
  it("montre l'état, la référence et qui a reçu ou consulté le rapport", async () => {
    await afficher(
      <ListeRapports
        vide="Rien"
        rapports={[
          resume({
            points: 100,
            etat: "approuve",
            lectures: [
              { nom: "Afi Sena", consulte_le: "2026-03-14T08:00:00Z" },
              { nom: "Yao Mensah", consulte_le: null },
            ],
          }),
        ]}
      />,
    );
    expect(screen.getByText(/RA-2026-000001/)).toBeInTheDocument();
    expect(screen.getByText("Approuvé")).toBeInTheDocument();
    expect(screen.getByText("+100 points")).toBeInTheDocument();
    expect(screen.getByText(/Afi Sena : consulté le/)).toBeInTheDocument();
    expect(screen.getByText("Yao Mensah : reçu")).toBeInTheDocument();
  });

  it("affiche l'état vide", async () => {
    await afficher(<ListeRapports vide="Tu n'as encore déposé aucun rapport." rapports={[]} />);
    expect(screen.getByText("Tu n'as encore déposé aucun rapport.")).toBeInTheDocument();
  });
});

describe("AFaireRapports (spec 038)", () => {
  it("liste les brouillons et les corrections, rien d'autre", async () => {
    await afficher(
      <AFaireRapports
        rapports={[
          resume({ id: "a", etat: "brouillon", titre: "Brouillon" }),
          resume({ id: "b", etat: "a_corriger", titre: "À reprendre" }),
          resume({ id: "c", etat: "approuve", titre: "Fini" }),
        ]}
      />,
    );
    expect(screen.getByText(/Finir : Rapport d'activité « Brouillon »/)).toBeInTheDocument();
    expect(screen.getByText(/Corriger : Rapport d'activité « À reprendre »/)).toBeInTheDocument();
    expect(screen.queryByText(/« Fini »/)).toBeNull();
  });
});

describe("ChampsRapport (spec 038)", () => {
  it("affiche les textes en texte simple, la participation et les vidéos", () => {
    render(
      <ChampsRapport
        modele="activite"
        donnees={{
          objectifs: "<b>Prévenir</b> le paludisme",
          participants: { total: 40, filles: 22 },
          videos: ["dQw4w9WgXcQ"],
        }}
      />,
    );
    expect(screen.getByText("<b>Prévenir</b> le paludisme")).toBeInTheDocument();
    expect(screen.getByText("Participants (total) : 40")).toBeInTheDocument();
    expect(screen.getByText("dont filles : 22")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Vidéo YouTube/ })).toHaveAttribute(
      "href",
      "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    );
  });
});

describe("FormulaireRapport (spec 038)", () => {
  const props = {
    axes: [{ code: "sante-environnement", libelle: "Santé et environnement", description: "" }],
    types: [{ code: "causerie", libelle: "Causerie éducative" }],
    semestres: [],
  };

  it("demande les champs du rapport d'activité et rappelle de ne nommer aucun élève", async () => {
    await afficher(<FormulaireRapport rapport={detail()} {...props} />);
    expect(screen.getByLabelText("Date de l'activité *")).toBeInTheDocument();
    expect(screen.getByLabelText("Type d'activité *")).toBeInTheDocument();
    expect(screen.getByLabelText("Participants (total) *")).toBeInTheDocument();
    expect(screen.getByText(/N'écris aucun nom d'élève/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Supprimer le brouillon/ })).toBeInTheDocument();
  });

  it("propose le mois pour un mensuel, sans participants", async () => {
    await afficher(<FormulaireRapport rapport={detail({ modele: "mensuel" })} {...props} />);
    expect(screen.getByLabelText("Mois *")).toBeInTheDocument();
    expect(screen.queryByLabelText("Participants (total) *")).toBeNull();
  });

  it("n'envoie de photo qu'après l'attestation", async () => {
    await afficher(<FormulaireRapport rapport={detail()} {...props} />);
    const photo = screen.getByText(/Ajouter une photo/).querySelector("input")!;
    expect(photo).toBeDisabled();
    fireEvent.click(screen.getByRole("checkbox"));
    expect(photo).not.toBeDisabled();
  });

  it("enregistre puis soumet, et affiche le refus de l'API", async () => {
    const { ErreurApi } = await import("@/lib/api/client");
    api.modifierRapport.mockResolvedValue(detail({ version: 2 }));
    api.soumettreRapport.mockRejectedValue(new ErreurApi(422, "Il manque le lieu."));
    await afficher(<FormulaireRapport rapport={detail()} {...props} />);

    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /Soumettre/ }));
    });

    expect(api.modifierRapport).toHaveBeenCalledWith("r-1", 1, {});
    expect(api.soumettreRapport).toHaveBeenCalledWith("r-1", 2);
    expect(screen.getByText("Il manque le lieu.")).toBeInTheDocument();
  });
});
