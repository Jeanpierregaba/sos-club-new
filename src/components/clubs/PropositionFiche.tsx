import { Loader2, Send, Undo2 } from "lucide-react";
import { useState } from "react";

import { EtatContenu } from "@/components/articles/EtatContenu";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  ErreurApi,
  MESSAGE_INDISPONIBLE,
  proposerFiche,
  retirerProposition,
  type AxePublic,
  type PropositionFiche as Proposition,
} from "@/lib/api/client";
import { dateCourte } from "@/lib/dates";

const AXES_MAX = 3;
const DESCRIPTION_MAX = 300;

// Le président propose une nouvelle présentation du club (spec 026) : la fiche publique ne change qu'à
// l'approbation d'un modérateur, et une seule proposition attend à la fois.
export function PropositionFiche({
  description,
  axes,
  tousLesAxes,
  propositions,
  onRafraichir,
}: {
  description: string | null;
  axes: string[];
  tousLesAxes: AxePublic[];
  propositions: Proposition[];
  onRafraichir: () => Promise<unknown>;
}) {
  const enAttente = propositions.find((p) => p.etat === "en_attente") ?? null;
  const [texte, setTexte] = useState(description ?? "");
  const [choisis, setChoisis] = useState<string[]>(axes);
  const [erreur, setErreur] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);
  const [enCours, setEnCours] = useState(false);

  const inchange =
    texte.trim() === (description ?? "") && [...choisis].sort().join() === [...axes].sort().join();

  async function agir(action: () => Promise<unknown>, message: string) {
    setErreur(null);
    setInfo(null);
    setEnCours(true);
    try {
      await action();
      setInfo(message);
      await onRafraichir();
    } catch (e) {
      setErreur(e instanceof ErreurApi ? e.message : MESSAGE_INDISPONIBLE);
    } finally {
      setEnCours(false);
    }
  }

  const basculer = (code: string) =>
    setChoisis((c) =>
      c.includes(code) ? c.filter((x) => x !== code) : c.length < AXES_MAX ? [...c, code] : c,
    );
  const libelle = (code: string) => tousLesAxes.find((a) => a.code === code)?.libelle ?? code;

  return (
    <section className="space-y-4 rounded-3xl bg-card p-5 shadow-card sm:p-7">
      <div>
        <h2 className="font-display text-xl text-ink">Présentation du club</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Propose une nouvelle description ou d'autres axes : la fiche publique change après la
          validation de l'équipe.
        </p>
      </div>

      {enAttente ? (
        <div className="space-y-3 rounded-2xl bg-sun/15 p-4">
          <p className="text-sm font-bold text-ink">
            Proposition envoyée le {enAttente.soumis_le ? dateCourte(enAttente.soumis_le) : "—"}, en
            attente de validation
          </p>
          <p className="whitespace-pre-line text-sm">
            {enAttente.description ?? "(sans description)"}
          </p>
          <p className="text-sm text-muted-foreground">
            Axes : {enAttente.axes.map(libelle).join(", ")}
          </p>
          <Button
            variant="outline"
            size="sm"
            className="rounded-full font-bold"
            disabled={enCours}
            onClick={() =>
              void agir(
                () => retirerProposition(enAttente.id),
                "Proposition retirée : tu peux en faire une autre.",
              )
            }
          >
            <Undo2 className="size-4" /> Retirer la proposition
          </Button>
        </div>
      ) : (
        <form
          className="space-y-4"
          onSubmit={(e) => {
            e.preventDefault();
            void agir(
              () => proposerFiche({ description: texte.trim() || null, axes: choisis }),
              "Proposition envoyée : tu recevras la décision dans tes notifications.",
            );
          }}
        >
          <div className="space-y-2">
            <Label htmlFor="description-club">Description</Label>
            <Textarea
              id="description-club"
              value={texte}
              maxLength={DESCRIPTION_MAX}
              rows={3}
              onChange={(e) => setTexte(e.target.value)}
            />
            <p className="text-xs text-muted-foreground">
              {texte.length} / {DESCRIPTION_MAX}
            </p>
          </div>
          <fieldset className="space-y-2">
            <legend className="text-sm font-medium">Axes du club (1 à {AXES_MAX})</legend>
            <div className="flex flex-wrap gap-2">
              {tousLesAxes.map((a) => {
                const actif = choisis.includes(a.code);
                return (
                  <button
                    key={a.code}
                    type="button"
                    aria-pressed={actif}
                    onClick={() => basculer(a.code)}
                    className={`rounded-full px-3 py-1.5 text-sm font-semibold ring-1 transition ${
                      actif
                        ? "bg-primary text-primary-foreground ring-primary"
                        : "bg-white ring-border"
                    }`}
                  >
                    {a.libelle}
                  </button>
                );
              })}
            </div>
          </fieldset>
          <Button
            type="submit"
            className="rounded-full font-bold"
            disabled={enCours || inchange || choisis.length === 0}
          >
            {enCours ? <Loader2 className="size-4 animate-spin" /> : <Send className="size-4" />}
            Proposer ces changements
          </Button>
        </form>
      )}

      {propositions.filter((p) => p.etat !== "en_attente").slice(0, 3).length > 0 && (
        <ul className="space-y-2 border-t pt-3 text-sm">
          {propositions
            .filter((p) => p.etat !== "en_attente")
            .slice(0, 3)
            .map((p) => (
              <li key={p.id} className="flex flex-wrap items-center gap-2">
                <EtatContenu etat={p.etat} />
                <span className="text-muted-foreground">
                  {p.soumis_le ? dateCourte(p.soumis_le) : ""}
                </span>
                {p.motif && <span>Motif : {p.motif}</span>}
              </li>
            ))}
        </ul>
      )}

      {erreur && (
        <Alert variant="destructive">
          <AlertDescription>{erreur}</AlertDescription>
        </Alert>
      )}
      {info && (
        <p role="status" className="text-sm font-semibold text-ink">
          {info}
        </p>
      )}
    </section>
  );
}
