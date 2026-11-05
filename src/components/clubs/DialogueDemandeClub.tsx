import { Plus, Trash2 } from "lucide-react";
import { useState } from "react";

import { Champ, CHAMP_ADMIN, DialogueFormulaire } from "@/components/admin/DialogueFormulaire";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  demanderClub,
  ErreurApi,
  type AxePublic,
  type DemandeClubEntree,
  type EtablissementRattache,
} from "@/lib/api/client";

type EncadreurSaisi = { nom: string; email: string; telephone: string };

const VIDE: EncadreurSaisi = { nom: "", email: "", telephone: "" };

// Formulaire de demande de création (spec 019) : l'établissement est celui du profil, jamais un champ libre.
export function DialogueDemandeClub({
  ouvert,
  onOuvert,
  etablissement,
  axes,
  onCree,
}: {
  ouvert: boolean;
  onOuvert: (ouvert: boolean) => void;
  etablissement: EtablissementRattache;
  axes: AxePublic[];
  onCree: () => Promise<unknown>;
}) {
  const [nom, setNom] = useState("");
  const [description, setDescription] = useState("");
  const [choisis, setChoisis] = useState<string[]>([]);
  const [encadreurs, setEncadreurs] = useState<EncadreurSaisi[]>([]);
  const [confirmation, setConfirmation] = useState(false);

  const reinitialiser = () => {
    setNom("");
    setDescription("");
    setChoisis([]);
    setEncadreurs([]);
    setConfirmation(false);
  };

  const basculerAxe = (code: string) => {
    setChoisis((actuels) =>
      actuels.includes(code)
        ? actuels.filter((c) => c !== code)
        : actuels.length >= 3
          ? actuels
          : [...actuels, code],
    );
  };

  const modifierEncadreur = (index: number, champ: keyof EncadreurSaisi, valeur: string) => {
    setEncadreurs((actuels) =>
      actuels.map((personne, i) => (i === index ? { ...personne, [champ]: valeur } : personne)),
    );
  };

  const envoyer = async () => {
    const nomPropre = nom.trim();
    if (nomPropre.length < 3) {
      throw new ErreurApi(422, "Le nom officiel du club doit contenir au moins 3 caractères.");
    }
    if (!confirmation) {
      throw new ErreurApi(
        422,
        "Coche la case pour confirmer que tu es désigné président de ce club par ton établissement.",
      );
    }
    if (encadreurs.some((personne) => personne.nom.trim().length === 0)) {
      throw new ErreurApi(422, "Chaque encadreur associé doit avoir un nom.");
    }
    const entree: DemandeClubEntree = {
      nom: nomPropre,
      description: description.trim() || null,
      axes: choisis,
      encadreurs_associes: encadreurs.map((personne) => ({
        nom: personne.nom.trim(),
        email: personne.email.trim() || null,
        telephone: personne.telephone.trim() || null,
      })),
      confirmation: true,
    };
    await demanderClub(entree);
    reinitialiser();
    await onCree();
  };

  return (
    <DialogueFormulaire
      ouvert={ouvert}
      onOuvert={onOuvert}
      titre="Ouvrir l'espace de mon club"
      description="L'équipe nationale vérifie chaque demande avant l'activation. Rien n'est public avant."
      bouton="Envoyer ma demande"
      onEnvoie={envoyer}
    >
      <p className="rounded-2xl bg-mist-soft px-4 py-3 text-sm font-semibold text-ink">
        Établissement : <strong>{etablissement.nom}</strong>
        <span className="block font-medium text-muted-foreground">
          {etablissement.iesg} · {etablissement.dre}
        </span>
      </p>

      <Champ libelle="Nom officiel du club">
        <input
          value={nom}
          onChange={(e) => setNom(e.target.value)}
          maxLength={150}
          required
          placeholder="Ex. : Club Santé du Lycée de Tokoin"
          className={CHAMP_ADMIN}
        />
      </Champ>

      <Champ libelle="Description courte (facultatif)">
        <Textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          maxLength={300}
          rows={2}
          placeholder="Ce que le club veut faire cette année…"
          className="font-medium"
        />
      </Champ>

      <fieldset className="grid gap-2">
        <legend className="text-sm font-bold">Axes privilégiés (3 au plus)</legend>
        <div className="flex flex-wrap gap-2">
          {axes.map((axe) => {
            const on = choisis.includes(axe.code);
            return (
              <label
                key={axe.code}
                className={`cursor-pointer rounded-full px-3 py-1.5 text-sm font-bold ring-1 transition ${
                  on
                    ? "bg-logo-blue text-white ring-logo-blue"
                    : "bg-white text-ink ring-border hover:ring-logo-blue/40"
                } ${!on && choisis.length >= 3 ? "cursor-not-allowed opacity-50" : ""}`}
              >
                <input
                  type="checkbox"
                  checked={on}
                  disabled={!on && choisis.length >= 3}
                  onChange={() => basculerAxe(axe.code)}
                  className="sr-only"
                />
                {axe.libelle}
              </label>
            );
          })}
        </div>
        <p className="text-xs font-medium text-muted-foreground">{choisis.length}/3 choisis.</p>
      </fieldset>

      <fieldset className="grid gap-2">
        <legend className="text-sm font-bold">Encadreurs associés (facultatif)</legend>
        <p className="text-xs font-medium text-muted-foreground">
          Des personnes de ton établissement qui accompagnent le club. Aucun compte n'est créé :
          l'équipe s'en sert pour vérifier la demande.
        </p>
        {encadreurs.map((personne, index) => (
          <div
            key={index}
            className="grid gap-2 rounded-2xl border p-3 sm:grid-cols-[1fr_1fr_auto]"
          >
            <input
              value={personne.nom}
              onChange={(e) => modifierEncadreur(index, "nom", e.target.value)}
              maxLength={100}
              placeholder="Nom et prénom"
              aria-label={`Nom de l'encadreur ${index + 1}`}
              className={CHAMP_ADMIN}
            />
            <input
              value={personne.email}
              onChange={(e) => modifierEncadreur(index, "email", e.target.value)}
              maxLength={254}
              type="email"
              placeholder="E-mail (facultatif)"
              aria-label={`E-mail de l'encadreur ${index + 1}`}
              className={CHAMP_ADMIN}
            />
            <div className="flex gap-2">
              <input
                value={personne.telephone}
                onChange={(e) => modifierEncadreur(index, "telephone", e.target.value)}
                maxLength={30}
                type="tel"
                placeholder="Téléphone"
                aria-label={`Téléphone de l'encadreur ${index + 1}`}
                className={CHAMP_ADMIN}
              />
              <button
                type="button"
                onClick={() => setEncadreurs((actuels) => actuels.filter((_, i) => i !== index))}
                aria-label={`Retirer l'encadreur ${index + 1}`}
                className="inline-flex size-11 shrink-0 items-center justify-center rounded-xl text-muted-foreground hover:bg-mist-soft hover:text-logo-red"
              >
                <Trash2 className="size-4" />
              </button>
            </div>
          </div>
        ))}
        {encadreurs.length < 10 && (
          <Button
            type="button"
            variant="outline"
            onClick={() => setEncadreurs((actuels) => [...actuels, { ...VIDE }])}
            className="w-fit rounded-full font-bold"
          >
            <Plus className="size-4" /> Ajouter un encadreur
          </Button>
        )}
      </fieldset>

      <label className="flex cursor-pointer items-start gap-3 rounded-2xl bg-sun/20 p-4 text-sm font-semibold text-ink">
        <input
          type="checkbox"
          checked={confirmation}
          onChange={(e) => setConfirmation(e.target.checked)}
          className="mt-0.5 size-4 shrink-0 accent-primary"
        />
        Je confirme être désigné(e) président(e) de ce club par mon établissement.
      </label>
    </DialogueFormulaire>
  );
}
