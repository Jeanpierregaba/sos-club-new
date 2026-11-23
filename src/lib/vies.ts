import type { Vies } from "@/lib/api/client";

// Spec 048 : le message affiché quand le joueur a perdu ses vies du jour (le même que celui de l'API).
export const messagePlusDeVies = (total = 3) =>
  `Tu as utilisé tes ${total} vies aujourd'hui. Reviens demain, elles se rechargent à minuit.`;

export const plusDeVies = (vies: Vies | null | undefined) => vies != null && vies.restantes === 0;
