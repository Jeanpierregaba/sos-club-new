import { createFileRoute } from "@tanstack/react-router";
import { Quote } from "lucide-react";

import { EnTete } from "@/components/EnTete";
import { FilAriane } from "@/components/FilAriane";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";
import { ContenuEnFrancais } from "@/components/ContenuEnFrancais";
import { temoignages } from "@/lib/temoignages";
import { m } from "@/paraglide/messages.js";

export const Route = createFileRoute("/temoignages")({
  head: () => ({
    meta: [
      { title: m.temoignages_meta_titre() },
      { name: "description", content: m.temoignages_meta_description() },
    ],
  }),
  component: Temoignages,
});

// La page des témoignages en entier : on y arrive par « Lire la suite » depuis la section de l'accueil, chaque
// témoignage ayant son ancre. Elle n'est pas dans le menu.
function Temoignages() {
  return (
    <>
      <SiteHeader />
      <main className="bg-carnet">
        <div className="mx-auto max-w-4xl px-4 py-12 sm:px-6 md:py-16">
          <FilAriane rubrique={m.temoignages_rubrique()} page={m.temoignages_bloc_etiquette()} />
          <div className="mt-6">
            <EnTete
              sur={m.temoignages_bloc_etiquette()}
              bleu={m.temoignages_bloc_titre_1()}
              vert={m.temoignages_bloc_titre_2()}
            >
              {m.temoignages_bloc_texte()}
            </EnTete>
            <ContenuEnFrancais className="mt-3" />
          </div>
          <ol className="mt-10 grid gap-6">
            {temoignages.map((x) => (
              <li
                key={x.id}
                id={x.id}
                className="relative isolate scroll-mt-24 overflow-hidden rounded-[2rem] bg-white p-6 shadow-card ring-1 ring-border md:p-10"
              >
                <Quote
                  aria-hidden
                  className="absolute right-5 top-5 -z-10 size-20 fill-current text-mist"
                />
                <figure>
                  <blockquote>
                    <p className="font-display text-2xl leading-tight text-logo-blue md:text-3xl">
                      {x.t}
                    </p>
                    {x.suite && (
                      <div className="mt-5 space-y-3 text-base leading-relaxed text-foreground/80">
                        {x.suite.map((paragraphe) => (
                          <p key={paragraphe}>{paragraphe}</p>
                        ))}
                      </div>
                    )}
                  </blockquote>
                  <figcaption className="mt-6 border-t pt-4">
                    <span className="block text-lg font-extrabold">{x.nom}</span>
                    <span className="block text-sm font-medium text-muted-foreground">
                      {x.role}
                    </span>
                  </figcaption>
                </figure>
              </li>
            ))}
          </ol>
        </div>
      </main>
      <SiteFooter />
    </>
  );
}
