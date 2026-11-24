import { useState, useEffect, useRef } from "react";
import { texteAxe } from "@/lib/axes";
import { lien } from "@/lib/langues";
import { m } from "@/paraglide/messages.js";
import { createFileRoute } from "@tanstack/react-router";
import {
  ArrowRight,
  ChevronLeft,
  ChevronRight,
  Earth,
  Pyramid,
  RotateCw,
  Sparkles,
  Trophy,
  HeartPulse,
  Users,
  School,
  Backpack,
  MapPinned,
  SearchCheck,
  Landmark,
  Volume2,
  VolumeX,
} from "lucide-react";
import { ClubsSection } from "@/components/ClubsSection";
import { chargerDre, chargerProchainsEvenements } from "@/lib/api/client";
import { AgendaSidebar } from "@/components/AgendaSidebar";
import { PartenairesSection } from "@/components/PartenairesSection";
import { GalerieSection } from "@/components/GalerieSection";
import { InitiateurSection } from "@/components/InitiateurSection";
import { CampagnesSection } from "@/components/CampagnesSection";
import { TemoignagesSection } from "@/components/TemoignagesSection";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";
import { Compteur } from "@/components/Compteur";
import { SiteMotion, retard } from "@/components/SiteMotion";
import { DecorAnime } from "@/components/DecorAnime";
import { BulleDefi } from "@/components/BulleDefi";
import { PodiumClubs } from "@/components/PodiumClubs";
import { BandeAxes, QuelAxe } from "@/components/QuelAxe";
import hero from "@/assets/hero.jpg";
import mascotteImhotep from "@/assets/mascotte-imhotep.webp";
import mascotteValeurs from "@/assets/mascotte-valeurs.webp";
import mascotteMedias from "@/assets/mascotte-medias.webp";
import mascotteSecourisme from "@/assets/mascotte-secourisme.webp";
import mascotteBourses from "@/assets/mascotte-bourses.webp";
import mascotteLeadership from "@/assets/mascotte-leadership.webp";
import mascotteEnvironnement from "@/assets/mascotte-environnement.webp";
import mascottesLivres from "@/assets/mascottes-livres.webp";
import mascottesVs from "@/assets/mascottes-vs.webp";
import mascottesAxes from "@/assets/mascottes-axes.webp";
import grandesFinales from "@/assets/agenda-grandes-finales.jpg";
import story1 from "@/assets/story1.jpg";
import story2 from "@/assets/story2.jpg";
import slideMascottes from "@/assets/slide-mascottes.jpg";
import slideClubs from "@/assets/slide-clubs.webp";
import slideGenie from "@/assets/slide-genie.jpg";
import slideAxes from "@/assets/slide-axes.jpg";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: m.accueil_meta_titre() },
      { name: "description", content: m.accueil_meta_description() },
      { property: "og:title", content: "Club Santé SOS Docteur TV" },
      {
        property: "og:description",
        content: m.accueil_meta_description(),
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  // Sans l'API, l'accueil s'affiche quand même : la section des clubs disparaît, l'agenda dit qu'il est vide.
  loader: async () => {
    const [dre, prochains] = await Promise.all([
      chargerDre().catch(() => []),
      chargerProchainsEvenements().catch(() => []),
    ]);
    return { dre, prochains };
  },
  component: Index,
});

// Les 7 axes stratégiques. `t` : nom de l'axe, au dos de la carte ; `s` : slogan ; `c` : couleur de la carte.
const univers = () => [
  {
    t: texteAxe(1).titre,
    s: texteAxe(1).slogan,
    c: "bg-sky",
    img: mascotteImhotep,
  },
  {
    t: texteAxe(2).titre,
    s: m.axe_2_slogan_evss(),
    c: "bg-rose",
    img: mascotteValeurs,
  },
  {
    t: texteAxe(3).titre,
    s: texteAxe(3).slogan,
    c: "bg-grape",
    img: mascotteMedias,
  },
  {
    t: texteAxe(4).titre,
    s: texteAxe(4).slogan,
    c: "bg-tangerine",
    img: mascotteSecourisme,
  },
  {
    t: texteAxe(5).titre,
    s: texteAxe(5).slogan,
    c: "bg-sun",
    img: mascotteBourses,
  },
  {
    t: texteAxe(6).titre,
    s: texteAxe(6).slogan,
    c: "bg-bark",
    img: mascotteLeadership,
  },
  {
    t: texteAxe(7).titre,
    s: texteAxe(7).slogan,
    c: "bg-leaf",
    img: mascotteEnvironnement,
  },
];

