import { useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import {
  Accessibility,
  ArrowRight,
  Check,
  GraduationCap,
  HeartPulse,
  MapPinned,
  Users,
  CircleCheck,
  Eye,
  Gem,
  HeartHandshake,
  House,
  Laptop,
  Megaphone,
  MessageCircleQuestion,
  Quote,
  Rocket,
  School,
  Smartphone,
  Target,
  Trophy,
} from "lucide-react";
import { EnTete } from "@/components/EnTete";
import { SiteHeader } from "@/components/SiteHeader";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteMotion, retard } from "@/components/SiteMotion";
import banniere from "@/assets/club-sante-banniere.jpg";
import mascottesTrophees from "@/assets/mascottes-trophees.webp";
import mascotteImhotep from "@/assets/mascotte-imhotep.webp";
import kodom from "@/assets/initiateur-kodom.webp";
import { FilAriane } from "@/components/FilAriane";
import { lien } from "@/lib/langues";
import { m } from "@/paraglide/messages.js";

export const Route = createFileRoute("/club-sante")({
  head: () => ({
    meta: [
      { title: m.cs_meta_titre() },
      { name: "description", content: m.cs_meta_description() },
      { property: "og:title", content: m.cs_meta_og() },
    ],
  }),
  component: ClubSante,
});

// Les textes de la page sont des fonctions : ils suivent la langue de la page.
// Repères posés sous la bannière.
const reperesBanniere = () => [
  { i: MapPinned, n: "7", t: m.cs_repere_dre(), c: "bg-sky" },
  { i: HeartPulse, n: "+800", t: m.cs_repere_clubs(), c: "bg-primary" },
  { i: Users, n: "21", t: m.cs_repere_membres(), c: "bg-tangerine" },
  { i: GraduationCap, n: "3", t: m.cs_repere_enseignants(), c: "bg-grape" },
];

// Les sigles des ministères tiennent lieu de logos en attendant les fichiers officiels.
const ministeres = [
  { t: "MEPSTA / MEN", c: "border-logo-blue text-logo-blue", r: "-rotate-6" },
  { t: "MSHPAUS", c: "border-primary text-primary", r: "rotate-3" },
  { t: "MASPFA", c: "border-tangerine text-tangerine", r: "rotate-6" },
  { t: "MESR", c: "border-grape text-grape", r: "-rotate-3" },
];

const lots = () => [
  {
    i: Trophy,
    tag: m.cs_lot_1_etiquette(),
    t: m.cs_lot_1_titre(),
    d: m.cs_lot_1_texte(),
  },
  {
    i: Laptop,
    tag: m.cs_lot_2_etiquette(),
    t: m.cs_lot_2_titre(),
    d: m.cs_lot_2_texte(),
  },
  {
    i: Smartphone,
    tag: m.cs_lot_3_etiquette(),
    t: m.cs_lot_3_titre(),
    d: m.cs_lot_3_texte(),
  },
];

const objectifs = () => [
  {
    tag: m.cs_objectif_1_etiquette(),
    t: m.cs_objectif_1(),
    c: "bg-sky",
  },
  {
    tag: m.cs_objectif_2_etiquette(),
    t: m.cs_objectif_2(),
    c: "bg-tangerine",
  },
  {
    tag: m.cs_objectif_3_etiquette(),
    t: m.cs_objectif_3(),
    c: "bg-primary",
  },
  {
    tag: m.cs_objectif_4_etiquette(),
    t: m.cs_objectif_4(),
    c: "bg-grape",
  },
  {
    tag: m.cs_objectif_5_etiquette(),
    t: m.cs_objectif_5(),
    c: "bg-rose",
  },
];

const valeurs = () => [
  { t: m.cs_valeur_excellence(), c: "bg-logo-blue" },
  { t: m.cs_valeur_emulation(), c: "bg-primary" },
  { t: m.cs_valeur_engagement(), c: "bg-tangerine" },
  { t: m.cs_valeur_innovation(), c: "bg-grape" },
  { t: m.cs_valeur_leadership(), c: "bg-rose" },
];

const jalons = () => [
  {
    date: m.cs_jalon_1_date(),
    t: m.cs_jalon_1(),
    c: "bg-sky",
  },
  {
    date: m.cs_jalon_2_date(),
    t: m.cs_jalon_2(),
    c: "bg-primary",
  },
  {
    date: m.cs_jalon_3_date(),
    t: m.cs_jalon_3(),
    c: "bg-tangerine",
  },
];

const educations = () => [
  {
    i: School,
    tag: m.cs_education_1_etiquette(),
    t: m.cs_education_1_titre(),
    d: m.cs_education_1_texte(),
    coeur: false,
  },
  {
    i: HeartHandshake,
    tag: m.cs_education_2_etiquette(),
    t: m.cs_education_2_titre(),
    d: m.cs_education_2_texte(),
    coeur: true,
  },
  {
    i: House,
    tag: m.cs_education_3_etiquette(),
    t: m.cs_education_3_titre(),
    d: m.cs_education_3_texte(),
    coeur: false,
  },
];

