import { afterEach, describe, expect, it } from "vitest";

import { ErreurApi, MESSAGE_INDISPONIBLE, MESSAGE_SAISIE } from "@/lib/api/client";
import { overwriteGetLocale } from "@/paraglide/runtime.js";

import { traduireErreur, traduireValidation } from "./erreurs";

const parler = (langue: "fr" | "en" | "de") => overwriteGetLocale(() => langue);

describe("erreurs de l'API dans la langue de la page (spec 052)", () => {
  afterEach(() => parler("fr"));

  it("garde le message français tel quel sur une page française", () => {
    parler("fr");
    expect(traduireErreur("Identifiant ou mot de passe incorrect", 401)).toBe(
      "Identifiant ou mot de passe incorrect",
    );
    expect(new ErreurApi(0, MESSAGE_INDISPONIBLE).message).toBe(MESSAGE_INDISPONIBLE);
  });

  it("traduit les erreurs connues de l'inscription et de la connexion", () => {
    parler("en");
    expect(traduireErreur("Identifiant ou mot de passe incorrect", 401)).toBe(
      "Incorrect username or password",
    );
    expect(traduireErreur("Trop d'essais. Réessaie dans 15 minutes.", 429)).toBe(
      "Too many attempts. Try again in 15 minutes.",
    );
    expect(traduireErreur("Cet identifiant ou cet e-mail est déjà pris.", 409)).toBe(
      "This username or email is already taken.",
    );
    parler("de");
    expect(traduireErreur("Code incorrect.", 400)).toBe("Falscher Code.");
  });

  it("traduit le formulaire mal rempli et le réseau coupé", () => {
    parler("en");
    expect(new ErreurApi(422, MESSAGE_SAISIE).message).toBe(
      "Check the form: a field is empty, too long or filled in incorrectly.",
    );
    expect(new ErreurApi(0, MESSAGE_INDISPONIBLE).message).toBe(
      "Can't connect right now. Try again in a moment.",
    );
  });

  it("traduit par statut une limite ou une panne au message inconnu", () => {
    parler("de");
    expect(traduireErreur("Un message que le site ne connaît pas.", 429)).toBe(
      "Zu viele Versuche. Versuch es später noch einmal.",
    );
    expect(traduireErreur("Base de données injoignable", 503)).toBe(
      "Verbindung gerade nicht möglich. Versuch es gleich noch einmal.",
    );
  });

  it("affiche tel quel, en français, un message inconnu qui n'est ni une limite ni une panne", () => {
    parler("en");
    expect(traduireErreur("Un message que le site ne connaît pas.", 400)).toBe(
      "Un message que le site ne connaît pas.",
    );
  });

  it("traduit les messages de validation du site, nombres compris", () => {
    parler("fr");
    expect(traduireValidation("Indique ton prénom.")).toBe("Indique ton prénom.");
    parler("en");
    expect(traduireValidation("Indique ton prénom.")).toBe("Enter your first name.");
    expect(traduireValidation("150 caractères au plus.")).toBe("150 characters at most.");
    parler("de");
    expect(traduireValidation("Vérifie la date : un élève a entre 8 et 30 ans.")).toBe(
      "Prüfe das Datum: Ein Schüler ist zwischen 8 und 30 Jahre alt.",
    );
    expect(traduireValidation("Un message inconnu.")).toBe("Un message inconnu.");
  });
});
