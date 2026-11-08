import { Loader2, Plus, Save, X } from "lucide-react";
import { useState } from "react";

import { CHAMP_ADMIN } from "@/components/admin/DialogueFormulaire";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  ErreurApi,
  MESSAGE_INDISPONIBLE,
  type QuestionBanque,
  type QuestionEntree,
} from "@/lib/api/client";

const CHOIX_MIN = 2;
const CHOIX_MAX = 4;

// Saisie d'une question de la banque (spec 027) : énoncé, 2 à 4 choix, une seule bonne réponse cochée,
// explication facultative réservée à l'équipe. L'API revérifie tout.
export function EditeurQuestion({
  question,
  onEnregistre,
  onAnnule,
}: {
  question?: QuestionBanque;
  onEnregistre: (entree: QuestionEntree) => Promise<unknown>;
  onAnnule?: () => void;
}) {
  const [enonce, setEnonce] = useState(question?.enonce ?? "");
  const [choix, setChoix] = useState<string[]>(question?.choix ?? ["", ""]);
  const [bonne, setBonne] = useState(question?.bonne_reponse ?? 0);
  const [explication, setExplication] = useState(question?.explication ?? "");
  const [erreur, setErreur] = useState<string | null>(null);
  const [enCours, setEnCours] = useState(false);

  const complet = enonce.trim() !== "" && choix.every((c) => c.trim() !== "");

  async function enregistrer() {
    setErreur(null);
    setEnCours(true);
    try {
      await onEnregistre({
        enonce: enonce.trim(),
        choix: choix.map((c) => c.trim()),
        bonne_reponse: bonne,
        explication: explication.trim() || null,
      });
      if (!question) {
        setEnonce("");
        setChoix(["", ""]);
        setBonne(0);
        setExplication("");
      }
    } catch (e) {
      setErreur(e instanceof ErreurApi ? e.message : MESSAGE_INDISPONIBLE);
    } finally {
      setEnCours(false);
    }
  }

  function retirerChoix(i: number) {
    setChoix((c) => c.filter((_, j) => j !== i));
    setBonne((b) => (b === i ? 0 : b > i ? b - 1 : b));
  }

  return (
    <form
      className="grid gap-3 rounded-2xl bg-mist/60 p-4"
      onSubmit={(e) => {
        e.preventDefault();
        void enregistrer();
      }}
    >
      <label className="grid gap-1.5 text-sm font-bold">
        Énoncé
        <Textarea
          value={enonce}
          maxLength={300}
          rows={2}
          onChange={(e) => setEnonce(e.target.value)}
        />
      </label>
      <fieldset className="grid gap-2">
        <legend className="mb-1 text-sm font-bold">Choix (coche la bonne réponse)</legend>
        {choix.map((texte, i) => (
          <div key={i} className="flex items-center gap-2">
            <input
              type="radio"
              name="bonne-reponse"
              aria-label={`Choix ${i + 1} : bonne réponse`}
              checked={bonne === i}
              onChange={() => setBonne(i)}
              className="size-5 accent-primary"
            />
            <input
              className={CHAMP_ADMIN}
              aria-label={`Choix ${i + 1}`}
              value={texte}
              maxLength={150}
              onChange={(e) => setChoix((c) => c.map((x, j) => (j === i ? e.target.value : x)))}
            />
            {choix.length > CHOIX_MIN && (
              <Button
                type="button"
                variant="ghost"
                size="icon"
                aria-label={`Retirer le choix ${i + 1}`}
                onClick={() => retirerChoix(i)}
              >
                <X className="size-4" />
              </Button>
            )}
          </div>
        ))}
        {choix.length < CHOIX_MAX && (
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="w-fit rounded-full"
            onClick={() => setChoix((c) => [...c, ""])}
          >
            <Plus className="size-4" /> Ajouter un choix
          </Button>
        )}
      </fieldset>
      <label className="grid gap-1.5 text-sm font-bold">
        Explication (pour l'équipe, jamais montrée aux joueurs)
        <Textarea
          value={explication}
          maxLength={500}
          rows={2}
          onChange={(e) => setExplication(e.target.value)}
        />
      </label>
      {erreur && (
        <Alert variant="destructive">
          <AlertDescription>{erreur}</AlertDescription>
        </Alert>
      )}
      <div className="flex flex-wrap gap-2">
        <Button type="submit" className="rounded-full font-bold" disabled={enCours || !complet}>
          {enCours ? (
            <Loader2 className="size-4 animate-spin" />
          ) : question ? (
            <Save className="size-4" />
          ) : (
            <Plus className="size-4" />
          )}
          {question ? "Enregistrer la question" : "Ajouter la question"}
        </Button>
        {onAnnule && (
          <Button type="button" variant="ghost" className="rounded-full" onClick={onAnnule}>
            Annuler
          </Button>
        )}
      </div>
    </form>
  );
}
