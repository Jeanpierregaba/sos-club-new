import { useRouter, type ErrorComponentProps } from "@tanstack/react-router";

import { PageMaintenance } from "@/components/PageMaintenance";
import { Button } from "@/components/ui/button";
import { estMaintenance } from "@/lib/api/client";
import { lien } from "@/lib/langues";
import { m } from "@/paraglide/messages.js";

export function ServiceIndisponible({ error, reset }: ErrorComponentProps) {
  const router = useRouter();

  // Une route bloquée par la maintenance n'est pas une panne : on affiche la page dédiée.
  if (estMaintenance(error)) return <PageMaintenance />;

  return (
    <main className="flex min-h-screen items-center justify-center bg-mist-soft px-4">
      <div className="max-w-md text-center">
        <h1 className="text-3xl text-logo-blue">
          {m.service_titre_1()} <span className="text-primary">{m.service_titre_2()}</span>
        </h1>
        <p className="mt-3 text-muted-foreground">{m.service_texte()}</p>
        <div className="mt-6 flex flex-wrap justify-center gap-3">
          <Button
            onClick={() => {
              router.invalidate();
              reset();
            }}
            className="btn-fx rounded-full font-bold"
          >
            {m.service_reessayer()}
          </Button>
          <Button asChild variant="outline" className="rounded-full font-bold">
            <a href={lien("/")}>{m.service_accueil()}</a>
          </Button>
        </div>
      </div>
    </main>
  );
}
