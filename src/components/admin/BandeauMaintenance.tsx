import { useRouter } from "@tanstack/react-router";
import { Loader2, Wrench } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { changerMaintenance, ErreurApi, MESSAGE_INDISPONIBLE } from "@/lib/api/client";

// Bandeau de l'espace admin quand la maintenance est active (spec 047) : désactivation en un geste.
export function BandeauMaintenance() {
  const router = useRouter();
  const [enCours, setEnCours] = useState(false);
  const [erreur, setErreur] = useState<string | null>(null);

  const desactiver = async () => {
    setEnCours(true);
    setErreur(null);
    try {
      await changerMaintenance(false);
      await router.invalidate();
    } catch (e) {
      setErreur(e instanceof ErreurApi ? e.message : MESSAGE_INDISPONIBLE);
    } finally {
      setEnCours(false);
    }
  };

  return (
    <div
      role="status"
      className="flex flex-wrap items-center gap-x-3 gap-y-2 border-b border-sun/60 bg-sun/25 px-4 py-3 text-sm font-semibold text-ink sm:px-6 lg:px-10"
    >
      <Wrench aria-hidden className="size-5 shrink-0 text-logo-red" />
      <span>Le mode maintenance est actif : le site est fermé aux visiteurs.</span>
      {erreur && <span className="text-logo-red">{erreur}</span>}
      <Button
        onClick={desactiver}
        disabled={enCours}
        variant="outline"
        className="ml-auto rounded-full font-bold"
      >
        {enCours && <Loader2 className="size-4 animate-spin" />}
        Désactiver la maintenance
      </Button>
    </div>
  );
}
