import { useQuery } from "@tanstack/react-query";

import { chargerMoi } from "@/lib/api/client";

export const CLE_MOI = ["moi"];

// Interrogé depuis le navigateur seulement : les pages publiques s'affichent même si l'API est arrêtée.
export function useMoi() {
  return useQuery({ queryKey: CLE_MOI, queryFn: chargerMoi, retry: false, staleTime: 60_000 });
}
