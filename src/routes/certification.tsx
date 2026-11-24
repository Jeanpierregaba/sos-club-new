import { useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import {
  ArrowRight,
  Award,
  BookOpen,
  CalendarRange,
  Crown,
  Gem,
  Laptop,
  ListChecks,
  Lock,
  Medal,
  Save,
  Smartphone,
  Sparkles,
  Trophy,
  type LucideIcon,
  ShieldCheck,
} from "lucide-react";
import { DecorAnime } from "@/components/DecorAnime";
import { EnTete } from "@/components/EnTete";
import { FilAriane } from "@/components/FilAriane";
import { SiteHeader } from "@/components/SiteHeader";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteMotion, retard } from "@/components/SiteMotion";
import mascottesEquipe from "@/assets/mascottes-equipe.webp";
import { BADGES_CERTIFICATION, BAREME, points, QUIZ_CERTIFICATION } from "@/lib/bareme";
import { lien } from "@/lib/langues";
import { m } from "@/paraglide/messages.js";

export const Route = createFileRoute("/certification")({
  head: () => ({
    meta: [
      { title: m.certif_meta_titre() },
      { name: "description", content: m.certif_meta_description() },
      { property: "og:title", content: m.certif_meta_og() },
    ],
  }),
  component: Certification,
});

// Des fonctions : les textes suivent la langue de la page (spec 052).
const atouts = () => [
  { sur: m.certif_atout_1_sur(), t: m.certif_atout_1() },
  { sur: m.certif_atout_2_sur(), t: m.certif_atout_2() },
  { sur: m.certif_atout_3_sur(), t: m.certif_atout_3() },
];

const lots = () => [
  { i: Laptop, t: m.certif_lot_1(), d: m.certif_lot_1_d() },
  { i: Smartphone, t: m.certif_lot_2(), d: m.certif_lot_2_d() },
  { i: Award, t: m.certif_lot_3(), d: "SOS Docteur TV" },
];

const principes = (): {
  i: LucideIcon;
  sur: string;
  t: string;
  d: string;
  plus: string;
  c: string;
}[] => [
  {
    i: CalendarRange,
    sur: m.certif_principe_1_sur(),
    t: m.certif_principe_1(),
    d: m.certif_principe_1_d(),
    plus: m.certif_principe_1_plus(),
    c: "bg-sky",
  },
  {
    i: BookOpen,
    sur: m.certif_principe_2_sur(),
    t: m.certif_principe_2(),
    d: m.certif_principe_2_d(),
    plus: m.certif_principe_2_plus(),
    c: "bg-primary",
  },
  {
    i: ListChecks,
    sur: m.certif_principe_3_sur(),
    t: m.certif_principe_3(),
    d: m.certif_principe_3_d(),
    plus: m.certif_principe_3_plus(),
    c: "bg-tangerine",
  },
  {
    i: Save,
    sur: m.certif_principe_4_sur(),
    t: m.certif_principe_4(),
    d: m.certif_principe_4_d(),
    plus: m.certif_principe_4_plus(),
    c: "bg-grape",
  },
];

const etapes = () => [
  { t: m.certif_etape_1(), d: m.certif_etape_1_d() },
  { t: m.certif_etape_2(), d: m.certif_etape_2_d() },
  { t: m.certif_etape_3(), d: m.certif_etape_3_d() },
  { t: m.certif_etape_4(), d: m.certif_etape_4_d() },
  { t: m.certif_etape_5(), d: m.certif_etape_5_d() },
];

// Les quiz du badge `rang` (1 à 5), et sa description : 4 quiz par badge.
const quizDuBadge = (rang: number) =>
  m.certif_badge_quiz({ debut: String(rang * 4 - 3), fin: String(rang * 4) });
const suiteDuBadge = (rang: number) =>
  m.certif_badge_suite_d({
    debut: String(rang * 4 - 3),
    fin: String(rang * 4),
    total: String(rang * 4),
  });