const regles = () => [
  m.cs_regle_1(),
  m.cs_regle_2(),
  m.cs_regle_3(),
  m.cs_regle_4(),
  m.cs_regle_5(),
  m.cs_regle_6(),
];

const bureau = () => [
  m.cs_bureau_1(),
  m.cs_bureau_2(),
  m.cs_bureau_3(),
  m.cs_bureau_4(),
  m.cs_bureau_5(),
];

// Couleur de l'étiquette de chaque thème de la FAQ, et son nom dans la langue de la page.
const themes = {
  adhesion: "bg-sky",
  bureau: "bg-rose",
  fonctionnement: "bg-tangerine",
  championnat: "bg-grape",
} as const;

const NOMS_THEMES = {
  adhesion: m.cs_theme_adhesion,
  bureau: m.cs_theme_bureau,
  fonctionnement: m.cs_theme_fonctionnement,
  championnat: m.cs_theme_championnat,
};
const nomTheme = (theme: keyof typeof themes | null) =>
  theme ? NOMS_THEMES[theme]() : m.cs_theme_tout();

const questions = (): { theme: keyof typeof themes; q: string; r: string }[] => [
  {
    theme: "adhesion",
    q: m.cs_faq_1_q(),
    r: m.cs_faq_1_r(),
  },
  {
    theme: "bureau",
    q: m.cs_faq_2_q(),
    r: m.cs_faq_2_r(),
  },
  {
    theme: "bureau",
    q: m.cs_faq_3_q(),
    r: m.cs_faq_3_r(),
  },
  {
    theme: "adhesion",
    q: m.cs_faq_4_q(),
    r: m.cs_faq_4_r(),
  },
  {
    theme: "fonctionnement",
    q: m.cs_faq_5_q(),
    r: m.cs_faq_5_r(),
  },
  {
    theme: "fonctionnement",
    q: m.cs_faq_6_q(),
    r: m.cs_faq_6_r(),
  },
  {
    theme: "adhesion",
    q: m.cs_faq_7_q(),
    r: m.cs_faq_7_r(),
  },
  {
    theme: "championnat",
    q: m.cs_faq_8_q(),
    r: m.cs_faq_8_r(),
  },
];

