import { Loader2 } from "lucide-react";
import { useEffect, useState } from "react";

import { VerificationCarte } from "@/components/cartes/VerificationCarte";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { m } from "@/paraglide/messages.js";
import {
  ErreurApi,
  MESSAGE_INDISPONIBLE,
  verifierCarte,
  type VerificationCarte as Verification,
} from "@/lib/api/client";

// La vérification d'une carte par son code (spec 040), faite par le navigateur : la limite par adresse IP de l'API
// doit voir l'adresse du visiteur, pas celle du serveur du site.
type Etat =
  | { phase: "chargement" }
  | { phase: "fait"; resultat: Verification | null }
  | { phase: "erreur"; message: string };

export function Verifier({ code }: { code: string }) {
  const [etat, setEtat] = useState<Etat>({ phase: "chargement" });

  useEffect(() => {
    let actif = true;
    setEtat({ phase: "chargement" });
    verifierCarte(code)
      .then((resultat) => actif && setEtat({ phase: "fait", resultat }))
      .catch((e: unknown) => {
        if (!actif) return;
        if (e instanceof ErreurApi && e.statut === 404) setEtat({ phase: "fait", resultat: null });
        else
          setEtat({
            phase: "erreur",
            message: e instanceof ErreurApi && e.statut === 429 ? e.message : MESSAGE_INDISPONIBLE,
          });
      });
    return () => {
      actif = false;
    };
  }, [code]);

  if (etat.phase === "chargement")
    return (
      <p className="flex items-center gap-2 text-muted-foreground" role="status">
        <Loader2 aria-hidden className="size-5 animate-spin" /> {m.carte_en_cours()}
      </p>
    );
  if (etat.phase === "erreur")
    return (
      <Alert variant="destructive">
        <AlertDescription>{etat.message}</AlertDescription>
      </Alert>
    );
  return <VerificationCarte resultat={etat.resultat} />;
}
