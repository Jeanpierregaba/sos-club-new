import { useState } from "react";

import { dateCourte } from "@/lib/admin";
import { chargerContenusInscrit, type EtatContenu } from "@/lib/api/client";
import { ETATS } from "@/lib/articles";

import { Bloc, Chargement, Liste, Pagination, Rafraichissement, Vide } from "./commun";
import { useChargement } from "./useChargement";

const TYPES = [
  { valeur: "", libelle: "Tous" },
  { valeur: "article", libelle: "Articles" },
  { valeur: "actualite", libelle: "Actualités" },
  { valeur: "fiche_club", libelle: "Fiches de club" },
  { valeur: "evenement", libelle: "Événements" },
  { valeur: "commentaire", libelle: "Commentaires" },
  { valeur: "partage", libelle: "Partages" },
  { valeur: "rapport_activite", libelle: "Rapports d'activité" },
  { valeur: "rapport_mensuel", libelle: "Rapports mensuels" },
  { valeur: "bilan_semestriel", libelle: "Bilans semestriels" },
];

// Le libellé « Retiré par toi » s'adresse à l'auteur : vu par l'équipe, c'est l'auteur qui l'a retiré.
const libelleEtat = (etat: string) =>
  etat === "retire" ? "Retiré par l'auteur" : (ETATS[etat as EtatContenu]?.libelle ?? etat);

// Spec 045 : tout ce que la personne a écrit, quel que soit l'état de modération.
export function OngletContenus({ id }: { id: string }) {
  const [type, setType] = useState("");
  const [etat, setEtat] = useState("");
  const [page, setPage] = useState(1);
  const { donnees, erreur, enCours } = useChargement(
    () => chargerContenusInscrit(id, { type: type || undefined, etat: etat || undefined, page }),
    [id, type, etat, page],
  );

  return (
    <Bloc titre="Contenus">
      <div className="flex flex-wrap gap-3">
        <Liste
          libelle="Type"
          valeur={type}
          onChange={(v) => {
            setType(v);
            setPage(1);
          }}
          options={TYPES}
        />
        <Liste
          libelle="État"
          valeur={etat}
          onChange={(v) => {
            setEtat(v);
            setPage(1);
          }}
          options={[
            { valeur: "", libelle: "Tous" },
            ...Object.keys(ETATS).map((e) => ({ valeur: e, libelle: libelleEtat(e) })),
          ]}
        />
      </div>
      {!donnees ? (
        <div className="mt-4">
          <Chargement erreur={erreur} />
        </div>
      ) : (
        <>
          <Rafraichissement erreur={erreur} enCours={enCours}>
            {donnees.contenus.length === 0 ? (
              <div className="mt-4">
                <Vide>Aucun contenu.</Vide>
              </div>
            ) : (
              <ol className="mt-4 divide-y text-sm">
                {donnees.contenus.map((c) => (
                  <li key={c.id} className="flex items-start justify-between gap-4 py-3">
                    <span className="min-w-0">
                      <span className="block font-bold">{c.titre}</span>
                      <span className="block text-muted-foreground">
                        {c.type_libelle} · créé le {dateCourte(c.cree_le)}
                        {c.publie_le && ` · publié le ${dateCourte(c.publie_le)}`}
                      </span>
                    </span>
                    <span
                      className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-extrabold ${ETATS[c.etat as EtatContenu]?.classe ?? "bg-muted"}`}
                    >
                      {libelleEtat(c.etat)}
                    </span>
                  </li>
                ))}
              </ol>
            )}
            <Pagination
              page={donnees.page}
              parPage={donnees.par_page}
              total={donnees.total}
              unite={["contenu", "contenus"]}
              onPage={setPage}
            />
          </Rafraichissement>
        </>
      )}
    </Bloc>
  );
}
