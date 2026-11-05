import type { CSSProperties } from "react";

// Décors animés posés derrière le contenu d'une bannière : cercles pointillés qui tournent, carrés qui
// flottent, croix qui scintillent, petits points qui dérivent. Purement décoratif : invisible des lecteurs
// d'écran, sans effet sur les clics, figé si l'utilisateur réduit les animations.
// `ton` : « sombre » pour une bannière foncée (traits clairs), « clair » pour une bannière claire.

type Ton = "sombre" | "clair";

const TONS: Record<Ton, { trait: string; accent: string; plein: string }> = {
  sombre: { trait: "text-white/25", accent: "text-sun/70", plein: "bg-white/20" },
  clair: { trait: "text-tangerine/45", accent: "text-logo-red/45", plein: "bg-tangerine/30" },
};

const delai = (s: number) => ({ animationDelay: `${s}s` }) as CSSProperties;

function Croix({ className, style }: { className: string; style?: CSSProperties }) {
  return (
    <svg viewBox="0 0 24 24" className={className} style={style}>
      <path d="M12 3v18M3 12h18" stroke="currentColor" strokeWidth="3.5" strokeLinecap="round" />
    </svg>
  );
}

export function DecorAnime({ ton = "sombre" }: { ton?: Ton }) {
  const c = TONS[ton];
  return (
    <div aria-hidden className="pointer-events-none absolute inset-0 -z-10 overflow-hidden">
      {/* Cercles pointillés : l'un tourne, l'autre voit ses tirets défiler. */}
      <svg
        viewBox="0 0 100 100"
        className={`absolute -left-10 bottom-[6%] size-24 md:size-32 ${c.trait} motion-safe:animate-[spin_36s_linear_infinite]`}
      >
        <circle
          cx="50"
          cy="50"
          r="46"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.5"
          strokeDasharray="3 9"
          strokeLinecap="round"
        />
      </svg>
      <svg
        viewBox="0 0 100 100"
        className={`absolute right-[4%] top-[10%] hidden size-40 md:block ${c.trait}`}
      >
        <circle
          cx="50"
          cy="50"
          r="44"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeDasharray="10 10"
          className="motion-safe:animate-trace"
        />
      </svg>

      {/* Carrés arrondis qui flottent en tournant. */}
      <span
        className={`absolute left-[42%] top-[12%] size-5 rounded-md border-2 border-current md:size-7 ${c.trait} motion-safe:animate-flotte-tourne`}
      />
      <span
        style={delai(-5)}
        className={`absolute bottom-[26%] right-[10%] size-8 rotate-12 rounded-lg border-2 border-current md:size-10 ${c.accent} motion-safe:animate-flotte-tourne`}
      />
      <span
        style={delai(-8)}
        className={`absolute bottom-[8%] left-[38%] hidden size-4 rounded ${c.plein} md:block motion-safe:animate-flotte-tourne`}
      />

      {/* Croix « santé » qui scintillent, chacune à son rythme. */}
      <Croix
        className={`absolute left-[3%] top-[30%] hidden size-5 md:block ${c.accent} motion-safe:animate-scintille`}
      />
      <Croix
        style={delai(-1.5)}
        className={`absolute right-[30%] top-[8%] size-4 ${c.trait} motion-safe:animate-scintille`}
      />
      <Croix
        style={delai(-2.8)}
        className={`absolute bottom-[18%] right-[38%] hidden size-6 md:block ${c.accent} motion-safe:animate-scintille`}
      />

      {/* Petits points qui dérivent. */}
      <span
        className={`absolute left-[26%] top-[30%] size-2.5 rounded-full ${c.plein} motion-safe:animate-derive`}
      />
      <span
        style={delai(-7)}
        className={`absolute right-[22%] top-[40%] size-3 rounded-full ${c.plein} motion-safe:animate-derive`}
      />
      <span
        style={delai(-12)}
        className={`absolute bottom-[34%] left-[18%] hidden size-2 rounded-full ${c.plein} md:block motion-safe:animate-derive`}
      />
    </div>
  );
}
