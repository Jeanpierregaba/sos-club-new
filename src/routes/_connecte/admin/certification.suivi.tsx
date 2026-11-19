import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { Download, Search, X } from "lucide-react";
import { useState } from "react";

import { CHAMP_ADMIN, Champ, DialogueFormulaire } from "@/components/admin/DialogueFormulaire";
import { SuiviCertification } from "@/components/admin/SuiviCertification";
import { ServiceIndisponible } from "@/components/ServiceIndisponible";
import { peut } from "@/lib/admin";
import {
  chargerCandidatsCertification,
  chargerStatistiquesCertification,
  exporterCandidatsCertification,
  type CandidatCertification,
} from "@/lib/api/client";

const PAR_PAGE = 25;
const ETATS = { en_cours: "En cours", inactif: "Inactifs depuis 30 jours", certifie: "Certifiés" };
const ROLES = { eleve: "Élèves", encadreur: "Encadreurs" };

type Recherche = {
  dre?: string | undefined;
  club_id?: string | undefined;
  club?: string | undefined;
  role?: "eleve" | "encadreur" | undefined;
  etat?: "en_cours" | "inactif" | "certifie" | undefined;
  recherche?: string | undefined;
  page?: number | undefined;
};

const texte = (s: Record<string, unknown>, cle: string) =>
  typeof s[cle] === "string" && s[cle] ? { [cle]: s[cle] as string } : {};

// Suivi des certifications (spec 043) : chiffres, entonnoir des 20 places et candidats.
export const Route = createFileRoute("/_connecte/admin/certification/suivi")({
  validateSearch: (s: Record<string, unknown>): Recherche => ({
    ...texte(s, "dre"),
    ...texte(s, "club_id"),
    ...texte(s, "club"),
    ...texte(s, "recherche"),
    ...(s["role"] === "eleve" || s["role"] === "encadreur" ? { role: s["role"] } : {}),
    ...(s["etat"] === "en_cours" || s["etat"] === "inactif" || s["etat"] === "certifie"
      ? { etat: s["etat"] }
      : {}),
    ...(Number(s["page"]) > 1 ? { page: Math.floor(Number(s["page"])) } : {}),
  }),
  loaderDeps: ({ search }) => search,
  loader: async ({ deps }) => {
    const { club: _club, page = 1, ...filtres } = deps;
    const [stats, candidats] = await Promise.all([
      chargerStatistiquesCertification(),
      chargerCandidatsCertification({ ...filtres, page, par_page: PAR_PAGE }),
    ]);
    return { stats, candidats };
  },
  gcTime: 0,
  errorComponent: ServiceIndisponible,
  component: Suivi,
});

const date = (iso: string) =>
  new Date(iso).toLocaleDateString("fr-FR", { day: "numeric", month: "short", year: "numeric" });

function Etat({ c }: { c: CandidatCertification }) {
  if (c.certificat)
    return (
      <span className="rounded-full bg-leaf/15 px-2 py-0.5 text-xs font-bold text-night">
        Certifié · {c.certificat}
      </span>
    );
  return (
    <span className="text-xs font-semibold">
      Place {c.place_en_cours} · {c.tentatives_place} tentative{c.tentatives_place > 1 ? "s" : ""}
    </span>
  );
}

