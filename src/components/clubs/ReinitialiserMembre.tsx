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
  const [copie, setCopie] = useState(false);

  const copier = async () => {
    if (!provisoire) return;
    try {
      await navigator.clipboard.writeText(provisoire);
      setCopie(true);
    } catch {
      setCopie(false);
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
        onConfirme={async (texte) => {
          const { mot_de_passe } = await reinitialiserMembre(affiliationId, texte);
          setCopie(false);
          setProvisoire(mot_de_passe);
        }}
      />
      <Dialog open={provisoire !== null} onOpenChange={(o) => !o && setProvisoire(null)}>
        <DialogContent className="sm:rounded-[2rem]">
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
          <Button variant="outline" onClick={copier} className="rounded-full font-bold">
            {copie ? <Check className="size-4" /> : <Copy className="size-4" />}
            {copie ? "Copié" : "Copier"}
          </Button>
        </DialogContent>
      </Dialog>
    </>
  );
}
