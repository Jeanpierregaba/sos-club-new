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
import { formatDeLaLangue } from "@/lib/langues";
import { m } from "@/paraglide/messages.js";

export const Route = createFileRoute("/magazine")({
  head: () => ({
    meta: [
      { title: m.mag_meta_titre() },
      { name: "description", content: m.mag_meta_description() },
      { property: "og:title", content: m.mag_meta_og() },
    ],
  }),
  component: Magazine,
});

type Rubrique = "hygiene" | "sante" | "nutrition" | "environnement" | "paroles";

// Des fonctions : les textes suivent la langue de la page (spec 052).
const rubriques = (): { id: Rubrique; t: string; c: string }[] => [
  { id: "hygiene", t: m.mag_rubrique_hygiene(), c: "bg-sky" },
  { id: "sante", t: m.mag_rubrique_sante(), c: "bg-grape" },
  { id: "nutrition", t: m.mag_rubrique_nutrition(), c: "bg-tangerine" },
  { id: "environnement", t: m.mag_rubrique_environnement(), c: "bg-leaf" },
  { id: "paroles", t: m.mag_rubrique_paroles(), c: "bg-rose" },
];

// Articles et compteurs repris du magazine du site de référence fourni par le porteur du projet (clubsante.ibdastudio.com).
// `cadrage` : la partie de la photo gardée quand elle est rognée.
const articles = (): {
  rubrique: Rubrique;
  date: string;
  club: string;
  t: string;
  d: string;
  img: string;
  cadrage: string;
  aime: number;
  vues: number;
}[] => [
  {
    rubrique: "hygiene",
    date: "2026-06-15",
    club: "Club Santé du Lycée de Tokoin",
    t: m.mag_article_1_titre(),
    d: m.mag_article_1_texte(),
    img: hygiene,
    cadrage: "object-[50%_30%]",
    aime: 42,
    vues: 180,
  },
  {
    rubrique: "environnement",
    date: "2026-06-20",
    club: "Club Santé du Lycée de Kpalimé",
    t: m.mag_article_2_titre(),
    d: m.mag_article_2_texte(),
    img: ecologie,
    cadrage: "object-[50%_40%]",
    aime: 38,
    vues: 125,
  },
  {
    rubrique: "nutrition",
    date: "2026-06-28",
    club: "Club Santé du Lycée de Kara 1",
    t: m.mag_article_3_titre(),
    d: m.mag_article_3_texte(),
    img: slideClubs,
    cadrage: "object-center",
    aime: 29,
    vues: 92,
  },
];
type Article = ReturnType<typeof articles>[number];

const rubriqueDe = (r: Rubrique) => rubriques().find((x) => x.id === r);
const date = (iso: string) =>
  new Date(`${iso}T12:00:00Z`).toLocaleDateString(formatDeLaLangue(), {
    timeZone: "UTC",
    day: "numeric",
    month: "long",
    year: "numeric",
  });

