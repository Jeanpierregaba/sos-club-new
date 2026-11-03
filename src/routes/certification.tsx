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
  type LucideIcon,
} from "lucide-react";
import { EnTete } from "@/components/EnTete";
import { FilAriane } from "@/components/FilAriane";
import { SiteHeader } from "@/components/SiteHeader";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteMotion, retard } from "@/components/SiteMotion";
import mascotteImhotep from "@/assets/mascotte-imhotep.webp";

export const Route = createFileRoute("/certification")({
  head: () => ({
    meta: [
      { title: "Certification — Club Santé SOS Docteur TV" },
      {
        name: "description",
        content:
          "La Certification Académie Génie Imhotep : 12 quiz santé, 4 paliers de badges, un certificat officiel et jusqu'à 1 million FCFA de lots.",
      },
      { property: "og:title", content: "Obtiens ta certification Génie Imhotep" },
    ],
  }),
  component: Certification,
});

const atouts = [
  { sur: "Parcours", t: "12 quiz santé" },
  { sur: "Distinction", t: "Certificat + 5 badges" },
  { sur: "Cagnotte", t: "1 000 000 FCFA" },
];

const lots = [
  { i: Laptop, t: "Ordinateurs portables neufs", d: "pour exceller dans tes études" },
  { i: Smartphone, t: "Smartphones & tablettes", d: "pour les champions des 12 quiz santé" },
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
    sur: "12 quiz thématiques",
    t: "Un programme en 12 quiz obligatoires",
    d: "AIMES-AFRIQUE et SOS Docteur TV, Clubs Santé et Génie Imhotep, Journées mondiales de la santé, EVSS, santé générale et santé publique pratique.",
    plus: "6 grands pôles",
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
    d: "Terminer les 12 quiz obligatoires, remplir les conditions de réussite et obtenir la Certification Académie Génie Imhotep – Clubs Santé SOS Docteur TV.",
  },
];

// `fond` : le dégradé de la médaille.
const paliers: {
  n: string;
  metal: string;
  i: LucideIcon;
  t: string;
  seuil: string;
  d: string;
  quiz: string;
  fond: string;
}[] = [
  {
    n: "01",
    metal: "Bronze",
    i: Medal,
    t: "Ambassadeur junior santé",
    seuil: "3 / 12",
    d: "Pour la réussite sans faute du 1er palier : fondamentaux AIMES-AFRIQUE, Clubs Santé et Journées mondiales.",
    quiz: "Quiz 1, 2, 3",
    fond: "from-tangerine to-bark",
  },
  {
    n: "02",
    metal: "Argent",
    i: Medal,
    t: "Pair éducateur citoyenneté & santé",
    seuil: "6 / 12",
    d: "Pour la validation à 100 % du 2e palier : Journées mondiales de la santé, valeurs et connaissance du corps.",
    quiz: "Quiz 4, 5, 6",
    fond: "from-[oklch(0.82_0.02_257)] to-[oklch(0.58_0.03_257)]",
  },
  {
    n: "03",
    metal: "Or",
    i: Crown,
    t: "Champion prévention & hygiène",
    seuil: "9 / 12",
    d: "Pour la réussite à 100 % du 3e palier : prévention EVSS, hygiène bucco-dentaire, sommeil et nutrition.",
    quiz: "Quiz 7, 8, 9",
    fond: "from-sun to-tangerine",
  },
  {
    n: "04",
    metal: "Diamant Imhotep",
    i: Gem,
    t: "Maître certifié Génie Imhotep",
    seuil: "12 / 12",
    d: "Distinction suprême, après la validation intégrale des 12 quiz à 100 %. Elle ouvre droit au certificat officiel.",
    quiz: "Quiz 10, 11, 12",
    fond: "from-sky to-grape",
  },
];

type Groupe = "aimes" | "jms" | "evss" | "sante";

const groupes: Record<Groupe, { t: string; c: string }> = {
  aimes: { t: "AIMES & Clubs Santé", c: "text-logo-blue bg-logo-blue/10" },
  jms: { t: "Journées mondiales", c: "text-tangerine bg-tangerine/10" },
  evss: { t: "EVSS", c: "text-rose bg-rose/10" },
  sante: { t: "Santé générale & publique", c: "text-primary bg-primary/10" },
};

