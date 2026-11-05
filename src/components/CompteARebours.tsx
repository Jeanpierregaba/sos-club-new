import { useEffect, useState } from "react";

// Compte à rebours jusqu'à `cible` (date ISO) : jours, heures, minutes, secondes.
// Rendu serveur : des tirets, pour que le HTML ne dépende pas de l'heure du serveur ; le navigateur prend le relais.
const UNITES = [
  { t: "Jours", ms: 86_400_000 },
  { t: "Heures", ms: 3_600_000 },
  { t: "Minutes", ms: 60_000 },
  { t: "Secondes", ms: 1000 },
] as const;

function decouper(reste: number) {
  return UNITES.map((u, i) => {
    const auDessus = i === 0 ? Infinity : UNITES[i - 1]!.ms;
    return Math.floor((reste % auDessus) / u.ms);
  });
}

export function CompteARebours({ cible }: { cible: string }) {
  const fin = new Date(cible).getTime();
  const [maintenant, setMaintenant] = useState<number | null>(null);

  useEffect(() => {
    setMaintenant(Date.now());
    const minuterie = window.setInterval(() => setMaintenant(Date.now()), 1000);
    return () => window.clearInterval(minuterie);
  }, []);

  const reste = maintenant === null ? null : Math.max(0, fin - maintenant);
  if (reste === 0)
    return <p className="font-display text-4xl text-sun md:text-5xl">C’est parti !</p>;
  const valeurs = reste === null ? null : decouper(reste);

  return (
    <div>
      <ol className="grid max-w-xl grid-cols-4 gap-2 sm:gap-3">
        {UNITES.map((u, i) => (
          <li
            key={u.t}
            className="relative overflow-hidden rounded-2xl bg-white/10 px-1 pb-3 pt-4 text-center ring-1 ring-white/15 backdrop-blur-sm"
          >
            {/* Le pli du milieu, comme un afficheur à palettes. */}
            <span aria-hidden className="absolute inset-x-0 top-1/2 h-px bg-night/40" />
            <span className="block font-display text-4xl leading-none tabular-nums text-sun sm:text-5xl md:text-6xl">
              {valeurs === null ? "--" : String(valeurs[i]).padStart(2, "0")}
            </span>
            <span className="mt-2 block text-[11px] font-extrabold uppercase tracking-widest text-white/70 sm:text-xs">
              {u.t}
            </span>
          </li>
        ))}
      </ol>
      {/* Pour les lecteurs d'écran : la date, une seule fois, plutôt qu'une annonce chaque seconde. */}
      <p className="sr-only">
        Coup d’envoi le{" "}
        {new Date(cible).toLocaleDateString("fr-FR", {
          day: "numeric",
          month: "long",
          year: "numeric",
          timeZone: "UTC",
        })}
        .
      </p>
    </div>
  );
}
