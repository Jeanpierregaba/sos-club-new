import { BadgeCheck, BookOpenText, Download } from "lucide-react";
import type { CSSProperties } from "react";

import { urlRessource, type RessourcePublique } from "@/lib/api/client";
import { CATEGORIES, tailleLisible, telechargements } from "@/lib/bibliotheque";
import { dateCourte } from "@/lib/dates";

// Une ressource publiée (spec 028) : sa couverture ou le visuel de sa catégorie, son validateur, et les deux
// façons de l'ouvrir. Les liens vont droit à l'API : le PDF part en flux, sans passer par le site.
export function CarteRessource({
  ressource,
  style,
}: {
  ressource: RessourcePublique;
  style?: CSSProperties;
}) {
  const categorie = CATEGORIES[ressource.categorie];
  const Icone = categorie.icone;
  return (
    <li
      data-reveal
      style={style}
      className="card-fx group flex flex-col overflow-hidden rounded-[1.75rem] bg-white shadow-card"
    >
      <div
        className={`relative isolate flex aspect-[4/3] items-center justify-center overflow-hidden ${categorie.fond} text-white`}
      >
        {ressource.couverture ? (
          <img
            src={ressource.couverture}
            alt=""
            loading="lazy"
            className="absolute inset-0 size-full object-cover object-top transition duration-300 group-hover:scale-105"
          />
        ) : (
          <>
            <span aria-hidden className="absolute inset-y-0 left-5 -z-10 w-3 bg-black/15" />
            <span
              aria-hidden
              className="absolute -bottom-10 -right-10 -z-10 size-40 rounded-full bg-white/10"
            />
            <Icone aria-hidden className="size-16 transition duration-300 group-hover:scale-110" />
          </>
        )}
        <span className="absolute right-4 top-4 rounded-full bg-black/35 px-3 py-1 text-xs font-extrabold backdrop-blur">
          {tailleLisible(ressource.fichier_octets)}
        </span>
      </div>
      <div className="flex flex-1 flex-col p-6">
        <p className="flex flex-wrap items-center gap-2 text-xs font-extrabold uppercase tracking-wider text-logo-red">
          {categorie.un}
          {ressource.parution && (
            <span className="normal-case tracking-normal text-muted-foreground">
              · {ressource.parution}
            </span>
          )}
          {ressource.contenu_de_test && (
            <span className="rounded-full bg-sun/30 px-2 py-0.5 normal-case tracking-normal text-ink">
              Contenu de test
            </span>
          )}
        </p>
        <h3 className="mt-2 font-sans text-lg font-extrabold leading-snug">{ressource.titre}</h3>
        {ressource.description && (
          <p className="mt-2 line-clamp-3 text-sm text-muted-foreground">{ressource.description}</p>
        )}
        <p className="mt-3 flex items-start gap-1.5 text-xs font-semibold text-ink/70">
          <BadgeCheck aria-hidden className="mt-px size-4 shrink-0 text-primary" />
          <span>
            Validé par {ressource.validateur_nom} ({ressource.validateur_qualite})
          </span>
        </p>
        <p className="mt-1 text-xs text-muted-foreground">
          {dateCourte(ressource.publie_le)}
          {ressource.pages
            ? ` · ${ressource.pages} page${ressource.pages > 1 ? "s" : ""}`
            : ""} · {telechargements(ressource.telechargements)}
        </p>
        <div className="mt-auto flex flex-wrap gap-2 pt-5">
          <a
            href={urlRessource(ressource.id)}
            target="_blank"
            rel="noopener"
            aria-label={`Lire : ${ressource.titre} (s'ouvre dans un nouvel onglet)`}
            className="inline-flex h-11 items-center gap-2 rounded-full px-4 text-sm font-bold text-logo-blue ring-1 ring-border transition hover:bg-mist"
          >
            <BookOpenText className="size-4" /> Lire
          </a>
          <a
            href={urlRessource(ressource.id, true)}
            download
            aria-label={`Télécharger : ${ressource.titre}`}
            className="btn-fx inline-flex h-11 items-center gap-2 rounded-full bg-primary px-4 text-sm font-bold text-primary-foreground"
          >
            <Download className="size-4" /> Télécharger
          </a>
        </div>
      </div>
    </li>
  );
}
