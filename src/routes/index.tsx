import { useState, useEffect, useRef } from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
import * as NavigationMenuPrimitive from "@radix-ui/react-navigation-menu";
import {
  ArrowRight,
  Play,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  Earth,
  Pyramid,
  RotateCw,
  Sparkles,
  Trophy,
  Menu,
  HeartPulse,
  Users,
  School,
  Backpack,
  MapPinned,
  SearchCheck,
  Landmark,
} from "lucide-react";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Sheet, SheetClose, SheetContent, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { ClubsSection } from "@/components/ClubsSection";
import { AgendaSidebar } from "@/components/AgendaSidebar";
import { PartenairesSection } from "@/components/PartenairesSection";
import { GalerieSection } from "@/components/GalerieSection";
import { InitiateurSection } from "@/components/InitiateurSection";
import { TemoignagesSection } from "@/components/TemoignagesSection";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteMotion, retard } from "@/components/SiteMotion";
import hero from "@/assets/hero.jpg";
import { useMoi } from "@/hooks/use-moi";
import logo from "@/assets/logo.webp";
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
      { title: "Club Santé SOS Docteur TV — Ton club, tes talents, tes défis" },
      {
        name: "description",
        content: "Apprends, joue et fais bouger ton établissement avec les Clubs Santé du Togo.",
      },
      { property: "og:title", content: "Club Santé SOS Docteur TV" },
      {
        property: "og:description",
        content: "Apprends, joue et fais bouger ton établissement avec les Clubs Santé du Togo.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Index,
});

// Les 7 axes stratégiques. `t` : nom de l'axe, au dos de la carte ; `s` : slogan ; `c` : couleur de la carte.
const univers = [
  {
    t: "Académie GENIE IMHOTEP : jeu de culture générale en santé publique dans les collèges et lycées du Togo",
    s: "Génie Imhotep, c’est ici et maintenant",
    c: "bg-sky",
    img: mascotteImhotep,
  },
  {
    t: "Sensibilisation, Information et Communication sur l’éducation aux valeurs et à la santé sexuelle (EVSS), les Journées Mondiales en lien avec la Santé (JMS)",
    s: "EVSS, Un élève bien informé est un élève serein et engagé dans sa communauté",
    c: "bg-rose",
    img: mascotteValeurs,
  },
  {
    t: "Production et diffusion des émissions de santé par les élèves sur SOS DOCTEUR TV",
    s: "La voix des jeunes au cœur des ondes de santé",
    c: "bg-grape",
    img: mascotteMedias,
  },
  {
    t: "Organisation et soutien des activités sportives, culturelles et de secourisme dans les établissements scolaires",
    s: "Un esprit sain dans un corps sain et agile",
    c: "bg-tangerine",
    img: mascotteSecourisme,
  },
  {
    t: "Bourses d’excellence, gamification, parrainage des orphelins et distinctions des meilleurs acteurs",
    s: "L’excellence récompensée, l’émulation stimulée",
    c: "bg-sun",
    img: mascotteBourses,
  },
  {
    t: "Développement personnel, leadership transformationnel, promotion du genre et mentorat",
    s: "Oser grandir, inspirer et diriger avec intégrité",
    c: "bg-bark",
    img: mascotteLeadership,
  },
  {
    t: "Promotion de la santé, cadre de vie et cohésion sociale (Santé environnementale, nutrition & PEVPAH)",
    s: "Un environnement scolaire sain pour une jeunesse épanouie",
    c: "bg-leaf",
    img: mascotteEnvironnement,
  },
];

// Socle et valeurs du programme. `c` : fond de l'icône et filet du bas ; `tc` : couleur du mot clé.
const valeurs = [
  {
    i: Sparkles,
    mot: "Confiance",
    titre: "Découverte et confiance en soi",
    d: "École, un lieu de révélation de talents et de vocations & Leadership transformationnel",
    c: "bg-logo-blue",
    tc: "text-logo-blue",
  },
  {
    i: Earth,
    mot: "Citoyenneté",
    titre: "Culture de la citoyenneté et du panafricanisme",
    d: "Engagement citoyen et Ouverture sur l’Afrique",
    c: "bg-primary",
    tc: "text-primary",
  },
  {
    i: Pyramid,
    mot: "Bâtisseur",
    titre: "Esprit bâtisseur et polyvalence (Imhotep)",
    d: "Innovation & Impact communautaire",
    c: "bg-tangerine",
    tc: "text-tangerine",
  },
];

