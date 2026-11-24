import { Eye, EyeOff } from "lucide-react";
import { useState } from "react";
import type { Control, FieldPathByValue, FieldValues } from "react-hook-form";

import {
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { CHAMP } from "@/components/inscription/styles";
import { Input } from "@/components/ui/input";
import { lien } from "@/lib/langues";
import { m } from "@/paraglide/messages.js";

// Les morceaux communs aux formulaires d'inscription des élèves (spec 017) et des encadreurs (spec 018).

export function ChampMotDePasse<T extends FieldValues>({
  control,
  name,
}: {
  control: Control<T>;
  name: FieldPathByValue<T, string>;
}) {
  const [afficher, setAfficher] = useState(false);
  return (
    <FormField
      control={control}
      name={name}
      render={({ field }) => (
        <FormItem>
          <FormLabel>{m.cnx_mdp()}</FormLabel>
          <div className="relative">
            <FormControl>
              <Input
                {...field}
                type={afficher ? "text" : "password"}
                autoComplete="new-password"
                className={`${CHAMP} pr-12`}
              />
            </FormControl>
            <button
              type="button"
              onClick={() => setAfficher((v) => !v)}
              aria-pressed={afficher}
              aria-label={afficher ? m.cnx_masquer() : m.cnx_afficher()}
              className="absolute inset-y-0 right-0 flex w-12 items-center justify-center rounded-r-md text-muted-foreground transition hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              {afficher ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
            </button>
          </div>
          <FormDescription>{m.ins_mdp_aide()}</FormDescription>
          <FormMessage />
        </FormItem>
      )}
    />
  );
}

export function CaseAccord<T extends FieldValues>({
  control,
  name,
  libelle,
}: {
  control: Control<T>;
  name: FieldPathByValue<T, boolean>;
  libelle: React.ReactNode;
}) {
  return (
    <FormField
      control={control}
      name={name}
      render={({ field }) => (
        <FormItem>
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
            <span>{libelle}</span>
          </label>
          <FormMessage />
        </FormItem>
      )}
    />
  );
}

export function LienCharte() {
  return (
    <>
      {m.ins_charte_debut()}{" "}
      <a
        href={lien("/charte")}
        target="_blank"
        rel="noreferrer"
        className="font-bold text-logo-blue underline underline-offset-4"
      >
        {m.ins_charte_lien()}
      </a>
      {m.ins_charte_fin()}
    </>
  );
}
