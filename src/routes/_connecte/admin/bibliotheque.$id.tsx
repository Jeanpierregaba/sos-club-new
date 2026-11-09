import { createFileRoute, Link, useNavigate, useRouter } from "@tanstack/react-router";
import {
  ArrowLeft,
  CheckCircle2,
  ExternalLink,
  EyeOff,
  Pencil,
  Send,
  ShieldCheck,
  Trash2,
  Undo2,
  X,
} from "lucide-react";
import { useState, type ReactNode } from "react";

import { Champ, CHAMP_ADMIN, DialogueFormulaire } from "@/components/admin/DialogueFormulaire";
import { DialogueMotif } from "@/components/admin/DialogueMotif";
import { ChampsRessource } from "@/components/bibliotheque/ChampsRessource";
import { DepotFichier } from "@/components/bibliotheque/DepotFichier";
import { BadgeEtatQuiz as BadgeEtat } from "@/components/quiz/BadgeEtatQuiz";
import { ServiceIndisponible } from "@/components/ServiceIndisponible";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { peut } from "@/lib/admin";
import {
  approuverRessource,
  chargerAxes,
  chargerRessource,
  deposerFichierRessource,
  depublierRessource,
  ErreurApi,
  MESSAGE_INDISPONIBLE,
  modifierRessource,
  refuserRessource,
  reprendreRessource,
  retirerCouvertureRessource,
  soumettreRessource,
  supprimerRessource,
  urlCouvertureGestion,
  urlRelectureRessource,
  type AxePublic,
  type RessourceEntree,
} from "@/lib/api/client";
import { CATEGORIES, tailleLisible } from "@/lib/bibliotheque";
import { dateCourte } from "@/lib/dates";

export const Route = createFileRoute("/_connecte/admin/bibliotheque/$id")({
  gcTime: 0,
  loader: async ({ params }) => {
    const [ressource, axes] = await Promise.all([
      chargerRessource(params.id),
      chargerAxes().catch((): AxePublic[] => []),
    ]);
    return { ressource, axes };
  },
  errorComponent: ServiceIndisponible,
  component: FicheRessource,
});

type Dialogue = null | "infos" | "approuver" | "refuser" | "depublier";

