import { useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import {
  Accessibility,
  ArrowRight,
  Check,
  ChevronRight,
  GraduationCap,
  HeartPulse,
  MapPinned,
  Users,
  CircleCheck,
  Eye,
  Gem,
  HeartHandshake,
  House,
  Laptop,
  Megaphone,
  MessageCircleQuestion,
  Quote,
  Rocket,
  School,
  Smartphone,
  Target,
  Trophy,
} from "lucide-react";
import { EnTete } from "@/components/EnTete";
import { SiteHeader } from "@/components/SiteHeader";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteMotion, retard } from "@/components/SiteMotion";
import banniere from "@/assets/club-sante-banniere.jpg";
import mascottesTrophees from "@/assets/mascottes-trophees.webp";
import mascotteImhotep from "@/assets/mascotte-imhotep.webp";
import kodom from "@/assets/initiateur-kodom.webp";

export const Route = createFileRoute("/club-sante")({
  head: () => ({
    meta: [
      { title: "Le Club Santé — Club Santé SOS Docteur TV" },
      {
        name: "description",
        content:
          "Vision, objectifs, règles d'adhésion et fonctionnement des Clubs Santé SOS Docteur TV dans les collèges et lycées du Togo.",
      },
      { property: "og:title", content: "Le Club Santé SOS Docteur TV" },
    ],
  }),
  component: ClubSante,
});

// Repères posés sous la bannière.
const reperesBanniere = [
  { i: MapPinned, n: "7", t: "Directions régionales de l’éducation", c: "bg-sky" },
  { i: HeartPulse, n: "+800", t: "Clubs santé actifs", c: "bg-primary" },
  { i: Users, n: "21", t: "Membres par bureau de club", c: "bg-tangerine" },
  { i: GraduationCap, n: "3", t: "Enseignants encadreurs au minimum", c: "bg-grape" },
];

// Les sigles des ministères tiennent lieu de logos en attendant les fichiers officiels.
const ministeres = [
  { t: "MEPSTA / MEN", c: "border-logo-blue text-logo-blue", r: "-rotate-6" },
  { t: "MSHPAUS", c: "border-primary text-primary", r: "rotate-3" },
  { t: "MASPFA", c: "border-tangerine text-tangerine", r: "rotate-6" },
  { t: "MESR", c: "border-grape text-grape", r: "-rotate-3" },
];

const lots = [
  {
    i: Trophy,
    tag: "Grand prix & bourses",
    t: "1 million FCFA",
    d: "Cagnotte exceptionnelle, bourses scolaires et appuis financiers pour récompenser l’excellence des jeunes certifiés.",
  },
  {
    i: Laptop,
    tag: "Numérique & études",
    t: "Des ordinateurs portables",
    d: "Des PC portables neufs pour accompagner tes recherches scientifiques, tes cours et tes projets numériques.",
  },
  {
    i: Smartphone,
    tag: "High-tech & kits",
    t: "Des téléphones & lots",
    d: "Smartphones dernière génération, tablettes éducatives, médailles et kits officiels Clubs Santé SOS DOCTEUR TV.",
  },
];

const objectifs = [
  {
    tag: "Santé & vocations",
    t: "Promouvoir la culture générale en santé et susciter des vocations auprès des jeunes",
    c: "bg-sky",
  },
  {
    tag: "Leadership",
    t: "Développer le leadership personnel et transformationnel chez les jeunes apprenants",
    c: "bg-tangerine",
  },
  {
    tag: "Citoyenneté",
    t: "Promouvoir la citoyenneté et le changement de comportement dans la communauté",
    c: "bg-primary",
  },
  {
    tag: "Innovation",
    t: "Stimuler l’innovation et l’esprit d’initiative chez les jeunes",
    c: "bg-grape",
  },
  {
    tag: "Inclusion & équité",
    t: "Promouvoir l’inclusion, la masculinité positive et l’équité chez les jeunes",
    c: "bg-rose",
  },
];

const valeurs = [
  { t: "Excellence", c: "bg-logo-blue" },
  { t: "Émulation", c: "bg-primary" },
  { t: "Engagement", c: "bg-tangerine" },
  { t: "Innovation", c: "bg-grape" },
  { t: "Leadership", c: "bg-rose" },
];

const jalons = [
  {
    date: "19 – 29 mars 2024",
    t: "Tournée de lancement de la création des Clubs Santé SOS DOCTEUR TV dans les 7 DRE",
    c: "bg-sky",
  },
  {
    date: "24 mars 2025",
    t: "Lancement des activités des Clubs Santé SOS DOCTEUR TV",
    c: "bg-primary",
  },
  {
    date: "02 avril 2026",
    t: "Lancement de la 1re édition du championnat GÉNIE IMHOTEP",
    c: "bg-tangerine",
  },
];

const educations = [
  {
    i: School,
    tag: "Système structuré",
    t: "Éducation formelle",
    d: "Elle se déroule dans le cadre du système éducatif structuré, du préscolaire jusqu’à l’université.",
    coeur: false,
  },
  {
    i: HeartHandshake,
    tag: "Cœur des Clubs Santé",
    t: "Éducation non formelle",
    d: "Elle regroupe les activités éducatives organisées en dehors de l’enseignement formel, notamment les activités parascolaires, périscolaires et extrascolaires.",
    coeur: true,
  },
  {
    i: House,
    tag: "Vie quotidienne",
    t: "Éducation informelle",
    d: "Elle résulte des apprentissages du quotidien, notamment à la maison, dans le quartier, à travers les réseaux sociaux et les différentes expériences de la vie.",
    coeur: false,
  },
];

