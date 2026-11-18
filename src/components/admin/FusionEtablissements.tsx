import { ArrowLeftRight, Loader2 } from "lucide-react";
import { useEffect, useState } from "react";

import { Champ, DialogueFormulaire } from "@/components/admin/DialogueFormulaire";
import { ChoixEtablissement, type EtablissementChoisi } from "@/components/ChoixEtablissement";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  adminApercuFusion,
  adminFusionnerEtablissements,
  ErreurApi,
  type ApercuFusion,
  type FicheDoublon,
} from "@/lib/api/client";
import { prefereGarder } from "@/lib/fusion";

const ETATS_CLUB: Record<string, string> = {
  en_constitution: "en constitution",
  actif: "actif",
  en_regularisation: "en régularisation",
  suspendu: "suspendu",
};

const pluriel = (n: number, mot: string) => `${n} ${mot}${n > 1 ? "s" : ""}`;

function Fiche({ fiche, role }: { fiche: FicheDoublon; role: "Gardé" | "Absorbé" }) {
  return (
    <div
      className={`rounded-2xl p-4 text-sm ring-1 ${role === "Gardé" ? "bg-mist-soft ring-logo-blue/40" : "ring-border"}`}
    >
      <p className="text-[11px] font-extrabold uppercase tracking-wider text-muted-foreground">
        {role}
      </p>
      <p className="mt-1 text-base font-extrabold">{fiche.nom}</p>
      <p className="text-muted-foreground">
        {fiche.iesg} · {fiche.prefecture ?? "préfecture non renseignée"}
      </p>
      <p className="text-muted-foreground">
        {fiche.statut === "propose" ? "Proposé" : fiche.statut === "actif" ? "Actif" : "Désactivé"}
        {" · "}
        {fiche.import_source ? "liste nationale" : "annuaire"}
      </p>
      <p className="mt-2 font-semibold">
        {pluriel(fiche.nb_eleves, "élève")} · {pluriel(fiche.nb_encadreurs, "encadreur")}
      </p>
      <p className="font-semibold">
        {fiche.club
          ? `Club ${ETATS_CLUB[fiche.club.etat] ?? fiche.club.etat}, ${pluriel(fiche.club.membres_actifs, "membre")}`
          : "Pas de club"}
      </p>
    </div>
  );
}

// Fusion de deux établissements (spec 042) : on choisit le gardé et le nom final ; l'aperçu de l'API annonce
// l'effet, ou le refus, avant la confirmation.
export function FusionEtablissements({
  depart,
  autre: autreInitial,
  fermer,
  apresFusion,
}: {
  depart: { id: string; nom: string };
  autre?: { id: string } | undefined;
  fermer: () => void;
  apresFusion: () => Promise<unknown>;
}) {
  const [choix, setChoix] = useState<EtablissementChoisi | null>(null);
  const autreId = autreInitial?.id ?? choix?.id ?? null;
  const [roles, setRoles] = useState<[string, string] | null>(null);
  const [apercu, setApercu] = useState<ApercuFusion | null>(null);
  const [erreur, setErreur] = useState<string | null>(null);
  const [nom, setNom] = useState<"garde" | "absorbe">("garde");

  // Une nouvelle paire : on lit l'aperçu dans un sens, puis on retient le gardé par défaut.
  useEffect(() => {
    if (!autreId) return;
    let annule = false;
    setRoles(null);
    setApercu(null);
    setErreur(null);
    adminApercuFusion(depart.id, autreId)
      .then((vu) => {
        if (annule) return;
        setRoles(prefereGarder(vu.garde, vu.absorbe) ? [depart.id, autreId] : [autreId, depart.id]);
      })
      .catch((e: unknown) => !annule && setErreur(e instanceof ErreurApi ? e.message : String(e)));
    return () => {
      annule = true;
    };
  }, [depart.id, autreId]);

  useEffect(() => {
    if (!roles) return;
    let annule = false;
    setApercu(null);
    adminApercuFusion(roles[0], roles[1])
      .then((vu) => !annule && setApercu(vu))
      .catch((e: unknown) => !annule && setErreur(e instanceof ErreurApi ? e.message : String(e)));
    return () => {
      annule = true;
    };
  }, [roles]);

  const nomFinal = apercu ? (nom === "garde" ? apercu.garde.nom : apercu.absorbe.nom) : null;

  return (
    <DialogueFormulaire
      ouvert
      onOuvert={(o) => !o && fermer()}
      titre={`Fusionner « ${depart.nom} »`}
      description="Les deux fiches deviennent une seule : rien n'est supprimé, et la fusion est inscrite au journal. Elle ne s'annule pas."
      bouton="Fusionner"
      danger
      onEnvoie={async () => {
        if (!apercu || !roles) throw new ErreurApi(422, "Choisis l'autre établissement.");
        await adminFusionnerEtablissements(roles[0], {
          absorbe_id: roles[1],
          version_garde: apercu.garde.version,
          version_absorbe: apercu.absorbe.version,
          nom,
        });
        await apresFusion();
      }}
    >
      {!autreInitial && (
        <Champ libelle="L'autre établissement">
          <ChoixEtablissement valeur={choix} onChoix={setChoix} exclure={depart.id} />
        </Champ>
      )}
      {erreur && (
        <Alert variant="destructive" role="alert">
          <AlertDescription>{erreur}</AlertDescription>
        </Alert>
      )}
      {autreId && !apercu && !erreur && (
        <p className="flex items-center gap-2 text-sm font-semibold text-muted-foreground">
          <Loader2 className="size-4 animate-spin" /> Lecture des deux fiches…
        </p>
      )}
      {apercu && roles && (
        <>
          <div className="grid gap-3 sm:grid-cols-2">
            <Fiche fiche={apercu.garde} role="Gardé" />
            <Fiche fiche={apercu.absorbe} role="Absorbé" />
          </div>
          <button
            type="button"
            onClick={() => setRoles([roles[1], roles[0]])}
            className="inline-flex w-fit items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-bold ring-1 ring-border transition hover:bg-mist-soft"
          >
            <ArrowLeftRight className="size-3.5" /> Inverser
          </button>
          <fieldset className="grid gap-2 text-sm">
            <legend className="mb-1 font-bold">Nom final</legend>
            {(["garde", "absorbe"] as const).map((cle) => (
              <label key={cle} className="flex items-center gap-2 font-semibold">
                <input
                  type="radio"
                  name="nom-final"
                  checked={nom === cle}
                  onChange={() => setNom(cle)}
                  className="size-4 accent-primary"
                />
                {cle === "garde" ? apercu.garde.nom : apercu.absorbe.nom}
              </label>
            ))}
          </fieldset>
          {apercu.refus ? (
            <Alert variant="destructive" role="alert">
              <AlertDescription>{apercu.refus}</AlertDescription>
            </Alert>
          ) : (
            <p role="status" className="rounded-2xl bg-mist-soft p-4 text-sm font-semibold">
              {apercu.effet} L'établissement gardé s'appellera « {nomFinal} ».
            </p>
          )}
        </>
      )}
    </DialogueFormulaire>
  );
}
