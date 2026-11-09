import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { Plus } from "lucide-react";
import { useState } from "react";

import { DialogueFormulaire } from "@/components/admin/DialogueFormulaire";
import { ChampsRessource } from "@/components/bibliotheque/ChampsRessource";
import {
  BadgeEtatQuiz as BadgeEtat,
  ETATS_QUIZ as ETATS_LIBELLES,
} from "@/components/quiz/BadgeEtatQuiz";
import { ServiceIndisponible } from "@/components/ServiceIndisponible";
import { Button } from "@/components/ui/button";
import { peut } from "@/lib/admin";
import {
  chargerAxes,
  chargerRessources,
  creerRessource,
  type AxePublic,
  type EtatRessource,
} from "@/lib/api/client";
import { CATEGORIES, entreeVide, tailleLisible } from "@/lib/bibliotheque";
import { dateCourte } from "@/lib/dates";

type Recherche = { etat?: EtatRessource | undefined };
const ETATS = Object.keys(ETATS_LIBELLES) as EtatRessource[];

export const Route = createFileRoute("/_connecte/admin/bibliotheque/")({
  gcTime: 0,
  validateSearch: (search: Record<string, unknown>): Recherche =>
    ETATS.includes(search["etat"] as EtatRessource)
      ? { etat: search["etat"] as EtatRessource }
      : {},
  loaderDeps: ({ search }) => search,
  loader: async ({ deps }) => {
    const [liste, axes] = await Promise.all([
      chargerRessources(deps.etat),
      chargerAxes().catch((): AxePublic[] => []),
    ]);
    return { liste, axes };
  },
  errorComponent: ServiceIndisponible,
  component: Ressources,
});

function Ressources() {
  const { liste, axes } = Route.useLoaderData();
  const { etat } = Route.useSearch();
  const { admin } = Route.useRouteContext();
  const naviguer = useNavigate();
  const [ouvert, setOuvert] = useState(false);
  const [entree, setEntree] = useState(entreeVide);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <nav aria-label="Filtrer par état" className="flex flex-wrap gap-2">
          <Filtre libelle="Toutes" actif={!etat} />
          {ETATS.map((e) => (
            <Filtre key={e} etat={e} libelle={ETATS_LIBELLES[e].libelle} actif={etat === e} />
          ))}
        </nav>
        {peut(admin, "bibliotheque", "creer") && (
          <Button
            className="rounded-full font-bold"
            onClick={() => {
              setEntree(entreeVide);
              setOuvert(true);
            }}
          >
            <Plus className="size-4" /> Nouvelle ressource
          </Button>
        )}
      </div>

      {liste.ressources.length === 0 ? (
        <p className="rounded-3xl bg-white p-8 text-center font-semibold shadow-card">
          Aucune ressource ici pour l'instant.
        </p>
      ) : (
        <ul className="grid gap-3">
          {liste.ressources.map((r) => (
            <li key={r.id}>
              <Link
                to="/admin/bibliotheque/$id"
                params={{ id: r.id }}
                className="flex flex-wrap items-center justify-between gap-3 rounded-2xl bg-white p-4 shadow-card ring-1 ring-transparent hover:ring-logo-blue/30"
              >
                <span>
                  <span className="block font-bold text-ink">{r.titre}</span>
                  <span className="text-sm text-muted-foreground">
                    {CATEGORIES[r.categorie].un}
                    {r.fichier_octets ? ` · ${tailleLisible(r.fichier_octets)}` : " · sans PDF"}
                    {r.etat === "publie" ? ` · ${r.telechargements} téléchargements` : ""} ·
                    modifiée le {dateCourte(r.modifie_le)}
                  </span>
                </span>
                <span className="flex flex-wrap gap-2">
                  {r.contenu_de_test && (
                    <span className="rounded-full bg-sun/30 px-2.5 py-0.5 text-xs font-extrabold">
                      Contenu de test
                    </span>
                  )}
                  <BadgeEtat etat={r.etat} />
                </span>
              </Link>
            </li>
          ))}
        </ul>
      )}

      <DialogueFormulaire
        ouvert={ouvert}
        onOuvert={setOuvert}
        titre="Nouvelle ressource"
        description="Elle reste en brouillon : dépose ensuite son PDF, puis soumets-la."
        bouton="Créer la ressource"
        onEnvoie={async () => {
          const ressource = await creerRessource(entree);
          await naviguer({ to: "/admin/bibliotheque/$id", params: { id: ressource.id } });
        }}
      >
        <ChampsRessource entree={entree} onChange={setEntree} axes={axes} />
      </DialogueFormulaire>
    </div>
  );
}

function Filtre({
  etat,
  libelle,
  actif,
}: {
  etat?: EtatRessource;
  libelle: string;
  actif: boolean;
}) {
  return (
    <Link
      to="/admin/bibliotheque"
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
