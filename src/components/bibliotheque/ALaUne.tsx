import { BookOpenText, Download, Newspaper } from "lucide-react";

import { EnTete } from "@/components/EnTete";
import { urlRessource, type RessourcePublique } from "@/lib/api/client";
import { dateCourte } from "@/lib/dates";

// « À la Une » (CDC § 4.6) : les 3 derniers magazines publiés, leur couverture en grand. Une rangée qui défile
// au doigt ou au clavier sur un petit écran, jamais d'elle-même.
export function ALaUne({ magazines }: { magazines: RessourcePublique[] }) {
  if (magazines.length === 0) return null;
  return (
    <section aria-label="À la Une" className="mx-auto max-w-7xl px-5 pt-20">
      <EnTete sur="À la Une" bleu="Les derniers" vert="magazines">
        Les magazines SOS Docteur TV, à lire en ligne ou à télécharger.
      </EnTete>
      {/* Pas d'arrêt de tabulation sur la rangée : chaque carte a déjà ses liens, qui la font défiler au clavier. */}
      <ul
        aria-label="Derniers magazines"
        className="-mx-5 mt-10 flex snap-x snap-mandatory gap-6 overflow-x-auto px-5 pb-4 lg:grid lg:grid-cols-3 lg:overflow-visible"
      >
        {magazines.map((m) => (
          <li
            key={m.id}
            data-reveal
            className="card-fx relative isolate flex w-[80%] shrink-0 snap-start flex-col overflow-hidden rounded-[2rem] bg-night text-white shadow-card sm:w-[45%] lg:w-auto"
          >
            <div className="relative aspect-[3/4] overflow-hidden bg-grape">
              {m.couverture ? (
                <img
                  src={m.couverture}
                  alt={`Couverture : ${m.titre}`}
                  loading="lazy"
                  className="size-full object-cover"
                />
              ) : (
                <Newspaper aria-hidden className="absolute inset-0 m-auto size-20 opacity-80" />
              )}
              <div
                aria-hidden
                className="absolute inset-x-0 bottom-0 h-1/2 bg-linear-to-t from-night to-transparent"
              />
            </div>
            <div className="relative -mt-24 flex flex-1 flex-col p-6">
              <p className="text-xs font-extrabold uppercase tracking-widest text-sun">
                {m.parution ?? dateCourte(m.publie_le)}
                {m.contenu_de_test && " · Contenu de test"}
              </p>
              <h3 className="mt-2 font-sans text-xl font-extrabold leading-snug">{m.titre}</h3>
              <div className="mt-auto flex flex-wrap gap-2 pt-5">
                <a
                  href={urlRessource(m.id)}
                  target="_blank"
                  rel="noopener"
                  aria-label={`Lire : ${m.titre} (s'ouvre dans un nouvel onglet)`}
                  className="inline-flex h-11 items-center gap-2 rounded-full bg-white/15 px-4 text-sm font-bold backdrop-blur transition hover:bg-white/25"
                >
                  <BookOpenText className="size-4" /> Lire
                </a>
                <a
                  href={urlRessource(m.id, true)}
                  download
                  aria-label={`Télécharger : ${m.titre}`}
                  className="btn-fx inline-flex h-11 items-center gap-2 rounded-full bg-primary px-4 text-sm font-bold text-primary-foreground"
                >
                  <Download className="size-4" /> Télécharger
                </a>
              </div>
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}
