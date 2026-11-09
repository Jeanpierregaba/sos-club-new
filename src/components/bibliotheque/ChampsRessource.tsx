import { Champ, CHAMP_ADMIN } from "@/components/admin/DialogueFormulaire";
import type { AxePublic, RessourceEntree } from "@/lib/api/client";
import { CATEGORIES, ORDRE_CATEGORIES } from "@/lib/bibliotheque";

// Les informations d'une ressource (spec 028), à la création comme à la modification.
export function ChampsRessource({
  entree,
  onChange,
  axes,
}: {
  entree: RessourceEntree;
  onChange: (entree: RessourceEntree) => void;
  axes: AxePublic[];
}) {
  const changer = (champs: Partial<RessourceEntree>) => onChange({ ...entree, ...champs });
  return (
    <>
      <Champ libelle="Titre">
        <input
          className={CHAMP_ADMIN}
          value={entree.titre}
          maxLength={150}
          onChange={(e) => changer({ titre: e.target.value })}
        />
      </Champ>
      <Champ libelle="Description courte">
        <textarea
          className={CHAMP_ADMIN}
          rows={3}
          value={entree.description ?? ""}
          maxLength={500}
          onChange={(e) => changer({ description: e.target.value })}
        />
      </Champ>
      <Champ libelle="Catégorie">
        <select
          className={CHAMP_ADMIN}
          value={entree.categorie}
          onChange={(e) => changer({ categorie: e.target.value as RessourceEntree["categorie"] })}
        >
          {ORDRE_CATEGORIES.map((c) => (
            <option key={c} value={c}>
              {CATEGORIES[c].un}
            </option>
          ))}
        </select>
      </Champ>
      {entree.categorie === "magazine" && (
        <Champ libelle="Numéro ou date de parution">
          <input
            className={CHAMP_ADMIN}
            value={entree.parution ?? ""}
            maxLength={60}
            placeholder="N° 12 — octobre 2026"
            onChange={(e) => changer({ parution: e.target.value || null })}
          />
        </Champ>
      )}
      <Champ libelle="Axe (facultatif)">
        <select
          className={CHAMP_ADMIN}
          value={entree.axe_code ?? ""}
          onChange={(e) => changer({ axe_code: e.target.value || null })}
        >
          <option value="">Aucun axe</option>
          {axes.map((a) => (
            <option key={a.code} value={a.code}>
              {a.libelle}
            </option>
          ))}
        </select>
      </Champ>
    </>
  );
}
