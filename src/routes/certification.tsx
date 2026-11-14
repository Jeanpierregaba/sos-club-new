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
import mascotteImhotep from "@/assets/mascotte-imhotep.webp";
import { BADGES_CERTIFICATION, BAREME, points, QUIZ_CERTIFICATION } from "@/lib/bareme";

export const Route = createFileRoute("/certification")({
  head: () => ({
    meta: [
      { title: "Certification — Club Santé SOS Docteur TV" },
      {
        name: "description",
        content:
          "La Certification Académie Génie Imhotep : 20 quiz santé, 5 badges, un certificat officiel et jusqu'à 1 million FCFA de lots.",
      },
      { property: "og:title", content: "Obtiens ta certification Génie Imhotep" },
    ],
  }),
  component: Certification,
});

const atouts = [
  { sur: "Parcours", t: "20 quiz santé" },
  { sur: "Distinction", t: "Certificat + 5 badges" },
  { sur: "Cagnotte", t: "1 000 000 FCFA" },
];

const lots = [
  { i: Laptop, t: "Ordinateurs portables neufs", d: "pour exceller dans tes études" },
  { i: Smartphone, t: "Smartphones & tablettes", d: "pour les champions des 20 quiz santé" },
  { i: Award, t: "Certificat officiel", d: "SOS Docteur TV" },
];

const principes: { i: LucideIcon; sur: string; t: string; d: string; plus: string; c: string }[] = [
  {
    i: CalendarRange,
    sur: "Rythme libre",
    t: "À ton rythme, sans contrainte",
    d: "Le parcours peut se faire sur plusieurs semaines ou plusieurs mois : pas besoin de tout terminer en une seule fois.",
    plus: "Flexibilité totale",
    c: "bg-sky",
  },
  {
    i: BookOpen,
    sur: "Révision gratuite",
    t: "Des fascicules en libre accès",
    d: "Avant les quiz, consulte et télécharge gratuitement les fascicules pédagogiques pour apprendre, réviser et te préparer.",
    plus: "100 % gratuits",
    c: "bg-primary",
  },
  {
    i: ListChecks,
    sur: "20 quiz thématiques",
    t: "Un programme en 20 quiz obligatoires",
    d: "5 thématiques de 4 quiz, jouées dans l’ordre. Chaque thématique terminée débloque son badge ; il faut 10/10 pour valider un quiz.",
    plus: "5 thématiques",
    c: "bg-tangerine",
  },
  {
    i: Save,
    sur: "Sauvegarde auto",
    t: "Ta progression est gardée",
    d: "Chaque quiz est une étape indépendante. Ta progression est sauvegardée dans ton compte : tu reprends là où tu t’étais arrêté.",
    plus: "À chaque étape validée",
    c: "bg-grape",
  },
];

const etapes = [
  {
    t: "Apprendre",
    d: "Consulter les fascicules pédagogiques, découvrir les notions essentielles et enrichir ses connaissances.",
  },
  { t: "Se préparer", d: "Relire, réviser et s’entraîner avant de lancer un quiz." },
  {
    t: "Se challenger",
    d: "Tester ses connaissances à travers des quiz chronométrés et relever progressivement les défis proposés.",
  },
  {
    t: "Progresser",
    d: "Avancer quiz après quiz, suivre ses résultats et reprendre son parcours à son rythme, même plusieurs semaines ou plusieurs mois plus tard.",
  },
  {
    t: "Se certifier",
    d: "Terminer les 20 quiz obligatoires, remplir les conditions de réussite et obtenir la Certification Académie Génie Imhotep – Clubs Santé SOS Docteur TV.",
  },
];

