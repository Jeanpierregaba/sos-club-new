// L'adresse du site (`https://domaine`), pour les liens qui doivent être complets (`hreflang`, spec 052).
import { createIsomorphicFn } from "@tanstack/react-start";
import { getRequestHeader } from "@tanstack/react-start/server";

/**
 * Côté serveur : `SITE_ORIGINE` (celle que l'API connaît, ADR-0006), sinon l'hôte de la requête (en local). Dans le
 * navigateur : l'adresse de la page.
 */
export const origineDuSite = createIsomorphicFn()
  .server((): string => {
    const configuree = process.env["SITE_ORIGINE"];
    if (configuree) return configuree.replace(/\/+$/, "");
    const protocole = getRequestHeader("x-forwarded-proto")?.split(",")[0]?.trim() || "http";
    return `${protocole}://${getRequestHeader("host") ?? "localhost:3000"}`;
  })
  .client((): string => window.location.origin);
