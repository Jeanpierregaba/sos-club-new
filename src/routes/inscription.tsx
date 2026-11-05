import { createFileRoute, Link, redirect } from "@tanstack/react-router";
import {
  ArrowLeft,
  ArrowRight,
  Award,
  ChevronRight,
  GraduationCap,
  Hourglass,
  ListChecks,
  Lock,
  Presentation,
  Share2,
  Sparkles,
  UserRound,
} from "lucide-react";

import logo from "@/assets/logo.webp";
import mascottesEquipe from "@/assets/mascottes-equipe.webp";
import { InscriptionEleve } from "@/components/inscription/InscriptionEleve";
import { InscriptionEncadreur } from "@/components/inscription/InscriptionEncadreur";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  chargerDre,
  chargerEtatInscription,
  chargerMoi,
  MESSAGE_INDISPONIBLE,
} from "@/lib/api/client";

// « visiteur » : particulier ou visiteur qui veut suivre les quiz et la certification. Sa fiche
// d'inscription reste à construire (R19, Q27) : le profil est présenté, sans formulaire, en attendant.
type Profil = "eleve" | "encadreur" | "visiteur";
const PROFILS_VALIDES: Profil[] = ["eleve", "encadreur", "visiteur"];

export const Route = createFileRoute("/inscription")({
  // Sans profil, la page propose de choisir : élève, encadreur (spec 018) ou particulier / visiteur.
  validateSearch: (search: Record<string, unknown>): { profil?: Profil } =>
    PROFILS_VALIDES.includes(search["profil"] as Profil)
      ? { profil: search["profil"] as Profil }
      : {},
  beforeLoad: async () => {
    const moi = await chargerMoi().catch(() => null);
    if (moi) throw redirect({ to: "/mon-espace" });
  },
  // API en panne : la page s'affiche et explique pourquoi l'inscription n'est pas possible.
  loader: async () => {
    const [etat, dre] = await Promise.all([
      chargerEtatInscription().catch(() => null),
      chargerDre().catch(() => []),
    ]);
    return { etat, dre };
  },
  head: () => ({
    meta: [
      { title: "Inscription — Club Santé SOS Docteur TV" },
      {
        name: "description",
        content:
          "Crée ton compte élève, encadreur ou visiteur des Clubs Santé : quiz, points, classements et certification.",
      },
    ],
  }),
  component: Inscription,
});

const ATOUTS: Record<Profil, string[]> = {
  eleve: [
    "Des points de bienvenue dès ton inscription",
    "Des quiz santé et la certification Génie Imhotep",
    "Ton pseudonyme dans les classements, jamais ton nom",
  ],
  encadreur: [
    "Accompagne le Club Santé de ton établissement",
    "Forme-toi avec les quiz et la certification Génie Imhotep",
    "Valorise les actions de tes élèves",
  ],
  visiteur: [
    "Les 12 quiz de santé publique, à ton rythme",
    "Des badges à partager sur tes réseaux",
    "Ta certification Génie Imhotep",
  ],
};

const TEXTES: Record<Profil, { eyebrow: string; intro: string }> = {
  eleve: {
    eyebrow: "Compte élève",
    intro:
      "Quelques minutes suffisent. Tu peux participer même si ton établissement n'a pas encore de Club Santé.",
  },
  encadreur: {
    eyebrow: "Compte encadreur",
    intro:
      "Enseignant, responsable ou accompagnateur : crée ton compte. L'équipe nationale vérifie ton inscription avant de l'activer.",
  },
  visiteur: {
    eyebrow: "Particulier / visiteur",
    intro:
      "Tu n'es ni élève ni encadreur, mais la santé publique t'intéresse ? Ce compte arrive bientôt.",
  },
};

