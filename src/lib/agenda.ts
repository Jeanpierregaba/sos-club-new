// Libellés et formats de l'agenda (spec 041). Les heures s'affichent à Lomé (UTC+0, sans heure d'été) : le serveur
// et le navigateur montrent la même heure.

import { Landmark, School, Stethoscope } from "lucide-react";
import type { LucideIcon } from "lucide-react";

import type { EvenementPublic, ReponseAgenda } from "@/lib/api/client";
import { formatDeLaLangue, LANGUE_DE_BASE, langueCourante } from "@/lib/langues";
import { m } from "@/paraglide/messages.js";

export const FUSEAU = "Africa/Lome";

export const TYPES_EVENEMENT: Record<string, string> = {
  formation: "Formation",
  sensibilisation: "Sensibilisation",
  concours: "Concours",
  assainissement: "Assainissement",
  campagne: "Campagne",
  emission: "Émission",
  reunion: "Réunion",
  autre: "Autre",
};

/** Le type d'un événement dans la langue de la page (spec 052) ; un type inconnu s'affiche tel quel. */
export function typeEvenement(type: string): string {
  const message = m[`agenda_type_${type}` as keyof typeof m] as (() => string) | undefined;
  return typeof message === "function" ? message() : (TYPES_EVENEMENT[type] ?? type);
}

export const NIVEAUX: Record<"national" | "regional" | "club", { court: string; long: string }> = {
  national: { court: "Secrétariat technique permanent", long: "Coordination centrale & pilotage" },
  regional: { court: "Comité", long: "Encadrement scientifique & régional" },
  club: { court: "Club Santé SOS Docteur TV", long: "Actions terrain & vie des établissements" },
};

export const REPONSES: Record<ReponseAgenda, string> = {
  participe: "Je participe",
  peut_etre: "Peut-être",
  non: "Je ne peux pas",
};

export const ETATS_EVENEMENT: Record<string, string> = {
  brouillon: "Brouillon",
  en_attente: "En attente de validation",
  a_corriger: "À corriger",
  refuse: "Refusé",
  publie: "Publié",
  depublie: "Retiré du site",
  retire: "Retiré",
};

export function dateEvenement(iso: string, options: Intl.DateTimeFormatOptions): string {
  return new Date(iso).toLocaleDateString(formatDeLaLangue(), { timeZone: FUSEAU, ...options });
}

export function heureEvenement(iso: string): string {
  const heure = new Date(iso).toLocaleTimeString(formatDeLaLangue(), {
    timeZone: FUSEAU,
    hour: "2-digit",
    minute: "2-digit",
  });
  // « 09 h 30 » en français ; l'anglais et l'allemand gardent leur propre écriture.
  return langueCourante() === LANGUE_DE_BASE ? heure.replace(":", " h ") : heure;
}

// « Samedi 5 décembre, 09 h 30 – 11 h 30 »
export function plageEvenement(debut: string, fin: string): string {
  const brut = dateEvenement(debut, { weekday: "long", day: "numeric", month: "long" });
  // Seule la première lettre prend une majuscule : « Dimanche 22 novembre », pas « Dimanche 22 Novembre ».
  const jour = brut.charAt(0).toUpperCase() + brut.slice(1);
  const memeJour =
    dateEvenement(debut, { year: "numeric", month: "2-digit", day: "2-digit" }) ===
    dateEvenement(fin, { year: "numeric", month: "2-digit", day: "2-digit" });
  return memeJour
    ? `${jour}, ${heureEvenement(debut)} – ${heureEvenement(fin)}`
    : `${jour}, ${heureEvenement(debut)} – ${dateEvenement(fin, { day: "numeric", month: "long" })}, ${heureEvenement(fin)}`;
}

// La valeur d'un champ <input type="datetime-local"> (heure de Lomé, soit UTC) à partir d'une date ISO. Une heure
// sans fuseau (un brouillon) est déjà celle de Lomé ; une heure datée est ramenée en UTC.
export function versSaisie(iso: string | null | undefined): string {
  if (!iso) return "";
  const date = /(Z|[+-]\d{2}:?\d{2})$/.test(iso) ? new Date(iso).toISOString() : iso;
  return date.slice(0, 16);
}

export const COULEURS_NIVEAU: Record<
  EvenementPublic["niveau"],
  { couleur: string; icone: LucideIcon }
> = {
  national: { couleur: "var(--logo-blue)", icone: Landmark },
  regional: { couleur: "var(--grape)", icone: Stethoscope },
  club: { couleur: "var(--primary)", icone: School },
};

// Une heure saisie à Lomé, sans fuseau (un brouillon), datée en UTC pour l'affichage.
export function depuisLome(iso: string): string {
  return /(Z|[+-]\d{2}:?\d{2})$/.test(iso) ? iso : `${iso}Z`;
}
