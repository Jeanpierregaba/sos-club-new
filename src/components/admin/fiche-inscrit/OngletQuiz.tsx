import { useState } from "react";

import { dateCourte, dateHeure, dureeLisible } from "@/lib/admin";
import { chargerQuizInscrit, type TentativeAdmin } from "@/lib/api/client";

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
import { DetailTentative } from "./DetailTentative";
import { useChargement } from "./useChargement";

const NIVEAUX: Record<string, string> = {
  debutant: "Débutant",
  intermediaire: "Intermédiaire",
  avance: "Avancé",
  expert: "Expert",
};

// Le parcours d'un quiz : niveau des Jeux ou place de la certification.
const repere = (q: { parcours: string; place: number | null; niveau: string | null }) =>
  q.parcours === "certification"
    ? `Certification${q.place ? ` · place ${q.place}` : ""}`
    : `Jeux${q.niveau ? ` · ${NIVEAUX[q.niveau] ?? q.niveau}` : ""}`;

function Resultat({ t }: { t: TentativeAdmin }) {
  if (t.etat !== "terminee") return <Pastille ton="or">En cours</Pastille>;
  return t.reussie ? (
    <Pastille ton="vert">Réussie</Pastille>
  ) : (
    <Pastille ton="rouge">Échouée</Pastille>
  );
}

