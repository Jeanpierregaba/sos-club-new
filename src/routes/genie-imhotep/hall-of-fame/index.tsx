import { createFileRoute } from "@tanstack/react-router";
import { ArrowDown, ArrowRight, Medal, Trophy } from "lucide-react";
import { DecorAnime } from "@/components/DecorAnime";
import { FilAriane } from "@/components/FilAriane";
import { SectionEditions } from "@/components/SectionEditions";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";
import { SiteMotion } from "@/components/SiteMotion";
import { editions, libelleSaison } from "@/lib/genie-imhotep-editions";
import mascottesVs from "@/assets/mascottes-vs.webp";
import { auSingulier, lien } from "@/lib/langues";
import { m } from "@/paraglide/messages.js";

export const Route = createFileRoute("/genie-imhotep/hall-of-fame/")({
  head: () => ({
    meta: [
      { title: m.ghof_meta_titre() },
      { name: "description", content: m.ghof_meta_description() },
      { property: "og:title", content: m.ghof_meta_og() },
    ],
  }),
  component: HallOfFame,
});

const jouees = editions.filter((e) => e.statut === "terminee").length;
const prochaine = editions.find((e) => e.statut === "a-venir");

const reperes = () => [
  { n: String(jouees), t: auSingulier(jouees) ? m.ghof_une_jouee() : m.ghof_n_jouees() },
  { n: "7", t: m.ghof_regions() },
  ...(prochaine ? [{ n: libelleSaison(prochaine.id), t: m.ghof_prochaine() }] : []),
];

// L'accueil du Hall of Fame : il présente le Hall of Fame, sans s'arrêter sur une édition ; chaque
// édition a sa page, ouverte depuis la section « Les éditions ».
function HallOfFame() {
  return (
    <div className="min-h-screen overflow-x-clip bg-carnet text-ink">
      <SiteMotion />
      <SiteHeader />

      {/* Bannière claire : le titre à gauche, les mascottes en duel sur des rayons dorés à droite. */}
      <section className="relative isolate overflow-hidden bg-linear-to-br from-sky via-[oklch(0.52_0.17_252)] to-logo-blue text-white">
        <div
          aria-hidden
          className="absolute left-1/2 top-[88%] -z-10 size-[56rem] -translate-x-1/2 -translate-y-1/2 bg-[repeating-conic-gradient(rgb(255_220_100/0.16)_0deg_6deg,transparent_6deg_18deg)] [mask-image:radial-gradient(circle,black_20%,transparent_65%)] motion-safe:animate-[spin_120s_linear_infinite] lg:left-[74%] lg:top-[60%] lg:size-[68rem]"
        />
        <div
          aria-hidden
          className="absolute left-1/2 top-[90%] -z-10 size-96 -translate-x-1/2 -translate-y-1/2 rounded-full bg-sun/40 blur-3xl lg:left-[74%] lg:top-[64%]"
        />
        <DecorAnime />

        <div className="mx-auto grid max-w-7xl items-center gap-8 px-5 pt-8 md:pt-12 lg:grid-cols-[1.15fr_1fr]">
          <div className="pb-14 lg:pb-24">
            <FilAriane rubrique={m.menu_genie_imhotep()} page={m.menu_hall_of_fame()} clair />
            <div data-reveal="left" className="pt-10 lg:pt-16">
              <p className="inline-flex items-center gap-2 rounded-full bg-sun px-4 py-1.5 text-xs font-extrabold uppercase tracking-wide text-ink">
                <Trophy className="size-4" /> {m.ghof_badge()}
              </p>
              <h1 className="mt-5 text-5xl leading-[0.95] md:text-7xl">
                <span className="block">{m.ghof_titre_1()}</span>
                <span className="block text-sun">{m.ghof_titre_2()}</span>
              </h1>
              <p className="mt-6 max-w-xl text-lg font-medium text-white/85">{m.ghof_intro()}</p>
              <ul className="mt-8 flex flex-wrap gap-x-8 gap-y-4">
                {reperes().map((r) => (
                  <li key={r.t} className="flex items-center gap-3">
                    <span className="font-display text-4xl leading-none tabular-nums text-sun">
                      {r.n}
                    </span>
                    <span className="max-w-[7rem] text-sm font-bold leading-tight text-white/80">
                      {r.t}
                    </span>
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
                  href={lien("/genie-imhotep/palmares")}
                  className="btn-fx inline-flex items-center gap-2 rounded-full border-2 border-white px-7 py-3 text-[15px] font-bold text-white hover:bg-white hover:text-ink"
                >
                  <Medal className="size-4" /> {m.ghof_le_palmares()}
                </a>
              </div>
            </div>
          </div>

          <div data-reveal="zoom" className="relative mx-auto self-end">
            <img
              src={mascottesVs}
              alt={m.gi_mascottes_alt()}
              width={2000}
              height={2000}
              className="w-72 drop-shadow-2xl sm:w-96 lg:w-[30rem]"
            />
            <p className="absolute left-0 top-10 -rotate-6 rounded-2xl bg-white px-4 py-2 font-hand text-2xl text-ink shadow-card motion-safe:animate-float">
              {m.ghof_prochain()}
            </p>
          </div>
        </div>
      </section>

      <SectionEditions base="hall-of-fame" sur={m.ghof_editions_sur()}>
        {m.ghof_editions_texte()}
      </SectionEditions>

      <section className="mx-auto max-w-7xl px-5 pb-20">
        <div
          data-reveal="zoom"
          className="flex flex-col items-start justify-between gap-6 rounded-3xl bg-sun p-8 md:flex-row md:items-center md:p-12"
        >
          <div>
            <h2 className="text-3xl text-ink md:text-4xl">
              {m.ghof_et_si_1()} <span className="text-logo-blue">{m.ghof_et_si_2()}</span>
              {m.ghof_et_si_3()}
            </h2>
            <p className="mt-2 max-w-2xl font-semibold text-ink/75">{m.ghof_inscriptions()}</p>
          </div>
          <a
            href={lien("/genie-imhotep/inscription")}
            className="btn-fx inline-flex shrink-0 items-center gap-2 rounded-full bg-primary px-7 py-3 text-[15px] font-bold text-primary-foreground"
          >
            {m.ghof_sinscrire()} <ArrowRight className="size-4" />
          </a>
        </div>
      </section>

      <SiteFooter />
    </div>
  );
}
