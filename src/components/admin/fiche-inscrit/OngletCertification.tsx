import { Link } from "@tanstack/react-router";
import { Check } from "lucide-react";

import { dateCourte } from "@/lib/admin";
import { chargerCertificationInscrit } from "@/lib/api/client";

import { Bloc, Chargement, Chiffres, Pastille, Vide } from "./commun";
import { useChargement } from "./useChargement";

const ETATS = {
  valide: { libelle: "Valide", ton: "vert" },
  revoque: { libelle: "Révoqué", ton: "rouge" },
  remplace: { libelle: "Remplacé", ton: "gris" },
} as const;

// Spec 045 : progression sur les 20 places, badges et certificats.
export function OngletCertification({
  id,
  identifiant,
  peutSuivre,
}: {
  id: string;
  identifiant: string;
  peutSuivre: boolean;
}) {
  const { donnees, erreur } = useChargement(() => chargerCertificationInscrit(id), [id]);

  if (!donnees)
    return (
      <Bloc titre="Certification">
        <Chargement erreur={erreur} />
      </Bloc>
    );

  const reussies = donnees.places.filter((p) => p.reussie_le).length;
  return (
    <div className="space-y-6">
      <Bloc
        titre="Certification Génie Imhotep"
        actions={
          peutSuivre && (
            <Link
              to="/admin/certification/suivi"
              search={{ recherche: identifiant }}
              className="rounded-full px-4 py-2 text-sm font-bold text-logo-blue ring-1 ring-border hover:ring-night/30"
            >
              Voir dans le suivi
            </Link>
          )
        }
      >
        <Chiffres
          chiffres={[
            ["Places réussies", `${reussies} / ${donnees.places.length}`],
            ["Badges", donnees.badges.length],
            ["Certificats", donnees.certificats.length],
          ]}
        />
        <ol className="mt-5 grid grid-cols-4 gap-2 sm:grid-cols-5 md:grid-cols-10">
          {donnees.places.map((p) => (
            <li
              key={p.place}
              title={
                p.reussie_le ? `${p.quiz_titre ?? ""} · ${dateCourte(p.reussie_le)}` : "Non réussie"
              }
              className={`flex aspect-square flex-col items-center justify-center rounded-2xl text-sm font-extrabold ${p.reussie_le ? "bg-logo-blue text-white" : "bg-mist-soft text-muted-foreground"}`}
            >
              {p.reussie_le && <Check className="size-4" aria-hidden />}
              <span>{p.place}</span>
              <span className="sr-only">{p.reussie_le ? " réussie" : " non réussie"}</span>
            </li>
          ))}
        </ol>
        {reussies > 0 && (
          <ol className="mt-4 divide-y text-sm">
            {donnees.places
              .filter((p) => p.reussie_le)
              .map((p) => (
                <li key={p.place} className="flex justify-between gap-4 py-2">
                  <span>
                    <span className="font-bold">Place {p.place}</span> · {p.quiz_titre}
                  </span>
                  <span className="shrink-0 text-muted-foreground">
                    {p.reussie_le && dateCourte(p.reussie_le)}
                  </span>
                </li>
              ))}
          </ol>
        )}
      </Bloc>

      <Bloc titre="Badges">
        {donnees.badges.length === 0 ? (
          <Vide>Aucun badge obtenu.</Vide>
        ) : (
          <ul className="flex flex-wrap gap-3">
            {donnees.badges.map((b) => (
              <li key={b.rang} className="rounded-2xl bg-sun/20 px-4 py-3 text-sm">
                <span className="block font-extrabold">{b.nom}</span>
                <span className="text-muted-foreground">
                  {b.palier} places · {dateCourte(b.obtenu_le)}
                </span>
              </li>
            ))}
          </ul>
        )}
      </Bloc>

      <Bloc titre="Certificats">
        {donnees.certificats.length === 0 ? (
          <Vide>Aucun certificat délivré.</Vide>
        ) : (
          <ol className="divide-y text-sm">
            {donnees.certificats.map((c) => {
              const etat = ETATS[c.etat as keyof typeof ETATS] ?? {
                libelle: c.etat,
                ton: "gris" as const,
              };
              return (
                <li key={c.numero} className="py-3">
                  <span className="flex flex-wrap items-center gap-2 font-bold">
                    <span className="font-mono">{c.numero}</span>
                    <Pastille ton={etat.ton}>{etat.libelle}</Pastille>
                  </span>
                  <span className="block text-muted-foreground">
                    Délivré le {dateCourte(c.delivre_le)} au nom de {c.titulaire}
                  </span>
                  {c.motif && (
                    <span className="block text-muted-foreground">
                      Motif : {c.motif}
                      {c.decide_le && ` · ${dateCourte(c.decide_le)}`}
                    </span>
                  )}
                </li>
              );
            })}
          </ol>
        )}
        <p className="mt-4 text-xs font-medium text-muted-foreground">
          Un certificat garde le nom de sa délivrance. Après une correction du nom, révoque-le puis
          fais-le délivrer de nouveau.
        </p>
      </Bloc>
    </div>
  );
}
