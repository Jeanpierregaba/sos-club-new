import { BadgeCheck, Download, ImageDown, ShieldAlert, TriangleAlert } from "lucide-react";

import { Button } from "@/components/ui/button";
import { URL_CARTE_PDF, URL_CARTE_PNG, type MaCarte } from "@/lib/api/client";
import { CAUSES_TITULAIRE, ROLES_CARTE, TYPES_CARTE } from "@/lib/cartes";
import { dateCourte } from "@/lib/dates";

// « Ma carte » (spec 040) : la carte valide s'affiche telle qu'elle se télécharge (l'image produite par l'API, QR
// compris) ; une carte non valide montre ses informations, sa marche à suivre, et ne se télécharge pas.
export function ApercuCarte({ carte }: { carte: MaCarte }) {
  return (
    <section aria-label={TYPES_CARTE[carte.type]} className="space-y-6">
      <p
        role="status"
        className={`inline-flex items-center gap-2 rounded-full px-4 py-1.5 text-sm font-extrabold ${
          carte.valide ? "bg-primary/15 text-primary" : "bg-logo-red/10 text-logo-red"
        }`}
      >
        {carte.valide ? (
          <BadgeCheck aria-hidden className="size-4" />
        ) : (
          <ShieldAlert aria-hidden className="size-4" />
        )}
        {carte.valide ? "Valide" : "Non valide"}
      </p>

      {carte.valide ? (
        <>
          <img
            src={URL_CARTE_PNG}
            width={1012}
            height={638}
            alt={`${TYPES_CARTE[carte.type]} n° ${carte.numero} de ${carte.prenom} ${carte.nom}`}
            className="w-full max-w-xl rounded-2xl shadow-card ring-1 ring-border"
          />
          <div className="flex flex-col gap-3 sm:flex-row">
            <Button asChild className="btn-fx h-11 rounded-full font-bold">
              <a href={URL_CARTE_PDF} download>
                <Download className="size-4" /> Télécharger en PDF
              </a>
            </Button>
            <Button asChild variant="outline" className="h-11 rounded-full font-bold">
              <a href={URL_CARTE_PNG} download>
                <ImageDown className="size-4" /> Télécharger en image
              </a>
            </Button>
          </div>
          <p className="flex max-w-xl gap-2 rounded-2xl bg-sun/25 p-4 text-sm font-semibold text-ink ring-1 ring-sun">
            <TriangleAlert aria-hidden className="mt-0.5 size-4 shrink-0" />
            Ta carte porte ton nom : garde-la pour toi et ne la publie pas sur les réseaux sociaux.
            Le QR code ne montre que son statut, son numéro et ton club.
          </p>
        </>
      ) : (
        <div className="max-w-xl rounded-3xl bg-white p-6 shadow-card ring-1 ring-logo-red/30">
          {carte.cause && <p className="font-semibold text-ink">{CAUSES_TITULAIRE[carte.cause]}</p>}
          <dl className="mt-5 grid gap-3 sm:grid-cols-2">
            <Info terme="Titulaire" valeur={`${carte.prenom} ${carte.nom}`} />
            <Info terme="Rôle" valeur={ROLES_CARTE[carte.role]} />
            <Info terme="Numéro" valeur={carte.numero} />
            <Info terme="Club" valeur={carte.club ?? "Non affilié"} />
          </dl>
        </div>
      )}

      <dl className="grid max-w-xl gap-3 text-sm sm:grid-cols-2">
        {carte.valide && (
          <>
            <Info terme="Rôle" valeur={ROLES_CARTE[carte.role]} />
            <Info terme="Club" valeur={carte.club ?? "Non affilié"} />
          </>
        )}
        <Info terme="Établissement" valeur={carte.etablissement ?? "—"} />
        <Info terme="Délivrée le" valeur={dateCourte(carte.delivree_le)} />
      </dl>
    </section>
  );
}

function Info({ terme, valeur }: { terme: string; valeur: string }) {
  return (
    <div>
      <dt className="text-xs font-bold uppercase tracking-wide text-muted-foreground">{terme}</dt>
      <dd className="font-bold text-ink">{valeur}</dd>
    </div>
  );
}
