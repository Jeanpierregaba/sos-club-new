// Sélecteur FR / EN / DE (spec 052) : ouvre la même page dans l'autre langue. Un vrai changement de page (pas une
// navigation du routeur) : tous les textes, rendus serveur compris, passent ainsi dans la nouvelle langue.
import { useRouterState } from "@tanstack/react-router";

import { estTraduite, LANGUES, langueCourante, localiser, NOMS_DES_LANGUES } from "@/lib/langues";
import { cn } from "@/lib/utils";
import { m } from "@/paraglide/messages.js";

export function SelecteurLangue({ className }: { className?: string }) {
  const { pathname, searchStr, hash } = useRouterState({ select: (etat) => etat.location });
  // Les espaces connectés et l'admin restent en français : pas de choix à proposer.
  if (!estTraduite(pathname)) return null;
  const actuelle = langueCourante();
  const page = pathname + searchStr + (hash ? `#${hash}` : "");

  return (
    <nav
      aria-label={m.langue_choisir()}
      className={cn("flex items-center rounded-full border px-2 py-1 text-sm font-bold", className)}
    >
      {LANGUES.map((langue, n) => (
        <span key={langue} className="flex items-center">
          {n > 0 && (
            <span aria-hidden className="text-muted-foreground">
              /
            </span>
          )}
          <a
            href={localiser(page, langue)}
            hrefLang={langue}
            lang={langue}
            aria-current={langue === actuelle ? "true" : undefined}
            aria-label={m.langue_lire_en(
              { langue: NOMS_DES_LANGUES[langue].nom },
              { locale: langue },
            )}
            className={cn(
              "rounded-full px-1.5 py-1 transition hover:text-logo-blue",
              langue === actuelle ? "text-logo-blue" : "text-muted-foreground",
            )}
          >
            {NOMS_DES_LANGUES[langue].court}
          </a>
        </span>
      ))}
    </nav>
  );
}
