import { m } from "@/paraglide/messages.js";
import { Link } from "@tanstack/react-router";
import { ArrowLeft } from "lucide-react";
import type { ReactNode } from "react";

// La mise en page sobre des pages de compte publiques (spec 039) : mot de passe oublié, nouveau mot de passe.
export function PageCompte({
  titre,
  accent,
  intro,
  children,
}: {
  titre: string;
  accent: string;
  intro: string;
  children: ReactNode;
}) {
  return (
    <main className="min-h-screen bg-carnet px-4 py-10 sm:px-6">
      <div className="mx-auto max-w-lg">
        <Link
          to="/connexion"
          className="inline-flex items-center gap-2 text-sm font-bold text-logo-blue hover:underline"
        >
          <ArrowLeft className="size-4" /> {m.mdp_connexion()}
        </Link>
        <h1 className="mt-4 text-4xl leading-tight">
          <span className="text-logo-blue">{titre}</span>{" "}
          <span className="text-primary">{accent}</span>
        </h1>
        <p className="mt-2 mb-6 font-medium text-muted-foreground">{intro}</p>
        <div className="rounded-3xl bg-white p-6 shadow-card ring-1 ring-border sm:p-8">
          {children}
        </div>
      </div>
    </main>
  );
}