// Spec 045 : quiz validés et toutes les tentatives. Spec 046 : temps de jeu, moyenne des autres joueurs et
// détail d'une tentative question par question.
export function OngletQuiz({ id }: { id: string }) {
  const [ouverte, setOuverte] = useState<string | null>(null);
  const [parcours, setParcours] = useState("");
  const [resultat, setResultat] = useState("");
  const [page, setPage] = useState(1);
  const { donnees, erreur, enCours } = useChargement(
    () =>
      chargerQuizInscrit(id, {
        parcours: parcours || undefined,
        resultat: resultat || undefined,
        page,
      }),
    [id, parcours, resultat, page],
  );

  if (!donnees)
    return (
      <Bloc titre="Quiz">
        <Chargement erreur={erreur} />
      </Bloc>
    );

  const { resume, valides, tentatives } = donnees;
  return (
    <div className="space-y-6">
      <Bloc titre="Quiz validés">
        <Chiffres
          chiffres={[
            ["Quiz validés", resume.quiz_valides],
            ["Tentatives", resume.tentatives],
            ["Échecs", resume.echecs],
            ["Points des quiz", resume.points],
            ["Temps de jeu", dureeLisible(resume.temps_total_s)],
            ["Moyenne par tentative", dureeLisible(resume.temps_moyen_s)],
          ]}
        />
        <p className="mt-2 text-xs font-medium text-muted-foreground">
          Tentatives terminées, hors essais. Les points sont ceux du gain initial : une correction
          ultérieure apparaît dans l'onglet Points. Le temps de jeu va du début d'une partie à la
          dernière action du joueur ; la moyenne compare aux réussites des autres joueurs (5 au
          moins).
        </p>
        {valides.length === 0 ? (
          <div className="mt-4">
            <Vide>Aucun quiz validé pour l'instant.</Vide>
          </div>
        ) : (
          <div className="mt-4 overflow-x-auto">
            <table className="w-full min-w-[760px] text-left text-sm">
              <thead className="text-xs font-extrabold uppercase tracking-wider text-muted-foreground">
                <tr>
                  <th className="py-2 pr-3">Quiz</th>
                  <th className="py-2 pr-3">Parcours</th>
                  <th className="py-2 pr-3">Validé le</th>
                  <th className="py-2 pr-3">Meilleur score</th>
                  <th className="py-2 pr-3">Temps de réussite</th>
                  <th className="py-2 text-right">Points</th>
                </tr>
              </thead>
              <tbody>
                {valides.map((q) => (
                  <tr key={q.quiz_id} className="border-t">
                    <td className="py-2.5 pr-3">
                      <span className="font-bold">{q.titre}</span>
                      <span className="block text-xs text-muted-foreground">{q.axe}</span>
                    </td>
                    <td className="py-2.5 pr-3">{repere(q)}</td>
                    <td className="py-2.5 pr-3">{dateCourte(q.premiere_reussite)}</td>
                    <td className="py-2.5 pr-3 tabular-nums">
                      {q.meilleur_score} / {q.nb_questions}
                      {q.reussites > 1 && (
                        <span className="text-xs text-muted-foreground">
                          {" "}
                          · {q.reussites} réussites
                        </span>
                      )}
                    </td>
                    <td className="py-2.5 pr-3 tabular-nums">
                      <span className="flex flex-wrap items-center gap-2">
                        {dureeLisible(q.temps_premiere_reussite_s)}
                        {q.tres_rapide && <Pastille ton="rouge">Très rapide</Pastille>}
                      </span>
                      <span className="block text-xs text-muted-foreground">
                        {q.moyenne_nationale_s != null
                          ? `Moyenne : ${dureeLisible(q.moyenne_nationale_s)} (${q.reussites_nationales} réussites)`
                          : "Moyenne : trop peu de réussites"}
                      </span>
                    </td>
                    <td className="py-2.5 text-right font-extrabold tabular-nums text-primary">
                      +{q.points}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Bloc>

      <Bloc titre="Toutes les tentatives">
        <div className="flex flex-wrap gap-3">
          <Liste
            libelle="Parcours"
            valeur={parcours}
            onChange={(v) => {
              setParcours(v);
              setPage(1);
            }}
            options={[
              { valeur: "", libelle: "Tous" },
              { valeur: "jeux", libelle: "Jeux" },
              { valeur: "certification", libelle: "Certification" },
            ]}
          />
          <Liste
            libelle="Résultat"
            valeur={resultat}
            onChange={(v) => {
              setResultat(v);
              setPage(1);
            }}
            options={[
              { valeur: "", libelle: "Toutes" },
              { valeur: "reussies", libelle: "Réussies" },
              { valeur: "echouees", libelle: "Échouées" },
            ]}
          />
        </div>
        <Rafraichissement erreur={erreur} enCours={enCours}>
          {tentatives.tentatives.length === 0 ? (
            <div className="mt-4">
              <Vide>Aucune tentative.</Vide>
            </div>
          ) : (
            <ol className="mt-4 divide-y text-sm">
              {tentatives.tentatives.map((t) => (
                <li key={t.id}>
                  <button
                    type="button"
                    onClick={() => setOuverte(t.id)}
                    className="flex w-full items-start justify-between gap-4 py-3 text-left hover:bg-mist-soft/60"
                  >
                    <span className="min-w-0">
                      <span className="flex flex-wrap items-center gap-2 font-bold">
                        {t.quiz_titre}
                        <Resultat t={t} />
                        {t.abandonnee && <Pastille ton="or">Abandonnée</Pastille>}
                        {t.essai && <Pastille>Essai</Pastille>}
                      </span>
                      <span className="block text-muted-foreground">
                        {repere(t)} · {dateHeure(t.commencee_le)} · temps de jeu{" "}
                        {dureeLisible(t.duree_s)}
                      </span>
                    </span>
                    <span className="shrink-0 text-right tabular-nums">
                      <span className="block font-bold">
                        {t.score ?? "—"} / {t.nb_questions}
                      </span>
                      {t.points != null && (
                        <span className="block font-extrabold text-primary">+{t.points}</span>
                      )}
                    </span>
                  </button>
                </li>
              ))}
            </ol>
          )}
          <Pagination
            page={tentatives.page}
            parPage={tentatives.par_page}
            total={tentatives.total}
            unite={["tentative", "tentatives"]}
            onPage={setPage}
          />
        </Rafraichissement>
        {ouverte && (
          <DetailTentative id={id} tentativeId={ouverte} fermer={() => setOuverte(null)} />
        )}
      </Bloc>
    </div>
  );
}
