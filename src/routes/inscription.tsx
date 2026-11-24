import { createFileRoute, Link, redirect } from "@tanstack/react-router";
import {
  ArrowLeft,
  ChevronRight,
  GraduationCap,
  Lock,
  Presentation,
  Sparkles,
  UserRound,
} from "lucide-react";

import logo from "@/assets/logo.webp";
import mascottesEquipe from "@/assets/mascottes-equipe.webp";
import { InscriptionEleve } from "@/components/inscription/InscriptionEleve";
import { InscriptionEncadreur } from "@/components/inscription/InscriptionEncadreur";
import { InscriptionVisiteur } from "@/components/inscription/InscriptionVisiteur";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { chargerAxes, chargerDre, chargerEtatInscription, chargerMoi } from "@/lib/api/client";
import { m } from "@/paraglide/messages.js";

// « visiteur » : particulier ou visiteur qui veut jouer aux quiz santé (spec 030), sans points ni certification.
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
    const [etat, dre, axes] = await Promise.all([
      chargerEtatInscription().catch(() => null),
      chargerDre().catch(() => []),
      chargerAxes().catch(() => []),
    ]);
    return { etat, dre, axes };
  },
  head: () => ({
    meta: [
      { title: m.ins_meta_titre() },
      { name: "description", content: m.ins_meta_description() },
    ],
  }),
  component: Inscription,
});

// Des fonctions : les textes suivent la langue de la page (spec 052).
const ATOUTS: Record<Profil, () => string[]> = {
  eleve: () => [m.ins_atout_eleve_1(), m.ins_atout_eleve_2(), m.ins_atout_eleve_3()],
  encadreur: () => [
    m.ins_atout_encadreur_1(),
    m.ins_atout_encadreur_2(),
    m.ins_atout_encadreur_3(),
  ],
  visiteur: () => [m.ins_atout_visiteur_1(), m.ins_atout_visiteur_2(), m.ins_atout_visiteur_3()],
};

const TEXTES: Record<Profil, () => { eyebrow: string; intro: string }> = {
  eleve: () => ({ eyebrow: m.ins_eyebrow_eleve(), intro: m.ins_intro_eleve() }),
  encadreur: () => ({ eyebrow: m.ins_eyebrow_encadreur(), intro: m.ins_intro_encadreur() }),
  visiteur: () => ({ eyebrow: m.ins_eyebrow_visiteur(), intro: m.ins_intro_visiteur() }),
};

function Inscription() {
  const { etat, dre, axes } = Route.useLoaderData();
  const { profil } = Route.useSearch();
  const atouts = ATOUTS[profil ?? "eleve"]();

  return (
    <main className="grid min-h-screen grid-cols-[minmax(0,1fr)] bg-carnet lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
      <section className="relative isolate hidden overflow-hidden bg-linear-to-br from-logo-blue to-night p-10 text-white lg:flex lg:flex-col xl:p-14">
        <div aria-hidden className="pointer-events-none absolute inset-0 -z-10">
          <div className="absolute inset-0 bg-[radial-gradient(oklch(1_0_0/0.14)_1.5px,transparent_1.5px)] bg-size-[22px_22px] [mask-image:linear-gradient(to_bottom,black,transparent_70%)]" />
          <div className="absolute -right-40 -top-40 size-[36rem] rounded-full border-[3rem] border-white/5" />
          <div className="absolute -bottom-24 left-1/4 size-96 rounded-full bg-primary/25 blur-3xl" />
        </div>
        <Link
          to="/"
          aria-label={m.cnx_retour_accueil()}
          className="self-start rounded-2xl bg-white px-4 py-2.5 shadow-card transition hover:scale-105"
        >
          <img src={logo} alt="" width={1014} height={195} className="h-9 w-auto" />
        </Link>
        <p className="mt-12 font-display text-5xl leading-[0.95] xl:text-6xl">
          <span className="block">{m.ins_rejoins_1()}</span>
          <span className="block text-sun">{m.ins_rejoins_2()}</span>
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
          alt={m.cnx_mascottes_alt()}
          width={1122}
          height={1402}
          className="mx-auto -mb-10 mt-auto w-full max-w-sm pt-8 drop-shadow-[0_24px_40px_oklch(0_0_0/0.35)] xl:-mb-14"
        />
      </section>

      <section className="flex flex-col items-center px-4 py-10 sm:px-8">
        <Link
          to="/"
          aria-label={m.cnx_retour_accueil()}
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
            {profil ? TEXTES[profil]().eyebrow : m.ins_inscription()}
          </p>
          <h1 className="mt-3 text-4xl leading-tight md:text-5xl">
            <span className="text-logo-blue">{m.ins_titre_1()}</span>{" "}
            <span className="text-primary">{m.ins_titre_2()}</span>
          </h1>
          <p className="mt-2 mb-8 text-lg font-medium text-muted-foreground">
            {profil ? TEXTES[profil]().intro : m.ins_choisis_profil()}
          </p>
          <div className="rounded-3xl bg-white p-6 shadow-card ring-1 ring-border sm:p-8">
            {etat === null ? (
              <Alert variant="destructive">
                <AlertDescription>{m.erreur_indisponible()}</AlertDescription>
              </Alert>
            ) : !etat.ouvertes ? (
              <div className="flex items-start gap-3 rounded-2xl bg-mist-soft p-4">
                <Lock aria-hidden className="mt-0.5 size-5 shrink-0 text-logo-blue" />
                <p className="font-medium text-ink/80">{m.ins_fermees()}</p>
              </div>
            ) : profil === "encadreur" ? (
              <InscriptionEncadreur dre={dre} />
            ) : profil === "eleve" ? (
              <InscriptionEleve dre={dre} axes={axes} />
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
              <ArrowLeft className="size-4" /> {m.ins_changer_profil()}
            </Link>
          )}
          <p className="mt-6 text-center text-sm font-semibold text-muted-foreground">
            {m.ins_deja_compte()}{" "}
            <Link
              to="/connexion"
              className="font-bold text-logo-blue underline-offset-4 hover:underline"
            >
              {m.ins_connecte_toi()}
            </Link>
          </p>
          <Link
            to="/"
            className="mx-auto mt-3 flex w-fit items-center gap-1.5 text-sm font-bold text-logo-blue underline-offset-4 hover:underline"
          >
            <ArrowLeft className="size-4" /> {m.cnx_retour_accueil()}
          </Link>
        </div>
      </section>
    </main>
  );
}

const PROFILS = (): {
  profil: Profil;
  titre: string;
  texte: string;
  icone: typeof GraduationCap;
}[] => [
  {
    profil: "eleve",
    titre: m.ins_profil_eleve(),
    texte: m.ins_profil_eleve_d(),
    icone: GraduationCap,
  },
  {
    profil: "encadreur",
    titre: m.ins_profil_encadreur(),
    texte: m.ins_profil_encadreur_d(),
    icone: Presentation,
  },
  {
    profil: "visiteur",
    titre: m.ins_profil_visiteur(),
    texte: m.ins_profil_visiteur_d(),
    icone: UserRound,
  },
];

function ChoixProfil() {
  return (
    <ul className="grid gap-4">
      {PROFILS().map(({ profil, titre, texte, icone: Icone }) => (
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
