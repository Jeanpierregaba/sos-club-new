import { useState } from "react";
import { createFileRoute, Link, notFound, useNavigate, useRouter } from "@tanstack/react-router";
import { ExternalLink } from "lucide-react";

import { FormulaireEvenement } from "@/components/agenda/FormulaireEvenement";
import { Reponses } from "@/components/agenda/Reponses";
import { DialogueMotif } from "@/components/admin/DialogueMotif";
import { PageArticle } from "@/components/articles/PageArticle";
import { ServiceIndisponible } from "@/components/ServiceIndisponible";
import { Button } from "@/components/ui/button";
import {
  ErreurApi,
  annulerEvenement,
  chargerAxes,
  chargerEvenementDuClub,
  chargerReponsesEvenement,
  modifierEvenement,
  retirerEvenement,
  soumettreEvenement,
  supprimerEvenement,
} from "@/lib/api/client";
import { ETATS_EVENEMENT, depuisLome, plageEvenement } from "@/lib/agenda";

export const Route = createFileRoute("/_connecte/mon-club/agenda/$id")({
  gcTime: 0,
  loader: async ({ params }) => {
    try {
      const evenement = await chargerEvenementDuClub(params.id);
      const [axes, reponses] = await Promise.all([
        chargerAxes(),
        evenement.publie
          ? chargerReponsesEvenement(params.id).catch(() => null)
          : Promise.resolve(null),
      ]);
      return { evenement, axes, reponses };
    } catch (e) {
      if (e instanceof ErreurApi && (e.statut === 404 || e.statut === 403)) throw notFound();
      throw e;
    }
  },
  head: () => ({
    meta: [
      { title: "Événement du club — Club Santé SOS Docteur TV" },
      { name: "robots", content: "noindex" },
    ],
  }),
  errorComponent: ServiceIndisponible,
  notFoundComponent: () => (
    <PageArticle titre="Événement" accent="introuvable" retour="club">
      <Link to="/mon-club/agenda" className="font-bold text-logo-blue hover:underline">
        Retour à l'agenda du club
      </Link>
    </PageArticle>
  ),
  component: EvenementDuClub,
});

