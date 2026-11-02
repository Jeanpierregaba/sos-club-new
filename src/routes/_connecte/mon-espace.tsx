import { useQueryClient } from "@tanstack/react-query";
import { createFileRoute, Link, useRouter } from "@tanstack/react-router";
import { LogOut } from "lucide-react";
import { useState } from "react";

import { ServiceIndisponible } from "@/components/ServiceIndisponible";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { CLE_MOI } from "@/hooks/use-moi";
import {
  chargerChiffresAdmin,
  deconnecter,
  ErreurApi,
  MESSAGE_INDISPONIBLE,
} from "@/lib/api/client";

const LIBELLES_ROLE = { eleve: "Élève", encadreur: "Encadreur", admin: "Admin" } as const;

export const Route = createFileRoute("/_connecte/mon-espace")({
  // Rien en cache : les données d'un compte ne doivent pas s'afficher, même un instant, au compte suivant.
  gcTime: 0,
  loader: ({ context }) => (context.moi.role === "admin" ? chargerChiffresAdmin() : null),
  head: () => ({
    meta: [
      { title: "Mon espace — Club Santé SOS Docteur TV" },
      { name: "robots", content: "noindex" },
    ],
  }),
  errorComponent: ServiceIndisponible,
  component: MonEspace,
});

function MonEspace() {
  const { moi } = Route.useRouteContext();
  const chiffres = Route.useLoaderData();
  const queryClient = useQueryClient();
  const router = useRouter();
  const [erreur, setErreur] = useState<string | null>(null);
  const [enCours, setEnCours] = useState(false);

  const seDeconnecter = async () => {
    setErreur(null);
    setEnCours(true);
    try {
      await deconnecter();
      queryClient.setQueryData(CLE_MOI, null);
      await router.navigate({ to: "/", replace: true });
    } catch (e) {
      setErreur(e instanceof ErreurApi ? e.message : MESSAGE_INDISPONIBLE);
      setEnCours(false);
    }
  };

  return (
    <main className="flex min-h-screen items-center justify-center bg-mist-soft px-4 py-10">
      <section className="w-full max-w-lg rounded-3xl bg-card p-6 text-center shadow-card sm:p-8">
        <h1 className="text-3xl text-logo-blue">
          salut <span className="text-primary">{moi.prenom} !</span>
        </h1>
        <p className="mt-2 text-muted-foreground">
          Rôle : <strong className="text-foreground">{LIBELLES_ROLE[moi.role]}</strong>
        </p>
        <p className="mt-1 text-sm text-muted-foreground">Ton espace s'enrichira bientôt.</p>

        {chiffres && (
          <dl className="mt-6 grid grid-cols-3 gap-3">
            {(["eleve", "encadreur", "admin"] as const).map((role) => (
              <div key={role} className="flex flex-col-reverse rounded-2xl bg-mist p-3">
                <dt className="text-xs font-semibold text-muted-foreground">
                  {LIBELLES_ROLE[role]}
                </dt>
                <dd className="font-display text-2xl text-logo-blue">{chiffres.comptes[role]}</dd>
              </div>
            ))}
          </dl>
        )}

        {erreur && (
          <Alert variant="destructive" className="mt-6 text-left">
            <AlertDescription>{erreur}</AlertDescription>
          </Alert>
        )}

        <div className="mt-6 flex flex-col items-center gap-4">
          <Button
            variant="outline"
            onClick={seDeconnecter}
            disabled={enCours}
            className="h-12 rounded-full px-6 font-bold"
          >
            <LogOut className="h-5 w-5" />
            Me déconnecter
          </Button>
          <Link
            to="/"
            className="text-sm font-bold text-logo-blue underline-offset-4 hover:underline"
          >
            Retour à l'accueil
          </Link>
        </div>
      </section>
    </main>
  );
}