// Les 5 badges du parcours (spec 034) : un par thématique de 4 quiz, chacun +500 points pour l'élève et la moitié pour
// son club, une fois. Les intitulés des thématiques restent à fournir par l'équipe pédagogique : chacune porte le nom
// de son badge. `apres` : le nombre de quiz réussis qui débloque le badge ; `fond` : le dégradé de la médaille.
const badges: {
  n: string;
  metal: string;
  i: LucideIcon;
  t: string;
  apres: number;
  d: string;
  quiz: string;
  fond: string;
}[] = [
  {
    n: "01",
    metal: "Thématique 1",
    i: Medal,
    t: "Ambassadeur Santé Junior",
    apres: 4,
    d: "Les 4 premiers quiz du parcours réussis à 10/10.",
    quiz: "Quiz 1 à 4",
    fond: "from-tangerine to-bark",
  },
  {
    n: "02",
    metal: "Thématique 2",
    i: Medal,
    t: "Pair Éducateur Santé et Citoyenneté",
    apres: 8,
    d: "La deuxième thématique terminée : 8 quiz réussis.",
    quiz: "Quiz 5 à 8",
    fond: "from-[oklch(0.82_0.02_257)] to-[oklch(0.58_0.03_257)]",
  },
  {
    n: "03",
    metal: "Thématique 3",
    i: ShieldCheck,
    t: "Sentinelle de la Prévention",
    apres: 12,
    d: "La troisième thématique terminée : 12 quiz réussis.",
    quiz: "Quiz 9 à 12",
    fond: "from-[oklch(0.85_0.04_200)] to-sky",
  },
  {
    n: "04",
    metal: "Thématique 4",
    i: Crown,
    t: "Champion de la Santé et EVSS",
    apres: 16,
    d: "La quatrième thématique terminée : 16 quiz réussis.",
    quiz: "Quiz 13 à 16",
    fond: "from-sun to-tangerine",
  },
  {
    n: "05",
    metal: "Thématique 5",
    i: Gem,
    t: "Maître Génie Imhotep",
    apres: 20,
    d: "La distinction suprême, après les 20 quiz obligatoires : elle accompagne le certificat officiel.",
    quiz: "Quiz 17 à 20",
    fond: "from-sky to-grape",
  },
];

// L'anneau des 20 quiz : un segment par quiz, qui s'allume à tour de rôle ; au centre, le certificat.
// Chaque badge est posé sur l'anneau à l'endroit où il se débloque (après le 4e, 8e, 12e, 16e et 20e quiz).
const RAYON = 130;
const TOUR = 2 * Math.PI * RAYON;
const SEGMENT = TOUR / QUIZ_CERTIFICATION;
// La place d'un badge, en % du cadre de 300 : l'anneau part du haut et tourne dans le sens des aiguilles.
const placeBadge = (apres: number) => {
  const angle = (apres / QUIZ_CERTIFICATION) * 2 * Math.PI;
  const rayon = (RAYON / 300) * 100;
  return { left: `${50 + rayon * Math.sin(angle)}%`, top: `${50 - rayon * Math.cos(angle)}%` };
};

function AnneauCertification() {
  return (
    <div
      data-reveal="zoom"
      role="img"
      aria-label="Les 20 quiz forment un anneau autour du certificat officiel ; 5 badges se débloquent en chemin."
      className="relative mx-auto size-[19rem] sm:size-[24rem] lg:size-[27rem]"
    >
      <svg viewBox="0 0 300 300" className="absolute inset-0 size-full -rotate-90">
        <circle
          cx="150"
          cy="150"
          r={RAYON}
          fill="none"
          stroke="rgb(255 255 255 / 0.08)"
          strokeWidth="16"
        />
        {Array.from({ length: QUIZ_CERTIFICATION }, (_, i) => (
          <circle
            key={i}
            cx="150"
            cy="150"
            r={RAYON}
            fill="none"
            stroke="var(--sun)"
            strokeWidth="16"
            strokeLinecap="round"
            strokeDasharray={`${SEGMENT - 9} ${TOUR - SEGMENT + 9}`}
            strokeDashoffset={-i * SEGMENT - 4.5}
            className="motion-safe:animate-allume"
            style={{ animationDelay: `${i * 0.21}s` }}
          />
        ))}
      </svg>

      {/* Le certificat, au centre de l'anneau. */}
      <div className="absolute inset-[18%] flex flex-col items-center justify-center rounded-full bg-linear-to-br from-white to-mist text-center text-ink shadow-[0_0_60px_-10px_rgb(255_210_80/0.6)] ring-8 ring-white/10">
        <span className="inline-flex size-16 items-center justify-center rounded-full bg-linear-to-br from-sun to-tangerine text-white shadow-card ring-4 ring-sun/30 motion-safe:animate-float sm:size-20">
          <Award className="size-8 sm:size-10" />
        </span>
        <p className="mt-3 text-[10px] font-extrabold uppercase tracking-[0.2em] text-logo-red sm:text-xs">
          Certificat officiel
        </p>
        <p className="font-display text-xl leading-tight text-logo-blue sm:text-2xl">
          Génie Imhotep
        </p>
        <p className="mt-1 font-display text-3xl tabular-nums text-primary sm:text-4xl">
          {QUIZ_CERTIFICATION} / {QUIZ_CERTIFICATION}
        </p>
        <p className="text-[11px] font-bold text-muted-foreground">quiz obligatoires réussis</p>
      </div>

      {/* Les 5 badges, posés sur l'anneau. */}
      {badges.map((p, i) => (
        <span
          key={p.n}
          title={`Badge ${p.n} · ${p.metal}`}
          style={placeBadge(p.apres)}
          className="absolute -translate-x-1/2 -translate-y-1/2"
        >
          <span
            style={{ animationDelay: `${-i * 1.2}s` }}
            className={`flex size-14 items-center justify-center rounded-full bg-linear-to-br text-white shadow-card ring-4 ring-night motion-safe:animate-float sm:size-16 ${p.fond}`}
          >
            <p.i className="size-6 sm:size-7" />
          </span>
          <span className="absolute left-1/2 top-full mt-1 -translate-x-1/2 whitespace-nowrap rounded-full bg-night px-2 py-0.5 ring-1 ring-white/20 text-[10px] font-extrabold uppercase tracking-wide text-white/80">
            {p.apres} quiz
          </span>
        </span>
      ))}

      <img
        src={mascotteImhotep}
        alt=""
        width={1414}
        height={2000}
        className="absolute -bottom-6 -left-4 w-20 -rotate-6 drop-shadow-xl sm:-left-10 sm:w-28"
      />
    </div>
  );
}

