import { useQueryClient } from "@tanstack/react-query";
import { createFileRoute, Link, redirect, useRouter } from "@tanstack/react-router";
import { ArrowLeft, Bell, CheckCheck } from "lucide-react";
import { useState } from "react";

import { CLE_NOTIFICATIONS } from "@/components/notifications/Cloche";
import { ServiceIndisponible } from "@/components/ServiceIndisponible";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
  chargerNotifications,
  ErreurApi,
  marquerNotificationLue,
  marquerToutesLues,
  MESSAGE_INDISPONIBLE,
  type NotificationSortie,
} from "@/lib/api/client";
import { dateCourte } from "@/lib/dates";

export const Route = createFileRoute("/_connecte/notifications")({
  gcTime: 0,
  beforeLoad: ({ context }) => {
    if (context.moi.role === "admin") throw redirect({ to: "/admin" });
  },
  loader: () => chargerNotifications(),
  head: () => ({
    meta: [
      { title: "Mes notifications — Club Santé SOS Docteur TV" },
      { name: "robots", content: "noindex" },
    ],
  }),
  errorComponent: ServiceIndisponible,
  component: MesNotifications,
});

function MesNotifications() {
  const { notifications, non_lues } = Route.useLoaderData();
  const router = useRouter();
  const queryClient = useQueryClient();
  const [erreur, setErreur] = useState<string | null>(null);

  async function agir(action: () => Promise<unknown>) {
    setErreur(null);
    try {
      await action();
      await queryClient.invalidateQueries({ queryKey: [CLE_NOTIFICATIONS] });
      await router.invalidate();
    } catch (e) {
      setErreur(e instanceof ErreurApi ? e.message : MESSAGE_INDISPONIBLE);
    }
  }

  return (
    <main className="min-h-screen bg-carnet px-4 py-10 sm:px-6">
      <div className="mx-auto max-w-3xl">
        <Link
          to="/mon-espace"
          className="inline-flex items-center gap-2 text-sm font-bold text-logo-blue hover:underline"
        >
          <ArrowLeft className="size-4" /> Mon espace
        </Link>
        <div className="mt-4 flex flex-wrap items-end justify-between gap-4">
          <h1 className="text-4xl leading-tight md:text-5xl">
            <span className="text-logo-blue">Mes</span>{" "}
            <span className="text-primary">notifications</span>
          </h1>
          {non_lues > 0 && (
            <Button
              variant="outline"
              className="h-11 rounded-full px-5 font-bold"
              onClick={() => agir(marquerToutesLues)}
            >
              <CheckCheck className="size-4" /> Tout marquer comme lu
            </Button>
          )}
        </div>

        {erreur && (
          <Alert variant="destructive" className="mt-6">
            <AlertDescription>{erreur}</AlertDescription>
          </Alert>
        )}

        {notifications.length === 0 ? (
          <div className="mt-8 rounded-3xl bg-card p-8 text-center shadow-card">
            <Bell className="mx-auto size-10 text-logo-blue/40" />
            <p className="mt-3 font-semibold">Aucune notification pour l'instant.</p>
            <p className="text-sm text-muted-foreground">
              Les décisions sur tes articles arriveront ici.
            </p>
          </div>
        ) : (
          <ul className="mt-8 space-y-3">
            {notifications.map((n) => (
              <Ligne
                key={n.id}
                notification={n}
                onLue={() => agir(() => marquerNotificationLue(n.id))}
                onVoir={() =>
                  agir(async () => {
                    if (!n.lue) await marquerNotificationLue(n.id);
                    // Le lien vient de l'API : toujours un chemin du site.
                    if (n.lien?.startsWith("/")) await router.navigate({ to: n.lien });
                  })
                }
              />
            ))}
          </ul>
        )}
      </div>
    </main>
  );
}

function Ligne({
  notification: n,
  onLue,
  onVoir,
}: {
  notification: NotificationSortie;
  onLue: () => void;
  onVoir: () => void;
}) {
  return (
    <li
      className={`rounded-3xl bg-card p-5 shadow-card ${n.lue ? "opacity-75" : "ring-2 ring-primary/30"}`}
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <p className="font-bold text-ink">
            {!n.lue && <span className="sr-only">Non lue : </span>}
            {n.titre}
          </p>
          {n.message && <p className="mt-1 whitespace-pre-line text-sm text-ink/80">{n.message}</p>}
          <p className="mt-2 text-xs text-muted-foreground">{dateCourte(n.cree_le)}</p>
        </div>
        <div className="flex gap-2">
          {n.lien && (
            <Button className="rounded-full font-bold" onClick={onVoir}>
              Voir
            </Button>
          )}
          {!n.lue && (
            <Button variant="ghost" className="rounded-full font-bold" onClick={onLue}>
              Marquer comme lue
            </Button>
          )}
        </div>
      </div>
    </li>
  );
}
