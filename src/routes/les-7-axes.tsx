import type { CSSProperties } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { texteAxe } from "@/lib/axes";
import { lien } from "@/lib/langues";
import { m } from "@/paraglide/messages.js";
import {
  ArrowDown,
  ArrowRight,
  Award,
  Brain,
  CirclePlay,
  Clapperboard,
  Compass,
  Download,
  Dumbbell,
  ListChecks,
  MessageCircleHeart,
  Sprout,
} from "lucide-react";
import { FilAriane } from "@/components/FilAriane";
import { SiteHeader } from "@/components/SiteHeader";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteMotion, retard } from "@/components/SiteMotion";
import { DecorAnime } from "@/components/DecorAnime";
import mascottesAxes from "@/assets/mascottes-axes.webp";
import slideAxes from "@/assets/slide-axes.jpg";
import mascotteImhotep from "@/assets/mascotte-imhotep.webp";
import mascotteValeurs from "@/assets/mascotte-valeurs.webp";
import mascotteMedias from "@/assets/mascotte-medias.webp";
import mascotteSecourisme from "@/assets/mascotte-secourisme.webp";
import mascotteBourses from "@/assets/mascotte-bourses.webp";
import mascotteLeadership from "@/assets/mascotte-leadership.webp";
import mascotteEnvironnement from "@/assets/mascotte-environnement.webp";

export const Route = createFileRoute("/les-7-axes")({
  head: () => ({
    meta: [
      { title: m.axes7_meta_titre() },
      { name: "description", content: m.axes7_meta_description() },
      { property: "og:title", content: m.axes7_meta_og() },
    ],
  }),
  component: LesSeptAxes,
});

// `couleur` : la couleur de l'axe, posée en variable CSS sur sa section ; `encre` : le texte posé sur cette couleur.
// Une fonction : les textes suivent la langue de la page.
const lesAxes = () => [
  {
    t: texteAxe(1).titre,
    s: texteAxe(1).slogan,
    activites: [m.axe_1_activite_1(), m.axe_1_activite_2(), m.axe_1_activite_3()],
    i: Brain,
    img: mascotteImhotep,
    couleur: "var(--sky)",
    encre: "text-white",
  },
  {
    t: texteAxe(2).titre,
    s: m.axe_2_slogan_evss(),
    activites: [m.axe_2_activite_1(), m.axe_2_activite_2(), m.axe_2_activite_3()],
    i: MessageCircleHeart,
    img: mascotteValeurs,
    couleur: "var(--rose)",
    encre: "text-white",
  },
  {
    t: texteAxe(3).titre,
    s: texteAxe(3).slogan,
    activites: [m.axe_3_activite_1(), m.axe_3_activite_2(), m.axe_3_activite_3()],
    i: Clapperboard,
    img: mascotteMedias,
    couleur: "var(--grape)",
    encre: "text-white",
  },
  {
    t: texteAxe(4).titre,
    s: texteAxe(4).slogan,
    activites: [m.axe_4_activite_1(), m.axe_4_activite_2(), m.axe_4_activite_3()],
    i: Dumbbell,
    img: mascotteSecourisme,
    couleur: "var(--tangerine)",
    encre: "text-white",
  },
  {
    t: texteAxe(5).titre,
    s: texteAxe(5).slogan,
    activites: [m.axe_5_activite_1(), m.axe_5_activite_2(), m.axe_5_activite_3()],
    i: Award,
    img: mascotteBourses,
    couleur: "var(--sun)",
    encre: "text-ink",
  },
  {
    t: texteAxe(6).titre,
    s: texteAxe(6).slogan,
    activites: [m.axe_6_activite_1(), m.axe_6_activite_2(), m.axe_6_activite_3()],
    i: Compass,
    img: mascotteLeadership,
    couleur: "var(--bark)",
    encre: "text-white",
  },
  {
    t: texteAxe(7).titre,
    s: texteAxe(7).slogan,
    activites: [m.axe_7_activite_1(), m.axe_7_activite_2(), m.axe_7_activite_3()],
    i: Sprout,
    img: mascotteEnvironnement,
    couleur: "var(--leaf)",
    encre: "text-white",
  },
];

const reperes = () => [
  { n: "7", t: m.axes7_repere_axes() },
  { n: "21", t: m.axes7_repere_activites() },
  { n: "7", t: m.axes7_repere_mascottes() },
];

