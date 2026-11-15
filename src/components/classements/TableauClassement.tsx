import { ChevronLeft, ChevronRight, Medal } from "lucide-react";
import type { ReactNode } from "react";

import { Button } from "@/components/ui/button";
import { formaterPoints, formaterRang, nombreDePages } from "@/lib/classements";

// Une ligne affichable : un élève, un encadreur ou un club. Le sous-titre porte le club ou l'établissement, et la
// DRE ; aucune donnée personnelle n'arrive ici sans être déjà publique (spec 036).
export type LigneAffichee = {
  cle: string;
  rang: number;
  nom: string;
  sousTitre: string;
  points: number;
  estMoi?: boolean;
  action?: ReactNode;
};

const COULEURS_PODIUM = [
  "bg-sun/30 ring-sun",
  "bg-mist-soft ring-border",
  "bg-[color-mix(in_oklch,var(--tangerine)_18%,white)] ring-tangerine/40",
];

export function Podium({ lignes }: { lignes: LigneAffichee[] }) {
  if (lignes.length === 0) return null;
  return (
    <ol aria-label="Les trois premiers" className="grid gap-3 sm:grid-cols-3">
      {lignes.map((ligne) => (
        <li
          key={ligne.cle}
          className={`rounded-3xl p-5 ring-1 ${COULEURS_PODIUM[Math.min(ligne.rang, 3) - 1]}`}
        >
          <p className="flex items-center gap-2 text-sm font-extrabold uppercase tracking-wider text-logo-blue">
            <Medal aria-hidden className="size-5 text-primary" /> {formaterRang(ligne.rang)}
          </p>
          <p className="mt-2 break-words font-display text-2xl text-ink">{ligne.nom}</p>
          <p className="mt-1 text-sm font-semibold text-muted-foreground">{ligne.sousTitre}</p>
          <p className="mt-3 font-display text-3xl text-primary">
            {formaterPoints(ligne.points)} <span className="text-base text-ink/60">pts</span>
          </p>
        </li>
      ))}
    </ol>
  );
}

export function ListeClassement({ lignes, libelle }: { lignes: LigneAffichee[]; libelle: string }) {
  if (lignes.length === 0) return null;
  return (
    <ol
      aria-label={libelle}
      className="divide-y overflow-hidden rounded-3xl bg-white shadow-sm ring-1 ring-border"
    >
      {lignes.map((ligne) => (
        <li
          key={ligne.cle}
          className={`flex items-center gap-4 px-4 py-3 sm:px-5 ${ligne.estMoi ? "bg-primary/10" : ""}`}
        >
          <span className="w-12 shrink-0 text-center font-display text-xl text-logo-blue">
            {formaterRang(ligne.rang)}
          </span>
          <div className="min-w-0 flex-1">
            <p className="break-words font-bold text-ink">
              {ligne.nom}
              {ligne.estMoi && (
                <span className="ml-2 rounded-full bg-primary px-2 py-0.5 text-xs font-extrabold text-white">
                  Toi
                </span>
              )}
            </p>
            {ligne.sousTitre && (
              <p className="break-words text-xs font-semibold text-muted-foreground">
                {ligne.sousTitre}
              </p>
            )}
          </div>
          <span className="shrink-0 font-extrabold text-ink">
            {formaterPoints(ligne.points)} pts
          </span>
          {ligne.action}
        </li>
      ))}
    </ol>
  );
}

export function Pagination({
  page,
  total,
  parPage,
  allerA,
}: {
  page: number;
  total: number;
  parPage: number;
  allerA: (page: number) => void;
}) {
  const pages = nombreDePages(total, parPage);
  if (pages <= 1) return null;
  return (
    <nav
      aria-label="Pages du classement"
      className="flex flex-wrap items-center justify-between gap-3"
    >
      <Button
        variant="outline"
        className="rounded-full font-bold"
        disabled={page <= 1}
        onClick={() => allerA(page - 1)}
      >
        <ChevronLeft className="size-4" /> Précédents
      </Button>
      <p className="text-sm font-semibold text-muted-foreground">
        Page {page} sur {pages} · {total.toLocaleString("fr-FR")} classés
      </p>
      <Button
        variant="outline"
        className="rounded-full font-bold"
        disabled={page >= pages}
        onClick={() => allerA(page + 1)}
      >
        Suivants <ChevronRight className="size-4" />
      </Button>
    </nav>
  );
}

export function Choix<T extends string>({
  libelle,
  options,
  valeur,
  choisir,
}: {
  libelle: string;
  options: { valeur: T; libelle: string }[];
  valeur: T;
  choisir: (valeur: T) => void;
}) {
  return (
    <div role="group" aria-label={libelle} className="flex flex-wrap gap-2">
      {options.map((option) => (
        <button
          key={option.valeur}
          type="button"
          aria-pressed={option.valeur === valeur}
          onClick={() => choisir(option.valeur)}
          className={`rounded-full px-4 py-2 text-sm font-bold ring-1 transition ${
            option.valeur === valeur
              ? "bg-night text-white ring-night"
              : "bg-white ring-border hover:ring-night/30"
          }`}
        >
          {option.libelle}
        </button>
      ))}
    </div>
  );
}