// `plus` : le chiffre est un minimum, affiché « +800 ». Grille bento : l'ordre remplit la grille ligne par ligne,
// `place` fixe l'emprise de la case (2 colonnes sur mobile, 4 sur grand écran) et `taille` celle du chiffre.
const chiffresCles = [
  {
    plus: true,
    n: 800,
    t: "Clubs de santé actifs",
    i: HeartPulse,
    place: "col-span-2 lg:row-span-2",
    fond: "bg-linear-to-br from-logo-blue to-night text-white",
    chiffre: "text-primary",
    taille: "text-7xl md:text-8xl lg:text-9xl",
  },
  {
    plus: true,
    n: 3500,
    t: "Encadreurs pédagogiques & pairs éducateurs",
    i: Users,
    place: "col-span-2",
    fond: "bg-primary text-white",
    chiffre: "",
    taille: "text-5xl md:text-6xl",
  },
  {
    plus: true,
    n: 2396,
    t: "Établissements du secondaire 1",
    i: Backpack,
    place: "",
    fond: "bg-sun text-ink",
    chiffre: "",
    taille: "text-4xl md:text-5xl",
  },
  {
    plus: true,
    n: 714,
    t: "Établissements du secondaire 2",
    i: School,
    place: "",
    fond: "bg-mist text-ink",
    chiffre: "text-logo-blue",
    taille: "text-4xl md:text-5xl",
  },
  {
    plus: false,
    n: 7,
    t: "Directions régionales de l'éducation",
    i: MapPinned,
    place: "",
    fond: "bg-card text-ink ring-1 ring-logo-blue/15",
    chiffre: "text-logo-blue",
    taille: "text-4xl md:text-5xl",
  },
  {
    plus: false,
    n: 18,
    t: "Inspections pédagogiques",
    i: SearchCheck,
    place: "",
    fond: "bg-tangerine text-white",
    chiffre: "",
    taille: "text-4xl md:text-5xl",
  },
  {
    plus: false,
    n: 1,
    t: "Cabinet ministériel",
    i: Landmark,
    place: "col-span-2",
    fond: "bg-logo-red text-white",
    chiffre: "",
    taille: "text-5xl md:text-6xl",
  },
];

// Le rendu serveur affiche le vrai chiffre (sans JavaScript, ou si l'utilisateur limite les animations) ; le compte part de 0 quand le chiffre devient visible.
function Compteur({ value }: { value: number }) {
  const [current, setCurrent] = useState(value);
  const ref = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    setCurrent(0);
    let frame = 0;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (!entry?.isIntersecting) return;
        observer.disconnect();
        const start = performance.now();
        const tick = (now: number) => {
          const p = Math.min(Math.max(now - start, 0) / 1800, 1);
          setCurrent(Math.round(value * (1 - (1 - p) ** 3)));
          if (p < 1) frame = requestAnimationFrame(tick);
        };
        frame = requestAnimationFrame(tick);
      },
      { threshold: 0.5 },
    );
    observer.observe(el);
    return () => {
      observer.disconnect();
      cancelAnimationFrame(frame);
    };
  }, [value]);

  return <span ref={ref}>{String(current).replace(/\B(?=(\d{3})+$)/g, " ")}</span>;
}

// Section Actualités : un article à la une, puis les autres en ligne.
const aLaUne = {
  img: grandesFinales,
  tag: "Génie Imhotep",
  t: "Grandes finales du Championnat national Génie Imhotep",
  d: "Retour sur la 1re édition : champions, finalistes et demi-finalistes des clubs santé récompensés sur scène.",
};

const stars = [
  {
    img: story2,
    tag: "TV & Médias",
    tc: "bg-grape",
    t: "Les lycéens en action !",
    d: "Reportage du Club Santé du Lycée de Lomé sur la prévention du paludisme.",
  },
  {
    img: story1,
    tag: "Sports & Secourisme",
    tc: "bg-tangerine",
    t: "Apprendre aujourd'hui, sauver des vies demain !",
    d: "Initiation aux premiers secours avec les clubs santé.",
  },
  {
    img: hero,
    tag: "Vie des clubs",
    tc: "bg-leaf",
    t: "Une journée verte pour un meilleur cadre de vie",
    d: "Les clubs se mobilisent pour l'environnement.",
  },
];

// `onglet` : nom court affiché en étiquette au-dessus du titre. `fond` : dégradé de la section, assez sombre pour le texte blanc.
// `accent` : couleur du cadre décalé derrière la photo. `cadrage` : point de la photo à garder visible.

