import { Check, Copy, KeyRound } from "lucide-react";
import { useState } from "react";

import { DialogueMotif } from "@/components/admin/DialogueMotif";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { reinitialiserMembre } from "@/lib/api/client";

// Réinitialiser le mot de passe d'un membre confirmé (spec 039) : un motif, puis le mot de passe provisoire montré
// une seule fois, à donner à l'élève en main propre. L'API vérifie le club, l'affiliation et le plafond du jour.
export function ReinitialiserMembre({
  affiliationId,
  pseudonyme,
}: {
  affiliationId: string;
  pseudonyme: string;
}) {
  const [motif, setMotif] = useState(false);
  const [provisoire, setProvisoire] = useState<string | null>(null);
  const [copie, setCopie] = useState<"non" | "oui" | "echec">("non");

  const copier = async () => {
    if (!provisoire) return;
    try {
      await navigator.clipboard.writeText(provisoire);
      setCopie("oui");
    } catch {
      setCopie("echec");
    }
  };

  return (
    <>
      <Button
        size="sm"
        variant="outline"
        onClick={() => setMotif(true)}
        className="rounded-full font-bold"
        aria-label={`Réinitialiser le mot de passe de ${pseudonyme}`}
      >
        <KeyRound className="size-4" /> Mot de passe
      </Button>
      <DialogueMotif
        ouvert={motif}
        onOuvert={setMotif}
        titre={`Réinitialiser le mot de passe de ${pseudonyme} ?`}
        description="Son ancien mot de passe ne marchera plus et ses connexions seront fermées. L'élève sera prévenu que c'est toi. Indique pourquoi (10 caractères au moins) : 10 réinitialisations par jour au plus."
        bouton="Réinitialiser"
        longueurMin={10}
        longueurMax={200}
        onConfirme={async (texte) => {
          const { mot_de_passe } = await reinitialiserMembre(affiliationId, texte);
          setCopie("non");
          setProvisoire(mot_de_passe);
        }}
      />
      {/* Le mot de passe ne se réaffiche pas : on ne ferme qu'après l'avoir noté, jamais par un clic à côté. */}
      <Dialog open={provisoire !== null}>
        <DialogContent
          className="sm:rounded-[2rem] [&>button]:hidden"
          onInteractOutside={(e) => e.preventDefault()}
          onEscapeKeyDown={(e) => e.preventDefault()}
        >
          <DialogHeader>
            <DialogTitle className="text-2xl text-logo-blue">Mot de passe provisoire</DialogTitle>
            <DialogDescription>
              Donne-le à {pseudonyme} en main propre. Il ne s'affichera plus : note-le maintenant.
              Conseille-lui de choisir son propre mot de passe dès sa connexion.
            </DialogDescription>
          </DialogHeader>
          <p
            className="select-all rounded-2xl bg-mist-soft p-4 text-center font-mono text-2xl font-bold tracking-widest text-ink"
            aria-label="Mot de passe à donner à l’élève"
          >
            {provisoire}
          </p>
          <div className="flex flex-wrap gap-2">
            <Button variant="outline" onClick={copier} className="rounded-full font-bold">
              {copie === "oui" ? <Check className="size-4" /> : <Copy className="size-4" />}
              {copie === "oui" ? "Copié" : "Copier"}
            </Button>
            <Button onClick={() => setProvisoire(null)} className="rounded-full font-bold">
              J'ai noté le mot de passe
            </Button>
          </div>
          {copie === "echec" && (
            <p role="alert" className="text-sm font-semibold text-logo-red">
              La copie n'a pas marché : recopie le mot de passe à la main.
            </p>
          )}
        </DialogContent>
      </Dialog>
    </>
  );
}
