import { useState } from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
import { ArrowDown, Eye, Heart, Newspaper, PenLine } from "lucide-react";
import { EnTete } from "@/components/EnTete";
import { FilAriane } from "@/components/FilAriane";
import { SiteHeader } from "@/components/SiteHeader";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteMotion, retard } from "@/components/SiteMotion";
import couverture from "@/assets/story2.jpg";
import hygiene from "@/assets/campagne-hygiene.jpg";
import ecologie from "@/assets/campagne-ecologie.jpg";
import slideClubs from "@/assets/slide-clubs.webp";

export const Route = createFileRoute("/magazine")({
  head: () => ({
    meta: [
      { title: "Magazine — Club Santé SOS Docteur TV" },
      {
        name: "description",
        content:
          "Le magazine officiel des Clubs Santé : reportages dans les lycées, articles d'éducation sanitaire, émissions SOS Docteur TV et paroles d'élèves.",
      },
      { property: "og:title", content: "Le magazine des Clubs Santé" },
    ],
  }),
  component: Magazine,
});

const rubriques = [
  { t: "Hygiène & sensibilisation", c: "bg-sky" },
  { t: "Santé publique & reportages TV", c: "bg-grape" },
  { t: "Nutrition", c: "bg-tangerine" },
  { t: "Protection de l’environnement", c: "bg-leaf" },
  { t: "Paroles aux élèves", c: "bg-rose" },
];

// Articles et compteurs repris du magazine du site de référence fourni par le porteur du projet (clubsante.ibdastudio.com).
// `cadrage` : la partie de la photo gardée quand elle est rognée.
const articles = [
  {
    rubrique: "Hygiène & sensibilisation",
    date: "2026-06-15",
    club: "Club Santé du Lycée de Tokoin",
    t: "Grande journée « Lavage des mains & hygiène » avec SOS Docteur TV",
    d: "Le Club Santé du Lycée de Tokoin, avec l’équipe médicale de SOS Docteur TV, a organisé une démonstration géante du lavage des mains selon les normes de l’OMS. Plus de 350 élèves ont été formés, et des kits sanitaires ont été distribués.",
    img: hygiene,
    cadrage: "object-[50%_30%]",
    aime: 42,
    vues: 180,
  },
  {
    rubrique: "Protection de l’environnement",
    date: "2026-06-20",
    club: "Club Santé du Lycée de Kpalimé",
    t: "Campagne de reboisement et création d’un jardin de plantes médicinales",
    d: "Pour agir face au changement climatique et créer un cadre de vie sain, les membres du club ont planté 150 arbres à croissance rapide dans l’enceinte du lycée, et aménagé un espace pour les plantes thérapeutiques locales : moringa, citronnelle et neem.",
    img: ecologie,
    cadrage: "object-[50%_40%]",
    aime: 38,
    vues: 125,
  },
  {
    rubrique: "Nutrition",
    date: "2026-06-28",
    club: "Club Santé du Lycée de Kara 1",
    t: "Distribution de fruits de saison & causerie sur la nutrition équilibrée",
    d: "Une alimentation équilibrée est la clé d’une bonne santé d’apprentissage ! Le club a mobilisé des partenaires pour distribuer mangues, oranges et bananes aux élèves du premier cycle, avec un mini-quiz interactif sur les vitamines essentielles.",
    img: slideClubs,
    cadrage: "object-center",
    aime: 29,
    vues: 92,
  },
];

const couleur = (r: string) => rubriques.find((x) => x.t === r)?.c ?? "bg-logo-blue";
const date = (iso: string) =>
  new Date(`${iso}T12:00:00Z`).toLocaleDateString("fr-FR", {
    timeZone: "UTC",
    day: "numeric",
    month: "long",
    year: "numeric",
  });

