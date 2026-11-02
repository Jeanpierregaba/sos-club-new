import { useState, useEffect, useRef } from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
import * as NavigationMenuPrimitive from "@radix-ui/react-navigation-menu";
import {
  ArrowRight,
  Users,
  Play,
  ClipboardCheck,
  Award,
  Medal,
  Gift,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  Menu,
  HeartPulse,
  GraduationCap,
  School,
  UserCheck,
} from "lucide-react";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Sheet, SheetClose, SheetContent, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { ClubsSection } from "@/components/ClubsSection";
import { AgendaSection } from "@/components/AgendaSection";
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

const univers = [
  {
    t: "Académie Génie Imhotep",
    d: "Apprendre, se former, réussir",
    c: "bg-sky",
    a: "text-sky",
    img: mascotteImhotep,
  },
  {
    t: "Santé sexuelle & valeurs",
    d: "S'informer, se respecter",
    c: "bg-rose",
    a: "text-rose",
    img: mascotteValeurs,
  },
  {
    t: "TV & Médias",
    d: "Créer, informer, partager",
    c: "bg-grape",
    a: "text-grape",
    img: mascotteMedias,
  },
  {
    t: "Sports & Secourisme",
    d: "Bouger, sauver des vies",
    c: "bg-tangerine",
    a: "text-tangerine",
    img: mascotteSecourisme,
  },
  {
    t: "Jeux & Bourses",
    d: "Jouer, gagner, saisir sa chance",
    c: "bg-sun",
    a: "text-tangerine",
    img: mascotteBourses,
  },
  {
    t: "Leadership",
    d: "S'engager, impacter",
    c: "bg-bark",
    a: "text-bark",
    img: mascotteLeadership,
  },
  {
    t: "Bien-être & Environnement",
    d: "Vivre mieux, protéger la planète",
    c: "bg-leaf",
    a: "text-leaf",
    img: mascotteEnvironnement,
  },
];

