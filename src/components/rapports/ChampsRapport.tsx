import { ExternalLink, FileText } from "lucide-react";

import type { ModeleRapport } from "@/lib/api/client";
import { octetsLisibles, PARTICIPANTS, TEXTES } from "@/lib/rapports";

type Document = { id: string; nom: string; type: string; octets: number };

// Lecture d'un rapport (spec 038) : ses textes, ses participants, ses vidéos et ses documents. Sert à l'auteur, au
// club et au modérateur ; aucun champ n'est du HTML, tout s'affiche en texte simple.
export function ChampsRapport({
  modele,
  donnees,
  documents = [],
  urlDocument,
}: {
  modele: ModeleRapport;
  donnees: Record<string, unknown>;
  documents?: Document[];
  urlDocument?: (id: string) => string;
}) {
  const participants = (donnees["participants"] ?? {}) as Record<string, number | null>;
  const videos = (donnees["videos"] ?? []) as string[];
  const champs = TEXTES[modele].filter((c) => c.cle !== "titre" && texte(donnees[c.cle]));
  const nombres = PARTICIPANTS.filter((p) => typeof participants[p.cle] === "number");
  return (
    <div className="space-y-4">
      {champs.map((c) => (
        <section key={c.cle}>
          <h3 className="text-xs font-extrabold uppercase tracking-wider text-muted-foreground">
            {c.libelle}
          </h3>
          <p className="mt-1 whitespace-pre-line break-words text-ink">{texte(donnees[c.cle])}</p>
        </section>
      ))}
      {modele === "bilan" && typeof donnees["participants_total"] === "number" && (
        <p className="font-semibold">
          Participants cumulés sur le semestre : {donnees["participants_total"] as number}
        </p>
      )}
      {nombres.length > 0 && (
        <section>
          <h3 className="text-xs font-extrabold uppercase tracking-wider text-muted-foreground">
            Participation
          </h3>
          <ul className="mt-1 flex flex-wrap gap-2">
            {nombres.map((p) => (
              <li key={p.cle} className="rounded-full bg-mist-soft px-3 py-1 text-sm font-semibold">
                {p.libelle} : {participants[p.cle]}
              </li>
            ))}
          </ul>
        </section>
      )}
      {videos.length > 0 && (
        <section>
          <h3 className="text-xs font-extrabold uppercase tracking-wider text-muted-foreground">
            Vidéos
          </h3>
          <ul className="mt-1 space-y-1">
            {videos.map((v) => (
              <li key={v}>
                <a
                  href={`https://www.youtube.com/watch?v=${encodeURIComponent(v)}`}
                  target="_blank"
                  rel="noreferrer noopener"
                  className="inline-flex items-center gap-1 font-bold text-logo-blue underline-offset-4 hover:underline"
                >
                  Vidéo YouTube {v} <ExternalLink className="size-3.5" />
                </a>
              </li>
            ))}
          </ul>
        </section>
      )}
      {documents.length > 0 && urlDocument && (
        <section>
          <h3 className="text-xs font-extrabold uppercase tracking-wider text-muted-foreground">
            Documents
          </h3>
          <ul className="mt-1 space-y-1">
            {documents.map((d) => (
              <li key={d.id}>
                <a
                  href={urlDocument(d.id)}
                  download
                  className="inline-flex items-center gap-2 font-bold text-logo-blue underline-offset-4 hover:underline"
                >
                  <FileText className="size-4" /> {d.nom}
                  <span className="text-xs font-semibold text-muted-foreground">
                    {d.type.toUpperCase()} · {octetsLisibles(d.octets)}
                  </span>
                </a>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}

const texte = (valeur: unknown) => (typeof valeur === "string" ? valeur.trim() : "");
