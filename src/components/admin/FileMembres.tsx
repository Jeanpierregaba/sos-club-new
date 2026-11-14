import { Check, CircleAlert, X } from "lucide-react";
import { useState } from "react";

import { DialogueFormulaire } from "@/components/admin/DialogueFormulaire";
import { DialogueMotif } from "@/components/admin/DialogueMotif";
import { Button } from "@/components/ui/button";
import {
  adminDeciderAffiliations,
  type AffiliationAValider,
  type Classe,
  type ResultatLot,
} from "@/lib/api/client";
import { libelleClasse } from "@/lib/classes";
import { dateCourte } from "@/lib/dates";

type Props = { demandes: AffiliationAValider[] };

// La file des affiliations à confirmer (spec 033) : un encadreur du club les confirme d'habitude ; l'équipe peut le
// faire à sa place (décision 2). Le collaborateur coche les élèves et décide en lot ; chaque affiliation est traitée
// à part et le résultat s'affiche ligne par ligne.
export function FileMembres({
  decideur,
  onRafraichir,
  ...props
}: Props & { decideur: boolean; onRafraichir: () => Promise<unknown> }) {
  const [selection, setSelection] = useState<Set<string>>(new Set());
  const [validation, setValidation] = useState(false);
  const [refus, setRefus] = useState(false);
  const [resultat, setResultat] = useState<ResultatLot | null>(null);
  const decidables = props.demandes;
  const echecs = new Map(resultat?.echecs.map((e) => [e.id, e.message]));
  const nom = "affiliation";

  const basculer = (id: string) =>
    setSelection((s) => {
      const suivante = new Set(s);
      if (suivante.has(id)) suivante.delete(id);
      else suivante.add(id);
      return suivante;
    });
  const elements = () =>
    props.demandes
      .filter((d) => selection.has(d.id))
      .map((d) => ({ id: d.id, version: d.version }));
  const decider = async (decision: "valider" | "refuser", motif?: string) => {
    const lot = elements();
    const reponse = await adminDeciderAffiliations(decision, lot, motif);
    setResultat(reponse);
    setSelection(new Set());
    await onRafraichir();
  };

  if (props.demandes.length === 0)
    return (
      <div className="rounded-3xl bg-white p-8 text-center font-medium text-muted-foreground shadow-card ring-1 ring-border">
        {resultat && <Bilan resultat={resultat} nom={nom} />}
        Aucune affiliation n'attend de confirmation dans ton périmètre.
      </div>
    );

  return (
    <div className="space-y-4">
      {resultat && <Bilan resultat={resultat} nom={nom} />}
      {decideur && (
        <div className="flex flex-wrap items-center gap-3 rounded-2xl bg-white p-4 shadow-card ring-1 ring-border">
          <label className="flex items-center gap-2 text-sm font-bold text-ink">
            <input
              type="checkbox"
              className="size-4 accent-primary"
              checked={decidables.length > 0 && decidables.every((d) => selection.has(d.id))}
              onChange={(e) =>
                setSelection(e.target.checked ? new Set(decidables.map((d) => d.id)) : new Set())
              }
            />
            Tout sélectionner
          </label>
          <Button
            disabled={selection.size === 0}
            onClick={() => setValidation(true)}
            className="ml-auto rounded-full font-bold"
          >
            <Check className="size-4" /> Valider la sélection ({selection.size})
          </Button>
          <Button
            variant="outline"
            disabled={selection.size === 0}
            onClick={() => setRefus(true)}
            className="rounded-full font-bold"
          >
            <X className="size-4" /> Refuser la sélection
          </Button>
        </div>
      )}

      <ul className="divide-y rounded-3xl bg-white shadow-card ring-1 ring-border">
        {props.demandes.map((d) => (
          <Ligne
            key={d.id}
            id={d.id}
            decideur={decideur}
            coche={selection.has(d.id)}
            onCocher={basculer}
            echec={echecs.get(d.id)}
            titre={d.pseudonyme}
            detail={`Élève de ${libelleClasse(d.classe as Classe)} · ${d.club_nom} · ${d.etablissement} · DRE ${d.dre}`}
            demande={d.demande_le}
          />
        ))}
      </ul>

      <DialogueFormulaire
        ouvert={validation}
        onOuvert={setValidation}
        titre={`Valider ${selection.size} ${nom}${selection.size > 1 ? "s" : ""} ?`}
        description="Chaque élève sélectionné devient membre confirmé de son club, qui est recalculé."
        bouton="Valider"
        onEnvoie={() => decider("valider")}
      />
      <DialogueMotif
        ouvert={refus}
        onOuvert={setRefus}
        titre={`Refuser ${selection.size} demande${selection.size > 1 ? "s" : ""} ?`}
        description="Le même motif est lu par chaque élève dans son espace."
        bouton="Refuser"
        danger
        onConfirme={(motif) => decider("refuser", motif)}
      />
    </div>
  );
}

function Ligne({
  id,
  decideur,
  coche,
  onCocher,
  echec,
  titre,
  detail,
  demande,
}: {
  id: string;
  decideur: boolean;
  coche: boolean;
  onCocher: (id: string) => void;
  echec: string | undefined;
  titre: string;
  detail: string;
  demande: string;
}) {
  return (
    <li className="flex items-start gap-3 px-5 py-4">
      <input
        type="checkbox"
        aria-label={`Sélectionner ${titre}`}
        disabled={!decideur}
        checked={coche}
        onChange={() => onCocher(id)}
        className="mt-1 size-4 accent-primary disabled:opacity-40"
      />
      <div className="min-w-0 flex-1">
        <p className="font-bold text-ink">{titre}</p>
        <p className="text-sm font-medium text-muted-foreground">{detail}</p>
        <p className="text-xs font-semibold text-muted-foreground">
          Inscrit le {dateCourte(demande)}
        </p>
        {echec && (
          <p
            role="alert"
            className="mt-1 flex items-center gap-1.5 text-sm font-semibold text-logo-red"
          >
            <CircleAlert aria-hidden className="size-4" /> {echec}
          </p>
        )}
      </div>
    </li>
  );
}

function Bilan({ resultat, nom }: { resultat: ResultatLot; nom: string }) {
  const n = resultat.reussies.length;
  return (
    <p
      role="status"
      className={`mb-2 rounded-2xl px-4 py-3 text-sm font-semibold ${
        resultat.echecs.length ? "bg-sun/20 text-ink" : "bg-primary/10 text-ink"
      }`}
    >
      {n} {nom}
      {n > 1 ? "s" : ""} traitée{n > 1 ? "s" : ""}
      {resultat.echecs.length > 0 &&
        ` · ${resultat.echecs.length} non traitée${resultat.echecs.length > 1 ? "s" : ""} : le motif est indiqué sur chaque ligne.`}
    </p>
  );
}