// Piliers et valeurs du programme. `c` : fond de l'icône et filet du bas ; `tc` : couleur du mot clé.
const valeurs = () => [
  {
    i: Sparkles,
    mot: m.accueil_valeur_1_mot(),
    titre: m.accueil_valeur_1_titre(),
    d: m.accueil_valeur_1_texte(),
    c: "bg-logo-blue",
    tc: "text-logo-blue",
  },
  {
    i: Earth,
    mot: m.accueil_valeur_2_mot(),
    titre: m.accueil_valeur_2_titre(),
    d: m.accueil_valeur_2_texte(),
    c: "bg-primary",
    tc: "text-primary",
  },
  {
    i: Pyramid,
    mot: m.accueil_valeur_3_mot(),
    titre: m.accueil_valeur_3_titre(),
    d: m.accueil_valeur_3_texte(),
    c: "bg-tangerine",
    tc: "text-tangerine",
  },
];

// `plus` : le chiffre est un minimum, affiché « +800 ». Grille bento : l'ordre remplit la grille ligne par ligne,
// `place` fixe l'emprise de la case (2 colonnes sur mobile, 4 sur grand écran) et `taille` celle du chiffre.
const chiffresCles = () => [
  {
    plus: true,
    n: 800,
    t: m.accueil_chiffre_clubs(),
    i: HeartPulse,
    place: "col-span-2 lg:row-span-2",
    fond: "bg-linear-to-br from-logo-blue to-night text-white",
    chiffre: "text-primary",
    taille: "text-7xl md:text-8xl lg:text-9xl",
  },
  {
    plus: true,
    n: 3500,
    t: m.accueil_chiffre_encadreurs(),
    i: Users,
    place: "col-span-2",
    fond: "bg-primary text-white",
    chiffre: "",
    taille: "text-5xl md:text-6xl",
  },
  {
    plus: true,
    n: 2396,
    t: m.accueil_chiffre_secondaire1(),
    i: Backpack,
    place: "",
    fond: "bg-sun text-ink",
    chiffre: "",
    taille: "text-4xl md:text-5xl",
  },
  {
    plus: true,
    n: 714,
    t: m.accueil_chiffre_secondaire2(),
    i: School,
    place: "",
    fond: "bg-mist text-ink",
    chiffre: "text-logo-blue",
    taille: "text-4xl md:text-5xl",
  },
  {
    plus: false,
    n: 7,
    t: m.accueil_chiffre_dre(),
    i: MapPinned,
    place: "",
    fond: "bg-card text-ink ring-1 ring-logo-blue/15",
    chiffre: "text-logo-blue",
    taille: "text-4xl md:text-5xl",
  },
  {
    plus: false,
    n: 19,
    t: m.accueil_chiffre_inspections(),
    i: SearchCheck,
    place: "",
    fond: "bg-tangerine text-white",
    chiffre: "",
    taille: "text-4xl md:text-5xl",
  },
  {
    plus: false,
    n: 1,
    t: m.accueil_chiffre_cabinet(),
    i: Landmark,
    place: "col-span-2",
    fond: "bg-logo-red text-white",
    chiffre: "",
    taille: "text-5xl md:text-6xl",
  },
];

// Section Actualités : un article à la une, puis les autres en ligne.
const aLaUne = () => ({
  img: grandesFinales,
  tag: m.accueil_une_etiquette(),
  t: m.accueil_une_titre(),
  d: m.accueil_une_texte(),
});

const stars = () => [
  {
    img: story2,
    tag: m.accueil_star_1_etiquette(),
    tc: "bg-grape",
    t: m.accueil_star_1_titre(),
    d: m.accueil_star_1_texte(),
  },
  {
    img: story1,
    tag: m.accueil_star_2_etiquette(),
    tc: "bg-tangerine",
    t: m.accueil_star_2_titre(),
    d: m.accueil_star_2_texte(),
  },
  {
    img: hero,
    tag: m.accueil_star_3_etiquette(),
    tc: "bg-leaf",
    t: m.accueil_star_3_titre(),
    d: m.accueil_star_3_texte(),
  },
];

// `onglet` : nom court affiché en étiquette au-dessus du titre. `fond` : dégradé de la section, assez sombre pour le texte blanc.
// `accent` : couleur du cadre décalé derrière la photo. `cadrage` : point de la photo à garder visible.

