import { useState, type CSSProperties } from "react";
import { useQuery } from "@tanstack/react-query";
import { ArrowRight, Compass, Share2 } from "lucide-react";

import { etatQuelAxe, type PartieQuelAxe } from "@/lib/api/client";
import { axeDecouverte, partagerAxe } from "@/lib/axes-decouverte";

// « Mon axe » dans l'espace élève (spec 032) : le compteur de « Quel axe est fait pour toi ? » et les résultats
// des parties terminées. Le jeu lui-même s'ouvre sur l'accueil.
export function MonAxe() {
  const etat = useQuery({ queryKey: ["quel-axe"], queryFn: etatQuelAxe, retry: false });
  if (etat.isPending || etat.isError) return null;
  const { utilisees, limite, restantes, en_cours: enCours, historique } = etat.data;
  const action = enCours
    ? "Reprendre ma partie"
    : restantes > 0
      ? utilisees === 0
        ? "Commencer le jeu"
        : `Rejouer (${restantes} partie${restantes > 1 ? "s" : ""} restante${restantes > 1 ? "s" : ""})`
      : "Revoir mes résultats";

  return (
    <section className="mt-6 rounded-3xl bg-white p-6 shadow-card ring-1 ring-border">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2 className="text-2xl">
            <span className="text-logo-blue">Mon</span> <span className="text-primary">axe</span>
          </h2>
          <p className="mt-1 text-sm font-semibold text-muted-foreground">
            Quel axe est fait pour toi&#8239;? · Participations utilisées : {utilisees}/{limite} ·
            Participations restantes : {restantes}
          </p>
        </div>
        <a
          href="/?test=quel-axe#quel-axe"
          className="btn-fx inline-flex items-center gap-2 rounded-full bg-grape px-5 py-2.5 text-sm font-bold text-white"
        >
          <Compass className="size-4" /> {action}
        </a>
      </div>
      {historique.length > 0 ? (
        <ul className="mt-4 grid gap-3 sm:grid-cols-3">
          {historique.map((partie) => (
            <Resultat key={partie.id} partie={partie} />
          ))}
        </ul>
      ) : (
        <p className="mt-4 font-medium text-ink/75">
          Réponds à sept questions et découvre l’axe des Clubs Santé qui correspond le mieux à tes
          envies. Aucun point en jeu.
        </p>
      )}
    </section>
  );
}

function Resultat({ partie }: { partie: PartieQuelAxe }) {
  const [message, setMessage] = useState<string | null>(null);
  const axe = axeDecouverte(partie.resultat!.principal);
  const autres = partie.resultat!.autres.map(axeDecouverte);
  return (
    <li
      style={{ "--axe": axe.couleur } as CSSProperties}
      className="flex flex-col gap-2 rounded-2xl border-2 border-(color:--axe)/40 p-3"
    >
      <div className="flex items-center gap-3">
        <span className="size-12 shrink-0 overflow-hidden rounded-xl bg-(color:--axe)">
          <img
            src={axe.img}
            alt=""
            width={1414}
            height={2000}
            className="size-full scale-150 object-cover object-top"
          />
        </span>
        <span>
          <span className="block text-xs font-bold text-muted-foreground">
            Partie {partie.numero} · {new Date(partie.terminee_le!).toLocaleDateString("fr-FR")}
          </span>
          <a
            href={`/les-7-axes#axe-${axe.n}`}
            className="inline-flex items-center gap-1 font-bold text-ink hover:text-grape"
          >
            {axe.nom} <ArrowRight className="size-3.5" />
          </a>
        </span>
      </div>
      <p className="text-xs font-semibold text-ink/65">
        À explorer aussi : {autres.map((a) => a.nom).join(" · ")}
      </p>
      <button
        type="button"
        onClick={async () => setMessage(await partagerAxe(axe.nom))}
        className="inline-flex items-center gap-1.5 self-start text-sm font-bold text-grape hover:underline"
      >
        <Share2 className="size-3.5" /> Partager ce résultat
      </button>
      {message && <p className="text-xs font-semibold text-ink">{message}</p>}
    </li>
  );
}