function Magazine() {
  const [rubrique, setRubrique] = useState<Rubrique | null>(null);
  const liste = articles().filter((a) => !rubrique || a.rubrique === rubrique);
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
            <FilAriane rubrique={m.menu_actualites()} page={m.menu_magazine()} clair />
            <div data-reveal="left" className="pt-12">
              <span className="inline-flex items-center gap-2 rounded-full bg-white px-4 py-1.5 text-xs font-extrabold uppercase tracking-wide text-logo-red">
                <Newspaper className="size-4" /> {m.mag_blog()}
              </span>
              <h1 className="mt-5 text-5xl leading-[0.95] md:text-6xl">
                <span className="block">{m.mag_titre_1()}</span>
                <span className="block text-sun">{m.mag_titre_2()}</span>
              </h1>
              <p className="mt-6 max-w-xl text-lg font-medium text-white/90">{m.mag_intro()}</p>
              <ul className="mt-6 flex flex-wrap gap-2">
                {[
                  m.mag_tag_terrain(),
                  m.mag_rubrique_paroles(),
                  m.mag_tag_prevention(),
                  m.mag_tag_emissions(),
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
                {m.mag_lire_articles()} <ArrowDown className="size-4" />
              </a>
              {/* Les articles des élèves et des encadreurs, publiés après modération (spec 023). */}
              <Link
                to="/articles"
                className="btn-fx ml-3 mt-8 inline-flex items-center gap-2 rounded-full bg-white px-7 py-3 text-[15px] font-bold text-logo-red shadow-card"
              >
                <PenLine className="size-4" /> {m.mag_articles_clubs()}
              </Link>
            </div>
          </div>

          <div data-reveal="right" className="relative mx-auto w-full max-w-sm">
            <div className="rotate-3 overflow-hidden rounded-[1.5rem] bg-white text-ink shadow-[0_30px_60px_-20px_rgb(0_0_0/0.5)]">
              <div className="flex items-baseline justify-between bg-ink px-5 py-3 text-white">
                <span className="font-display text-2xl">{m.mag_mag_sante()}</span>
                <span className="text-xs font-bold text-white/70">{m.mag_numero()}</span>
              </div>
              <div className="relative">
                <img
                  src={couverture}
                  alt={m.mag_couverture_alt()}
                  width={992}
                  height={672}
                  className="aspect-[4/5] w-full object-cover"
                />
                <div className="absolute inset-0 flex flex-col justify-between bg-linear-to-t from-night/90 via-transparent to-night/30 p-5 text-white">
                  <span className="self-start rounded bg-sun px-2 py-1 text-xs font-extrabold uppercase text-ink">
                    {m.mag_une_clubs()}
                  </span>
                  <div>
                    <p className="font-display text-3xl leading-tight">
                      {m.mag_rubrique_paroles()}
                    </p>
                    <p className="mt-1 text-sm font-bold text-white/80">
                      {m.mag_presse_jeunesse()}
                    </p>
                  </div>
                </div>
              </div>
            </div>
            <span className="absolute -left-6 -top-6 inline-flex size-24 -rotate-12 items-center justify-center rounded-full bg-sun text-center font-display text-sm leading-tight text-ink shadow-card">
              {m.mag_nouveau()}
              <br />
              {m.mag_numero_court()}
            </span>
          </div>
        </div>
      </section>

      {/* Articles : un filtre par rubrique, l'article à la une en grand, puis les suivants. */}
      <section id="articles" className="mx-auto max-w-7xl scroll-mt-20 px-5 py-20">
        <EnTete sur={m.mag_une_clubs()} bleu={m.mag_derniers()} vert={m.mag_articles()} />
        <div data-reveal className="mt-8 flex flex-wrap gap-2">
          {[null, ...rubriques()].map((r) => (
            <button
              key={r?.id ?? "tous"}
              type="button"
              aria-pressed={rubrique === (r?.id ?? null)}
              onClick={() => setRubrique(r?.id ?? null)}
              className={`rounded-full px-4 py-2 text-sm font-bold transition active:scale-95 ${
                rubrique === (r?.id ?? null)
                  ? "bg-logo-red text-white shadow-card"
                  : "bg-white ring-1 ring-border hover:ring-logo-red/40"
              }`}
            >
              {r?.t ?? m.mag_tous()}
            </button>
          ))}
        </div>

        {!une ? (
          <p className="mt-10 rounded-[1.75rem] border border-dashed p-10 text-center font-semibold text-muted-foreground">
            {m.mag_bientot()}
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
              {m.mag_histoire_1()} <span className="text-sun">{m.mag_histoire_2()}</span>
            </h2>
            <p className="mt-2 max-w-3xl text-lg font-medium text-white/80">
              {m.mag_histoire_texte()}
            </p>
          </div>
        </div>
      </section>

      <SiteFooter />
    </div>
  );
}

function Meta({ a }: { a: Article }) {
  return (
    <p className="flex flex-wrap items-center gap-2 text-sm font-semibold text-muted-foreground">
      <span
        className={`rounded-full px-2.5 py-0.5 text-[11px] font-extrabold uppercase text-white ${rubriqueDe(a.rubrique)?.c ?? "bg-logo-blue"}`}
      >
        {rubriqueDe(a.rubrique)?.t}
      </span>
      {date(a.date)} · {a.club}
    </p>
  );
}

function Reactions({ a }: { a: Article }) {
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
