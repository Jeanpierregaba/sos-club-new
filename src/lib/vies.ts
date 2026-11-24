import type { Vies } from "@/lib/api/client";
import { m } from "@/paraglide/messages.js";

// Spec 048 : le message affiché quand le joueur a perdu ses vies du jour (le même que celui de l'API).
export const messagePlusDeVies = (total = 3) => m.vies_plus({ total: String(total) });

export const plusDeVies = (vies: Vies | null | undefined) => vies != null && vies.restantes === 0;