function Inscription() {
  const { etat, dre } = Route.useLoaderData();
  const { profil } = Route.useSearch();
  const atouts = ATOUTS[profil ?? "eleve"];

  return (
    <main className="grid min-h-screen bg-carnet lg:grid-cols-[0.9fr_1.1fr]">
      <section className="relative isolate hidden overflow-hidden bg-linear-to-br from-logo-blue to-night p-10 text-white lg:flex lg:flex-col xl:p-14">
        <div aria-hidden className="pointer-events-none absolute inset-0 -z-10">
          <div className="absolute inset-0 bg-[radial-gradient(oklch(1_0_0/0.14)_1.5px,transparent_1.5px)] bg-size-[22px_22px] [mask-image:linear-gradient(to_bottom,black,transparent_70%)]" />
          <div className="absolute -right-40 -top-40 size-[36rem] rounded-full border-[3rem] border-white/5" />
          <div className="absolute -bottom-24 left-1/4 size-96 rounded-full bg-primary/25 blur-3xl" />
        </div>
        <Link
          to="/"
          aria-label="Retour à l'accueil"
          className="self-start rounded-2xl bg-white px-4 py-2.5 shadow-card transition hover:scale-105"
        >
          <img src={logo} alt="" width={1014} height={195} className="h-9 w-auto" />
        </Link>
        <p className="mt-12 font-display text-5xl leading-[0.95] xl:text-6xl">
          <span className="block">Rejoins</span>
          <span className="block text-sun">les Clubs Santé</span>
        </p>
        <ul className="mt-8 space-y-3">
          {atouts.map((t) => (
            <li key={t} className="flex items-center gap-3 font-semibold text-white/90">
              <span className="inline-flex size-9 shrink-0 items-center justify-center rounded-xl bg-white/10 text-sun ring-1 ring-white/15">
                <Sparkles className="size-5" />
              </span>
              {t}
            </li>
          ))}
        </ul>
        <img
          src={mascottesEquipe}
          alt="Les sept mascottes des Clubs Santé"
          width={1122}
          height={1402}
          className="mx-auto -mb-10 mt-auto w-full max-w-sm pt-8 drop-shadow-[0_24px_40px_oklch(0_0_0/0.35)] xl:-mb-14"
        />
      </section>

      <section className="flex flex-col items-center px-4 py-10 sm:px-8">
        <Link
          to="/"
          aria-label="Retour à l'accueil"
          className="transition hover:scale-105 lg:hidden"
        >
          <img
            src={logo}
            alt="Club Santé SOS Docteur TV"
            width={1014}
            height={195}
            className="h-11 w-auto"
          />
        </Link>
        <div className="mt-8 w-full max-w-xl lg:mt-0">
          <p className="flex items-center gap-3 text-sm font-extrabold uppercase tracking-widest text-logo-red">
            <span className="h-1 w-8 rounded-full bg-primary" />
            {profil ? TEXTES[profil].eyebrow : "Inscription"}
          </p>
          <h1 className="mt-3 text-4xl leading-tight md:text-5xl">
            <span className="text-logo-blue">Crée ton</span>{" "}
            <span className="text-primary">compte</span>
          </h1>
          <p className="mt-2 mb-8 text-lg font-medium text-muted-foreground">
            {profil ? TEXTES[profil].intro : "Choisis d'abord ton profil."}
          </p>
          <div className="rounded-3xl bg-white p-6 shadow-card ring-1 ring-border sm:p-8">
            {etat === null ? (
              <Alert variant="destructive">
                <AlertDescription>{MESSAGE_INDISPONIBLE}</AlertDescription>
              </Alert>
            ) : !etat.ouvertes ? (
              <div className="flex items-start gap-3 rounded-2xl bg-mist-soft p-4">
                <Lock aria-hidden className="mt-0.5 size-5 shrink-0 text-logo-blue" />
                <p className="font-medium text-ink/80">
                  Les inscriptions ne sont pas encore ouvertes. Elles ouvriront avec le lancement
                  officiel de la plateforme : reviens bientôt !
                </p>
              </div>
            ) : profil === "encadreur" ? (
              <InscriptionEncadreur dre={dre} />
            ) : profil === "eleve" ? (
              <InscriptionEleve dre={dre} />
            ) : profil === "visiteur" ? (
              <InscriptionVisiteur />
            ) : (
              <ChoixProfil />
            )}
          </div>
          {profil && etat?.ouvertes && (
            <Link
              to="/inscription"
              search={{}}
              className="mx-auto mt-6 flex w-fit items-center gap-1.5 text-sm font-bold text-logo-blue underline-offset-4 hover:underline"
            >
              <ArrowLeft className="size-4" /> Changer de profil
            </Link>
          )}
          <p className="mt-6 text-center text-sm font-semibold text-muted-foreground">
            Déjà un compte ?{" "}
            <Link
              to="/connexion"
              className="font-bold text-logo-blue underline-offset-4 hover:underline"
            >
              Connecte-toi
            </Link>
          </p>
          <Link
            to="/"
            className="mx-auto mt-3 flex w-fit items-center gap-1.5 text-sm font-bold text-logo-blue underline-offset-4 hover:underline"
          >
            <ArrowLeft className="size-4" /> Retour à l’accueil
          </Link>
        </div>
      </section>
    </main>
  );
}

