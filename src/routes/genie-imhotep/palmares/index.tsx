import { createFileRoute } from "@tanstack/react-router";
import { ArrowDown, ArrowRight, Sparkles, Trophy } from "lucide-react";
import { DecorAnime } from "@/components/DecorAnime";
import { FilAriane } from "@/components/FilAriane";
import { SectionEditions } from "@/components/SectionEditions";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";
import { SiteMotion } from "@/components/SiteMotion";
import mascottesTrophees from "@/assets/mascottes-trophees.webp";
import { lien } from "@/lib/langues";
import { m } from "@/paraglide/messages.js";

export const Route = createFileRoute("/genie-imhotep/palmares/")({
  head: () => ({
    meta: [
      { title: m.gpal_meta_titre() },
      { name: "description", content: m.gpal_meta_description() },
      { property: "og:title", content: m.gpal_meta_og() },
    ],
  }),
  component: Palmares,
});

const distinctions = () => [
  { t: m.gpal_dist_podium(), d: m.gpal_dist_podium_d() },
  { t: m.gpal_dist_joueurs(), d: m.gpal_dist_joueurs_d() },
  { t: m.gpal_dist_regionaux(), d: m.gpal_dist_regionaux_d() },
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
            <FilAriane rubrique={m.menu_genie_imhotep()} page={m.menu_palmares()} clair />
            <div data-reveal="left" className="pt-10 lg:pt-16">
              <p className="inline-flex items-center gap-2 rounded-full bg-sun px-4 py-1.5 text-xs font-extrabold uppercase tracking-wide text-ink">
                <Sparkles className="size-4" /> {m.gpal_badge()}
              </p>
              <h1 className="mt-5 text-5xl leading-[0.95] md:text-7xl">
                <span className="block">{m.gpal_titre_1()}</span>
                <span className="block text-sun">{m.gpal_titre_2()}</span>
              </h1>
              <p className="mt-6 max-w-xl text-lg font-medium text-white/85">{m.gpal_intro()}</p>
              <ul className="mt-8 grid max-w-xl gap-3 sm:grid-cols-3">
                {distinctions().map((d) => (
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
                  {m.gpal_voir_editions()} <ArrowDown className="size-4" />
                </a>
                <a
                  href={lien("/genie-imhotep/hall-of-fame")}
                  className="btn-fx inline-flex items-center gap-2 rounded-full border-2 border-white px-7 py-3 text-[15px] font-bold text-white hover:bg-white hover:text-ink"
                >
                  {m.gpal_le_hof()} <ArrowRight className="size-4" />
                </a>
              </div>
            </div>
          </div>
          <img
            src={mascottesTrophees}
            alt={m.gpal_mascottes_alt()}
            width={1122}
            height={1402}
            data-reveal="zoom"
            className="mx-auto w-64 drop-shadow-2xl sm:w-80 lg:w-[26rem]"
          />
        </div>
      </section>

      <SectionEditions base="palmares" sur={m.gpal_editions_sur()}>
        {m.gpal_editions_texte()}
      </SectionEditions>

      <SiteFooter />
    </div>
  );
}