// FAQ : les thèmes en filtre, les questions à gauche, la réponse dans une grande bulle à droite.
// Sur mobile, la réponse s'ouvre sous la question choisie.
function FaqSection() {
  const [theme, setTheme] = useState<keyof typeof themes | null>(null);
  const [ouverte, setOuverte] = useState(0);
  const faq = questions();
  const visibles = faq.map((f, i) => ({ ...f, i })).filter((f) => !theme || f.theme === theme);
  const active = faq[ouverte];
  const filtrer = (t: keyof typeof themes | null) => {
    setTheme(t);
    setOuverte(faq.findIndex((f) => !t || f.theme === t));
  };

  return (
    <section
      id="faq"
      className="relative isolate mt-20 scroll-mt-20 overflow-hidden bg-[color-mix(in_oklch,var(--sun)_16%,white)] py-20 md:py-24"
    >
      <MessageCircleQuestion
        aria-hidden
        className="absolute -left-16 top-10 -z-10 size-72 -rotate-12 text-sun/40"
      />
      <div className="mx-auto max-w-7xl px-5">
        <EnTete sur={m.cs_faq_sur()} bleu={m.cs_faq_bleu()} vert={m.cs_faq_vert()} centre>
          {m.cs_faq_texte()}
        </EnTete>

        <div data-reveal className="mt-8 flex flex-wrap justify-center gap-2">
          {([null, ...Object.keys(themes)] as (keyof typeof themes | null)[]).map((t) => (
            <button
              key={t ?? "tout"}
              type="button"
              aria-pressed={theme === t}
              onClick={() => filtrer(t)}
              className={`rounded-full px-5 py-2 text-sm font-extrabold transition duration-200 active:scale-95 ${
                theme === t
                  ? "bg-logo-blue text-white shadow-card"
                  : "bg-white text-logo-blue ring-1 ring-logo-blue/15 hover:ring-logo-blue/40"
              }`}
            >
              {nomTheme(t)}
            </button>
          ))}
        </div>

        <div className="mt-10 grid gap-8 lg:grid-cols-[1fr_1.15fr] lg:gap-10">
          <ul data-reveal="left" className="grid content-start gap-3">
            {visibles.map((f) => {
              const choisie = f.i === ouverte;
              return (
                <li key={f.q}>
                  <button
                    type="button"
                    aria-expanded={choisie}
                    aria-controls={`faq-${f.i}`}
                    onClick={() => setOuverte(f.i)}
                    className={`group flex w-full items-center gap-4 rounded-2xl p-4 text-left font-bold leading-snug transition duration-300 ${
                      choisie
                        ? "bg-logo-blue text-white shadow-card"
                        : "bg-white hover:-translate-y-0.5 hover:shadow-card"
                    }`}
                  >
                    <span
                      className={`inline-flex size-10 shrink-0 items-center justify-center rounded-xl font-display text-lg ${
                        choisie ? "bg-sun text-ink" : "bg-mist text-logo-blue"
                      }`}
                    >
                      {String(f.i + 1).padStart(2, "0")}
                    </span>
                    <span className="flex-1">{f.q}</span>
                    <ArrowRight
                      className={`size-5 shrink-0 transition duration-300 ${
                        choisie
                          ? "text-sun max-lg:-rotate-90"
                          : "text-logo-blue/40 group-hover:translate-x-1 max-lg:rotate-90"
                      }`}
                    />
                  </button>
                  {choisie && (
                    <p
                      id={`faq-${f.i}`}
                      className="mx-2 rounded-b-2xl bg-white px-5 pb-5 pt-4 text-[15px] font-medium leading-relaxed text-muted-foreground lg:hidden"
                    >
                      {f.r}
                    </p>
                  )}
                </li>
              );
            })}
          </ul>

          {active && (
            <div data-reveal="right" className="hidden lg:block">
              <article
                aria-live="polite"
                className="sticky top-24 overflow-hidden rounded-[2rem] bg-white shadow-card"
              >
                <div className="p-8 md:p-10">
                  <div className="flex items-center justify-between gap-4">
                    <span
                      className={`rounded-full px-3 py-1 text-xs font-extrabold uppercase text-white ${themes[active.theme]}`}
                    >
                      {nomTheme(active.theme)}
                    </span>
                    <span className="font-display text-5xl leading-none text-sun">
                      {String(ouverte + 1).padStart(2, "0")}
                    </span>
                  </div>
                  <h3 className="mt-5 text-3xl leading-tight text-logo-blue">{active.q}</h3>
                  <p className="mt-4 text-lg font-medium leading-relaxed text-muted-foreground">
                    {active.r}
                  </p>
                </div>
                <div className="flex items-end gap-4 bg-mist-soft pl-8 pr-4 pt-4 md:pl-10">
                  <p className="mb-8 flex-1 rounded-2xl rounded-br-none bg-white p-4 text-sm font-bold shadow-sm">
                    {m.cs_faq_pas_trouve()}
                  </p>
                  <img
                    src={mascotteImhotep}
                    alt=""
                    loading="lazy"
                    width={1414}
                    height={2000}
                    className="-mb-16 w-32 shrink-0 drop-shadow-xl"
                  />
                </div>
              </article>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}

function ClubSante() {
  return (
    <div className="min-h-screen overflow-x-clip bg-carnet text-ink">
      <SiteMotion />
      <SiteHeader />

      {/* Bannière : la photo des clubs en plein écran, un voile bleu nuit pour le texte, puis les repères en carte qui chevauche le bas. */}
      <section className="relative isolate overflow-hidden text-white">
        <img
          src={banniere}
          alt={m.cs_banniere_alt()}
          width={2000}
          height={1160}
          className="absolute inset-0 -z-20 size-full object-cover object-[60%_30%] transition-transform duration-[6s] ease-out starting:scale-110"
        />
        <div
          aria-hidden
          className="absolute inset-0 -z-10 bg-linear-to-t from-night from-30% via-night/70 to-night/10 lg:bg-linear-to-r lg:from-0% lg:from-night/95 lg:via-logo-blue/70 lg:to-transparent"
        />
        <div className="mx-auto flex min-h-[38rem] max-w-7xl flex-col px-5 pb-36 pt-8 md:pt-12 lg:min-h-[44rem] lg:pb-40">
          <FilAriane rubrique={m.menu_vie_du_club()} page={m.menu_club_sante()} clair />

          <div data-reveal="left" className="mt-auto max-w-2xl pt-16">
            <span className="inline-flex rounded-full bg-sun px-4 py-1.5 text-xs font-extrabold uppercase tracking-wide text-ink">
              {m.cs_slogan_officiel()}
            </span>
            <h1 className="mt-5 text-5xl leading-[0.95] [text-shadow:0_2px_16px_rgb(0_0_0/0.55)] md:text-7xl">
              <span className="block">{m.cs_titre_1()}</span>
              <span className="block text-primary">SOS Docteur TV</span>
            </h1>
            <p className="mt-6 font-hand text-3xl leading-tight text-sun md:text-4xl">
              {m.commun_citation({ texte: m.cs_slogan() })}
            </p>
            <p className="mt-5 max-w-xl text-lg font-medium text-white/85">{m.cs_intro()}</p>
            <div className="mt-8 flex flex-wrap gap-3">
              <a
                href="#adhesion"
                className="btn-fx inline-flex items-center gap-2 rounded-full bg-primary px-7 py-3 text-[15px] font-bold text-primary-foreground shadow-card"
              >
                {m.cs_regles_adhesion()} <ArrowRight className="size-4" />
              </a>
              <a
                href="#piliers"
                className="btn-fx rounded-full border-2 border-white px-7 py-3 text-[15px] font-bold hover:bg-white hover:text-logo-blue"
              >
                {m.cs_vision_clubs()}
              </a>
            </div>
          </div>
        </div>
      </section>

      <div className="relative z-10 mx-auto -mt-24 max-w-7xl px-5">
        <ul
          data-reveal
          className="grid grid-cols-2 gap-px overflow-hidden rounded-[2rem] bg-border shadow-card lg:grid-cols-4"
        >
          {reperesBanniere().map((r) => (
            <li key={r.t} className="flex items-start gap-4 bg-card p-5 sm:items-center md:p-7">
              <span
                className={`${r.c} hidden size-12 shrink-0 items-center justify-center rounded-2xl text-white sm:inline-flex`}
              >
                <r.i className="size-6" />
              </span>
              <span>
                <span className="block font-display text-3xl leading-none text-logo-blue md:text-4xl">
                  {r.n}
                </span>
                <span className="mt-1 block text-sm font-bold leading-snug">{r.t}</span>
              </span>
            </li>
          ))}
        </ul>
      </div>

      {/* Cadre réglementaire : les sigles des ministères posés comme des tampons officiels. */}
      <section id="cadre" className="mx-auto max-w-7xl scroll-mt-20 px-5 pt-14">
        <div
          data-reveal
          className="grid items-center gap-10 rounded-[2rem] bg-card p-7 shadow-card md:p-12 lg:grid-cols-[1.25fr_1fr]"
        >
          <div>
            <p className="flex items-center gap-3 text-sm font-extrabold uppercase tracking-widest text-logo-red">
              <span className="h-1 w-8 rounded-full bg-primary" />
              {m.cs_cadre_sur()}
            </p>
            <h2 className="mt-3 text-4xl md:text-5xl">
              <span className="text-logo-blue">{m.cs_cadre_bleu()}</span>{" "}
              <span className="text-primary">{m.cs_cadre_vert()}</span>
            </h2>
            <p className="mt-4 text-lg font-medium text-muted-foreground">{m.cs_cadre_texte()}</p>
            <ul className="mt-6 grid gap-3">
              {[m.cs_cadre_point_1(), m.cs_cadre_point_2(), m.cs_cadre_point_3()].map((t) => (
                <li key={t} className="flex items-center gap-3 font-bold">
                  <CircleCheck className="size-6 shrink-0 text-primary" /> {t}
                </li>
              ))}
            </ul>
          </div>
          <div className="rounded-3xl bg-mist p-6 md:p-8">
            <p className="text-center text-xs font-extrabold uppercase tracking-widest text-logo-blue">
              {m.cs_ministeres()}
            </p>
            <ul className="mt-6 grid grid-cols-2 gap-5">
              {ministeres.map((ministere, i) => (
                <li
                  key={ministere.t}
                  data-reveal="zoom"
                  style={retard(i)}
                  className={`mx-auto flex aspect-square w-full max-w-36 items-center justify-center rounded-full border-4 border-double bg-white p-3 text-center font-display text-lg leading-tight shadow-sm transition duration-300 hover:rotate-0 hover:scale-105 ${ministere.c} ${ministere.r}`}
                >
                  {ministere.t}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </section>

      {/* Certification : bandeau bleu pleine largeur, les lots en lignes à gauche, les mascottes sur un soleil rayonnant à droite. */}
      <section className="relative isolate mt-20 overflow-hidden bg-linear-to-br from-logo-blue via-logo-blue to-night text-white">
        <div
          aria-hidden
          className="absolute inset-0 -z-10 bg-[radial-gradient(circle,rgb(255_255_255/0.08)_1.5px,transparent_1.5px)] bg-size-[22px_22px]"
        />
        <div className="mx-auto grid max-w-7xl items-center gap-12 px-5 py-16 md:py-20 lg:grid-cols-[1.15fr_1fr]">
          <div data-reveal="left">
            <span className="inline-flex items-center gap-2 rounded-full bg-sun px-4 py-1.5 text-xs font-extrabold uppercase tracking-wide text-ink">
              <Trophy className="size-4" /> {m.cs_certif_etiquette()}
            </span>
            <h2 className="mt-5 text-4xl leading-[1.05] md:text-5xl">
              {m.cs_certif_titre_1()}{" "}
              <span className="inline-block -rotate-2 whitespace-nowrap rounded-xl bg-sun px-3 text-ink">
                {m.cs_certif_somme()}
              </span>
              {m.cs_certif_titre_2()}
            </h2>
            <p className="mt-5 max-w-2xl text-lg font-medium text-white/85">
              {m.cs_certif_texte()}
            </p>
            <ul className="mt-8 grid gap-3">
              {lots().map((l, i) => (
                <li
                  key={l.t}
                  data-reveal
                  style={retard(i)}
                  className="flex gap-4 rounded-2xl bg-white/10 p-4 ring-1 ring-white/15 backdrop-blur transition-colors duration-300 hover:bg-white/15"
                >
                  <span
                    className={`inline-flex size-12 shrink-0 items-center justify-center rounded-2xl ${["bg-sun text-ink", "bg-sky", "bg-tangerine"][i]}`}
                  >
                    <l.i className="size-6" />
                  </span>
                  <span>
                    <span className="block text-xs font-extrabold uppercase tracking-wide text-sun">
                      {l.tag}
                    </span>
                    <span className="block font-display text-2xl leading-tight">{l.t}</span>
                    <span className="mt-1 block text-sm font-medium text-white/75">{l.d}</span>
                  </span>
                </li>
              ))}
            </ul>
            <div className="mt-8 flex flex-wrap items-center gap-x-6 gap-y-4">
              <a
                href={lien("/certification")}
                className="btn-fx inline-flex items-center gap-2 rounded-full bg-primary px-7 py-3 text-[15px] font-bold shadow-card"
              >
                {m.cs_certif_lancer()} <ArrowRight className="size-4" />
              </a>
              <p className="text-sm font-bold text-white/80">{m.cs_certif_resume()}</p>
            </div>
          </div>

          <div data-reveal="right" className="relative mx-auto w-full max-w-md lg:max-w-lg">
            {/* Soleil rayonnant derrière les mascottes : il tourne lentement si le visiteur accepte les animations. */}
            <div
              aria-hidden
              className="absolute left-1/2 top-1/2 -z-10 aspect-square w-[135%] -translate-x-1/2 -translate-y-1/2 rounded-full bg-[repeating-conic-gradient(rgb(255_255_255/0.16)_0deg_8deg,transparent_8deg_20deg)] [mask-image:radial-gradient(circle,black_25%,transparent_68%)] motion-safe:animate-[spin_90s_linear_infinite]"
            />
            <div
              aria-hidden
              className="absolute inset-[22%] -z-10 rounded-full bg-sun/45 blur-3xl"
            />
            <img
              src={mascottesTrophees}
              alt={m.cs_certif_mascottes()}
              loading="lazy"
              width={1122}
              height={1402}
              className="mx-auto w-4/5 drop-shadow-2xl sm:w-full"
            />
            <span className="absolute left-0 top-8 -rotate-6 rounded-2xl bg-sun px-4 py-2 text-ink shadow-card sm:-left-4">
              <span className="block text-[11px] font-extrabold uppercase">
                {m.cs_grand_prix()}
              </span>
              <span className="block font-display text-2xl leading-none md:text-3xl">
                {m.cs_grand_prix_somme()}
              </span>
            </span>
            <span className="absolute bottom-10 right-0 flex size-24 rotate-12 flex-col items-center justify-center rounded-full bg-primary shadow-card md:size-28">
              <span className="font-display text-4xl leading-none">12</span>
              <span className="text-xs font-extrabold uppercase">{m.cs_quiz_sante()}</span>
            </span>
          </div>
        </div>
      </section>

      {/* Objectifs : l'objectif général en grand, puis les cinq objectifs spécifiques en tickets numérotés. */}
      <section id="objectifs" className="mx-auto max-w-7xl scroll-mt-20 px-5 pt-20">
        <EnTete sur={m.cs_objectif_sur()} bleu={m.cs_objectif_bleu()} vert={m.cs_objectif_vert()} />
        <blockquote
          data-reveal
          className="relative mt-8 overflow-hidden rounded-[2rem] bg-logo-blue p-8 text-xl font-bold leading-relaxed text-white shadow-card md:p-12 md:text-2xl"
        >
          <Quote aria-hidden className="absolute right-6 top-6 size-20 text-white/10" />
          {m.accueil_objectif_texte()}
        </blockquote>

        <div data-reveal className="mt-14">
          <h3 className="text-3xl">
            <span className="text-logo-blue">{m.cs_orientations_1()}</span>{" "}
            <span className="text-primary">{m.cs_orientations_2()}</span>
          </h3>
          <p className="mt-2 font-medium text-muted-foreground">{m.cs_orientations_texte()}</p>
        </div>
        <ol className="mt-8 grid gap-5 sm:grid-cols-2 lg:grid-cols-5">
          {objectifs().map((o, i) => (
            <li
              key={o.tag}
              data-reveal
              style={retard(i)}
              className="card-fx flex flex-col overflow-hidden rounded-3xl bg-card shadow-card"
            >
              <div className={`${o.c} relative flex items-end justify-between p-5 text-white`}>
                <span className="font-display text-5xl leading-none">0{i + 1}</span>
                <span className="text-right text-[11px] font-extrabold uppercase leading-tight tracking-wide">
                  {o.tag}
                </span>
                {/* Encoches de ticket entre l'en-tête et le texte. */}
                <span
                  aria-hidden
                  className="absolute -bottom-2.5 -left-2.5 size-5 rounded-full bg-background"
                />
                <span
                  aria-hidden
                  className="absolute -bottom-2.5 -right-2.5 size-5 rounded-full bg-background"
                />
              </div>
              <p className="flex-1 border-t-2 border-dashed border-border p-5 font-bold leading-snug">
                {o.t}
              </p>
            </li>
          ))}
        </ol>
      </section>

      {/* Piliers en grille bento, sur un fond blanc bleuté qui rompt la feuille de carnet. */}
      <section id="piliers" className="mt-20 scroll-mt-20 bg-mist-soft py-20">
        <div className="mx-auto max-w-7xl px-5">
          <EnTete sur={m.cs_piliers_sur()} bleu={m.cs_piliers_bleu()} vert={m.cs_piliers_vert()} />
          <div className="mt-8 grid gap-5 lg:grid-cols-3">
            <article
              data-reveal
              className="card-fx relative isolate overflow-hidden rounded-[2rem] bg-linear-to-br from-logo-blue to-night p-8 text-white shadow-card md:p-10 lg:col-span-2"
            >
              <Eye
                aria-hidden
                className="absolute -bottom-8 -right-8 -z-10 size-56 text-white/10"
              />
              <p className="flex items-center gap-2 text-sm font-extrabold uppercase tracking-widest text-sun">
                <Eye className="size-5" /> {m.cs_vision()}
              </p>
              <p className="mt-4 max-w-xl font-display text-3xl leading-tight md:text-5xl">
                {m.cs_vision_texte()}
              </p>
              <p className="mt-4 font-semibold text-white/75">{m.cs_vision_sous()}</p>
            </article>
            <article
              data-reveal
              style={retard(1)}
              className="card-fx rounded-[2rem] bg-primary p-8 text-white shadow-card"
            >
              <p className="flex items-center gap-2 text-sm font-extrabold uppercase tracking-widest">
                <Target className="size-5" /> {m.cs_but()}
              </p>
              <p className="mt-4 text-xl font-extrabold leading-snug">{m.cs_but_texte()}</p>
              <p className="mt-4 font-semibold text-white/80">{m.cs_but_sous()}</p>
            </article>
            <article data-reveal className="card-fx rounded-[2rem] bg-sun p-8 text-ink shadow-card">
              <p className="flex items-center gap-2 text-sm font-extrabold uppercase tracking-widest">
                <Rocket className="size-5" /> {m.cs_mission()}
              </p>
              <p className="mt-4 text-xl font-extrabold leading-snug">{m.cs_mission_texte()}</p>
              <p className="mt-4 font-semibold text-ink/70">{m.cs_mission_sous()}</p>
            </article>
            <article
              data-reveal
              style={retard(1)}
              className="card-fx rounded-[2rem] bg-card p-8 shadow-card lg:col-span-2"
            >
              <p className="flex items-center gap-2 text-sm font-extrabold uppercase tracking-widest text-logo-blue">
                <Gem className="size-5" /> {m.cs_valeurs()}
              </p>
              <ul className="mt-5 flex flex-wrap gap-3">
                {valeurs().map((v) => (
                  <li
                    key={v.t}
                    className={`${v.c} rounded-full px-5 py-2 font-display text-xl text-white transition duration-300 hover:-rotate-3 hover:scale-105`}
                  >
                    {v.t}
                  </li>
                ))}
              </ul>
              <p className="mt-5 font-semibold text-muted-foreground">{m.cs_valeurs_texte()}</p>
            </article>
            <article
              data-reveal
              className="relative isolate overflow-hidden rounded-[2rem] bg-logo-red p-8 text-white shadow-card md:p-10 lg:col-span-3"
            >
              <Megaphone
                aria-hidden
                className="absolute -bottom-10 -right-6 -z-10 size-56 -rotate-12 text-white/10"
              />
              <div className="flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
                <div>
                  <p className="flex items-center gap-2 text-sm font-extrabold uppercase tracking-widest text-white/85">
                    <Megaphone className="size-5" /> {m.cs_slogan_etiquette()}
                  </p>
                  <p className="mt-3 font-hand text-3xl leading-tight md:text-5xl">
                    {m.commun_citation({ texte: m.cs_slogan() })}
                  </p>
                </div>
                <p className="max-w-xs shrink-0 font-semibold text-white/85">
                  {m.cs_slogan_texte()}
                </p>
              </div>
            </article>
          </div>
        </div>
      </section>

      {/* Historique : le récit à gauche, les jalons en frise verticale à droite. */}
      <section id="historique" className="mx-auto max-w-7xl scroll-mt-20 px-5 pt-20">
        <div className="grid gap-10 lg:grid-cols-[1.35fr_1fr] lg:gap-14">
          <div>
            <EnTete
              sur={m.cs_historique_sur()}
              bleu={m.cs_historique_bleu()}
              vert={m.cs_historique_vert()}
            />
            <div
              data-reveal
              className="mt-6 space-y-4 text-lg leading-relaxed text-muted-foreground"
            >
              <p>{m.cs_historique_1()}</p>
              <p>{m.cs_historique_2()}</p>
            </div>
          </div>

          <aside
            data-reveal="right"
            className="self-start rounded-[2rem] bg-card p-7 shadow-card md:p-9 lg:sticky lg:top-24"
          >
            <p className="text-sm font-extrabold uppercase tracking-widest text-logo-blue">
              {m.cs_jalons_titre()}
            </p>
            <h3 className="mt-1 text-3xl text-primary">{m.cs_reperes()}</h3>
            <ol className="relative mt-6 space-y-8 border-l-2 border-dashed border-logo-blue/25 pl-8">
              {jalons().map((j) => (
                <li key={j.date} className="relative">
                  <span
                    aria-hidden
                    className={`${j.c} absolute -left-[2.6rem] top-0.5 size-5 rounded-full ring-4 ring-card`}
                  />
                  <p
                    className={`${j.c} inline-flex rounded-full px-3 py-1 text-xs font-extrabold uppercase text-white`}
                  >
                    {j.date}
                  </p>
                  <p className="mt-2 font-bold leading-snug">{j.t}</p>
                </li>
              ))}
            </ol>
          </aside>
        </div>
      </section>

      {/* Les trois formes d'éducation : la non formelle, cœur des clubs, au centre et en couleur. */}
      <section id="education" className="mx-auto max-w-7xl scroll-mt-20 px-5 pt-20">
        <EnTete
          sur={m.cs_education_sur()}
          bleu={m.cs_education_bleu()}
          vert={m.cs_education_vert()}
          centre
        >
          {m.cs_education_texte()}
        </EnTete>
        <div className="mt-10 grid items-center gap-5 md:grid-cols-3">
          {educations().map((e, i) => (
            <article
              key={e.t}
              data-reveal
              style={retard(i)}
              className={`card-fx relative rounded-[2rem] p-7 shadow-card ${e.coeur ? "bg-primary py-10 text-white md:-my-4" : "bg-card"}`}
            >
              {e.coeur && (
                <span className="absolute -top-4 left-1/2 -translate-x-1/2 whitespace-nowrap rounded-full bg-sun px-4 py-1.5 text-xs font-extrabold uppercase text-ink shadow-card">
                  {m.cs_education_2_etiquette()}
                </span>
              )}
              <span
                className={`inline-flex size-14 items-center justify-center rounded-2xl ${e.coeur ? "bg-white/20" : "bg-mist text-logo-blue"}`}
              >
                <e.i className="size-7" />
              </span>
              <p
                className={`mt-5 text-xs font-extrabold uppercase tracking-wide ${e.coeur ? "text-white/80" : "text-tangerine"}`}
              >
                {e.tag}
              </p>
              <h3 className={`mt-1 text-2xl ${e.coeur ? "" : "text-logo-blue"}`}>{e.t}</h3>
              <p
                className={`mt-3 font-medium ${e.coeur ? "text-white/90" : "text-muted-foreground"}`}
              >
                {e.d}
              </p>
              <p
                className={`mt-5 border-t pt-4 text-sm font-bold ${e.coeur ? "border-white/25" : ""}`}
              >
                {m.cs_education_dimension({ numero: String(i + 1) })}
              </p>
            </article>
          ))}
        </div>
        <div
          data-reveal
          className="mt-12 grid items-center gap-6 rounded-[2rem] border-2 border-dashed border-primary/40 bg-card/80 p-7 md:grid-cols-[auto_1fr] md:p-9"
        >
          <span className="inline-flex size-16 items-center justify-center rounded-full bg-primary/15 text-primary">
            <HeartHandshake className="size-8" />
          </span>
          <div>
            <h3 className="text-2xl text-logo-blue">{m.cs_positionnement_titre()}</h3>
            <p className="mt-2 font-medium text-muted-foreground">{m.cs_positionnement_texte()}</p>
          </div>
        </div>
      </section>

      {/* Mot du promoteur : bandeau pleine largeur. */}
      <section className="relative isolate mt-24 overflow-hidden bg-linear-to-br from-logo-blue to-night text-white">
        <div
          aria-hidden
          className="absolute -right-20 top-0 -z-10 size-96 rounded-full bg-sky/30 blur-3xl"
        />
        <div className="mx-auto grid max-w-7xl items-center gap-10 px-5 py-16 md:py-20 lg:grid-cols-[auto_1fr] lg:gap-16">
          <div data-reveal="left" className="relative mx-auto w-56 md:w-64">
            <div
              aria-hidden
              className="absolute inset-0 translate-x-3 translate-y-3 rounded-[2rem] bg-sun"
            />
            <img
              src={kodom}
              alt={m.cs_promoteur_photo()}
              loading="lazy"
              width={1097}
              height={1434}
              className="relative aspect-[4/5] w-full rounded-[2rem] object-cover object-top"
            />
          </div>
          <div data-reveal="right">
            <p className="text-sm font-extrabold uppercase tracking-widest text-sun">
              {m.cs_promoteur_etiquette()}
            </p>
            <blockquote className="mt-4 text-xl font-semibold leading-relaxed md:text-2xl">
              <Quote aria-hidden className="mb-3 size-10 text-primary" />
              {m.cs_promoteur_texte()}
            </blockquote>
            <p className="mt-6 font-display text-2xl">{m.cs_promoteur_photo()}</p>
            <p className="text-sm font-semibold text-white/70">{m.cs_promoteur_role()}</p>
          </div>
        </div>
      </section>

      {/* Adhésion et gouvernance : les règles à gauche, le bureau de 21 membres à droite. */}
      <section id="adhesion" className="mx-auto max-w-7xl scroll-mt-20 px-5 pt-20">
        <div className="flex flex-wrap items-end justify-between gap-6">
          <EnTete sur={m.cs_adhesion_sur()} bleu={m.cs_adhesion_bleu()} vert={m.cs_adhesion_vert()}>
            {m.cs_adhesion_texte()}
          </EnTete>
          <a
            href="#"
            data-reveal
            className="btn-fx inline-flex items-center gap-2 rounded-full bg-primary px-7 py-3 text-[15px] font-bold text-primary-foreground shadow-card"
          >
            {m.cs_affiliation()} <ArrowRight className="size-4" />
          </a>
        </div>

        <div className="mt-10 grid gap-6 lg:grid-cols-2">
          <article data-reveal="left" className="rounded-[2rem] bg-card p-7 shadow-card md:p-9">
            <h3 className="text-2xl text-logo-blue md:text-3xl">{m.cs_faq_1_q()}</h3>
            <ul className="mt-6 space-y-4">
              {regles().map((r, i) => (
                <li key={r} className="flex gap-4">
                  <span
                    className={`mt-0.5 inline-flex size-7 shrink-0 items-center justify-center rounded-full text-white ${["bg-sky", "bg-primary", "bg-tangerine", "bg-grape", "bg-rose", "bg-logo-blue"][i]}`}
                  >
                    <Check className="size-4" strokeWidth={3} />
                  </span>
                  <p className="font-semibold leading-snug">{r}</p>
                </li>
              ))}
            </ul>
          </article>

          <article data-reveal="right" className="rounded-[2rem] bg-card p-7 shadow-card md:p-9">
            <h3 className="text-2xl text-logo-blue md:text-3xl">{m.cs_bureau_titre()}</h3>
            <p className="mt-1 font-semibold text-muted-foreground">{m.cs_bureau_sous()}</p>
            {/* 21 pastilles : 11 filles au moins, 10 garçons au plus. */}
            <div className="mt-6 flex flex-wrap items-center gap-6 rounded-3xl bg-mist p-5">
              <div>
                <p className="font-display text-6xl leading-none text-logo-blue">21</p>
                <p className="text-xs font-extrabold uppercase tracking-wide">
                  {m.cs_membres_total()}
                </p>
              </div>
              <div className="flex-1">
                <ul aria-hidden className="grid max-w-64 grid-cols-7 gap-1.5">
                  {Array.from({ length: 21 }, (_, i) => (
                    <li
                      key={i}
                      className={`aspect-square rounded-full ${i < 11 ? "bg-rose" : "bg-sky"}`}
                    />
                  ))}
                </ul>
                <p className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-sm font-bold">
                  <span className="flex items-center gap-1.5">
                    <span className="size-3 rounded-full bg-rose" /> {m.cs_filles()}
                  </span>
                  <span className="flex items-center gap-1.5">
                    <span className="size-3 rounded-full bg-sky" /> {m.cs_garcons()}
                  </span>
                </p>
              </div>
            </div>
            <ol className="mt-6 space-y-3">
              {bureau().map((b, i) => (
                <li key={b} className="flex gap-3">
                  <span className="inline-flex size-7 shrink-0 items-center justify-center rounded-lg bg-logo-blue font-display text-sm text-white">
                    {i + 1}
                  </span>
                  <p className="font-semibold leading-snug">{b}</p>
                </li>
              ))}
            </ol>
            <p className="mt-6 flex gap-3 rounded-2xl bg-primary/10 p-4 text-sm font-semibold">
              <Accessibility className="size-5 shrink-0 text-primary" />
              <span>
                <strong>{m.cs_inclusion_titre()}</strong> {m.cs_inclusion_texte()}
              </span>
            </p>
          </article>
        </div>
      </section>

      <FaqSection />

      <SiteFooter />
    </div>
  );
}