function Magazine() {
  const [rubrique, setRubrique] = useState<string | null>(null);
  const liste = articles.filter((a) => !rubrique || a.rubrique === rubrique);
  const [une, ...autres] = liste;

  return (
    <div className="min-h-screen overflow-x-clip bg-carnet text-ink">
      <SiteMotion />
      <SiteHeader />

      {/* Bannière façon couverture : le titre de presse à gauche, la « une » du numéro à droite. */}
      <section className="relative isolate overflow-hidden bg-linear-to-br from-logo-red to-rose text-white">
        <div
          aria-hidden
          className="absolute inset-0 -z-10 bg-[repeating-linear-gradient(135deg,oklch(1_0_0/0.05)_0_2px,transparent_2px_14px)]"
        />
        <div className="mx-auto grid max-w-7xl items-center gap-12 px-5 pb-20 pt-8 md:pt-12 lg:grid-cols-[1.15fr_1fr]">
          <div>
            <FilAriane rubrique="Actualités" page="Magazine" clair />
            <div data-reveal="left" className="pt-12">
              <span className="inline-flex items-center gap-2 rounded-full bg-white px-4 py-1.5 text-xs font-extrabold uppercase tracking-wide text-logo-red">
                <Newspaper className="size-4" /> Le blog & magazine officiel
              </span>
              <h1 className="mt-5 text-5xl leading-[0.95] md:text-6xl">
                <span className="block">La voix de la jeunesse</span>
                <span className="block text-sun">& l’actu santé en direct</span>
              </h1>
              <p className="mt-6 max-w-xl text-lg font-medium text-white/90">
                Plonge au cœur du magazine des Clubs Santé SOS Docteur TV : reportages photo dans
                les lycées, articles d’éducation sanitaire, émissions TV, chroniques d’élèves et
                témoignages d’impact dans tout le Togo.
              </p>
              <ul className="mt-6 flex flex-wrap gap-2">
                {[
                  "Reportages terrain",
                  "Paroles aux élèves",
                  "Prévention & hygiène",
                  "Émissions SOS Docteur TV",
                ].map((t) => (
                  <li
                    key={t}
                    className="rounded-full bg-white/15 px-3 py-1 text-sm font-bold ring-1 ring-white/30"
                  >
                    {t}
                  </li>
                ))}
              </ul>
              <a
                href="#articles"
                className="btn-fx mt-8 inline-flex items-center gap-2 rounded-full bg-primary px-7 py-3 text-[15px] font-bold text-primary-foreground shadow-card"
              >
                Lire les articles <ArrowDown className="size-4" />
              </a>
              {/* Les articles des élèves et des encadreurs, publiés après modération (spec 023). */}
              <Link
                to="/articles"
                className="btn-fx ml-3 mt-8 inline-flex items-center gap-2 rounded-full bg-white px-7 py-3 text-[15px] font-bold text-logo-red shadow-card"
              >
                <PenLine className="size-4" /> Articles des clubs
              </Link>
            </div>
          </div>

          <div data-reveal="right" className="relative mx-auto w-full max-w-sm">
            <div className="rotate-3 overflow-hidden rounded-[1.5rem] bg-white text-ink shadow-[0_30px_60px_-20px_rgb(0_0_0/0.5)]">
              <div className="flex items-baseline justify-between bg-ink px-5 py-3 text-white">
                <span className="font-display text-2xl">Le Mag’ Santé</span>
                <span className="text-xs font-bold text-white/70">N° 01 · 2026</span>
              </div>
              <div className="relative">
                <img
                  src={couverture}
                  alt="Des lycéens du Club Santé en reportage"
                  width={992}
                  height={672}
                  className="aspect-[4/5] w-full object-cover"
                />
                <div className="absolute inset-0 flex flex-col justify-between bg-linear-to-t from-night/90 via-transparent to-night/30 p-5 text-white">
                  <span className="self-start rounded bg-sun px-2 py-1 text-xs font-extrabold uppercase text-ink">
                    À la une des clubs
                  </span>
                  <div>
                    <p className="font-display text-3xl leading-tight">Paroles aux élèves</p>
                    <p className="mt-1 text-sm font-bold text-white/80">100 % presse jeunesse</p>
                  </div>
                </div>
              </div>
            </div>
            <span className="absolute -left-6 -top-6 inline-flex size-24 -rotate-12 items-center justify-center rounded-full bg-sun text-center font-display text-sm leading-tight text-ink shadow-card">
              Nouveau
              <br />
              numéro
            </span>
          </div>
        </div>
      </section>

      {/* Articles : un filtre par rubrique, l'article à la une en grand, puis les suivants. */}
      <section id="articles" className="mx-auto max-w-7xl scroll-mt-20 px-5 py-20">
        <EnTete sur="À la une des clubs" bleu="Les derniers" vert="articles" />
        <div data-reveal className="mt-8 flex flex-wrap gap-2">
          {[null, ...rubriques.map((r) => r.t)].map((r) => (
            <button
              key={r ?? "tous"}
              type="button"
              aria-pressed={rubrique === r}
              onClick={() => setRubrique(r)}
              className={`rounded-full px-4 py-2 text-sm font-bold transition active:scale-95 ${
                rubrique === r
                  ? "bg-logo-red text-white shadow-card"
                  : "bg-white ring-1 ring-border hover:ring-logo-red/40"
              }`}
            >
              {r ?? "Tous"}
            </button>
          ))}
        </div>

        {!une ? (
          <p className="mt-10 rounded-[1.75rem] border border-dashed p-10 text-center font-semibold text-muted-foreground">
            Les premiers articles de cette rubrique arrivent bientôt.
          </p>
        ) : (
          <div className="mt-10 grid gap-6 lg:grid-cols-3">
            <article
              key={une.t}
              data-reveal
              className="card-fx overflow-hidden rounded-[2rem] bg-white shadow-card lg:col-span-2 lg:row-span-2"
            >
              <img
                src={une.img}
                alt=""
                loading="lazy"
                className={`aspect-[16/10] w-full object-cover ${une.cadrage}`}
              />
              <div className="p-7 md:p-9">
                <Meta a={une} />
                <h3 className="mt-3 text-3xl leading-tight text-logo-blue md:text-4xl">{une.t}</h3>
                <p className="mt-3 text-lg font-medium text-muted-foreground">{une.d}</p>
                <Reactions a={une} />
              </div>
            </article>
            {autres.map((a, i) => (
              <article
                key={a.t}
                data-reveal
                style={retard(i + 1)}
                className="card-fx flex flex-col overflow-hidden rounded-[2rem] bg-white shadow-card"
              >
                <img
                  src={a.img}
                  alt=""
                  loading="lazy"
                  className={`aspect-[16/9] w-full object-cover ${a.cadrage}`}
                />
                <div className="flex flex-1 flex-col p-6">
                  <Meta a={a} />
                  <h3 className="mt-3 font-sans text-xl font-extrabold leading-snug">{a.t}</h3>
                  <p className="mt-2 flex-1 text-[15px] font-medium text-muted-foreground">{a.d}</p>
                  <Reactions a={a} />
                </div>
              </article>
            ))}
          </div>
        )}
      </section>

      {/* Appel à contributions : le magazine est écrit par les clubs. */}
      <section className="mx-auto max-w-7xl px-5 pb-20">
        <div
          data-reveal="zoom"
          className="grid items-center gap-8 rounded-[2rem] bg-ink p-8 text-white md:p-12 lg:grid-cols-[auto_1fr]"
        >
          <span className="inline-flex size-20 items-center justify-center rounded-3xl bg-sun text-ink">
            <PenLine className="size-10" />
          </span>
          <div>
            <h2 className="text-3xl md:text-4xl">
              Ton club a une histoire <span className="text-sun">à raconter ?</span>
            </h2>
            <p className="mt-2 max-w-3xl text-lg font-medium text-white/80">
              Reportage, chronique ou action de terrain : prépare ton article avec l’encadreur de
              ton Club Santé, qui le transmet à la rédaction pour validation avant publication.
            </p>
          </div>
        </div>
      </section>

      <SiteFooter />
    </div>
  );
}

function Meta({ a }: { a: (typeof articles)[number] }) {
  return (
    <p className="flex flex-wrap items-center gap-2 text-sm font-semibold text-muted-foreground">
      <span
        className={`rounded-full px-2.5 py-0.5 text-[11px] font-extrabold uppercase text-white ${couleur(a.rubrique)}`}
      >
        {a.rubrique}
      </span>
      {date(a.date)} · {a.club}
    </p>
  );
}

function Reactions({ a }: { a: (typeof articles)[number] }) {
  return (
    <p className="mt-5 flex items-center gap-4 border-t pt-4 text-sm font-bold text-muted-foreground">
      <span className="flex items-center gap-1.5">
        <Heart className="size-4 text-rose" /> {a.aime}
      </span>
      <span className="flex items-center gap-1.5">
        <Eye className="size-4" /> {a.vues}
      </span>
    </p>
  );
}
