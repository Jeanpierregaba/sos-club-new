import { BookOpenText, Download, Newspaper } from "lucide-react";

import { EnTete } from "@/components/EnTete";
import { urlRessource, type RessourcePublique } from "@/lib/api/client";
import { dateCourte } from "@/lib/dates";
import { m } from "@/paraglide/messages.js";

// « À la Une » (CDC § 4.6) : les 3 derniers magazines publiés, leur couverture en grand. Une rangée qui défile
// au doigt ou au clavier sur un petit écran, jamais d'elle-même.
export function ALaUne({ magazines }: { magazines: RessourcePublique[] }) {
  if (magazines.length === 0) return null;
  return (
    <section aria-label={m.biblio_a_la_une()} className="mx-auto max-w-7xl px-5 pt-20">
      <EnTete sur={m.biblio_a_la_une()} bleu={m.biblio_une_bleu()} vert={m.biblio_une_vert()}>
        {m.biblio_une_texte()}
      </EnTete>
      {/* Pas d'arrêt de tabulation sur la rangée : chaque carte a déjà ses liens, qui la font défiler au clavier. */}
      <ul
        aria-label={m.biblio_derniers_magazines()}
        className="-mx-5 mt-10 flex snap-x snap-mandatory gap-6 overflow-x-auto px-5 pb-4 lg:grid lg:grid-cols-3 lg:overflow-visible"
      >
        {magazines.map((mag) => (
          <li
            key={mag.id}
            data-reveal
            className="card-fx relative isolate flex w-[80%] shrink-0 snap-start flex-col overflow-hidden rounded-[2rem] bg-night text-white shadow-card sm:w-[45%] lg:w-auto"
          >
            <div className="relative aspect-[3/4] overflow-hidden bg-grape">
              {mag.couverture ? (
                <img
                  src={mag.couverture}
                  alt={m.biblio_couverture({ titre: mag.titre })}
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
                {mag.parution ?? dateCourte(mag.publie_le)}
                {mag.contenu_de_test && ` · ${m.biblio_contenu_test()}`}
              </p>
              <h3 className="mt-2 font-sans text-xl font-extrabold leading-snug">{mag.titre}</h3>
              <div className="mt-auto flex flex-wrap gap-2 pt-5">
                <a
                  href={urlRessource(mag.id)}
                  target="_blank"
                  rel="noopener"
                  aria-label={m.biblio_lire_aria({ titre: mag.titre })}
                  className="inline-flex h-11 items-center gap-2 rounded-full bg-white/15 px-4 text-sm font-bold backdrop-blur transition hover:bg-white/25"
                >
                  <BookOpenText className="size-4" /> {m.biblio_lire()}
                </a>
                <a
                  href={urlRessource(mag.id, true)}
                  download
                  aria-label={m.biblio_telecharger_aria({ titre: mag.titre })}
                  className="btn-fx inline-flex h-11 items-center gap-2 rounded-full bg-primary px-4 text-sm font-bold text-primary-foreground"
                >
                  <Download className="size-4" /> {m.biblio_telecharger()}
                </a>
              </div>
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}
