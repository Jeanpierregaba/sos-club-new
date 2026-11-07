import { useState } from "react";

import { Dialog, DialogContent, DialogDescription, DialogTitle } from "@/components/ui/dialog";
import { urlPhotoPublique, type PhotoPublique } from "@/lib/api/client";

// La couverture d'un article publié (spec 024). Les dimensions fixées évitent tout saut de mise en page.
export function Couverture({
  adresse,
  photo,
  taille = "grande",
  className = "",
}: {
  adresse: string;
  photo: PhotoPublique;
  taille?: "grande" | "vignette";
  className?: string;
}) {
  return (
    <img
      src={urlPhotoPublique(adresse, photo.id, taille)}
      alt={photo.legende ?? ""}
      width={photo.largeur}
      height={photo.hauteur}
      loading={taille === "vignette" ? "lazy" : "eager"}
      decoding="async"
      className={`h-auto w-full object-cover ${className}`}
    />
  );
}

// Les autres photos, en galerie sous le texte : vignettes chargées à la demande, la grande au clic.
export function Galerie({ adresse, photos }: { adresse: string; photos: PhotoPublique[] }) {
  const [ouverte, setOuverte] = useState<PhotoPublique | null>(null);
  if (photos.length === 0) return null;

  return (
    <section aria-label="Photos de l'article" className="mt-10">
      <ul className="grid grid-cols-2 gap-3 sm:grid-cols-3">
        {photos.map((p) => (
          <li key={p.id}>
            <figure>
              <button
                type="button"
                onClick={() => setOuverte(p)}
                className="block w-full overflow-hidden rounded-2xl bg-mist"
                aria-label={p.legende ? `Agrandir : ${p.legende}` : "Agrandir la photo"}
              >
                <img
                  src={urlPhotoPublique(adresse, p.id, "vignette")}
                  alt={p.legende ?? ""}
                  width={p.largeur}
                  height={p.hauteur}
                  loading="lazy"
                  decoding="async"
                  className="aspect-[4/3] w-full object-cover transition hover:scale-105"
                />
              </button>
              {p.legende && (
                <figcaption className="mt-1.5 text-sm text-muted-foreground">
                  {p.legende}
                </figcaption>
              )}
            </figure>
          </li>
        ))}
      </ul>

      <Dialog open={ouverte !== null} onOpenChange={(o) => !o && setOuverte(null)}>
        <DialogContent className="max-h-[95dvh] w-full max-w-4xl overflow-y-auto p-3 sm:p-4">
          <DialogTitle className="sr-only">{ouverte?.legende ?? "Photo de l'article"}</DialogTitle>
          <DialogDescription className="sr-only">Photo agrandie</DialogDescription>
          {ouverte && (
            <figure>
              <Couverture adresse={adresse} photo={ouverte} className="rounded-xl" />
              {ouverte.legende && (
                <figcaption className="mt-2 text-sm text-muted-foreground">
                  {ouverte.legende}
                </figcaption>
              )}
            </figure>
          )}
        </DialogContent>
      </Dialog>
    </section>
  );
}
