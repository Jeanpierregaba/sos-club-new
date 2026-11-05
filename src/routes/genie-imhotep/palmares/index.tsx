import { createFileRoute } from "@tanstack/react-router";
import { ArrowDown, ArrowRight, Sparkles, Trophy } from "lucide-react";
import { DecorAnime } from "@/components/DecorAnime";
import { FilAriane } from "@/components/FilAriane";
import { SectionEditions } from "@/components/SectionEditions";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";
import { SiteMotion } from "@/components/SiteMotion";
import mascottesTrophees from "@/assets/mascottes-trophees.webp";

export const Route = createFileRoute("/genie-imhotep/palmares/")({
  head: () => ({
    meta: [
      { title: "Palmarès — Génie Imhotep" },
      {
        name: "description",
        content:
          "Le palmarès du Championnat national Génie Imhotep, édition par édition : les établissements sur le podium, les champions régionaux et les joueurs primés.",
      },
      { property: "og:title", content: "Le palmarès du Génie Imhotep" },
    ],
  }),
  component: Palmares,
});

const distinctions = [
  { t: "Podium national", d: "Champion, finaliste et demi-finalistes" },
  { t: "Joueurs primés", d: "Par pseudonyme et établissement" },
  { t: "Champions régionaux", d: "Un par DRE" },
];

// L'accueil du Palmarès : il présente les distinctions du championnat, sans s'arrêter sur une
// édition ; chaque édition a sa page, ouverte depuis la section « Les éditions ».
function Palmares() {
  return (
    <div className="min-h-screen overflow-x-clip bg-carnet text-ink">
      <SiteMotion />
      <SiteHeader />

      {/* Bannière claire : le titre à gauche, les mascottes et leurs trophées sur des rayons dorés. */}
      <section className="relative isolate overflow-hidden bg-linear-to-br from-[oklch(0.66_0.21_30)] via-logo-red to-[oklch(0.47_0.19_25)] text-white">
        <div
          aria-hidden
          className="absolute left-1/2 top-full -z-10 size-[60rem] -translate-x-1/2 -translate-y-1/2 bg-[repeating-conic-gradient(rgb(255_220_100/0.16)_0deg_6deg,transparent_6deg_18deg)] [mask-image:radial-gradient(circle,black_20%,transparent_65%)] motion-safe:animate-[spin_120s_linear_infinite] lg:left-[75%] lg:top-[70%]"
        />
        <DecorAnime />

        <div className="mx-auto grid max-w-7xl items-end gap-8 px-5 pt-8 md:pt-12 lg:grid-cols-[1.2fr_1fr]">
          <div className="pb-14 lg:pb-24">
            <FilAriane rubrique="Génie Imhotep" page="Palmarès" clair />
            <div data-reveal="left" className="pt-10 lg:pt-16">
              <p className="inline-flex items-center gap-2 rounded-full bg-sun px-4 py-1.5 text-xs font-extrabold uppercase tracking-wide text-ink">
                <Sparkles className="size-4" /> Génie Imhotep · Palmarès
              </p>
              <h1 className="mt-5 text-5xl leading-[0.95] md:text-7xl">
                <span className="block">Le palmarès</span>
                <span className="block text-sun">des lauréats</span>
              </h1>
              <p className="mt-6 max-w-xl text-lg font-medium text-white/85">
                Ils ont buzzé plus vite, répondu plus juste et porté haut les couleurs de leur
                établissement : honneur aux lauréats du Championnat national Génie Imhotep, édition
                après édition.
              </p>
              <ul className="mt-8 grid max-w-xl gap-3 sm:grid-cols-3">
                {distinctions.map((d) => (
                  <li key={d.t} className="rounded-2xl bg-white p-4 shadow-card">
                    <Trophy aria-hidden className="size-5 text-tangerine" />
                    <p className="mt-2 font-display text-lg leading-tight text-logo-blue">{d.t}</p>
                    <p className="mt-1 text-xs font-bold text-muted-foreground">{d.d}</p>
                  </li>
                ))}
              </ul>
              <div className="mt-9 flex flex-wrap gap-3">
                <a
                  href="#editions"
                  className="btn-fx inline-flex items-center gap-2 rounded-full bg-primary px-7 py-3 text-[15px] font-bold text-primary-foreground shadow-card"
                >
                  Voir les éditions <ArrowDown className="size-4" />
                </a>
                <a
                  href="/genie-imhotep/hall-of-fame"
                  className="btn-fx inline-flex items-center gap-2 rounded-full border-2 border-white px-7 py-3 text-[15px] font-bold text-white hover:bg-white hover:text-ink"
                >
                  Le Hall of Fame <ArrowRight className="size-4" />
                </a>
              </div>
            </div>
          </div>
          <img
            src={mascottesTrophees}
            alt="Des mascottes des Clubs Santé brandissent leurs trophées"
            width={1122}
            height={1402}
            data-reveal="zoom"
            className="mx-auto w-64 drop-shadow-2xl sm:w-80 lg:w-[26rem]"
          />
        </div>
      </section>

      <SectionEditions base="palmares" sur="Édition par édition">
        Choisis une édition pour découvrir son podium, ses joueurs primés et ses champions
        régionaux.
      </SectionEditions>

      <SiteFooter />
    </div>
  );
}
