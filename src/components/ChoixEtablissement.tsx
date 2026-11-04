import { Check, Loader2, Search, X } from "lucide-react";
import { useEffect, useId, useState } from "react";

import { Input } from "@/components/ui/input";
import { chercherEtablissements, type EtablissementTrouve } from "@/lib/api/client";

export type EtablissementChoisi = { id: string; nom: string; detail: string };

const choixDe = (e: EtablissementTrouve): EtablissementChoisi => ({
  id: e.id,
  nom: e.nom,
  detail: `${e.iesg} · ${e.dre}`,
});

// Recherche d'un établissement actif du référentiel (spec 016), mot à mot, à partir de 2 lettres.
export function ChoixEtablissement({
  valeur,
  onChoix,
  invalide = false,
  exclure,
}: {
  valeur: EtablissementChoisi | null;
  onChoix: (choix: EtablissementChoisi | null) => void;
  invalide?: boolean;
  exclure?: string;
}) {
  const identifiant = useId();
  const [recherche, setRecherche] = useState("");
  const [resultats, setResultats] = useState<EtablissementTrouve[] | null>(null);
  const [enCours, setEnCours] = useState(false);
  const [erreur, setErreur] = useState(false);

  useEffect(() => {
    const texte = recherche.trim();
    if (texte.replace(/\s/g, "").length < 2) {
      setResultats(null);
      return;
    }
    let annule = false;
    const minuteur = setTimeout(() => {
      setEnCours(true);
      setErreur(false);
      chercherEtablissements({ recherche: texte })
        .then((liste) => !annule && setResultats(liste.filter((e) => e.id !== exclure)))
        .catch(() => !annule && setErreur(true))
        .finally(() => !annule && setEnCours(false));
    }, 300);
    return () => {
      annule = true;
      clearTimeout(minuteur);
    };
  }, [recherche, exclure]);

  if (valeur) {
    return (
      <div className="flex items-center gap-3 rounded-2xl border-2 border-primary/40 bg-primary/5 p-3">
        <Check aria-hidden className="size-5 shrink-0 text-primary" />
        <div className="min-w-0 flex-1">
          <p className="truncate font-bold text-ink">{valeur.nom}</p>
          <p className="truncate text-sm font-medium text-muted-foreground">{valeur.detail}</p>
        </div>
        <button
          type="button"
          onClick={() => onChoix(null)}
          className="inline-flex shrink-0 items-center gap-1 rounded-full px-3 py-1.5 text-sm font-bold text-logo-blue hover:bg-mist-soft"
        >
          <X aria-hidden className="size-4" /> Changer
        </button>
      </div>
    );
  }

  return (
    <div>
      <div className="relative">
        <Search
          aria-hidden
          className="pointer-events-none absolute left-3 top-1/2 size-5 -translate-y-1/2 text-muted-foreground"
        />
        <Input
          type="search"
          value={recherche}
          onChange={(e) => setRecherche(e.target.value)}
          placeholder="Nom de ton établissement ou de ta ville"
          aria-label="Rechercher un établissement"
          aria-controls={identifiant}
          aria-invalid={invalide}
          autoComplete="off"
          className="h-12 pl-10 text-base"
        />
        {enCours && (
          <Loader2
            aria-hidden
            className="absolute right-3 top-1/2 size-5 -translate-y-1/2 animate-spin text-muted-foreground"
          />
        )}
      </div>
      <div id={identifiant} aria-live="polite">
        {erreur && (
          <p className="mt-2 text-sm font-semibold text-destructive">
            Recherche impossible pour le moment. Réessaie dans un instant.
          </p>
        )}
        {resultats && resultats.length === 0 && !erreur && (
          <p className="mt-2 text-sm font-medium text-muted-foreground">
            Aucun établissement ne correspond.
          </p>
        )}
        {resultats && resultats.length > 0 && (
          <ul className="mt-2 max-h-64 divide-y overflow-y-auto rounded-2xl border bg-white">
            {resultats.map((e) => (
              <li key={e.id}>
                <button
                  type="button"
                  onClick={() => {
                    onChoix(choixDe(e));
                    setRecherche("");
                  }}
                  className="w-full px-4 py-3 text-left transition hover:bg-mist-soft focus-visible:bg-mist-soft focus-visible:outline-none"
                >
                  <span className="block font-bold text-ink">{e.nom}</span>
                  <span className="block text-sm font-medium text-muted-foreground">
                    {e.iesg} · {e.dre}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
