import { useNavigate } from "@tanstack/react-router";
import { FileUp, ImagePlus, Save, Send, Trash2, X } from "lucide-react";
import { useState, type ReactNode } from "react";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  envoyerPieceRapport,
  ErreurApi,
  MESSAGE_INDISPONIBLE,
  modifierRapport,
  retirerPieceRapport,
  soumettreRapport,
  supprimerRapport,
  urlDocumentRapport,
  urlPhotoRapport,
  type AxePublic,
  type RapportDetail,
  type RapportResume,
  type SemestreRapport,
  type SortePiece,
  type TypeActivite,
} from "@/lib/api/client";
import { MODELES, octetsLisibles, PARTICIPANTS, RAPPEL_NOMS, TEXTES } from "@/lib/rapports";

type Donnees = Record<string, unknown>;

const vers = (valeur: string) => (valeur.trim() === "" ? null : Number(valeur));

// Le formulaire d'un rapport (spec 038) : brouillon ou version à corriger. Enregistrer garde un brouillon
// incomplet ; soumettre vérifie les champs obligatoires côté API, qui garde la main sur tout.
export function FormulaireRapport({
  rapport: initial,
  axes,
  types,
  semestres,
  activites = [],
}: {
  // Spec 038 : les rapports d'activité du club, rappelés dans un mensuel pour le mois choisi.
  activites?: RapportResume[];
  rapport: RapportDetail;
  axes: AxePublic[];
  types: TypeActivite[];
  semestres: SemestreRapport[];
}) {
  const navigate = useNavigate();
  const [rapport, setRapport] = useState(initial);
  const [donnees, setDonnees] = useState<Donnees>(initial.donnees);
  const [erreur, setErreur] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [occupe, setOccupe] = useState(false);
  const [attestation, setAttestation] = useState(false);
  const modele = rapport.modele;
  const participants = (donnees["participants"] ?? {}) as Record<string, number | null>;
  const videos = ((donnees["videos"] ?? []) as string[]).join("\n");

  const changer = (cle: string, valeur: unknown) => setDonnees((d) => ({ ...d, [cle]: valeur }));
  const action = async (faire: () => Promise<RapportDetail | void>, succes?: string) => {
    setErreur(null);
    setMessage(null);
    setOccupe(true);
    try {
      const nouveau = await faire();
      if (nouveau) {
        setRapport(nouveau);
        setDonnees(nouveau.donnees);
      }
      if (succes) setMessage(succes);
    } catch (e) {
      setErreur(e instanceof ErreurApi ? e.message : MESSAGE_INDISPONIBLE);
    } finally {
      setOccupe(false);
    }
  };
  const enregistrer = () => modifierRapport(rapport.id, rapport.version, donnees);
  const envoyer = (sorte: SortePiece) => (evenement: React.ChangeEvent<HTMLInputElement>) => {
    const fichier = evenement.target.files?.[0];
    evenement.target.value = "";
    if (!fichier) return;
    void action(async () => {
      const enregistre = await enregistrer();
      return envoyerPieceRapport(rapport.id, sorte, { fichier, version: enregistre.version });
    });
  };

  return (
    <div className="space-y-6">
      <Alert>
        <AlertDescription>
          {RAPPEL_NOMS} {MODELES[modele].points}
        </AlertDescription>
      </Alert>

      {modele === "activite" && (
        <div className="grid gap-4 sm:grid-cols-3">
          <Bloc libelle="Date de l'activité *" id="date_activite">
            <Input
              id="date_activite"
              type="date"
              value={(donnees["date_activite"] as string | null) ?? ""}
              onChange={(e) => changer("date_activite", e.target.value || null)}
            />
          </Bloc>
          <Bloc libelle="Type d'activité *" id="type_activite">
            <Choix
              id="type_activite"
              valeur={donnees["type_activite"] as string | null}
              options={types.map((t) => ({ valeur: t.code, libelle: t.libelle }))}
              onChange={(v) => changer("type_activite", v)}
            />
          </Bloc>
          <Bloc libelle="Axe *" id="axe_code">
            <Choix
              id="axe_code"
              valeur={donnees["axe_code"] as string | null}
              options={axes.map((a) => ({ valeur: a.code, libelle: a.libelle }))}
              onChange={(v) => changer("axe_code", v)}
            />
          </Bloc>
        </div>
      )}
      {modele === "mensuel" && (
        <Bloc libelle="Mois *" id="mois">
          <Input
            id="mois"
            type="month"
            className="max-w-xs"
            value={((donnees["mois"] as string | null) ?? "").slice(0, 7)}
            onChange={(e) => changer("mois", e.target.value ? `${e.target.value}-01` : null)}
          />
        </Bloc>
      )}
      {modele === "mensuel" && typeof donnees["mois"] === "string" && (
        <RappelDuMois mois={donnees["mois"]} activites={activites} />
      )}
      {modele === "bilan" && (
        <Bloc libelle="Semestre *" id="semestre_id">
          <Choix
            id="semestre_id"
            valeur={donnees["semestre_id"] as string | null}
            options={semestres.map((s) => ({ valeur: s.id, libelle: s.libelle }))}
            onChange={(v) => changer("semestre_id", v)}
          />
        </Bloc>
      )}

      {TEXTES[modele].map((c) => (
        <Bloc key={c.cle} libelle={`${c.libelle}${c.obligatoire ? " *" : ""}`} id={c.cle}>
          {c.long ? (
            <Textarea
              id={c.cle}
              rows={4}
              maxLength={5000}
              value={(donnees[c.cle] as string | undefined) ?? ""}
              onChange={(e) => changer(c.cle, e.target.value)}
            />
          ) : (
            <Input
              id={c.cle}
              maxLength={200}
              value={(donnees[c.cle] as string | undefined) ?? ""}
              onChange={(e) => changer(c.cle, e.target.value)}
            />
          )}
        </Bloc>
      ))}

      {modele === "activite" && (
        <fieldset className="rounded-2xl bg-mist-soft p-4">
          <legend className="px-1 text-sm font-extrabold text-ink">Participation</legend>
          <div className="grid gap-3 sm:grid-cols-5">
            {PARTICIPANTS.map((p) => (
              <Bloc
                key={p.cle}
                libelle={`${p.libelle}${p.cle === "total" ? " *" : ""}`}
                id={`participants-${p.cle}`}
              >
                <Input
                  id={`participants-${p.cle}`}
                  type="number"
                  min={0}
                  inputMode="numeric"
                  value={participants[p.cle] ?? ""}
                  onChange={(e) =>
                    changer("participants", { ...participants, [p.cle]: vers(e.target.value) })
                  }
                />
              </Bloc>
            ))}
          </div>
        </fieldset>
      )}
      {modele === "bilan" && (
        <Bloc libelle="Participants cumulés sur le semestre" id="participants_total">
          <Input
            id="participants_total"
            type="number"
            min={0}
            className="max-w-xs"
            value={(donnees["participants_total"] as number | null) ?? ""}
            onChange={(e) => changer("participants_total", vers(e.target.value))}
          />
        </Bloc>
      )}

      <Bloc
        libelle="Vidéos YouTube (un lien par ligne, 5 au plus)"
        id="videos"
        aide="Les vidéos ne sont jamais envoyées sur la plateforme : publie-les sur YouTube et colle le lien."
      >
        <Textarea
          id="videos"
          rows={2}
          value={videos}
          onChange={(e) =>
            changer(
              "videos",
              e.target.value
                .split("\n")
                .map((v) => v.trim())
                .filter(Boolean),
            )
          }
        />
      </Bloc>

      <section className="space-y-3 rounded-2xl bg-card p-4 ring-1 ring-border">
        <h2 className="font-display text-lg text-logo-blue">Justificatifs</h2>
        <p className="text-sm text-muted-foreground">
          Photos JPEG, PNG ou WebP (5 au plus, 8 Mo chacune) ; documents PDF ou Word .docx (5 au
          plus, 10 Mo chacun). Le PDF est conseillé.
        </p>
        <ul className="space-y-2">
          {rapport.documents.map((d) => (
            <li key={d.id} className="flex flex-wrap items-center gap-2 text-sm">
              <a
                href={urlDocumentRapport(rapport.id, d.id)}
                download
                className="font-bold text-logo-blue hover:underline"
              >
                {d.nom}
              </a>
              <span className="text-muted-foreground">{octetsLisibles(d.octets)}</span>
              <Retirer
                libelle={`Retirer ${d.nom}`}
                onClick={() =>
                  action(async () =>
                    retirerPieceRapport(
                      rapport.id,
                      "documents",
                      d.id,
                      (await enregistrer()).version,
                    ),
                  )
                }
              />
            </li>
          ))}
        </ul>
        {rapport.photos.length > 0 && (
          <ul className="grid grid-cols-2 gap-2 sm:grid-cols-4">
            {rapport.photos.map((p) => (
              <li key={p.id} className="relative">
                <img
                  src={urlPhotoRapport(rapport.id, p.id, "vignette")}
                  alt={p.legende ?? "Photo de l'activité"}
                  className="aspect-[4/3] w-full rounded-xl object-cover"
                  loading="lazy"
                />
                <div className="absolute right-1 top-1">
                  <Retirer
                    libelle="Retirer cette photo"
                    onClick={() =>
                      action(async () =>
                        retirerPieceRapport(
                          rapport.id,
                          "photos",
                          p.id,
                          (await enregistrer()).version,
                        ),
                      )
                    }
                  />
                </div>
              </li>
            ))}
          </ul>
        )}
        <div className="flex flex-wrap items-center gap-3">
          <Label className="inline-flex cursor-pointer items-center gap-2 rounded-full bg-white px-4 py-2 font-bold ring-1 ring-border">
            <FileUp className="size-4" /> Ajouter un document
            <input
              type="file"
              accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
              className="sr-only"
              disabled={occupe}
              onChange={envoyer("documents")}
            />
          </Label>
          <Label
            className={`inline-flex items-center gap-2 rounded-full bg-white px-4 py-2 font-bold ring-1 ring-border ${attestation ? "cursor-pointer" : "cursor-not-allowed opacity-50"}`}
          >
            <ImagePlus className="size-4" /> Ajouter une photo
            <input
              type="file"
              accept="image/jpeg,image/png,image/webp"
              className="sr-only"
              disabled={occupe || !attestation}
              onChange={envoyer("photos")}
            />
          </Label>
        </div>
        <label className="flex items-start gap-2 text-sm">
          <Checkbox
            checked={attestation}
            onCheckedChange={(v) => setAttestation(v === true)}
            className="mt-0.5"
          />
          Les personnes photographiées, ou leurs parents pour les mineurs, ont accepté la prise de
          vue.
        </label>
      </section>

      {erreur && (
        <p role="alert" className="font-semibold text-logo-red">
          {erreur}
        </p>
      )}
      {message && (
        <p role="status" className="font-semibold text-leaf">
          {message}
        </p>
      )}

      <div className="flex flex-wrap gap-2 border-t pt-4">
        <Button
          variant="outline"
          className="rounded-full font-bold"
          disabled={occupe}
          onClick={() => action(enregistrer, "Brouillon enregistré.")}
        >
          <Save className="size-4" /> Enregistrer
        </Button>
        <Button
          className="btn-fx rounded-full font-bold"
          disabled={occupe}
          onClick={() =>
            action(async () => {
              const enregistre = await enregistrer();
              const soumis = await soumettreRapport(rapport.id, enregistre.version);
              await navigate({ to: "/rapports/$id", params: { id: soumis.id } });
              return soumis;
            })
          }
        >
          <Send className="size-4" /> Soumettre à l'équipe
        </Button>
        {rapport.reference === null && (
          <Button
            variant="ghost"
            className="rounded-full font-bold text-logo-red"
            disabled={occupe}
            onClick={() =>
              action(async () => {
                if (!window.confirm("Supprimer ce brouillon et ses fichiers ?")) return;
                await supprimerRapport(rapport.id);
                await navigate({ to: "/rapports" });
              })
            }
          >
            <Trash2 className="size-4" /> Supprimer le brouillon
          </Button>
        )}
      </div>
    </div>
  );
}

