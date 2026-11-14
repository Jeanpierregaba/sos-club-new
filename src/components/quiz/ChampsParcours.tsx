import { Champ, CHAMP_ADMIN } from "@/components/admin/DialogueFormulaire";
import type { Parcours } from "@/lib/api/client";
import { NIVEAUX_JEUX, type NiveauJeux } from "@/lib/bareme";
import type { FasciculeChoix, useParcours } from "@/lib/parcours";

// Spec 034 : 20 places, en 5 thématiques de 4.
const PLACES = Array.from({ length: 20 }, (_, i) => i + 1);

// Le parcours d'un quiz dans la banque (spec 029) : jeux avec son niveau (spec 034), ou une place du parcours de
// certification et son fascicule.

export function ChampsParcours({
  etat,
  fascicules,
}: {
  etat: ReturnType<typeof useParcours>;
  fascicules: FasciculeChoix[];
}) {
  return (
    <>
      <Champ libelle="Parcours">
        <select
          className={CHAMP_ADMIN}
          value={etat.parcours}
          onChange={(e) => etat.setParcours(e.target.value as Parcours)}
        >
          <option value="jeux">Jeux (quiz santé libres)</option>
          <option value="certification">Certification Génie Imhotep</option>
        </select>
      </Champ>
      {etat.parcours === "jeux" && (
        <Champ libelle="Niveau">
          <select
            className={CHAMP_ADMIN}
            value={etat.niveau}
            onChange={(e) => etat.setNiveau(e.target.value as NiveauJeux)}
          >
            {NIVEAUX_JEUX.map((n) => (
              <option key={n.code} value={n.code}>
                {n.nom} ({n.eleve} points par quiz réussi)
              </option>
            ))}
          </select>
        </Champ>
      )}
      {etat.parcours === "certification" && (
        <>
          <Champ libelle="Place dans le parcours">
            <select
              className={CHAMP_ADMIN}
              value={etat.place}
              onChange={(e) => etat.setPlace(Number(e.target.value))}
            >
              {PLACES.map((p) => (
                <option key={p} value={p}>
                  Quiz {p} sur 20 · thématique {Math.ceil(p / 4)}
                </option>
              ))}
            </select>
          </Champ>
          <Champ libelle="Fascicule à lire avant de jouer">
            <select
              className={CHAMP_ADMIN}
              value={etat.ressource}
              onChange={(e) => etat.setRessource(e.target.value)}
            >
              <option value="">Aucun</option>
              {etat.ressource && !fascicules.some((f) => f.id === etat.ressource) && (
                <option value={etat.ressource}>
                  {etat.ressourceTitre ?? "Fascicule relié"} (plus en ligne)
                </option>
              )}
              {fascicules.map((f) => (
                <option key={f.id} value={f.id}>
                  {f.titre}
                </option>
              ))}
            </select>
          </Champ>
        </>
      )}
    </>
  );
}
