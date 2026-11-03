import type { CSSProperties } from "react";
import { createFileRoute } from "@tanstack/react-router";
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
      { title: "Les 7 axes — Club Santé SOS Docteur TV" },
      {
        name: "description",
        content:
          "Les 7 axes d'intervention des Clubs Santé SOS Docteur TV : slogan et activités opérationnelles de chaque axe, du Génie Imhotep à la santé environnementale.",
      },
      { property: "og:title", content: "Les 7 axes des Clubs Santé" },
    ],
  }),
  component: LesSeptAxes,
});

// `couleur` : la couleur de l'axe, posée en variable CSS sur sa section ; `encre` : le texte posé sur cette couleur.
const axes = [
  {
    bleu: "Génie",
    vert: "Imhotep",
    t: "Académie GENIE IMHOTEP : jeu de culture générale en santé publique dans les collèges et lycées du Togo.",
    s: "Génie Imhotep, c’est ici et maintenant",
    activites: [
      "Vulgarisation du jeu de culture générale en santé publique dénommé « Académie Génie Imhotep » dans tous les collèges et lycées du Togo.",
      "Compétition nationale de culture générale en santé « GÉNIE IMHOTEP » au niveau communal, préfectoral, inspection, régional et national.",
      "Organisation hebdomadaire du jeu GÉNIE IMHOTEP sur la chaîne SOS DOCTEUR TV.",
    ],
    i: Brain,
    img: mascotteImhotep,
    couleur: "var(--sky)",
    encre: "text-white",
  },
  {
    bleu: "Santé sexuelle",
    vert: "& EVSS",
    t: "Sensibilisation, information et communication sur l’éducation aux valeurs et à la santé sexuelle (EVSS) et les Journées Mondiales en lien avec la Santé (JMS).",
    s: "EVSS, un élève bien informé est un élève serein et engagé dans sa communauté",
    activites: [
      "E-Club Santé sur l’application SOS DOCTEUR TV : un cadre d’expression et d’échanges avec les professionnels de santé.",
      "Sensibilisation sur la Santé Sexuelle et Reproductive (SSR) et les déterminants de santé en milieu scolaire.",
      "Innovation et créativité des jeunes dans les messages de sensibilisation, avec un recueil annuel des bonnes pratiques.",
    ],
    i: MessageCircleHeart,
    img: mascotteValeurs,
    couleur: "var(--rose)",
    encre: "text-white",
  },
  {
    bleu: "Production TV",
    vert: "& médias",
    t: "Production et diffusion des émissions de santé par les élèves sur SOS DOCTEUR TV.",
    s: "La voix des jeunes au cœur des ondes de santé",
    activites: [
      "Vulgarisation des Journées Mondiales de Santé (JMS) dans les établissements scolaires.",
      "Entraînement et production de sketchs, poèmes, slams, chants et reportages santé.",
      "Émissions « Télé des Ados » : diffusion hebdomadaire des prestations des clubs par région éducative.",
    ],
    i: Clapperboard,
    img: mascotteMedias,
    couleur: "var(--grape)",
    encre: "text-white",
  },
  {
    bleu: "Sport",
    vert: "& secourisme",
    t: "Organisation et soutien des activités sportives, culturelles et de secourisme dans les établissements scolaires.",
    s: "Un esprit sain dans un corps sain et agile",
    activites: [
      "Soutien aux activités physiques, tournois sportifs et olympiades scolaires inter-clubs.",
      "Formation certifiante aux gestes qui sauvent et aux premiers secours d’urgence.",
      "Promotion des jeux de réflexion (échecs, scrabble) et découverte des fédérations sportives nationales.",
    ],
    i: Dumbbell,
    img: mascotteSecourisme,
    couleur: "var(--tangerine)",
    encre: "text-white",
  },
  {
    bleu: "Bourses",
    vert: "& excellence",
    t: "Bourses d’excellence, gamification, parrainage des orphelins et distinctions des meilleurs acteurs.",
    s: "L’excellence récompensée, l’émulation stimulée",
    activites: [
      "Bourses PEEP Plus : 100 bourses annuelles d’excellence pour les bacheliers méritants inscrits en sciences de la santé.",
      "Prix spéciaux trimestriels pour les meilleurs enseignants encadreurs et agents de santé.",
      "Cérémonie solennelle de remise de distinctions nationales aux élèves et établissements lauréats.",
    ],
    i: Award,
    img: mascotteBourses,
    couleur: "var(--sun)",
    encre: "text-ink",
  },
  {
    bleu: "Leadership",
    vert: "& mentorat",
    t: "Développement personnel, leadership transformationnel, promotion du genre et mentorat.",
    s: "Oser grandir, inspirer et diriger avec intégrité",
    activites: [
      "Rencontres inspirantes et mentorat direct avec des personnalités médicales et des leaders d’opinion apolitiques.",
      "Dispositif « Ma Parole, Ma Voix Compte » : boîtes à idées et expression libre des apprenants dans chaque école.",
      "Formation démocratique des bureaux d’élèves et responsabilisation civique des jeunes.",
    ],
    i: Compass,
    img: mascotteLeadership,
    couleur: "var(--bark)",
    encre: "text-white",
  },
  {
    bleu: "Santé",
    vert: "& environnement",
    t: "Promotion de la santé, cadre de vie et cohésion sociale : santé environnementale, nutrition et PEVPAH.",
    s: "Un environnement scolaire sain pour une jeunesse épanouie",
    activites: [
      "Prix PEVPAH (Établissement Vert, Propre, Assaini et Hygiénique) récompensant les meilleurs lycées.",
      "Contrôle sanitaire et encadrement des revendeuses d’aliments scolaires pour une nutrition saine.",
      "Reboisement scolaire (« 1 élève, 1 arbre »), gestion des déchets plastiques et hygiène de l’eau.",
    ],
    i: Sprout,
    img: mascotteEnvironnement,
    couleur: "var(--leaf)",
    encre: "text-white",
  },
];

