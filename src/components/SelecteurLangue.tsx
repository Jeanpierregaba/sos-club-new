// Sélecteur FR / EN / DE (spec 052) : un menu déroulant à drapeaux ronds qui ouvre la même page dans l'autre langue.
// Un vrai changement de page (pas une navigation du routeur) : tous les textes, rendus serveur compris, passent ainsi
// dans la nouvelle langue.
import { useRouterState } from "@tanstack/react-router";
import { Check, ChevronDown } from "lucide-react";
import { useId } from "react";

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  estTraduite,
  LANGUES,
  langueCourante,
  localiser,
  NOMS_DES_LANGUES,
  type Langue,
} from "@/lib/langues";
import { cn } from "@/lib/utils";
import { m } from "@/paraglide/messages.js";

/** Drapeau dessiné en SVG (les émojis drapeaux ne s'affichent pas sous Windows), recadré dans un rond. */
function Drapeau({ langue, className }: { langue: Langue; className?: string }) {
  // Identifiant propre à chaque drapeau : le sélecteur apparaît deux fois (en-tête et menu mobile).
  const decoupe = useId();
  return (
    <span
      aria-hidden
      className={cn(
        "inline-flex size-6 shrink-0 overflow-hidden rounded-full ring-1 ring-black/10",
        className,
      )}
    >
      {langue === "fr" && (
        <svg viewBox="0 0 3 2" preserveAspectRatio="xMidYMid slice" className="size-full">
          <rect width="1" height="2" fill="#002654" />
          <rect x="1" width="1" height="2" fill="#fff" />
          <rect x="2" width="1" height="2" fill="#CE1126" />
        </svg>
      )}
      {langue === "de" && (
        <svg viewBox="0 0 5 3" preserveAspectRatio="xMidYMid slice" className="size-full">
          <rect width="5" height="1" fill="#000" />
          <rect y="1" width="5" height="1" fill="#DD0000" />
          <rect y="2" width="5" height="1" fill="#FFCE00" />
        </svg>
      )}
      {langue === "en" && (
        <svg viewBox="0 0 60 30" preserveAspectRatio="xMidYMid slice" className="size-full">
          <clipPath id={decoupe}>
            <path d="M30,15 h30 v15 z v15 h-30 z h-30 v-15 z v-15 h30 z" />
          </clipPath>
          <rect width="60" height="30" fill="#012169" />
          <path d="M0,0 L60,30 M60,0 L0,30" stroke="#fff" strokeWidth="6" />
          <path
            d="M0,0 L60,30 M60,0 L0,30"
            clipPath={`url(#${decoupe})`}
            stroke="#C8102E"
            strokeWidth="4"
          />
          <path d="M30,0 v30 M0,15 h60" stroke="#fff" strokeWidth="10" />
          <path d="M30,0 v30 M0,15 h60" stroke="#C8102E" strokeWidth="6" />
        </svg>
      )}
    </span>
  );
}

export function SelecteurLangue({ className }: { className?: string }) {
  const { pathname, searchStr, hash } = useRouterState({ select: (etat) => etat.location });
  // Les espaces connectés et l'admin restent en français : pas de choix à proposer.
  if (!estTraduite(pathname)) return null;
  const actuelle = langueCourante();
  const page = pathname + searchStr + (hash ? `#${hash}` : "");

  return (
    <DropdownMenu modal={false}>
      <DropdownMenuTrigger
        aria-label={`${m.langue_choisir()} : ${NOMS_DES_LANGUES[actuelle].nom}`}
        className={cn(
          "flex w-fit items-center gap-1 rounded-full border p-1 pr-1.5 transition hover:border-logo-blue focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-logo-blue",
          className,
        )}
      >
        <Drapeau langue={actuelle} />
        <ChevronDown aria-hidden className="size-4 text-muted-foreground" />
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="min-w-40">
        {LANGUES.map((langue) => (
          <DropdownMenuItem key={langue} asChild className="cursor-pointer gap-3">
            <a
              href={localiser(page, langue)}
              hrefLang={langue}
              lang={langue}
              aria-current={langue === actuelle ? "true" : undefined}
              aria-label={m.langue_lire_en(
                { langue: NOMS_DES_LANGUES[langue].nom },
                { locale: langue },
              )}
            >
              <Drapeau langue={langue} />
              <span className={cn("flex-1", langue === actuelle && "font-bold")}>
                {NOMS_DES_LANGUES[langue].nom}
              </span>
              {langue === actuelle && <Check aria-hidden className="text-logo-blue" />}
            </a>
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
