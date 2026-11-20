import { useState } from "react";

import { CHAMP_ADMIN, Champ, DialogueFormulaire } from "@/components/admin/DialogueFormulaire";
import { Textarea } from "@/components/ui/textarea";
import type { InscritDetail, ModificationInscrit } from "@/lib/api/client";
import { CLASSES } from "@/lib/classes";
import { FONCTIONS } from "@/lib/fonctions";
import { MOTIF_MIN, entreeDe, valeursDe, type Valeurs } from "@/lib/modification-inscrit";

export function DialogueModification({
  inscrit,
  fermer,
  envoyer,
}: {
  inscrit: InscritDetail;
  fermer: () => void;
  envoyer: (entree: ModificationInscrit) => Promise<unknown>;
}) {
  const [valeurs, setValeurs] = useState(() => valeursDe(inscrit));
  const [motif, setMotif] = useState("");
  const encadreur = Boolean(inscrit.encadreur);
  const changer = (champ: keyof Valeurs) => (e: { target: { value: string } }) =>
    setValeurs((v) => ({ ...v, [champ]: e.target.value }));
  const entree = entreeDe(inscrit, valeurs, motif);
  const rienAChanger = Object.keys(entree).length === 2;

  return (
    <DialogueFormulaire
      ouvert
      onOuvert={(o) => !o && fermer()}
      titre="Modifier l'inscrit"
      description="Les règles de l'inscription s'appliquent. Le motif et la liste des champs changés sont inscrits au journal."
      bouton="Enregistrer"
      desactive={rienAChanger}
      onEnvoie={() => envoyer(entree)}
    >
      <div className="grid gap-4 sm:grid-cols-2">
        <Champ libelle="Prénom">
          <input
            required
            maxLength={100}
            value={valeurs.prenom}
            onChange={changer("prenom")}
            className={CHAMP_ADMIN}
          />
        </Champ>
        <Champ libelle="Nom">
          <input
            required
            maxLength={100}
            value={valeurs.nom}
            onChange={changer("nom")}
            className={CHAMP_ADMIN}
          />
        </Champ>
        <Champ libelle={encadreur ? "E-mail" : "E-mail (facultatif)"}>
          <input
            type="email"
            required={encadreur}
            maxLength={254}
            value={valeurs.email}
            onChange={changer("email")}
            className={CHAMP_ADMIN}
          />
        </Champ>
        <Champ libelle={encadreur ? "Téléphone" : "Téléphone (facultatif)"}>
          <input
            type="tel"
            required={encadreur}
            maxLength={30}
            value={valeurs.telephone}
            onChange={changer("telephone")}
            className={CHAMP_ADMIN}
          />
        </Champ>
        {inscrit.eleve && (
          <Champ libelle="Classe">
            <select
              required
              value={valeurs.classe}
              onChange={changer("classe")}
              className={CHAMP_ADMIN}
            >
              {CLASSES.map((c) => (
                <option key={c.valeur} value={c.valeur}>
                  {c.libelle}
                </option>
              ))}
            </select>
          </Champ>
        )}
        {inscrit.encadreur && (
          <>
            <Champ libelle="Fonction">
              <select
                required
                value={valeurs.fonction}
                onChange={changer("fonction")}
                className={CHAMP_ADMIN}
              >
                {FONCTIONS.map((f) => (
                  <option key={f.valeur} value={f.valeur}>
                    {f.libelle}
                  </option>
                ))}
              </select>
            </Champ>
            {valeurs.fonction === "autre" && (
              <Champ libelle="Précise la fonction">
                <input
                  required
                  maxLength={100}
                  value={valeurs.fonction_precision}
                  onChange={changer("fonction_precision")}
                  className={CHAMP_ADMIN}
                />
              </Champ>
            )}
            <Champ libelle="Discipline (facultatif)">
              <input
                maxLength={100}
                value={valeurs.discipline}
                onChange={changer("discipline")}
                className={CHAMP_ADMIN}
              />
            </Champ>
            <Champ libelle="Commune">
              <input
                required
                maxLength={100}
                value={valeurs.commune}
                onChange={changer("commune")}
                className={CHAMP_ADMIN}
              />
            </Champ>
          </>
        )}
      </div>
      <Champ libelle="Motif (inscrit au journal)">
        <Textarea
          required
          value={motif}
          onChange={(e) => setMotif(e.target.value)}
          minLength={MOTIF_MIN}
          maxLength={500}
          rows={3}
          className="font-medium"
        />
      </Champ>
    </DialogueFormulaire>
  );
}
