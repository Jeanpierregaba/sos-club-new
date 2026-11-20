import { Link } from "@tanstack/react-router";
import { useState } from "react";

import { dateHeure } from "@/lib/admin";
import { chargerPointsInscrit } from "@/lib/api/client";

import {
  Bloc,
  Chargement,
  Chiffres,
  Liste,
  Pagination,
  Rafraichissement,
  Pastille,
  Vide,
} from "./commun";
import { useChargement } from "./useChargement";

// Spec 045 : tout le registre des points d'un inscrit, 50 lignes par page.
export function OngletPoints({ id, peutCorriger }: { id: string; peutCorriger: boolean }) {
  const [semestre, setSemestre] = useState("");
  const [page, setPage] = useState(1);
  const { donnees, erreur, enCours } = useChargement(
    () => chargerPointsInscrit(id, { semestre_id: semestre || undefined, page }),
    [id, semestre, page],
  );

  return (
    <Bloc
      titre="Registre des points"
      actions={
        peutCorriger && (
          <Link
            to="/admin/points/registre"
            search={{ utilisateur_id: id }}
            className="rounded-full px-4 py-2 text-sm font-bold text-logo-blue ring-1 ring-border hover:ring-night/30"
          >
            Corriger dans le registre
          </Link>
        )
      }
    >
      {!donnees ? (
        <Chargement erreur={erreur} />
      ) : (
        <>
          <Chiffres
            chiffres={[
              [
                donnees.totaux.semestre ? `Semestre · ${donnees.totaux.semestre}` : "Semestre",
                donnees.totaux.points_semestre,
              ],
              ["Total", donnees.totaux.total],
            ]}
          />
          <div className="mt-5">
            <Liste
              libelle="Période"
              valeur={semestre}
              onChange={(v) => {
                setSemestre(v);
                setPage(1);
              }}
              options={[
                { valeur: "", libelle: "Tout l'historique" },
                ...donnees.semestres.map((s) => ({ valeur: s.id, libelle: s.libelle })),
              ]}
            />
          </div>
          <Rafraichissement erreur={erreur} enCours={enCours}>
            {donnees.registre.lignes.length === 0 ? (
              <div className="mt-4">
                <Vide>Aucune ligne de points sur cette période.</Vide>
              </div>
            ) : (
              <ol className="mt-4 divide-y text-sm">
                {donnees.registre.lignes.map((ligne) => (
                  <li key={ligne.id} className="flex items-start justify-between gap-4 py-3">
                    <span className="min-w-0">
                      <span className="flex flex-wrap items-center gap-2 font-bold">
                        {ligne.action_libelle}
                        {ligne.est_correction && <Pastille ton="or">Correction</Pastille>}
                        {ligne.est_annulation && <Pastille ton="rouge">Annulation</Pastille>}
                        {ligne.annulee && <Pastille>Annulée</Pastille>}
                      </span>
                      <span className="block text-muted-foreground">
                        {dateHeure(ligne.cree_le)} · {ligne.semestre ?? "hors semestre"}
                        {ligne.club &&
                          ` · ${ligne.club.nom}${ligne.points_club != null ? ` (+${ligne.points_club} au club)` : ""}`}
                      </span>
                      {ligne.motif && (
                        <span className="block text-muted-foreground">
                          Motif : {ligne.motif}
                          {ligne.valide_par && ` · par ${ligne.valide_par.nom}`}
                        </span>
                      )}
                    </span>
                    <span
                      className={`shrink-0 font-extrabold tabular-nums ${ligne.montant < 0 ? "text-logo-red" : "text-primary"} ${ligne.annulee ? "line-through opacity-60" : ""}`}
                    >
                      {ligne.montant > 0 ? `+${ligne.montant}` : ligne.montant}
                    </span>
                  </li>
                ))}
              </ol>
            )}
            <Pagination
              page={donnees.registre.page}
              parPage={donnees.registre.par_page}
              total={donnees.registre.total}
              unite={["ligne", "lignes"]}
              onPage={setPage}
            />
          </Rafraichissement>
        </>
      )}
    </Bloc>
  );
}