const PROFILS: {
  profil: Profil;
  titre: string;
  texte: string;
  icone: typeof GraduationCap;
  bientot?: boolean;
}[] = [
  {
    profil: "eleve",
    titre: "Je suis élève",
    texte: "De la 6e à la Terminale. Ton compte est actif tout de suite.",
    icone: GraduationCap,
  },
  {
    profil: "encadreur",
    titre: "Je suis encadreur",
    texte: "Enseignant, responsable ou accompagnateur. L'équipe vérifie ton inscription.",
    icone: Presentation,
  },
  {
    profil: "visiteur",
    titre: "Je suis un particulier ou un visiteur",
    texte: "Participe aux 12 quiz de santé publique, gagne des badges et obtiens ta certification.",
    icone: UserRound,
    bientot: true,
  },
];

function ChoixProfil() {
  return (
    <ul className="grid gap-4">
      {PROFILS.map(({ profil, titre, texte, icone: Icone, bientot }) => (
        <li key={profil}>
          <Link
            to="/inscription"
            search={{ profil }}
            className="group flex items-center gap-4 rounded-2xl border-2 border-border p-5 transition hover:border-primary hover:bg-primary/5 focus-visible:border-primary focus-visible:outline-none"
          >
            <span className="inline-flex size-14 shrink-0 items-center justify-center rounded-2xl bg-mist-soft text-logo-blue">
              <Icone aria-hidden className="size-7" />
            </span>
            <span className="min-w-0 flex-1">
              <span className="flex flex-wrap items-center gap-2 text-lg font-bold text-ink">
                {titre}
                {bientot && (
                  <span className="rounded-full bg-sun px-2.5 py-0.5 text-[11px] font-extrabold uppercase tracking-wide text-ink">
                    Bientôt
                  </span>
                )}
              </span>
              <span className="block text-sm font-medium text-muted-foreground">{texte}</span>
            </span>
            <ChevronRight
              aria-hidden
              className="size-6 shrink-0 text-muted-foreground transition group-hover:translate-x-1 group-hover:text-primary"
            />
          </Link>
        </li>
      ))}
    </ul>
  );
}

// Le profil particulier / visiteur, en attendant sa fiche d'inscription : ce qu'il offrira, et de quoi
// découvrir le parcours dès maintenant. Aucune donnée n'est demandée.
const PROMESSES_VISITEUR = [
  {
    i: ListChecks,
    t: "12 quiz de santé publique",
    d: "Les mêmes quiz que les élèves, à ton rythme.",
  },
  {
    i: Share2,
    t: "Des badges partageables",
    d: "Un badge à chaque palier, à montrer sur tes réseaux.",
  },
  { i: Award, t: "Ta certification", d: "Le certificat Génie Imhotep, après les 12 quiz réussis." },
];

function InscriptionVisiteur() {
  return (
    <div>
      <p className="flex items-start gap-3 rounded-2xl bg-sun/25 p-4 font-semibold text-ink">
        <Hourglass aria-hidden className="mt-0.5 size-5 shrink-0 text-tangerine" />
        Le compte particulier / visiteur est en préparation. Il ouvrira très bientôt : reviens vite
        !
      </p>
      <ul className="mt-6 grid gap-4">
        {PROMESSES_VISITEUR.map((p) => (
          <li key={p.t} className="flex items-start gap-4">
            <span className="inline-flex size-11 shrink-0 items-center justify-center rounded-xl bg-mist-soft text-logo-blue">
              <p.i aria-hidden className="size-5" />
            </span>
            <span>
              <span className="block font-bold text-ink">{p.t}</span>
              <span className="block text-sm font-medium text-muted-foreground">{p.d}</span>
            </span>
          </li>
        ))}
      </ul>
      <a
        href="/certification"
        className="btn-fx mt-8 inline-flex items-center gap-2 rounded-full bg-primary px-7 py-3 text-[15px] font-bold text-primary-foreground"
      >
        Découvrir la certification <ArrowRight className="size-4" />
      </a>
    </div>
  );
}
