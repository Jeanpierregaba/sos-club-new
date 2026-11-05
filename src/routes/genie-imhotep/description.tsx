import { useState, type CSSProperties } from "react";
import { createFileRoute } from "@tanstack/react-router";
import {
  ArrowRight,
  BookOpen,
  Check,
  ClipboardCheck,
  GraduationCap,
  HeartPulse,
  Lightbulb,
  Mic,
  Scale,
  School,
  ShieldCheck,
  Sparkles,
  Star,
  Stethoscope,
  Timer,
  Trophy,
  Tv,
  Users,
  type LucideIcon,
} from "lucide-react";
import { EnTete } from "@/components/EnTete";
import { FilAriane } from "@/components/FilAriane";
import { SiteHeader } from "@/components/SiteHeader";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteMotion, retard } from "@/components/SiteMotion";
import { DecorAnime } from "@/components/DecorAnime";
import mascottesVs from "@/assets/mascottes-vs.webp";
import mascotteImhotep from "@/assets/mascotte-imhotep.webp";
import mascottesLivres from "@/assets/mascottes-livres.webp";
import slideGenie from "@/assets/slide-genie.jpg";
import grandesFinales from "@/assets/agenda-grandes-finales.jpg";

export const Route = createFileRoute("/genie-imhotep/description")({
  head: () => ({
    meta: [
      { title: "Description — Génie Imhotep" },
      {
        name: "description",
        content:
          "L'Académie Génie Imhotep, le jeu de culture générale en santé des Clubs Santé SOS DOCTEUR TV : origine du nom, règles du match, rubriques, championnat national et émission télévisée.",
      },
      { property: "og:title", content: "L'Académie Génie Imhotep" },
    ],
  }),
  component: Description,
});

// Contenus repris du document « Académie Génie Imhotep — présentation » remis par AIMES-AFRIQUE.

const chiffres = [
  { n: "+5 000", t: "questions-réponses à réviser" },
  { n: "11", t: "rubriques de jeu" },
  { n: "2", t: "catégories : secondaire 1 et 2" },
  { n: "12", t: "matchs par saison télévisée" },
];

const roles = ["Architecte", "Ingénieur", "Prêtre", "Écrivain", "Médecin"];

const reperes = [
  { t: "Vers 2700 à 2667 av. J.-C.", d: "Naissance à Memphis (ou Anoué), sous la 3e dynastie." },
  { t: "Vizir du pharaon Djéser", d: "Son premier conseiller." },
  { t: "Pyramide de Saqqarah", d: "La pyramide à degrés, premier grand monument de pierre." },
  {
    t: "Papyrus Edwin Smith",
    d: "La tradition lui attribue ses savoirs, consignés dans un des plus anciens traités de médecine : diagnostic, examen, pronostic, traitement.",
  },
  {
    t: "Plus de 2 000 ans avant Hippocrate",
    d: "Que l'on présente souvent comme le « père de la médecine ».",
  },
];

const objectifs: { i: LucideIcon; c: string; t: string }[] = [
  {
    i: BookOpen,
    c: "var(--logo-blue)",
    t: "Renforcer les connaissances en promotion de la santé, bien-être, éducation aux valeurs et santé sexuelle et reproductive.",
  },
  {
    i: ShieldCheck,
    c: "var(--primary)",
    t: "Donner aux jeunes les compétences pour prévenir les maladies, décider en connaissance de cause et adopter des comportements responsables.",
  },
  {
    i: Lightbulb,
    c: "var(--tangerine)",
    t: "Apprendre de manière ludique, interactive et durable, par la compétition.",
  },
  {
    i: Trophy,
    c: "var(--logo-red)",
    t: "Encourager l'excellence en valorisant les meilleurs élèves et établissements, au Togo et en Afrique.",
  },
];

const fascicules = [
  // Vert assombri : sur le vert du site, le texte blanc et le jaune manqueraient de contraste.
  {
    n: "2 000",
    t: "questions-réponses",
    pour: "Secondaire I",
    c: "color-mix(in oklch, var(--primary) 70%, black)",
  },
  { n: "3 000", t: "questions-réponses", pour: "Secondaire II", c: "var(--logo-blue)" },
  { n: "EVSS", t: "questions-réponses", pour: "Émission télévisée", c: "var(--grape)" },
];

const conditions = [
  "Un bureau en place",
  "Des membres inscrits",
  "Des encadreurs",
  "Des commissions actives qui rendent compte",
];

const acteurs: { i: LucideIcon; t: string; d: string; c: string }[] = [
  {
    i: Users,
    t: "Le bloc",
    c: "var(--logo-blue)",
    d: "L'équipe : 6 joueurs, dont 3 en jeu et 3 remplaçants, avec leur encadreur. Tous doivent jouer pendant le match ; on change entre deux rubriques.",
  },
  {
    i: Mic,
    t: "L'interne",
    c: "var(--primary)",
    d: "Le présentateur : il lit les questions, donne la parole à l'équipe qui buzze en premier, dit si la réponse est juste et anime le jeu.",
  },
  {
    i: Scale,
    t: "Le staff",
    c: "var(--tangerine)",
    d: "Le jury de 2 ou 3 personnes, dont un président : réponses, score, chronomètre, litiges et sanctions. En cas de désaccord, il l'emporte sur l'interne.",
  },
  {
    i: HeartPulse,
    t: "Le patient",
    c: "var(--logo-red)",
    d: "Le personnage fictif à « guérir » : il ne connaît pas sa maladie, et chaque rubrique est une étape de sa prise en charge.",
  },
];