function Certification() {
  const [etape, setEtape] = useState(0);
  const e = etapes[etape] ?? etapes[0]!;

  return (
    <div className="min-h-screen overflow-x-clip bg-carnet text-ink">
      <SiteMotion />
      <SiteHeader />

      {/* Bannière « cérémonie » : nuit et or. À droite, l'anneau des 20 quiz s'allume segment après segment
          autour du certificat, et les 5 badges sont posés là où ils se débloquent (4, 8, 12, 16, 20). */}
      <section className="relative isolate overflow-hidden bg-night text-white">
        <div
          aria-hidden
          className="absolute left-1/2 top-[85%] -z-10 size-[56rem] -translate-x-1/2 -translate-y-1/2 bg-[repeating-conic-gradient(rgb(255_210_80/0.08)_0deg_5deg,transparent_5deg_15deg)] [mask-image:radial-gradient(circle,black_15%,transparent_65%)] motion-safe:animate-[spin_140s_linear_infinite] lg:left-[74%] lg:top-1/2"
        />
        <div
          aria-hidden
          className="absolute -left-32 top-1/3 -z-10 size-96 rounded-full bg-grape/40 blur-3xl motion-safe:animate-derive"
        />
        <div
          aria-hidden
          className="absolute left-1/2 top-[85%] -z-10 size-80 -translate-x-1/2 -translate-y-1/2 rounded-full bg-sun/25 blur-3xl lg:left-[74%] lg:top-1/2"
        />
        <DecorAnime />

        <div className="mx-auto grid max-w-7xl items-center gap-12 px-5 pb-20 pt-8 md:pt-12 lg:grid-cols-[1.1fr_1fr]">
          <div>
            <FilAriane rubrique="Gamification" page="Certification" clair />
            <div data-reveal="left" className="pt-10 lg:pt-14">
              <p className="inline-flex items-center gap-2 rounded-full bg-white/10 px-4 py-1.5 text-xs font-extrabold uppercase tracking-widest text-sun ring-1 ring-white/15">
                <Sparkles className="size-4" /> Certification Académie Génie Imhotep
              </p>
              <h1 className="mt-5 text-5xl leading-[0.95] md:text-7xl">
                <span className="block">Obtiens ta</span>
                <span className="block text-sun">certification</span>
              </h1>
              {/* Le ticket de la cagnotte, avec sa perforation. */}
              <p className="relative mt-6 inline-flex -rotate-2 items-center gap-3 rounded-2xl bg-logo-red py-3 pl-4 pr-6 shadow-card">
                <span
                  aria-hidden
                  className="absolute -left-2 top-1/2 size-4 -translate-y-1/2 rounded-full bg-night"
                />
                <span
                  aria-hidden
                  className="absolute -right-2 top-1/2 size-4 -translate-y-1/2 rounded-full bg-night"
                />
                <Trophy aria-hidden className="size-7 shrink-0 text-sun" />
                <span className="border-l-2 border-dashed border-white/40 pl-3 font-display text-xl leading-tight md:text-2xl">
                  & gagne jusqu’à <span className="text-sun">1 million FCFA</span> !
                </span>
              </p>
              <p className="mt-6 max-w-xl text-lg font-medium text-white/80">
                Élèves, collégiens, lycéens et visiteurs engagés : relève le défi des 20 quiz santé,
                décroche ton certificat officiel Génie Imhotep et tes badges, et tente de remporter
                des lots exceptionnels !
              </p>
              <ul className="mt-6 flex flex-wrap gap-2">
                {atouts.map((a) => (
                  <li
                    key={a.sur}
                    className="rounded-full bg-white/10 px-4 py-2 text-sm font-bold ring-1 ring-white/15 backdrop-blur-sm"
                  >
                    <span className="text-white/60">{a.sur} · </span>
                    {a.t}
                  </li>
                ))}
              </ul>
              <div className="mt-8 flex flex-wrap gap-3">
                {/* Connecté, le parcours s'ouvre ; sinon la connexion le demande d'abord. */}
                <a
                  href="/certification/parcours"
                  className="btn-fx inline-flex items-center gap-2 rounded-full bg-primary px-7 py-3 text-[15px] font-bold text-primary-foreground shadow-card"
                >
                  Lancer ma certification <ArrowRight className="size-4" />
                </a>
                <a
                  href="/connexion"
                  className="btn-fx rounded-full border-2 border-white px-7 py-3 text-[15px] font-bold hover:bg-white hover:text-ink"
                >
                  Se connecter
                </a>
              </div>
            </div>
          </div>

          <AnneauCertification />
        </div>
      </section>

      {/* Lots à gagner, sur un ruban jaune. */}
      <section aria-label="Lots à gagner" className="bg-sun">
        <ul className="mx-auto grid max-w-7xl gap-x-8 gap-y-4 px-5 py-7 md:grid-cols-3">
          {lots.map((l) => (
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
          sur="Guide officiel du parcours"
          bleu="Comment fonctionne"
          vert="la certification ?"
          large
        >
          Un parcours progressif pour renforcer tes connaissances en santé, prévention, valeurs et
          citoyenneté, puis les valider à travers une série de quiz.
        </EnTete>
        <ul className="mt-10 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {principes.map((p, i) => (
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
            sur="Méthodologie & préparation"
            bleu="La certification"
            vert="en 5 étapes"
            sombre
            centre
          />
          <ol className="relative mx-auto mt-12 flex max-w-4xl justify-between">
            <span aria-hidden className="absolute inset-x-6 top-7 h-1 rounded-full bg-white/15" />
            <span
              aria-hidden
              className="absolute left-6 top-7 h-1 rounded-full bg-sun transition-[width] duration-500"
              style={{
                width: `calc(${(etape / (etapes.length - 1)) * 100}% - ${(etape / (etapes.length - 1)) * 3}rem)`,
              }}
            />
            {etapes.map((x, i) => {
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
                Étape {String(etape + 1).padStart(2, "0")}
              </p>
              <h3 className="mt-1 text-3xl">{e.t}</h3>
              <p className="mt-2 text-lg font-medium text-white/85">{e.d}</p>
            </div>
            <a
              href="/bibliotheque"
              className="btn-fx inline-flex items-center gap-2 justify-self-start rounded-full bg-primary px-6 py-3 text-[15px] font-bold"
            >
              <BookOpen className="size-4" /> Accéder aux fascicules
            </a>
          </div>
        </div>
      </section>

      {/* Les 5 badges : des médailles sur fond nuit, et le barème du parcours. */}
      <section className="bg-night py-20 text-white">
        <div className="mx-auto max-w-7xl px-5">
          <EnTete
            sur="Récompenses progressives · 5 badges"
            bleu="Tes 5 badges"
            vert="officiels"
            sombre
          >
            Chaque badge débloqué rapporte {points(BAREME.badge.eleve)} points à toi et{" "}
            {points(BAREME.badge.club)} à ton Club Santé, une seule fois. Télécharge-le et
            partage-le sur tes réseaux sociaux.
          </EnTete>
          <Bareme />
          <ul className="mt-10 grid gap-5 sm:grid-cols-2 lg:grid-cols-5">
            {badges.map((p, i) => (
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
                  Badge {p.n} · {p.metal}
                </p>
                <h3 className="mt-1 font-display text-2xl leading-tight">{p.t}</h3>
                <p className="mt-1 text-sm font-bold text-primary">Après {p.apres} quiz réussis</p>
                <p className="mt-3 flex-1 text-sm font-medium text-white/70">{p.d}</p>
                <p className="mt-4 rounded-full bg-white/10 px-3 py-1 text-center text-xs font-bold">
                  {p.quiz}
                </p>
                <p className="mt-2 text-center text-sm font-extrabold text-sun">
                  {points(BAREME.badge.eleve)} pts · {points(BAREME.badge.club)} club
                </p>
              </li>
            ))}
          </ul>
          <p className="mt-6 text-center text-sm font-medium text-white/60">
            Noms et jalons provisoires : l’équipe nationale confirmera les conditions de déblocage
            des badges.
          </p>
        </div>
      </section>

      {/* Feuille de route : 5 thématiques de 4 quiz, chacune avec son badge (spec 034). */}
      <section id="parcours" className="mx-auto max-w-7xl scroll-mt-20 px-5 py-20">
        <div className="flex flex-wrap items-end justify-between gap-6">
          <EnTete
            sur="Parcours qualifiant officiel"
            bleu={`Les ${QUIZ_CERTIFICATION} quiz`}
            vert="obligatoires"
          />
          <p
            data-reveal
            className="flex max-w-md items-start gap-3 rounded-2xl bg-white p-4 text-sm font-semibold text-muted-foreground shadow-sm ring-1 ring-border"
          >
            <Lock className="mt-0.5 size-5 shrink-0 text-logo-red" />
            En mode visiteur, tu peux découvrir le parcours. Connecte-toi pour lancer les quiz et
            sauvegarder ta progression.
          </p>
        </div>
        <ol className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {badges.map((b, i) => (
            <li
              key={b.n}
              className={`flex flex-col rounded-[1.75rem] p-6 shadow-sm ring-1 ring-border ${i === badges.length - 1 ? "bg-linear-to-br from-sun/30 to-white" : "bg-white"}`}
            >
              <div className="flex items-center justify-between gap-3">
                <span className="font-display text-xl text-logo-blue">{b.metal}</span>
                <span className="rounded-full bg-sun px-2.5 py-0.5 text-xs font-extrabold text-ink">
                  {points(BAREME.quizCertification.eleve)} pts par quiz
                </span>
              </div>
              <span className="mt-4 self-start rounded-full bg-logo-blue/10 px-2.5 py-0.5 text-[11px] font-extrabold uppercase text-logo-blue">
                {b.quiz}
              </span>
              <h3 className="mt-2 flex-1 font-sans text-lg font-extrabold leading-snug">
                Badge {b.t}
              </h3>
              <p className="mt-3 text-sm font-medium text-muted-foreground">
                {b.d} Badge : {points(BAREME.badge.eleve)} points.
              </p>
              <a
                href="/connexion"
                className="mt-5 inline-flex items-center gap-2 self-start text-sm font-bold text-logo-blue hover:text-primary"
              >
                <Lock className="size-4" /> Débloquer le parcours
              </a>
            </li>
          ))}
        </ol>
        <div data-reveal className="mt-10 text-center">
          <p className="mx-auto max-w-2xl text-lg font-semibold">
            Une fois les 20 quiz réussis à 10/10, tu obtiens ta{" "}
            <span className="text-logo-blue">Certification Académie Génie Imhotep</span>.
          </p>
          <a
            href="/connexion"
            className="btn-fx mt-6 inline-flex items-center gap-2 rounded-full bg-primary px-8 py-3.5 text-[15px] font-bold text-primary-foreground shadow-card"
          >
            Se connecter / S’inscrire <ArrowRight className="size-4" />
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
    {
      t: "Chaque quiz obligatoire réussi",
      b: BAREME.quizCertification,
      d: "une seule fois par quiz",
    },
    { t: "Chaque badge débloqué", b: BAREME.badge, d: `${BADGES_CERTIFICATION} badges au plus` },
    { t: "Certification obtenue", b: BAREME.certification, d: "bonus final, une seule fois" },
  ];
  return (
    <ul className="mt-8 grid gap-3 md:grid-cols-3">
      {lignes.map((l) => (
        <li key={l.t} className="rounded-2xl bg-white/10 p-4 ring-1 ring-white/15">
          <p className="text-sm font-bold text-white/80">{l.t}</p>
          <p className="mt-1 font-display text-2xl text-sun">
            {points(l.b.eleve)} <span className="text-base text-white">pts</span>
          </p>
          <p className="text-sm font-semibold text-white/70">
            {points(l.b.club)} pour ton club · {l.d}
          </p>
        </li>
      ))}
    </ul>
  );
}
