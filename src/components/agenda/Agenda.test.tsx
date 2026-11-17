import { act, fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  createMemoryHistory,
  createRootRoute,
  createRouter,
  RouterProvider,
} from "@tanstack/react-router";
import type { ReactNode } from "react";

import { CarteEvenement } from "@/components/agenda/CarteEvenement";
import { ChoixReponse } from "@/components/agenda/ChoixReponse";
import { FormulaireEvenement } from "@/components/agenda/FormulaireEvenement";
import { Reponses } from "@/components/agenda/Reponses";
import { ErreurApi } from "@/lib/api/client";
import type { EvenementPublic, ReponsesEvenement } from "@/lib/api/client";
import { plageEvenement, versSaisie } from "@/lib/agenda";

const api = vi.hoisted(() => ({ repondreEvenement: vi.fn(), pointerPresences: vi.fn() }));
vi.mock("@/lib/api/client", async (original) => ({
  ...(await original<typeof import("@/lib/api/client")>()),
  ...api,
}));

beforeEach(() => vi.clearAllMocks());

const evenement: EvenementPublic = {
  id: "0193e0c0-0000-7000-8000-000000000001",
  niveau: "club",
  type: "sensibilisation",
  axe_code: "sante-environnement",
  titre: "Causerie sur le paludisme",
  objectif: null,
  description: "Une causerie dans la cour, avec démonstration.",
  lieu: "Cour du lycée",
  en_ligne: false,
  lien: null,
  public_vise: null,
  debut: "2026-12-05T09:30:00Z",
  fin: "2026-12-05T11:30:00Z",
  places: 2,
  participants: 1,
  complet: false,
  annule: false,
  motif_annulation: null,
  dre_code: "grand-lome",
  dre: "Grand Lomé",
  club_id: "0193e0c0-0000-7000-8000-000000000002",
  club: "Club Santé Tokoin",
  etablissement: "Lycée de Tokoin I",
  peut_repondre: true,
  ma_reponse: null,
};

async function afficher(contenu: ReactNode) {
  const route = createRootRoute({ component: () => <>{contenu}</> });
  const router = createRouter({
    routeTree: route,
    history: createMemoryHistory({ initialEntries: ["/"] }),
  });
  render(<RouterProvider router={router} />);
  await act(() => router.load());
}

describe("heures de Lomé", () => {
  it("affiche la plage à l'heure de Lomé, quel que soit le navigateur", () => {
    expect(plageEvenement("2026-12-05T09:30:00Z", "2026-12-05T11:30:00Z")).toBe(
      "Samedi 5 décembre, 09 h 30 – 11 h 30",
    );
  });

  it("garde telle quelle une heure de brouillon et ramène une heure datée en UTC", () => {
    expect(versSaisie("2026-12-05T09:30:00")).toBe("2026-12-05T09:30");
    expect(versSaisie("2026-12-05T10:30:00+01:00")).toBe("2026-12-05T09:30");
  });
});

describe("CarteEvenement", () => {
  it("montre le club et le nombre de participants, et marque un événement annulé", async () => {
    await afficher(<CarteEvenement evenement={{ ...evenement, annule: true }} />);

    expect(screen.getByText("Club Santé Tokoin")).toBeTruthy();
    expect(screen.getByText(/1 participant sur 2/)).toBeTruthy();
    expect(screen.getByText("Annulé")).toBeTruthy();
  });

  it("marque un événement complet", async () => {
    await afficher(<CarteEvenement evenement={{ ...evenement, participants: 2, complet: true }} />);

    expect(screen.getByText("Complet")).toBeTruthy();
  });
});

describe("ChoixReponse", () => {
  it("enregistre la réponse et la montre choisie", async () => {
    api.repondreEvenement.mockResolvedValue({
      ...evenement,
      ma_reponse: "participe",
      participants: 2,
    });
    await afficher(<ChoixReponse evenement={evenement} />);

    await act(async () => fireEvent.click(screen.getByRole("button", { name: "Je participe" })));

    expect(api.repondreEvenement).toHaveBeenCalledWith(evenement.id, "participe");
    expect(screen.getByRole("button", { name: "Je participe" }).getAttribute("aria-pressed")).toBe(
      "true",
    );
  });

  it("désactive « Je participe » quand c'est complet, et montre le refus du serveur", async () => {
    await afficher(<ChoixReponse evenement={{ ...evenement, complet: true }} />);
    expect(
      (screen.getByRole("button", { name: "Je participe" }) as HTMLButtonElement).disabled,
    ).toBe(true);

    api.repondreEvenement.mockRejectedValue(
      new ErreurApi(409, "Cet événement a commencé : les réponses sont closes."),
    );
    await act(async () => fireEvent.click(screen.getByRole("button", { name: "Peut-être" })));

    expect(screen.getByRole("alert").textContent).toContain("les réponses sont closes");
  });
});

describe("FormulaireEvenement", () => {
  it("montre le message de l'API qui nomme le champ fautif", async () => {
    const onEnvoi = vi
      .fn()
      .mockRejectedValue(new ErreurApi(422, "Champ « fin » : la fin doit venir après le début"));
    await afficher(
      <FormulaireEvenement
        initial={{ ...evenement, debut: "2026-12-05T09:30", fin: "2026-12-05T11:30" }}
        axes={[{ code: "sante-environnement", libelle: "Santé et environnement" } as never]}
        bouton="Enregistrer"
        onEnvoi={onEnvoi}
      />,
    );

    await act(async () =>
      fireEvent.submit(screen.getByRole("button", { name: "Enregistrer" }).closest("form")!),
    );

    expect(onEnvoi).toHaveBeenCalledOnce();
    expect(onEnvoi.mock.calls[0]![0]).toMatchObject({
      titre: evenement.titre,
      debut: "2026-12-05T09:30",
    });
    expect(screen.getByRole("alert").textContent).toContain("la fin doit venir après le début");
  });
});

describe("Reponses", () => {
  const reponses: ReponsesEvenement = {
    participe: 1,
    peut_etre: 0,
    non: 0,
    sans_reponse: 1,
    presents: 0,
    pointage_ouvert: true,
    membres: [
      {
        eleve_id: "a",
        pseudonyme: "Kossi-K",
        nom: "Kossi Agbeko",
        reponse: "participe",
        present: null,
      },
      { eleve_id: "b", pseudonyme: "Afi-A", nom: "Afi Mensah", reponse: null, present: null },
    ],
  };

  it("pointe les présents et envoie la liste", async () => {
    api.pointerPresences.mockResolvedValue({ ...reponses, presents: 1 });
    await afficher(<Reponses evenementId="e1" initiales={reponses} />);

    await act(async () => fireEvent.click(screen.getAllByRole("checkbox")[0]!));
    await act(async () =>
      fireEvent.click(screen.getByRole("button", { name: "Enregistrer les présences" })),
    );

    expect(api.pointerPresences).toHaveBeenCalledWith("e1", { a: true, b: false });
    expect(screen.getByRole("status").textContent).toBe("Présences enregistrées.");
  });

  it("n'offre pas le pointage avant le début", async () => {
    await afficher(
      <Reponses evenementId="e1" initiales={{ ...reponses, pointage_ouvert: false }} />,
    );

    expect(screen.queryAllByRole("checkbox")).toHaveLength(0);
    expect(screen.getByText("Pas de réponse")).toBeTruthy();
  });
});
