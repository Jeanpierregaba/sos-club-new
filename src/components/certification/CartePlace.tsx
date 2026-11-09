import { Link } from "@tanstack/react-router";
import { BookOpenText, CheckCircle2, Clock, Lock, Play } from "lucide-react";

import { urlRessource, type PlaceParcours } from "@/lib/api/client";
import { ETATS_PLACE, jouable } from "@/lib/certification";

// Une place du parcours (spec 029) : son état, son fascicule à lire avant de jouer, et le bouton pour jouer.
export function CartePlace({ place, seuil }: { place: PlaceParcours; seuil: number }) {
  const etat = ETATS_PLACE[place.etat];
  const Icone =
    place.etat === "reussie"
      ? CheckCircle2
      : place.etat === "ouverte"
        ? Play
        : place.etat === "bientot"
          ? Clock
          : Lock;
  const titre = place.titre ?? (place.etat === "reussie" ? "Quiz réussi" : "Quiz à venir");

  return (
    <li
      className={`flex flex-col gap-3 rounded-3xl p-5 shadow-card sm:flex-row sm:items-center ${place.etat === "ouverte" ? "bg-white ring-2 ring-primary" : "bg-card"}`}
    >
      <div className="flex min-w-0 flex-1 items-start gap-4">
        <span
          className={`grid size-12 shrink-0 place-items-center rounded-2xl font-display text-xl ${place.etat === "reussie" ? "bg-primary text-primary-foreground" : place.etat === "ouverte" ? "bg-sun text-ink" : "bg-mist text-muted-foreground"}`}
        >
          {place.place}
        </span>
        <div className="min-w-0">
          <p className="flex flex-wrap items-center gap-2">
            <span
              className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-bold ${etat.classe}`}
            >
              <Icone aria-hidden className="size-3.5" /> {etat.libelle}
            </span>
            {place.contenu_de_test && (
              <span className="rounded-full bg-sun/30 px-2 py-0.5 text-xs font-semibold text-ink">
                Contenu de test
              </span>
            )}
          </p>
          <h3 className="mt-1 break-words font-sans text-base font-extrabold text-ink">{titre}</h3>
          {place.meilleur_score !== null && (
            <p className="text-sm text-muted-foreground">
              Meilleur score : {place.meilleur_score} (réussite à {seuil})
            </p>
          )}
          {place.etat === "verrouillee" && (
            <p className="text-sm text-muted-foreground">
              Réussis d'abord le quiz {place.place - 1} pour l'ouvrir.
            </p>
          )}
          {place.fascicule && (
            <a
              href={urlRessource(place.fascicule.id)}
              target="_blank"
              rel="noopener"
              className="mt-1 inline-flex items-center gap-1.5 text-sm font-bold text-logo-blue hover:underline"
            >
              <BookOpenText aria-hidden className="size-4" />
              Lire le fascicule : {place.fascicule.titre}
              <span className="sr-only"> (s'ouvre dans un nouvel onglet)</span>
            </a>
          )}
        </div>
      </div>
      {jouable(place) && (
        <Link
          to="/certification/parcours/$place"
          params={{ place: String(place.place) }}
          className={`inline-flex h-11 shrink-0 items-center justify-center gap-2 rounded-full px-5 text-sm font-bold ${place.etat === "ouverte" ? "btn-fx bg-primary text-primary-foreground" : "text-logo-blue ring-1 ring-border hover:bg-mist"}`}
        >
          <Play aria-hidden className="size-4" />
          {place.tentative_en_cours ? "Reprendre" : place.etat === "reussie" ? "Rejouer" : "Jouer"}
          <span className="sr-only"> le quiz {place.place}</span>
        </Link>
      )}
    </li>
  );
}
