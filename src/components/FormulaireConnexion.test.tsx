import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { FormulaireConnexion } from "./FormulaireConnexion";

const connecter = vi.hoisted(() => vi.fn());

vi.mock("@/lib/api/client", async () => {
  class ErreurApi extends Error {
    constructor(
      readonly statut: number,
      message: string,
    ) {
      super(message);
    }
  }
  return { connecter, ErreurApi, MESSAGE_INDISPONIBLE: "Connexion impossible pour le moment." };
});

const { ErreurApi } = await import("@/lib/api/client");
const moi = { id: "1", identifiant: "jeank", prenom: "Jean", nom: "K", role: "eleve" };

function remplir(identifiant: string, motDePasse: string) {
  fireEvent.change(screen.getByLabelText("Identifiant ou email"), {
    target: { value: identifiant },
  });
  fireEvent.change(screen.getByLabelText("Mot de passe"), { target: { value: motDePasse } });
}

const valider = () => fireEvent.click(screen.getByRole("button", { name: "Me connecter" }));

describe("FormulaireConnexion", () => {
  beforeEach(() => {
    connecter.mockReset();
  });

  it("n'appelle pas l'API quand un champ est vide", async () => {
    render(<FormulaireConnexion onConnecte={vi.fn()} />);

    valider();

    expect(await screen.findByText("Indique ton identifiant ou ton email.")).toBeInTheDocument();
    expect(screen.getByText("Indique ton mot de passe.")).toBeInTheDocument();
    expect(connecter).not.toHaveBeenCalled();
  });

  it("n'envoie pas un mot de passe de plus de 256 caractères", async () => {
    render(<FormulaireConnexion onConnecte={vi.fn()} />);

    remplir("jeank", "x".repeat(257));
    valider();

    expect(await screen.findByText("Ce mot de passe est trop long.")).toBeInTheDocument();
    expect(connecter).not.toHaveBeenCalled();
  });

  it("envoie l'identifiant sans espaces et le mot de passe tel quel", async () => {
    connecter.mockResolvedValue(moi);
    const onConnecte = vi.fn();
    render(<FormulaireConnexion onConnecte={onConnecte} />);

    remplir("  jeank ", " Éléphant 42 ");
    valider();

    await waitFor(() => expect(onConnecte).toHaveBeenCalledWith(moi));
    expect(connecter).toHaveBeenCalledWith("jeank", " Éléphant 42 ");
  });

  it("affiche le message de l'API et garde le formulaire rempli", async () => {
    connecter.mockRejectedValue(new ErreurApi(401, "Identifiant ou mot de passe incorrect"));
    render(<FormulaireConnexion onConnecte={vi.fn()} />);

    remplir("jeank", "faux");
    valider();

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Identifiant ou mot de passe incorrect",
    );
    expect(screen.getByLabelText("Identifiant ou email")).toHaveValue("jeank");
    expect(screen.getByLabelText("Mot de passe")).toHaveValue("faux");
  });

  it("affiche le message d'indisponibilité quand le réseau est coupé", async () => {
    connecter.mockRejectedValue(new ErreurApi(0, "Connexion impossible pour le moment."));
    render(<FormulaireConnexion onConnecte={vi.fn()} />);

    remplir("jeank", "secret");
    valider();

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Connexion impossible pour le moment.",
    );
    expect(screen.getByLabelText("Mot de passe")).toHaveValue("secret");
  });

  it("désactive le bouton pendant l'envoi", async () => {
    let terminer = (_: unknown) => {};
    connecter.mockReturnValue(new Promise((resolve) => (terminer = resolve)));
    render(<FormulaireConnexion onConnecte={vi.fn()} />);

    remplir("jeank", "secret");
    valider();

    await waitFor(() =>
      expect(screen.getByRole("button", { name: "Me connecter" })).toBeDisabled(),
    );
    await act(async () => terminer(moi));
  });

  it("affiche et masque le mot de passe", () => {
    render(<FormulaireConnexion onConnecte={vi.fn()} />);
    const champ = screen.getByLabelText("Mot de passe");
    expect(champ).toHaveAttribute("type", "password");

    fireEvent.click(screen.getByRole("button", { name: "Afficher le mot de passe" }));

    expect(champ).toHaveAttribute("type", "text");
  });
});
