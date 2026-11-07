import { Link } from "@tanstack/react-router";
import { ArrowLeft } from "lucide-react";
import type { ReactNode } from "react";

// Le cadre des pages de rédaction (spec 023).
export function PageArticle({
  titre,
  accent,
  children,
}: {
  titre: string;
  accent: string;
  children: ReactNode;
}) {
  return (
    <main className="min-h-screen bg-carnet px-4 py-10 sm:px-6">
      <div className="mx-auto max-w-3xl">
        <Link
          to="/mes-articles"
          className="inline-flex items-center gap-2 text-sm font-bold text-logo-blue hover:underline"
        >
          <ArrowLeft className="size-4" /> Mes articles
        </Link>
        <h1 className="mb-6 mt-4 text-4xl leading-tight md:text-5xl">
          <span className="text-logo-blue">{titre}</span>{" "}
          <span className="text-primary">{accent}</span>
        </h1>
        {children}
      </div>
    </main>
  );
}
