import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { DialogueModification } from "@/components/admin/fiche-inscrit/DialogueModification";
import type { InscritDetail } from "@/lib/api/client";
import { entreeDe, valeursDe } from "@/lib/modification-inscrit";

const MOTIF = "Faute de frappe signalée";

const base = {
  id: "u1",
  identifiant: "eleve1",
  prenom: "Jean",
  nom: "Kodjo",
  email: null,
  telephone: null,
  statut: "actif",
  consentement_le: null,
  cree_le: "2026-11-01T10:00:00Z",
  historique: [],
  carte: null,
} as const;

const eleve = {
  ...base,
  role: "eleve",
  version: 4,
  eleve: { classe: "2nde" },
  encadreur: null,
} as unknown as InscritDetail;

const encadreur = {
  ...base,
  role: "encadreur",
  email: "prof@ecole.tg",
  telephone: "+22890123456",
  version: 2,
  eleve: null,
  encadreur: {
    fonction: "enseignant",
    fonction_precision: null,
    discipline: null,
    commune: "Golfe 1",
  },
} as unknown as InscritDetail;

describe("entreeDe", () => {
  it("n'envoie que les champs changés, sans espaces autour", () => {
    const valeurs = { ...valeursDe(eleve), prenom: "  Afi ", classe: "tle" };

    expect(entreeDe(eleve, valeurs, `  ${MOTIF} `)).toEqual({
      motif: MOTIF,
      version: 4,
      prenom: "Afi",
      classe: "tle",
    });
  });

  it("n'envoie rien du profil d'encadreur pour un élève, et inversement", () => {
    const pourEleve = entreeDe(eleve, { ...valeursDe(eleve), commune: "Lomé" }, MOTIF);
    const pourEncadreur = entreeDe(encadreur, { ...valeursDe(encadreur), classe: "3e" }, MOTIF);

    expect(pourEleve).toEqual({ motif: MOTIF, version: 4 });
    expect(pourEncadreur).toEqual({ motif: MOTIF, version: 2 });
  });

  it("vide l'e-mail d'un élève avec une chaîne vide", () => {
    const avecEmail = { ...eleve, email: "a@b.tg" } as InscritDetail;

    expect(entreeDe(avecEmail, { ...valeursDe(avecEmail), email: "" }, MOTIF)).toMatchObject({
      email: "",
    });
  });
});

describe("DialogueModification", () => {
  it("montre la classe pour un élève et la commune pour un encadreur", () => {
    const { unmount } = render(
      <DialogueModification inscrit={eleve} fermer={() => {}} envoyer={vi.fn()} />,
    );
    expect(screen.getByLabelText("Classe")).toBeTruthy();
    expect(screen.queryByLabelText("Commune")).toBeNull();
    unmount();

    render(<DialogueModification inscrit={encadreur} fermer={() => {}} envoyer={vi.fn()} />);
    expect(screen.getByLabelText("Commune")).toBeTruthy();
    expect(screen.queryByLabelText("Classe")).toBeNull();
  });

  it("garde le bouton grisé tant que rien n'a changé, puis envoie les changements", async () => {
    const envoyer = vi.fn().mockResolvedValue(undefined);
    const fermer = vi.fn();
    render(<DialogueModification inscrit={encadreur} fermer={fermer} envoyer={envoyer} />);
    const bouton = screen.getByRole("button", { name: "Enregistrer" });
    expect(bouton.hasAttribute("disabled")).toBe(true);

    fireEvent.change(screen.getByLabelText("Commune"), { target: { value: "Golfe 3" } });
    fireEvent.change(screen.getByLabelText("Motif (inscrit au journal)"), {
      target: { value: MOTIF },
    });
    fireEvent.click(screen.getByRole("button", { name: "Enregistrer" }));

    await waitFor(() =>
      expect(envoyer).toHaveBeenCalledWith({ motif: MOTIF, version: 2, commune: "Golfe 3" }),
    );
    await waitFor(() => expect(fermer).toHaveBeenCalled());
  });

  it("demande la précision quand la fonction est « autre »", () => {
    render(<DialogueModification inscrit={encadreur} fermer={() => {}} envoyer={vi.fn()} />);
    expect(screen.queryByLabelText("Précise la fonction")).toBeNull();

    fireEvent.change(screen.getByLabelText("Fonction"), { target: { value: "autre" } });

    expect(screen.getByLabelText("Précise la fonction")).toBeTruthy();
  });
});
