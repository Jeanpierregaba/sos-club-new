import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import type { ArticleAuteur } from "@/lib/api/client";

import { Photos } from "./Photos";

const article = {
  id: "a1",
  etat: "brouillon",
  version: 1,
  champs: { titre: "T", chapo: "C", texte: "X", axe_code: "axe", afficher_club: true },
  en_ligne: false,
  adresse: null,
  modifiable: true,
  soumettable: true,
  supprimable: true,
  derniere_decision: null,
  photos: [],
  soumis_le: null,
  publie_le: null,
  modifie_le: "2026-11-07T10:00:00Z",
} as ArticleAuteur;

describe("Photos", () => {
  it("n'envoie pas de photo sans l'attestation", () => {
    render(<Photos article={article} modifiable onArticle={vi.fn()} />);
    const envoyer = screen.getByRole("button", { name: /Envoyer la photo/ });
    const champ = screen.getByLabelText(/Ajouter une photo/);

    fireEvent.change(champ, {
      target: { files: [new File(["x"], "p.jpg", { type: "image/jpeg" })] },
    });
    expect(envoyer).toBeDisabled();

    fireEvent.click(screen.getByRole("checkbox", { name: "Attestation" }));
    expect(envoyer).toBeEnabled();
  });

  it("demande d'enregistrer le brouillon avant la première photo", () => {
    render(<Photos article={null} modifiable onArticle={vi.fn()} />);
    expect(screen.getByText(/Enregistre d'abord ton brouillon/)).toBeInTheDocument();
  });

  it("n'accepte que JPEG, PNG et WebP", () => {
    render(<Photos article={article} modifiable onArticle={vi.fn()} />);
    expect(screen.getByLabelText(/Ajouter une photo/)).toHaveAttribute(
      "accept",
      "image/jpeg,image/png,image/webp",
    );
  });
});
