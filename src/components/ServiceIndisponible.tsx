import { useRouter, type ErrorComponentProps } from "@tanstack/react-router";

import { Button } from "@/components/ui/button";

export function ServiceIndisponible({ reset }: ErrorComponentProps) {
  const router = useRouter();

  return (
    <main className="flex min-h-screen items-center justify-center bg-mist-soft px-4">
      <div className="max-w-md text-center">
        <h1 className="text-3xl text-logo-blue">
          service <span className="text-primary">indisponible</span>
        </h1>
        <p className="mt-3 text-muted-foreground">
          Impossible de charger ton espace pour le moment. Réessaie dans quelques instants.
        </p>
        <div className="mt-6 flex flex-wrap justify-center gap-3">
          <Button
            onClick={() => {
              router.invalidate();
              reset();
            }}
            className="btn-fx rounded-full font-bold"
          >
            Réessayer
          </Button>
          <Button asChild variant="outline" className="rounded-full font-bold">
            <a href="/">Retour à l'accueil</a>
          </Button>
        </div>
      </div>
    </main>
  );
}
