import { createFileRoute, Link, useRouter } from "@tanstack/react-router";
import { RefreshCw, ShieldX } from "lucide-react";
import { useState } from "react";

import { DialogueFormulaire } from "@/components/admin/DialogueFormulaire";
import { DialogueMotif } from "@/components/admin/DialogueMotif";
import { ServiceIndisponible } from "@/components/ServiceIndisponible";
import { Button } from "@/components/ui/button";
import { peut } from "@/lib/admin";
import {
  chargerCertificats,
  reemettreCertificat,
  revoquerCertificat,
  type CertificatGestion,
  type EtatCertificat,
} from "@/lib/api/client";
import { ETATS_CERTIFICAT } from "@/lib/certification";
import { dateCourte } from "@/lib/dates";

type Recherche = { etat?: EtatCertificat };
const ETATS = Object.keys(ETATS_CERTIFICAT) as EtatCertificat[];

export const Route = createFileRoute("/_connecte/admin/certification/")({
  gcTime: 0,
  validateSearch: (search: Record<string, unknown>): Recherche =>
    ETATS.includes(search["etat"] as EtatCertificat)
      ? { etat: search["etat"] as EtatCertificat }
      : {},
  loaderDeps: ({ search }) => search,
  loader: ({ deps }) => chargerCertificats(deps.etat),
  errorComponent: ServiceIndisponible,
  component: Certificats,
});

function Certificats() {
  const { certificats } = Route.useLoaderData();
  const { etat } = Route.useSearch();
  const { admin } = Route.useRouteContext();
  const router = useRouter();
  // Révoquer et réémettre : droit sensible de dépublier un quiz (l'API exige aussi la double authentification).
  const decideur = peut(admin, "quiz", "depublier");
  const [cible, setCible] = useState<{
    action: "revoquer" | "reemettre";
    c: CertificatGestion;
  } | null>(null);

  return (
    <div className="space-y-4">
      <nav aria-label="Filtrer par état" className="flex flex-wrap gap-2">
        <Filtre libelle="Tous" actif={!etat} />
        {ETATS.map((e) => (
          <Filtre key={e} etat={e} libelle={ETATS_CERTIFICAT[e].libelle} actif={etat === e} />
        ))}
      </nav>

      {certificats.length === 0 ? (
        <p className="rounded-3xl bg-white p-8 text-center font-semibold shadow-card">
          Aucun certificat ici pour l'instant.
        </p>
      ) : (
        <ul className="grid gap-3">
          {certificats.map((c) => (
            <li
              key={c.id}
              className="flex flex-wrap items-center justify-between gap-3 rounded-2xl bg-white p-4 shadow-card"
            >
              <div className="min-w-0">
                <p className="flex flex-wrap items-center gap-2">
                  <span className="font-mono font-bold text-ink">{c.numero}</span>
                  <span
                    className={`rounded-full px-2.5 py-0.5 text-xs font-bold ${ETATS_CERTIFICAT[c.etat].classe}`}
                  >
                    {ETATS_CERTIFICAT[c.etat].libelle}
                  </span>
                </p>
                <p className="font-semibold text-ink">
                  {c.titulaire}{" "}
                  <span className="text-sm font-normal text-muted-foreground">
                    · {c.role === "eleve" ? "élève" : "encadreur"}
                    {c.club ? ` · ${c.club}` : ""} · délivré le {dateCourte(c.delivre_le)}
                  </span>
                </p>
                {c.remplace_numero && (
                  <p className="text-sm text-muted-foreground">
                    Remplace le n° {c.remplace_numero}
                  </p>
                )}
                {c.motif && <p className="text-sm text-logo-red">Motif : {c.motif}</p>}
              </div>
              <div className="flex flex-wrap gap-2">
                <Link
                  to="/certificats/$numero"
                  params={{ numero: c.numero }}
                  className="inline-flex h-9 items-center rounded-full px-3 text-sm font-bold text-logo-blue ring-1 ring-border hover:bg-mist"
                >
                  Vérification publique
                </Link>
                {decideur && c.etat !== "remplace" && (
                  <Button
                    variant="outline"
                    size="sm"
                    className="rounded-full font-bold"
                    onClick={() => setCible({ action: "reemettre", c })}
                  >
                    <RefreshCw className="size-4" /> Réémettre
                  </Button>
                )}
                {decideur && c.etat === "valide" && (
                  <Button
                    variant="outline"
                    size="sm"
                    className="rounded-full font-bold text-logo-red"
                    onClick={() => setCible({ action: "revoquer", c })}
                  >
                    <ShieldX className="size-4" /> Révoquer
                  </Button>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}

      <DialogueMotif
        ouvert={cible?.action === "revoquer"}
        onOuvert={(o) => !o && setCible(null)}
        titre={`Révoquer le certificat ${cible?.c.numero ?? ""}`}
        description="La vérification publique affichera « révoqué », le titulaire ne pourra plus le télécharger, et les points du certificat lui seront retirés. Il est prévenu avec ton motif."
        bouton="Révoquer"
        danger
        onConfirme={async (motif) => {
          if (cible) await revoquerCertificat(cible.c.id, motif);
          await router.invalidate();
        }}
      />
      <DialogueFormulaire
        ouvert={cible?.action === "reemettre"}
        onOuvert={(o) => !o && setCible(null)}
        titre={`Réémettre le certificat ${cible?.c.numero ?? ""}`}
        description="Un nouveau numéro remplace l'ancien, avec le prénom et le nom actuels du compte. Aucun point n'est ajouté ; un certificat révoqué est rétabli sans ses points."
        bouton="Réémettre"
        onEnvoie={async () => {
          if (cible) await reemettreCertificat(cible.c.id);
          await router.invalidate();
        }}
      />
    </div>
  );
}

function Filtre({
  etat,
  libelle,
  actif,
}: {
  etat?: EtatCertificat;
  libelle: string;
  actif: boolean;
}) {
  return (
    <Link
      to="/admin/certification"
      search={etat ? { etat } : {}}
      aria-current={actif ? "page" : undefined}
      className={`rounded-full px-3 py-1.5 text-sm font-semibold ring-1 transition ${
        actif ? "bg-night text-white ring-night" : "bg-white ring-border"
      }`}
    >
      {libelle}
    </Link>
  );
}
