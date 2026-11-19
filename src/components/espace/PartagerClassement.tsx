import { useQuery } from "@tanstack/react-query";
import { Download, Loader2, Share2 } from "lucide-react";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import {
  chargerCarteClassement,
  chargerMonClassement,
  ErreurApi,
  MESSAGE_INDISPONIBLE,
  type OptionsCarteClassement,
  type PeriodeClassement,
  type VueCarteClassement,
} from "@/lib/api/client";

const NOM_FICHIER = "mon-classement-clubs-sante.png";
const VUES: { code: VueCarteClassement; libelle: string }[] = [
  { code: "national", libelle: "National" },
  { code: "dre", libelle: "Ma DRE" },
  { code: "club", libelle: "Mon club" },
];

// « Partager mon classement » (spec 044) : une carte image produite par l'API, sans nom ni coordonnées. Le club
// n'y figure que si la personne coche la case. Le partage natif du téléphone, sinon le téléchargement.
export function PartagerClassement({ className }: { className?: string }) {
  const [ouvert, setOuvert] = useState(false);
  return (
    <Dialog open={ouvert} onOpenChange={setOuvert}>
      <DialogTrigger asChild>
        <Button variant="outline" className={className}>
          <Share2 className="size-4" /> Partager mon classement
        </Button>
      </DialogTrigger>
      <DialogContent className="max-h-[92vh] overflow-y-auto rounded-3xl sm:max-w-lg">
        <DialogHeader>
          <DialogTitle className="text-2xl text-logo-blue">Partager mon classement</DialogTitle>
          <DialogDescription>
            Ta carte montre ton pseudonyme, ton rang et tes points, jamais ton nom ni ton
            établissement. Partager ne rapporte pas de points.
          </DialogDescription>
        </DialogHeader>
        {ouvert && <Choix />}
      </DialogContent>
    </Dialog>
  );
}

function Choix() {
  const moi = useQuery({ queryKey: ["mon-classement"], queryFn: chargerMonClassement });
  const aClub = moi.data?.club != null;
  const aSemestre = moi.data?.semestre_en_cours != null;
  const [options, setOptions] = useState<OptionsCarteClassement>({
    niveau: "national",
    periode: "semestre",
    club: false,
  });

  if (moi.isPending) return <Loader2 className="size-5 animate-spin" aria-label="Chargement" />;
  if (moi.isError) {
    return (
      <p role="alert" className="text-sm font-semibold text-destructive">
        {moi.error instanceof ErreurApi ? moi.error.message : MESSAGE_INDISPONIBLE}
      </p>
    );
  }
  const periodes: { code: PeriodeClassement; libelle: string }[] = [
    ...(aSemestre ? [{ code: "semestre" as const, libelle: "Ce semestre" }] : []),
    { code: "historique", libelle: "Depuis le début" },
  ];

  return (
    <div className="grid gap-4">
      <fieldset>
        <legend className="text-sm font-bold">Classement</legend>
        <div className="mt-2 flex flex-wrap gap-2">
          {VUES.filter((v) => v.code !== "club" || aClub).map((v) => (
            <Puce
              key={v.code}
              actif={options.niveau === v.code}
              onClick={() => setOptions({ ...options, niveau: v.code })}
            >
              {v.libelle}
            </Puce>
          ))}
        </div>
      </fieldset>
      <fieldset>
        <legend className="text-sm font-bold">Période</legend>
        <div className="mt-2 flex flex-wrap gap-2">
          {periodes.map((p) => (
            <Puce
              key={p.code}
              actif={(aSemestre ? options.periode : "historique") === p.code}
              onClick={() => setOptions({ ...options, periode: p.code })}
            >
              {p.libelle}
            </Puce>
          ))}
        </div>
      </fieldset>
      {aClub && (
        <div className="flex items-center gap-2">
          <Checkbox
            id="carte-club"
            checked={options.club}
            onCheckedChange={(v) => setOptions({ ...options, club: v === true })}
          />
          <Label htmlFor="carte-club">Afficher le nom de mon club</Label>
        </div>
      )}
      {/* Sans semestre en cours, seule la vue historique existe. */}
      <Apercu options={aSemestre ? options : { ...options, periode: "historique" }} />
    </div>
  );
}

function Puce({
  actif,
  onClick,
  children,
}: {
  actif: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      aria-pressed={actif}
      onClick={onClick}
      className={`rounded-full px-4 py-2 text-sm font-bold transition ${
        actif ? "bg-logo-blue text-white" : "bg-white ring-1 ring-border hover:ring-logo-blue/40"
      }`}
    >
      {children}
    </button>
  );
}

function Apercu({ options }: { options: OptionsCarteClassement }) {
  const carte = useQuery({
    queryKey: ["carte-classement", options],
    queryFn: () => chargerCarteClassement(options),
    staleTime: 60_000,
  });
  const [url, setUrl] = useState<string | null>(null);
  useEffect(() => {
    if (!carte.data) return;
    const adresse = URL.createObjectURL(carte.data);
    setUrl(adresse);
    return () => URL.revokeObjectURL(adresse);
  }, [carte.data]);

  if (carte.isPending)
    return <Loader2 className="size-5 animate-spin" aria-label="Préparation de ta carte" />;
  if (carte.isError) {
    return (
      <p role="alert" className="rounded-2xl bg-mist p-4 text-sm font-semibold">
        {carte.error instanceof ErreurApi ? carte.error.message : MESSAGE_INDISPONIBLE}
      </p>
    );
  }
  const fichier = new File([carte.data], NOM_FICHIER, { type: "image/png" });
  const natif =
    typeof navigator !== "undefined" &&
    typeof navigator.canShare === "function" &&
    navigator.canShare({ files: [fichier] });

  return (
    <div className="grid gap-3">
      {url && (
        <img
          src={url}
          alt="Aperçu de ta carte de classement"
          width={1080}
          height={1350}
          className="mx-auto w-full max-w-64 rounded-2xl shadow-card"
        />
      )}
      <div className="flex flex-wrap justify-center gap-2">
        {url && (
          <Button asChild variant={natif ? "outline" : "default"}>
            <a href={url} download={NOM_FICHIER}>
              <Download className="size-4" /> Télécharger
            </a>
          </Button>
        )}
        {natif && (
          <Button
            type="button"
            onClick={() =>
              void navigator
                .share({ files: [fichier], title: "Mon classement aux Clubs Santé" })
                .catch(() => undefined)
            }
          >
            <Share2 className="size-4" /> Partager
          </Button>
        )}
      </div>
    </div>
  );
}
