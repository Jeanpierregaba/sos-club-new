import { createFileRoute, useRouter } from "@tanstack/react-router";
import { Pencil } from "lucide-react";
import { useState } from "react";

import {
  BadgeActif,
  CHAMP_ADMIN,
  Champ,
  DialogueFormulaire,
} from "@/components/admin/DialogueFormulaire";
import { ServiceIndisponible } from "@/components/ServiceIndisponible";
import { peut } from "@/lib/admin";
import { adminListerBareme, adminModifierBareme, type LigneBaremeAdmin } from "@/lib/api/client";

export const Route = createFileRoute("/_connecte/admin/points/bareme")({
  loader: () => adminListerBareme(),
  gcTime: 0,
  errorComponent: ServiceIndisponible,
  component: Bareme,
});

type Ligne = LigneBaremeAdmin;

// Spec 034 : les actions de l'élève par parcours ; le club de l'élève reçoit la moitié de chaque gain (ADR-0012).
const GROUPES: { titre: [string, string]; garde: (l: Ligne) => boolean; part_club: boolean }[] = [
  {
    titre: ["Élèves —", "certification"],
    garde: (l) => l.beneficiaire === "eleve" && l.parcours === "certification",
    part_club: true,
  },
  {
    titre: ["Élèves —", "jeux, points des quiz"],
    garde: (l) => l.beneficiaire === "eleve" && l.sous_compte === "quiz",
    part_club: true,
  },
  {
    titre: ["Élèves —", "jeux, points des étoiles"],
    garde: (l) => l.beneficiaire === "eleve" && l.sous_compte === "etoiles",
    part_club: true,
  },
  {
    titre: ["Élèves —", "vie du site"],
    garde: (l) => l.beneficiaire === "eleve" && (l.parcours === "vie" || l.parcours === null),
    part_club: true,
  },
  {
    titre: ["Points des", "encadreurs"],
    garde: (l) => l.beneficiaire === "encadreur",
    part_club: false,
  },
  {
    titre: ["Compte collectif du", "club"],
    garde: (l) => l.beneficiaire === "club",
    part_club: false,
  },
];

const demi = (montant: number) => (montant / 2).toLocaleString("fr-FR");

function Bareme() {
  const { admin } = Route.useRouteContext();
  const lignes = Route.useLoaderData();
  const modifiable = peut(admin, "points", "modifier") && admin.perimetre_dre === null;
  const [edition, setEdition] = useState<LigneBaremeAdmin | null>(null);

  return (
    <div className="space-y-8">
      <p className="max-w-3xl text-sm font-medium text-muted-foreground">
        Les montants « proposés » restent à valider par les organisateurs. Une action « pas encore
        utilisée » ne rapporte rien tant que sa fonctionnalité n'est pas livrée. Pour chaque gain
        d'un élève, son Club Santé reçoit la moitié, si l'élève y est affilié et que le club est en
        service.
      </p>
      {GROUPES.map((g) => (
        <section key={g.titre.join(" ")}>
          <h2 className="text-2xl">
            <span className="text-logo-blue">{g.titre[0]}</span>{" "}
            <span className="text-primary">{g.titre[1]}</span>
          </h2>
          <ul className="mt-3 divide-y overflow-hidden rounded-3xl bg-white shadow-sm ring-1 ring-border">
            {lignes.filter(g.garde).map((l) => (
              <li
                key={l.code}
                className={`flex flex-wrap items-center gap-3 px-5 py-4 ${l.actif ? "" : "opacity-60"}`}
              >
                <div className="min-w-0 flex-1">
                  <p className="flex flex-wrap items-center gap-2 font-bold text-ink">
                    {l.libelle} <BadgeActif actif={l.actif} />
                    {l.propose && (
                      <span className="rounded-full bg-sun/30 px-2.5 py-0.5 text-xs font-extrabold text-ink">
                        Proposé
                      </span>
                    )}
                    {!l.en_service && (
                      <span className="rounded-full bg-mist-soft px-2.5 py-0.5 text-xs font-extrabold text-muted-foreground">
                        Pas encore utilisée
                      </span>
                    )}
                  </p>
                  <code className="font-mono text-xs text-muted-foreground">{l.code}</code>
                </div>
                <span className="text-right">
                  <span className="block font-display text-2xl text-logo-blue tabular-nums">
                    +{l.montant}
                  </span>
                  {g.part_club && l.montant > 0 && (
                    <span className="block text-xs font-bold text-primary tabular-nums">
                      club +{demi(l.montant)}
                    </span>
                  )}
                </span>
                {modifiable && (
                  <button
                    type="button"
                    onClick={() => setEdition(l)}
                    aria-label={`Modifier ${l.libelle}`}
                    className="inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-bold ring-1 ring-border transition hover:bg-mist-soft"
                  >
                    <Pencil className="size-3.5" /> Modifier
                  </button>
                )}
              </li>
            ))}
          </ul>
        </section>
      ))}
      {edition && (
        <FormulaireLigne key={edition.code} ligne={edition} fermer={() => setEdition(null)} />
      )}
    </div>
  );
}

function FormulaireLigne({ ligne, fermer }: { ligne: LigneBaremeAdmin; fermer: () => void }) {
  const router = useRouter();
  const [montant, setMontant] = useState(String(ligne.montant));
  const [propose, setPropose] = useState(ligne.propose);
  const [actif, setActif] = useState(ligne.actif);

  return (
    <DialogueFormulaire
      ouvert
      onOuvert={(o) => !o && fermer()}
      titre={ligne.libelle}
      description="Le nouveau montant vaut pour les gains à venir. Les points déjà gagnés ne changent pas."
      bouton="Enregistrer"
      onEnvoie={async () => {
        await adminModifierBareme(ligne.code, {
          version: ligne.version,
          montant: Number(montant),
          propose,
          actif,
        });
        await router.invalidate();
      }}
    >
      <Champ libelle="Montant (0 à 10 000)">
        <input
          type="number"
          required
          min={0}
          max={10000}
          step={1}
          value={montant}
          onChange={(e) => setMontant(e.target.value)}
          className={CHAMP_ADMIN}
        />
      </Champ>
      <label className="flex items-center gap-3 text-sm font-bold">
        <input
          type="checkbox"
          checked={propose}
          onChange={(e) => setPropose(e.target.checked)}
          className="size-5 accent-primary"
        />
        Montant encore à valider par les organisateurs
      </label>
      <label className="flex items-center gap-3 text-sm font-bold">
        <input
          type="checkbox"
          checked={actif}
          onChange={(e) => setActif(e.target.checked)}
          className="size-5 accent-primary"
        />
        Action active (décochée, elle ne rapporte plus rien)
      </label>
    </DialogueFormulaire>
  );
}
