import { formatDeLaLangue } from "./langues";

// Dates dans la langue de la page (spec 052) : le français partout, sauf les pages publiques lues en anglais ou en
// allemand.
export const dateCourte = (iso: string) =>
  new Date(iso).toLocaleDateString(formatDeLaLangue(), {
    day: "numeric",
    month: "long",
    year: "numeric",
  });

// Date et heure courtes, pour les étapes datées de l'admin.
export const dateHeure = (iso: string) =>
  new Date(iso).toLocaleString(formatDeLaLangue(), { dateStyle: "short", timeStyle: "short" });
