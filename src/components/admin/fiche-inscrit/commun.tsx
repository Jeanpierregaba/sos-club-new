import { ChevronLeft, ChevronRight, Loader2 } from "lucide-react";
import type { ReactNode } from "react";

// Commun aux onglets de la fiche d'un inscrit (spec 045).

export function Chargement({ erreur }: { erreur: string | null }) {
  if (erreur)
    return (
      <p role="alert" className="text-sm font-semibold text-destructive">
        {erreur}
      </p>
    );
  return (
    <p className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
      <Loader2 className="size-4 animate-spin" /> Chargement…
    </p>
  );
}

export function Bloc({
  titre,
  actions,
  children,
}: {
  titre: string;
  actions?: ReactNode;
  children: ReactNode;
}) {
  return (
    <section className="rounded-3xl bg-white p-6 shadow-sm ring-1 ring-border md:p-8">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-xl text-logo-blue">{titre}</h2>
        {actions}
      </div>
      <div className="mt-4">{children}</div>
    </section>
  );
}

export function Vide({ children }: { children: ReactNode }) {
  return (
    <p className="rounded-2xl bg-mist-soft px-4 py-6 text-center text-sm font-semibold text-muted-foreground">
      {children}
    </p>
  );
}

export function Chiffres({ chiffres }: { chiffres: [string, string | number][] }) {
  return (
    <dl className="grid grid-cols-2 gap-3 md:grid-cols-4">
      {chiffres.map(([libelle, valeur]) => (
        <div key={libelle} className="flex flex-col-reverse rounded-2xl bg-mist-soft px-4 py-3">
          <dt className="text-xs font-extrabold uppercase tracking-wider text-muted-foreground">
            {libelle}
          </dt>
          <dd className="text-2xl font-extrabold tabular-nums text-logo-blue">{valeur}</dd>
        </div>
      ))}
    </dl>
  );
}

export function Liste({
  libelle,
  valeur,
  options,
  onChange,
}: {
  libelle: string;
  valeur: string;
  options: { valeur: string; libelle: string }[];
  onChange: (valeur: string) => void;
}) {
  return (
    <label className="flex items-center gap-2 text-sm font-semibold">
      <span className="text-muted-foreground">{libelle}</span>
      <select
        value={valeur}
        onChange={(e) => onChange(e.target.value)}
        className="h-9 rounded-full border bg-white px-3 text-sm font-semibold"
      >
        {options.map((o) => (
          <option key={o.valeur} value={o.valeur}>
            {o.libelle}
          </option>
        ))}
      </select>
    </label>
  );
}

export function Pagination({
  page,
  parPage,
  total,
  unite,
  onPage,
}: {
  page: number;
  parPage: number;
  total: number;
  unite: [string, string];
  onPage: (page: number) => void;
}) {
  const pages = Math.max(1, Math.ceil(total / parPage));
  return (
    <div className="mt-4 flex items-center justify-between gap-3 text-sm font-semibold">
      <span className="text-muted-foreground">
        {total} {total > 1 ? unite[1] : unite[0]}
      </span>
      {pages > 1 && (
        <div className="flex items-center gap-2">
          <button
            type="button"
            disabled={page <= 1}
            onClick={() => onPage(page - 1)}
            aria-label="Page précédente"
            className="inline-flex size-9 items-center justify-center rounded-full border bg-white disabled:opacity-40"
          >
            <ChevronLeft className="size-4" />
          </button>
          <span>
            {page} / {pages}
          </span>
          <button
            type="button"
            disabled={page >= pages}
            onClick={() => onPage(page + 1)}
            aria-label="Page suivante"
            className="inline-flex size-9 items-center justify-center rounded-full border bg-white disabled:opacity-40"
          >
            <ChevronRight className="size-4" />
          </button>
        </div>
      )}
    </div>
  );
}

const TONS = {
  vert: "bg-emerald-100 text-emerald-800",
  rouge: "bg-logo-red/10 text-logo-red",
  gris: "bg-mist-soft text-muted-foreground",
  or: "bg-sun/30 text-ink",
};

export function Pastille({
  ton = "gris",
  children,
}: {
  ton?: keyof typeof TONS;
  children: ReactNode;
}) {
  return (
    <span
      className={`whitespace-nowrap rounded-full px-2 py-0.5 text-xs font-extrabold ${TONS[ton]}`}
    >
      {children}
    </span>
  );
}

// Une page suivante ou un filtre qui échoue : l'ancienne liste reste, grisée, sous le message d'erreur.
export function Rafraichissement({
  erreur,
  enCours,
  children,
}: {
  erreur: string | null;
  enCours: boolean;
  children: ReactNode;
}) {
  return (
    <>
      {erreur && (
        <p role="alert" className="mt-4 text-sm font-semibold text-destructive">
          {erreur}
        </p>
      )}
      <div aria-busy={enCours} className={enCours || erreur ? "opacity-50" : undefined}>
        {children}
      </div>
    </>
  );
}
