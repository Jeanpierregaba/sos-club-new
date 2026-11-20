import { useState } from "react";

import { dateCourte, dateHeure } from "@/lib/admin";
import { chargerQuizInscrit, type TentativeAdmin } from "@/lib/api/client";

import { Bloc, Chargement, Chiffres, Liste, Pagination, Pastille, Vide } from "./commun";
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

const duree = (secondes: number | null) =>
  secondes == null
    ? "—"
    : secondes < 60
      ? `${secondes} s`
      : `${Math.floor(secondes / 60)} min ${String(secondes % 60).padStart(2, "0")}`;

function Resultat({ t }: { t: TentativeAdmin }) {
  if (t.etat !== "terminee") return <Pastille ton="or">En cours ou abandonnée</Pastille>;
  return t.reussie ? (
    <Pastille ton="vert">Réussie</Pastille>
  ) : (
    <Pastille ton="rouge">Échouée</Pastille>
  );
}

// Spec 045 : quiz validés et toutes les tentatives. Ni les questions ni les réponses ne sont montrées.
export function OngletQuiz({ id }: { id: string }) {
  const [parcours, setParcours] = useState("");
  const [resultat, setResultat] = useState("");
  const [page, setPage] = useState(1);
  const { donnees, erreur } = useChargement(
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
          ]}
        />
        <p className="mt-2 text-xs font-medium text-muted-foreground">
          Tentatives terminées, hors essais.
        </p>
        {valides.length === 0 ? (
          <div className="mt-4">
            <Vide>Aucun quiz validé pour l'instant.</Vide>
          </div>
        ) : (
          <div className="mt-4 overflow-x-auto">
            <table className="w-full min-w-[640px] text-left text-sm">
              <thead className="text-xs font-extrabold uppercase tracking-wider text-muted-foreground">
                <tr>
                  <th className="py-2 pr-3">Quiz</th>
                  <th className="py-2 pr-3">Parcours</th>
                  <th className="py-2 pr-3">Validé le</th>
                  <th className="py-2 pr-3">Meilleur score</th>
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
        {tentatives.tentatives.length === 0 ? (
          <div className="mt-4">
            <Vide>Aucune tentative.</Vide>
          </div>
        ) : (
          <ol className="mt-4 divide-y text-sm">
            {tentatives.tentatives.map((t) => (
              <li key={t.id} className="flex items-start justify-between gap-4 py-3">
                <span className="min-w-0">
                  <span className="flex flex-wrap items-center gap-2 font-bold">
                    {t.quiz_titre}
                    <Resultat t={t} />
                    {t.essai && <Pastille>Essai</Pastille>}
                  </span>
                  <span className="block text-muted-foreground">
                    {repere(t)} · {dateHeure(t.commencee_le)} · durée {duree(t.duree_s)}
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
      </Bloc>
    </div>
  );
}
