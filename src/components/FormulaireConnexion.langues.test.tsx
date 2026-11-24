import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { overwriteGetLocale } from "@/paraglide/runtime.js";

import { FormulaireConnexion } from "./FormulaireConnexion";

// La vraie classe ErreurApi, qui traduit le message français de l'API ; seul l'appel réseau est simulé.
const connecter = vi.hoisted(() => vi.fn());
vi.mock("@/lib/api/client", async (original) => ({
  ...(await original<typeof import("@/lib/api/client")>()),
  connecter,
}));

const { ErreurApi } = await import("@/lib/api/client");
const parler = (langue: "fr" | "en" | "de") => overwriteGetLocale(() => langue);

function envoyer(identifiant: string, motDePasse: string) {
  fireEvent.change(screen.getByLabelText("Username or email"), { target: { value: identifiant } });
  fireEvent.change(screen.getByLabelText("Password"), { target: { value: motDePasse } });
  fireEvent.click(screen.getByRole("button", { name: "Log in" }));
}

describe("connexion en anglais (spec 052)", () => {
  beforeEach(() => {
    parler("en");
    connecter.mockReset();
  });
  afterEach(() => parler("fr"));

  it("donne les messages de validation en anglais", async () => {
    render(<FormulaireConnexion onConnecte={vi.fn()} />);
    fireEvent.click(screen.getByRole("button", { name: "Log in" }));
    expect(await screen.findByText("Enter your username or email.")).toBeInTheDocument();
    expect(screen.getByText("Enter your password.")).toBeInTheDocument();
  });

  it("traduit les identifiants faux, la limite d'essais et le réseau coupé", async () => {
    const cas: [InstanceType<typeof ErreurApi>, string][] = [
      [
        new ErreurApi(401, "Identifiant ou mot de passe incorrect"),
        "Incorrect username or password",
      ],
      [
        new ErreurApi(429, "Trop d'essais. Réessaie dans 15 minutes."),
        "Too many attempts. Try again in 15 minutes.",
      ],
      [
        new ErreurApi(0, "Connexion impossible pour le moment. Réessaie dans quelques instants."),
        "Can't connect right now. Try again in a moment.",
      ],
    ];
    for (const [erreur, attendu] of cas) {
      connecter.mockRejectedValueOnce(erreur);
      const { unmount } = render(<FormulaireConnexion onConnecte={vi.fn()} />);
      envoyer("jeank", "secret");
      expect(await screen.findByRole("alert")).toHaveTextContent(attendu);
      unmount();
    }
  });

  it("affiche en allemand une erreur réseau qui n'est pas une erreur de l'API", async () => {
    parler("de");
    connecter.mockRejectedValueOnce(new TypeError("Failed to fetch"));
    render(<FormulaireConnexion onConnecte={vi.fn()} />);
    fireEvent.change(screen.getByLabelText("Benutzername oder E-Mail"), {
      target: { value: "jeank" },
    });
    fireEvent.change(screen.getByLabelText("Passwort"), { target: { value: "secret" } });
    fireEvent.click(screen.getByRole("button", { name: "Anmelden" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Verbindung gerade nicht möglich. Versuch es gleich noch einmal.",
    );
  });
});