const heroSlides = [
  {
    img: slideMascottes,
    onglet: "Mascottes",
    fond: "from-logo-blue to-grape",
    accent: "bg-sun",
    cadrage: "object-[50%_25%]",
    alt: "Remise du trophée de champion national Génie Imhotep 2026 à une élève en t-shirt orange",
    mascot: {
      src: mascottesAxes,
      alt: "Quatre mascottes caméléons avec une caméra, un mégaphone et un arrosoir",
      width: 1122,
      height: 1402,
    },
    lines: ["DÉCOUVRE NOS", "MASCOTTES !"],
    cta: [
      { t: "Découvrir les mascottes", href: "#" },
      { t: "Obtenir ma certification", href: "#" },
    ],
    sub: "Découvre les mascottes qui accompagnent les jeunes à apprendre, créer, s’engager et révéler leurs talents.",
  },
  {
    img: slideClubs,
    onglet: "Clubs Santé",
    fond: "from-night to-logo-blue",
    accent: "bg-primary",
    cadrage: "object-center",
    alt: "Jeunes des Clubs Santé en t-shirt blanc, affiches à la main, salués par un responsable",
    mascot: {
      src: mascottesLivres,
      alt: "Deux mascottes caméléons, l'une brune et l'autre bleue, entourées de livres",
      width: 1122,
      height: 1402,
    },
    lines: ["CLUBS SANTÉ", "SOS DOCTEUR TV"],
    cta: [
      { t: "Rejoindre un club", href: "#" },
      { t: "Découvrir les clubs", href: "#" },
    ],
    tagline: "Ensemble pour une génération de jeunes en bonne santé, responsables et épanouie",
    sub: "Les Clubs Santé SOS DOCTEUR TV réunissent des milliers de jeunes engagés pour la santé, le leadership, l'excellence et la citoyenneté active au Togo.",
  },
  {
    img: slideGenie,
    onglet: "Génie Imhotep",
    fond: "from-grape to-night",
    accent: "bg-tangerine",
    cadrage: "object-center",
    alt: "Trois élèves du Collège St. Joseph en polo bleu au pupitre de Génie Imhotep",
    mascot: {
      src: mascottesVs,
      alt: "Deux mascottes caméléons, l'une bleue et l'autre violette, face à un grand VS doré",
      width: 2000,
      height: 2000,
    },
    lines: ["GÉNIE", "IMHOTEP"],
    cta: [
      { t: "Lancer le quiz", href: "#" },
      { t: "Voir la carte", href: "#clubs" },
    ],
    tagline: "C’est ici et maintenant",
    sub: "La grande compétition de culture générale en santé publique dans les collèges et lycées du Togo et sur la chaîne SOS DOCTEUR TV !",
  },
  {
    img: slideAxes,
    onglet: "7 axes",
    fond: "from-logo-blue to-night",
    accent: "bg-sky",
    cadrage: "object-center",
    alt: "Élèves qui applaudissent et agitent le drapeau togolais",
    mascot: {
      src: mascottesAxes,
      alt: "Quatre mascottes caméléons avec une caméra, un mégaphone et un arrosoir",
      width: 1122,
      height: 1402,
    },
    lines: ["7 AXES", "STRATÉGIQUES"],
    cta: [
      { t: "Découvrir les 7 axes", href: "#univers" },
      { t: "Bibliothèque", href: "#" },
    ],
    tagline: "Conçus pour permettre aux élèves de mener leurs activités de façon autonome.",
    sub: "Conçus pour permettre aux élèves de mener leurs activités de façon autonome : découvre les programmes d'action concrets de l'hygiène au secourisme, de la nutrition à la santé mentale dans chaque établissement.",
  },
];

// Ces pages n'existent pas encore : les liens sans `href` pointent vers « # ».
const menu: { t: string; items: { t: string; href?: string }[] }[] = [
  {
    t: "Vie du club",
    items: [
      { t: "Club santé" },
      { t: "Les 7 axes", href: "#univers" },
      { t: "Cartes des clubs", href: "#clubs" },
      { t: "Bibliothèques" },
    ],
  },
  { t: "Génie Imhotep", items: [{ t: "Hall of Fame" }, { t: "Inscription" }] },
  { t: "Gamification", items: [{ t: "Jeux" }, { t: "Certification" }] },
  { t: "Actualités", items: [{ t: "Agenda", href: "#agenda" }, { t: "Magazine" }] },
];

// Le contenu sortant s'efface vite, puis le suivant apparaît : les deux ne se superposent jamais.
const heroFade = (on: boolean) =>
  `transition-[opacity,visibility,translate] ease-out ${on ? "translate-y-0 opacity-100 duration-500 delay-200" : "invisible translate-y-3 opacity-0 duration-200"}`;

const defi = {
  options: ["Dormir sous une moustiquaire", "Boire beaucoup d'eau", "Éviter les fruits la nuit"],
  bonne: 0,
};

