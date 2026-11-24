import { useQueryClient } from "@tanstack/react-query";
import { createFileRoute, Link, redirect, useRouter } from "@tanstack/react-router";

import { ArrowLeft, BookOpen, KeyRound, Trophy, Users } from "lucide-react";

import logo from "@/assets/logo.webp";
import mascottesEquipe from "@/assets/mascottes-equipe.webp";
import { FormulaireConnexion } from "@/components/FormulaireConnexion";
import { CLE_MOI } from "@/hooks/use-moi";
import { chargerMoi, type Moi } from "@/lib/api/client";
import { cheminSur } from "@/lib/redirection";
import { m } from "@/paraglide/messages.js";

export const Route = createFileRoute("/connexion")({
  validateSearch: (search: Record<string, unknown>): { redirection?: string } =>
    typeof search["redirection"] === "string" ? { redirection: search["redirection"] } : {},
  beforeLoad: async ({ search }) => {
    // API en panne : le formulaire s'affiche quand même et donnera le message d'erreur à l'envoi.
    const moi = await chargerMoi().catch(() => null);
    if (moi) throw redirect({ href: cheminSur(search.redirection) });
  },
  head: () => ({
    meta: [{ title: m.cnx_meta_titre() }, { name: "robots", content: "noindex" }],
  }),
  component: Connexion,
});

const atouts = () => [
  { i: Trophy, t: m.cnx_atout_1() },
  { i: BookOpen, t: m.cnx_atout_2() },
  { i: Users, t: m.cnx_atout_3() },
];

function Connexion() {
  const { redirection } = Route.useSearch();
  const queryClient = useQueryClient();
  const router = useRouter();

  const allerAuCompte = (moi: Moi) => {
    // Un autre compte a pu laisser des données en cache dans cet onglet.
    queryClient.clear();
    queryClient.setQueryData(CLE_MOI, moi);
    void router.navigate({ href: cheminSur(redirection), replace: true });
  };

  return (
    <main className="grid min-h-screen bg-carnet lg:grid-cols-[1.05fr_1fr]">
      {/* Panneau d'accueil : le fond bleu, les mascottes et ce qui attend l'élève dans son espace. */}
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
          <span className="block">{m.cnx_slogan_1()}</span>
          <span className="block text-sun">{m.cnx_slogan_2()}</span>
          <span className="block">{m.cnx_slogan_3()}</span>
        </p>
        <ul className="mt-8 space-y-3">
          {atouts().map(({ i: Icone, t }) => (
            <li key={t} className="flex items-center gap-3 font-semibold text-white/90">
              <span className="inline-flex size-9 shrink-0 items-center justify-center rounded-xl bg-white/10 text-sun ring-1 ring-white/15">
                <Icone className="size-5" />
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

      {/* Le formulaire, sur la feuille de carnet. */}
      <section className="flex flex-col items-center justify-center px-4 py-10 sm:px-8">
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
        <div className="mt-8 w-full max-w-md lg:mt-0">
          <p className="flex items-center gap-3 text-sm font-extrabold uppercase tracking-widest text-logo-red">
            <span className="h-1 w-8 rounded-full bg-primary" />
            {m.cnx_mon_espace()}
          </p>
          <h1 className="mt-3 text-4xl leading-tight md:text-5xl">
            <span className="text-logo-blue">{m.cnx_titre_1()}</span>{" "}
            <span className="text-primary">{m.cnx_titre_2()}</span>
          </h1>
          <p className="mt-2 mb-8 text-lg font-medium text-muted-foreground">{m.cnx_intro()}</p>
          <div className="rounded-3xl bg-white p-6 shadow-card ring-1 ring-border sm:p-8">
            <FormulaireConnexion onConnecte={allerAuCompte} />
            <p className="mt-6 flex items-start gap-3 rounded-2xl bg-mist-soft p-4 text-sm font-medium text-ink/75">
              <KeyRound aria-hidden className="mt-0.5 size-4 shrink-0 text-logo-blue" />
              <span>
                {m.cnx_oubli_debut()}{" "}
                <Link
                  to="/mot-de-passe-oublie"
                  className="font-bold text-logo-blue underline-offset-4 hover:underline"
                >
                  {m.cnx_oubli_lien()}
                </Link>
                .
              </span>
            </p>
          </div>
          <p className="mt-6 text-center text-sm font-semibold text-muted-foreground">
            {m.cnx_pas_de_compte()}{" "}
            <Link
              to="/inscription"
              className="font-bold text-logo-blue underline-offset-4 hover:underline"
            >
              {m.cnx_creer()}
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
