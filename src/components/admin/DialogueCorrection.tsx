import { useEffect, useRef, useState } from "react";

import { CHAMP_ADMIN, Champ, DialogueFormulaire } from "@/components/admin/DialogueFormulaire";
import { Button } from "@/components/ui/button";
import {
  adminChercherBeneficiaires,
  adminCorrigerPoints,
  ErreurApi,
  type BeneficiairePoints,
} from "@/lib/api/client";
import { formaterPoints } from "@/lib/classements";

type Choisi = { id: string; libelle: string };

// La correction motivée d'un score (spec 036) : depuis le registre (bénéficiaire à chercher) ou depuis une ligne de
// classement (bénéficiaire déjà choisi). La clé d'idempotence change à chaque ouverture.
export function DialogueCorrection({
  ouvert,
  onOuvert,
  onFait,
  beneficiaire = null,
}: {
  ouvert: boolean;
  onOuvert: (ouvert: boolean) => void;
  onFait: () => Promise<unknown>;
  beneficiaire?: Choisi | null;
}) {
  const [texte, setTexte] = useState("");
  const [trouves, setTrouves] = useState<BeneficiairePoints[]>([]);
  const [choisi, setChoisi] = useState<Choisi | null>(beneficiaire);
  const [montant, setMontant] = useState("");
  const [motif, setMotif] = useState("");
  // Une clé par correction : un double envoi n'écrit qu'une ligne.
  const cle = useRef(crypto.randomUUID());

  useEffect(() => {
    if (!ouvert) return;
    cle.current = crypto.randomUUID();
    setTexte("");
    setTrouves([]);
    setChoisi(beneficiaire);
    setMontant("");
    setMotif("");
  }, [ouvert, beneficiaire]);

  useEffect(() => {
    if (texte.trim().length < 2) {
      setTrouves([]);
      return;
    }
    let actif = true;
    const minuteur = setTimeout(() => {
      adminChercherBeneficiaires(texte.trim())
        .then((resultats) => actif && setTrouves(resultats))
        .catch(() => actif && setTrouves([]));
    }, 250);
    return () => {
      actif = false;
      clearTimeout(minuteur);
    };
  }, [texte]);

  return (
    <DialogueFormulaire
      ouvert={ouvert}
      onOuvert={onOuvert}
      titre="Corriger un score"
      description="La correction ajoute une ligne motivée au registre, sans part de club. Pour retirer la part d'un club, annule la ligne d'origine."
      bouton="Enregistrer la correction"
      onEnvoie={async () => {
        if (!choisi) throw new ErreurApi(422, "Choisis un élève ou un encadreur.");
        await adminCorrigerPoints({
          utilisateur_id: choisi.id,
          montant: Number(montant),
          motif: motif.trim(),
          cle: cle.current,
        });
        await onFait();
      }}
    >
      {choisi ? (
        <div className="flex items-center justify-between gap-3 rounded-2xl bg-mist-soft p-3">
          <p className="min-w-0 break-words text-sm font-bold">{choisi.libelle}</p>
          <Button type="button" variant="outline" size="sm" onClick={() => setChoisi(null)}>
            Changer
          </Button>
        </div>
      ) : (
        <Champ libelle="Bénéficiaire">
          <input
            value={texte}
            onChange={(e) => setTexte(e.target.value)}
            maxLength={100}
            placeholder="Pseudonyme ou identifiant"
            className={CHAMP_ADMIN}
          />
          {trouves.length > 0 && (
            <ul className="mt-1 max-h-52 divide-y overflow-y-auto rounded-xl ring-1 ring-border">
              {trouves.map((b) => (
                <li key={b.id}>
                  <button
                    type="button"
                    onClick={() =>
                      setChoisi({
                        id: b.id,
                        libelle: `${b.nom_public} (${b.identifiant}) · ${formaterPoints(b.points_total)} pts`,
                      })
                    }
                    className="w-full px-3 py-2 text-left text-sm font-semibold hover:bg-mist-soft"
                  >
                    {b.nom_public} ({b.identifiant}) · {b.role === "eleve" ? "élève" : "encadreur"}
                    {b.club ? ` · ${b.club}` : ""}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </Champ>
      )}
      <Champ libelle="Montant (positif ou négatif)">
        <input
          type="number"
          required
          min={-10000}
          max={10000}
          step={1}
          value={montant}
          onChange={(e) => setMontant(e.target.value)}
          className={CHAMP_ADMIN}
        />
      </Champ>
      <Champ libelle="Motif (10 à 500 caractères)">
        <textarea
          required
          minLength={10}
          maxLength={500}
          value={motif}
          onChange={(e) => setMotif(e.target.value)}
          className={`${CHAMP_ADMIN} h-24 py-2`}
        />
      </Champ>
    </DialogueFormulaire>
  );
}
