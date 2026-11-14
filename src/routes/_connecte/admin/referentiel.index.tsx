import { createFileRoute, useRouter } from "@tanstack/react-router";
import { Pencil, Plus, Power } from "lucide-react";
import { useState } from "react";

import {
  BadgeActif,
  CHAMP_ADMIN,
  Champ,
  DialogueFormulaire,
} from "@/components/admin/DialogueFormulaire";
import { ServiceIndisponible } from "@/components/ServiceIndisponible";
import { Button } from "@/components/ui/button";
import {
  adminCreerDre,
  adminCreerIesg,
  adminListerDre,
  adminModifierDre,
  adminModifierIesg,
  type DreAdmin,
  type IesgAdmin,
  type RegionScolaire,
} from "@/lib/api/client";
import { nomRegion, REGIONS_SCOLAIRES } from "@/lib/clubs";

export const Route = createFileRoute("/_connecte/admin/referentiel/")({
  loader: () => adminListerDre(),
  gcTime: 0,
  errorComponent: ServiceIndisponible,
  component: DreEtIesg,
});

// Ce qu'un dialogue ouvert est en train de faire.
type Action =
  | { type: "nouvelle-dre" }
  | { type: "modifier-dre"; dre: DreAdmin }
  | { type: "basculer-dre"; dre: DreAdmin }
  | { type: "nouvelle-iesg"; dre: DreAdmin }
  | { type: "modifier-iesg"; iesg: IesgAdmin }
  | { type: "basculer-iesg"; iesg: IesgAdmin };

const BOUTON_ICONE =
  "inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-bold ring-1 ring-border transition hover:bg-mist-soft";