function RappelDuMois({ mois, activites }: { mois: string; activites: RapportResume[] }) {
  // La période d'un rapport d'activité s'écrit JJ/MM/AAAA ; le mois choisi, AAAA-MM-01.
  const suffixe = `/${mois.slice(5, 7)}/${mois.slice(0, 4)}`;
  const duMois = activites.filter((r) => r.periode?.endsWith(suffixe));
  return (
    <section className="rounded-2xl bg-mist-soft p-4 text-sm">
      <h2 className="font-bold text-ink">Rapports d'activité du club ce mois-là</h2>
      {duMois.length === 0 ? (
        <p className="mt-1 text-muted-foreground">Aucun rapport d'activité soumis pour ce mois.</p>
      ) : (
        <ul className="mt-1 list-disc pl-5">
          {duMois.map((r) => (
            <li key={r.id}>
              {r.reference} · {r.periode} · {r.titre}
            </li>
          ))}
        </ul>
      )}
      <p className="mt-2 text-xs text-muted-foreground">
        Ils gardent leurs propres points : le mensuel en fait la synthèse, sans les redonner.
      </p>
    </section>
  );
}

function Bloc({
  libelle,
  id,
  aide,
  children,
}: {
  libelle: string;
  id: string;
  aide?: string;
  children: ReactNode;
}) {
  return (
    <div className="space-y-1.5">
      <Label htmlFor={id} className="font-bold">
        {libelle}
      </Label>
      {children}
      {aide && <p className="text-xs text-muted-foreground">{aide}</p>}
    </div>
  );
}

function Choix({
  id,
  valeur,
  options,
  onChange,
}: {
  id: string;
  valeur: string | null;
  options: { valeur: string; libelle: string }[];
  onChange: (valeur: string | null) => void;
}) {
  return (
    <select
      id={id}
      value={valeur ?? ""}
      onChange={(e) => onChange(e.target.value || null)}
      className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
    >
      <option value="">Choisis…</option>
      {options.map((o) => (
        <option key={o.valeur} value={o.valeur}>
          {o.libelle}
        </option>
      ))}
    </select>
  );
}

function Retirer({ libelle, onClick }: { libelle: string; onClick: () => void }) {
  return (
    <button
      type="button"
      aria-label={libelle}
      title={libelle}
      onClick={onClick}
      className="rounded-full bg-white p-1 text-logo-red shadow ring-1 ring-border hover:bg-logo-red/10"
    >
      <X className="size-3.5" />
    </button>
  );
}
