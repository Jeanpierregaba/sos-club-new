import mascottesEquipe from "@/assets/mascottes-equipe.webp";
import logo from "@/assets/logo.webp";
import { Button } from "@/components/ui/button";

// Page affichée quand le mode maintenance est actif (spec 047) : les mascottes de l'équipe et un message fixe.
export function PageMaintenance() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-carnet px-4 py-10">
      <div className="w-full max-w-lg text-center">
        <a
          href="/"
          aria-label="Club Santé SOS Docteur TV"
          className="inline-block transition hover:scale-105"
        >
          <img
            src={logo}
            alt="Club Santé SOS Docteur TV"
            width={1014}
            height={195}
            className="h-11 w-auto"
          />
        </a>

        <section className="mt-8 rounded-3xl bg-white p-6 shadow-card ring-1 ring-border sm:p-10">
          <p className="flex items-center justify-center gap-3 text-xs font-extrabold uppercase tracking-widest text-logo-red">
            <span className="h-1 w-6 rounded-full bg-primary" />
            Maintenance
          </p>
          <h1 className="mt-3 text-3xl leading-tight text-logo-blue sm:text-4xl">
            On revient <span className="text-primary">très vite !</span>
          </h1>
          <p className="mt-3 text-lg font-medium text-muted-foreground">
            La plateforme est actuellement en maintenance et sera de nouveau disponible.
          </p>
          <img
            src={mascottesEquipe}
            alt="Les sept mascottes des Clubs Santé"
            width={1122}
            height={1402}
            className="mx-auto mt-6 w-full max-w-sm"
          />
          <div className="mt-6 flex justify-center">
            <Button asChild className="btn-fx rounded-full font-bold">
              <a href="/">Réessayer</a>
            </Button>
          </div>
        </section>

        <a
          href="/connexion"
          className="mt-6 inline-block text-sm font-bold text-logo-blue hover:underline"
        >
          Connexion de l'équipe
        </a>
      </div>
    </main>
  );
}