const chiffres = [
  { i: HeartPulse, n: 800, t: "Clubs de santé actifs" },
  { i: GraduationCap, n: 714, t: "Lycées" },
  { i: School, n: 2396, t: "Collèges" },
  { i: Users, n: 50000, t: "Jeunes mobilisés" },
  { i: UserCheck, n: 3500, t: "Encadreurs pédagogiques & pairs éducateurs" },
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

// `pos` : cadrage de la photo, à préciser quand le cadrage par défaut couperait le sujet.
// `fullPhoto` : photo en portrait affichée entière sur grand écran, sans le dégradé qui en masquerait la moitié.
// `place` : emplacement de la mascotte à droite ; `mobile` : son emplacement sous 768 px, selon la place laissée par le texte.

const heroSlides = [
  {
    img: slideMascottes,
    pos: "object-right-top lg:left-auto lg:w-auto lg:max-w-[50vw] lg:[mask-composite:intersect] lg:[mask-image:linear-gradient(110deg,transparent_10%,black_30%),linear-gradient(to_right,transparent,black_10%)]",
    fullPhoto: true,
    alt: "Remise du trophée de champion national Génie Imhotep 2026 à une élève en t-shirt orange",
    mascot: {
      src: mascottesAxes,
      alt: "Quatre mascottes caméléons avec une caméra, un mégaphone et un arrosoir",
      width: 1122,
      height: 1402,
      place: "-bottom-24 left-0 w-80 drop-shadow-2xl",
      mobile: "mx-auto mt-3 h-44",
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
    alt: "Jeunes des Clubs Santé en t-shirt blanc, affiches à la main, salués par un responsable",
    mascot: {
      src: mascottesLivres,
      alt: "Deux mascottes caméléons, l'une brune et l'autre bleue, entourées de livres",
      width: 1122,
      height: 1402,
      place: "-bottom-24 left-0 w-80 drop-shadow-2xl",
      mobile: "absolute inset-x-0 bottom-4 mx-auto h-24",
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
    alt: "Trois élèves du Collège St. Joseph en polo bleu au pupitre de Génie Imhotep",
    mascot: {
      src: mascottesVs,
      alt: "Deux mascottes caméléons, l'une bleue et l'autre violette, face à un grand VS doré",
      width: 2000,
      height: 2000,
      place: "-bottom-24 left-0 w-80 drop-shadow-2xl lg:w-96",
      mobile: "mx-auto mt-3 h-32",
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
    alt: "Élèves qui applaudissent et agitent le drapeau togolais",
    mascot: {
      src: mascottesAxes,
      alt: "Quatre mascottes caméléons avec une caméra, un mégaphone et un arrosoir",
      width: 1122,
      height: 1402,
      place: "-bottom-24 left-0 w-80 drop-shadow-2xl",
      mobile: "absolute inset-x-0 bottom-4 mx-auto h-24",
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

const steps = [
  { i: ClipboardCheck, n: "12", t: "Quiz Santé" },
  { i: Award, n: "1", t: "Certificat officiel Génie Imhotep" },
  { i: Medal, n: "5", t: "Badges thématiques" },
  { i: Gift, n: "1 M", t: "Des lots jusqu'à 1 million FCFA" },
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

  return (
    <section className="mx-auto -mt-6 max-w-7xl px-5">
      <div
        data-reveal
        className="relative grid items-center gap-6 rounded-3xl bg-sun p-6 shadow-card md:grid-cols-[1fr_2fr]"
      >
        <div>
          <h2 className="text-4xl">LE DÉFI DU JOUR</h2>
          <p className="font-bold">Teste tes connaissances et gagne des points !</p>
        </div>
        <div className="rounded-2xl bg-card p-5">
          <p className="text-xs font-extrabold uppercase text-rose">Santé & bien-être</p>
          <p className="mt-1 font-extrabold">
            Quelle est la meilleure façon de se protéger contre le paludisme ?
          </p>
          <div className="mt-4 flex flex-wrap gap-3">
            {defi.options.map((o, i) => (
              <button
                key={o}
                type="button"
                disabled={valide}
                aria-pressed={i === choix}
                onClick={() => setChoix(i)}
                className={`rounded-xl border-2 px-4 py-2 text-sm font-bold transition duration-200 active:scale-95 ${couleur(i)}`}
              >
                {"ABC"[i]} · {o}
              </button>
            ))}
            {valide ? (
              <button
                type="button"
                onClick={() => {
                  setValide(false);
                  setChoix(null);
                }}
                className="btn-fx ml-auto rounded-full bg-primary px-6 py-2 font-bold text-primary-foreground"
              >
                Rejouer
              </button>
            ) : (
              <button
                type="button"
                disabled={choix === null}
                onClick={() => setValide(true)}
                className="btn-fx ml-auto rounded-full bg-primary px-6 py-2 font-bold text-primary-foreground disabled:opacity-50"
              >
                Valider
              </button>
            )}
          </div>
          {valide && (
            <p
              role="status"
              className="mt-3 text-sm font-bold animate-in fade-in slide-in-from-top-1"
            >
              {choix === defi.bonne
                ? "Bravo, c'est la bonne réponse !"
                : "Pas tout à fait : la bonne réponse est en vert."}
            </p>
          )}
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

      {/* Hero */}
      <section className="relative flex min-h-[80vh] overflow-hidden bg-mist">
        <div className="absolute inset-y-0 right-0 isolate h-full w-full md:w-3/4">
          {/* La nouvelle photo arrive par-dessus l'ancienne, qui ne s'efface qu'ensuite : le fond ne transparaît pas entre les deux. Elle avance lentement pendant son affichage, et ne revient à sa taille qu'une fois invisible. */}
          {heroSlides.map((s, i) => (
            <img
              key={i}
              src={s.img}
              alt={s.alt}
              width={1600}
              height={912}
              aria-hidden={i !== active}
              className={`absolute inset-0 h-full w-full object-cover ${s.pos ?? "object-right"} ${i === active ? "z-10 scale-105 opacity-100 [transition:opacity_700ms_ease-in-out,scale_7000ms_linear]" : "scale-100 opacity-0 [transition:opacity_500ms_ease-in-out_300ms,scale_0s_linear_800ms]"}`}
            />
          ))}
        </div>
        <div
          className={`absolute inset-0 bg-hero transition-opacity duration-700 ${heroSlides[active]?.fullPhoto ? "lg:opacity-0" : ""}`}
        />
        <div className="absolute inset-0 bg-mist/80 md:hidden" />
        <div className="relative mx-auto grid w-full max-w-7xl items-center px-5 pb-30 pt-8 md:grid-cols-2 md:pb-24 md:pt-14 xl:pl-16">
          <div>
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
                    <Heading className="text-4xl leading-[0.95] min-[360px]:text-[2.625rem] sm:text-[3.25rem] md:text-5xl lg:text-[4rem]">
                      {s.lines.map((l, j) => (
                        <span key={l}>
                          <span className={j === 0 ? "text-logo-blue" : "text-logo-red"}>{l}</span>
                          <br />
                        </span>
                      ))}
                    </Heading>
                    {s.tagline && (
                      <p className="mt-4 text-lg font-extrabold md:text-xl">{s.tagline}</p>
                    )}
                    <p className="mt-3 font-semibold md:text-lg">{s.sub}</p>
                    <div className="mt-6 flex flex-wrap gap-3">
                      {s.cta.map((c, j) => (
                        <a
                          key={c.t}
                          href={c.href}
                          className={`btn-fx group flex h-12 w-60 items-center justify-center gap-2 whitespace-nowrap rounded-full px-4 text-[15px] font-bold shadow-card ${j === 0 ? "bg-primary text-primary-foreground" : "bg-card"}`}
                        >
                          {c.t}{" "}
                          <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
                        </a>
                      ))}
                    </div>
                    {s.mascot.mobile && (
                      <img
                        src={s.mascot.src}
                        alt={s.mascot.alt}
                        width={s.mascot.width}
                        height={s.mascot.height}
                        className={`${s.mascot.mobile} w-auto md:hidden`}
                      />
                    )}
                  </div>
                );
              })}
            </div>
          </div>
          <div className="relative hidden self-stretch md:block">
            {heroSlides.map((s, i) => (
              <img
                key={i}
                src={s.mascot.src}
                alt={s.mascot.alt}
                width={s.mascot.width}
                height={s.mascot.height}
                aria-hidden={i !== active}
                className={`absolute motion-safe:animate-float ${s.mascot.place} ${heroFade(i === active)}`}
              />
            ))}
          </div>
        </div>
        <button
          aria-label="Diapositive précédente"
          onClick={prev}
          className="absolute bottom-12 left-5 z-10 flex h-10 w-10 items-center justify-center rounded-full bg-card text-ink shadow-card transition hover:scale-110 hover:bg-primary hover:text-primary-foreground active:scale-95 md:bottom-14 xl:bottom-auto xl:left-4 xl:top-1/2 xl:-translate-y-1/2"
        >
          <ChevronLeft className="h-5 w-5" />
        </button>
        <button
          aria-label="Diapositive suivante"
          onClick={next}
          className="absolute bottom-12 right-5 z-10 flex h-10 w-10 items-center justify-center rounded-full bg-card text-ink shadow-card transition hover:scale-110 hover:bg-primary hover:text-primary-foreground active:scale-95 md:bottom-14 xl:bottom-auto xl:right-4 xl:top-1/2 xl:-translate-y-1/2"
        >
          <ChevronRight className="h-5 w-5" />
        </button>
      </section>

      <DefiDuJour />

      {/* Univers */}
      <section id="univers" className="mx-auto max-w-7xl px-5 py-20">
        <div data-reveal className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <h2 className="text-4xl md:text-5xl">
              <span className="text-logo-blue">Les 7 univers</span>{" "}
              <span className="text-primary">du Club Santé</span>
            </h2>
            <p className="mt-2 text-muted-foreground">
              Explore les sept axes du Club Santé et trouve celui qui te fait vibrer !
            </p>
          </div>
          <a
            href="#"
            className="group font-bold text-primary underline transition hover:brightness-90"
          >
            Découvrir les 7 univers{" "}
            <span className="inline-block transition-transform group-hover:translate-x-1">→</span>
          </a>
        </div>
        <div className="mt-8 grid grid-cols-2 gap-4 sm:grid-cols-4 lg:grid-cols-7">
          {univers.map((u, i) => (
            <a
              key={u.t}
              href="#"
              data-reveal
              style={retard(i)}
              className={`${u.c} card-fx group flex flex-col overflow-hidden rounded-3xl bg-[radial-gradient(circle_at_50%_22%,oklch(1_0_0/0.25),transparent_65%)] pt-2 text-center text-primary-foreground shadow-card`}
            >
              {/* Mascotte en buste : le bas de l'image passe sous le panneau, dont le flou donne l'effet de verre. La marge en % suit la largeur de la carte, donc celle de l'image. */}
              <img
                src={u.img}
                alt=""
                loading="lazy"
                width={1414}
                height={2000}
                className="aspect-[1/0.83] w-[115%] max-w-none origin-top self-center object-cover object-top transition duration-300 group-hover:-rotate-2 group-hover:scale-110"
              />
              <div className="relative mx-1.5 mb-1.5 -mt-[17%] flex flex-1 flex-col items-center rounded-[1.25rem] border border-white/30 bg-black/10 px-2 py-3 backdrop-blur-md backdrop-saturate-150">
                <h3 className="text-base leading-tight">{u.t}</h3>
                <p className="mt-2 flex-1 text-xs font-semibold">{u.d}</p>
                <span
                  className={`mt-3 rounded-full bg-card p-2.5 transition duration-300 group-hover:scale-110 ${u.a}`}
                >
                  <ArrowRight className="h-5 w-5 transition-transform duration-300 group-hover:translate-x-0.5" />
                </span>
              </div>
            </a>
          ))}
        </div>
        <div className="mt-10 grid items-center gap-6 lg:grid-cols-[1fr_2.6fr]">
          <div data-reveal="left">
            <h3 className="text-3xl leading-tight md:text-4xl">
              Les Clubs Santé
              <br />
              en chiffres
            </h3>
            <p className="mt-2 text-sm font-medium text-muted-foreground">
              Une communauté qui grandit et qui agit pour une génération de jeunes en bonne santé.
            </p>
          </div>
          {/* Comme sur les cards des univers : le panneau de verre est posé dans la card, et les formes floutées derrière lui donnent l'effet. */}
          <div
            data-reveal="right"
            className="relative isolate overflow-hidden rounded-3xl bg-logo-blue bg-[radial-gradient(circle_at_50%_22%,oklch(1_0_0/0.25),transparent_65%)] p-1.5 text-primary-foreground shadow-card"
          >
            <div className="absolute -left-6 -top-6 -z-10 h-28 w-28 rounded-full bg-sky/70" />
            <div className="absolute -bottom-8 left-1/2 -z-10 h-24 w-24 rounded-full bg-primary/60" />
            <div className="absolute -right-6 top-1/4 -z-10 h-28 w-28 rounded-full bg-sky/50" />
            <div className="grid grid-cols-2 gap-y-6 rounded-[1.25rem] border border-white/30 bg-white/10 px-1 py-6 text-center backdrop-blur-md backdrop-saturate-150 md:grid-cols-5">
              {chiffres.map((c) => (
                <div
                  key={c.t}
                  className="group flex flex-col items-center border-white/25 px-1 last:col-span-2 md:border-l md:first:border-l-0 md:last:col-span-1"
                >
                  <c.i className="h-8 w-8 text-sun transition duration-300 group-hover:-translate-y-1 group-hover:scale-110" />
                  <p className="mt-2 whitespace-nowrap font-display text-[1.75rem] leading-none min-[360px]:text-3xl sm:text-4xl md:text-3xl lg:text-[1.75rem] xl:text-4xl">
                    <span className="text-[0.7em]">+</span>
                    <Compteur value={c.n} />
                  </p>
                  <p className="mt-2 text-xs font-bold">{c.t}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <ClubsSection />
      <AgendaSection />

      {/* Stars */}
      <section className="mx-auto max-w-7xl px-5 py-20">
        <div data-reveal>
          <h2 className="text-4xl md:text-5xl">
            <span className="text-logo-blue">C'est toi</span>{" "}
            <span className="text-primary">la star !</span>
          </h2>
          <p className="mt-2 text-muted-foreground">
            Les réalisations et talents des jeunes des Clubs Santé.
          </p>
        </div>
        <div className="mt-8 grid gap-6 md:grid-cols-3">
          {stars.map((s, i) => (
            <article
              key={s.t}
              data-reveal
              style={retard(i)}
              className="card-fx group overflow-hidden rounded-3xl bg-card shadow-card"
            >
              <div className="relative">
                <div className="overflow-hidden">
                  <img
                    src={s.img}
                    alt={s.t}
                    loading="lazy"
                    className="aspect-[3/2] w-full object-cover object-right transition duration-500 group-hover:scale-105"
                  />
                </div>
                <span className="absolute -bottom-5 right-5 rounded-full bg-primary p-3 text-primary-foreground transition duration-300 group-hover:scale-110">
                  <Play className="h-5 w-5 fill-current" />
                </span>
              </div>
              <div className="p-5">
                <span
                  className={`${s.tc} rounded-full px-3 py-1 text-xs font-extrabold uppercase text-primary-foreground`}
                >
                  {s.tag}
                </span>
                <h3 className="mt-3 font-sans text-lg font-extrabold">{s.t}</h3>
                <p className="mt-1 text-sm text-muted-foreground">{s.d}</p>
              </div>
            </article>
          ))}
        </div>
      </section>

      {/* Parcours */}
      <section className="relative isolate overflow-hidden bg-logo-blue text-primary-foreground">
        <div className="absolute -left-16 -top-16 -z-10 h-72 w-72 rounded-full bg-sky/40 blur-3xl" />
        <div className="mx-auto grid max-w-7xl px-5 lg:grid-cols-[1fr_2fr]">
          {/* Mascotte coupée à la taille : elle sort du bas du panneau. */}
          <img
            src={mascotteBourses}
            alt="Mascotte du Club Santé brandissant un trophée"
            loading="lazy"
            width={1414}
            height={2000}
            data-reveal="left"
            className="order-last mx-auto aspect-[1414/1280] w-full max-w-xs self-end object-cover object-top drop-shadow-2xl lg:order-first lg:max-w-none"
          />
          <div className="py-12 md:py-16 lg:pl-8">
            <h2 data-reveal className="text-4xl md:text-5xl">
              PASSE AU NIVEAU SUPÉRIEUR{" "}
              <span className="block text-sun">& GAGNE JUSQU'À 1 MILLION FCFA !</span>
            </h2>
            <p data-reveal className="mt-4 max-w-3xl font-medium">
              Collégien, lycéen ou simple visiteur engagé : relève le défi des 12 Quiz Santé,
              décroche ton Certificat officiel Génie Imhotep et tes 5 Badges, et tente de remporter
              des lots exceptionnels !
            </p>
            <div className="mt-8 grid grid-cols-2 gap-3 md:grid-cols-4 md:gap-6">
              {steps.map((s, i) => (
                <div
                  key={s.t}
                  data-reveal="zoom"
                  style={retard(i)}
                  className="card-fx group relative rounded-2xl border border-white/25 bg-white/10 p-4 backdrop-blur-md hover:bg-white/20"
                >
                  <s.i className="h-7 w-7 text-sun transition duration-300 group-hover:-rotate-6 group-hover:scale-110" />
                  <p className="mt-2 font-display text-3xl leading-none">{s.n}</p>
                  <p className="mt-2 text-xs font-bold">{s.t}</p>
                  {i < steps.length - 1 && (
                    <ChevronRight className="absolute -right-5 top-1/2 hidden h-4 w-4 -translate-y-1/2 text-sun md:block" />
                  )}
                </div>
              ))}
            </div>
            <a
              href="#"
              className="btn-fx mt-8 inline-block rounded-full bg-primary px-8 py-3 text-center text-[15px] font-bold shadow-card"
            >
              Découvrir la certification
            </a>
          </div>
        </div>
      </section>

      <PartenairesSection />
      <GalerieSection />
      <InitiateurSection />
      <TemoignagesSection />

      <SiteFooter />
    </div>
  );
}
