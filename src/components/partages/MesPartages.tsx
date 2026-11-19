import { useQuery } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import { Share2 } from "lucide-react";

import { chargerMesPartages, type PartageAuteur } from "@/lib/api/client";
import { dateCourte } from "@/lib/dates";
import { nomDuReseau } from "@/lib/partages";

const ETATS: Record<PartageAuteur["etat"], { libelle: string; classe: string }> = {
  en_attente: { libelle: "En vérification", classe: "bg-sun/30 text-ink" },
  approuve: { libelle: "Validé", classe: "bg-leaf/15 text-leaf" },
  refuse: { libelle: "Refusé", classe: "bg-logo-red/10 text-logo-red" },
};

// « Mes partages » (spec 044) : les déclarations de la personne, leur état, le motif d'un refus et les points
// crédités. Le lien déclaré n'est montré qu'ici et au modérateur.
export function MesPartages() {
  const partages = useQuery({ queryKey: ["mes-partages"], queryFn: chargerMesPartages });
  const liste = partages.data?.partages ?? [];

  return (
    <section
      id="mes-partages"
      aria-labelledby="titre-mes-partages"
      className="mt-6 scroll-mt-20 rounded-3xl bg-white p-6 shadow-card ring-1 ring-border sm:p-8"
    >
      <h2 id="titre-mes-partages" className="flex items-center gap-2 text-2xl">
        <Share2 aria-hidden className="size-6 text-primary" />
        <span className="text-logo-blue">Mes</span> <span className="text-primary">partages</span>
      </h2>
      {partages.isError ? (
        <p className="mt-3 text-sm text-muted-foreground">
          Tes partages ne sont pas disponibles pour le moment.
        </p>
      ) : partages.isPending ? null : liste.length === 0 ? (
        <p className="mt-3 text-sm text-muted-foreground">
          Partage un article sur tes réseaux, puis déclare le lien de ta publication depuis la page
          de l'article : tu gagnes des points une fois le partage vérifié.{" "}
          <Link to="/articles" className="font-bold text-logo-blue hover:underline">
            Voir les articles
          </Link>
        </p>
      ) : (
        <ul className="mt-4 divide-y">
          {liste.map((p) => {
            const etat = ETATS[p.etat];
            return (
              <li key={p.id} className="py-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="min-w-0 text-sm">
                    <strong className="text-ink">
                      {p.nature === "partage" ? "Partage" : "Republication"} sur{" "}
                      {nomDuReseau(p.reseau)}
                    </strong>
                    <span className="text-muted-foreground">
                      {" · "}
                      {p.article_adresse ? (
                        <Link
                          to="/articles/$adresse"
                          params={{ adresse: p.article_adresse }}
                          className="hover:underline"
                        >
                          {p.article_titre}
                        </Link>
                      ) : (
                        p.article_titre
                      )}
                      {" · "}
                      {dateCourte(p.declare_le)}
                    </span>
                  </p>
                  <span className={`rounded-full px-3 py-1 text-xs font-extrabold ${etat.classe}`}>
                    {etat.libelle}
                    {p.points ? ` · +${p.points}` : ""}
                  </span>
                </div>
                <p className="mt-1 truncate text-xs text-muted-foreground">{p.lien}</p>
                {p.motif && <p className="mt-1 text-sm text-logo-red">Motif : {p.motif}</p>}
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}