const postes = ["Chirurgien", "Anesthésiste", "Instrumentiste"];

// Les rubriques d'un match, dans l'ordre du parcours du patient. `tv` : jouée aussi à l'émission.
const rubriques = [
  {
    t: "Admission",
    p: "Un joueur seul répond à 5 questions, 3 secondes par question.",
    pts: "+10 par réponse, +10 de bonus si 5/5",
  },
  {
    t: "Constante",
    p: "Questions rapides dont toutes les réponses commencent par la même lettre.",
    pts: "+10 ; –10 si mauvaise lettre",
  },
  {
    t: "Consultation",
    p: "Questions posées à tour de rôle à chaque équipe.",
    pts: "+20 ; réplique +10",
  },
  {
    t: "Diagnostic",
    p: "Des indices de plus en plus faciles pour trouver la réponse.",
    pts: "40, 30, 20 ou 10 selon l'indice",
  },
  {
    t: "Dossier médical",
    p: "Questions sur un thème choisi par l'équipe qui mène.",
    pts: "+20 ; réplique +10",
  },
  {
    t: "Scanner",
    p: "Un joueur fait deviner 3 mots à un coéquipier en 30 secondes, un indice à la fois.",
    pts: "+10 par mot, +10 de bonus",
  },
  {
    t: "Orthopédie",
    p: "Former un nouveau mot en retirant et en ajoutant des lettres au précédent.",
    pts: "+10",
  },
  {
    t: "Points de suture",
    p: "Relier les éléments de deux listes et trouver l'élément manquant.",
    pts: "+10 par bonne association",
  },
  {
    t: "État de choc",
    p: "Questions éclairs : le premier qui buzze répond.",
    pts: "+10 ; –10 si buzz trop tôt et erreur",
  },
  {
    t: "Réanimation",
    p: "Questions en cascade : chaque réponse commence par la lettre suivante de l'alphabet.",
    pts: "+10",
  },
  {
    t: "Exeat",
    p: "Ultime chance pour l'équipe menée de peu : duel en face à face sur 10 questions. Hors émission télévisée.",
    pts: "Comme l'état de choc",
  },
];

const regles: { i: LucideIcon; t: string; d: string }[] = [
  {
    i: ClipboardCheck,
    t: "Le score",
    d: "La somme des points gagnés moins les pénalités ; il ne peut pas être négatif en fin de match.",
  },
  {
    i: Sparkles,
    t: "Le public",
    d: "Cris de génie, slam, chanson, chorégraphie : les supporters rapportent de 0 à 50 points de jury à leur équipe en fin de match.",
  },
  {
    i: ShieldCheck,
    t: "Le fair-play",
    d: "Insultes, moqueries ou violences sont sanctionnées : retrait de points, défaite sur tapis vert, voire exclusion.",
  },
  {
    i: Star,
    t: "La fiche de match",
    d: "Chaque match a sa fiche officielle signée, qui désigne aussi l'homme du match.",
  },
];

const composantes: {
  id: string;
  i: LucideIcon;
  t: string;
  c: string;
  ou: string;
  qui: string;
  quand: string;
  but: string;
}[] = [
  {
    id: "interclasses",
    i: School,
    t: "Matchs inter-classes",
    c: "var(--primary)",
    ou: "Dans chaque établissement",
    qui: "Les équipes des différentes classes",
    quand: "Tout au long de l'année scolaire",
    but: "Faire jouer tous les élèves et désigner la meilleure équipe de l'établissement",
  },
  {
    id: "championnat",
    i: Trophy,
    t: "Championnat national",
    c: "var(--logo-blue)",
    ou: "De la préfecture au niveau national",
    qui: "Les meilleures équipes de chaque niveau",
    quand: "De janvier à avril",
    but: "Désigner les meilleures équipes du pays",
  },
  {
    id: "emission",
    i: Tv,
    t: "Émission télévisée",
    c: "var(--grape)",
    ou: "Studio Prof JAMES, SOS DOCTEUR TV",
    qui: "Deux établissements par émission",
    quand: "Chaque samedi à 10 h, 12 matchs par saison",
    but: "Faire rayonner le jeu et les clubs auprès du grand public",
  },
];

const phases = [
  { t: "Phase préfectorale", d: "La meilleure équipe de la préfecture" },
  { t: "Phase inspectorale", d: "La meilleure équipe de l'inspection" },
  { t: "Phase régionale", d: "La meilleure équipe de la région éducative" },
  { t: "Phase nationale", d: "Les 7 champions régionaux" },
  { t: "Grande finale", d: "Le champion national" },
];

const emission = [
  "Chaque émission oppose deux équipes en confrontation directe, selon les règles du jeu, sans la rubrique Exeat.",
  "L'équipe gagnante devient tenante du titre et le remet en jeu face à un nouveau challenger, jusqu'à trois matchs. Sa cagnotte augmente à chaque victoire.",
  "Pour la saison 3, les participants sont des clubs santé champions préfectoraux du Grand Lomé et de la région Maritime.",
  "L'émission fait connaître le jeu, les clubs santé et les messages de santé bien au-delà de l'école.",
];

