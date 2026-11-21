import type { Vies } from "@/lib/api/client";

// Spec 048 : le message affiché quand le joueur a perdu ses 7 vies du jour (le même que celui de l'API).
export const MESSAGE_PLUS_DE_VIES =
  "Tu as utilisé tes 7 vies aujourd'hui. Reviens demain, elles se rechargent à minuit.";

export const plusDeVies = (vies: Vies | null | undefined) => vies != null && vies.restantes === 0;