const heroSlides = () => [
  {
    img: slideMascottes,
    video: "0eflxy2KLRQ",
    onglet: m.accueil_slide_1_onglet(),
    fond: "from-logo-blue to-grape",
    accent: "bg-sun",
    cadrage: "object-[50%_25%]",
    alt: m.accueil_slide_1_alt(),
    lines: [m.accueil_slide_1_ligne1(), m.accueil_slide_1_ligne2()],
    cta: [
      { t: m.accueil_slide_1_action1(), href: "#" },
      { t: m.accueil_slide_1_action2(), href: "/certification" },
    ],
    sub: m.accueil_slide_1_texte(),
  },
  {
    img: slideClubs,
    onglet: m.accueil_slide_2_onglet(),
    fond: "from-night to-logo-blue",
    accent: "bg-primary",
    cadrage: "object-center",
    alt: m.accueil_slide_2_alt(),
    mascot: {
      src: mascottesLivres,
      alt: m.accueil_slide_2_mascotte(),
      width: 1122,
      height: 1402,
    },
    lines: [m.accueil_slide_2_ligne1(), m.accueil_slide_2_ligne2()],
    cta: [
      { t: m.accueil_slide_2_action1(), href: "/club-sante#adhesion" },
      { t: m.accueil_slide_2_action2(), href: "/carte-des-clubs" },
    ],
    tagline: m.accueil_slide_2_accroche(),
    sub: m.accueil_slide_2_texte(),
  },
  {
    img: slideGenie,
    onglet: m.accueil_une_etiquette(),
    fond: "from-grape to-night",
    accent: "bg-tangerine",
    cadrage: "object-center",
    alt: m.accueil_slide_3_alt(),
    mascot: {
      src: mascottesVs,
      alt: m.accueil_slide_3_mascotte(),
      width: 2000,
      height: 2000,
    },
    lines: [m.accueil_slide_3_ligne1(), m.accueil_slide_3_ligne2()],
    cta: [
      { t: m.accueil_slide_3_action1(), href: "/jeux" },
      { t: m.accueil_slide_3_action2(), href: "/carte-des-clubs" },
    ],
    tagline: m.accueil_slide_3_accroche(),
    sub: m.accueil_slide_3_texte(),
  },
  {
    img: slideAxes,
    onglet: m.accueil_slide_4_onglet(),
    fond: "from-logo-blue to-night",
    accent: "bg-sky",
    cadrage: "object-center",
    alt: m.accueil_slide_4_alt(),
    mascot: {
      src: mascottesAxes,
      alt: m.accueil_slide_4_mascotte(),
      width: 1122,
      height: 1402,
    },
    lines: [m.accueil_slide_4_ligne1(), m.accueil_slide_4_ligne2()],
    cta: [
      { t: m.accueil_slide_4_action1(), href: "/les-7-axes" },
      { t: m.accueil_slide_4_action2(), href: "/bibliotheque" },
    ],
    tagline: m.accueil_slide_4_accroche(),
    sub: m.accueil_slide_4_texte(),
  },
];

// Le contenu sortant s'efface vite, puis le suivant apparaît : les deux ne se superposent jamais.
const heroFade = (on: boolean) =>
  `transition-[opacity,visibility,translate] ease-out ${on ? "translate-y-0 opacity-100 duration-500 delay-200" : "invisible translate-y-3 opacity-0 duration-200"}`;

// Carte d'un axe : la mascotte au recto, la description et le slogan au verso.
// À la souris, le survol la retourne ; au toucher et au clavier, chaque appui la retourne et la laisse ainsi.
function CarteAxe({ u, i }: { u: ReturnType<typeof univers>[number]; i: number }) {
  const [retournee, setRetournee] = useState(false);
  const basculer = () => setRetournee((r) => !r);

  return (
    <div
      data-reveal
      style={retard(i)}
      className="group perspective-[1400px] sm:col-span-2 sm:max-lg:last:col-start-2 lg:nth-5:col-start-2"
    >
      <div
        role="button"
        tabIndex={0}
        aria-pressed={retournee}
        onClick={() => {
          // Un clic de souris suit déjà le survol : le compter retournerait la carte une seconde fois.
          if (window.matchMedia("(hover: none)").matches) basculer();
        }}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            basculer();
          }
        }}
        className={`relative aspect-[4/5] w-full cursor-pointer rounded-3xl shadow-card transition-transform duration-700 transform-3d lg:aspect-[3/4] group-hover:rotate-y-180 ${retournee ? "rotate-y-180" : ""}`}
      >
        <div
          className={`${u.c} absolute inset-0 overflow-hidden rounded-3xl bg-[radial-gradient(circle_at_50%_22%,oklch(1_0_0/0.25),transparent_65%)] text-center text-primary-foreground backface-hidden`}
        >
          <img
            src={u.img}
            alt=""
            loading="lazy"
            width={1414}
            height={2000}
            className="absolute inset-x-0 bottom-0 mx-auto h-[94%] w-auto object-contain object-bottom"
          />
          <span className="absolute left-3 top-3 rounded-full bg-white px-3 py-1 font-display text-sm uppercase text-ink shadow-card">
            {m.axe_numero({ numero: String(i + 1) })}
          </span>
          {/* Indice au recto : la carte se retourne. */}
          <span className="absolute bottom-3 right-3 rounded-full bg-white/25 p-2 backdrop-blur-sm">
            <RotateCw className="h-5 w-5" />
          </span>
        </div>

        <div className="absolute inset-0 flex rotate-y-180 flex-col overflow-hidden rounded-3xl bg-night p-6 text-white backface-hidden">
          <div
            aria-hidden
            className={`${u.c} absolute -right-16 -top-16 size-48 rounded-full opacity-50 blur-3xl`}
          />
          <span
            className={`${u.c} relative self-start rounded-full px-3 py-1 text-xs font-extrabold uppercase text-primary-foreground`}
          >
            {m.axe_numero({ numero: String(i + 1) })}
          </span>
          <h3 className="relative mt-4 flex-1 font-sans text-lg font-extrabold leading-snug lg:text-base xl:text-lg">
            {u.t}
          </h3>
          <p className="relative font-hand text-2xl leading-tight text-sun lg:text-xl xl:text-2xl">
            {m.commun_citation({ texte: u.s })}
          </p>
        </div>
      </div>
    </div>
  );
}

