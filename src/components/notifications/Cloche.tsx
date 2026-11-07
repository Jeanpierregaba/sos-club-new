import { useQuery } from "@tanstack/react-query";
import { Link, useRouterState } from "@tanstack/react-router";
import { Bell } from "lucide-react";

import { useMoi } from "@/hooks/use-moi";
import { compterNotifications } from "@/lib/api/client";

export const CLE_NOTIFICATIONS = "notifications";

// La cloche du centre de notifications (spec 023) : pour un élève ou un encadreur connecté, avec le nombre de
// notifications non lues, rechargé à chaque navigation. Pas de temps réel : le PRD l'exclut.
export function Cloche() {
  const { data: moi } = useMoi();
  const chemin = useRouterState({ select: (s) => s.location.pathname });
  const actif = Boolean(moi && moi.role !== "admin");
  const { data } = useQuery({
    // Le compte et la page font partie de la clé : un autre compte ne voit jamais ce compteur.
    queryKey: [CLE_NOTIFICATIONS, moi?.id, chemin],
    queryFn: compterNotifications,
    enabled: actif,
    retry: false,
    staleTime: 30_000,
  });
  if (!actif) return null;
  const nombre = data?.non_lues ?? 0;

  return (
    <Link
      to="/notifications"
      aria-label={
        nombre ? `Notifications : ${nombre} non lue${nombre > 1 ? "s" : ""}` : "Notifications"
      }
      className="relative inline-flex size-10 items-center justify-center rounded-full border text-logo-blue transition hover:bg-mist"
    >
      <Bell className="size-5" />
      {nombre > 0 && (
        <span className="absolute -right-1 -top-1 min-w-5 rounded-full bg-logo-red px-1.5 text-center text-xs font-bold leading-5 text-white">
          {nombre > 9 ? "9+" : nombre}
        </span>
      )}
    </Link>
  );
}