const regles = [
  "Chaque club santé est encadré par au moins 03 enseignants volontaires et bénévoles.",
  "Tout élève régulièrement inscrit peut adhérer au club.",
  "L’adhésion est libre et volontaire. Une liste des membres doit obligatoirement être tenue.",
  "Une fois inscrit, la participation aux activités des « commissions / composantes / axes » est obligatoire.",
  "Le nombre d’élèves du Club Santé SOS DOCTEUR TV n’est pas limité.",
  "Le club est ouvert aux garçons comme aux filles, mais l’enrôlement des filles est encouragé.",
];

const bureau = [
  "1 Président(e) et son/sa Adjoint(e)",
  "1 Secrétaire Général(e) et son/sa Adjoint(e)",
  "1 Trésorier(ère) Général(e) et son/sa Adjoint(e)",
  "1 Coordonnateur(trice) par commission (Axe 1 à Axe 7), ainsi que leurs Adjoints(es) respectifs(ves)",
  "1 Conseiller(ère)",
];

// Couleur de l'étiquette de chaque thème de la FAQ.
const themes = {
  Adhésion: "bg-sky",
  Bureau: "bg-rose",
  Fonctionnement: "bg-tangerine",
  Championnat: "bg-grape",
} as const;

const faq: { theme: keyof typeof themes; q: string; r: string }[] = [
  {
    theme: "Adhésion",
    q: "Qui peut adhérer au Club Santé dans un collège ou un lycée ?",
    r: "Tout élève régulièrement inscrit peut adhérer au club : l’adhésion est libre et volontaire, et le nombre de membres n’est pas limité. Le club est ouvert aux garçons comme aux filles, mais l’enrôlement des filles est encouragé. Une liste des membres doit être tenue, et chaque membre participe aux activités des commissions. Le club est encadré par au moins 03 enseignants volontaires et bénévoles.",
  },
  {
    theme: "Bureau",
    q: "Combien de membres composent obligatoirement le bureau du club ?",
    r: "Tout bureau du « Club Santé SOS DOCTEUR TV » compte 21 personnes, dont au moins 11 filles et au plus 10 garçons : 1 Président(e), 1 Secrétaire Général(e), 1 Trésorier(ère) Général(e) et leurs Adjoint(e)s ; 1 Coordonnateur(trice) par commission (Axe 1 à Axe 7) et leurs Adjoint(e)s ; 1 Conseiller(ère).",
  },
  {
    theme: "Bureau",
    q: "Les élèves vivant avec un handicap peuvent-ils faire partie du bureau ?",
    r: "Oui, tout à fait ! Le bureau doit être inclusif, notamment en favorisant la participation des personnes vivant avec un handicap, et comporter de préférence plus de filles que de garçons.",
  },
  {
    theme: "Adhésion",
    q: "Tous les établissements du secondaire doivent-ils avoir un club ?",
    r: "Oui. Selon les directives nationales, tous les établissements du secondaire (collèges et lycées) du Togo sont tenus d’avoir un club santé.",
  },
  {
    theme: "Fonctionnement",
    q: "Comment s’organisent les réunions et activités du club ?",
    r: "Le bureau se réunit en session ordinaire une fois par mois, et en session extraordinaire sur convocation du Président ou à la demande de la majorité des membres. Les activités de sensibilisation, journées de salubrité et causeries éducatives sont programmées en dehors des heures de cours pour respecter le calendrier pédagogique.",
  },
  {
    theme: "Fonctionnement",
    q: "Quel est le rôle des 3 enseignants encadreurs ?",
    r: "Les enseignants tuteurs volontaires assurent la supervision pédagogique, facilitent les autorisations avec la direction de l’établissement, valident les plans d’action trimestriels et accompagnent la préparation des élèves aux compétitions et activités communautaires.",
  },
  {
    theme: "Adhésion",
    q: "Comment un club santé est-il officiellement enregistré ?",
    r: "Le chef d’établissement transmet le procès-verbal d’installation du bureau et la liste des membres à la Direction Régionale de l’Éducation (DRE) ainsi qu’à la coordination nationale SOS DOCTEUR TV / AIMES-AFRIQUE, pour l’obtention de l’attestation officielle d’affiliation.",
  },
  {
    theme: "Championnat",
    q: "Qu’est-ce que le Championnat national GÉNIE IMHOTEP ?",
    r: "C’est la compétition nationale d’excellence scolaire retransmise sur SOS DOCTEUR TV, qui confronte les clubs santé sur la culture générale en santé, les gestes qui sauvent et les projets d’impact communautaire. Lancement officiel de la 1re édition : 02 avril 2026.",
  },
];

