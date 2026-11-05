import { QueryClient } from "@tanstack/react-query";
import {
  createMemoryHistory,
  createRootRoute,
  createRouter,
  RouterProvider,
} from "@tanstack/react-router";
import { act, fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AdhesionClub } from "./AdhesionClub";
import { GestionClub } from "./GestionClub";
import type {
  AdhesionResume,
  ClubPublic,
  DemandeAdhesion,
  DemandeRattachement,
  MembresDuClub,
} from "@/lib/api/client";

const api = vi.hoisted(() => ({
  demanderAdhesion: vi.fn(),
  quitterClub: vi.fn(),
  confirmerAdhesion: vi.fn(),
  confirmerRattachement: vi.fn(),
}));
vi.mock("@/lib/api/client", async (original) => ({
  ...(await original<typeof import("@/lib/api/client")>()),
  ...api,
}));

const club: ClubPublic = {
  id: "club-1",
  nom: "Club Santé Tokoin",
  etablissement: {
    id: "etab-1",
    nom: "Lycée de Tokoin I",
    statut: "actif",
    iesg: "IESG Golfe",
    dre_code: "grand-lome",
    dre: "Grand Lomé",
  },
  axes: [],
  actif_le: "2026-11-04T10:00:00Z",
};

const membres: MembresDuClub = {
  membres: [
    { id: "a-1", pseudonyme: "Zoé", depuis: "2026-11-01T10:00:00Z", president: true, version: 1 },
    { id: "a-2", pseudonyme: "Ama", depuis: "2026-11-02T10:00:00Z", president: false, version: 3 },
  ],
  encadreurs: [{ id: "r-1", prenom: "Jean", nom: "Kodjo", fonction: "enseignant", version: 1 }],
};

const adhesion = (
  etat: AdhesionResume["etat"],
  extra: Partial<AdhesionResume> = {},
): AdhesionResume => ({
  id: "adh-1",
  club_id: club.id,
  club_nom: club.nom,
  etat,
  demande_le: "2026-11-05T10:00:00Z",
  version: 1,
  ...extra,
});

async function afficher(element: React.ReactElement) {
  const route = createRootRoute({ component: () => element });
  const router = createRouter({
    routeTree: route,
    history: createMemoryHistory({ initialEntries: ["/"] }),
    context: { queryClient: new QueryClient() },
  });
  render(<RouterProvider router={router} />);
  await act(() => router.load());
}

const rafraichir = vi.fn().mockResolvedValue(undefined);

beforeEach(() => {
  vi.clearAllMocks();
});

describe("AdhesionClub — l'élève et le club de son établissement", () => {
  it("propose de rejoindre le club et envoie la demande après confirmation", async () => {
    api.demanderAdhesion.mockResolvedValue(adhesion("en_attente_president"));
    await afficher(
      <AdhesionClub club={club} adhesion={null} membres={null} onRafraichir={rafraichir} />,
    );

    fireEvent.click(screen.getByRole("button", { name: /Rejoindre ce club/ }));
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Envoyer ma demande" }));
    });

    expect(api.demanderAdhesion).toHaveBeenCalledWith("club-1");
    expect(rafraichir).toHaveBeenCalled();
  });

  it("montre une demande en attente du président, et permet de l'annuler", async () => {
    await afficher(
      <AdhesionClub
        club={club}
        adhesion={adhesion("en_attente_president")}
        membres={null}
        onRafraichir={rafraichir}
      />,
    );

    expect(screen.getByText(/attend la confirmation du président/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Annuler ma demande" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Rejoindre ce club/ })).not.toBeInTheDocument();
  });

  it("montre le motif d'un refus et propose de redemander", async () => {
    await afficher(
      <AdhesionClub
        club={club}
        adhesion={adhesion("refusee", { motif_refus: "Tu n'es pas de ce lycée." })}
        membres={null}
        onRafraichir={rafraichir}
      />,
    );

    expect(screen.getByText(/Tu n'es pas de ce lycée\./)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Rejoindre ce club/ })).toBeInTheDocument();
  });

  it("montre aux membres la liste par pseudonyme, sans bouton pour retirer", async () => {
    await afficher(
      <AdhesionClub
        club={club}
        adhesion={adhesion("active")}
        membres={membres}
        onRafraichir={rafraichir}
      />,
    );

    expect(screen.getByText("Ama")).toBeInTheDocument();
    expect(screen.getByText("Jean Kodjo")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Retirer/ })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Quitter le club/ })).toBeInTheDocument();
  });

  it("ignore une adhésion à un autre club", async () => {
    await afficher(
      <AdhesionClub
        club={club}
        adhesion={{ ...adhesion("active"), club_id: "autre-club" }}
        membres={null}
        onRafraichir={rafraichir}
      />,
    );

    expect(screen.getByRole("button", { name: /Rejoindre ce club/ })).toBeInTheDocument();
  });
});

describe("GestionClub — le président", () => {
  const demandeEleve: DemandeAdhesion = {
    id: "adh-9",
    pseudonyme: "Kofi Curieux",
    classe: "2nde",
    demande_le: "2026-11-05T10:00:00Z",
    version: 1,
  };
  const demandeEncadreur: DemandeRattachement = {
    id: "rat-9",
    prenom: "Afi",
    nom: "Mensah",
    fonction: "sante",
    etablissement: "Lycée de Tokoin I",
    demande_le: "2026-11-05T10:00:00Z",
    version: 2,
  };

  it("confirme les demandes des élèves et des encadreurs", async () => {
    api.confirmerAdhesion.mockResolvedValue({});
    api.confirmerRattachement.mockResolvedValue({});
    await afficher(
      <GestionClub
        clubId="club-1"
        demandesAdhesion={[demandeEleve]}
        demandesRattachement={[demandeEncadreur]}
        membres={membres}
        onRafraichir={rafraichir}
      />,
    );

    expect(screen.getByRole("tab", { name: "Demandes (2)" })).toBeInTheDocument();
    const [eleve, encadreur] = screen.getAllByRole("button", { name: /Confirmer/ });
    await act(async () => {
      fireEvent.click(eleve!);
    });
    await act(async () => {
      fireEvent.click(encadreur!);
    });

    expect(api.confirmerAdhesion).toHaveBeenCalledWith("club-1", "adh-9", 1);
    expect(api.confirmerRattachement).toHaveBeenCalledWith("club-1", "rat-9", 2);
  });

  it("ouvre la liste des membres quand il n'y a pas de demande", async () => {
    await afficher(
      <GestionClub
        clubId="club-1"
        demandesAdhesion={[]}
        demandesRattachement={[]}
        membres={membres}
        onRafraichir={rafraichir}
      />,
    );

    // Le président peut retirer un membre ou un encadreur, mais pas lui-même.
    expect(screen.getAllByRole("button", { name: /Retirer/ })).toHaveLength(2);
  });
});
