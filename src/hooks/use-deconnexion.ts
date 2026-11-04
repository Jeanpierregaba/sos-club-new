import { useQueryClient } from "@tanstack/react-query";
import { useRouter } from "@tanstack/react-router";
import { useState } from "react";

import { CLE_MOI } from "@/hooks/use-moi";
import { deconnecter, ErreurApi, MESSAGE_INDISPONIBLE } from "@/lib/api/client";

export function useDeconnexion() {
  const queryClient = useQueryClient();
  const router = useRouter();
  const [erreur, setErreur] = useState<string | null>(null);
  const [enCours, setEnCours] = useState(false);

  const seDeconnecter = async () => {
    setErreur(null);
    setEnCours(true);
    try {
      await deconnecter();
      queryClient.setQueryData(CLE_MOI, null);
      await router.navigate({ to: "/", replace: true });
    } catch (e) {
      setErreur(e instanceof ErreurApi ? e.message : MESSAGE_INDISPONIBLE);
      setEnCours(false);
    }
  };
  return { seDeconnecter, erreur, enCours };
}
