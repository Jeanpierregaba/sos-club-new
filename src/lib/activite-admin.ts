// Mise en forme des chiffres de la page « Activité » (spec 051).
import type { BlocActivite } from "@/lib/api/client";

type Chiffre = BlocActivite["chiffres"][number];
type Unite = Chiffre["unite"];

const NOMBRE = new Intl.NumberFormat("fr-FR", { maximumFractionDigits: 1 });

export function formater(
  valeur: string | number | null | undefined,
  unite: Unite = "nombre",
): string {
  if (valeur === null || valeur === undefined || valeur === "") return "—";
  if (typeof valeur === "string") return valeur;
  if (unite === "pourcent") return `${NOMBRE.format(valeur)} %`;
  if (unite === "secondes") {
    const minutes = Math.floor(valeur / 60);
    return minutes ? `${minutes} min ${Math.round(valeur % 60)} s` : `${Math.round(valeur)} s`;
  }
  return NOMBRE.format(valeur);
}

/** L'écart à la période précédente : en % pour un nombre, en points pour un pourcentage. */
export function ecart(
  chiffre: Chiffre,
): { texte: string; sens: "hausse" | "baisse" | "egal" } | null {
  const { valeur, precedent, unite } = chiffre;
  if (valeur === null || valeur === undefined || precedent === null || precedent === undefined)
    return null;
  const sens = valeur > precedent ? "hausse" : valeur < precedent ? "baisse" : "egal";
  if (unite === "pourcent") {
    const points = valeur - precedent;
    return { texte: `${points > 0 ? "+" : ""}${NOMBRE.format(points)} pts`, sens };
  }
  if (precedent === 0) return { texte: valeur > 0 ? "nouveau" : "=", sens };
  const taux = ((valeur - precedent) / precedent) * 100;
  return { texte: `${taux > 0 ? "+" : ""}${NOMBRE.format(taux)} %`, sens };
}
