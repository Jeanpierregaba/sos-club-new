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

// Les champs de la fiche d'adhésion (spec 030), rangés sous « fiche » dans le formulaire qui les accueille :
// l'inscription d'un élève, ou « Ma fiche d'adhésion » dans son espace.

type AvecFiche = { fiche: ValeursFiche };
type NomTexte =
  | `fiche.${"numeroAdhesion" | "prefecture" | "commune" | "canton" | "lieuNaissance" | "telephone" | "responsableNom" | "responsableTelephone" | "reseauAutre"}`
  | `fiche.${"pere" | "mere"}.${"nom" | "profession" | "telephone"}`
  | `fiche.parcours.${number}.${"annee" | "etablissement" | "iesg"}`;

const facultatif = <span className="font-medium text-muted-foreground">(facultatif)</span>;

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
            {libelle} {optionnel && facultatif}
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
      <Titre>Ton établissement et ta localité</Titre>
      <Texte
        name="fiche.numeroAdhesion"
        libelle="N° d'adhésion dans l'établissement"
        aide="Si ton club t'en a déjà donné un."
        optionnel
      />
      <div className="grid gap-5 sm:grid-cols-3">
        <Texte name="fiche.prefecture" libelle="Préfecture" optionnel />
        <Texte name="fiche.commune" libelle="Commune" optionnel />
        <Texte name="fiche.canton" libelle="Canton" optionnel />
      </div>
    </fieldset>
  );
}

export function SectionToi() {
  const { control } = useFormContext<AvecFiche>();
  return (
    <fieldset className="space-y-5">
      <Titre>Toi</Titre>
      <div className="grid gap-5 sm:grid-cols-2">
        <FormField
          control={control}
          name="fiche.sexe"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Sexe</FormLabel>
              <FormControl>
                <select {...field} className={LISTE}>
                  <option value="">Choisis</option>
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
              <FormLabel>Date de naissance</FormLabel>
              <FormControl>
                <Input {...field} type="date" autoComplete="bday" className={CHAMP} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
      </div>
      <Texte name="fiche.lieuNaissance" libelle="Lieu de naissance" />
      <Texte
        name="fiche.telephone"
        libelle="Ton téléphone"
        type="tel"
        autoComplete="tel"
        aide="Il reste privé : seule l'équipe nationale le voit."
        optionnel
      />
    </fieldset>
  );
}

function Parent({ qui, libelle }: { qui: "pere" | "mere"; libelle: string }) {
  return (
    <div className="space-y-4 rounded-2xl bg-mist-soft p-4">
      <p className="font-bold text-ink">
        {libelle} {facultatif}
      </p>
      <Texte name={`fiche.${qui}.nom`} libelle="Nom et prénoms" />
      <div className="grid gap-4 sm:grid-cols-2">
        <Texte name={`fiche.${qui}.profession`} libelle="Profession" />
        <Texte name={`fiche.${qui}.telephone`} libelle="Contact" type="tel" />
      </div>
    </div>
  );
}

export function SectionFamille() {
  return (
    <fieldset className="space-y-5">
      <Titre>Ta famille</Titre>
      <Parent qui="pere" libelle="Père" />
      <Parent qui="mere" libelle="Mère" />
      <div className="space-y-4 rounded-2xl border-2 border-primary/30 p-4">
        <p className="font-bold text-ink">Ton parent ou tuteur responsable</p>
        <p className="-mt-2 text-sm font-medium text-muted-foreground">
          Il remplace la signature de la fiche papier : l'équipe peut le joindre si besoin.
        </p>
        <Texte name="fiche.responsableNom" libelle="Nom et prénoms" />
        <Texte name="fiche.responsableTelephone" libelle="Contact" type="tel" />
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
            <FormLabel>Axe(s) choisi(s)</FormLabel>
            <FormDescription>De 1 à {AXES_MAX} axes du Club Santé.</FormDescription>
            <div className="grid gap-2 sm:grid-cols-2">
              {axes.map((axe) => {
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
      <p className="text-sm font-semibold">Club Santé les années précédentes {facultatif}</p>
      {fields.map((ligne, i) => (
        <div key={ligne.id} className="space-y-3 rounded-2xl bg-mist-soft p-4">
          <div className="flex items-center justify-between">
            <span className="text-sm font-bold text-ink">Année {i + 1}</span>
            <Button type="button" variant="ghost" size="sm" onClick={() => remove(i)}>
              <Trash2 className="size-4" /> Retirer
            </Button>
          </div>
          <div className="grid gap-3 sm:grid-cols-3">
            <Texte name={`fiche.parcours.${i}.annee`} libelle="Année scolaire" aide="2025-2026" />
            <Texte name={`fiche.parcours.${i}.etablissement`} libelle="Établissement" />
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
          <Plus className="size-4" /> Ajouter une année
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
              <FormLabel>Réseaux sociaux auxquels tu es abonné {facultatif}</FormLabel>
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
        <Texte name="fiche.reseauAutre" libelle="Quel autre réseau ?" />
      )}
    </div>
  );
}

export function SectionClub({ axes }: { axes: AxePublic[] }) {
  const { control } = useFormContext<AvecFiche>();
  return (
    <fieldset className="space-y-6">
      <Titre>Ton Club Santé</Titre>
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
              <span>
                Je m'engage à mener les activités du Club Santé SOS Docteur TV de mon établissement.
              </span>
            </label>
            <FormMessage />
          </FormItem>
        )}
      />
    </fieldset>
  );
}