function EvenementDuClub() {
  const { evenement, axes, reponses } = Route.useLoaderData();
  const router = useRouter();
  const naviguer = useNavigate();
  const [modification, setModification] = useState(false);
  const [annulation, setAnnulation] = useState(false);
  const [erreur, setErreur] = useState<string | null>(null);
  const champs = evenement.champs;
  const titre = typeof champs["titre"] === "string" ? champs["titre"] : "Événement";
  const debut = typeof champs["debut"] === "string" ? depuisLome(champs["debut"]) : null;
  const fin = typeof champs["fin"] === "string" ? depuisLome(champs["fin"]) : null;
  const soumettable =
    evenement.de_moi && (evenement.etat === "brouillon" || evenement.etat === "a_corriger");
  const recharger = () => router.invalidate();

  async function agir(action: () => Promise<unknown>) {
    setErreur(null);
    try {
      await action();
      await recharger();
    } catch (e) {
      setErreur(e instanceof ErreurApi ? e.message : "L'action n'a pas abouti.");
    }
  }

  return (
    <PageArticle titre={titre} accent="" retour="club">
      <Link
        to="/mon-club/agenda"
        className="-mt-2 mb-4 inline-flex text-sm font-bold text-logo-blue hover:underline"
      >
        Agenda du club
      </Link>
      <div className="flex flex-wrap items-center gap-2">
        <span className="rounded-full bg-mist px-3 py-1 text-xs font-extrabold uppercase text-logo-blue">
          {evenement.annule_le ? "Annulé" : (ETATS_EVENEMENT[evenement.etat] ?? evenement.etat)}
        </span>
        {evenement.publie && !evenement.annule_le && (
          <Link
            to="/agenda/$id"
            params={{ id: evenement.id }}
            className="inline-flex items-center gap-1 text-sm font-bold text-logo-blue hover:underline"
          >
            Voir dans l'agenda public <ExternalLink className="size-4" />
          </Link>
        )}
      </div>
      {debut && fin && (
        <p className="mt-3 font-bold text-logo-blue">{plageEvenement(debut, fin)}</p>
      )}
      <p className="mt-1 text-sm font-semibold text-muted-foreground">
        Proposé par {evenement.de_moi ? "toi" : evenement.auteur}
      </p>

      {evenement.motif_decision &&
        (evenement.etat === "a_corriger" || evenement.etat === "refuse") && (
          <p className="mt-4 rounded-2xl bg-sun/30 px-4 py-3 font-semibold">
            Message de l'équipe : {evenement.motif_decision}
          </p>
        )}
      {evenement.annule_le && evenement.motif_annulation && (
        <p className="mt-4 rounded-2xl bg-logo-red/10 px-4 py-3 font-semibold">
          Annulé : {evenement.motif_annulation}
        </p>
      )}
      {erreur && (
        <p role="alert" className="mt-4 rounded-2xl bg-logo-red/10 px-4 py-3 text-sm font-semibold">
          {erreur}
        </p>
      )}

      <div className="mt-6 flex flex-wrap gap-3">
        {soumettable && (
          <Button
            className="h-11 rounded-full px-6 font-bold"
            onClick={() => void agir(() => soumettreEvenement(evenement.id, evenement.version))}
          >
            Soumettre à l'équipe
          </Button>
        )}
        {evenement.de_moi && evenement.etat === "en_attente" && (
          <Button
            variant="outline"
            className="h-11 rounded-full px-6 font-bold"
            onClick={() => void agir(() => retirerEvenement(evenement.id, evenement.version))}
          >
            Reprendre pour modifier
          </Button>
        )}
        {evenement.peut_modifier && !modification && (
          <Button
            variant="outline"
            className="h-11 rounded-full px-6 font-bold"
            onClick={() => setModification(true)}
          >
            Modifier
          </Button>
        )}
        {evenement.de_moi && evenement.etat === "brouillon" && !evenement.publie && (
          <Button
            variant="outline"
            className="h-11 rounded-full px-6 font-bold text-logo-red"
            onClick={() =>
              void agir(async () => {
                await supprimerEvenement(evenement.id, evenement.version);
                await naviguer({ to: "/mon-club/agenda" });
              })
            }
          >
            Supprimer le brouillon
          </Button>
        )}
        {evenement.publie && !evenement.annule_le && (
          <Button
            variant="outline"
            className="h-11 rounded-full px-6 font-bold text-logo-red"
            onClick={() => setAnnulation(true)}
          >
            Annuler l'événement
          </Button>
        )}
      </div>

      {modification ? (
        <div className="mt-6">
          <FormulaireEvenement
            initial={champs}
            axes={axes}
            bouton="Enregistrer"
            onEnvoi={async (saisie) => {
              await modifierEvenement(evenement.id, evenement.version, saisie);
              setModification(false);
              await recharger();
            }}
          />
          {evenement.publie && (
            <p className="mt-3 text-sm font-medium text-muted-foreground">
              La version en ligne reste affichée jusqu'à la validation de ta modification.
            </p>
          )}
        </div>
      ) : (
        <section className="mt-6 rounded-[1.75rem] bg-white p-5 shadow-card md:p-7">
          {typeof champs["objectif"] === "string" && champs["objectif"] && (
            <p className="font-medium">
              <strong>Objectif :</strong> {champs["objectif"]}
            </p>
          )}
          <p className="mt-2 whitespace-pre-line font-medium">
            {String(champs["description"] ?? "")}
          </p>
          <p className="mt-3 text-sm font-semibold text-muted-foreground">
            {champs["en_ligne"] === true ? "En ligne" : String(champs["lieu"] ?? "")}
          </p>
        </section>
      )}

      {reponses && <Reponses evenementId={evenement.id} initiales={reponses} />}

      <DialogueMotif
        ouvert={annulation}
        onOuvert={setAnnulation}
        titre="Annuler l'événement"
        description="Les membres invités seront prévenus avec ce motif. L'événement restera dans l'agenda, marqué « Annulé »."
        bouton="Annuler l'événement"
        danger
        longueurMin={10}
        longueurMax={200}
        onConfirme={async (motif) => {
          await annulerEvenement(evenement.id, motif);
          await recharger();
        }}
      />
    </PageArticle>
  );
}