const parcours: { g: Groupe; sur: string; t: string; themes: string; pts: number }[] = [
  {
    g: "aimes",
    sur: "Institutionnel & vision",
    t: "AIMES-AFRIQUE, Dr Kodom et SOS Docteur TV",
    themes: "ONG AIMES-AFRIQUE · Le Docteur Kodom · SOS Docteur TV",
    pts: 150,
  },
  {
    g: "aimes",
    sur: "Clubs Santé & émulation",
    t: "Club Santé SOS Docteur TV et Génie Imhotep",
    themes: "Le Club Santé · Organisation du club · Les 7 axes",
    pts: 150,
  },
  {
    g: "jms",
    sur: "JMS internationales",
    t: "Les Journées mondiales de la santé (janvier à mai)",
    themes: "Janvier et février · Avril · Mai",
    pts: 150,
  },
  {
    g: "jms",
    sur: "JMS internationales",
    t: "Les Journées mondiales de la santé (juin à décembre & révision)",
    themes: "Juin à décembre · Révision",
    pts: 150,
  },
  {
    g: "evss",
    sur: "EVSS & citoyenneté",
    t: "Genre, égalité, valeurs & droits de l’enfant",
    themes: "Genre, égalité et valeurs",
    pts: 150,
  },
  {
    g: "evss",
    sur: "EVSS & anatomie",
    t: "Puberté, connaissance du corps & cycle menstruel",
    themes: "Puberté et corps",
    pts: 150,
  },
  {
    g: "evss",
    sur: "EVSS & prévention",
    t: "IST, VIH/sida, contraception & planification familiale",
    themes: "IST et VIH/sida",
    pts: 150,
  },
  {
    g: "evss",
    sur: "EVSS & protection",
    t: "Grossesse précoce, consentement, violences & compétences de vie",
    themes: "Consentement et protection",
    pts: 150,
  },
  {
    g: "sante",
    sur: "Hygiène & nutrition",
    t: "Hygiène corporelle, salubrité & alimentation équilibrée",
    themes: "Hygiène corporelle · Nutrition",
    pts: 150,
  },
  {
    g: "sante",
    sur: "Physiologie & épidémies",
    t: "Le corps humain & les maladies infectieuses courantes",
    themes: "Le corps humain",
    pts: 150,
  },
  {
    g: "sante",
    sur: "Bien-être & prévention",
    t: "Maladies non transmissibles, addictions & santé mentale",
    themes: "Prévention et bien-être",
    pts: 150,
  },
  {
    g: "sante",
    sur: "Épreuve finale & secourisme",
    t: "Vaccination, premiers secours & système de santé au Togo",
    themes: "Vaccination · Premiers secours · Système de santé",
    pts: 250,
  },
];