const resume: { i: LucideIcon; t: string; d: string }[] = [
  { i: BookOpen, t: "Un fascicule", d: "pour apprendre" },
  { i: School, t: "Des matchs en classe", d: "pour s'entraîner" },
  { i: Trophy, t: "Un championnat", d: "pour se mesurer aux meilleurs" },
  { i: Tv, t: "Une émission", d: "pour briller devant tout le pays" },
];

const couleur = (c: string) => ({ "--c": c }) as CSSProperties;

function Description() {
  const [etape, setEtape] = useState(0);
  const rubrique = rubriques[etape] ?? rubriques[0]!;
  const progression = Math.round(((etape + 1) / rubriques.length) * 100);

  return (
    <div className="min-h-screen overflow-x-clip bg-carnet text-ink">
      <SiteMotion />
      <SiteHeader />

      {/* Bannière : le nom du jeu et sa devise, les mascottes en duel à droite. */}
      <section className="relative isolate overflow-hidden bg-linear-to-br from-[oklch(0.58_0.22_300)] via-grape to-[oklch(0.5_0.25_285)] text-white">
        <div aria-hidden className="pointer-events-none absolute inset-0 -z-10">
          <div className="absolute inset-0 bg-[radial-gradient(oklch(1_0_0/0.14)_1.5px,transparent_1.5px)] bg-size-[22px_22px] [mask-image:linear-gradient(to_right,black,transparent_55%)] motion-safe:animate-defile-motif" />
          <div className="absolute -right-40 -top-40 size-[44rem] rounded-full border-[3.5rem] border-white/5 motion-safe:animate-respire" />
          <div className="absolute -bottom-32 right-1/4 size-96 rounded-full bg-sun/20 blur-3xl motion-safe:animate-derive" />
        </div>
        <DecorAnime />

        <div className="mx-auto grid max-w-7xl items-center gap-8 px-5 pt-8 md:pt-12 lg:grid-cols-[1.15fr_1fr]">
          <div className="pb-10 lg:pb-20">
            <FilAriane rubrique="Génie Imhotep" page="Description" clair />
            <div data-reveal="left" className="pt-10 lg:pt-14">
              <p className="inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1 text-sm font-bold backdrop-blur-sm">
                <span className="size-2 rounded-full bg-sun" /> Axe 1 des Clubs Santé
              </p>
              <h1 className="mt-5 text-5xl leading-[0.95] md:text-7xl">
                <span className="block">Académie</span>
                <span className="block text-sun">Génie Imhotep</span>
              </h1>
              <p className="mt-5 text-xl font-extrabold md:text-2xl">
                Le jeu de culture générale en santé des Clubs Santé SOS DOCTEUR TV
              </p>
              <p className="mt-4 max-w-xl text-lg font-medium text-white/80">
                Des équipes d’élèves des collèges et lycées du Togo s’affrontent au buzzer sur des
                questions de santé, d’éducation aux valeurs et de santé sexuelle. Conçu par l’ONG
                AIMES-AFRIQUE, diffusé sur SOS DOCTEUR TV.
              </p>
              <div className="mt-8 flex flex-wrap gap-3">
                <a
                  href="/genie-imhotep/inscription"
                  className="btn-fx group flex h-12 items-center gap-2 rounded-full bg-primary px-6 text-[15px] font-bold text-primary-foreground shadow-card"
                >
                  Inscrire mon établissement
                  <ArrowRight className="size-4 transition-transform group-hover:translate-x-1" />
                </a>
                <a
                  href="#match"
                  className="btn-fx flex h-12 items-center gap-2 rounded-full border-2 border-white/60 bg-white/10 px-6 text-[15px] font-bold backdrop-blur-sm"
                >
                  Découvrir les règles
                </a>
              </div>
            </div>
          </div>

          <div
            data-reveal="right"
            className="relative mx-auto w-full max-w-md self-end lg:max-w-xl"
          >
            <img
              src={mascottesVs}
              alt="Deux mascottes des Clubs Santé face à face, au-dessus d’un grand « VS » doré"
              width={2000}
              height={2000}
              className="w-full drop-shadow-2xl"
            />
            <p className="absolute left-0 top-6 -rotate-6 rounded-2xl bg-sun px-4 py-2 font-display text-lg leading-tight text-ink shadow-card sm:text-xl">
              « Génie Imhotep,
              <br />
              c’est ici et maintenant »
            </p>
          </div>
        </div>
      </section>

      {/* Chiffres clés, à cheval sur le bas de la bannière. */}
      <section className="relative z-10 mx-auto -mt-10 max-w-6xl px-5">
        <dl
          data-reveal
          className="grid grid-cols-2 gap-px overflow-hidden rounded-3xl bg-border shadow-card ring-4 ring-white md:grid-cols-4"
        >
          {chiffres.map((c) => (
            <div key={c.t} className="flex flex-col-reverse bg-white p-5 text-center md:p-6">
              <dt className="mt-1 text-sm font-bold text-muted-foreground">{c.t}</dt>
              <dd className="font-display text-4xl text-logo-blue md:text-5xl">{c.n}</dd>
            </div>
          ))}
        </dl>
      </section>

      {/* Qui était Imhotep : le récit à gauche, une fiche de repères à droite. */}
      <section id="imhotep" className="mx-auto max-w-7xl scroll-mt-16 px-5 py-20">
        <div className="grid gap-12 lg:grid-cols-[1.1fr_1fr] lg:gap-16">
          <div>
            <EnTete sur="Aux origines du nom" bleu="Qui était" vert="Imhotep ?" />
            <div data-reveal className="mt-6 space-y-4 text-lg leading-relaxed text-ink/80">
              <p>
                Imhotep, dont le nom signifie{" "}
                <strong className="text-ink">« celui qui vient en paix »</strong>, est un grand
                savant de l’Égypte ancienne. Il vécut sous le règne du pharaon Djéser, dont il fut
                le vizir, c’est-à-dire le premier conseiller.
              </p>
              <p>
                Sa réputation de guérisseur fut telle que les Égyptiens l’honorèrent plus tard comme
                une divinité de la médecine, et que les Grecs l’identifièrent à leur dieu guérisseur
                Asclépios. Une tradition lui attribue les savoirs médicaux du papyrus Edwin Smith,
                acquis en 1862.
              </p>
            </div>
            <ul data-reveal className="mt-6 flex flex-wrap gap-2">
              {roles.map((r) => (
                <li
                  key={r}
                  className="rounded-full bg-white px-4 py-1.5 text-sm font-extrabold text-logo-blue shadow-sm ring-1 ring-logo-blue/15"
                >
                  {r}
                </li>
              ))}
            </ul>

            <div
              data-reveal
              className="relative mt-10 overflow-hidden rounded-[2rem] bg-[color-mix(in_oklch,var(--sun)_22%,white)] p-6 ring-1 ring-sun/50 md:p-8"
            >
              <Sparkles
                aria-hidden
                className="absolute -right-4 -top-4 size-28 rotate-12 text-sun/60"
              />
              <h3 className="relative text-2xl text-logo-blue md:text-3xl">Pourquoi ce nom ?</h3>
              <p className="relative mt-3 font-medium text-ink/80">
                Imhotep est un Africain dont le savoir a traversé les millénaires. En donnant son
                nom au jeu, AIMES-AFRIQUE propose aux élèves un modèle d’excellence africaine : un
                savant complet, bâtisseur et soignant. L’« esprit bâtisseur et polyvalent » figure
                d’ailleurs parmi les piliers fondateurs des Clubs Santé SOS DOCTEUR TV.
              </p>
            </div>
          </div>

          <aside
            data-reveal="right"
            className="relative self-start overflow-hidden rounded-[2rem] bg-night p-6 text-white shadow-card md:p-8"
          >
            <div
              aria-hidden
              className="absolute -right-20 -top-20 size-64 rounded-full bg-sun/25 blur-3xl"
            />
            <p className="relative text-sm font-extrabold uppercase tracking-widest text-sun">
              Fiche du savant
            </p>
            <ol className="relative mt-6 space-y-5 border-l-2 border-dashed border-white/20 pl-6">
              {reperes.map((r) => (
                <li key={r.t} className="relative">
                  <span className="absolute -left-[1.95rem] top-1 size-3.5 rounded-full bg-sun ring-4 ring-night" />
                  <p className="font-display text-lg leading-tight">{r.t}</p>
                  <p className="mt-1 text-sm font-medium text-white/70">{r.d}</p>
                </li>
              ))}
            </ol>
            <img
              src={mascotteImhotep}
              alt=""
              loading="lazy"
              width={1414}
              height={2000}
              className="relative -mb-6 ml-auto mt-4 w-32 md:-mb-8 md:w-40"
            />
          </aside>
        </div>
      </section>

      {/* Place du jeu dans le projet : l'axe 1, les objectifs, le fascicule et les conditions de participation. */}
      <section
        id="projet"
        className="scroll-mt-16 bg-[color-mix(in_oklch,var(--sky)_8%,white)] py-20"
      >
        <div className="mx-auto max-w-7xl px-5">
          <EnTete sur="Dans le projet des Clubs Santé" bleu="Un jeu au cœur" vert="de l’axe 1">
            Les Clubs Santé SOS DOCTEUR TV, présents dans les établissements secondaires depuis
            2024, agissent autour de sept axes. L’Académie Génie Imhotep en est le premier : la
            vulgarisation du jeu dans toutes les classes, la compétition nationale à tous les
            niveaux et l’émission hebdomadaire sur SOS DOCTEUR TV. Son exécution est réservée à
            AIMES-AFRIQUE et SOS DOCTEUR TV.
          </EnTete>

          <ul className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {objectifs.map((o, i) => (
              <li
                key={o.t}
                data-reveal
                style={{ ...couleur(o.c), ...retard(i) }}
                className="card-fx rounded-3xl border-t-4 border-(--c) bg-white p-6 shadow-card"
              >
                <span className="inline-flex size-12 items-center justify-center rounded-2xl bg-[color-mix(in_oklch,var(--c)_14%,white)] text-(--c)">
                  <o.i className="size-6" />
                </span>
                <p className="mt-4 font-semibold leading-snug">{o.t}</p>
              </li>
            ))}
          </ul>

          <div className="mt-16 grid items-center gap-10 lg:grid-cols-[1fr_1.1fr]">
            <img
              data-reveal="left"
              src={mascottesLivres}
              alt="Deux mascottes, livres en main, devant des piles de livres « Santé », « Prévention », « Bien-être »"
              loading="lazy"
              width={1122}
              height={1402}
              className="mx-auto w-full max-w-sm"
            />
            <div>
              <div data-reveal>
                <h3 className="text-3xl md:text-4xl">
                  <span className="text-logo-blue">Le fascicule</span>{" "}
                  <span className="text-primary">de questions-réponses</span>
                </h3>
                <p className="mt-3 text-lg font-medium text-muted-foreground">
                  Toutes les questions du jeu viennent des fascicules élaborés par AIMES-AFRIQUE
                  entre décembre 2024 et mars 2025, et mis à la disposition des établissements.
                  Réviser le fascicule, c’est apprendre la santé.
                </p>
              </div>
              <ul className="mt-6 grid gap-3 sm:grid-cols-3">
                {fascicules.map((f, i) => (
                  <li
                    key={f.pour}
                    data-reveal
                    style={{ ...couleur(f.c), ...retard(i) }}
                    className="relative overflow-hidden rounded-2xl bg-(--c) p-5 pl-7 text-white shadow-card"
                  >
                    {/* Le dos du livre. */}
                    <span aria-hidden className="absolute inset-y-0 left-0 w-3 bg-black/20" />
                    <p className="font-display text-4xl leading-none">{f.n}</p>
                    <p className="mt-1 text-sm font-bold text-white/85">{f.t}</p>
                    <p className="mt-4 text-xs font-extrabold uppercase tracking-wider text-sun">
                      {f.pour}
                    </p>
                  </li>
                ))}
              </ul>
              <p
                data-reveal
                className="mt-4 flex items-start gap-2 text-sm font-semibold text-muted-foreground"
              >
                <ShieldCheck className="mt-0.5 size-4 shrink-0 text-primary" />
                Pour chaque compétition, une cellule de rédaction compose les questionnaires de
                match, les vérifie et les conserve sous pli fermé.
              </p>
            </div>
          </div>

          {/* Qui peut participer. */}
          <div
            data-reveal
            className="mt-16 grid gap-8 rounded-[2rem] bg-logo-blue p-6 text-white shadow-card md:p-10 lg:grid-cols-[1fr_1.2fr] lg:items-center"
          >
            <div>
              <p className="text-sm font-extrabold uppercase tracking-widest text-sun">
                Qui peut participer ?
              </p>
              <h3 className="mt-3 text-3xl md:text-4xl">
                Les collèges et lycées dotés d’un{" "}
                <span className="text-sun">Club Santé fonctionnel</span>
              </h3>
              <p className="mt-4 font-medium text-white/80">
                La compétition distingue deux catégories : le{" "}
                <strong className="text-white">secondaire 1</strong> et le{" "}
                <strong className="text-white">secondaire 2</strong>.
              </p>
            </div>
            <ul className="grid gap-3 sm:grid-cols-2">
              {conditions.map((c) => (
                <li
                  key={c}
                  className="flex items-center gap-3 rounded-2xl border border-white/20 bg-white/10 p-4 font-bold backdrop-blur-sm"
                >
                  <span className="inline-flex size-8 shrink-0 items-center justify-center rounded-full bg-primary">
                    <Check className="size-4" />
                  </span>
                  {c}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </section>

      {/* Comment se joue un match : le principe du patient, puis les acteurs. */}
      <section id="match" className="mx-auto max-w-7xl scroll-mt-16 px-5 py-20">
        <div className="grid items-center gap-10 lg:grid-cols-[1.1fr_1fr]">
          <EnTete
            sur="Comment se joue un match"
            bleu="Soigner le patient,"
            vert="question après question"
          >
            Chaque match raconte le parcours d’un patient à l’hôpital, de son admission à sa
            guérison. Les deux équipes, appelées blocs, doivent le « soigner » en répondant juste :
            chaque bonne réponse le rapproche de la sortie.
          </EnTete>
          <figure data-reveal="right" className="relative">
            <img
              src={slideGenie}
              alt="Trois élèves en polo bleu au pupitre de la compétition Génie Imhotep"
              loading="lazy"
              width={2000}
              height={1600}
              className="aspect-[4/3] w-full rounded-[2rem] object-cover object-[50%_20%] shadow-card"
            />
            <figcaption className="absolute -bottom-5 left-5 flex items-center gap-2 rounded-full bg-white px-4 py-2 text-sm font-extrabold text-logo-blue shadow-card">
              <Timer className="size-4 text-logo-red" /> 5 s pour répondre · 3 s pour la réplique
            </figcaption>
          </figure>
        </div>

        <ul className="mt-14 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {acteurs.map((a, i) => (
            <li
              key={a.t}
              data-reveal
              style={{ ...couleur(a.c), ...retard(i) }}
              className="card-fx relative overflow-hidden rounded-3xl bg-white p-6 shadow-card"
            >
              <span
                aria-hidden
                className="absolute -right-8 -top-8 size-28 rounded-full bg-[color-mix(in_oklch,var(--c)_14%,white)]"
              />
              <span className="relative inline-flex size-12 items-center justify-center rounded-2xl bg-(--c) text-white">
                <a.i className="size-6" />
              </span>
              <h3 className="relative mt-4 text-2xl text-(--c)">{a.t}</h3>
              <p className="relative mt-2 text-sm font-medium leading-relaxed text-ink/75">{a.d}</p>
              {a.t === "Le bloc" && (
                <ul className="relative mt-4 flex flex-wrap gap-1.5">
                  {postes.map((p) => (
                    <li
                      key={p}
                      className="rounded-full bg-mist px-2.5 py-1 text-xs font-extrabold text-logo-blue"
                    >
                      {p}
                    </li>
                  ))}
                </ul>
              )}
            </li>
          ))}
        </ul>
      </section>

      {/* Les rubriques : un parcours de soin à explorer étape par étape. */}
      <section
        id="rubriques"
        className="relative isolate scroll-mt-16 overflow-hidden bg-night py-20 text-white"
      >
        <div aria-hidden className="pointer-events-none absolute inset-0 -z-10">
          <div className="absolute -left-24 top-10 size-96 rounded-full bg-logo-red/25 blur-3xl" />
          <div className="absolute -right-24 bottom-0 size-96 rounded-full bg-primary/20 blur-3xl" />
        </div>
        <div className="mx-auto max-w-7xl px-5">
          <EnTete sur="Les rubriques" bleu="Le parcours" vert="du patient" sombre>
            Un match enchaîne des rubriques aux noms médicaux, chacune inspirée d’une épreuve
            classique de jeu de culture générale. Choisis une étape pour voir comment elle se joue.
          </EnTete>

          <div className="mt-10 grid gap-6 lg:grid-cols-[1fr_1.1fr]">
            <ol className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-2">
              {rubriques.map((r, i) => {
                const on = i === etape;
                return (
                  <li key={r.t}>
                    <button
                      type="button"
                      aria-pressed={on}
                      onClick={() => setEtape(i)}
                      className={`flex w-full items-center gap-3 rounded-2xl px-3 py-3 text-left font-bold transition ${
                        on
                          ? "bg-white text-ink shadow-card"
                          : i < etape
                            ? "bg-primary/20 text-white hover:bg-primary/30"
                            : "bg-white/5 text-white/80 ring-1 ring-white/10 hover:bg-white/10"
                      }`}
                    >
                      <span
                        className={`inline-flex size-8 shrink-0 items-center justify-center rounded-full font-display text-sm ${
                          on
                            ? "bg-logo-red text-white"
                            : i < etape
                              ? "bg-primary text-white"
                              : "bg-white/10"
                        }`}
                      >
                        {i < etape ? <Check className="size-4" /> : i + 1}
                      </span>
                      <span className="leading-tight">{r.t}</span>
                    </button>
                  </li>
                );
              })}
            </ol>

            <div className="relative flex flex-col overflow-hidden rounded-[2rem] bg-white p-6 text-ink shadow-card md:p-8">
              {/* Seule la fiche de l'étape est annoncée, d'un bloc, à chaque changement. */}
              <div aria-live="polite" aria-atomic="true" className="flex flex-col">
                <div className="flex items-center justify-between gap-4">
                  <span className="inline-flex items-center gap-2 rounded-full bg-[color-mix(in_oklch,var(--logo-red)_12%,white)] px-3 py-1 text-xs font-extrabold uppercase tracking-wider text-logo-red">
                    <Stethoscope className="size-3.5" /> Étape {etape + 1} sur {rubriques.length}
                  </span>
                  <HeartPulse
                    aria-hidden
                    className="size-8 text-logo-red motion-safe:animate-pulse"
                  />
                </div>
                <h3
                  key={rubrique.t}
                  className="mt-4 text-4xl text-logo-blue animate-in fade-in md:text-5xl"
                >
                  {rubrique.t}
                </h3>
                <p className="mt-3 text-lg font-medium text-ink/80">{rubrique.p}</p>
                <p className="mt-5 inline-flex self-start rounded-2xl bg-sun px-4 py-2 font-display text-lg text-ink">
                  {rubrique.pts}
                </p>
              </div>

              <div className="mt-auto pt-8">
                <div className="flex items-center justify-between text-sm font-bold text-muted-foreground">
                  <span>Admission</span>
                  <span>Sortie de l’hôpital</span>
                </div>
                <div
                  role="progressbar"
                  aria-label="Avancée du patient vers sa sortie"
                  aria-valuenow={progression}
                  aria-valuetext={`Étape ${etape + 1} sur ${rubriques.length} : ${rubrique.t}`}
                  aria-valuemin={0}
                  aria-valuemax={100}
                  className="mt-2 h-3 overflow-hidden rounded-full bg-mist"
                >
                  <div
                    className="h-full rounded-full bg-linear-to-r from-logo-red via-sun to-primary transition-[width] duration-500"
                    style={{ width: `${progression}%` }}
                  />
                </div>
                {/* aria-disabled plutôt que disabled : le bouton garde le focus clavier aux deux bouts du parcours. */}
                <div className="mt-5 flex gap-2">
                  <button
                    type="button"
                    onClick={() => setEtape((e) => Math.max(e - 1, 0))}
                    aria-disabled={etape === 0}
                    className="rounded-full border-2 border-border px-5 py-2.5 text-sm font-bold transition hover:border-logo-blue aria-disabled:opacity-40"
                  >
                    Étape précédente
                  </button>
                  <button
                    type="button"
                    onClick={() => setEtape((e) => Math.min(e + 1, rubriques.length - 1))}
                    aria-disabled={etape === rubriques.length - 1}
                    className="btn-fx rounded-full bg-primary px-5 py-2.5 text-sm font-bold text-primary-foreground aria-disabled:opacity-40"
                  >
                    Étape suivante
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Score, public et fair-play. */}
      <section className="mx-auto max-w-7xl px-5 py-20">
        <EnTete sur="Pendant le match" bleu="Score, public" vert="& fair-play" />
        <ul className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {regles.map((r, i) => (
            <li
              key={r.t}
              data-reveal
              style={retard(i)}
              className="rounded-3xl border bg-white p-6 shadow-sm"
            >
              <r.i className="size-7 text-logo-red" />
              <h3 className="mt-4 text-xl text-logo-blue">{r.t}</h3>
              <p className="mt-2 text-sm font-medium leading-relaxed text-ink/75">{r.d}</p>
            </li>
          ))}
        </ul>
      </section>

      {/* Les trois composantes : un tableau en cartes, puis le détail de chacune. */}
      <section
        id="composantes"
        className="scroll-mt-16 bg-[color-mix(in_oklch,var(--sun)_10%,white)] py-20"
      >
        <div className="mx-auto max-w-7xl px-5">
          <EnTete sur="Trois formes complémentaires" bleu="Trois façons" vert="de jouer" centre>
            L’Académie Génie Imhotep se joue dans les établissements, dans le championnat national
            et à la télévision.
          </EnTete>

          <ul className="mt-10 grid gap-5 lg:grid-cols-3">
            {composantes.map((c, i) => (
              <li
                key={c.id}
                data-reveal
                style={{ ...couleur(c.c), ...retard(i) }}
                className="card-fx flex flex-col overflow-hidden rounded-[2rem] bg-white shadow-card"
              >
                <a
                  href={`#${c.id}`}
                  className="flex items-center gap-3 bg-(--c) px-6 py-5 text-white"
                >
                  <c.i className="size-7 shrink-0" />
                  <span className="font-display text-2xl leading-tight">{c.t}</span>
                </a>
                <dl className="grid flex-1 gap-4 p-6">
                  {[
                    ["Où", c.ou],
                    ["Qui", c.qui],
                    ["Quand", c.quand],
                    ["But", c.but],
                  ].map(([k, v]) => (
                    <div key={k}>
                      <dt className="text-xs font-extrabold uppercase tracking-widest text-(--c)">
                        {k}
                      </dt>
                      <dd className="mt-0.5 font-semibold leading-snug">{v}</dd>
                    </div>
                  ))}
                </dl>
              </li>
            ))}
          </ul>

          {/* Inter-classes. */}
          <article
            id="interclasses"
            data-reveal
            className="mt-16 scroll-mt-24 rounded-[2rem] bg-white p-6 shadow-card md:p-10"
          >
            <p className="flex items-center gap-2 text-sm font-extrabold uppercase tracking-widest text-logo-red">
              <School className="size-4" /> Le niveau de base
            </p>
            <h3 className="mt-3 text-3xl md:text-4xl">
              <span className="text-logo-blue">Les matchs</span>{" "}
              <span className="text-primary">inter-classes</span>
            </h3>
            <p className="mt-4 max-w-4xl text-lg font-medium text-ink/80">
              Dans chaque établissement doté d’un club santé, des équipes se forment dans toutes les
              classes et s’affrontent selon les règles du jeu, avec les questions du fascicule. Un
              grand nombre d’élèves révisent et jouent, et les meilleurs forment l’équipe de
              l’établissement en secondaire 1 et en secondaire 2. Ces équipes le représentent
              ensuite au championnat.
            </p>
          </article>

          {/* Championnat : les étapes, puis la première édition. */}
          <article
            id="championnat"
            data-reveal
            className="mt-6 scroll-mt-24 overflow-hidden rounded-[2rem] bg-logo-blue text-white shadow-card"
          >
            <div className="p-6 md:p-10">
              <p className="flex items-center gap-2 text-sm font-extrabold uppercase tracking-widest text-sun">
                <Trophy className="size-4" /> Compétition inter-établissements
              </p>
              <h3 className="mt-3 text-3xl md:text-4xl">
                Le championnat <span className="text-sun">national</span>
              </h3>
              <p className="mt-4 max-w-4xl text-lg font-medium text-white/80">
                Organisé par étapes successives, en secondaire 1 et en secondaire 2. À chaque étape,
                les meilleures équipes de l’étape précédente s’affrontent.
              </p>
              <ol className="mt-8 grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
                {phases.map((p, i) => (
                  <li
                    key={p.t}
                    className={`relative rounded-2xl p-4 ${
                      i === phases.length - 1
                        ? "bg-sun text-ink"
                        : "border border-white/20 bg-white/10 backdrop-blur-sm"
                    }`}
                  >
                    <span className="font-display text-3xl opacity-60">{i + 1}</span>
                    <p className="mt-1 font-display text-lg leading-tight">{p.t}</p>
                    <p
                      className={`mt-1 text-sm font-medium ${i === phases.length - 1 ? "text-ink/75" : "text-white/75"}`}
                    >
                      {p.d}
                    </p>
                    {i < phases.length - 1 && (
                      <ArrowRight
                        aria-hidden
                        className="absolute -right-3 top-1/2 z-10 hidden size-5 -translate-y-1/2 rounded-full bg-sun p-0.5 text-ink lg:block"
                      />
                    )}
                  </li>
                ))}
              </ol>
            </div>
            <div className="grid lg:grid-cols-[1.2fr_1fr]">
              <img
                src={grandesFinales}
                alt="Les finalistes du Championnat national Génie Imhotep sur scène, chèques géants en main"
                loading="lazy"
                width={2000}
                height={963}
                className="aspect-[2/1] size-full object-cover lg:aspect-auto"
              />
              <div className="bg-night p-6 md:p-10">
                <p className="text-sm font-extrabold uppercase tracking-widest text-sun">
                  1re édition · fin juin 2026, Lomé
                </p>
                <p className="mt-4 font-display text-2xl leading-tight md:text-3xl">
                  Le Lycée d’Adétikopé, champion national
                </p>
                <p className="mt-4 flex items-center gap-4">
                  <span className="font-display text-5xl text-sun">490</span>
                  <span className="text-sm font-bold uppercase text-white/60">à</span>
                  <span className="font-display text-5xl text-white/60">360</span>
                </p>
                <p className="mt-1 text-sm font-medium text-white/70">
                  face au Lycée scientifique de Kara
                </p>
                <p className="mt-6 text-sm font-medium text-white/80">
                  À terme, AIMES-AFRIQUE prévoit aussi une compétition internationale entre les
                  meilleures équipes nationales des pays où l’association est représentée.
                </p>
                <a
                  href="/genie-imhotep/hall-of-fame"
                  className="mt-6 inline-flex items-center gap-2 font-bold text-sun hover:underline"
                >
                  Voir le Hall of Fame <ArrowRight className="size-4" />
                </a>
              </div>
            </div>
          </article>

          {/* Émission télévisée. */}
          <article
            id="emission"
            data-reveal
            className="mt-6 grid scroll-mt-24 gap-8 rounded-[2rem] bg-grape p-6 text-white shadow-card md:p-10 lg:grid-cols-[1fr_1.2fr]"
          >
            <div>
              <p className="flex items-center gap-2 text-sm font-extrabold uppercase tracking-widest text-sun">
                <Tv className="size-4" /> Sur SOS DOCTEUR TV
              </p>
              <h3 className="mt-3 text-3xl md:text-4xl">
                L’émission <span className="text-sun">Génie Imhotep</span>
              </h3>
              <div className="mt-6 inline-flex items-center gap-4 rounded-2xl bg-white p-4 text-ink shadow-card">
                <span className="text-center">
                  <span className="block font-display text-3xl leading-none text-logo-red">
                    SAM.
                  </span>
                  <span className="block font-display text-xl text-logo-blue">10 h</span>
                </span>
                <span className="h-12 w-px bg-border" />
                <span className="text-sm font-bold leading-snug">
                  Studio Prof JAMES
                  <br />
                  <span className="text-muted-foreground">
                    12 matchs par saison · saison 3 en cours
                  </span>
                </span>
              </div>
              <p className="mt-6 text-sm font-medium text-white/80">
                La chaîne est accessible par application mobile, sur les décodeurs MP4 et sur le
                bouquet CANAL+.
              </p>
            </div>
            <ul className="grid gap-3">
              {emission.map((e) => (
                <li
                  key={e}
                  className="flex gap-3 rounded-2xl border border-white/20 bg-white/10 p-4 font-medium backdrop-blur-sm"
                >
                  <Star className="mt-0.5 size-5 shrink-0 text-sun" />
                  {e}
                </li>
              ))}
            </ul>
          </article>
        </div>
      </section>

      {/* En résumé : les quatre façons de vivre le jeu, puis la devise. */}
      <section className="relative isolate overflow-hidden bg-linear-to-br from-logo-blue to-night py-20 text-white">
        <div
          aria-hidden
          className="absolute -right-24 -top-24 -z-10 size-96 rounded-full bg-sun/20 blur-3xl"
        />
        <div className="mx-auto max-w-7xl px-5">
          <EnTete
            sur="En résumé"
            bleu="Chaque élève, acteur"
            vert="de sa propre santé"
            sombre
            centre
          >
            Par la compétition, l’Académie Génie Imhotep fait de chaque élève un relais de
            prévention dans sa famille et sa communauté.
          </EnTete>
          <ol className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {resume.map((r, i) => (
              <li
                key={r.t}
                data-reveal
                style={retard(i)}
                className="rounded-3xl border border-white/15 bg-white/10 p-6 text-center backdrop-blur-sm"
              >
                <span className="mx-auto inline-flex size-14 items-center justify-center rounded-2xl bg-sun text-ink">
                  <r.i className="size-7" />
                </span>
                <p className="mt-4 font-display text-2xl leading-tight">{r.t}</p>
                <p className="mt-1 font-medium text-white/75">{r.d}</p>
              </li>
            ))}
          </ol>
          <div data-reveal className="mt-14 text-center">
            <p className="font-display text-3xl text-sun md:text-5xl">
              Génie Imhotep, c’est ici et maintenant !
            </p>
            <div className="mt-8 flex flex-wrap justify-center gap-3">
              <a
                href="/genie-imhotep/inscription"
                className="btn-fx group flex h-12 items-center gap-2 rounded-full bg-primary px-6 text-[15px] font-bold text-primary-foreground shadow-card"
              >
                <GraduationCap className="size-5" /> Inscrire mon établissement
                <ArrowRight className="size-4 transition-transform group-hover:translate-x-1" />
              </a>
              <a
                href="/bibliotheque"
                className="btn-fx flex h-12 items-center gap-2 rounded-full border-2 border-white/60 bg-white/10 px-6 text-[15px] font-bold backdrop-blur-sm"
              >
                <BookOpen className="size-5" /> Réviser dans la bibliothèque
              </a>
            </div>
          </div>
        </div>
      </section>

      <SiteFooter />
    </div>
  );
}