// Un axe : la mascotte sur un aplat de sa couleur avec le slogan en bulle, le texte et les activités en face.
// Les côtés alternent d'un axe à l'autre, et chaque bande prend une teinte claire de la couleur de l'axe.
function Axe({ a, n }: { a: ReturnType<typeof lesAxes>[number]; n: number }) {
  const inverse = n % 2 === 0;
  return (
    <section
      id={`axe-${n}`}
      style={{ "--axe": a.couleur } as CSSProperties}
      className="relative isolate scroll-mt-20 overflow-hidden bg-[color-mix(in_oklch,var(--axe)_11%,white)] py-16 md:py-24"
    >
      <div className="mx-auto grid max-w-7xl items-center gap-12 px-5 lg:grid-cols-[0.9fr_1.1fr] lg:gap-16">
        <div
          data-reveal={inverse ? "right" : "left"}
          className={`relative mx-auto w-full max-w-md pb-16 sm:pb-10 ${inverse ? "lg:order-last" : ""}`}
        >
          <span
            aria-hidden
            className={`absolute -top-6 font-display text-[9rem] leading-none text-transparent opacity-50 [-webkit-text-stroke:3px_var(--axe)] md:text-[12rem] ${inverse ? "right-0" : "left-0"}`}
          >
            {String(n).padStart(2, "0")}
          </span>
          <div
            aria-hidden
            className={`absolute inset-x-8 bottom-20 top-24 -z-10 rounded-[3rem] bg-(color:--axe) sm:bottom-14 ${inverse ? "-rotate-3" : "rotate-3"}`}
          />
          <img
            src={a.img}
            alt={m.axes7_mascotte_alt({ numero: String(n), titre: a.t })}
            loading="lazy"
            width={1414}
            height={2000}
            className="relative mx-auto h-80 w-auto drop-shadow-2xl md:h-[26rem]"
          />
          <p
            className={`absolute bottom-0 max-w-[18rem] rounded-2xl bg-white p-4 font-hand text-xl leading-tight sm:text-2xl text-ink shadow-card sm:max-w-xs ${inverse ? "left-0 rotate-2" : "right-0 -rotate-2"}`}
          >
            {m.commun_citation({ texte: a.s })}
          </p>
        </div>

        <div data-reveal>
          <div className="flex items-center gap-3">
            <span
              className={`inline-flex size-12 shrink-0 items-center justify-center rounded-2xl bg-(color:--axe) shadow-card ${a.encre}`}
            >
              <a.i className="size-6" />
            </span>
            <p className="text-sm font-extrabold uppercase tracking-widest text-logo-red">
              {m.axes7_axe_sur_7({ numero: String(n) })}
            </p>
          </div>
          <h2 className="mt-4 text-2xl leading-tight text-logo-blue md:text-3xl">{a.t}</h2>

          <p className="mt-8 flex items-center gap-2 text-sm font-extrabold uppercase tracking-widest text-logo-blue">
            <ListChecks aria-hidden className="size-4" /> {m.axes7_activites()}
          </p>
          <ol className="mt-4 grid gap-3">
            {a.activites.map((act, j) => (
              <li
                key={act}
                data-reveal
                style={retard(j + 1)}
                className="flex items-start gap-4 rounded-2xl bg-white p-4 shadow-sm ring-1 ring-[color-mix(in_oklch,var(--axe)_25%,transparent)] md:p-5"
              >
                <span
                  className={`inline-flex size-9 shrink-0 items-center justify-center rounded-full bg-(color:--axe) font-display text-lg ${a.encre}`}
                >
                  {j + 1}
                </span>
                <p className="font-semibold leading-snug">{act}</p>
              </li>
            ))}
          </ol>
        </div>
      </div>
    </section>
  );
}