// FAQ : les thèmes en filtre, les questions à gauche, la réponse dans une grande bulle à droite.
// Sur mobile, la réponse s'ouvre sous la question choisie.
function FaqSection() {
  const [theme, setTheme] = useState<keyof typeof themes | null>(null);
  const [ouverte, setOuverte] = useState(0);
  const visibles = faq.map((f, i) => ({ ...f, i })).filter((f) => !theme || f.theme === theme);
  const active = faq[ouverte];
  const filtrer = (t: keyof typeof themes | null) => {
    setTheme(t);
    setOuverte(faq.findIndex((f) => !t || f.theme === t));
  };

  return (
    <section
      id="faq"
      className="relative isolate mt-20 scroll-mt-20 overflow-hidden bg-[color-mix(in_oklch,var(--sun)_16%,white)] py-20 md:py-24"
    >
      <MessageCircleQuestion
        aria-hidden
        className="absolute -left-16 top-10 -z-10 size-72 -rotate-12 text-sun/40"
      />
      <div className="mx-auto max-w-7xl px-5">
        <EnTete
          sur="Réponses & informations pratiques"
          bleu="Foire aux questions"
          vert="& vie des clubs"
          centre
        >
          Tout ce que tu dois savoir pour démarrer, animer sereinement ton Club Santé et participer
          au championnat.
        </EnTete>

        <div data-reveal className="mt-8 flex flex-wrap justify-center gap-2">
          {([null, ...Object.keys(themes)] as (keyof typeof themes | null)[]).map((t) => (
            <button
              key={t ?? "tout"}
              type="button"
              aria-pressed={theme === t}
              onClick={() => filtrer(t)}
              className={`rounded-full px-5 py-2 text-sm font-extrabold transition duration-200 active:scale-95 ${
                theme === t
                  ? "bg-logo-blue text-white shadow-card"
                  : "bg-white text-logo-blue ring-1 ring-logo-blue/15 hover:ring-logo-blue/40"
              }`}
            >
              {t ?? "Tout"}
            </button>
          ))}
        </div>

        <div className="mt-10 grid gap-8 lg:grid-cols-[1fr_1.15fr] lg:gap-10">
          <ul data-reveal="left" className="grid content-start gap-3">
            {visibles.map((f) => {
              const choisie = f.i === ouverte;
              return (
                <li key={f.q}>
                  <button
                    type="button"
                    aria-expanded={choisie}
                    aria-controls={`faq-${f.i}`}
                    onClick={() => setOuverte(f.i)}
                    className={`group flex w-full items-center gap-4 rounded-2xl p-4 text-left font-bold leading-snug transition duration-300 ${
                      choisie
                        ? "bg-logo-blue text-white shadow-card"
                        : "bg-white hover:-translate-y-0.5 hover:shadow-card"
                    }`}
                  >
                    <span
                      className={`inline-flex size-10 shrink-0 items-center justify-center rounded-xl font-display text-lg ${
                        choisie ? "bg-sun text-ink" : "bg-mist text-logo-blue"
                      }`}
                    >
                      {String(f.i + 1).padStart(2, "0")}
                    </span>
                    <span className="flex-1">{f.q}</span>
                    <ArrowRight
                      className={`size-5 shrink-0 transition duration-300 ${
                        choisie
                          ? "text-sun max-lg:-rotate-90"
                          : "text-logo-blue/40 group-hover:translate-x-1 max-lg:rotate-90"
                      }`}
                    />
                  </button>
                  {choisie && (
                    <p
                      id={`faq-${f.i}`}
                      className="mx-2 rounded-b-2xl bg-white px-5 pb-5 pt-4 text-[15px] font-medium leading-relaxed text-muted-foreground lg:hidden"
                    >
                      {f.r}
                    </p>
                  )}
                </li>
              );
            })}
          </ul>

          {active && (
            <div data-reveal="right" className="hidden lg:block">
              <article
                aria-live="polite"
                className="sticky top-24 overflow-hidden rounded-[2rem] bg-white shadow-card"
              >
                <div className="p-8 md:p-10">
                  <div className="flex items-center justify-between gap-4">
                    <span
                      className={`rounded-full px-3 py-1 text-xs font-extrabold uppercase text-white ${themes[active.theme]}`}
                    >
                      {active.theme}
                    </span>
                    <span className="font-display text-5xl leading-none text-sun">
                      {String(ouverte + 1).padStart(2, "0")}
                    </span>
                  </div>
                  <h3 className="mt-5 text-3xl leading-tight text-logo-blue">{active.q}</h3>
                  <p className="mt-4 text-lg font-medium leading-relaxed text-muted-foreground">
                    {active.r}
                  </p>
                </div>
                <div className="flex items-end gap-4 bg-mist-soft pl-8 pr-4 pt-4 md:pl-10">
                  <p className="mb-8 flex-1 rounded-2xl rounded-br-none bg-white p-4 text-sm font-bold shadow-sm">
                    Tu ne trouves pas ta réponse ? Pose ta question à tes encadreurs : ils sont là
                    pour t’accompagner.
                  </p>
                  <img
                    src={mascotteImhotep}
                    alt=""
                    loading="lazy"
                    width={1414}
                    height={2000}
                    className="-mb-16 w-32 shrink-0 drop-shadow-xl"
                  />
                </div>
              </article>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}

function ClubSante() {
  return (
    <div className="min-h-screen overflow-x-clip bg-carnet text-ink">
      <SiteMotion />
      <SiteHeader />

      {/* Bannière : la photo des clubs en plein écran, un voile bleu nuit pour le texte, puis les repères en carte qui chevauche le bas. */}
      <section className="relative isolate overflow-hidden text-white">
        <img
          src={banniere}
          alt="Élèves des Clubs Santé en t-shirts bleus, verts et rouges, drapeaux du Togo en main"
          width={2000}
          height={1160}
          className="absolute inset-0 -z-20 size-full object-cover object-[60%_30%] transition-transform duration-[6s] ease-out starting:scale-110"
        />
        <div
          aria-hidden
          className="absolute inset-0 -z-10 bg-linear-to-t from-night from-30% via-night/70 to-night/10 lg:bg-linear-to-r lg:from-0% lg:from-night/95 lg:via-logo-blue/70 lg:to-transparent"
        />
        <div className="mx-auto flex min-h-[38rem] max-w-7xl flex-col px-5 pb-36 pt-8 md:pt-12 lg:min-h-[44rem] lg:pb-40">
          <nav aria-label="Fil d’Ariane" className="text-sm font-semibold text-white/70">
            <ol className="flex flex-wrap items-center gap-1.5">
              <li>
                <a href="/" className="hover:text-white">
                  Accueil
                </a>
              </li>
              <li className="flex items-center gap-1.5">
                <ChevronRight aria-hidden className="size-3.5" /> Vie du club
              </li>
              <li aria-current="page" className="flex items-center gap-1.5 text-white">
                <ChevronRight aria-hidden className="size-3.5" /> Club santé
              </li>
            </ol>
          </nav>

          <div data-reveal="left" className="mt-auto max-w-2xl pt-16">
            <span className="inline-flex rounded-full bg-sun px-4 py-1.5 text-xs font-extrabold uppercase tracking-wide text-ink">
              Slogan officiel du programme
            </span>
            <h1 className="mt-5 text-5xl leading-[0.95] [text-shadow:0_2px_16px_rgb(0_0_0/0.55)] md:text-7xl">
              <span className="block">Le Club Santé</span>
              <span className="block text-primary">SOS Docteur TV</span>
            </h1>
            <p className="mt-6 font-hand text-3xl leading-tight text-sun md:text-4xl">
              « Ensemble pour une génération de jeunes en bonne santé, responsable et épanouie »
            </p>
            <p className="mt-5 max-w-xl text-lg font-medium text-white/85">
              AIMES-AFRIQUE & SOS DOCTEUR TV mobilisent la jeunesse scolaire dans les collèges et
              lycées des 7 Directions Régionales de l’Éducation (DRE) du Togo.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <a
                href="#adhesion"
                className="btn-fx inline-flex items-center gap-2 rounded-full bg-primary px-7 py-3 text-[15px] font-bold text-primary-foreground shadow-card"
              >
                Règles d’adhésion <ArrowRight className="size-4" />
              </a>
              <a
                href="#piliers"
                className="btn-fx rounded-full border-2 border-white px-7 py-3 text-[15px] font-bold hover:bg-white hover:text-logo-blue"
              >
                Vision des clubs
              </a>
            </div>
          </div>
        </div>
      </section>

      <div className="relative z-10 mx-auto -mt-24 max-w-7xl px-5">
        <ul
          data-reveal
          className="grid grid-cols-2 gap-px overflow-hidden rounded-[2rem] bg-border shadow-card lg:grid-cols-4"
        >
          {reperesBanniere.map((r) => (
            <li key={r.t} className="flex items-start gap-4 bg-card p-5 sm:items-center md:p-7">
              <span
                className={`${r.c} hidden size-12 shrink-0 items-center justify-center rounded-2xl text-white sm:inline-flex`}
              >
                <r.i className="size-6" />
              </span>
              <span>
                <span className="block font-display text-3xl leading-none text-logo-blue md:text-4xl">
                  {r.n}
                </span>
                <span className="mt-1 block text-sm font-bold leading-snug">{r.t}</span>
              </span>
            </li>
          ))}
        </ul>
      </div>

      {/* Cadre réglementaire : les sigles des ministères posés comme des tampons officiels. */}
      <section id="cadre" className="mx-auto max-w-7xl scroll-mt-20 px-5 pt-14">
        <div
          data-reveal
          className="grid items-center gap-10 rounded-[2rem] bg-card p-7 shadow-card md:p-12 lg:grid-cols-[1.25fr_1fr]"
        >
          <div>
            <p className="flex items-center gap-3 text-sm font-extrabold uppercase tracking-widest text-logo-red">
              <span className="h-1 w-8 rounded-full bg-primary" />
              Cadre réglementaire & accords interministériels
            </p>
            <h2 className="mt-3 text-4xl md:text-5xl">
              <span className="text-logo-blue">Autorisations officielles</span>{" "}
              <span className="text-primary">& cadre ministériel</span>
            </h2>
            <p className="mt-4 text-lg font-medium text-muted-foreground">
              La mise en place et le fonctionnement de ces clubs respectent les procédures de
              création suivantes et s’articulent autour des notes de service du MEPS/MEN, du MSHPAUS
              et du MSGFPE.
            </p>
            <ul className="mt-6 grid gap-3">
              {[
                "Notes de service interministérielles",
                "Reconnaissance officielle dans les 7 DRE du Togo",
                "Encadrement certifié par au moins 3 enseignants tuteurs",
              ].map((t) => (
                <li key={t} className="flex items-center gap-3 font-bold">
                  <CircleCheck className="size-6 shrink-0 text-primary" /> {t}
                </li>
              ))}
            </ul>
          </div>
          <div className="rounded-3xl bg-mist p-6 md:p-8">
            <p className="text-center text-xs font-extrabold uppercase tracking-widest text-logo-blue">
              Ministères & partenaires officiels
            </p>
            <ul className="mt-6 grid grid-cols-2 gap-5">
              {ministeres.map((m, i) => (
                <li
                  key={m.t}
                  data-reveal="zoom"
                  style={retard(i)}
                  className={`mx-auto flex aspect-square w-full max-w-36 items-center justify-center rounded-full border-4 border-double bg-white p-3 text-center font-display text-lg leading-tight shadow-sm transition duration-300 hover:rotate-0 hover:scale-105 ${m.c} ${m.r}`}
                >
                  {m.t}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </section>

      {/* Certification : bandeau bleu pleine largeur, les lots en lignes à gauche, les mascottes sur un soleil rayonnant à droite. */}
      <section className="relative isolate mt-20 overflow-hidden bg-linear-to-br from-logo-blue via-logo-blue to-night text-white">
        <div
          aria-hidden
          className="absolute inset-0 -z-10 bg-[radial-gradient(circle,rgb(255_255_255/0.08)_1.5px,transparent_1.5px)] bg-size-[22px_22px]"
        />
        <div className="mx-auto grid max-w-7xl items-center gap-12 px-5 py-16 md:py-20 lg:grid-cols-[1.15fr_1fr]">
          <div data-reveal="left">
            <span className="inline-flex items-center gap-2 rounded-full bg-sun px-4 py-1.5 text-xs font-extrabold uppercase tracking-wide text-ink">
              <Trophy className="size-4" /> Certification jeunesse & méga lots à la clé
            </span>
            <h2 className="mt-5 text-4xl leading-[1.05] md:text-5xl">
              Décroche ta certification officielle & gagne jusqu’à{" "}
              <span className="inline-block -rotate-2 whitespace-nowrap rounded-xl bg-sun px-3 text-ink">
                1 million FCFA
              </span>
              , des ordinateurs et des téléphones !
            </h2>
            <p className="mt-5 max-w-2xl text-lg font-medium text-white/85">
              Complète les 12 Quiz de Santé Publique, collectionne tes 5 Badges d’excellence
              partageables et accède aux tirages et récompenses nationales destinés aux jeunes les
              plus engagés du Togo.
            </p>
            <ul className="mt-8 grid gap-3">
              {lots.map((l, i) => (
                <li
                  key={l.t}
                  data-reveal
                  style={retard(i)}
                  className="flex gap-4 rounded-2xl bg-white/10 p-4 ring-1 ring-white/15 backdrop-blur transition-colors duration-300 hover:bg-white/15"
                >
                  <span
                    className={`inline-flex size-12 shrink-0 items-center justify-center rounded-2xl ${["bg-sun text-ink", "bg-sky", "bg-tangerine"][i]}`}
                  >
                    <l.i className="size-6" />
                  </span>
                  <span>
                    <span className="block text-xs font-extrabold uppercase tracking-wide text-sun">
                      {l.tag}
                    </span>
                    <span className="block font-display text-2xl leading-tight">{l.t}</span>
                    <span className="mt-1 block text-sm font-medium text-white/75">{l.d}</span>
                  </span>
                </li>
              ))}
            </ul>
            <div className="mt-8 flex flex-wrap items-center gap-x-6 gap-y-4">
              <a
                href="/certification"
                className="btn-fx inline-flex items-center gap-2 rounded-full bg-primary px-7 py-3 text-[15px] font-bold shadow-card"
              >
                Lancer ma certification <ArrowRight className="size-4" />
              </a>
              <p className="text-sm font-bold text-white/80">
                12 Quiz · 5 paliers de badges · 1 certificat officiel téléchargeable
              </p>
            </div>
          </div>

          <div data-reveal="right" className="relative mx-auto w-full max-w-md lg:max-w-lg">
            {/* Soleil rayonnant derrière les mascottes : il tourne lentement si le visiteur accepte les animations. */}
            <div
              aria-hidden
              className="absolute left-1/2 top-1/2 -z-10 aspect-square w-[135%] -translate-x-1/2 -translate-y-1/2 rounded-full bg-[repeating-conic-gradient(rgb(255_255_255/0.16)_0deg_8deg,transparent_8deg_20deg)] [mask-image:radial-gradient(circle,black_25%,transparent_68%)] motion-safe:animate-[spin_90s_linear_infinite]"
            />
            <div
              aria-hidden
              className="absolute inset-[22%] -z-10 rounded-full bg-sun/45 blur-3xl"
            />
            <img
              src={mascottesTrophees}
              alt="Les mascottes du Club Santé avec des trophées, un ordinateur portable et des livres"
              loading="lazy"
              width={1122}
              height={1402}
              className="mx-auto w-4/5 drop-shadow-2xl sm:w-full"
            />
            <span className="absolute left-0 top-8 -rotate-6 rounded-2xl bg-sun px-4 py-2 text-ink shadow-card sm:-left-4">
              <span className="block text-[11px] font-extrabold uppercase">Grand prix</span>
              <span className="block font-display text-2xl leading-none md:text-3xl">
                1 000 000 FCFA
              </span>
            </span>
            <span className="absolute bottom-10 right-0 flex size-24 rotate-12 flex-col items-center justify-center rounded-full bg-primary shadow-card md:size-28">
              <span className="font-display text-4xl leading-none">12</span>
              <span className="text-xs font-extrabold uppercase">Quiz santé</span>
            </span>
          </div>
        </div>
      </section>

      {/* Objectifs : l'objectif général en grand, puis les cinq objectifs spécifiques en tickets numérotés. */}
      <section id="objectifs" className="mx-auto max-w-7xl scroll-mt-20 px-5 pt-20">
        <EnTete sur="Objectif général" bleu="Mobiliser" vert="les apprenants" />
        <blockquote
          data-reveal
          className="relative mt-8 overflow-hidden rounded-[2rem] bg-logo-blue p-8 text-xl font-bold leading-relaxed text-white shadow-card md:p-12 md:text-2xl"
        >
          <Quote aria-hidden className="absolute right-6 top-6 size-20 text-white/10" />
          Mobiliser les apprenants autour de 5 entités clés à savoir : la redynamisation de la vie
          scolaire ; la promotion de la santé dès le bas âge ; la culture de l’excellence et
          l’émulation ; la responsabilité et la citoyenneté pour un épanouissement intégral des
          élèves.
        </blockquote>

        <div data-reveal className="mt-14">
          <h3 className="text-3xl">
            <span className="text-logo-blue">Cinq orientations concrètes</span>{" "}
            <span className="text-primary">pour transformer le quotidien des élèves</span>
          </h3>
          <p className="mt-2 font-medium text-muted-foreground">
            Objectifs spécifiques · feuille de route opérationnelle : des actions ciblées pour
            impacter durablement les établissements scolaires et les communautés.
          </p>
        </div>
        <ol className="mt-8 grid gap-5 sm:grid-cols-2 lg:grid-cols-5">
          {objectifs.map((o, i) => (
            <li
              key={o.tag}
              data-reveal
              style={retard(i)}
              className="card-fx flex flex-col overflow-hidden rounded-3xl bg-card shadow-card"
            >
              <div className={`${o.c} relative flex items-end justify-between p-5 text-white`}>
                <span className="font-display text-5xl leading-none">0{i + 1}</span>
                <span className="text-right text-[11px] font-extrabold uppercase leading-tight tracking-wide">
                  {o.tag}
                </span>
                {/* Encoches de ticket entre l'en-tête et le texte. */}
                <span
                  aria-hidden
                  className="absolute -bottom-2.5 -left-2.5 size-5 rounded-full bg-background"
                />
                <span
                  aria-hidden
                  className="absolute -bottom-2.5 -right-2.5 size-5 rounded-full bg-background"
                />
              </div>
              <p className="flex-1 border-t-2 border-dashed border-border p-5 font-bold leading-snug">
                {o.t}
              </p>
            </li>
          ))}
        </ol>
      </section>

      {/* Piliers en grille bento, sur un fond blanc bleuté qui rompt la feuille de carnet. */}
      <section id="piliers" className="mt-20 scroll-mt-20 bg-mist-soft py-20">
        <div className="mx-auto max-w-7xl px-5">
          <EnTete
            sur="Les piliers fondamentaux du programme"
            bleu="Vision, but,"
            vert="mission & valeurs"
          />
          <div className="mt-8 grid gap-5 lg:grid-cols-3">
            <article
              data-reveal
              className="card-fx relative isolate overflow-hidden rounded-[2rem] bg-linear-to-br from-logo-blue to-night p-8 text-white shadow-card md:p-10 lg:col-span-2"
            >
              <Eye
                aria-hidden
                className="absolute -bottom-8 -right-8 -z-10 size-56 text-white/10"
              />
              <p className="flex items-center gap-2 text-sm font-extrabold uppercase tracking-widest text-sun">
                <Eye className="size-5" /> Vision
              </p>
              <p className="mt-4 max-w-xl font-display text-3xl leading-tight md:text-5xl">
                Jeunesse en bonne santé, responsable et épanouie
              </p>
              <p className="mt-4 font-semibold text-white/75">
                Santé et Éducation pour chaque apprenant
              </p>
            </article>
            <article
              data-reveal
              style={retard(1)}
              className="card-fx rounded-[2rem] bg-primary p-8 text-white shadow-card"
            >
              <p className="flex items-center gap-2 text-sm font-extrabold uppercase tracking-widest">
                <Target className="size-5" /> But
              </p>
              <p className="mt-4 text-xl font-extrabold leading-snug">
                Culture de la responsabilité sociale, le leadership transformationnel et le
                volontariat
              </p>
              <p className="mt-4 font-semibold text-white/80">
                Volontariat & engagement communautaire
              </p>
            </article>
            <article data-reveal className="card-fx rounded-[2rem] bg-sun p-8 text-ink shadow-card">
              <p className="flex items-center gap-2 text-sm font-extrabold uppercase tracking-widest">
                <Rocket className="size-5" /> Mission
              </p>
              <p className="mt-4 text-xl font-extrabold leading-snug">
                Excellence et Émulation en milieu scolaire et universitaire
              </p>
              <p className="mt-4 font-semibold text-ink/70">
                Stimulation des talents et de l’excellence
              </p>
            </article>
            <article
              data-reveal
              style={retard(1)}
              className="card-fx rounded-[2rem] bg-card p-8 shadow-card lg:col-span-2"
            >
              <p className="flex items-center gap-2 text-sm font-extrabold uppercase tracking-widest text-logo-blue">
                <Gem className="size-5" /> Valeurs
              </p>
              <ul className="mt-5 flex flex-wrap gap-3">
                {valeurs.map((v) => (
                  <li
                    key={v.t}
                    className={`${v.c} rounded-full px-5 py-2 font-display text-xl text-white transition duration-300 hover:-rotate-3 hover:scale-105`}
                  >
                    {v.t}
                  </li>
                ))}
              </ul>
              <p className="mt-5 font-semibold text-muted-foreground">
                Des repères cardinaux pour former une élite responsable au service de la nation
                togolaise.
              </p>
            </article>
            <article
              data-reveal
              className="relative isolate overflow-hidden rounded-[2rem] bg-logo-red p-8 text-white shadow-card md:p-10 lg:col-span-3"
            >
              <Megaphone
                aria-hidden
                className="absolute -bottom-10 -right-6 -z-10 size-56 -rotate-12 text-white/10"
              />
              <div className="flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
                <div>
                  <p className="flex items-center gap-2 text-sm font-extrabold uppercase tracking-widest text-white/85">
                    <Megaphone className="size-5" /> Slogan
                  </p>
                  <p className="mt-3 font-hand text-3xl leading-tight md:text-5xl">
                    « Ensemble pour une génération de jeunes en bonne santé, responsable et épanouie
                    »
                  </p>
                </div>
                <p className="max-w-xs shrink-0 font-semibold text-white/85">
                  Un mot d’ordre fédérateur unissant élèves, éducateurs et soignants.
                </p>
              </div>
            </article>
          </div>
        </div>
      </section>

      {/* Historique : le récit à gauche, les jalons en frise verticale à droite. */}
      <section id="historique" className="mx-auto max-w-7xl scroll-mt-20 px-5 pt-20">
        <div className="grid gap-10 lg:grid-cols-[1.35fr_1fr] lg:gap-14">
          <div>
            <EnTete
              sur="Historique & vision globale d’AIMES-AFRIQUE"
              bleu="Santé et éducation :"
              vert="une vision portée depuis 2005"
            />
            <div
              data-reveal
              className="mt-6 space-y-4 text-lg leading-relaxed text-muted-foreground"
            >
              <p>
                C’est dans cette dynamique que l’Association Internationale des Médecins pour la
                promotion de l’Éducation et de la Santé en Afrique (AIMES-AFRIQUE), créée en janvier
                2005 à Lomé et aujourd’hui présente dans 20 pays, renforce son engagement en faveur
                de l’éducation en promouvant l’excellence et l’émulation en milieu scolaire et
                universitaire, telles que prévues dans ses statuts.
              </p>
              <p>
                Dans le cadre de sa mission globale, AIMES-AFRIQUE a lancé en août 2020 la première
                chaîne de télévision panafricaine thématique 100 % santé, SOS DOCTEUR TV. Après le
                volet consacré à la santé, elle a renforcé en mars 2025 son deuxième volet
                d’intervention, « l’Éducation », à travers le programme « Excellence et Émulation en
                milieu scolaire et universitaire au Togo ».
              </p>
            </div>
          </div>

          <aside
            data-reveal="right"
            className="self-start rounded-[2rem] bg-card p-7 shadow-card md:p-9 lg:sticky lg:top-24"
          >
            <p className="text-sm font-extrabold uppercase tracking-widest text-logo-blue">
              Jalons clés du programme
            </p>
            <h3 className="mt-1 text-3xl text-primary">Repères</h3>
            <ol className="relative mt-6 space-y-8 border-l-2 border-dashed border-logo-blue/25 pl-8">
              {jalons.map((j) => (
                <li key={j.date} className="relative">
                  <span
                    aria-hidden
                    className={`${j.c} absolute -left-[2.6rem] top-0.5 size-5 rounded-full ring-4 ring-card`}
                  />
                  <p
                    className={`${j.c} inline-flex rounded-full px-3 py-1 text-xs font-extrabold uppercase text-white`}
                  >
                    {j.date}
                  </p>
                  <p className="mt-2 font-bold leading-snug">{j.t}</p>
                </li>
              ))}
            </ol>
          </aside>
        </div>
      </section>

      {/* Les trois formes d'éducation : la non formelle, cœur des clubs, au centre et en couleur. */}
      <section id="education" className="mx-auto max-w-7xl scroll-mt-20 px-5 pt-20">
        <EnTete sur="Cadre pédagogique" bleu="Les trois formes" vert="d’éducation" centre>
          Comprendre l’articulation entre école, activités parascolaires et apprentissages
          quotidiens.
        </EnTete>
        <div className="mt-10 grid items-center gap-5 md:grid-cols-3">
          {educations.map((e, i) => (
            <article
              key={e.t}
              data-reveal
              style={retard(i)}
              className={`card-fx relative rounded-[2rem] p-7 shadow-card ${e.coeur ? "bg-primary py-10 text-white md:-my-4" : "bg-card"}`}
            >
              {e.coeur && (
                <span className="absolute -top-4 left-1/2 -translate-x-1/2 whitespace-nowrap rounded-full bg-sun px-4 py-1.5 text-xs font-extrabold uppercase text-ink shadow-card">
                  Cœur des Clubs Santé
                </span>
              )}
              <span
                className={`inline-flex size-14 items-center justify-center rounded-2xl ${e.coeur ? "bg-white/20" : "bg-mist text-logo-blue"}`}
              >
                <e.i className="size-7" />
              </span>
              <p
                className={`mt-5 text-xs font-extrabold uppercase tracking-wide ${e.coeur ? "text-white/80" : "text-tangerine"}`}
              >
                {e.tag}
              </p>
              <h3 className={`mt-1 text-2xl ${e.coeur ? "" : "text-logo-blue"}`}>{e.t}</h3>
              <p
                className={`mt-3 font-medium ${e.coeur ? "text-white/90" : "text-muted-foreground"}`}
              >
                {e.d}
              </p>
              <p
                className={`mt-5 border-t pt-4 text-sm font-bold ${e.coeur ? "border-white/25" : ""}`}
              >
                Dimension {i + 1} de l’apprentissage
              </p>
            </article>
          ))}
        </div>
        <div
          data-reveal
          className="mt-12 grid items-center gap-6 rounded-[2rem] border-2 border-dashed border-primary/40 bg-card/80 p-7 md:grid-cols-[auto_1fr] md:p-9"
        >
          <span className="inline-flex size-16 items-center justify-center rounded-full bg-primary/15 text-primary">
            <HeartHandshake className="size-8" />
          </span>
          <div>
            <h3 className="text-2xl text-logo-blue">Positionnement sur l’éducation non formelle</h3>
            <p className="mt-2 font-medium text-muted-foreground">
              Les Clubs Santé SOS DOCTEUR TV se positionnent principalement dans le champ de
              l’éducation non formelle, en proposant aux jeunes des activités complémentaires à
              l’enseignement scolaire, axées sur la santé, le développement personnel, la confiance
              en soi, la responsabilité et l’engagement pour un leadership transformationnel.
            </p>
          </div>
        </div>
      </section>

      {/* Mot du promoteur : bandeau pleine largeur. */}
      <section className="relative isolate mt-24 overflow-hidden bg-linear-to-br from-logo-blue to-night text-white">
        <div
          aria-hidden
          className="absolute -right-20 top-0 -z-10 size-96 rounded-full bg-sky/30 blur-3xl"
        />
        <div className="mx-auto grid max-w-7xl items-center gap-10 px-5 py-16 md:py-20 lg:grid-cols-[auto_1fr] lg:gap-16">
          <div data-reveal="left" className="relative mx-auto w-56 md:w-64">
            <div
              aria-hidden
              className="absolute inset-0 translate-x-3 translate-y-3 rounded-[2rem] bg-sun"
            />
            <img
              src={kodom}
              alt="Dr Serge Michel KODOM"
              loading="lazy"
              width={1097}
              height={1434}
              className="relative aspect-[4/5] w-full rounded-[2rem] object-cover object-top"
            />
          </div>
          <div data-reveal="right">
            <p className="text-sm font-extrabold uppercase tracking-widest text-sun">
              Le mot du promoteur
            </p>
            <blockquote className="mt-4 text-xl font-semibold leading-relaxed md:text-2xl">
              <Quote aria-hidden className="mb-3 size-10 text-primary" />
              C’est avec une immense fierté que nous constatons l’impact croissant des Clubs Santé
              scolaires au Togo. Notre ambition ultime à travers ce programme est de forger une
              nouvelle génération de leaders civiques et d’ambassadeurs de santé publique, capables
              d’agir concrètement à l’école pour transformer durablement la santé de nos communautés
              locales.
            </blockquote>
            <p className="mt-6 font-display text-2xl">Dr Serge Michel KODOM</p>
            <p className="text-sm font-semibold text-white/70">
              Président-fondateur d’AIMES-AFRIQUE · Promoteur de SOS DOCTEUR TV
            </p>
          </div>
        </div>
      </section>

      {/* Adhésion et gouvernance : les règles à gauche, le bureau de 21 membres à droite. */}
      <section id="adhesion" className="mx-auto max-w-7xl scroll-mt-20 px-5 pt-20">
        <div className="flex flex-wrap items-end justify-between gap-6">
          <EnTete
            sur="Cadre d’adhésion et gouvernance scolaire"
            bleu="Qui peut adhérer"
            vert="et comment fonctionnent les clubs ?"
          >
            Directives officielles applicables à l’ensemble des collèges et lycées du Togo.
          </EnTete>
          <a
            href="#"
            data-reveal
            className="btn-fx inline-flex items-center gap-2 rounded-full bg-primary px-7 py-3 text-[15px] font-bold text-primary-foreground shadow-card"
          >
            Faire une demande d’affiliation <ArrowRight className="size-4" />
          </a>
        </div>

        <div className="mt-10 grid gap-6 lg:grid-cols-2">
          <article data-reveal="left" className="rounded-[2rem] bg-card p-7 shadow-card md:p-9">
            <h3 className="text-2xl text-logo-blue md:text-3xl">
              Qui peut adhérer au Club Santé dans un collège ou un lycée ?
            </h3>
            <ul className="mt-6 space-y-4">
              {regles.map((r, i) => (
                <li key={r} className="flex gap-4">
                  <span
                    className={`mt-0.5 inline-flex size-7 shrink-0 items-center justify-center rounded-full text-white ${["bg-sky", "bg-primary", "bg-tangerine", "bg-grape", "bg-rose", "bg-logo-blue"][i]}`}
                  >
                    <Check className="size-4" strokeWidth={3} />
                  </span>
                  <p className="font-semibold leading-snug">{r}</p>
                </li>
              ))}
            </ul>
          </article>

          <article data-reveal="right" className="rounded-[2rem] bg-card p-7 shadow-card md:p-9">
            <h3 className="text-2xl text-logo-blue md:text-3xl">Composition du bureau des clubs</h3>
            <p className="mt-1 font-semibold text-muted-foreground">
              Structure officielle et parité obligatoire
            </p>
            {/* 21 pastilles : 11 filles au moins, 10 garçons au plus. */}
            <div className="mt-6 flex flex-wrap items-center gap-6 rounded-3xl bg-mist p-5">
              <div>
                <p className="font-display text-6xl leading-none text-logo-blue">21</p>
                <p className="text-xs font-extrabold uppercase tracking-wide">membres au total</p>
              </div>
              <div className="flex-1">
                <ul aria-hidden className="grid max-w-64 grid-cols-7 gap-1.5">
                  {Array.from({ length: 21 }, (_, i) => (
                    <li
                      key={i}
                      className={`aspect-square rounded-full ${i < 11 ? "bg-rose" : "bg-sky"}`}
                    />
                  ))}
                </ul>
                <p className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-sm font-bold">
                  <span className="flex items-center gap-1.5">
                    <span className="size-3 rounded-full bg-rose" /> au moins 11 filles
                  </span>
                  <span className="flex items-center gap-1.5">
                    <span className="size-3 rounded-full bg-sky" /> au plus 10 garçons
                  </span>
                </p>
              </div>
            </div>
            <ol className="mt-6 space-y-3">
              {bureau.map((b, i) => (
                <li key={b} className="flex gap-3">
                  <span className="inline-flex size-7 shrink-0 items-center justify-center rounded-lg bg-logo-blue font-display text-sm text-white">
                    {i + 1}
                  </span>
                  <p className="font-semibold leading-snug">{b}</p>
                </li>
              ))}
            </ol>
            <p className="mt-6 flex gap-3 rounded-2xl bg-primary/10 p-4 text-sm font-semibold">
              <Accessibility className="size-5 shrink-0 text-primary" />
              <span>
                <strong>Inclusion & parité :</strong> le bureau doit être inclusif, notamment en
                favorisant la participation des personnes vivant avec un handicap, et comporter de
                préférence plus de filles que de garçons.
              </span>
            </p>
          </article>
        </div>
      </section>

      <FaqSection />

      <SiteFooter />
    </div>
  );
}
