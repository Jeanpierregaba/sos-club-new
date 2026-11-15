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
  adminCreerTypeActivite,
  adminListerTypesActivite,
  adminModifierTypeActivite,
  type TypeActiviteAdmin,
} from "@/lib/api/client";

export const Route = createFileRoute("/_connecte/admin/referentiel/types-activite")({
  loader: () => adminListerTypesActivite(),
  gcTime: 0,
  errorComponent: ServiceIndisponible,
  component: TypesActivite,
});

type Action = { type: "nouveau" } | { type: "modifier" | "basculer"; axe: TypeActiviteAdmin };

const BOUTON =
  "inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-bold ring-1 ring-border transition hover:bg-mist-soft";

function TypesActivite() {
  const { admin } = Route.useRouteContext();
  const types = Route.useLoaderData();
  const router = useRouter();
  const [action, setAction] = useState<Action | null>(null);
  const fermer = () => setAction(null);

  return (
    <div className="space-y-5">
      <p className="max-w-3xl text-sm font-medium text-muted-foreground">
        Les types d'activité classent les rapports d'activité des clubs (spec 038). Un type
        désactivé reste sur les rapports déjà déposés, mais ne se choisit plus.
      </p>
      {admin.super_admin && (
        <Button
          onClick={() => setAction({ type: "nouveau" })}
          className="btn-fx h-11 rounded-full px-5 font-bold"
        >
          <Plus className="size-4" /> Nouveau type
        </Button>
      )}

      <ol className="grid gap-3">
        {types.map((axe) => (
          <li
            key={axe.code}
            className={`flex flex-wrap items-start gap-4 rounded-3xl bg-white p-5 shadow-sm ring-1 ring-border ${axe.actif ? "" : "opacity-60"}`}
          >
            <span className="font-display text-3xl leading-none text-primary tabular-nums">
              {axe.ordre}
            </span>
            <div className="min-w-0 flex-1">
              <p className="flex flex-wrap items-center gap-2 font-extrabold text-logo-blue">
                {axe.libelle} <BadgeActif actif={axe.actif} />
              </p>
              <code className="mt-1 block font-mono text-xs text-muted-foreground">{axe.code}</code>
            </div>
            {admin.super_admin && (
              <div className="flex gap-2">
                <button
                  type="button"
                  className={BOUTON}
                  onClick={() => setAction({ type: "modifier", axe })}
                >
                  <Pencil className="size-3.5" /> Modifier
                </button>
                <button
                  type="button"
                  className={BOUTON}
                  onClick={() => setAction({ type: "basculer", axe })}
                >
                  <Power className="size-3.5" /> {axe.actif ? "Désactiver" : "Réactiver"}
                </button>
              </div>
            )}
          </li>
        ))}
      </ol>

      {action?.type === "basculer" && (
        <DialogueFormulaire
          ouvert
          onOuvert={(o) => !o && fermer()}
          titre={`${action.axe.actif ? "Désactiver" : "Réactiver"} le type ${action.axe.libelle} ?`}
          description={
            action.axe.actif
              ? "Il ne se choisira plus pour un nouveau rapport. Il faut garder au moins un type actif."
              : "Il se choisira de nouveau pour les rapports."
          }
          bouton={action.axe.actif ? "Désactiver" : "Réactiver"}
          danger={action.axe.actif}
          onEnvoie={async () => {
            await adminModifierTypeActivite(action.axe.code, {
              version: action.axe.version,
              actif: !action.axe.actif,
            });
            await router.invalidate();
          }}
        />
      )}
      {(action?.type === "nouveau" || action?.type === "modifier") && (
        <FormulaireType
          key={action.type === "modifier" ? action.axe.code : "nouveau"}
          axe={action.type === "modifier" ? action.axe : null}
          fermer={fermer}
        />
      )}
    </div>
  );
}

function FormulaireType({ axe, fermer }: { axe: TypeActiviteAdmin | null; fermer: () => void }) {
  const router = useRouter();
  const [code, setCode] = useState("");
  const [libelle, setLibelle] = useState(axe?.libelle ?? "");
  const [ordre, setOrdre] = useState(axe ? String(axe.ordre) : "");

  return (
    <DialogueFormulaire
      ouvert
      onOuvert={(o) => !o && fermer()}
      titre={axe ? `Modifier le type ${axe.libelle}` : "Nouveau type d'activité"}
      description={
        axe
          ? "Son code ne change pas : les rapports déjà déposés le gardent."
          : "Le code ne pourra plus changer : choisis-le court, en minuscules et tirets."
      }
      bouton="Enregistrer"
      onEnvoie={async () => {
        const champs = { libelle, ordre: ordre ? Number(ordre) : null };
        if (axe) await adminModifierTypeActivite(axe.code, { version: axe.version, ...champs });
        else await adminCreerTypeActivite({ code, ...champs });
        await router.invalidate();
      }}
    >
      {!axe && (
        <Champ libelle="Code">
          <input
            required
            value={code}
            onChange={(e) => setCode(e.target.value)}
            pattern="[a-z0-9\-]+"
            minLength={2}
            maxLength={40}
            placeholder="ex. forum-sante"
            className={`${CHAMP_ADMIN} font-mono`}
          />
        </Champ>
      )}
      <Champ libelle="Libellé">
        <input
          required
          value={libelle}
          onChange={(e) => setLibelle(e.target.value)}
          maxLength={120}
          className={CHAMP_ADMIN}
        />
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