function DreEtIesg() {
  const { admin } = Route.useRouteContext();
  const dres = Route.useLoaderData();
  const [action, setAction] = useState<Action | null>(null);
  const gere = admin.super_admin;

  return (
    <div className="space-y-5">
      {gere && (
        <Button
          onClick={() => setAction({ type: "nouvelle-dre" })}
          className="btn-fx h-11 rounded-full px-5 font-bold"
        >
          <Plus className="size-4" /> Nouvelle DRE
        </Button>
      )}

      {dres.map((dre) => (
        <section
          key={dre.code}
          aria-labelledby={`dre-${dre.code}`}
          className={`rounded-3xl bg-white p-5 shadow-sm ring-1 ring-border ${dre.actif ? "" : "opacity-70"}`}
        >
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <h2 id={`dre-${dre.code}`} className="flex flex-wrap items-center gap-2 text-2xl">
                <span className="text-logo-blue">DRE</span>
                <span className="text-primary">{dre.nom}</span>
                <BadgeActif actif={dre.actif} />
              </h2>
              <p className="text-sm font-medium text-muted-foreground">
                {dre.nom_complet} · région {nomRegion(dre.region)} · code{" "}
                <code className="font-mono">{dre.code}</code> · ordre {dre.ordre} ·{" "}
                {dre.nb_etablissements} établissements actifs
              </p>
            </div>
            {gere && (
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  className={BOUTON_ICONE}
                  onClick={() => setAction({ type: "modifier-dre", dre })}
                >
                  <Pencil className="size-3.5" /> Modifier
                </button>
                {dre.actif && (
                  <button
                    type="button"
                    className={BOUTON_ICONE}
                    onClick={() => setAction({ type: "nouvelle-iesg", dre })}
                  >
                    <Plus className="size-3.5" /> IESG
                  </button>
                )}
                <button
                  type="button"
                  className={BOUTON_ICONE}
                  onClick={() => setAction({ type: "basculer-dre", dre })}
                >
                  <Power className="size-3.5" /> {dre.actif ? "Désactiver" : "Réactiver"}
                </button>
              </div>
            )}
          </div>

          <div className="mt-4 overflow-x-auto">
            <table className="w-full min-w-[32rem] text-sm">
              <thead className="text-left text-[11px] font-extrabold uppercase tracking-wider text-ink/60">
                <tr>
                  <th scope="col" className="py-2 pr-4">
                    IESG
                  </th>
                  <th scope="col" className="py-2 pr-4">
                    Zone
                  </th>
                  <th scope="col" className="py-2 pr-4 text-right">
                    Établissements actifs
                  </th>
                  {gere && (
                    <th scope="col" className="py-2">
                      <span className="sr-only">Actions</span>
                    </th>
                  )}
                </tr>
              </thead>
              <tbody>
                {dre.iesg.map((iesg) => (
                  <tr key={iesg.id} className={`border-t ${iesg.actif ? "" : "opacity-60"}`}>
                    <td className="py-2.5 pr-4 font-bold">
                      {iesg.nom} <BadgeActif actif={iesg.actif} />
                    </td>
                    <td className="py-2.5 pr-4 text-muted-foreground">{iesg.zone ?? "—"}</td>
                    <td className="py-2.5 pr-4 text-right tabular-nums">
                      {iesg.nb_etablissements}
                    </td>
                    {gere && (
                      <td className="py-2.5 text-right">
                        <div className="inline-flex gap-2">
                          <button
                            type="button"
                            className={BOUTON_ICONE}
                            aria-label={`Modifier ${iesg.nom}`}
                            onClick={() => setAction({ type: "modifier-iesg", iesg })}
                          >
                            <Pencil className="size-3.5" />
                          </button>
                          <button
                            type="button"
                            className={BOUTON_ICONE}
                            aria-label={`${iesg.actif ? "Désactiver" : "Réactiver"} ${iesg.nom}`}
                            onClick={() => setAction({ type: "basculer-iesg", iesg })}
                          >
                            <Power className="size-3.5" />
                          </button>
                        </div>
                      </td>
                    )}
                  </tr>
                ))}
                {dre.iesg.length === 0 && (
                  <tr>
                    <td colSpan={4} className="py-4 text-center text-muted-foreground">
                      Aucune IESG dans cette DRE.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </section>
      ))}

      {action && (
        <Dialogues
          key={JSON.stringify(action)}
          action={action}
          dres={dres}
          fermer={() => setAction(null)}
        />
      )}
    </div>
  );
}

function Dialogues({
  action,
  dres,
  fermer,
}: {
  action: Action;
  dres: DreAdmin[];
  fermer: () => void;
}) {
  const router = useRouter();
  const recharger = () => router.invalidate();
  const commun = { ouvert: true, onOuvert: (o: boolean) => !o && fermer() };

  if (action.type === "nouvelle-dre" || action.type === "modifier-dre") {
    const dre = action.type === "modifier-dre" ? action.dre : null;
    return <FormulaireDre dre={dre} commun={commun} recharger={recharger} />;
  }
  if (action.type === "nouvelle-iesg" || action.type === "modifier-iesg") {
    return (
      <FormulaireIesg
        iesg={action.type === "modifier-iesg" ? action.iesg : null}
        dreCode={action.type === "nouvelle-iesg" ? action.dre.code : action.iesg.dre_code}
        dres={dres}
        commun={commun}
        recharger={recharger}
      />
    );
  }
  if (action.type === "basculer-dre") {
    const { dre } = action;
    return (
      <DialogueFormulaire
        {...commun}
        titre={`${dre.actif ? "Désactiver" : "Réactiver"} la DRE ${dre.nom} ?`}
        description={
          dre.actif
            ? "Elle disparaîtra des listes publiques et des formulaires. Ses IESG doivent d'abord être déplacées ou désactivées, et aucun collaborateur ne doit l'avoir pour périmètre."
            : "Elle réapparaîtra dans les listes publiques et les formulaires."
        }
        bouton={dre.actif ? "Désactiver" : "Réactiver"}
        danger={dre.actif}
        onEnvoie={async () => {
          await adminModifierDre(dre.code, { version: dre.version, actif: !dre.actif });
          await recharger();
        }}
      />
    );
  }
  const { iesg } = action;
  return (
    <DialogueFormulaire
      {...commun}
      titre={`${iesg.actif ? "Désactiver" : "Réactiver"} ${iesg.nom} ?`}
      description={
        iesg.actif
          ? "Ses établissements doivent d'abord être déplacés ou désactivés."
          : "Sa DRE doit être active."
      }
      bouton={iesg.actif ? "Désactiver" : "Réactiver"}
      danger={iesg.actif}
      onEnvoie={async () => {
        await adminModifierIesg(iesg.id, { version: iesg.version, actif: !iesg.actif });
        await recharger();
      }}
    />
  );
}

type Commun = { ouvert: boolean; onOuvert: (o: boolean) => void };

function FormulaireDre({
  dre,
  commun,
  recharger,
}: {
  dre: DreAdmin | null;
  commun: Commun;
  recharger: () => Promise<void>;
}) {
  const [code, setCode] = useState("");
  const [nom, setNom] = useState(dre?.nom ?? "");
  const [nomComplet, setNomComplet] = useState(dre?.nom_complet ?? "");
  const [ordre, setOrdre] = useState(dre ? String(dre.ordre) : "");
  const [region, setRegion] = useState<RegionScolaire>(dre?.region ?? "maritime");

  return (
    <DialogueFormulaire
      {...commun}
      titre={dre ? `Modifier la DRE ${dre.nom}` : "Nouvelle DRE"}
      description={
        dre
          ? "Son code ne change pas : les périmètres des collaborateurs restent valides."
          : "Le code ne pourra plus changer : choisis-le court, en minuscules et tirets."
      }
      bouton="Enregistrer"
      onEnvoie={async () => {
        const champs = {
          nom,
          nom_complet: nomComplet,
          region,
          ordre: ordre ? Number(ordre) : null,
        };
        if (dre) await adminModifierDre(dre.code, { version: dre.version, ...champs });
        else await adminCreerDre({ code, ...champs });
        await recharger();
      }}
    >
      {!dre && (
        <Champ libelle="Code">
          <input
            required
            value={code}
            onChange={(e) => setCode(e.target.value)}
            pattern="[a-z0-9\-]+"
            minLength={2}
            maxLength={30}
            placeholder="ex. grand-lome"
            className={`${CHAMP_ADMIN} font-mono`}
          />
        </Champ>
      )}
      <Champ libelle="Nom court">
        <input
          required
          value={nom}
          onChange={(e) => setNom(e.target.value)}
          maxLength={150}
          className={CHAMP_ADMIN}
        />
      </Champ>
      <Champ libelle="Nom complet">
        <input
          required
          value={nomComplet}
          onChange={(e) => setNomComplet(e.target.value)}
          maxLength={200}
          className={CHAMP_ADMIN}
        />
      </Champ>
      <Champ libelle="Région">
        <select
          value={region}
          onChange={(e) => setRegion(e.target.value as RegionScolaire)}
          className={CHAMP_ADMIN}
        >
          {REGIONS_SCOLAIRES.map((r) => (
            <option key={r.code} value={r.code}>
              {r.nom}
            </option>
          ))}
        </select>
      </Champ>
      <Champ libelle="Ordre d'affichage">
        <input
          type="number"
          min={1}
          max={99}
          value={ordre}
          onChange={(e) => setOrdre(e.target.value)}
          placeholder="À la fin"
          className={CHAMP_ADMIN}
        />
      </Champ>
    </DialogueFormulaire>
  );
}

function FormulaireIesg({
  iesg,
  dreCode,
  dres,
  commun,
  recharger,
}: {
  iesg: IesgAdmin | null;
  dreCode: string;
  dres: DreAdmin[];
  commun: Commun;
  recharger: () => Promise<void>;
}) {
  const [nom, setNom] = useState(iesg?.nom ?? "");
  const [zone, setZone] = useState(iesg?.zone ?? "");
  const [dre, setDre] = useState(dreCode);
  const deplacee = iesg !== null && dre !== iesg.dre_code;

  return (
    <DialogueFormulaire
      {...commun}
      titre={iesg ? `Modifier ${iesg.nom}` : "Nouvelle IESG"}
      description="Son nom doit être unique dans sa DRE. La zone s'affiche sur la carte des clubs."
      bouton={deplacee ? "Déplacer et enregistrer" : "Enregistrer"}
      onEnvoie={async () => {
        if (iesg)
          await adminModifierIesg(iesg.id, {
            version: iesg.version,
            nom,
            zone: zone || null,
            dre_code: dre,
          });
        else await adminCreerIesg({ dre_code: dre, nom, zone: zone || null });
        await recharger();
      }}
    >
      <Champ libelle="Nom">
        <input
          required
          value={nom}
          onChange={(e) => setNom(e.target.value)}
          maxLength={150}
          placeholder="ex. IESG Golfe"
          className={CHAMP_ADMIN}
        />
      </Champ>
      <Champ libelle="Zone (facultatif)">
        <input
          value={zone}
          onChange={(e) => setZone(e.target.value)}
          maxLength={150}
          placeholder="ex. Golfe (Lomé)"
          className={CHAMP_ADMIN}
        />
      </Champ>
      {iesg && (
        <Champ libelle="DRE">
          <select value={dre} onChange={(e) => setDre(e.target.value)} className={CHAMP_ADMIN}>
            {dres
              .filter((d) => d.actif || d.code === iesg.dre_code)
              .map((d) => (
                <option key={d.code} value={d.code}>
                  DRE {d.nom}
                </option>
              ))}
          </select>
        </Champ>
      )}
      {deplacee && (
        <p role="status" className="rounded-2xl bg-sun/25 p-3 text-sm font-bold">
          Ses {iesg.nb_etablissements} établissements actifs changeront de DRE, et leurs futurs
          clubs avec eux.
        </p>
      )}
    </DialogueFormulaire>
  );
}