function LesSeptAxes() {
  const axes = lesAxes();
  return (
    <div className="min-h-screen overflow-x-clip bg-carnet text-ink">
      <SiteMotion />
      <SiteHeader />

      {/* Bannière : le titre à gauche, les mascottes posées sur le bas à droite, puis le ruban des 7 couleurs. */}
      <section className="relative isolate overflow-hidden bg-linear-to-br from-logo-blue via-logo-blue to-night text-white">
        <div
          aria-hidden
          className="absolute inset-0 -z-10 bg-[radial-gradient(oklch(1_0_0/0.14)_1.5px,transparent_1.5px)] bg-size-[22px_22px] [mask-image:linear-gradient(to_right,black,transparent_70%)] motion-safe:animate-defile-motif"
        />
        <div
          aria-hidden
          className="absolute -right-40 top-10 -z-10 size-[40rem] rounded-full border-[3rem] border-white/5 motion-safe:animate-respire"
        />
        {/* Rayons dorés qui tournent et halo derrière les mascottes, comme sur le Hall of Fame. */}
        <div
          aria-hidden
          className="absolute left-1/2 top-[78%] -z-10 size-[50rem] -translate-x-1/2 -translate-y-1/2 bg-[repeating-conic-gradient(rgb(255_210_80/0.12)_0deg_6deg,transparent_6deg_18deg)] [mask-image:radial-gradient(circle,black_20%,transparent_65%)] motion-safe:animate-[spin_120s_linear_infinite] lg:left-[76%] lg:top-[62%] lg:size-[70rem]"
        />
        <div
          aria-hidden
          className="absolute left-1/2 top-[80%] -z-10 size-80 -translate-x-1/2 -translate-y-1/2 rounded-full bg-sun/30 blur-3xl lg:left-[76%] lg:top-[66%] lg:size-96"
        />
        <DecorAnime />
        <div className="mx-auto grid max-w-7xl gap-6 px-5 pt-8 md:pt-12 lg:grid-cols-[1.1fr_1fr] lg:gap-10">
          <div className="pb-4 lg:pb-20">
            <FilAriane rubrique={m.menu_vie_du_club()} page={m.menu_7_axes()} clair />

            <div data-reveal="left" className="pt-12 lg:pt-20">
              <span className="inline-flex rounded-full bg-sun px-4 py-1.5 text-xs font-extrabold uppercase tracking-wide text-ink">
                {m.axes7_cadre()}
              </span>
              <h1 className="mt-5 text-5xl leading-[0.95] md:text-7xl">
                <span className="block">{m.axes7_titre_1()}</span>
                <span className="block text-primary">{m.axes7_titre_2()}</span>
              </h1>
              <p className="mt-6 max-w-xl text-lg font-medium text-white/85">{m.axes7_intro()}</p>
              <ul className="mt-8 flex flex-wrap gap-x-8 gap-y-4">
                {reperes().map((r) => (
                  <li key={r.t} className="flex items-center gap-3">
                    <span className="font-display text-4xl leading-none text-sun">{r.n}</span>
                    <span className="max-w-[7rem] text-sm font-bold leading-tight text-white/80">
                      {r.t}
                    </span>
                  </li>
                ))}
              </ul>
              <a
                href="#axe-1"
                className="btn-fx mt-9 inline-flex items-center gap-2 rounded-full bg-primary px-7 py-3 text-[15px] font-bold text-primary-foreground shadow-card"
              >
                {m.axes7_explorer()} <ArrowDown className="size-4" />
              </a>
            </div>
          </div>

          <img
            src={mascottesAxes}
            alt={m.axes7_mascottes_alt()}
            width={1122}
            height={1402}
            data-reveal="right"
            className="mx-auto w-4/5 max-w-md self-end drop-shadow-2xl sm:w-3/5 lg:w-full lg:max-w-lg"
          />
        </div>
        <div aria-hidden className="flex h-2.5">
          {axes.map((a) => (
            <span key={a.t} className="flex-1" style={{ background: a.couleur }} />
          ))}
        </div>
      </section>

      {/* Pourquoi un caméléon : la mascotte change de couleur sous les yeux du lecteur, mais reste la même. */}
      <section className="relative isolate overflow-hidden bg-white py-20 md:py-28">
        <div className="mx-auto grid max-w-7xl items-center gap-12 px-5 lg:grid-cols-[0.9fr_1.1fr] lg:gap-16">
          <div data-reveal="left" className="relative mx-auto w-full max-w-sm">
            {/* Les 7 couleurs des axes, en anneau autour de la mascotte. */}
            <div
              aria-hidden
              className="absolute inset-x-0 top-1/2 -z-10 aspect-square -translate-y-1/2 rounded-full p-3 motion-safe:animate-[spin_30s_linear_infinite]"
              style={{
                background: `conic-gradient(${axes.map((a) => a.couleur).join(", ")}, ${axes[0]!.couleur})`,
              }}
            >
              <div className="size-full rounded-full bg-white" />
            </div>
            <div className="drop-shadow-2xl">
              <img
                src={mascotteImhotep}
                alt={m.axes7_cameleon_alt()}
                loading="lazy"
                width={1414}
                height={2000}
                className="relative mx-auto h-96 w-auto motion-safe:animate-cameleon md:h-[28rem]"
              />
            </div>
          </div>

          <div data-reveal>
            <p className="text-sm font-extrabold uppercase tracking-widest text-logo-red">
              {m.axes7_notre_mascotte()}
            </p>
            <h2 className="mt-3 text-4xl md:text-5xl">
              <span className="text-logo-blue">{m.axes7_pourquoi_1()}</span>{" "}
              <span className="text-primary">{m.axes7_pourquoi_2()}</span>
            </h2>
            <p className="mt-6 text-xl font-semibold leading-relaxed">{m.axes7_cameleon_1()}</p>
            <p className="mt-4 text-lg font-medium leading-relaxed text-muted-foreground">
              {m.axes7_cameleon_2()}
            </p>
            <div className="mt-8 rounded-3xl bg-mist-soft p-6 ring-1 ring-border md:p-8">
              <ul aria-hidden className="flex gap-1.5">
                {axes.map((a) => (
                  <li
                    key={a.t}
                    className="h-2 flex-1 rounded-full"
                    style={{ background: a.couleur }}
                  />
                ))}
              </ul>
              <p className="mt-5 font-display text-2xl leading-snug text-logo-blue md:text-3xl">
                {m.axes7_couleurs()}
              </p>
              <p className="mt-2 text-lg font-bold">{m.axes7_generation()}</p>
            </div>
          </div>
        </div>
      </section>

      {axes.map((a, i) => (
        <Axe key={a.t} a={a} n={i + 1} />
      ))}

      {/* Documentation officielle : la plaquette et le documentaire. Les liens restent à fournir. */}
      <section className="mx-auto max-w-7xl px-5 py-20">
        <div
          data-reveal="zoom"
          className="relative isolate grid overflow-hidden rounded-[2rem] bg-night text-white shadow-card lg:grid-cols-[1.2fr_1fr]"
        >
          <span
            aria-hidden
            className="absolute -left-16 -top-16 -z-10 size-64 rounded-full bg-primary/25 blur-3xl"
          />
          <div className="p-8 md:p-12">
            <p className="text-sm font-extrabold uppercase tracking-widest text-sun">
              SOS Docteur TV & AIMES-AFRIQUE
            </p>
            <h2 className="mt-3 text-4xl md:text-5xl">
              {m.axes7_doc_1()} <span className="text-primary">{m.axes7_doc_2()}</span>
            </h2>
            <p className="mt-4 max-w-xl text-lg font-medium text-white/80">{m.axes7_doc_texte()}</p>
            <div className="mt-8 flex flex-wrap gap-3">
              <a
                href="#"
                className="btn-fx inline-flex items-center gap-2 rounded-full bg-primary px-7 py-3 text-[15px] font-bold text-primary-foreground"
              >
                <Download className="size-4" /> {m.axes7_plaquette()}
              </a>
              <a
                href="#"
                className="btn-fx inline-flex items-center gap-2 rounded-full border-2 border-white px-7 py-3 text-[15px] font-bold hover:bg-white hover:text-logo-blue"
              >
                <CirclePlay className="size-4" /> {m.axes7_documentaire()}
              </a>
            </div>
          </div>
          <div className="relative min-h-64">
            <img
              src={slideAxes}
              alt={m.axes7_applaudir_alt()}
              loading="lazy"
              width={2000}
              height={1228}
              className="absolute inset-0 size-full object-cover [mask-image:linear-gradient(to_bottom,transparent,black_35%)] lg:[mask-image:linear-gradient(to_right,transparent,black_40%)]"
            />
            <a
              href={lien("/club-sante")}
              className="btn-fx absolute bottom-5 right-5 inline-flex items-center gap-2 rounded-full bg-white px-5 py-2.5 text-sm font-bold text-logo-blue shadow-card"
            >
              {m.axes7_decouvrir_club()} <ArrowRight className="size-4" />
            </a>
          </div>
        </div>
      </section>

      <SiteFooter />
    </div>
  );
}
