import { afterEach, describe, expect, it, vi } from "vitest";

import {
  chargerMoi,
  connecter,
  deconnecter,
  ErreurApi,
  MESSAGE_INDISPONIBLE,
  type Moi,
} from "./client";

// Sans le compilateur de TanStack Start, seule la branche navigateur est gardée.
vi.mock("@tanstack/react-start", () => ({
  createIsomorphicFn: () => ({
    server: () => ({ client: (fonction: unknown) => fonction }),
  }),
}));
vi.mock("@tanstack/react-start/server", () => ({ getRequestHeader: vi.fn() }));

const moi: Moi = { id: "1", identifiant: "jeank", prenom: "Jean", nom: "K", role: "eleve" };

function repondre(statut: number, corps?: string) {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => new Response(corps ?? null, { status: statut })),
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("chargerMoi", () => {
  it("renvoie l'utilisateur connecté", async () => {
    repondre(200, JSON.stringify(moi));

    await expect(chargerMoi()).resolves.toEqual(moi);
  });

  it("renvoie null pour un visiteur", async () => {
    repondre(401, JSON.stringify({ detail: "Connecte-toi pour continuer." }));

    await expect(chargerMoi()).resolves.toBeNull();
  });

  it("ne confond pas une API en panne avec un visiteur", async () => {
    repondre(500, "Internal Server Error");

    await expect(chargerMoi()).rejects.toMatchObject({
      statut: 500,
      message: MESSAGE_INDISPONIBLE,
    });
  });

  it("signale un réseau coupé", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));

    const erreur = await chargerMoi().catch((e: unknown) => e);

    expect(erreur).toBeInstanceOf(ErreurApi);
    expect(erreur).toMatchObject({ statut: 0, message: MESSAGE_INDISPONIBLE });
  });
});

describe("connecter", () => {
  it("envoie les identifiants en JSON", async () => {
    repondre(200, JSON.stringify(moi));

    await connecter("jeank", "secret");

    expect(fetch).toHaveBeenCalledWith(
      "/api/comptes/connexion",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ identifiant: "jeank", mot_de_passe: "secret" }),
      }),
    );
  });

  it("transmet le message de l'API", async () => {
    repondre(429, JSON.stringify({ detail: "Trop d'essais. Réessaie dans 15 minutes." }));

    await expect(connecter("jeank", "secret")).rejects.toMatchObject({
      statut: 429,
      message: "Trop d'essais. Réessaie dans 15 minutes.",
    });
  });

  it("n'affiche pas le détail technique d'une erreur de validation", async () => {
    repondre(422, JSON.stringify({ detail: [{ loc: ["body"], msg: "x", type: "y" }] }));

    await expect(connecter("jeank", "secret")).rejects.toMatchObject({
      statut: 422,
      message: MESSAGE_INDISPONIBLE,
    });
  });
});

describe("deconnecter", () => {
  it("accepte une réponse sans contenu", async () => {
    repondre(204);

    await expect(deconnecter()).resolves.toBeUndefined();
  });
});