function FicheRessource() {
  const { ressource, axes } = Route.useLoaderData();
  const { admin } = Route.useRouteContext();
  const router = useRouter();
  const naviguer = useNavigate();
  const [erreur, setErreur] = useState<string | null>(null);
  const [enCours, setEnCours] = useState(false);
  const [dialogue, setDialogue] = useState<Dialogue>(null);
  const [entree, setEntree] = useState<RessourceEntree>(ressource);
  const [validateurNom, setValidateurNom] = useState("");
  const [validateurQualite, setValidateurQualite] = useState("");

  const rafraichir = () => router.invalidate();
  const brouillon = ressource.etat === "brouillon";
  const redaction = brouillon && peut(admin, "bibliotheque", "modifier");
  const axe = axes.find((a) => a.code === ressource.axe_code)?.libelle;
  const magazineSansCouverture = ressource.categorie === "magazine" && !ressource.a_couverture;
  const pretPourSoumission = ressource.fichier_octets !== null && !magazineSansCouverture;

  async function agir(action: () => Promise<unknown>) {
    setErreur(null);
    setEnCours(true);
    try {
      await action();
      await rafraichir();
    } catch (e) {
      setErreur(e instanceof ErreurApi ? e.message : MESSAGE_INDISPONIBLE);
    } finally {
      setEnCours(false);
    }
  }

  async function supprimer() {
    if (!window.confirm("Supprimer cette ressource et ses fichiers ? C'est définitif.")) return;
    setErreur(null);
    try {
      await supprimerRessource(ressource.id);
      await naviguer({ to: "/admin/bibliotheque" });
    } catch (e) {
      setErreur(e instanceof ErreurApi ? e.message : MESSAGE_INDISPONIBLE);
    }
  }

  const actions: ReactNode[] = [];
  if (redaction)
    actions.push(
      <Button
        key="infos"
        variant="outline"
        className="rounded-full font-bold"
        onClick={() => {
          setEntree(ressource);
          setDialogue("infos");
        }}
      >
        <Pencil className="size-4" /> Informations
      </Button>,
    );
  if (brouillon && peut(admin, "bibliotheque", "soumettre"))
    actions.push(
      <Button
        key="soumettre"
        className="rounded-full font-bold"
        disabled={enCours || !pretPourSoumission}
        onClick={() => void agir(() => soumettreRessource(ressource.id))}
      >
        <Send className="size-4" /> Soumettre pour publication
      </Button>,
    );
  if (
    (ressource.etat === "soumis" || ressource.etat === "depublie") &&
    peut(admin, "bibliotheque", "soumettre")
  )
    actions.push(
      <Button
        key="reprendre"
        variant="outline"
        className="rounded-full font-bold"
        disabled={enCours}
        onClick={() => void agir(() => reprendreRessource(ressource.id))}
      >
        <Undo2 className="size-4" /> Reprendre en brouillon
      </Button>,
    );
  if (ressource.etat === "soumis" && peut(admin, "bibliotheque", "approuver"))
    actions.push(
      <Button
        key="approuver"
        className="rounded-full font-bold"
        disabled={ressource.contributeur}
        onClick={() => setDialogue("approuver")}
      >
        <ShieldCheck className="size-4" /> Publier
      </Button>,
      <Button
        key="refuser"
        variant="outline"
        className="rounded-full font-bold"
        onClick={() => setDialogue("refuser")}
      >
        <X className="size-4" /> Refuser
      </Button>,
    );
  if (ressource.etat === "publie" && peut(admin, "bibliotheque", "depublier"))
    actions.push(
      <Button
        key="depublier"
        variant="outline"
        className="rounded-full font-bold text-logo-red"
        onClick={() => setDialogue("depublier")}
      >
        <EyeOff className="size-4" /> Dépublier
      </Button>,
    );
  if (redaction && !ressource.deja_publiee)
    actions.push(
      <Button
        key="supprimer"
        variant="ghost"
        className="rounded-full font-bold text-logo-red"
        onClick={() => void supprimer()}
      >
        <Trash2 className="size-4" /> Supprimer
      </Button>,
    );

  return (
    <div className="space-y-5">
      <Link
        to="/admin/bibliotheque"
        className="inline-flex items-center gap-2 text-sm font-bold text-logo-blue hover:underline"
      >
        <ArrowLeft className="size-4" /> Toutes les ressources
      </Link>

      <section className="space-y-3 rounded-3xl bg-white p-5 shadow-card sm:p-7">
        <div className="flex flex-wrap items-center gap-2">
          <BadgeEtat etat={ressource.etat} />
          {ressource.contenu_de_test && (
            <span className="rounded-full bg-sun/30 px-2.5 py-0.5 text-xs font-extrabold">
              Contenu de test
            </span>
          )}
          <span className="text-sm text-muted-foreground">
            {CATEGORIES[ressource.categorie].un}
            {ressource.parution && ` · ${ressource.parution}`}
            {axe && ` · ${axe}`}
          </span>
        </div>
        <h2 className="font-display text-2xl text-ink">{ressource.titre}</h2>
        {ressource.description && <p className="text-muted-foreground">{ressource.description}</p>}
        {ressource.etat === "publie" && ressource.validateur_nom && (
          <p className="flex items-center gap-2 text-sm">
            <CheckCircle2 className="size-4 text-primary" /> Validé par {ressource.validateur_nom} (
            {ressource.validateur_qualite})
            {ressource.publie_le && `, en ligne depuis le ${dateCourte(ressource.publie_le)}`} ·{" "}
            {ressource.telechargements} téléchargements
          </p>
        )}
        {ressource.motif && ressource.etat !== "publie" && (
          <p className="rounded-2xl bg-logo-red/10 p-3 text-sm">
            <strong>Motif :</strong> {ressource.motif}
          </p>
        )}
        {ressource.etat === "soumis" &&
          ressource.contributeur &&
          peut(admin, "bibliotheque", "approuver") && (
            <p className="text-sm text-muted-foreground">
              Tu as préparé cette ressource : un autre membre de l'équipe doit la publier.
            </p>
          )}
        {brouillon && !pretPourSoumission && (
          <p className="text-sm text-muted-foreground">
            {ressource.fichier_octets === null
              ? "Dépose le PDF avant de soumettre."
              : "Un magazine a besoin d'une couverture avant d'être soumis."}
          </p>
        )}
        <div className="flex flex-wrap gap-2 pt-2">{actions}</div>
        {erreur && (
          <Alert variant="destructive">
            <AlertDescription>{erreur}</AlertDescription>
          </Alert>
        )}
      </section>

      <div className="grid gap-5 lg:grid-cols-2">
        <section className="space-y-3 rounded-3xl bg-white p-5 shadow-card sm:p-7">
          <h2 className="font-display text-xl text-ink">Le PDF</h2>
          {ressource.fichier_octets !== null ? (
            <p className="flex flex-wrap items-center gap-3 text-sm">
              <span>
                {tailleLisible(ressource.fichier_octets)}
                {ressource.pages ? ` · ${ressource.pages} pages` : ""}
              </span>
              <a
                href={urlRelectureRessource(ressource.id, ressource.modifie_le)}
                target="_blank"
                rel="noopener"
                className="inline-flex items-center gap-1 font-bold text-logo-blue hover:underline"
              >
                Ouvrir le PDF <ExternalLink className="size-4" />
              </a>
            </p>
          ) : (
            <p className="text-sm text-muted-foreground">Aucun PDF pour l'instant.</p>
          )}
          {redaction && (
            <DepotFichier
              libelle={ressource.fichier_octets === null ? "Déposer le PDF" : "Remplacer le PDF"}
              accept="application/pdf,.pdf"
              aide="20 Mo au plus. Un PDF simple : sans mot de passe, script ni fichier joint."
              onEnvoie={async (fichier, progression) => {
                await deposerFichierRessource(ressource.id, "fichier", fichier, progression);
                await rafraichir();
              }}
            />
          )}
        </section>

        <section className="space-y-3 rounded-3xl bg-white p-5 shadow-card sm:p-7">
          <h2 className="font-display text-xl text-ink">La couverture</h2>
          {ressource.a_couverture ? (
            <img
              src={urlCouvertureGestion(ressource.id, ressource.modifie_le)}
              alt={`Couverture : ${ressource.titre}`}
              className="max-h-64 rounded-2xl object-contain shadow-sm"
            />
          ) : (
            <p className="text-sm text-muted-foreground">
              {ressource.categorie === "magazine"
                ? "Obligatoire pour un magazine : elle s'affiche dans « À la Une »."
                : "Facultative : sans elle, la carte garde le visuel de sa catégorie."}
            </p>
          )}
          {redaction && (
            <div className="flex flex-wrap items-start gap-3">
              <DepotFichier
                libelle={
                  ressource.a_couverture ? "Changer la couverture" : "Déposer une couverture"
                }
                accept="image/jpeg,image/png,image/webp"
                aide="JPEG, PNG ou WebP, 8 Mo au plus."
                onEnvoie={async (fichier, progression) => {
                  await deposerFichierRessource(ressource.id, "couverture", fichier, progression);
                  await rafraichir();
                }}
              />
              {ressource.a_couverture && (
                <Button
                  variant="ghost"
                  className="rounded-full font-bold text-logo-red"
                  disabled={enCours}
                  onClick={() => void agir(() => retirerCouvertureRessource(ressource.id))}
                >
                  <Trash2 className="size-4" /> Retirer
                </Button>
              )}
            </div>
          )}
        </section>
      </div>

      <DialogueFormulaire
        ouvert={dialogue === "infos"}
        onOuvert={(o) => setDialogue(o ? "infos" : null)}
        titre="Informations de la ressource"
        bouton="Enregistrer"
        onEnvoie={async () => {
          await modifierRessource(ressource.id, {
            titre: entree.titre,
            description: entree.description,
            categorie: entree.categorie,
            axe_code: entree.axe_code ?? null,
            parution: entree.parution ?? null,
          });
          await rafraichir();
        }}
      >
        <ChampsRessource entree={entree} onChange={setEntree} axes={axes} />
      </DialogueFormulaire>

      <DialogueFormulaire
        ouvert={dialogue === "approuver"}
        onOuvert={(o) => setDialogue(o ? "approuver" : null)}
        titre="Publier cette ressource"
        description="Nomme la personne qui a validé le contenu : son nom s'affiche avec la ressource."
        bouton="Publier"
        onEnvoie={async () => {
          await approuverRessource(ressource.id, {
            validateur_nom: validateurNom,
            validateur_qualite: validateurQualite,
          });
          await rafraichir();
        }}
      >
        <Champ libelle="Nom du validateur">
          <input
            className={CHAMP_ADMIN}
            value={validateurNom}
            maxLength={120}
            onChange={(e) => setValidateurNom(e.target.value)}
          />
        </Champ>
        <Champ libelle="Qualité (ex. médecin de santé publique)">
          <input
            className={CHAMP_ADMIN}
            value={validateurQualite}
            maxLength={120}
            onChange={(e) => setValidateurQualite(e.target.value)}
          />
        </Champ>
      </DialogueFormulaire>

      <DialogueMotif
        ouvert={dialogue === "refuser"}
        onOuvert={(o) => setDialogue(o ? "refuser" : null)}
        titre="Refuser cette ressource"
        description="Elle revient en brouillon ; la personne qui l'a soumise reçoit ton motif."
        bouton="Refuser"
        danger
        onConfirme={async (motif) => {
          await refuserRessource(ressource.id, motif);
          await rafraichir();
        }}
      />
      <DialogueMotif
        ouvert={dialogue === "depublier"}
        onOuvert={(o) => setDialogue(o ? "depublier" : null)}
        titre="Dépublier cette ressource"
        description="Elle disparaît de la bibliothèque et son PDF n'est plus servi."
        bouton="Dépublier"
        danger
        onConfirme={async (motif) => {
          await depublierRessource(ressource.id, motif);
          await rafraichir();
        }}
      />
    </div>
  );
}
