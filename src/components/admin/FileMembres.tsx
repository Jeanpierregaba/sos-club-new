import { Check, CircleAlert, X } from "lucide-react";
import { useState } from "react";

import { DialogueFormulaire } from "@/components/admin/DialogueFormulaire";
import { DialogueMotif } from "@/components/admin/DialogueMotif";
import { Button } from "@/components/ui/button";
import {
  adminDeciderAffiliations,
  adminDeciderRattachements,
  type AffiliationAValider,
  type Classe,
  type Fonction,
  type RattachementAValider,
  type ResultatLot,
} from "@/lib/api/client";
import { libelleClasse } from "@/lib/classes";
import { dateCourte } from "@/lib/dates";
import { libelleFonction } from "@/lib/fonctions";

type Props =
  | { type: "affiliations"; demandes: AffiliationAValider[] }
  | { type: "rattachements"; demandes: RattachementAValider[] };

// La file des affiliations ou des rattachements confirmés par un président (spec 020). Le collaborateur coche
// les demandes et décide en lot ; chaque demande est traitée à part et le résultat s'affiche ligne par ligne.
// Un rattachement supplémentaire n'est décidable que par l'équipe nationale.
export function FileMembres({
  decideur,
  onRafraichir,
  ...props
}: Props & { decideur: boolean; onRafraichir: () => Promise<unknown> }) {
  const [selection, setSelection] = useState<Set<string>>(new Set());
  const [validation, setValidation] = useState(false);
  const [refus, setRefus] = useState(false);
  const [resultat, setResultat] = useState<ResultatLot | null>(null);
  const decidables = props.demandes.filter((d) => !("decidable" in d) || d.decidable);
  const echecs = new Map(resultat?.echecs.map((e) => [e.id, e.message]));
  const nom = props.type === "affiliations" ? "affiliation" : "rattachement";

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
    const reponse =
      props.type === "affiliations"
        ? await adminDeciderAffiliations(decision, lot, motif)
        : await adminDeciderRattachements(decision, lot, motif);
    setResultat(reponse);
    setSelection(new Set());
    await onRafraichir();
  };

  if (props.demandes.length === 0)
    return (
      <div className="rounded-3xl bg-white p-8 text-center font-medium text-muted-foreground shadow-card ring-1 ring-border">
        {resultat && <Bilan resultat={resultat} nom={nom} />}
        Aucune demande confirmée par un président n'attend ta décision.
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
        {props.type === "affiliations"
          ? props.demandes.map((d) => (
              <Ligne
                key={d.id}
                id={d.id}
                decideur={decideur}
                coche={selection.has(d.id)}
                onCocher={basculer}
                echec={echecs.get(d.id)}
                titre={d.pseudonyme}
                detail={`Élève de ${libelleClasse(d.classe as Classe)} · ${d.club_nom} · ${d.etablissement} · DRE ${d.dre}`}
                confirme={d.confirme_le}
              />
            ))
          : props.demandes.map((d) => (
              <Ligne
                key={d.id}
                id={d.id}
                decideur={decideur && d.decidable}
                coche={selection.has(d.id)}
                onCocher={basculer}
                echec={echecs.get(d.id)}
                titre={`${d.prenom} ${d.nom}`}
                detail={`${libelleFonction(d.fonction as Fonction)} à ${d.etablissement_encadreur} → ${d.club_nom} (${d.club_etablissement}) · DRE ${d.dre}`}
                confirme={d.confirme_le}
                mention={
                  d.supplementaire
                    ? d.decidable
                      ? "Club supplémentaire : cet encadreur en a déjà un"
                      : "Club supplémentaire : autorisation nationale requise"
                    : undefined
                }
              />
            ))}
      </ul>

      <DialogueFormulaire
        ouvert={validation}
        onOuvert={setValidation}
        titre={`Valider ${selection.size} ${nom}${selection.size > 1 ? "s" : ""} ?`}
        description={
          props.type === "affiliations"
            ? "Chaque élève sélectionné devient membre de son club."
            : "Chaque encadreur sélectionné est rattaché au club demandé."
        }
        bouton="Valider"
        onEnvoie={() => decider("valider")}
      />
      <DialogueMotif
        ouvert={refus}
        onOuvert={setRefus}
        titre={`Refuser ${selection.size} demande${selection.size > 1 ? "s" : ""} ?`}
        description="Le même motif est envoyé à chaque demandeur, qui pourra redemander."
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
  confirme,
  mention,
}: {
  id: string;
  decideur: boolean;
  coche: boolean;
  onCocher: (id: string) => void;
  echec: string | undefined;
  titre: string;
  detail: string;
  confirme: string | null | undefined;
  mention?: string | undefined;
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
        {confirme && (
          <p className="text-xs font-semibold text-muted-foreground">
            Confirmée par le président le {dateCourte(confirme)}
          </p>
        )}
        {mention && (
          <p className="mt-1 inline-flex rounded-full bg-sun/30 px-2.5 py-0.5 text-xs font-extrabold text-ink">
            {mention}
          </p>
        )}
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
