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

export const Route = createFileRoute("/genie-imhotep/hall-of-fame/")({
  head: () => ({
    meta: [
      { title: "Hall of Fame — Génie Imhotep" },
      {
        name: "description",
        content:
          "Le Hall of Fame du Championnat national Génie Imhotep : toutes les éditions, leurs champions, leurs finales et la prochaine saison.",
      },
      { property: "og:title", content: "Hall of Fame du Génie Imhotep" },
    ],
  }),
  component: HallOfFame,
});

const jouees = editions.filter((e) => e.statut === "terminee").length;
const prochaine = editions.find((e) => e.statut === "a-venir");

const reperes = [
  { n: String(jouees), t: jouees > 1 ? "éditions jouées" : "édition jouée" },
  { n: "7", t: "régions en compétition" },
  ...(prochaine ? [{ n: libelleSaison(prochaine.id), t: "prochaine saison" }] : []),
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
            <FilAriane rubrique="Génie Imhotep" page="Hall of Fame" clair />
            <div data-reveal="left" className="pt-10 lg:pt-16">
              <p className="inline-flex items-center gap-2 rounded-full bg-sun px-4 py-1.5 text-xs font-extrabold uppercase tracking-wide text-ink">
                <Trophy className="size-4" /> Génie Imhotep · Hall of Fame
              </p>
              <h1 className="mt-5 text-5xl leading-[0.95] md:text-7xl">
                <span className="block">Le temple</span>
                <span className="block text-sun">des champions</span>
              </h1>
              <p className="mt-6 max-w-xl text-lg font-medium text-white/85">
                Ici entrent les collèges et lycées qui ont marqué le Championnat national Génie
                Imhotep. Saison après saison, revis leurs parcours, leurs finales et leurs exploits,
                de la préfecture jusqu’à la grande finale.
              </p>
              <ul className="mt-8 flex flex-wrap gap-x-8 gap-y-4">
                {reperes.map((r) => (
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
                  Voir les éditions <ArrowDown className="size-4" />
                </a>
                <a
                  href="/genie-imhotep/palmares"
                  className="btn-fx inline-flex items-center gap-2 rounded-full border-2 border-white px-7 py-3 text-[15px] font-bold text-white hover:bg-white hover:text-ink"
                >
                  <Medal className="size-4" /> Le palmarès
                </a>
              </div>
            </div>
          </div>

          <div data-reveal="zoom" className="relative mx-auto self-end">
            <img
              src={mascottesVs}
              alt="Deux mascottes des Clubs Santé face à face, au-dessus d’un grand « VS » doré"
              width={2000}
              height={2000}
              className="w-72 drop-shadow-2xl sm:w-96 lg:w-[30rem]"
            />
            <p className="absolute left-0 top-10 -rotate-6 rounded-2xl bg-white px-4 py-2 font-hand text-2xl text-ink shadow-card motion-safe:animate-float">
              Qui sera le prochain ?
            </p>
          </div>
        </div>
      </section>

      <SectionEditions base="hall-of-fame" sur="Saison après saison">
        Choisis une édition pour revivre ses matchs, ses finales et le parcours de son champion, ou
        découvre la prochaine saison.
      </SectionEditions>

      <section className="mx-auto max-w-7xl px-5 pb-20">
        <div
          data-reveal="zoom"
          className="flex flex-col items-start justify-between gap-6 rounded-3xl bg-sun p-8 md:flex-row md:items-center md:p-12"
        >
          <div>
            <h2 className="text-3xl text-ink md:text-4xl">
              Et si ton lycée entrait au <span className="text-logo-blue">Hall of Fame</span> ?
            </h2>
            <p className="mt-2 max-w-2xl font-semibold text-ink/75">
              Les inscriptions au Championnat national passent par ton chef d’établissement ou les
              encadreurs de ton Club Santé.
            </p>
          </div>
          <a
            href="/genie-imhotep/inscription"
            className="btn-fx inline-flex shrink-0 items-center gap-2 rounded-full bg-primary px-7 py-3 text-[15px] font-bold text-primary-foreground"
          >
            S’inscrire au championnat <ArrowRight className="size-4" />
          </a>
        </div>
      </section>

      <SiteFooter />
    </div>
  );
}
