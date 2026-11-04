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
import { Textarea } from "@/components/ui/textarea";
import { adminCreerAxe, adminListerAxes, adminModifierAxe, type AxeAdmin } from "@/lib/api/client";

export const Route = createFileRoute("/_connecte/admin/referentiel/axes")({
  loader: () => adminListerAxes(),
  gcTime: 0,
  errorComponent: ServiceIndisponible,
  component: Axes,
});

type Action = { type: "nouveau" } | { type: "modifier" | "basculer"; axe: AxeAdmin };

const BOUTON =
  "inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-bold ring-1 ring-border transition hover:bg-mist-soft";

function Axes() {
  const { admin } = Route.useRouteContext();
  const axes = Route.useLoaderData();
  const router = useRouter();
  const [action, setAction] = useState<Action | null>(null);
  const fermer = () => setAction(null);

  return (
    <div className="space-y-5">
      <p className="max-w-3xl text-sm font-medium text-muted-foreground">
        Les axes d'intervention classent les articles, vidéos, quiz, forums, événements et rapports.
        Un axe désactivé reste sur les contenus déjà classés, mais ne se choisit plus.
      </p>
      {admin.super_admin && (
        <Button
          onClick={() => setAction({ type: "nouveau" })}
          className="btn-fx h-11 rounded-full px-5 font-bold"
        >
          <Plus className="size-4" /> Nouvel axe
        </Button>
      )}

      <ol className="grid gap-3">
        {axes.map((axe) => (
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
              <p className="mt-1 text-sm font-medium text-muted-foreground">{axe.description}</p>
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
          titre={`${action.axe.actif ? "Désactiver" : "Réactiver"} l'axe ${action.axe.libelle} ?`}
          description={
            action.axe.actif
              ? "Il ne se choisira plus pour un nouveau contenu. Il faut garder au moins un axe actif."
              : "Il se choisira de nouveau pour les contenus."
          }
          bouton={action.axe.actif ? "Désactiver" : "Réactiver"}
          danger={action.axe.actif}
          onEnvoie={async () => {
            await adminModifierAxe(action.axe.code, {
              version: action.axe.version,
              actif: !action.axe.actif,
            });
            await router.invalidate();
          }}
        />
      )}
      {(action?.type === "nouveau" || action?.type === "modifier") && (
        <FormulaireAxe
          key={action.type === "modifier" ? action.axe.code : "nouveau"}
          axe={action.type === "modifier" ? action.axe : null}
          fermer={fermer}
        />
      )}
    </div>
  );
}

function FormulaireAxe({ axe, fermer }: { axe: AxeAdmin | null; fermer: () => void }) {
  const router = useRouter();
  const [code, setCode] = useState("");
  const [libelle, setLibelle] = useState(axe?.libelle ?? "");
  const [description, setDescription] = useState(axe?.description ?? "");
  const [ordre, setOrdre] = useState(axe ? String(axe.ordre) : "");

  return (
    <DialogueFormulaire
      ouvert
      onOuvert={(o) => !o && fermer()}
      titre={axe ? `Modifier l'axe ${axe.libelle}` : "Nouvel axe"}
      description={
        axe
          ? "Son code ne change pas : les contenus déjà classés le gardent."
          : "Le code ne pourra plus changer : choisis-le court, en minuscules et tirets."
      }
      bouton="Enregistrer"
      onEnvoie={async () => {
        const champs = { libelle, description, ordre: ordre ? Number(ordre) : null };
        if (axe) await adminModifierAxe(axe.code, { version: axe.version, ...champs });
        else await adminCreerAxe({ code, ...champs });
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
            placeholder="ex. sante-mentale"
            className={`${CHAMP_ADMIN} font-mono`}
          />
        </Champ>
      )}
      <Champ libelle="Libellé">
        <input
          required
          value={libelle}
          onChange={(e) => setLibelle(e.target.value)}
          maxLength={150}
          className={CHAMP_ADMIN}
        />
      </Champ>
      <Champ libelle="Description courte">
        <Textarea
          required
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          maxLength={300}
          rows={3}
          className="font-medium"
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
