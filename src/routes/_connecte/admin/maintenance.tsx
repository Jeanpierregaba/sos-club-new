import { createFileRoute, redirect, useRouter } from "@tanstack/react-router";
import { AlertTriangle, Loader2, ShieldCheck, Wrench } from "lucide-react";
import { useState } from "react";

import { EnTeteAdmin } from "@/components/admin/EnTeteAdmin";
import { ServiceIndisponible } from "@/components/ServiceIndisponible";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { dateHeure } from "@/lib/admin";
import {
  changerMaintenance,
  chargerMaintenance,
  ErreurApi,
  MESSAGE_INDISPONIBLE,
  type EtatMaintenance,
} from "@/lib/api/client";

export const Route = createFileRoute("/_connecte/admin/maintenance")({
  beforeLoad: ({ context }) => {
    if (!context.admin.super_admin) throw redirect({ to: "/admin" });
  },
  loader: () => chargerMaintenance(),
  gcTime: 0,
  errorComponent: ServiceIndisponible,
  component: Maintenance,
});

function Maintenance() {
  const initial = Route.useLoaderData();
  const router = useRouter();
  const [etat, setEtat] = useState<EtatMaintenance>(initial);
  const [dialogue, setDialogue] = useState<"activer" | "desactiver" | null>(null);
  const [enCours, setEnCours] = useState(false);
  const [erreur, setErreur] = useState<string | null>(null);

  const actif = etat.maintenance_active;

  const basculer = async () => {
    if (!dialogue) return;
    setEnCours(true);
    setErreur(null);
    try {
      const resultat = await changerMaintenance(dialogue === "activer");
      setEtat(resultat);
      setDialogue(null);
      await router.invalidate();
    } catch (e) {
      setErreur(e instanceof ErreurApi ? e.message : MESSAGE_INDISPONIBLE);
    } finally {
      setEnCours(false);
    }
  };

  return (
    <div className="space-y-6">
      <EnTeteAdmin sur="État du site" bleu="Mode" vert="maintenance">
        Ferme temporairement la plateforme pendant une mise à jour ou une intervention sur les
        données.
      </EnTeteAdmin>

      <section
        aria-labelledby="etat-maintenance"
        className="rounded-3xl bg-white p-6 shadow-sm ring-1 ring-border sm:p-8"
      >
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="flex items-start gap-4">
            <span
              className={`inline-flex size-12 shrink-0 items-center justify-center rounded-2xl ${
                actif ? "bg-logo-red/10 text-logo-red" : "bg-primary/10 text-primary"
              }`}
            >
              {actif ? <Wrench className="size-6" /> : <ShieldCheck className="size-6" />}
            </span>
            <div>
              <h2 id="etat-maintenance" className="text-xl text-logo-blue">
                {actif ? "Maintenance active" : "Le site est ouvert"}
              </h2>
              <p className="mt-1 font-medium text-muted-foreground">
                {actif
                  ? `Le site est fermé aux visiteurs depuis le ${dateHeure(etat.active_le)} (UTC). Seuls les super-administrateurs peuvent se connecter et contourner la maintenance.`
                  : "Les visiteurs, élèves et encadreurs accèdent normalement au site."}
              </p>
            </div>
          </div>
          <Button
            onClick={() => setDialogue(actif ? "desactiver" : "activer")}
            variant={actif ? "default" : "destructive"}
            className="btn-fx h-11 rounded-full px-5 font-bold"
          >
            {actif ? "Désactiver la maintenance" : "Activer la maintenance"}
          </Button>
        </div>

        {erreur && (
          <Alert variant="destructive" className="mt-5">
            <AlertTriangle className="size-4" />
            <AlertDescription>{erreur}</AlertDescription>
          </Alert>
        )}

        <div className="mt-6 grid gap-3 rounded-2xl bg-mist-soft p-4 text-sm font-medium text-ink/80 sm:grid-cols-2">
          <p>
            <strong className="text-ink">Pendant la maintenance :</strong> toutes les pages
            affichent la page dédiée, et l'API répond « service indisponible » aux comptes non
            super-administrateurs.
          </p>
          <p>
            <strong className="text-ink">Traçabilité :</strong> l'activation et la désactivation
            sont inscrites au journal d'audit avec ton nom.
          </p>
        </div>
      </section>

      <Dialog open={dialogue !== null} onOpenChange={(ouvert) => !ouvert && setDialogue(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {dialogue === "activer" ? "Activer la maintenance ?" : "Rouvrir le site ?"}
            </DialogTitle>
            <DialogDescription>
              {dialogue === "activer"
                ? "Le site sera fermé à tous les visiteurs, élèves et encadreurs. Les collaborateurs non super-administrateurs seront bloqués eux aussi. Tu pourras le rouvrir depuis cette page."
                : "Le site redeviendra accessible à tous immédiatement."}
            </DialogDescription>
          </DialogHeader>
          <div className="flex justify-end gap-2">
            <Button
              variant="outline"
              onClick={() => setDialogue(null)}
              disabled={enCours}
              className="rounded-full font-bold"
            >
              Annuler
            </Button>
            <Button
              onClick={basculer}
              disabled={enCours}
              variant={dialogue === "activer" ? "destructive" : "default"}
              className="btn-fx rounded-full font-bold"
            >
              {enCours && <Loader2 className="size-4 animate-spin" />}
              {dialogue === "activer" ? "Activer la maintenance" : "Rouvrir le site"}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
