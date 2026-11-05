import { Check, X } from "lucide-react";
import { useState } from "react";

import { CHAMP_ADMIN, Champ, DialogueFormulaire } from "@/components/admin/DialogueFormulaire";
import { DialogueMotif } from "@/components/admin/DialogueMotif";
import { ListeMembres } from "@/components/clubs/ListeMembres";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  confirmerAdhesion,
  confirmerRattachement,
  ErreurApi,
  MESSAGE_INDISPONIBLE,
  refuserAdhesion,
  refuserRattachement,
  retirerEncadreur,
  retirerMembre,
  type Classe,
  type DemandeAdhesion,
  type DemandeRattachement,
  type EncadreurDuClub,
  type Fonction,
  type MembreClub,
  type MembresDuClub,
} from "@/lib/api/client";
import { libelleClasse } from "@/lib/classes";
import { dateCourte } from "@/lib/dates";
import { libelleFonction } from "@/lib/fonctions";

type ARefuser =
  { type: "eleve"; demande: DemandeAdhesion } | { type: "encadreur"; demande: DemandeRattachement };
type ARetirer =
  { type: "membre"; membre: MembreClub } | { type: "encadreur"; encadreur: EncadreurDuClub };

// Le président gère son club depuis son espace (spec 020) : il confirme ou refuse les demandes des élèves et
// des encadreurs, puis l'équipe de la DRE les valide ; il retire un membre ou un encadreur.
export function GestionClub({
  clubId,
  demandesAdhesion,
  demandesRattachement,
  membres,
  onRafraichir,
}: {
  clubId: string;
  demandesAdhesion: DemandeAdhesion[];
  demandesRattachement: DemandeRattachement[];
  membres: MembresDuClub | null;
  onRafraichir: () => Promise<unknown>;
}) {
  const [erreur, setErreur] = useState<string | null>(null);
  const [enCours, setEnCours] = useState<string | null>(null);
  const [aRefuser, setARefuser] = useState<ARefuser | null>(null);
  const [aRetirer, setARetirer] = useState<ARetirer | null>(null);
  const [motifRetrait, setMotifRetrait] = useState("");
  const nombreDemandes = demandesAdhesion.length + demandesRattachement.length;

  const confirmer = async (id: string, action: () => Promise<unknown>) => {
    setErreur(null);
    setEnCours(id);
    try {
      await action();
      await onRafraichir();
    } catch (e) {
      setErreur(e instanceof ErreurApi ? e.message : MESSAGE_INDISPONIBLE);
    } finally {
      setEnCours(null);
    }
  };

  const boutons = (id: string, onConfirmer: () => Promise<unknown>, onRefuser: () => void) => (
    <span className="flex gap-2">
      <Button
        size="sm"
        disabled={enCours !== null}
        onClick={() => confirmer(id, onConfirmer)}
        className="rounded-full font-bold"
      >
        <Check className="size-4" /> Confirmer
      </Button>
      <Button
        size="sm"
        variant="outline"
        disabled={enCours !== null}
        onClick={onRefuser}
        className="rounded-full font-bold"
      >
        <X className="size-4" /> Refuser
      </Button>
    </span>
  );

  return (
    <div className="rounded-2xl border p-4">
      <Tabs defaultValue={nombreDemandes > 0 ? "demandes" : "membres"}>
        <TabsList className="rounded-full">
          <TabsTrigger value="demandes" className="rounded-full font-bold">
            Demandes{nombreDemandes > 0 ? ` (${nombreDemandes})` : ""}
          </TabsTrigger>
          <TabsTrigger value="membres" className="rounded-full font-bold">
            Membres{membres ? ` (${membres.membres.length})` : ""}
          </TabsTrigger>
        </TabsList>

        {erreur && (
          <p
            role="alert"
            className="mt-3 rounded-xl bg-logo-red/10 px-3 py-2 text-sm font-semibold text-ink"
          >
            {erreur}
          </p>
        )}

        <TabsContent value="demandes" className="mt-4 space-y-4">
          <p className="text-sm font-medium text-muted-foreground">
            Confirme les demandes des élèves et des encadreurs que tu connais : l'équipe de ta DRE
            les validera ensuite.
          </p>
          {nombreDemandes === 0 && (
            <p className="rounded-2xl bg-mist-soft px-4 py-3 text-sm font-medium text-muted-foreground">
              Aucune demande à confirmer pour l'instant.
            </p>
          )}
          {demandesAdhesion.length > 0 && (
            <ul aria-label="Demandes des élèves" className="divide-y rounded-2xl border">
              {demandesAdhesion.map((d) => (
                <li
                  key={d.id}
                  className="flex flex-wrap items-center justify-between gap-2 px-4 py-3"
                >
                  <span>
                    <span className="block font-bold text-ink">{d.pseudonyme}</span>
                    <span className="text-sm font-medium text-muted-foreground">
                      Élève de {libelleClasse(d.classe as Classe)} · demande du{" "}
                      {dateCourte(d.demande_le)}
                    </span>
                  </span>
                  {boutons(
                    d.id,
                    () => confirmerAdhesion(clubId, d.id, d.version),
                    () => setARefuser({ type: "eleve", demande: d }),
                  )}
                </li>
              ))}
            </ul>
          )}
          {demandesRattachement.length > 0 && (
            <ul aria-label="Demandes des encadreurs" className="divide-y rounded-2xl border">
              {demandesRattachement.map((d) => (
                <li
                  key={d.id}
                  className="flex flex-wrap items-center justify-between gap-2 px-4 py-3"
                >
                  <span>
                    <span className="block font-bold text-ink">
                      {d.prenom} {d.nom}{" "}
                      <span className="font-medium text-muted-foreground">· encadreur</span>
                    </span>
                    <span className="text-sm font-medium text-muted-foreground">
                      {libelleFonction(d.fonction as Fonction)} · {d.etablissement}
                    </span>
                  </span>
                  {boutons(
                    d.id,
                    () => confirmerRattachement(clubId, d.id, d.version),
                    () => setARefuser({ type: "encadreur", demande: d }),
                  )}
                </li>
              ))}
            </ul>
          )}
        </TabsContent>

        <TabsContent value="membres" className="mt-4">
          {membres ? (
            <ListeMembres
              liste={membres}
              onRetirerMembre={(membre) => {
                setMotifRetrait("");
                setARetirer({ type: "membre", membre });
              }}
              onRetirerEncadreur={(encadreur) => {
                setMotifRetrait("");
                setARetirer({ type: "encadreur", encadreur });
              }}
            />
          ) : (
            <p className="text-sm font-medium text-muted-foreground">
              La liste des membres n'a pas pu être chargée : recharge la page.
            </p>
          )}
        </TabsContent>
      </Tabs>

      <DialogueMotif
        ouvert={aRefuser !== null}
        onOuvert={(o) => !o && setARefuser(null)}
        titre="Refuser cette demande ?"
        description={
          aRefuser?.type === "eleve"
            ? `${aRefuser.demande.pseudonyme} lira ton motif et pourra redemander.`
            : aRefuser
              ? `${aRefuser.demande.prenom} ${aRefuser.demande.nom} lira ton motif.`
              : ""
        }
        bouton="Refuser"
        danger
        onConfirme={async (motif) => {
          if (!aRefuser) return;
          const d = aRefuser.demande;
          await (aRefuser.type === "eleve"
            ? refuserAdhesion(clubId, d.id, d.version, motif)
            : refuserRattachement(clubId, d.id, d.version, motif));
          setARefuser(null);
          await onRafraichir();
        }}
      />

      <DialogueFormulaire
        ouvert={aRetirer !== null}
        onOuvert={(o) => !o && setARetirer(null)}
        titre="Retirer du club ?"
        description={
          aRetirer?.type === "membre"
            ? `${aRetirer.membre.pseudonyme} ne fera plus partie du club. Il pourra redemander à le rejoindre.`
            : aRetirer
              ? `${aRetirer.encadreur.prenom} ${aRetirer.encadreur.nom} ne sera plus rattaché au club.`
              : ""
        }
        bouton="Retirer"
        danger
        onEnvoie={async () => {
          if (!aRetirer) return;
          await (aRetirer.type === "membre"
            ? retirerMembre(
                clubId,
                aRetirer.membre.id,
                aRetirer.membre.version,
                motifRetrait.trim(),
              )
            : retirerEncadreur(
                clubId,
                aRetirer.encadreur.id,
                aRetirer.encadreur.version,
                motifRetrait.trim(),
              ));
          setARetirer(null);
          await onRafraichir();
        }}
      >
        <Champ libelle="Motif (facultatif)">
          <input
            value={motifRetrait}
            onChange={(e) => setMotifRetrait(e.target.value)}
            maxLength={500}
            placeholder="Ex. : a quitté l'établissement"
            className={CHAMP_ADMIN}
          />
        </Champ>
      </DialogueFormulaire>
    </div>
  );
}
