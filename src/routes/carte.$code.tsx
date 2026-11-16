import { createFileRoute } from "@tanstack/react-router";

import { Verifier } from "@/components/cartes/Verifier";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";

// Vérification publique d'une carte numérique (spec 040), ouverte par son QR code. Elle est faite par le navigateur,
// pas au rendu serveur : la limite par adresse IP de l'API doit voir l'adresse du visiteur, pas celle du site.
export const Route = createFileRoute("/carte/$code")({
  head: () => ({
    meta: [
      { title: "Vérifier une carte — Club Santé SOS Docteur TV" },
      { name: "robots", content: "noindex" },
      { name: "referrer", content: "no-referrer" },
    ],
  }),
  component: PageVerification,
});

function PageVerification() {
  const { code } = Route.useParams();
  return (
    <div className="min-h-screen overflow-x-clip bg-carnet text-ink">
      <SiteHeader />
      <main className="mx-auto max-w-3xl px-4 pb-20 pt-8 sm:px-5">
        <header className="pt-4">
          <p className="flex items-center gap-3 text-sm font-extrabold uppercase tracking-widest text-logo-red">
            <span className="h-1 w-8 rounded-full bg-primary" />
            Clubs Santé SOS Docteur TV
          </p>
          <h1 className="mt-3 text-4xl leading-tight md:text-5xl">
            <span className="text-logo-blue">Vérifier une</span>{" "}
            <span className="text-primary">carte</span>
          </h1>
        </header>
        <div className="mt-8">
          <Verifier code={code} />
        </div>
      </main>
      <SiteFooter />
    </div>
  );
}
