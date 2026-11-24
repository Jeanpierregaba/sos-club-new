import { Plus, Trash2 } from "lucide-react";
import { useFieldArray, useFormContext, useWatch } from "react-hook-form";

import { CHAMP, LISTE } from "@/components/inscription/styles";
import { Button } from "@/components/ui/button";
import {
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import type { AxePublic } from "@/lib/api/client";
import { AXES_MAX, RESEAUX, SEXES, type ValeursFiche } from "@/lib/fiche";
import { m } from "@/paraglide/messages.js";

// Les champs de la fiche d'adhésion (spec 030), rangés sous « fiche » dans le formulaire qui les accueille :
// l'inscription d'un élève, ou « Ma fiche d'adhésion » dans son espace.

type AvecFiche = { fiche: ValeursFiche };
type NomTexte =
  | `fiche.${"numeroAdhesion" | "prefecture" | "commune" | "canton" | "lieuNaissance" | "telephone" | "responsableNom" | "responsableTelephone" | "reseauAutre"}`
  | `fiche.${"pere" | "mere"}.${"nom" | "profession" | "telephone"}`
  | `fiche.parcours.${number}.${"annee" | "etablissement" | "iesg"}`;

// Un composant : le texte suit la langue de la page (spec 052).
function Facultatif() {
  return <span className="font-medium text-muted-foreground">{m.vis_facultatif()}</span>;
}

function Texte({
  name,
  libelle,
  aide,
  optionnel = false,
  type = "text",
  autoComplete,
}: {
  name: NomTexte;
  libelle: string;
  aide?: string;
  optionnel?: boolean;
  type?: "text" | "tel";
  autoComplete?: string;
}) {
  const { control } = useFormContext<AvecFiche>();
  return (
    <FormField
      control={control}
      name={name}
      render={({ field }) => (
        <FormItem>
          <FormLabel>
            {libelle} {optionnel && <Facultatif />}
          </FormLabel>
          <FormControl>
            <Input
              {...field}
              value={String(field.value ?? "")}
              type={type}
              inputMode={type === "tel" ? "tel" : undefined}
              autoComplete={autoComplete ?? "off"}
              className={CHAMP}
            />
          </FormControl>
          {aide && <FormDescription>{aide}</FormDescription>}
          <FormMessage />
        </FormItem>
      )}
    />
  );
}

function Titre({ children }: { children: React.ReactNode }) {
  return <legend className="mb-4 text-lg font-bold text-logo-blue">{children}</legend>;
}

export function SectionLieu() {
  return (
    <fieldset className="space-y-5">
      <Titre>{m.fiche_localite()}</Titre>
      <Texte
        name="fiche.numeroAdhesion"
        libelle={m.fiche_numero()}
        aide={m.fiche_numero_aide()}
        optionnel
      />
      <div className="grid gap-5 sm:grid-cols-3">
        <Texte name="fiche.prefecture" libelle={m.fiche_prefecture()} optionnel />
        <Texte name="fiche.commune" libelle={m.fiche_commune()} />
        <Texte name="fiche.canton" libelle={m.fiche_canton()} optionnel />
      </div>
    </fieldset>
  );
}

export function SectionToi() {
  const { control } = useFormContext<AvecFiche>();
  return (
    <fieldset className="space-y-5">
      <Titre>{m.fiche_toi()}</Titre>
      <div className="grid gap-5 sm:grid-cols-2">
        <FormField
          control={control}
          name="fiche.sexe"
          render={({ field }) => (
            <FormItem>
              <FormLabel>{m.vis_sexe()}</FormLabel>
              <FormControl>
                <select {...field} className={LISTE}>
                  <option value="">{m.vis_choisis()}</option>
                  {SEXES.map((s) => (
                    <option key={s.valeur} value={s.valeur}>
                      {s.libelle}
                    </option>
                  ))}
                </select>
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={control}
          name="fiche.dateNaissance"
          render={({ field }) => (
            <FormItem>
              <FormLabel>{m.fiche_naissance()}</FormLabel>
              <FormControl>
                <Input {...field} type="date" autoComplete="bday" className={CHAMP} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
      </div>
      <Texte name="fiche.lieuNaissance" libelle={m.fiche_lieu_naissance()} />
      <Texte
        name="fiche.telephone"
        libelle={m.fiche_telephone()}
        type="tel"
        autoComplete="tel"
        aide={m.fiche_telephone_aide()}
        optionnel
      />
    </fieldset>
  );
}

function Parent({ qui }: { qui: "pere" | "mere" }) {
  const pere = qui === "pere";
  return (
    <div className="space-y-4 rounded-2xl bg-mist-soft p-4">
      <p className="font-bold text-ink">
        {pere ? m.fiche_pere() : m.fiche_mere()} <Facultatif />
      </p>
      <Texte name={`fiche.${qui}.nom`} libelle={pere ? m.fiche_nom_pere() : m.fiche_nom_mere()} />
      <div className="grid gap-4 sm:grid-cols-2">
        <Texte
          name={`fiche.${qui}.profession`}
          libelle={pere ? m.fiche_profession_pere() : m.fiche_profession_mere()}
        />
        <Texte
          name={`fiche.${qui}.telephone`}
          libelle={pere ? m.fiche_contact_pere() : m.fiche_contact_mere()}
          type="tel"
        />
      </div>
    </div>
  );
}

export function SectionFamille() {
  return (
    <fieldset className="space-y-5">
      <Titre>{m.fiche_famille()}</Titre>
      <Parent qui="pere" />
      <Parent qui="mere" />
      <div className="space-y-4 rounded-2xl border-2 border-primary/30 p-4">
        <p className="font-bold text-ink">{m.fiche_responsable()}</p>
        <p className="-mt-2 text-sm font-medium text-muted-foreground">
          {m.fiche_responsable_aide()}
        </p>
        <Texte name="fiche.responsableNom" libelle={m.fiche_responsable_nom()} />
        <Texte
          name="fiche.responsableTelephone"
          libelle={m.fiche_responsable_contact()}
          type="tel"
        />
      </div>
    </fieldset>
  );
}

function ChoixAxes({ axes }: { axes: AxePublic[] }) {
  const { control } = useFormContext<AvecFiche>();
  return (
    <FormField
      control={control}
      name="fiche.axes"
      render={({ field }) => {
        const choisis: string[] = field.value;
        const basculer = (code: string) =>
          field.onChange(
            choisis.includes(code) ? choisis.filter((c) => c !== code) : [...choisis, code],
          );
        return (
          <FormItem>
            <FormLabel>{m.fiche_axes()}</FormLabel>
            <FormDescription>{m.fiche_axes_aide({ max: String(AXES_MAX) })}</FormDescription>
            <div className="grid gap-2 sm:grid-cols-2">
              {[
                ...axes,
                // Un axe désactivé depuis le choix de l'élève reste affiché : il peut le décocher.
                ...choisis
                  .filter((code) => !axes.some((a) => a.code === code))
                  .map((code) => ({ code, libelle: m.fiche_axe_retire({ code }) })),
              ].map((axe) => {
                const coche = choisis.includes(axe.code);
                const bloque = !coche && choisis.length >= AXES_MAX;
                return (
                  <label
                    key={axe.code}
                    className={`flex cursor-pointer items-start gap-3 rounded-xl border-2 p-3 text-sm font-semibold transition ${
                      coche ? "border-primary bg-primary/5" : "border-border"
                    } ${bloque ? "cursor-not-allowed opacity-50" : ""}`}
                  >
                    <input
                      type="checkbox"
                      checked={coche}
                      disabled={bloque}
                      onChange={() => basculer(axe.code)}
                      className="mt-0.5 size-5 shrink-0 accent-primary"
                    />
                    <span>{axe.libelle}</span>
                  </label>
                );
              })}
            </div>
            <FormMessage />
          </FormItem>
        );
      }}
    />
  );
}

function Parcours() {
  const { control } = useFormContext<AvecFiche>();
  const { fields, append, remove } = useFieldArray({ control, name: "fiche.parcours" });
  return (
    <div className="space-y-3">
      <p className="text-sm font-semibold">
        {m.fiche_annees()} <Facultatif />
      </p>
      {fields.map((ligne, i) => (
        <div key={ligne.id} className="space-y-3 rounded-2xl bg-mist-soft p-4">
          <div className="flex items-center justify-between">
            <span className="text-sm font-bold text-ink">
              {m.fiche_annee({ numero: String(i + 1) })}
            </span>
            <Button type="button" variant="ghost" size="sm" onClick={() => remove(i)}>
              <Trash2 className="size-4" /> {m.fiche_retirer()}
            </Button>
          </div>
          <div className="grid gap-3 sm:grid-cols-3">
            <Texte
              name={`fiche.parcours.${i}.annee`}
              libelle={m.fiche_annee_scolaire()}
              aide="2025-2026"
            />
            <Texte name={`fiche.parcours.${i}.etablissement`} libelle={m.fiche_etablissement()} />
            <Texte name={`fiche.parcours.${i}.iesg`} libelle="IESG" optionnel />
          </div>
        </div>
      ))}
      {fields.length < 2 && (
        <Button
          type="button"
          variant="outline"
          className="rounded-full"
          onClick={() => append({ annee: "", etablissement: "", iesg: "" })}
        >
          <Plus className="size-4" /> {m.fiche_ajouter_annee()}
        </Button>
      )}
    </div>
  );
}

function ChoixReseaux() {
  const { control } = useFormContext<AvecFiche>();
  const reseaux = useWatch({ control, name: "fiche.reseaux" });
  return (
    <div className="space-y-3">
      <FormField
        control={control}
        name="fiche.reseaux"
        render={({ field }) => {
          const choisis: string[] = field.value;
          return (
            <FormItem>
              <FormLabel>
                {m.fiche_reseaux()} <Facultatif />
              </FormLabel>
              <div className="flex flex-wrap gap-2">
                {RESEAUX.map((r) => {
                  const coche = choisis.includes(r.valeur);
                  return (
                    <label
                      key={r.valeur}
                      className={`flex cursor-pointer items-center gap-2 rounded-full border-2 px-4 py-2 text-sm font-semibold ${
                        coche ? "border-primary bg-primary/5" : "border-border"
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={coche}
                        onChange={() =>
                          field.onChange(
                            coche ? choisis.filter((c) => c !== r.valeur) : [...choisis, r.valeur],
                          )
                        }
                        className="size-4 accent-primary"
                      />
                      {r.libelle}
                    </label>
                  );
                })}
              </div>
              <FormMessage />
            </FormItem>
          );
        }}
      />
      {reseaux.includes("autre") && (
        <Texte name="fiche.reseauAutre" libelle={m.fiche_autre_reseau()} />
      )}
    </div>
  );
}

export function SectionClub({ axes }: { axes: AxePublic[] }) {
  const { control } = useFormContext<AvecFiche>();
  return (
    <fieldset className="space-y-6">
      <Titre>{m.fiche_club()}</Titre>
      <ChoixAxes axes={axes} />
      <Parcours />
      <ChoixReseaux />
      <FormField
        control={control}
        name="fiche.engagement"
        render={({ field }) => (
          <FormItem className="rounded-2xl bg-mist-soft p-4">
            <label className="flex cursor-pointer items-start gap-3 text-sm font-semibold text-ink">
              <FormControl>
                <input
                  type="checkbox"
                  checked={field.value}
                  onChange={(e) => field.onChange(e.target.checked)}
                  onBlur={field.onBlur}
                  ref={field.ref}
                  className="mt-0.5 size-5 shrink-0 accent-primary"
                />
              </FormControl>
              <span>{m.fiche_engagement()}</span>
            </label>
            <FormMessage />
          </FormItem>
        )}
      />
    </fieldset>
  );
}
