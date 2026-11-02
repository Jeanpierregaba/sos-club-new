import { createIsomorphicFn } from "@tanstack/react-start";
import { getRequestHeader } from "@tanstack/react-start/server";

import type { components } from "./schema.gen";

export type Moi = components["schemas"]["Moi"];
export type ChiffresAdmin = components["schemas"]["ChiffresAdmin"];

export const MESSAGE_INDISPONIBLE =
  "Connexion impossible pour le moment. Réessaie dans quelques instants.";

export class ErreurApi extends Error {
  constructor(
    readonly statut: number,
    message: string,
  ) {
    super(message);
    this.name = "ErreurApi";
  }
}

// Dans le navigateur, /api passe par le domaine du site (ADR-0006). Pendant le rendu serveur, le site
// appelle l'API directement et lui transmet le cookie reçu du navigateur.
const envoyer = createIsomorphicFn()
  .server((chemin: string, init: RequestInit) => {
    const base = process.env["API_URL_INTERNE"] || "http://127.0.0.1:8000";
    const cookie = getRequestHeader("cookie");
    return fetch(`${base}${chemin}`, {
      ...init,
      headers: { ...init.headers, ...(cookie ? { cookie } : {}) },
      signal: AbortSignal.timeout(5000),
    });
  })
  .client((chemin: string, init: RequestInit) =>
    fetch(chemin, { ...init, signal: AbortSignal.timeout(15000) }),
  );

async function requeteApi<T>(chemin: string, init: RequestInit = {}): Promise<T> {
  let reponse: Response;
  try {
    reponse = await envoyer(chemin, init);
  } catch {
    throw new ErreurApi(0, MESSAGE_INDISPONIBLE);
  }
  if (reponse.status === 204) return undefined as T;

  const corps: unknown = await reponse.json().catch(() => null);
  if (!reponse.ok) {
    const detail = (corps as { detail?: unknown } | null)?.detail;
    throw new ErreurApi(reponse.status, typeof detail === "string" ? detail : MESSAGE_INDISPONIBLE);
  }
  return corps as T;
}

// Renvoie null pour un visiteur. Une API en panne reste une erreur : ce n'est pas la même chose.
export async function chargerMoi(): Promise<Moi | null> {
  try {
    return await requeteApi<Moi>("/api/comptes/moi");
  } catch (erreur) {
    if (erreur instanceof ErreurApi && erreur.statut === 401) return null;
    throw erreur;
  }
}

export function connecter(identifiant: string, motDePasse: string): Promise<Moi> {
  return requeteApi<Moi>("/api/comptes/connexion", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ identifiant, mot_de_passe: motDePasse }),
  });
}

export function deconnecter(): Promise<void> {
  return requeteApi<void>("/api/comptes/deconnexion", { method: "POST" });
}

export function chargerChiffresAdmin(): Promise<ChiffresAdmin> {
  return requeteApi<ChiffresAdmin>("/api/admin/chiffres");
}
