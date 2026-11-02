import { useQueryClient } from "@tanstack/react-query";
import { createFileRoute, Link, redirect, useRouter } from "@tanstack/react-router";

import logo from "@/assets/logo.webp";
import { FormulaireConnexion } from "@/components/FormulaireConnexion";
import { CLE_MOI } from "@/hooks/use-moi";
import { chargerMoi, type Moi } from "@/lib/api/client";
import { cheminSur } from "@/lib/redirection";

export const Route = createFileRoute("/connexion")({
  validateSearch: (search: Record<string, unknown>): { redirection?: string } =>
    typeof search["redirection"] === "string" ? { redirection: search["redirection"] } : {},
  beforeLoad: async ({ search }) => {
    // API en panne : le formulaire s'affiche quand même et donnera le message d'erreur à l'envoi.
    const moi = await chargerMoi().catch(() => null);
    if (moi) throw redirect({ href: cheminSur(search.redirection) });
  },
  head: () => ({
    meta: [
      { title: "Connexion — Club Santé SOS Docteur TV" },
      { name: "robots", content: "noindex" },
    ],
  }),
  component: Connexion,
});

function Connexion() {
  const { redirection } = Route.useSearch();
  const queryClient = useQueryClient();
  const router = useRouter();

  const allerAuCompte = (moi: Moi) => {
    queryClient.setQueryData(CLE_MOI, moi);
    void router.navigate({ href: cheminSur(redirection), replace: true });
  };

  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-mist-soft px-4 py-10">
      <Link to="/" aria-label="Retour à l'accueil" className="transition hover:scale-105">
        <img
          src={logo}
          alt="Club Santé SOS Docteur TV"
          width={1014}
          height={195}
          className="h-12 w-auto"
        />
      </Link>
      <section className="mt-8 w-full max-w-md rounded-3xl bg-card p-6 shadow-card sm:p-8">
        <h1 className="text-center text-3xl text-logo-blue">
          content de te <span className="text-primary">revoir !</span>
        </h1>
        <p className="mt-2 mb-6 text-center text-muted-foreground">
          Connecte-toi pour retrouver ton espace.
        </p>
        <FormulaireConnexion onConnecte={allerAuCompte} />
      </section>
      <Link
        to="/"
        className="mt-6 text-sm font-bold text-logo-blue underline-offset-4 hover:underline"
      >
        Retour à l'accueil
      </Link>
    </main>
  );
}
