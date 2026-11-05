import { ChevronRight } from "lucide-react";

// Fil d'Ariane des pages du menu : Accueil, la rubrique, puis la page. `clair` : texte blanc pour une bannière foncée.
// `parent` : un niveau intermédiaire cliquable, pour une sous-page (une édition du Hall of Fame, par exemple).
export function FilAriane({
  rubrique,
  page,
  parent,
  clair = false,
}: {
  rubrique: string;
  page: string;
  parent?: { t: string; href: string };
  clair?: boolean;
}) {
  return (
    <nav
      aria-label="Fil d’Ariane"
      className={`text-sm font-semibold ${clair ? "text-white/70" : "text-muted-foreground"}`}
    >
      <ol className="flex flex-wrap items-center gap-1.5">
        <li>
          <a href="/" className={clair ? "hover:text-white" : "hover:text-logo-blue"}>
            Accueil
          </a>
        </li>
        <li className="flex items-center gap-1.5">
          <ChevronRight aria-hidden className="size-3.5" /> {rubrique}
        </li>
        {parent && (
          <li className="flex items-center gap-1.5">
            <ChevronRight aria-hidden className="size-3.5" />
            <a href={parent.href} className={clair ? "hover:text-white" : "hover:text-logo-blue"}>
              {parent.t}
            </a>
          </li>
        )}
        <li
          aria-current="page"
          className={`flex items-center gap-1.5 ${clair ? "text-white" : "text-ink"}`}
        >
          <ChevronRight aria-hidden className="size-3.5" /> {page}
        </li>
      </ol>
    </nav>
  );
}