function DefiDuJour() {
  const [choix, setChoix] = useState<number | null>(null);
  const [valide, setValide] = useState(false);
  const couleur = (i: number) => {
    if (valide && i === defi.bonne) return "border-leaf bg-leaf text-primary-foreground";
    if (valide && i === choix)
      return "animate-shake border-logo-red bg-logo-red text-primary-foreground";
    if (i === choix) return "border-logo-blue bg-logo-blue text-primary-foreground";
    return valide
      ? "border-border opacity-60"
      : "border-border hover:-translate-y-0.5 hover:border-logo-blue";
  };
  const pastille = (i: number) =>
    (valide && i === defi.bonne) || i === choix ? "bg-white/25" : "bg-mist text-logo-blue";

  return (
    <section
      id="defi"
      className="relative isolate scroll-mt-16 overflow-hidden bg-logo-blue text-primary-foreground"
    >
      <div className="absolute -left-16 -top-16 -z-10 h-72 w-72 rounded-full bg-sky/40 blur-3xl" />
      <div className="absolute -bottom-24 right-0 -z-10 h-80 w-80 rounded-full bg-primary/25 blur-3xl" />
      <div className="mx-auto grid max-w-7xl px-5 lg:grid-cols-[1fr_2fr]">
        <img
          src={mascotteBourses}
          alt="Mascotte du Club Santé brandissant un trophée"
          loading="lazy"
          width={1414}
          height={2000}
          data-reveal="left"
          className="order-last mx-auto h-auto w-full max-w-60 pb-8 drop-shadow-2xl lg:order-first lg:max-w-sm lg:self-center lg:py-10"
        />
        <div className="py-12 md:py-16 lg:pl-8">
          <h2 data-reveal className="text-4xl md:text-5xl">
            Le défi <span className="text-sun">du jour</span>
          </h2>
          <p data-reveal className="mt-3 max-w-2xl text-lg font-medium text-white/85">
            Une nouvelle question santé chaque jour : teste tes connaissances et gagne des points !
          </p>

          <div
            data-reveal="zoom"
            className="mt-8 rounded-[2rem] bg-card p-6 text-foreground shadow-card md:p-8"
          >
            <div className="flex flex-wrap items-center gap-2">
              <span className="rounded-full bg-rose px-3 py-1 text-xs font-extrabold uppercase text-primary-foreground">
                Santé & bien-être
              </span>
              <span className="rounded-full bg-sun px-3 py-1 text-xs font-extrabold uppercase text-ink">
                Question du jour
              </span>
            </div>
            <p className="mt-4 font-display text-2xl leading-tight text-logo-blue md:text-3xl">
              Quelle est la meilleure façon de se protéger contre le paludisme ?
            </p>

            <div className="mt-6 grid gap-3 md:grid-cols-3">
              {defi.options.map((o, i) => (
                <button
                  key={o}
                  type="button"
                  disabled={valide}
                  aria-pressed={i === choix}
                  onClick={() => setChoix(i)}
                  className={`flex items-center gap-3 rounded-2xl border-2 p-3 text-left font-bold transition duration-200 active:scale-95 ${couleur(i)}`}
                >
                  <span
                    className={`inline-flex size-9 shrink-0 items-center justify-center rounded-xl font-display text-lg ${pastille(i)}`}
                  >
                    {"ABC"[i]}
                  </span>
                  {o}
                </button>
              ))}
            </div>

            <div className="mt-6 flex flex-wrap items-center justify-between gap-4">
              <p role="status" className="text-sm font-bold">
                {valide &&
                  (choix === defi.bonne
                    ? "Bravo, c'est la bonne réponse !"
                    : "Pas tout à fait : la bonne réponse est en vert.")}
              </p>
              {valide ? (
                <button
                  type="button"
                  onClick={() => {
                    setValide(false);
                    setChoix(null);
                  }}
                  className="btn-fx ml-auto rounded-full bg-primary px-8 py-3 font-bold text-primary-foreground"
                >
                  Rejouer
                </button>
              ) : (
                <button
                  type="button"
                  disabled={choix === null}
                  onClick={() => setValide(true)}
                  className="btn-fx ml-auto rounded-full bg-primary px-8 py-3 font-bold text-primary-foreground disabled:opacity-50"
                >
                  Valider
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

// Carte d'un axe : la mascotte au recto, la description et le slogan au verso.
// À la souris, le survol la retourne ; au toucher et au clavier, chaque appui la retourne et la laisse ainsi.
function CarteAxe({ u, i }: { u: (typeof univers)[number]; i: number }) {
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
          {/* Seul indice au recto, sans texte : la carte se retourne. */}
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
            Axe {i + 1}
          </span>
          <h3 className="relative mt-4 flex-1 font-sans text-lg font-extrabold leading-snug lg:text-base xl:text-lg">
            {u.t}
          </h3>
          <p className="relative font-hand text-2xl leading-tight text-sun lg:text-xl xl:text-2xl">
            « {u.s} »
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
          <span className="text-logo-blue">Objectif</span>{" "}
          <span className="text-primary">du programme</span>
        </h2>
        <p className="mt-3 max-w-4xl text-lg font-medium text-muted-foreground">
          Mobiliser les apprenants autour de 5 entités clés à savoir : la redynamisation de la vie
          scolaire ; la promotion de la santé dès le bas âge ; la culture de l’excellence et
          l’émulation ; la responsabilité et la citoyenneté pour un épanouissement intégral des
          élèves.
        </p>
      </div>

      <h3
        data-reveal
        className="mt-12 flex items-center gap-3 font-sans text-sm font-extrabold uppercase tracking-widest text-logo-blue"
      >
        <span className="h-1 w-8 rounded-full bg-primary" />
        Socle & valeurs du programme
      </h3>
      <div className="mt-6 grid gap-6 md:grid-cols-3">
        {valeurs.map((v, i) => (
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
        Chiffres clés du réseau national
      </h3>
      <ul className="mt-8 grid grid-cols-2 gap-4 md:gap-5 lg:auto-rows-[minmax(12.5rem,auto)] lg:grid-cols-4">
        {chiffresCles.map((c, i) => (
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
  return (
    <section id="actualites" className="mx-auto max-w-7xl scroll-mt-16 px-5 pb-12 pt-20">
      <div data-reveal>
        <h2 className="text-4xl md:text-5xl">
          <span className="text-logo-blue">Actualités</span>{" "}
          <span className="text-primary">des clubs</span>
        </h2>
        <p className="mt-3 max-w-2xl text-lg font-medium text-muted-foreground">
          Les talents des jeunes, les temps forts et les prochains rendez-vous des Clubs Santé.
        </p>
      </div>

      <div className="mt-10 grid gap-8 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <div data-reveal className="flex flex-wrap items-end justify-between gap-x-6 gap-y-1">
            <h3 className="text-3xl">
              <span className="text-logo-blue">C'est toi</span>{" "}
              <span className="text-primary">la star !</span>
            </h3>
            <a href="#" className="group flex items-center gap-1.5 font-bold text-logo-blue">
              Toutes les actus
              <ArrowRight className="size-4 transition-transform duration-300 group-hover:translate-x-1" />
            </a>
          </div>

          <article
            data-reveal="zoom"
            className="group relative isolate mt-5 flex min-h-[28rem] items-end overflow-hidden rounded-[2rem] shadow-card md:aspect-video md:min-h-0"
          >
            <img
              src={aLaUne.img}
              alt=""
              loading="lazy"
              width={2000}
              height={963}
              className="absolute inset-0 -z-20 size-full object-cover transition duration-1000 group-hover:scale-105"
            />
            <div className="absolute inset-0 -z-10 bg-linear-to-t from-night from-15% via-night/50 to-transparent" />
            <span className="absolute left-5 top-5 inline-flex items-center gap-1.5 rounded-full bg-sun px-3 py-1.5 text-xs font-extrabold uppercase text-ink shadow-card">
              <Sparkles className="size-3.5" /> À la une
            </span>
            <div className="p-6 text-white md:p-9">
              <span className="rounded-full border border-white/40 bg-white/10 px-3 py-1 text-xs font-extrabold uppercase backdrop-blur">
                {aLaUne.tag}
              </span>
              <h4 className="mt-4 max-w-xl font-display text-3xl leading-tight md:text-4xl">
                {aLaUne.t}
              </h4>
              <p className="mt-2 max-w-lg font-medium text-white/80">{aLaUne.d}</p>
              <a
                href="#"
                className="btn-fx mt-5 inline-flex items-center gap-2 rounded-full bg-primary px-6 py-3 text-[15px] font-bold after:absolute after:inset-0"
              >
                Lire l'article <ArrowRight className="size-4" />
              </a>
            </div>
          </article>

          <div className="mt-5 grid gap-4 sm:grid-cols-3 md:gap-5">
            {stars.map((s, i) => (
              <article
                key={s.t}
                data-reveal
                style={retard(i)}
                className="card-fx group relative flex gap-4 rounded-3xl bg-card p-2.5 shadow-card sm:flex-col sm:gap-0"
              >
                <div className="relative w-28 shrink-0 overflow-hidden rounded-2xl sm:w-auto">
                  <img
                    src={s.img}
                    alt=""
                    loading="lazy"
                    className="aspect-square w-full object-cover object-right transition duration-500 group-hover:scale-110 sm:aspect-[4/3]"
                  />
                  <span className="absolute bottom-2 right-2 rounded-full bg-primary p-2 text-primary-foreground transition duration-300 group-hover:scale-110">
                    <Play className="size-3.5 fill-current" />
                  </span>
                </div>
                <div className="flex flex-1 flex-col py-1 pr-2 sm:p-3 sm:pt-4">
                  <span
                    className={`${s.tc} self-start rounded-full px-2.5 py-0.5 text-[11px] font-extrabold uppercase text-primary-foreground`}
                  >
                    {s.tag}
                  </span>
                  <h4 className="mt-2 font-sans font-extrabold leading-snug">
                    <a href="#" className="after:absolute after:inset-0">
                      {s.t}
                    </a>
                  </h4>
                  <p className="mt-1 line-clamp-2 text-sm text-muted-foreground max-sm:hidden">
                    {s.d}
                  </p>
                </div>
              </article>
            ))}
          </div>
        </div>

        <AgendaSidebar />
      </div>
    </section>
  );
}

// Carte du jeu concours, à cheval sur le bas du hero : le liseré blanc la détache du fond coloré.
function JeuConcours() {
  return (
    <section className="mx-auto -mt-6 max-w-7xl px-5">
      <div
        data-reveal
        className="relative isolate overflow-hidden rounded-3xl bg-linear-to-br from-logo-blue via-logo-blue to-night p-5 text-white sm:p-6 shadow-card ring-4 ring-white md:p-10"
      >
        <div aria-hidden className="pointer-events-none absolute inset-0 -z-10">
          <div className="absolute -right-24 -top-24 size-80 rounded-full bg-sun/25 blur-3xl" />
          <div className="absolute -bottom-32 left-1/3 size-80 rounded-full bg-primary/25 blur-3xl" />
          <div className="absolute inset-0 bg-[radial-gradient(oklch(1_0_0/0.1)_1.5px,transparent_1.5px)] bg-size-[22px_22px] [mask-image:linear-gradient(to_bottom,black,transparent)]" />
          <Trophy className="absolute -bottom-10 -right-6 size-72 -rotate-12 text-white/5 md:size-96" />
        </div>

        <h2 className="text-[1.75rem] uppercase leading-[1.05] min-[400px]:text-4xl md:text-6xl">
          Obtiens ta <span className="text-primary">certification</span> & gagne jusqu'à{" "}
          <span className="mt-2 inline-block -rotate-2 whitespace-nowrap rounded-2xl bg-linear-to-r from-sun to-tangerine px-3 py-1 text-ink sm:px-4 shadow-[0_12px_30px_-8px] shadow-tangerine/70">
            1 million FCFA !
          </span>
        </h2>

        <div className="mt-8 grid items-center gap-6 lg:grid-cols-[1.3fr_1fr]">
          <div>
            <p className="text-lg font-bold md:text-xl">
              Inscription 100 % gratuite, ouverte à tous les élèves des Clubs Santé ainsi qu'aux
              visiteurs et particuliers du Togo.
            </p>
          </div>
          <div className="flex flex-col gap-3 sm:flex-row lg:flex-col lg:items-end">
            <a
              href="#"
              className="btn-fx group flex h-12 items-center justify-center gap-2 whitespace-nowrap rounded-full bg-primary px-4 text-sm font-bold text-primary-foreground shadow-card sm:px-6 sm:text-[15px] lg:w-88"
            >
              <Trophy className="hidden h-5 w-5 sm:block" />
              Obtenir ma certification & jouer
              <ArrowRight className="hidden h-4 w-4 transition-transform group-hover:translate-x-1 sm:block" />
            </a>
            <a
              href="#"
              className="btn-fx flex h-12 items-center justify-center rounded-full border-2 border-white/60 bg-white/10 px-6 lg:w-88 text-[15px] font-bold backdrop-blur-sm"
            >
              S'inscrire aux quiz
            </a>
          </div>
        </div>
      </div>
    </section>
  );
}

function Logo() {
  return (
    <img
      src={logo}
      alt="Club Santé SOS Docteur TV"
      width={1014}
      height={195}
      className="h-8 w-auto shrink-0 lg:h-11"
    />
  );
}

function SiteHeader() {
  const [lang, setLang] = useState<"FR" | "EN">("FR");
  const langSwitch = (
    <button
      aria-label={lang === "FR" ? "Passer en anglais" : "Passer en français"}
      onClick={() => setLang(lang === "FR" ? "EN" : "FR")}
      className="btn-fx rounded-full border px-3 py-2 text-sm font-bold"
    >
      <span className={lang === "FR" ? "text-logo-blue" : "text-muted-foreground"}>FR</span>
      <span className="text-muted-foreground"> / </span>
      <span className={lang === "EN" ? "text-logo-blue" : "text-muted-foreground"}>EN</span>
    </button>
  );
  const join = (
    <button className="btn-fx whitespace-nowrap rounded-full bg-primary px-5 py-2.5 text-sm font-bold text-primary-foreground">
      Rejoindre le club
    </button>
  );
  const { data: moi } = useMoi();
  const login = (
    <Link
      to={moi ? "/mon-espace" : "/connexion"}
      className="btn-fx whitespace-nowrap rounded-full border border-logo-blue px-5 py-2.5 text-center text-sm font-bold text-logo-blue hover:bg-logo-blue hover:text-primary-foreground"
    >
      {moi ? "Mon espace" : "Se connecter"}
    </Link>
  );

  return (
    <header className="sticky top-0 z-20 border-b bg-background/90 backdrop-blur transition-shadow duration-300 data-[scrolled]:shadow-lg">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-3 px-5 py-3">
        <a href="/" className="transition hover:scale-105">
          <Logo />
        </a>
        <NavigationMenuPrimitive.Root aria-label="Menu principal" className="hidden xl:block">
          <NavigationMenuPrimitive.List className="flex items-center gap-1">
            {menu.map((m) => (
              <NavigationMenuPrimitive.Item key={m.t} className="relative">
                <NavigationMenuPrimitive.Trigger className="group relative flex items-center gap-1 rounded-md px-3 py-2 text-sm font-bold transition-colors after:absolute after:inset-x-3 after:bottom-1 after:h-0.5 after:origin-left after:scale-x-0 after:rounded-full after:bg-primary after:transition-transform after:duration-300 hover:text-logo-blue hover:after:scale-x-100 data-[state=open]:text-logo-blue data-[state=open]:after:scale-x-100">
                  {m.t}{" "}
                  <ChevronDown
                    aria-hidden
                    className="h-4 w-4 transition group-data-[state=open]:rotate-180"
                  />
                </NavigationMenuPrimitive.Trigger>
                <NavigationMenuPrimitive.Content className="absolute left-0 top-full pt-2 animate-in fade-in slide-in-from-top-2 duration-200">
                  <ul className="min-w-52 rounded-2xl border bg-popover p-2 shadow-card">
                    {m.items.map((i) => (
                      <li key={i.t}>
                        <NavigationMenuPrimitive.Link
                          href={i.href ?? "#"}
                          className="block rounded-lg px-3 py-2 text-sm font-semibold transition hover:translate-x-1 hover:bg-mist hover:text-logo-blue"
                        >
                          {i.t}
                        </NavigationMenuPrimitive.Link>
                      </li>
                    ))}
                  </ul>
                </NavigationMenuPrimitive.Content>
              </NavigationMenuPrimitive.Item>
            ))}
          </NavigationMenuPrimitive.List>
        </NavigationMenuPrimitive.Root>
        <div className="flex items-center gap-3">
          <div className="hidden items-center gap-3 sm:flex">
            {join}
            {login}
            {langSwitch}
          </div>
          <Sheet>
            <SheetTrigger aria-label="Ouvrir le menu" className="rounded-full border p-2 xl:hidden">
              <Menu className="h-5 w-5" />
            </SheetTrigger>
            <SheetContent aria-describedby={undefined} className="flex flex-col overflow-y-auto">
              <SheetTitle className="text-xl text-logo-blue">Menu</SheetTitle>
              <Accordion type="single" collapsible>
                {menu.map((m) => (
                  <AccordionItem key={m.t} value={m.t}>
                    <AccordionTrigger className="text-base font-bold">{m.t}</AccordionTrigger>
                    <AccordionContent>
                      <ul>
                        {m.items.map((i) => (
                          <li key={i.t}>
                            <SheetClose asChild>
                              <a
                                href={i.href ?? "#"}
                                className="block rounded-lg px-3 py-2 font-semibold hover:bg-mist hover:text-logo-blue"
                              >
                                {i.t}
                              </a>
                            </SheetClose>
                          </li>
                        ))}
                      </ul>
                    </AccordionContent>
                  </AccordionItem>
                ))}
              </Accordion>
              <div className="mt-auto grid gap-3 pt-6 sm:hidden">
                {join}
                {login}
                {langSwitch}
              </div>
            </SheetContent>
          </Sheet>
        </div>
      </div>
    </header>
  );
}

function Index() {
  const [active, setActive] = useState(0);
  const count = heroSlides.length;
  const next = () => setActive((a) => (a + 1) % count);
  const prev = () => setActive((a) => (a - 1 + count) % count);

  useEffect(() => {
    const t = setInterval(() => setActive((a) => (a + 1) % count), 6000);
    return () => clearInterval(t);
  }, [active, count]);

  return (
    <div className="min-h-screen overflow-x-clip bg-carnet text-ink">
      <SiteMotion />
      <SiteHeader />

      {/* Hero : un fond coloré propre à chaque slide, la photo dans un cadre arrondi et des flèches sur les bords. */}
      <section className="relative isolate flex min-h-[80vh] flex-col justify-center overflow-hidden text-white">
        {heroSlides.map((s, i) => (
          <div
            key={i}
            aria-hidden
            className={`absolute inset-0 -z-10 bg-linear-to-br ${s.fond} transition-opacity duration-700 ${i === active ? "opacity-100" : "opacity-0"}`}
          />
        ))}
        <div aria-hidden className="pointer-events-none absolute inset-0 -z-10">
          <div className="absolute inset-0 bg-[radial-gradient(oklch(1_0_0/0.14)_1.5px,transparent_1.5px)] bg-size-[22px_22px] [mask-image:linear-gradient(to_right,black,transparent_60%)]" />
          <div className="absolute -right-48 -top-48 size-[44rem] rounded-full border-[3.5rem] border-white/5" />
          <div className="absolute -right-12 -top-16 size-[26rem] rounded-full border-2 border-dashed border-white/15" />
          <div className="absolute -bottom-32 -left-24 size-[22rem] rounded-full bg-white/5" />
        </div>

        <div className="mx-auto grid w-full max-w-7xl items-center gap-10 px-5 pb-24 pt-8 lg:grid-cols-[1.05fr_1fr] lg:gap-16 lg:pt-16 xl:px-16 xl:pb-20">
          {/* Toutes les slides partagent la même cellule : la hauteur reste celle de la plus longue. */}
          <div className="grid">
            {heroSlides.map((s, i) => {
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
                        href={c.href}
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
            {heroSlides.map((s, i) => (
              <div
                key={i}
                aria-hidden
                className={`absolute inset-0 translate-x-3 translate-y-3 rotate-2 rounded-[2.5rem] rounded-tl-[6rem] transition-opacity duration-700 sm:translate-x-5 sm:translate-y-5 ${s.accent} ${i === active ? "opacity-100" : "opacity-0"}`}
              />
            ))}
            {/* La nouvelle photo arrive par-dessus l'ancienne, qui ne s'efface qu'ensuite. Elle avance lentement pendant son affichage, et ne revient à sa taille qu'une fois invisible. */}
            <div className="relative isolate aspect-[16/11] overflow-hidden lg:aspect-[5/4] rounded-[2.5rem] rounded-tl-[6rem] shadow-2xl ring-4 ring-white/25">
              {heroSlides.map((s, i) => (
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
            </div>
            {heroSlides.map((s, i) => (
              <img
                key={i}
                src={s.mascot.src}
                alt={s.mascot.alt}
                width={s.mascot.width}
                height={s.mascot.height}
                aria-hidden={i !== active}
                className={`absolute bottom-0 left-1 w-24 drop-shadow-2xl motion-safe:animate-float sm:-left-4 sm:w-40 lg:-bottom-12 lg:-left-16 lg:w-56 ${heroFade(i === active)}`}
              />
            ))}
          </div>
        </div>

        {/* Flèches centrées sur les bords à partir de 1280 px ; en dessous, la marge latérale est trop étroite et elles passent en bas. */}
        <button
          aria-label="Diapositive précédente"
          onClick={prev}
          className="absolute bottom-10 left-5 z-10 flex size-10 items-center justify-center rounded-full border-2 border-white/40 bg-white/10 backdrop-blur-sm transition hover:scale-110 hover:bg-white hover:text-ink active:scale-95 xl:bottom-auto xl:left-4 xl:top-1/2 xl:-translate-y-1/2"
        >
          <ChevronLeft className="h-5 w-5" />
        </button>
        <button
          aria-label="Diapositive suivante"
          onClick={next}
          className="absolute bottom-10 right-5 z-10 flex size-10 items-center justify-center rounded-full border-2 border-white/40 bg-white/10 backdrop-blur-sm transition hover:scale-110 hover:bg-white hover:text-ink active:scale-95 xl:bottom-auto xl:right-4 xl:top-1/2 xl:-translate-y-1/2"
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
              <span className="text-logo-blue">Les 7 Axes</span>{" "}
              <span className="text-primary">Stratégiques</span>
            </h2>
            <p className="mt-2 text-muted-foreground">
              Une approche holistique pour promouvoir la santé publique et l'excellence dans les
              collèges et lycées du Togo.
            </p>
          </div>
          <a
            href="#"
            className="group font-bold text-primary underline transition hover:brightness-90"
          >
            Découvrir les 7 axes{" "}
            <span className="inline-block transition-transform group-hover:translate-x-1">→</span>
          </a>
        </div>
        {/* 4 cartes puis 3 centrées : chaque carte couvre 2 colonnes sur 8, et la 5e commence à la 2e colonne. */}
        <div className="mx-auto mt-8 grid max-w-sm gap-6 sm:max-w-none sm:grid-cols-4 lg:grid-cols-8">
          {univers.map((u, i) => (
            <CarteAxe key={u.t} u={u} i={i} />
          ))}
        </div>
      </section>

      <ClubsSection />
      <ActualitesSection />

      <DefiDuJour />

      <PartenairesSection />
      <GalerieSection />
      <InitiateurSection />
      <TemoignagesSection />

      <SiteFooter />
    </div>
  );
}