function Suivi() {
  const { admin } = Route.useRouteContext();
  const { stats, candidats } = Route.useLoaderData();
  const filtres = Route.useSearch();
  const naviguer = useNavigate({ from: Route.fullPath });
  const [saisie, setSaisie] = useState(filtres.recherche ?? "");
  const [export_, setExport] = useState(false);
  const [finalite, setFinalite] = useState("");
  const exporter = peut(admin, "inscrits", "exporter") && admin.perimetre_dre === null;
  const pages = Math.max(1, Math.ceil(candidats.total / PAR_PAGE));
  const page = filtres.page ?? 1;

  const filtrer = (changement: Partial<Recherche>) =>
    naviguer({ search: (avant) => ({ ...avant, ...changement, page: undefined }) });

  const { club: _club, page: _page, ...filtresApi } = filtres;

  return (
    <div className="space-y-6">
      <SuiviCertification stats={stats} />

      <section className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h2 className="text-xl font-extrabold">
            Candidats ({candidats.total.toLocaleString("fr-FR")})
          </h2>
          {exporter && (
            <button
              type="button"
              onClick={() => setExport(true)}
              className="inline-flex min-h-11 items-center gap-1.5 rounded-full px-4 py-2 text-sm font-bold ring-1 ring-border transition hover:bg-mist-soft"
            >
              <Download className="size-4" /> Exporter
            </button>
          )}
        </div>

        <form
          className="flex flex-wrap items-center gap-2"
          onSubmit={(e) => {
            e.preventDefault();
            filtrer({ recherche: saisie.trim() || undefined });
          }}
        >
          <label className="relative min-w-0 flex-1 basis-56">
            <span className="sr-only">Chercher un candidat</span>
            <Search className="pointer-events-none absolute top-3.5 left-3 size-4 text-muted-foreground" />
            <input
              type="search"
              value={saisie}
              onChange={(e) => setSaisie(e.target.value)}
              placeholder={admin.perimetre_dre ? "Pseudonyme" : "Nom ou pseudonyme"}
              className={`${CHAMP_ADMIN} pl-9`}
            />
          </label>
          {stats.par_dre.length > 1 && (
            <select
              aria-label="DRE"
              value={filtres.dre ?? ""}
              onChange={(e) => filtrer({ dre: e.target.value || undefined })}
              className={`${CHAMP_ADMIN} w-auto`}
            >
              <option value="">Toutes les DRE</option>
              {stats.par_dre.map((d) => (
                <option key={d.code} value={d.code}>
                  DRE {d.dre}
                </option>
              ))}
            </select>
          )}
          <select
            aria-label="Rôle"
            value={filtres.role ?? ""}
            onChange={(e) => filtrer({ role: (e.target.value || undefined) as Recherche["role"] })}
            className={`${CHAMP_ADMIN} w-auto`}
          >
            <option value="">Élèves et encadreurs</option>
            {Object.entries(ROLES).map(([cle, libelle]) => (
              <option key={cle} value={cle}>
                {libelle}
              </option>
            ))}
          </select>
          <select
            aria-label="État"
            value={filtres.etat ?? ""}
            onChange={(e) => filtrer({ etat: (e.target.value || undefined) as Recherche["etat"] })}
            className={`${CHAMP_ADMIN} w-auto`}
          >
            <option value="">Tous les états</option>
            {Object.entries(ETATS).map(([cle, libelle]) => (
              <option key={cle} value={cle}>
                {libelle}
              </option>
            ))}
          </select>
        </form>

        {filtres.club_id && (
          <button
            type="button"
            onClick={() => filtrer({ club_id: undefined, club: undefined })}
            aria-label={`Retirer le filtre du club ${filtres.club ?? ""}`}
            className="inline-flex min-h-11 items-center gap-1.5 rounded-full bg-night px-4 py-2 text-xs font-bold text-white"
          >
            Club : {filtres.club ?? "choisi"} <X className="size-3.5" />
          </button>
        )}

        {candidats.candidats.length === 0 ? (
          <p className="rounded-3xl border border-dashed p-8 text-center font-semibold text-muted-foreground">
            {stats.totaux.candidats === 0
              ? "Personne n'a encore commencé la certification."
              : "Aucun candidat ne correspond à ces filtres."}
          </p>
        ) : (
          <ul className="grid gap-3">
            {candidats.candidats.map((c) => (
              <li
                key={c.id}
                className="grid gap-2 rounded-3xl bg-white p-4 shadow-sm ring-1 ring-border md:grid-cols-[1.4fr_1fr_1fr] md:items-center md:p-5"
              >
                <div className="min-w-0">
                  <p className="font-extrabold break-words">
                    {c.nom}
                    {c.pseudonyme && c.nom !== c.pseudonyme && (
                      <span className="font-semibold text-muted-foreground"> · {c.pseudonyme}</span>
                    )}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {c.role === "eleve" ? (c.ancien_eleve ? "Ancien élève" : "Élève") : "Encadreur"}
                    {c.etablissement && ` · ${c.etablissement}`}
                    {c.dre && ` · DRE ${c.dre}`}
                  </p>
                  {c.club ? (
                    <button
                      type="button"
                      onClick={() => filtrer({ club_id: c.club!.id, club: c.club!.nom })}
                      className="mt-1 text-left text-xs font-bold text-logo-blue underline"
                    >
                      {c.club.nom}
                    </button>
                  ) : (
                    <p className="mt-1 text-xs text-muted-foreground">Sans club</p>
                  )}
                </div>
                <div>
                  <p className="text-sm font-extrabold">
                    {c.places_validees}/20 places · {c.badges.length}/5 badges
                  </p>
                  <Etat c={c} />
                </div>
                <div className="text-xs text-muted-foreground">
                  <p>
                    {c.tentatives} tentative{c.tentatives > 1 ? "s" : ""} depuis le {date(c.debut)}
                  </p>
                  <p className="font-semibold text-night">
                    Dernière activité : {date(c.derniere_activite)}
                  </p>
                </div>
              </li>
            ))}
          </ul>
        )}

        {pages > 1 && (
          <nav aria-label="Pages des candidats" className="flex items-center justify-center gap-2">
            <button
              type="button"
              disabled={page <= 1}
              onClick={() => naviguer({ search: (avant) => ({ ...avant, page: page - 1 }) })}
              className="min-h-11 rounded-full px-4 text-sm font-bold ring-1 ring-border disabled:opacity-40"
            >
              Précédente
            </button>
            <span className="text-sm font-semibold">
              Page {page} sur {pages}
            </span>
            <button
              type="button"
              disabled={page >= pages}
              onClick={() => naviguer({ search: (avant) => ({ ...avant, page: page + 1 }) })}
              className="min-h-11 rounded-full px-4 text-sm font-bold ring-1 ring-border disabled:opacity-40"
            >
              Suivante
            </button>
          </nav>
        )}
      </section>

      {exporter && (
        <DialogueFormulaire
          ouvert={export_}
          onOuvert={setExport}
          titre="Exporter les candidats"
          description="Le fichier contient les noms des candidats, avec les filtres en cours. L'export est inscrit au journal avec sa finalité."
          bouton="Télécharger le CSV"
          desactive={finalite.trim().length < 5}
          onEnvoie={async () => {
            const fichier = await exporterCandidatsCertification(filtresApi, finalite.trim());
            const lien = document.createElement("a");
            lien.href = URL.createObjectURL(fichier);
            lien.download = "suivi-certification.csv";
            lien.click();
            URL.revokeObjectURL(lien.href);
            setFinalite("");
          }}
        >
          <Champ libelle="Finalité de l'export">
            <textarea
              value={finalite}
              onChange={(e) => setFinalite(e.target.value)}
              rows={3}
              maxLength={300}
              placeholder="Ex. : relancer les candidats inactifs de la DRE Kara"
              className="w-full rounded-xl border bg-white p-3 text-sm font-semibold outline-none focus:border-logo-blue"
            />
          </Champ>
        </DialogueFormulaire>
      )}
    </div>
  );
}
