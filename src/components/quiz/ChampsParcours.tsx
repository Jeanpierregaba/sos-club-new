import { Champ, CHAMP_ADMIN } from "@/components/admin/DialogueFormulaire";
import type { Parcours } from "@/lib/api/client";
import type { FasciculeChoix, useParcours } from "@/lib/parcours";

const PLACES = Array.from({ length: 12 }, (_, i) => i + 1);

// Le parcours d'un quiz dans la banque (spec 029) : jeux, ou une place du parcours de certification et son
// fascicule.

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
                  Quiz {p} sur 12
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
