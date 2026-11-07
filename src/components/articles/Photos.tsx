import { ImagePlus, Loader2, Star, Trash2 } from "lucide-react";
import { useState } from "react";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  envoyerPhoto,
  ErreurApi,
  MESSAGE_INDISPONIBLE,
  modifierPhoto,
  retirerPhoto,
  urlPhotoAuteur,
  type ArticleAuteur,
} from "@/lib/api/client";

export const MAX_PHOTOS = 5;
export const TEXTE_ATTESTATION =
  "J'ai l'accord des personnes reconnaissables sur cette photo et, pour un élève mineur, celui de son parent ou tuteur.";
// Seuls ces formats : un iPhone convertit alors sa photo en JPEG avant l'envoi.
const FORMATS = "image/jpeg,image/png,image/webp";

// Les photos d'un article dans l'éditeur (spec 024) : une couverture et une galerie, 5 au plus. Chaque envoi exige
// l'attestation de l'auteur (Q8). Chaque opération renvoie l'article à jour, avec sa nouvelle version.
export function Photos({
  article,
  modifiable,
  onArticle,
}: {
  article: ArticleAuteur | null;
  modifiable: boolean;
  onArticle: (article: ArticleAuteur) => void;
}) {
  const [fichier, setFichier] = useState<File | null>(null);
  const [legende, setLegende] = useState("");
  const [couverture, setCouverture] = useState(false);
  const [attestation, setAttestation] = useState(false);
  const [progression, setProgression] = useState<number | null>(null);
  const [erreur, setErreur] = useState<string | null>(null);
  const [enCours, setEnCours] = useState(false);
  const [champ, setChamp] = useState(0);

  if (!article)
    return (
      <section className="rounded-3xl bg-card p-5 shadow-card sm:p-7">
        <h2 className="font-display text-xl text-ink">Photos</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          Enregistre d'abord ton brouillon : tu pourras ensuite ajouter jusqu'à {MAX_PHOTOS} photos.
        </p>
      </section>
    );

  const photos = article.photos;
  if (!modifiable && photos.length === 0) return null;

  async function agir(action: () => Promise<ArticleAuteur>) {
    setErreur(null);
    setEnCours(true);
    try {
      onArticle(await action());
    } catch (e) {
      setErreur(e instanceof ErreurApi ? e.message : MESSAGE_INDISPONIBLE);
    } finally {
      setEnCours(false);
      setProgression(null);
    }
  }

  const envoyer = () =>
    agir(async () => {
      if (!fichier) throw new ErreurApi(422, "Choisis une photo.");
      const resultat = await envoyerPhoto(
        article.id,
        { fichier, version: article.version, legende, couverture },
        setProgression,
      );
      setFichier(null);
      setLegende("");
      setCouverture(false);
      setAttestation(false);
      setChamp((c) => c + 1);
      return resultat;
    });

  return (
    <section className="space-y-4 rounded-3xl bg-card p-5 shadow-card sm:p-7">
      <div className="flex items-baseline justify-between gap-2">
        <h2 className="font-display text-xl text-ink">Photos</h2>
        <span className="text-xs text-muted-foreground">
          {photos.length} / {MAX_PHOTOS}
        </span>
      </div>

      {photos.length > 0 && (
        <ul className="grid grid-cols-2 gap-3 sm:grid-cols-3">
          {photos.map((p) => (
            <li key={p.id} className="space-y-2">
              <div className="relative overflow-hidden rounded-2xl bg-mist">
                {p.effacee ? (
                  <p className="flex aspect-[4/3] items-center justify-center p-3 text-center text-xs text-muted-foreground">
                    Photo effacée
                  </p>
                ) : (
                  <img
                    src={urlPhotoAuteur(article.id, p.id, "vignette")}
                    alt={p.legende ?? "Photo de l'article"}
                    width={p.largeur}
                    height={p.hauteur}
                    loading="lazy"
                    className="aspect-[4/3] w-full object-cover"
                  />
                )}
                {p.couverture && (
                  <span className="absolute left-2 top-2 inline-flex items-center gap-1 rounded-full bg-white/95 px-2 py-0.5 text-xs font-bold text-ink">
                    <Star className="size-3 fill-sun text-sun" /> Couverture
                  </span>
                )}
              </div>
              {modifiable ? (
                <>
                  <Input
                    defaultValue={p.legende ?? ""}
                    maxLength={200}
                    aria-label="Légende"
                    placeholder="Légende (facultative)"
                    disabled={enCours}
                    onBlur={(e) => {
                      const valeur = e.target.value.trim();
                      if (valeur !== (p.legende ?? ""))
                        void agir(() =>
                          modifierPhoto(article.id, p.id, {
                            version: article.version,
                            legende: valeur || null,
                          }),
                        );
                    }}
                    className="h-9 text-sm"
                  />
                  <div className="flex flex-wrap gap-1">
                    {!p.couverture && (
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        disabled={enCours}
                        onClick={() =>
                          agir(() =>
                            modifierPhoto(article.id, p.id, {
                              version: article.version,
                              couverture: true,
                            }),
                          )
                        }
                        className="h-8 rounded-full px-3 text-xs font-bold"
                      >
                        <Star className="size-3" /> En couverture
                      </Button>
                    )}
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      disabled={enCours}
                      onClick={() => {
                        if (window.confirm("Retirer cette photo de l'article ?"))
                          void agir(() => retirerPhoto(article.id, p.id, article.version));
                      }}
                      className="h-8 rounded-full px-3 text-xs font-bold text-logo-red"
                    >
                      <Trash2 className="size-3" /> Retirer
                    </Button>
                  </div>
                </>
              ) : (
                p.legende && <p className="text-xs text-muted-foreground">{p.legende}</p>
              )}
            </li>
          ))}
        </ul>
      )}

      {modifiable && photos.length < MAX_PHOTOS && (
        <div className="space-y-3 rounded-2xl border border-dashed p-4">
          <Label htmlFor="photo" className="flex items-center gap-2">
            <ImagePlus className="size-4" /> Ajouter une photo
          </Label>
          <Input
            key={champ}
            id="photo"
            type="file"
            accept={FORMATS}
            disabled={enCours}
            onChange={(e) => setFichier(e.target.files?.[0] ?? null)}
          />
          <Input
            value={legende}
            maxLength={200}
            onChange={(e) => setLegende(e.target.value)}
            placeholder="Légende (facultative)"
            aria-label="Légende de la nouvelle photo"
          />
          <label className="flex items-center gap-3 text-sm">
            <Checkbox checked={couverture} onCheckedChange={(v) => setCouverture(v === true)} />
            En faire la photo de couverture
          </label>
          <label className="flex items-start gap-3 rounded-xl bg-sun/15 p-3 text-sm font-semibold">
            <Checkbox
              checked={attestation}
              onCheckedChange={(v) => setAttestation(v === true)}
              className="mt-0.5"
              aria-label="Attestation"
            />
            <span>{TEXTE_ATTESTATION}</span>
          </label>
          {progression !== null && (
            <div
              role="progressbar"
              aria-label="Envoi de la photo"
              aria-valuenow={Math.round(progression * 100)}
              className="h-2 overflow-hidden rounded-full bg-mist"
            >
              <div
                className="h-full bg-primary transition-[width]"
                style={{ width: `${Math.round(progression * 100)}%` }}
              />
            </div>
          )}
          <Button
            type="button"
            className="rounded-full font-bold"
            disabled={!fichier || !attestation || enCours}
            onClick={envoyer}
          >
            {enCours ? (
              <Loader2 className="size-4 animate-spin" />
            ) : (
              <ImagePlus className="size-4" />
            )}
            Envoyer la photo
          </Button>
          <p className="text-xs text-muted-foreground">
            JPEG, PNG ou WebP, 8 Mo au plus. La photo est réduite et ses informations cachées
            (position, appareil) sont retirées.
          </p>
        </div>
      )}

      {erreur && (
        <Alert variant="destructive">
          <AlertDescription>{erreur}</AlertDescription>
        </Alert>
      )}
    </section>
  );
}
