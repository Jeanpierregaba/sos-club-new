import { act, fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { FileMembres } from "./FileMembres";
import type { AffiliationAValider, RattachementAValider } from "@/lib/api/client";

const api = vi.hoisted(() => ({
  adminDeciderAffiliations: vi.fn(),
  adminDeciderRattachements: vi.fn(),
}));
vi.mock("@/lib/api/client", async (original) => ({
  ...(await original<typeof import("@/lib/api/client")>()),
  ...api,
}));

const affiliation = (id: string, pseudonyme: string): AffiliationAValider => ({
  id,
  pseudonyme,
  classe: "2nde",
  club_id: "club-1",
  club_nom: "Club Santé Tokoin",
  etablissement: "Lycée de Tokoin I",
  dre: "Grand Lomé",
  demande_le: "2026-11-05T10:00:00Z",
  confirme_le: "2026-11-05T11:00:00Z",
  version: 2,
});

const rattachement = (decidable: boolean): RattachementAValider => ({
  id: "rat-1",
  prenom: "Afi",
  nom: "Mensah",
  fonction: "sante",
  etablissement_encadreur: "CEG Agoè",
  club_id: "club-1",
  club_nom: "Club Santé Tokoin",
  club_etablissement: "Lycée de Tokoin I",
  dre: "Grand Lomé",
  supplementaire: true,
  decidable,
  demande_le: "2026-11-05T10:00:00Z",
  confirme_le: null,
  version: 1,
});

const rafraichir = vi.fn().mockResolvedValue(undefined);

beforeEach(() => vi.clearAllMocks());

describe("FileMembres", () => {
  it("valide la sélection en lot et affiche l'échec ligne par ligne", async () => {
    api.adminDeciderAffiliations.mockResolvedValue({
      reussies: ["a-1"],
      echecs: [{ id: "a-2", message: "Cette demande a déjà été traitée : recharge la page." }],
    });
    render(
      <FileMembres
        type="affiliations"
        demandes={[affiliation("a-1", "Kofi"), affiliation("a-2", "Ama")]}
        decideur
        onRafraichir={rafraichir}
      />,
    );

    fireEvent.click(screen.getByLabelText("Tout sélectionner"));
    fireEvent.click(screen.getByRole("button", { name: /Valider la sélection \(2\)/ }));
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Valider" }));
    });

    expect(api.adminDeciderAffiliations).toHaveBeenCalledWith(
      "valider",
      [
        { id: "a-1", version: 2 },
        { id: "a-2", version: 2 },
      ],
      undefined,
    );
    expect(screen.getByRole("status")).toHaveTextContent("1 affiliation traitée");
    expect(screen.getByRole("alert")).toHaveTextContent("déjà été traitée");
    expect(rafraichir).toHaveBeenCalled();
  });

  it("ne laisse pas une DRE cocher un club supplémentaire", () => {
    render(
      <FileMembres
        type="rattachements"
        demandes={[rattachement(false)]}
        decideur
        onRafraichir={rafraichir}
      />,
    );

    expect(screen.getByLabelText("Sélectionner Afi Mensah")).toBeDisabled();
    expect(screen.getByText(/autorisation nationale requise/)).toBeInTheDocument();
  });

  it("sans le droit d'approuver, la file est en lecture seule", () => {
    render(
      <FileMembres
        type="affiliations"
        demandes={[affiliation("a-1", "Kofi")]}
        decideur={false}
        onRafraichir={rafraichir}
      />,
    );

    expect(screen.queryByRole("button", { name: /Valider la sélection/ })).not.toBeInTheDocument();
    expect(screen.getByLabelText("Sélectionner Kofi")).toBeDisabled();
  });
});