const reperes = [
  { n: "7", t: "axes d’intervention" },
  { n: "21", t: "activités opérationnelles" },
  { n: "7", t: "mascottes pour t’accompagner" },
];

// Un axe : la mascotte sur un aplat de sa couleur avec le slogan en bulle, le texte et les activités en face.
// Les côtés alternent d'un axe à l'autre, et chaque bande prend une teinte claire de la couleur de l'axe.
function Axe({ a, n }: { a: (typeof axes)[number]; n: number }) {
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
            alt={`Mascotte de l’axe ${n} : ${a.bleu} ${a.vert}`}
            loading="lazy"
            width={1414}
            height={2000}
            className="relative mx-auto h-80 w-auto drop-shadow-2xl md:h-[26rem]"
          />
          <p
            className={`absolute bottom-0 max-w-[18rem] rounded-2xl bg-white p-4 font-hand text-xl leading-tight sm:text-2xl text-ink shadow-card sm:max-w-xs ${inverse ? "left-0 rotate-2" : "right-0 -rotate-2"}`}
          >
            « {a.s} »
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
              Axe {n} sur 7
            </p>
          </div>
          <h2 className="mt-4 text-4xl md:text-5xl">
            <span className="text-logo-blue">{a.bleu}</span>{" "}
            <span className="text-primary">{a.vert}</span>
          </h2>
          <p className="mt-4 text-lg font-medium leading-relaxed text-muted-foreground">{a.t}</p>

          <p className="mt-8 flex items-center gap-2 text-sm font-extrabold uppercase tracking-widest text-logo-blue">
            <ListChecks aria-hidden className="size-4" /> Activités opérationnelles
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
  return (
    <div className="min-h-screen overflow-x-clip bg-carnet text-ink">
      <SiteMotion />
      <SiteHeader />

      {/* Bannière : le titre à gauche, les mascottes posées sur le bas à droite, puis le ruban des 7 couleurs. */}
      <section className="relative isolate overflow-hidden bg-linear-to-br from-logo-blue via-logo-blue to-night text-white">
        <div
          aria-hidden
          className="absolute inset-0 -z-10 bg-[radial-gradient(oklch(1_0_0/0.14)_1.5px,transparent_1.5px)] bg-size-[22px_22px] [mask-image:linear-gradient(to_right,black,transparent_70%)]"
        />
        <div
          aria-hidden
          className="absolute -right-40 top-10 -z-10 size-[40rem] rounded-full border-[3rem] border-white/5"
        />
        <div className="mx-auto grid max-w-7xl gap-6 px-5 pt-8 md:pt-12 lg:grid-cols-[1.1fr_1fr] lg:gap-10">
          <div className="pb-4 lg:pb-20">
            <FilAriane rubrique="Vie du club" page="Les 7 axes" clair />

            <div data-reveal="left" className="pt-12 lg:pt-20">
              <span className="inline-flex rounded-full bg-sun px-4 py-1.5 text-xs font-extrabold uppercase tracking-wide text-ink">
                Cadre d’orientation des Clubs Santé
              </span>
              <h1 className="mt-5 text-5xl leading-[0.95] md:text-7xl">
                <span className="block">Les 7 axes</span>
                <span className="block text-primary">de santé</span>
              </h1>
              <p className="mt-6 max-w-xl text-lg font-medium text-white/85">
                Sept univers, sept mascottes : chaque axe donne à ton Club Santé des activités
                concrètes à mener toute l’année dans ton établissement, des quiz du Génie Imhotep au
                reboisement de ta cour.
              </p>
              <ul className="mt-8 flex flex-wrap gap-x-8 gap-y-4">
                {reperes.map((r) => (
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
                Explorer les 7 axes <ArrowDown className="size-4" />
              </a>
            </div>
          </div>

          <img
            src={mascottesAxes}
            alt="Quatre mascottes des Clubs Santé : caméra, mégaphone, pouce levé et arrosoir"
            width={1122}
            height={1402}
            data-reveal="right"
            className="mx-auto w-4/5 max-w-md self-end drop-shadow-2xl sm:w-3/5 lg:w-full lg:max-w-lg"
          />
        </div>
        <div aria-hidden className="flex h-2.5">
          {axes.map((a) => (
            <span key={a.bleu} className="flex-1" style={{ background: a.couleur }} />
          ))}
        </div>
      </section>

      {axes.map((a, i) => (
        <Axe key={a.bleu} a={a} n={i + 1} />
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
              Documentation <span className="text-primary">& reportage officiel</span>
            </h2>
            <p className="mt-4 max-w-xl text-lg font-medium text-white/80">
              Retrouve l’intégralité du cadre d’orientation des Clubs Santé déployé dans les 7
              Directions Régionales de l’Éducation (DRE) du Togo.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <a
                href="#"
                className="btn-fx inline-flex items-center gap-2 rounded-full bg-primary px-7 py-3 text-[15px] font-bold text-primary-foreground"
              >
                <Download className="size-4" /> Télécharger la plaquette complète
              </a>
              <a
                href="#"
                className="btn-fx inline-flex items-center gap-2 rounded-full border-2 border-white px-7 py-3 text-[15px] font-bold hover:bg-white hover:text-logo-blue"
              >
                <CirclePlay className="size-4" /> Visionner le documentaire national
              </a>
            </div>
          </div>
          <div className="relative min-h-64">
            <img
              src={slideAxes}
              alt="Élèves des Clubs Santé qui applaudissent, drapeau du Togo levé"
              loading="lazy"
              width={2000}
              height={1228}
              className="absolute inset-0 size-full object-cover [mask-image:linear-gradient(to_bottom,transparent,black_35%)] lg:[mask-image:linear-gradient(to_right,transparent,black_40%)]"
            />
            <a
              href="/club-sante"
              className="btn-fx absolute bottom-5 right-5 inline-flex items-center gap-2 rounded-full bg-white px-5 py-2.5 text-sm font-bold text-logo-blue shadow-card"
            >
              Découvrir le Club Santé <ArrowRight className="size-4" />
            </a>
          </div>
        </div>
      </section>

      <SiteFooter />
    </div>
  );
}