function ObjectifProgramme() {
  return (
    <section id="objectif" className="mx-auto max-w-7xl scroll-mt-16 px-5 pt-20">
      <div data-reveal>
        <h2 className="text-4xl md:text-5xl">
          <span className="text-logo-blue">{m.accueil_objectif_1()}</span>{" "}
          <span className="text-primary">{m.accueil_objectif_2()}</span>
        </h2>
        <p className="mt-3 max-w-4xl text-lg font-medium text-muted-foreground">
          {m.accueil_objectif_texte()}
        </p>
      </div>

      <h3
        data-reveal
        className="mt-12 flex items-center gap-3 font-sans text-sm font-extrabold uppercase tracking-widest text-logo-blue"
      >
        <span className="h-1 w-8 rounded-full bg-primary" />
        {m.accueil_piliers()}
      </h3>
      <div className="mt-6 grid gap-6 md:grid-cols-3">
        {valeurs().map((v, i) => (
          <article
            key={v.mot}
            data-reveal
            style={retard(i)}
            className="card-fx group relative overflow-hidden rounded-3xl bg-card p-7 pb-9 shadow-card"
          >
            <span
              aria-hidden
              className="absolute -right-2 -top-5 font-display text-[7rem] leading-none text-ink/5"
            >
              0{i + 1}
            </span>
            <span
              className={`${v.c} inline-flex size-14 items-center justify-center rounded-2xl text-primary-foreground shadow-card transition duration-300 group-hover:-rotate-6 group-hover:scale-110`}
            >
              <v.i className="size-7" />
            </span>
            <h4 className={`mt-5 font-display text-3xl ${v.tc}`}>{v.mot}</h4>
            <p className="mt-2 text-sm font-extrabold uppercase tracking-wide">{v.titre}</p>
            <p className="mt-3 font-medium text-muted-foreground">{v.d}</p>
            <span className={`${v.c} absolute inset-x-0 bottom-0 h-1.5`} />
          </article>
        ))}
      </div>

      <h3
        data-reveal
        className="mt-12 flex items-center gap-3 font-sans text-sm font-extrabold uppercase tracking-widest text-logo-blue"
      >
        <span className="h-1 w-8 rounded-full bg-primary" />
        {m.accueil_chiffres()}
      </h3>
      <ul className="mt-8 grid grid-cols-2 gap-4 md:gap-5 lg:auto-rows-[minmax(12.5rem,auto)] lg:grid-cols-4">
        {chiffresCles().map((c, i) => (
          <li
            key={c.t}
            data-reveal={i === 0 ? "zoom" : ""}
            style={retard(i)}
            className={`card-fx group relative isolate flex min-h-44 flex-col justify-between gap-6 overflow-hidden rounded-3xl p-5 md:p-7 ${c.place} ${c.fond}`}
          >
            <c.i
              aria-hidden
              className={`absolute -z-10 opacity-10 transition-transform duration-500 group-hover:-rotate-12 group-hover:scale-110 ${i === 0 ? "-bottom-10 -right-10 size-72" : "-bottom-6 -right-6 size-32"}`}
            />
            {i === 0 && (
              <span
                aria-hidden
                className="absolute -left-20 -top-20 -z-10 size-64 rounded-full border-[2rem] border-white/10"
              />
            )}
            <span className="inline-flex size-11 items-center justify-center rounded-2xl bg-current/10">
              <c.i className="size-5" />
            </span>
            <div>
              <p className={`whitespace-nowrap font-display leading-none ${c.taille} ${c.chiffre}`}>
                {c.plus && "+"}
                <Compteur value={c.n} />
              </p>
              <p
                className={`mt-2 font-bold leading-snug ${i === 0 ? "text-xl md:text-2xl" : "text-sm md:text-base"}`}
              >
                {c.t}
              </p>
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}

// Actualités : « C'est toi la star ! » sur deux colonnes (un article à la une, puis trois en ligne), l'agenda en colonne de droite.
function ActualitesSection() {
  const { prochains } = Route.useLoaderData();
  const une = aLaUne();
  const articles = stars();
  return (
    <section id="actualites" className="mx-auto max-w-7xl scroll-mt-16 px-5 pb-12 pt-20">
      <div data-reveal>
        <h2 className="text-4xl md:text-5xl">
          <span className="text-logo-blue">{m.accueil_actus_1()}</span>{" "}
          <span className="text-primary">{m.accueil_actus_2()}</span>
        </h2>
        <p className="mt-3 max-w-2xl text-lg font-medium text-muted-foreground">
          {m.accueil_actus_texte()}
        </p>
      </div>

      <div className="mt-10 grid gap-8 lg:grid-cols-3">
        <div className="min-w-0 lg:col-span-2">
          <div data-reveal className="flex flex-wrap items-end justify-between gap-x-6 gap-y-1">
            <h3 className="text-3xl">
              <span className="text-logo-blue">{m.accueil_star_titre_1()}</span>{" "}
              <span className="text-primary">{m.accueil_star_titre_2()}</span>
            </h3>
            <a
              href={lien("/magazine")}
              className="group flex items-center gap-1.5 font-bold text-logo-blue"
            >
              {m.accueil_toutes_actus()}
              <ArrowRight className="size-4 transition-transform duration-300 group-hover:translate-x-1" />
            </a>
          </div>

          {/* À la une : la photo occupe toute la carte ; le texte est posé sur un verre bleu, assez opaque pour rester lisible sur n'importe quelle zone de la photo. */}
          <article
            data-reveal="zoom"
            className="group relative isolate mt-5 flex min-h-[30rem] items-end overflow-hidden rounded-[2rem] shadow-card md:aspect-video md:min-h-0"
          >
            <img
              src={une.img}
              alt=""
              loading="lazy"
              width={2000}
              height={963}
              className="absolute inset-0 -z-10 size-full object-cover transition duration-1000 group-hover:scale-105"
            />
            <span className="absolute left-5 top-5 inline-flex items-center gap-1.5 rounded-full bg-sun px-3 py-1.5 text-xs font-extrabold uppercase text-ink shadow-card">
              <Sparkles className="size-3.5" /> {m.accueil_a_la_une()}
            </span>
            <div className="relative m-3 max-w-lg overflow-hidden rounded-[1.5rem] border border-white/30 bg-logo-blue/80 p-5 text-white shadow-[0_20px_50px_-12px] shadow-night/50 backdrop-blur-xl backdrop-saturate-150 md:m-5 md:p-7">
              <div
                aria-hidden
                className="absolute inset-x-0 top-0 -z-10 h-1/2 bg-linear-to-b from-white/15 to-transparent"
              />
              <span className="rounded-full bg-white/15 px-3 py-1 text-xs font-extrabold uppercase text-sun ring-1 ring-white/25">
                {une.tag}
              </span>
              <h4 className="mt-3 font-display text-2xl leading-tight md:text-3xl">{une.t}</h4>
              <p className="mt-2 font-medium text-white/90">{une.d}</p>
              <a
                href={lien("/magazine")}
                className="btn-fx mt-5 inline-flex items-center gap-2 rounded-full bg-primary px-6 py-3 text-[15px] font-bold text-primary-foreground after:absolute after:inset-0"
              >
                {m.accueil_lire_article()} <ArrowRight className="size-4" />
              </a>
            </div>
          </article>

          {/* Carrousel continu : la liste est doublée pour boucler sans saut, et s'arrête au survol.
              Chaque article est une photo pleine, son titre posé sur un bandeau de verre blanc. */}
          <div className="group/defile mt-5 overflow-hidden [mask-image:linear-gradient(to_right,transparent,black_6%,black_94%,transparent)]">
            <ul className="flex w-max gap-4 py-2 motion-safe:animate-marquee group-hover/defile:[animation-play-state:paused] md:gap-5">
              {[...articles, ...articles].map((s, i) => (
                <li
                  key={i}
                  aria-hidden={i >= articles.length}
                  className="card-fx group relative isolate flex aspect-[4/5] w-60 shrink-0 items-end overflow-hidden rounded-3xl shadow-card sm:w-64"
                >
                  <img
                    src={s.img}
                    alt=""
                    loading="lazy"
                    className="absolute inset-0 -z-10 size-full object-cover object-right transition duration-500 group-hover:scale-110"
                  />
                  <div className="m-2.5 w-full rounded-2xl border border-white/60 bg-white/80 p-3.5 shadow-card backdrop-blur-lg backdrop-saturate-150">
                    <span
                      className={`${s.tc} rounded-full px-2.5 py-0.5 text-[11px] font-extrabold uppercase text-primary-foreground`}
                    >
                      {s.tag}
                    </span>
                    <h4 className="mt-2 font-sans font-extrabold leading-snug text-ink">
                      <a
                        href={lien("/magazine")}
                        tabIndex={i >= articles.length ? -1 : undefined}
                        className="after:absolute after:inset-0"
                      >
                        {s.t}
                      </a>
                    </h4>
                    <p className="mt-1 line-clamp-2 text-sm font-medium text-ink/70">{s.d}</p>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <AgendaSidebar evenements={prochains} />
      </div>
    </section>
  );
}

// Carte du jeu concours, à cheval sur le bas du hero : remontée de la moitié de sa propre hauteur, quelle que soit la largeur.
// La marge négative du bas rend une partie de la place libérée ; le liseré blanc la détache du fond coloré.
function JeuConcours() {
  return (
    <section className="relative z-10 mx-auto -mb-28 max-w-6xl -translate-y-1/2 px-5 sm:-mb-24 sm:px-8">
      <div
        data-reveal
        className="relative isolate grid items-center gap-6 overflow-hidden rounded-3xl bg-logo-red p-5 text-white shadow-card ring-4 ring-white sm:p-6 md:p-10 lg:grid-cols-[1fr_auto] lg:gap-10"
      >
        <Trophy
          aria-hidden
          className="pointer-events-none absolute -bottom-10 -right-6 -z-10 size-72 -rotate-12 text-white/10 md:size-96"
        />

        {/* Deux lignes à partir de 640 px ; en dessous, le texte revient à la ligne selon la place. */}
        <h2 className="text-[1.75rem] uppercase leading-[1.15] sm:text-3xl lg:text-[2rem] xl:text-[2.5rem]">
          <span className="sm:block sm:whitespace-nowrap">
            {m.accueil_concours_1()}{" "}
            <span className="text-sun">{m.accueil_concours_certification()}</span>
          </span>{" "}
          <span className="sm:block sm:whitespace-nowrap">
            {m.accueil_concours_2()}{" "}
            <span className="inline-block -rotate-2 whitespace-nowrap rounded-2xl bg-sun px-3 py-0.5 text-ink shadow-[0_12px_30px_-8px] shadow-black/40">
              {m.accueil_concours_somme()}
            </span>
          </span>
        </h2>

        <a
          href={lien("/certification")}
          className="btn-fx flex h-12 items-center justify-center whitespace-nowrap rounded-full bg-primary px-6 text-sm font-bold text-primary-foreground shadow-card sm:text-[15px] lg:h-14 lg:px-8"
        >
          {m.accueil_concours_action()}
        </a>
      </div>
    </section>
  );
}

// Le lecteur YouTube se pilote par messages (API IFrame).
const commande = (lecteur: HTMLIFrameElement | null, func: string, args: unknown[] = []) =>
  lecteur?.contentWindow?.postMessage(
    JSON.stringify({ event: "command", func, args }),
    "https://www.youtube-nocookie.com",
  );

// Les sous-titres automatiques se chargent avec la lecture, un peu après le lecteur : on les retire à plusieurs reprises au démarrage.
const sansSousTitres = (lecteur: HTMLIFrameElement | null) =>
  [500, 2000, 5000].forEach((t) =>
    setTimeout(() => {
      commande(lecteur, "unloadModule", ["captions"]);
      commande(lecteur, "unloadModule", ["cc"]);
    }, t),
  );

function Index() {
  const { dre } = Route.useLoaderData();
  const [active, setActive] = useState(0);
  const [son, setSon] = useState(false);
  const lecteur = useRef<HTMLIFrameElement>(null);
  const diapositives = heroSlides();
  const univers7 = univers();
  const count = diapositives.length;

  useEffect(() => {
    if (son) return;
    const t = setInterval(() => setActive((a) => (a + 1) % count), 6000);
    return () => clearInterval(t);
  }, [active, count, son]);

  // La vidéo démarre muette ; le bouton coupe ou rétablit le son.
  const basculerSon = () => {
    commande(lecteur.current, son ? "mute" : "unMute");
    setSon(!son);
  };
  // Le lecteur peut finir de charger avant l'hydratation : son onLoad serait alors perdu.
  useEffect(() => sansSousTitres(lecteur.current), []);
  const changer = (i: number) => {
    if (son) basculerSon();
    setActive(i);
  };

  return (
    <div className="min-h-screen overflow-x-clip bg-carnet text-ink">
      <SiteMotion />
      <SiteHeader />

      {/* Hero : un fond coloré propre à chaque slide, la photo dans un cadre arrondi et des flèches sur les bords. */}
      <section className="relative isolate flex min-h-[80vh] flex-col justify-center overflow-hidden text-white">
        {diapositives.map((s, i) => (
          <div
            key={i}
            aria-hidden
            className={`absolute inset-0 -z-10 bg-linear-to-br ${s.fond} transition-opacity duration-700 ${i === active ? "opacity-100" : "opacity-0"}`}
          />
        ))}
        <div aria-hidden className="pointer-events-none absolute inset-0 -z-10">
          <div className="absolute inset-0 bg-[radial-gradient(oklch(1_0_0/0.14)_1.5px,transparent_1.5px)] bg-size-[22px_22px] [mask-image:linear-gradient(to_right,black,transparent_60%)] motion-safe:animate-defile-motif" />
          <div className="absolute -right-48 -top-48 size-[44rem] rounded-full border-[3.5rem] border-white/5 motion-safe:animate-respire" />
          <div className="absolute -right-12 -top-16 size-[26rem] rounded-full border-2 border-dashed border-white/15 motion-safe:animate-[spin_60s_linear_infinite]" />
          <div className="absolute -bottom-32 -left-24 size-[22rem] rounded-full bg-white/5 motion-safe:animate-derive" />
        </div>
        <DecorAnime />

        <div className="mx-auto grid w-full max-w-7xl items-center gap-10 px-5 pb-52 pt-8 sm:pb-48 lg:grid-cols-[1.05fr_1fr] lg:gap-16 lg:pt-16 xl:px-16 xl:pb-36">
          {/* Toutes les slides partagent la même cellule : la hauteur reste celle de la plus longue. */}
          <div className="grid">
            {diapositives.map((s, i) => {
              const Heading = i === 0 ? "h1" : "h2";
              return (
                <div
                  key={i}
                  aria-hidden={i !== active}
                  className={`col-start-1 row-start-1 ${heroFade(i === active)}`}
                >
                  <p className="mb-4 inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1 text-sm font-bold backdrop-blur-sm">
                    <span className="size-2 rounded-full bg-sun" />
                    {s.onglet}
                  </p>
                  <Heading className="text-4xl leading-[0.95] min-[360px]:text-[2.625rem] sm:text-[3.25rem] lg:text-[4rem]">
                    {s.lines.map((l, j) => (
                      <span key={l}>
                        <span className={j === 0 ? "text-white" : "text-sun"}>{l}</span>
                        <br />
                      </span>
                    ))}
                  </Heading>
                  {s.tagline && (
                    <p className="mt-4 hidden text-lg font-extrabold sm:block md:text-xl">
                      {s.tagline}
                    </p>
                  )}
                  <p className="mt-3 font-semibold text-white/80 md:text-lg">{s.sub}</p>
                  <div className="mt-7 flex flex-wrap gap-3">
                    {s.cta.map((c, j) => (
                      <a
                        key={c.t}
                        href={lien(c.href)}
                        className={`btn-fx group flex h-12 w-60 items-center justify-center gap-2 whitespace-nowrap rounded-full px-4 text-[15px] font-bold ${j === 0 ? "bg-primary text-primary-foreground shadow-card" : "border-2 border-white/60 bg-white/10 backdrop-blur-sm"}`}
                      >
                        {c.t}{" "}
                        <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
                      </a>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Sur mobile la photo passe en premier : la hauteur réservée au texte le plus long se retrouve avant les flèches, pas entre le texte et la photo. */}
          <div className="relative order-first mx-auto w-full max-w-md sm:max-w-lg lg:order-none lg:max-w-none">
            {diapositives.map((s, i) => (
              <div
                key={i}
                aria-hidden
                className={`absolute inset-0 translate-x-3 translate-y-3 rotate-2 rounded-3xl transition-opacity duration-700 sm:translate-x-5 sm:translate-y-5 ${s.accent} ${i === active ? "opacity-100" : "opacity-0"}`}
              />
            ))}
            {/* La nouvelle photo arrive par-dessus l'ancienne, qui ne s'efface qu'ensuite. Elle avance lentement pendant son affichage, et ne revient à sa taille qu'une fois invisible. */}
            <div className="relative isolate aspect-video overflow-hidden rounded-3xl shadow-2xl ring-4 ring-white/25">
              {diapositives.map((s, i) => (
                <img
                  key={i}
                  src={s.img}
                  alt={s.alt}
                  width={1600}
                  height={912}
                  aria-hidden={i !== active}
                  className={`absolute inset-0 h-full w-full object-cover ${s.cadrage} ${i === active ? "z-10 scale-105 opacity-100 [transition:opacity_700ms_ease-in-out,scale_7000ms_linear]" : "scale-100 opacity-0 [transition:opacity_500ms_ease-in-out_300ms,scale_0s_linear_800ms]"}`}
                />
              ))}
              {/* Le cadre est en 16/9, comme la vidéo : elle s'affiche en entier, sans rognage. */}
              {diapositives.map(
                (s, i) =>
                  s.video && (
                    <iframe
                      key={s.video}
                      ref={lecteur}
                      onLoad={(e) => sansSousTitres(e.currentTarget)}
                      src={`https://www.youtube-nocookie.com/embed/${s.video}?autoplay=1&mute=1&loop=1&playlist=${s.video}&controls=0&rel=0&playsinline=1&modestbranding=1&cc_load_policy=0&iv_load_policy=3&disablekb=1&fs=0&enablejsapi=1`}
                      title={m.accueil_video_titre()}
                      allow="autoplay; encrypted-media; picture-in-picture"
                      tabIndex={-1}
                      aria-hidden={i !== active}
                      className={`pointer-events-none absolute inset-0 size-full transition-opacity duration-700 ${i === active ? "z-20 opacity-100" : "opacity-0"}`}
                    />
                  ),
              )}
              {diapositives[active]?.video && (
                <button
                  type="button"
                  onClick={basculerSon}
                  aria-pressed={son}
                  className="absolute bottom-4 right-4 z-30 inline-flex items-center gap-2 rounded-full bg-night/70 px-4 py-2 text-sm font-bold backdrop-blur-sm transition hover:bg-night"
                >
                  {son ? <VolumeX className="size-4" /> : <Volume2 className="size-4" />}
                  {son ? m.accueil_couper_son() : m.accueil_activer_son()}
                </button>
              )}
            </div>
            {/* La slide de la vidéo n'a pas de mascotte : rien ne vient la masquer. */}
            {diapositives.map(
              (s, i) =>
                s.mascot && (
                  <img
                    key={i}
                    src={s.mascot.src}
                    alt={s.mascot.alt}
                    width={s.mascot.width}
                    height={s.mascot.height}
                    aria-hidden={i !== active}
                    className={`absolute bottom-0 left-1 w-24 drop-shadow-2xl motion-safe:animate-float sm:-left-4 sm:w-40 lg:-bottom-12 lg:-left-16 lg:w-56 ${heroFade(i === active)}`}
                  />
                ),
            )}
          </div>
        </div>

        {/* Flèches centrées sur les bords à partir de 1280 px ; en dessous, elles passent en bas, au-dessus du bandeau de certification qui chevauche le hero. */}
        <button
          aria-label={m.accueil_precedente()}
          onClick={() => changer((active - 1 + count) % count)}
          className="absolute bottom-36 left-5 z-10 sm:bottom-32 flex size-10 items-center justify-center rounded-full border-2 border-white/40 bg-white/10 backdrop-blur-sm transition hover:scale-110 hover:bg-white hover:text-ink active:scale-95 xl:bottom-auto xl:left-4 xl:top-1/2 xl:-translate-y-1/2"
        >
          <ChevronLeft className="h-5 w-5" />
        </button>
        <button
          aria-label={m.accueil_suivante()}
          onClick={() => changer((active + 1) % count)}
          className="absolute bottom-36 right-5 z-10 sm:bottom-32 flex size-10 items-center justify-center rounded-full border-2 border-white/40 bg-white/10 backdrop-blur-sm transition hover:scale-110 hover:bg-white hover:text-ink active:scale-95 xl:bottom-auto xl:right-4 xl:top-1/2 xl:-translate-y-1/2"
        >
          <ChevronRight className="h-5 w-5" />
        </button>
      </section>

      <JeuConcours />
      <ObjectifProgramme />

      {/* Univers */}
      <section id="univers" className="mx-auto max-w-7xl px-5 py-20">
        <div data-reveal className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <h2 className="text-4xl md:text-5xl">
              <span className="text-logo-blue">{m.accueil_axes_1()}</span>{" "}
              <span className="text-primary">{m.accueil_axes_2()}</span>
            </h2>
            <p className="mt-2 text-muted-foreground">{m.accueil_axes_texte()}</p>
          </div>
          <a
            href={lien("/les-7-axes")}
            className="group font-bold text-primary underline transition hover:brightness-90"
          >
            {m.accueil_axes_decouvrir()}{" "}
            <span className="inline-block transition-transform group-hover:translate-x-1">→</span>
          </a>
        </div>
        {/* 4 cartes puis 3 centrées : chaque carte couvre 2 colonnes sur 8, et la 5e commence à la 2e colonne. */}
        <div className="mx-auto mt-8 grid max-w-sm gap-6 sm:max-w-none sm:grid-cols-4 lg:grid-cols-8">
          {univers7.map((u, i) => (
            <CarteAxe key={u.t} u={u} i={i} />
          ))}
        </div>
      </section>

      <QuelAxe />
      <ClubsSection liste={dre} />
      <PodiumClubs />
      <BandeAxes />
      <ActualitesSection />
      <CampagnesSection />
      <GalerieSection />
      <PartenairesSection />
      <TemoignagesSection />
      <InitiateurSection />

      <SiteFooter />
      <BulleDefi />
    </div>
  );
}