// Les 5 badges du parcours (spec 034) : un par thématique de 4 quiz, chacun +500 points pour l'élève et la moitié pour
// son club, une fois. Chaque groupe de 4 quiz porte le nom de son badge (spec 050). `apres` : le nombre de quiz
// réussis qui débloque le badge ; `fond` : le dégradé de la médaille.
const badges = (): {
  n: string;
  i: LucideIcon;
  t: string;
  apres: number;
  d: string;
  quiz: string;
  fond: string;
}[] => [
  {
    n: "01",
    i: Medal,
    t: m.certif_badge_1(),
    apres: 4,
    d: m.certif_badge_1_d(),
    quiz: quizDuBadge(1),
    fond: "from-tangerine to-bark",
  },
  {
    n: "02",
    i: Medal,
    t: m.certif_badge_2(),
    apres: 8,
    d: suiteDuBadge(2),
    quiz: quizDuBadge(2),
    fond: "from-[oklch(0.82_0.02_257)] to-[oklch(0.58_0.03_257)]",
  },
  {
    n: "03",
    i: ShieldCheck,
    t: m.certif_badge_3(),
    apres: 12,
    d: suiteDuBadge(3),
    quiz: quizDuBadge(3),
    fond: "from-[oklch(0.85_0.04_200)] to-sky",
  },
  {
    n: "04",
    i: Crown,
    t: m.certif_badge_4(),
    apres: 16,
    d: suiteDuBadge(4),
    quiz: quizDuBadge(4),
    fond: "from-sun to-tangerine",
  },
  {
    n: "05",
    i: Gem,
    t: m.certif_badge_5(),
    apres: 20,
    d: m.certif_badge_5_d(),
    quiz: quizDuBadge(5),
    fond: "from-sky to-grape",
  },
];