function Certification() {
  const [etape, setEtape] = useState(0);
  const [groupe, setGroupe] = useState<Groupe | null>(null);
  const e = etapes[etape] ?? etapes[0]!;

  return (
    <div className="min-h-screen overflow-x-clip bg-carnet text-ink">
      <SiteMotion />
      <SiteHeader />

      {/* Bannière : le titre à gauche, le certificat officiel en vedette à droite. */}
      <section className="relative isolate overflow-hidden bg-linear-to-b from-mist to-mist-soft">
        <div
          aria-hidden
          className="absolute right-[8%] top-1/2 -z-10 size-[32rem] -translate-y-1/2 rounded-full bg-sun/30 blur-3xl"
        />
        <div className="mx-auto grid max-w-7xl items-center gap-12 px-5 pb-20 pt-8 md:pt-12 lg:grid-cols-[1.1fr_1fr]">
          <div>
            <FilAriane rubrique="Gamification" page="Certification" />
            <div data-reveal="left" className="pt-12">
              <p className="flex items-center gap-3 text-sm font-extrabold uppercase tracking-widest text-logo-red">
                <Sparkles className="size-4" /> Certification & récompenses
              </p>
              <h1 className="mt-4 text-5xl leading-[0.95] md:text-7xl">
                <span className="block text-logo-blue">Obtiens ta certification</span>
                <span className="mt-2 block text-3xl text-primary md:text-5xl">
                  & gagne jusqu’à 1 million FCFA !
                </span>
              </h1>
              <p className="mt-6 max-w-xl text-lg font-medium text-muted-foreground">
                Élèves, collégiens, lycéens et visiteurs engagés : relève le défi des 12 quiz santé,
                décroche ton certificat officiel Génie Imhotep et tes badges, et tente de remporter
                des lots exceptionnels !
              </p>
              <dl className="mt-8 grid max-w-xl grid-cols-3 divide-x rounded-2xl bg-white shadow-sm ring-1 ring-border">
                {atouts.map((a) => (
                  <div key={a.sur} className="p-4">
                    <dt className="text-[11px] font-extrabold uppercase tracking-wider text-muted-foreground">
                      {a.sur}
                    </dt>
                    <dd className="mt-1 font-display text-lg leading-tight text-logo-blue md:text-xl">
                      {a.t}
                    </dd>
                  </div>
                ))}
              </dl>
              <div className="mt-8 flex flex-wrap gap-3">
                <a
                  href="#parcours"
                  className="btn-fx inline-flex items-center gap-2 rounded-full bg-primary px-7 py-3 text-[15px] font-bold text-primary-foreground shadow-card"
                >
                  Lancer ma certification <ArrowRight className="size-4" />
                </a>
                <a
                  href="/connexion"
                  className="btn-fx rounded-full border-2 border-logo-blue px-7 py-3 text-[15px] font-bold text-logo-blue hover:bg-logo-blue hover:text-white"
                >
                  Se connecter
                </a>
              </div>
            </div>
          </div>

          <div data-reveal="right" className="relative mx-auto w-full max-w-md">
            <div className="relative -rotate-3 rounded-[1.75rem] bg-white p-3 shadow-card">
              <div className="relative overflow-hidden rounded-[1.25rem] border-4 border-double border-sun p-8 text-center">
                <div
                  aria-hidden
                  className="absolute inset-0 -z-0 bg-[radial-gradient(circle_at_50%_0%,color-mix(in_oklch,var(--sun)_18%,transparent),transparent_60%)]"
                />
                <p className="relative text-xs font-extrabold uppercase tracking-[0.25em] text-logo-red">
                  Distinction officielle
                </p>
                <p className="relative mt-3 font-display text-3xl leading-tight text-logo-blue">
                  Académie Génie Imhotep
                </p>
                <p className="relative mt-1 text-sm font-bold text-muted-foreground">
                  Clubs Santé SOS Docteur TV
                </p>
                <p className="relative mt-8 font-hand text-2xl text-ink/70">Décerné à</p>
                <p className="relative mx-auto mt-1 h-8 w-3/4 border-b-2 border-dotted border-ink/30" />
                <div className="relative mt-8 flex items-end justify-between">
                  <span className="text-left text-[11px] font-bold leading-tight text-muted-foreground">
                    12 / 12 quiz
                    <br />
                    validés à 100 %
                  </span>
                  <span className="inline-flex size-20 items-center justify-center rounded-full bg-linear-to-br from-sun to-tangerine text-white shadow-card ring-4 ring-sun/30">
                    <Award className="size-10" />
                  </span>
                </div>
              </div>
            </div>
            <img
              src={mascotteImhotep}
              alt=""
              width={1414}
              height={2000}
              className="absolute -right-6 -top-16 w-24 rotate-6 drop-shadow-xl md:-right-10 md:w-32"
            />
          </div>
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

      {/* Les 4 paliers de badges : des médailles sur fond nuit. */}
      <section className="bg-night py-20 text-white">
        <div className="mx-auto max-w-7xl px-5">
          <EnTete
            sur="Récompenses progressives · 4 paliers"
            bleu="Tes badges"
            vert="de paliers"
            sombre
          >
            Chaque palier de 3 quiz validés à 100 % débloque un badge officiel, à télécharger et à
            partager sur tes réseaux sociaux.
          </EnTete>
          <ul className="mt-10 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
            {paliers.map((p, i) => (
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
                  Palier {p.n} · {p.metal}
                </p>
                <h3 className="mt-1 font-display text-2xl leading-tight">{p.t}</h3>
                <p className="mt-1 text-sm font-bold text-primary">{p.seuil} quiz à 100 %</p>
                <p className="mt-3 flex-1 text-sm font-medium text-white/70">{p.d}</p>
                <p className="mt-4 rounded-full bg-white/10 px-3 py-1 text-center text-xs font-bold">
                  {p.quiz}
                </p>
              </li>
            ))}
          </ul>
        </div>
      </section>

      {/* Feuille de route des 12 quiz, filtrable par thématique. */}
      <section id="parcours" className="mx-auto max-w-7xl scroll-mt-20 px-5 py-20">
        <div className="flex flex-wrap items-end justify-between gap-6">
          <EnTete sur="Parcours qualifiant officiel" bleu="Les 12 quiz" vert="obligatoires" />
          <p
            data-reveal
            className="flex max-w-md items-start gap-3 rounded-2xl bg-white p-4 text-sm font-semibold text-muted-foreground shadow-sm ring-1 ring-border"
          >
            <Lock className="mt-0.5 size-5 shrink-0 text-logo-red" />
            En mode visiteur, tu peux découvrir les 12 quiz. Connecte-toi pour les lancer et
            sauvegarder ta progression.
          </p>
        </div>
        <div data-reveal className="mt-8 flex flex-wrap gap-2">
          {([null, ...Object.keys(groupes)] as (Groupe | null)[]).map((g) => {
            const n = g ? parcours.filter((x) => x.g === g).length : parcours.length;
            return (
              <button
                key={g ?? "tous"}
                type="button"
                aria-pressed={groupe === g}
                onClick={() => setGroupe(g)}
                className={`rounded-full px-4 py-2 text-sm font-bold transition active:scale-95 ${
                  groupe === g
                    ? "bg-logo-blue text-white shadow-card"
                    : "bg-white ring-1 ring-border hover:ring-logo-blue/40"
                }`}
              >
                {g ? groupes[g].t : "Tous les quiz"} ({n})
              </button>
            );
          })}
        </div>
        <ol className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {parcours.map((q, i) =>
            groupe && q.g !== groupe ? null : (
              <li
                key={q.t}
                className={`flex flex-col rounded-[1.75rem] p-6 shadow-sm ring-1 ring-border ${i === 11 ? "bg-linear-to-br from-sun/30 to-white" : "bg-white"}`}
              >
                <div className="flex items-center justify-between gap-3">
                  <span className="font-display text-xl text-logo-blue">
                    Étape {String(i + 1).padStart(2, "0")}
                    <span className="text-muted-foreground"> / 12</span>
                  </span>
                  <span className="rounded-full bg-sun px-2.5 py-0.5 text-xs font-extrabold text-ink">
                    +{q.pts} pts
                  </span>
                </div>
                <span
                  className={`mt-4 self-start rounded-full px-2.5 py-0.5 text-[11px] font-extrabold uppercase ${groupes[q.g].c}`}
                >
                  {q.sur}
                </span>
                <h3 className="mt-2 flex-1 font-sans text-lg font-extrabold leading-snug">{q.t}</h3>
                <p className="mt-3 text-sm font-medium text-muted-foreground">{q.themes}</p>
                <a
                  href="/connexion"
                  className="mt-5 inline-flex items-center gap-2 self-start text-sm font-bold text-logo-blue hover:text-primary"
                >
                  <Lock className="size-4" /> Débloquer ce quiz
                </a>
              </li>
            ),
          )}
        </ol>
        <div data-reveal className="mt-10 text-center">
          <p className="mx-auto max-w-2xl text-lg font-semibold">
            Une fois les 12 quiz réalisés et les conditions de réussite remplies, tu obtiens ta{" "}
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
