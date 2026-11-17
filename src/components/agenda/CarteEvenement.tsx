import { Link } from "@tanstack/react-router";
import { ArrowRight, Globe, MapPin, Users } from "lucide-react";

import type { EvenementPublic } from "@/lib/api/client";
import {
  COULEURS_NIVEAU,
  NIVEAUX,
  TYPES_EVENEMENT,
  dateEvenement,
  plageEvenement,
} from "@/lib/agenda";

// Un événement de l'agenda public. Aucun nom d'élève : le club, l'établissement et le nombre de participants.
export function CarteEvenement({
  evenement,
  passe = false,
}: {
  evenement: EvenementPublic;
  passe?: boolean;
}) {
  const niveau = COULEURS_NIVEAU[evenement.niveau];
  const teinte = passe || evenement.annule ? "var(--muted-foreground)" : niveau.couleur;
  return (
    <article
      className={`grid gap-5 rounded-[1.75rem] bg-white p-5 shadow-card ring-1 ring-border md:grid-cols-[6rem_1fr] md:p-7 ${passe ? "opacity-75" : ""}`}
    >
      <div
        className="flex flex-row items-baseline gap-2 self-start rounded-2xl px-4 py-3 text-white md:flex-col md:items-center md:gap-0"
        style={{ backgroundColor: teinte }}
      >
        <span className="font-display text-4xl leading-none md:text-5xl">
          {dateEvenement(evenement.debut, { day: "numeric" })}
        </span>
        <span className="text-sm font-extrabold uppercase">
          {dateEvenement(evenement.debut, { month: "short" })}
        </span>
        <span className="text-xs font-semibold capitalize text-white/80">
          {dateEvenement(evenement.debut, { weekday: "long" })}
        </span>
      </div>
      <div className="min-w-0">
        <div className="flex flex-wrap items-center gap-2">
          <span
            className="rounded-full px-2.5 py-0.5 text-[11px] font-extrabold uppercase text-white"
            style={{ backgroundColor: niveau.couleur }}
          >
            {NIVEAUX[evenement.niveau].court}
          </span>
          <span className="rounded-full bg-mist px-2.5 py-0.5 text-[11px] font-extrabold uppercase text-logo-blue">
            {TYPES_EVENEMENT[evenement.type] ?? evenement.type}
          </span>
          {evenement.annule ? (
            <span className="ml-auto rounded-full bg-logo-red px-2.5 py-0.5 text-[11px] font-extrabold uppercase text-white">
              Annulé
            </span>
          ) : evenement.complet ? (
            <span className="ml-auto rounded-full bg-sun px-2.5 py-0.5 text-[11px] font-extrabold uppercase text-ink">
              Complet
            </span>
          ) : passe ? (
            <span className="ml-auto text-xs font-extrabold uppercase text-muted-foreground">
              Terminé
            </span>
          ) : null}
        </div>
        <h3 className="mt-3 font-sans text-xl font-extrabold leading-snug">
          <Link to="/agenda/$id" params={{ id: evenement.id }} className="hover:underline">
            {evenement.titre}
          </Link>
        </h3>
        <p className="mt-1 text-sm font-bold text-logo-blue">
          {plageEvenement(evenement.debut, evenement.fin)}
        </p>
        <p className="mt-2 line-clamp-3 font-medium text-muted-foreground">
          {evenement.description}
        </p>
        <div className="mt-5 flex flex-wrap items-center gap-x-5 gap-y-2 border-t pt-4 text-sm font-semibold">
          <span className="flex min-w-0 items-center gap-1.5">
            {evenement.en_ligne ? (
              <>
                <Globe className="size-4 shrink-0 text-logo-red" /> En ligne
              </>
            ) : (
              <>
                <MapPin className="size-4 shrink-0 text-logo-red" /> {evenement.lieu}
              </>
            )}
          </span>
          {evenement.club && <span className="text-muted-foreground">{evenement.club}</span>}
          {evenement.dre && <span className="text-muted-foreground">DRE {evenement.dre}</span>}
          {evenement.niveau === "club" && (
            <span className="flex items-center gap-1.5 text-muted-foreground">
              <Users className="size-4" /> {evenement.participants} participant
              {evenement.participants > 1 ? "s" : ""}
              {evenement.places ? ` sur ${evenement.places}` : ""}
            </span>
          )}
          <Link
            to="/agenda/$id"
            params={{ id: evenement.id }}
            className="ml-auto inline-flex items-center gap-1.5 font-bold text-logo-blue hover:underline"
          >
            Détails <ArrowRight className="size-4" />
          </Link>
        </div>
      </div>
    </article>
  );
}