function Certification() {
  const [etape, setEtape] = useState(0);
  const listeEtapes = etapes();
  const listeBadges = badges();
  const e = listeEtapes[etape] ?? listeEtapes[0]!;

  return (
    <div className="min-h-screen overflow-x-clip bg-carnet text-ink">
      <SiteMotion />
      <SiteHeader />

      {/* Bannière claire : le défi et la cagnotte à gauche ; à droite, les sept mascottes et le certificat avec ses
          5 badges. */}
      <section className="relative isolate overflow-hidden bg-linear-to-br from-[color-mix(in_oklch,var(--sky)_16%,white)] via-white to-[color-mix(in_oklch,var(--sun)_30%,white)]">
        <div
          aria-hidden
          className="absolute -right-24 top-1/2 -z-10 size-[36rem] -translate-y-1/2 rounded-full bg-sun/35 motion-safe:animate-respire"
        />
        <div
          aria-hidden
          className="absolute -right-10 top-1/2 -z-10 size-[46rem] -translate-y-1/2 rounded-full border-2 border-dashed border-tangerine/30 motion-safe:animate-[spin_70s_linear_infinite]"
        />
        <div
          aria-hidden
          className="absolute -left-32 top-1/4 -z-10 size-96 rounded-full bg-sky/15 blur-3xl motion-safe:animate-derive"
        />
        <DecorAnime ton="clair" />

        <div className="mx-auto grid max-w-7xl items-end gap-8 px-5 pt-8 md:pt-12 lg:grid-cols-[1.15fr_1fr]">
          <div className="pb-14 lg:pb-24">
            <FilAriane rubrique={m.menu_gamification()} page={m.menu_certification()} />
            <div data-reveal="left" className="pt-10 lg:pt-14">
              <p className="inline-flex items-center gap-2 rounded-full bg-white px-4 py-1.5 text-xs font-extrabold uppercase tracking-widest text-logo-red shadow-sm ring-1 ring-border">
                <Sparkles className="size-4 text-tangerine" /> {m.certif_academie()}
              </p>
              <h1 className="mt-5 text-5xl leading-[0.95] md:text-7xl">
                <span className="block text-logo-blue">{m.certif_titre_1()}</span>
                <span className="block text-primary">{m.certif_titre_2()}</span>
              </h1>
              {/* Le ticket de la cagnotte. */}
              <p className="mt-6 inline-flex -rotate-2 items-center gap-3 rounded-2xl bg-logo-red py-3 pl-4 pr-6 text-white shadow-card">
                <Trophy aria-hidden className="size-7 shrink-0 text-sun" />
                <span className="border-l-2 border-dashed border-white/40 pl-3 font-display text-xl leading-tight md:text-2xl">
                  {m.certif_ticket_debut()}{" "}
                  <span className="text-sun">{m.jeux_certif_somme()}</span>
                  {m.certif_ticket_fin()}
                </span>
              </p>
              <p className="mt-6 max-w-xl text-lg font-medium text-ink/75">{m.certif_intro()}</p>
              <ul className="mt-6 flex flex-wrap gap-2">
                {atouts().map((a) => (
                  <li
                    key={a.sur}
                    className="rounded-full bg-white/85 px-4 py-2 text-sm font-bold shadow-sm ring-1 ring-border backdrop-blur-sm"
                  >
                    <span className="text-muted-foreground">{a.sur} · </span>
                    {a.t}
                  </li>
                ))}
              </ul>
              <div className="mt-8 flex flex-wrap gap-3">
                {/* Connecté, le parcours s'ouvre ; sinon la connexion le demande d'abord. */}
                <a
                  href={lien("/certification/parcours")}
                  className="btn-fx inline-flex items-center gap-2 rounded-full bg-primary px-7 py-3 text-[15px] font-bold text-primary-foreground shadow-card"
                >
                  {m.certif_lancer()} <ArrowRight className="size-4" />
                </a>
                <a
                  href={lien("/connexion")}
                  className="btn-fx rounded-full border-2 border-logo-blue px-7 py-3 text-[15px] font-bold text-logo-blue hover:bg-logo-blue hover:text-white"
                >
                  {m.certif_se_connecter()}
                </a>
              </div>
            </div>
          </div>

          <div data-reveal="right" className="relative mx-auto w-full max-w-md self-end">
            <img
              src={mascottesEquipe}
              alt={m.certif_mascottes_alt()}
              width={1122}
              height={1402}
              className="w-full drop-shadow-2xl"
            />
            {/* Le certificat et ses 5 badges, posés devant les mascottes. */}
            <div className="absolute bottom-6 left-1/2 w-[17rem] -translate-x-1/2 rounded-3xl bg-white/95 p-4 text-center shadow-card ring-1 ring-border backdrop-blur sm:bottom-10 lg:-left-10 lg:translate-x-0">
              <p className="flex items-center justify-center gap-2 text-[11px] font-extrabold uppercase tracking-[0.2em] text-logo-red">
                <Award aria-hidden className="size-4 text-tangerine" /> {m.certif_lot_3()}
              </p>
              <p className="font-display text-xl leading-tight text-logo-blue">
                {m.certif_quiz_badges({ nombre: String(QUIZ_CERTIFICATION) })}
              </p>
              <ul className="mt-3 flex justify-center gap-1.5" aria-label={m.certif_badges_aria()}>
                {listeBadges.map((b, i) => (
                  <li key={b.n} title={b.t}>
                    <span
                      style={{ animationDelay: `${-i * 1.2}s` }}
                      className={`flex size-10 items-center justify-center rounded-full bg-linear-to-br text-white shadow-card ring-2 ring-white motion-safe:animate-float ${b.fond}`}
                    >
                      <b.i aria-hidden className="size-5" />
                    </span>
                    <span className="sr-only">{b.t}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* Lots à gagner, sur un ruban jaune. */}
      <section aria-label={m.certif_lots_aria()} className="bg-sun">
        <ul className="mx-auto grid max-w-7xl gap-x-8 gap-y-4 px-5 py-7 md:grid-cols-3">
          {lots().map((l) => (
            <li key={l.t} className="flex items-center gap-4">
              <span className="inline-flex size-12 shrink-0 items-center justify-center rounded-2xl bg-ink text-sun">
                <l.i className="size-6" />
              </span>
              <span>
                <span className="block font-display text-xl leading-tight text-ink">{l.t}</span>
                <span className="text-sm font-semibold text-ink/70">{l.d}</span>
              </span>
            </li>
          ))}
        </ul>
      </section>

      {/* Guide du parcours : les 4 principes. */}
      <section className="mx-auto max-w-7xl px-5 py-20">
        <EnTete
          sur={m.certif_guide_sur()}
          bleu={m.certif_guide_bleu()}
          vert={m.certif_guide_vert()}
          large
        >
          {m.certif_guide_texte()}
        </EnTete>
        <ul className="mt-10 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {principes().map((p, i) => (
            <li
              key={p.sur}
              data-reveal
              style={retard(i)}
              className="card-fx flex flex-col rounded-[1.75rem] bg-white p-6 shadow-card"
            >
              <span
                className={`inline-flex size-12 items-center justify-center rounded-2xl text-white ${p.c}`}
              >
                <p.i className="size-6" />
              </span>
              <p className="mt-5 text-xs font-extrabold uppercase tracking-wider text-muted-foreground">
                {String(i + 1).padStart(2, "0")} · {p.sur}
              </p>
              <h3 className="mt-1 font-display text-2xl leading-tight text-logo-blue">{p.t}</h3>
              <p className="mt-3 flex-1 font-medium text-muted-foreground">{p.d}</p>
              <p className="mt-5 text-sm font-extrabold text-primary">{p.plus}</p>
            </li>
          ))}
        </ul>
      </section>

      {/* Les 5 étapes : une frise cliquable et le détail de l'étape choisie. */}
      <section className="bg-logo-blue py-20 text-white">
        <div className="mx-auto max-w-7xl px-5">
          <EnTete
            sur={m.certif_methode_sur()}
            bleu={m.certif_methode_bleu()}
            vert={m.certif_methode_vert()}
            sombre
            centre
          />
          <ol className="relative mx-auto mt-12 flex max-w-4xl justify-between">
            <span aria-hidden className="absolute inset-x-6 top-7 h-1 rounded-full bg-white/15" />
            <span
              aria-hidden
              className="absolute left-6 top-7 h-1 rounded-full bg-sun transition-[width] duration-500"
              style={{
                width: `calc(${(etape / (listeEtapes.length - 1)) * 100}% - ${(etape / (listeEtapes.length - 1)) * 3}rem)`,
              }}
            />
            {listeEtapes.map((x, i) => {
              const on = i <= etape;
              return (
                <li key={x.t} className="relative flex flex-col items-center">
                  <button
                    type="button"
                    aria-pressed={i === etape}
                    onClick={() => setEtape(i)}
                    className={`inline-flex size-14 items-center justify-center rounded-full font-display text-xl transition duration-300 ${
                      on
                        ? "bg-sun text-ink"
                        : "bg-night text-white/70 ring-2 ring-white/20 hover:ring-sun"
                    } ${i === etape ? "scale-110 ring-4 ring-white/40" : ""}`}
                  >
                    {String(i + 1).padStart(2, "0")}
                  </button>
                  <span className="mt-3 hidden text-sm font-bold sm:block">{x.t}</span>
                </li>
              );
            })}
          </ol>
          <div className="mx-auto mt-10 grid max-w-4xl items-center gap-6 rounded-[2rem] bg-white/10 p-7 ring-1 ring-white/15 md:grid-cols-[1fr_auto] md:p-9">
            <div key={etape} className="animate-in fade-in slide-in-from-bottom-2 duration-300">
              <p className="text-xs font-extrabold uppercase tracking-widest text-sun">
                {m.certif_etape({ numero: String(etape + 1).padStart(2, "0") })}
              </p>
              <h3 className="mt-1 text-3xl">{e.t}</h3>
              <p className="mt-2 text-lg font-medium text-white/85">{e.d}</p>
            </div>
            <a
              href={lien("/bibliotheque")}
              className="btn-fx inline-flex items-center gap-2 justify-self-start rounded-full bg-primary px-6 py-3 text-[15px] font-bold"
            >
              <BookOpen className="size-4" /> {m.certif_fascicules()}
            </a>
          </div>
        </div>
      </section>

      {/* Les 5 badges : des médailles sur fond nuit, et le barème du parcours. */}
      <section className="bg-night py-20 text-white">
        <div className="mx-auto max-w-7xl px-5">
          <EnTete
            sur={m.certif_badges_sur()}
            bleu={m.certif_badges_bleu()}
            vert={m.certif_badges_vert()}
            sombre
          >
            {m.certif_badges_texte({
              eleve: points(BAREME.badge.eleve),
              club: points(BAREME.badge.club),
            })}
          </EnTete>
          <Bareme />
          <ul className="mt-10 grid gap-5 sm:grid-cols-2 lg:grid-cols-5">
            {listeBadges.map((p, i) => (
              <li
                key={p.n}
                data-reveal
                style={retard(i)}
                className="flex flex-col rounded-[1.75rem] bg-white/5 p-6 ring-1 ring-white/10"
              >
                <span
                  className={`inline-flex size-20 items-center justify-center rounded-full bg-linear-to-br text-white shadow-card ring-4 ring-white/10 ${p.fond}`}
                >
                  <p.i className="size-9" />
                </span>
                <p className="mt-5 text-xs font-extrabold uppercase tracking-widest text-sun">
                  {m.certif_badge_numero({ numero: p.n })}
                </p>
                <h3 className="mt-1 font-display text-2xl leading-tight">{p.t}</h3>
                <p className="mt-1 text-sm font-bold text-primary">
                  {m.certif_badge_apres({ nombre: String(p.apres) })}
                </p>
                <p className="mt-3 flex-1 text-sm font-medium text-white/70">{p.d}</p>
                <p className="mt-4 rounded-full bg-white/10 px-3 py-1 text-center text-xs font-bold">
                  {p.quiz}
                </p>
                <p className="mt-2 text-center text-sm font-extrabold text-sun">
                  {m.certif_badge_points({
                    eleve: points(BAREME.badge.eleve),
                    club: points(BAREME.badge.club),
                  })}
                </p>
              </li>
            ))}
          </ul>
          <p className="mt-6 text-center text-sm font-medium text-white/60">
            {m.certif_provisoire()}
          </p>
        </div>
      </section>

      {/* Feuille de route : 5 thématiques de 4 quiz, chacune avec son badge (spec 034). */}
      <section id="parcours" className="mx-auto max-w-7xl scroll-mt-20 px-5 py-20">
        <div className="flex flex-wrap items-end justify-between gap-6">
          <EnTete
            sur={m.certif_parcours_sur()}
            bleu={m.certif_parcours_bleu({ nombre: String(QUIZ_CERTIFICATION) })}
            vert={m.certif_parcours_vert()}
          />
          <p
            data-reveal
            className="flex max-w-md items-start gap-3 rounded-2xl bg-white p-4 text-sm font-semibold text-muted-foreground shadow-sm ring-1 ring-border"
          >
            <Lock className="mt-0.5 size-5 shrink-0 text-logo-red" />
            {m.certif_visiteur()}
          </p>
        </div>
        <ol className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {listeBadges.map((b, i) => (
            <li
              key={b.n}
              className={`flex flex-col rounded-[1.75rem] p-6 shadow-sm ring-1 ring-border ${i === listeBadges.length - 1 ? "bg-linear-to-br from-sun/30 to-white" : "bg-white"}`}
            >
              <div className="flex items-center justify-between gap-3">
                <span className="rounded-full bg-logo-blue/10 px-2.5 py-0.5 text-[11px] font-extrabold uppercase text-logo-blue">
                  {b.quiz}
                </span>
                <span className="rounded-full bg-sun px-2.5 py-0.5 text-xs font-extrabold text-ink">
                  {m.certif_pts_par_quiz({ points: points(BAREME.quizCertification.eleve) })}
                </span>
              </div>
              <h3 className="mt-4 flex-1 font-display text-2xl leading-tight text-logo-blue">
                {b.t}
              </h3>
              <p className="mt-3 text-sm font-medium text-muted-foreground">
                {b.d} {m.certif_badge_ligne({ points: points(BAREME.badge.eleve) })}
              </p>
              <a
                href={lien("/connexion")}
                className="mt-5 inline-flex items-center gap-2 self-start text-sm font-bold text-logo-blue hover:text-primary"
              >
                <Lock className="size-4" /> {m.certif_debloquer()}
              </a>
            </li>
          ))}
        </ol>
        <div data-reveal className="mt-10 text-center">
          <p className="mx-auto max-w-2xl text-lg font-semibold">
            {m.certif_fin_debut()} <span className="text-logo-blue">{m.certif_academie()}</span>.
          </p>
          <a
            href={lien("/connexion")}
            className="btn-fx mt-6 inline-flex items-center gap-2 rounded-full bg-primary px-8 py-3.5 text-[15px] font-bold text-primary-foreground shadow-card"
          >
            {m.certif_connecter_inscrire()} <ArrowRight className="size-4" />
          </a>
        </div>
      </section>

      <SiteFooter />
    </div>
  );
}

// Le barème du parcours, en trois chiffres (spec 034) ; le club de l'élève reçoit la moitié.
function Bareme() {
  const lignes = [
    { t: m.certif_bareme_1(), b: BAREME.quizCertification, d: m.certif_bareme_1_d() },
    {
      t: m.certif_bareme_2(),
      b: BAREME.badge,
      d: m.certif_bareme_2_d({ nombre: String(BADGES_CERTIFICATION) }),
    },
    { t: m.certif_bareme_3(), b: BAREME.certification, d: m.certif_bareme_3_d() },
  ];
  return (
    <ul className="mt-8 grid gap-3 md:grid-cols-3">
      {lignes.map((l) => (
        <li key={l.t} className="rounded-2xl bg-white/10 p-4 ring-1 ring-white/15">
          <p className="text-sm font-bold text-white/80">{l.t}</p>
          <p className="mt-1 font-display text-2xl text-sun">
            {points(l.b.eleve)} <span className="text-base text-white">{m.certif_pts()}</span>
          </p>
          <p className="text-sm font-semibold text-white/70">
            {m.certif_pour_ton_club({ points: points(l.b.club), detail: l.d })}
          </p>
        </li>
      ))}
    </ul>
  );
}
