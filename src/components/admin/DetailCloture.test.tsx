import {
  createMemoryHistory,
  createRootRoute,
  createRouter,
  RouterProvider,
} from "@tanstack/react-router";
import { act, fireEvent, render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";

import { ActionsCloture, DetailCloture } from "./DetailCloture";
import type { CandidatAdmin, ClotureDetail } from "@/lib/api/client";

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

const candidat = (rang: number, pseudonyme: string, options: Partial<CandidatAdmin> = {}) =>
  ({
    utilisateur_id: `u-${rang}`,
    rang,
    rang_brut: rang,
    pseudonyme,
    identifiant: `eleve.${rang}`,
    statut: "actif",
    club: "Club Santé Tokoin",
    dre: "Grand Lomé",
    points: 100 - rang,
    atteint_le: "2026-03-01T08:00:00Z",
    corrections: 0,
    annulations: 0,
    ecarte: false,
    motif_ecart: null,
    ecarte_le: null,
    ecarte_par: null,
    ...options,
  }) satisfies CandidatAdmin;

const cloture = (etat: ClotureDetail["etat"], candidats: CandidatAdmin[]): ClotureDetail => ({
  semestre: { id: "s-1", libelle: "Semestre 1 2026", debut: "2026-01-05", fin: "2026-06-30" },
  etat,
  etapes: {
    gele_le: "2026-07-01T09:00:00Z",
    gele_par: "admin.national",
    valide_le: null,
    valide_par: null,
    publie_le: null,
    publie_par: null,
  },
  candidats,
  top3: [],
  ecart_actuel: { top3_different: false, changements: [] },
});

const boutons = () => screen.queryAllByRole("button").map((b) => b.textContent?.trim());

describe("ActionsCloture (spec 037)", () => {
  it("propose le gel seulement pour un semestre terminé", () => {
    const { rerender } = render(
      <ActionsCloture etat="ouvert" termine={false} onAction={vi.fn()} />,
    );
    expect(boutons()).toEqual([]);
    rerender(<ActionsCloture etat="ouvert" termine onAction={vi.fn()} />);
    expect(boutons()).toEqual(["Geler le classement"]);
  });

  it("donne les actions de chaque état et rien après la publication", () => {
    const onAction = vi.fn();
    const { rerender } = render(<ActionsCloture etat="gele" termine onAction={onAction} />);
    expect(boutons()).toEqual(["Regeler", "Valider le Top 3"]);
    fireEvent.click(screen.getByRole("button", { name: /Valider le Top 3/ }));
    expect(onAction).toHaveBeenCalledWith("validation");

    rerender(<ActionsCloture etat="valide" termine onAction={onAction} />);
    expect(boutons()).toEqual(["Publier le palmarès", "Annuler la validation"]);

    rerender(<ActionsCloture etat="publie" termine onAction={onAction} />);
    expect(boutons()).toEqual([]);
  });
});

describe("DetailCloture (spec 037)", () => {
  const ecarte = candidat(2, "Ben", {
    ecarte: true,
    motif_ecart: "Points obtenus par un compte partagé.",
    ecarte_le: "2026-07-02T10:00:00Z",
    ecarte_par: "admin.national",
  });

  it("nomme chaque bouton par le candidat et renvoie vers ses lignes du registre", async () => {
    const onEcarter = vi.fn();
    await afficher(
      <DetailCloture
        cloture={cloture("gele", [candidat(1, "Aya"), ecarte])}
        modificateur
        onEcarter={onEcarter}
        onReintegrer={vi.fn()}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Écarter Aya" }));
    expect(onEcarter).toHaveBeenCalledWith(expect.objectContaining({ pseudonyme: "Aya" }));
    expect(screen.getByRole("button", { name: "Réintégrer Ben" })).toBeInTheDocument();
    expect(screen.getByText(/par admin\.national : « Points obtenus/)).toBeInTheDocument();
    const [lien] = screen.getAllByRole("link", { name: "Voir au registre" });
    if (!lien) throw new Error("lien absent");
    expect(lien.getAttribute("href")).toContain("recherche=eleve.1");
    expect(lien.getAttribute("href")).toContain("semestre_id=s-1");
  });

  it("n'offre aucun contrôle hors de l'état gelé ni à un simple lecteur", async () => {
    await afficher(
      <DetailCloture
        cloture={cloture("valide", [candidat(1, "Aya")])}
        modificateur
        onEcarter={vi.fn()}
        onReintegrer={vi.fn()}
      />,
    );
    expect(screen.queryByRole("button")).toBeNull();
  });

  it("distingue un élève devenu inclassable d'un élève sorti des 50 premiers", async () => {
    const detail = cloture("gele", [candidat(1, "Aya")]);
    detail.ecart_actuel = {
      top3_different: true,
      changements: [
        { pseudonyme: "Kofi", points_gel: 40, points_actuels: 40, hors_photo: true },
        { pseudonyme: "Ama", points_gel: 35, points_actuels: null, hors_photo: false },
      ],
    };
    await afficher(
      <DetailCloture
        cloture={detail}
        modificateur={false}
        onEcarter={vi.fn()}
        onReintegrer={vi.fn()}
      />,
    );
    expect(screen.getByText(/et le Top 3 changerait/)).toBeInTheDocument();
    expect(screen.getByText(/Kofi : 40 → 40 \(au-delà des 50 premiers\)/)).toBeInTheDocument();
    expect(screen.getByText(/Ama : 35 → plus classable/)).toBeInTheDocument();
  });
});
