import { zodResolver } from "@hookform/resolvers/zod";
import { useQueryClient } from "@tanstack/react-query";
import { useRouter } from "@tanstack/react-router";
import { Loader2 } from "lucide-react";
import { useRef, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { ChampEtablissement } from "@/components/inscription/ChampEtablissement";
import { CaseAccord, ChampMotDePasse, LienCharte } from "@/components/inscription/commun";
import { CHAMP, LISTE } from "@/components/inscription/styles";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { CLE_MOI } from "@/hooks/use-moi";
import { ErreurApi, inscrireEncadreur, type DrePublique, type Fonction } from "@/lib/api/client";
import { FONCTIONS, nomFonction } from "@/lib/fonctions";
import {
  corpsEtablissement,
  manqueEtablissement,
  SAISIE_VIDE,
  type SaisieEtablissement,
} from "@/lib/saisie-etablissement";
import { normaliserTelephone, telephoneValide } from "@/lib/telephone";
import { useEtapesInscription } from "@/lib/activite";
import { m } from "@/paraglide/messages.js";

const schema = z
  .object({
    prenom: z.string().trim().min(1, "Indique ton prénom.").max(100, "Ce prénom est trop long."),
    nom: z.string().trim().min(1, "Indique ton nom.").max(100, "Ce nom est trop long."),
    email: z
      .string()
      .trim()
      .min(1, "Indique ton email : il sert à te prévenir de la vérification.")
      .max(254, "Cet email est trop long.")
      .regex(/^[^\s@]+@[^\s@]+\.[^\s@]+$/, "Cet email n'est pas valide."),
    telephone: z
      .string()
      .max(30, "Ce numéro est trop long.")
      .refine((v) => normaliserTelephone(v) !== "", "Indique ton téléphone ou ton WhatsApp.")
      .refine(telephoneValide, "De 8 à 15 chiffres, avec « + » au début si besoin."),
    discipline: z.string().trim().max(100, "Cette discipline est trop longue."),
    commune: z
      .string()
      .trim()
      .min(1, "Indique ta commune.")
      .max(100, "Ce nom de commune est trop long."),
    fonction: z.string().min(1, "Choisis ta fonction."),
    precision: z.string().trim().max(100, "Cette précision est trop longue."),
    identifiant: z
      .string()
      .trim()
      .toLowerCase()
      .regex(
        /^[a-z0-9._-]{3,30}$/,
        "De 3 à 30 lettres sans accent, chiffres, « . », « - » ou « _ ».",
      ),
    motDePasse: z
      .string()
      .min(8, "Au moins 8 caractères.")
      .max(256, "Ce mot de passe est trop long."),
    charte: z.boolean().refine((v) => v, "Tu dois accepter la charte."),
    consentement: z
      .boolean()
      .refine((v) => v, "Ton accord est nécessaire pour vérifier ton compte."),
  })
  .refine((v) => v.fonction !== "autre" || v.precision.length > 0, {
    path: ["precision"],
    message: "Précise ta fonction.",
  });

type Valeurs = z.infer<typeof schema>;

// Un refus de l'API qui nomme un champ est affiché sous ce champ.
const CHAMPS_NOMMES: [string, keyof Valeurs][] = [
  ["identifiant", "identifiant"],
  ["email", "email"],
  ["téléphone", "telephone"],
  ["mot de passe", "motDePasse"],
];

// Le formulaire d'inscription d'un encadreur (spec 018) : le compte attend la vérification de l'équipe.
export function InscriptionEncadreur({ dre }: { dre: DrePublique[] }) {
  // Spec 051 : formulaire ouvert, puis commencé à la première saisie (événements anonymes).
  const commencer = useEtapesInscription("encadreur");
  const queryClient = useQueryClient();
  const router = useRouter();
  const haut = useRef<HTMLDivElement>(null);
  const [erreur, setErreur] = useState<string | null>(null);
  const [etablissement, setEtablissement] = useState<SaisieEtablissement>(SAISIE_VIDE);
  const [erreurEtablissement, setErreurEtablissement] = useState<string | null>(null);

  const form = useForm<Valeurs>({
    resolver: zodResolver(schema),
    defaultValues: {
      prenom: "",
      nom: "",
      email: "",
      telephone: "",
      fonction: "",
      precision: "",
      discipline: "",
      commune: "",
      identifiant: "",
      motDePasse: "",
      charte: false,
      consentement: false,
    },
  });
  const autre = form.watch("fonction") === "autre";

  const envoyer = form.handleSubmit(
    async (v) => {
      const manque = manqueEtablissement(etablissement);
      setErreurEtablissement(manque);
      if (manque) return;
      setErreur(null);
      try {
        const moi = await inscrireEncadreur({
          prenom: v.prenom,
          nom: v.nom,
          email: v.email,
          telephone: normaliserTelephone(v.telephone),
          identifiant: v.identifiant,
          mot_de_passe: v.motDePasse,
          fonction: v.fonction as Fonction,
          fonction_precision: v.fonction === "autre" ? v.precision : null,
          discipline: v.discipline || null,
          commune: v.commune,
          charte: true,
          consentement: true,
          ...corpsEtablissement(etablissement),
        });
        queryClient.setQueryData(CLE_MOI, moi);
        await router.navigate({ to: "/mon-espace", replace: true });
      } catch (e) {
        const message = e instanceof ErreurApi ? e.message : m.erreur_indisponible();
        // La saisie est gardée, sauf le mot de passe.
        form.resetField("motDePasse");
        const origine = e instanceof ErreurApi ? e.messageFrancais.toLowerCase() : "";
        const champ = CHAMPS_NOMMES.find(([mot]) => origine.includes(mot));
        if (champ) form.setError(champ[1], { message }, { shouldFocus: true });
        else {
          setErreur(message);
          haut.current?.scrollIntoView({ behavior: "smooth", block: "center" });
        }
      }
    },
    () => setErreurEtablissement(manqueEtablissement(etablissement)),
  );
  const enCours = form.formState.isSubmitting;

  return (
    <Form {...form}>
      <form onSubmit={envoyer} onChange={commencer} noValidate className="space-y-6">
        <div ref={haut}>
          {erreur && (
            <Alert variant="destructive" role="alert">
              <AlertDescription>{erreur}</AlertDescription>
            </Alert>
          )}
        </div>

        <fieldset className="space-y-5">
          <legend className="mb-4 text-lg font-bold text-logo-blue">{m.vis_qui()}</legend>
          <div className="grid gap-5 sm:grid-cols-2">
            <FormField
              control={form.control}
              name="prenom"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>{m.elv_prenom()}</FormLabel>
                  <FormControl>
                    <Input {...field} autoComplete="given-name" className={CHAMP} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="nom"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>{m.vis_nom()}</FormLabel>
                  <FormControl>
                    <Input {...field} autoComplete="family-name" className={CHAMP} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </div>
          <FormField
            control={form.control}
            name="fonction"
            render={({ field }) => (
              <FormItem>
                <FormLabel>{m.enc_fonction()}</FormLabel>
                <FormControl>
                  <select {...field} className={LISTE}>
                    <option value="">{m.enc_choisis_fonction()}</option>
                    {FONCTIONS.map((f) => (
                      <option key={f.valeur} value={f.valeur}>
                        {nomFonction(f.valeur)}
                      </option>
                    ))}
                  </select>
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          {autre && (
            <FormField
              control={form.control}
              name="precision"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>{m.enc_precise()}</FormLabel>
                  <FormControl>
                    <Input {...field} maxLength={100} className={CHAMP} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          )}
          <FormField
            control={form.control}
            name="discipline"
            render={({ field }) => (
              <FormItem>
                <FormLabel>
                  {m.enc_discipline()}{" "}
                  <span className="font-medium text-muted-foreground">{m.vis_facultatif()}</span>
                </FormLabel>
                <FormControl>
                  <Input
                    {...field}
                    maxLength={100}
                    placeholder={m.enc_discipline_ph()}
                    className={CHAMP}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
        </fieldset>

        <ChampEtablissement
          dre={dre}
          saisie={etablissement}
          onSaisie={(saisie) => {
            setEtablissement(saisie);
            if (saisie.choix) setErreurEtablissement(null);
          }}
          erreur={erreurEtablissement}
        />
        {etablissement.choix?.dre && (
          <dl className="-mt-2 grid grid-cols-2 gap-3 rounded-2xl bg-mist-soft p-4 text-sm">
            <div>
              <dt className="font-semibold text-muted-foreground">{m.enc_region_dre()}</dt>
              <dd className="font-bold text-ink">{etablissement.choix.dre}</dd>
            </div>
            <div>
              <dt className="font-semibold text-muted-foreground">{m.enc_ville_lycee()}</dt>
              <dd className="font-bold text-ink">{etablissement.choix.localite ?? "—"}</dd>
            </div>
          </dl>
        )}
        <FormField
          control={form.control}
          name="commune"
          render={({ field }) => (
            <FormItem>
              <FormLabel>{m.enc_commune()}</FormLabel>
              <FormControl>
                <Input
                  {...field}
                  maxLength={100}
                  placeholder={m.enc_commune_ph()}
                  autoComplete="address-level2"
                  className={CHAMP}
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <fieldset className="space-y-5">
          <legend className="mb-4 text-lg font-bold text-logo-blue">{m.enc_joindre()}</legend>
          <FormField
            control={form.control}
            name="email"
            render={({ field }) => (
              <FormItem>
                <FormLabel>{m.elv_email()}</FormLabel>
                <FormControl>
                  <Input
                    {...field}
                    type="email"
                    autoComplete="email"
                    autoCapitalize="none"
                    className={CHAMP}
                  />
                </FormControl>
                <FormDescription>{m.enc_email_aide()}</FormDescription>
                <FormMessage />
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name="telephone"
            render={({ field }) => (
              <FormItem>
                <FormLabel>{m.vis_telephone()}</FormLabel>
                <FormControl>
                  <Input {...field} type="tel" autoComplete="tel" className={CHAMP} />
                </FormControl>
                <FormDescription>{m.enc_telephone_aide()}</FormDescription>
                <FormMessage />
              </FormItem>
            )}
          />
        </fieldset>

        <fieldset className="space-y-5">
          <legend className="mb-4 text-lg font-bold text-logo-blue">{m.vis_acces()}</legend>
          <FormField
            control={form.control}
            name="identifiant"
            render={({ field }) => (
              <FormItem>
                <FormLabel>{m.elv_identifiant()}</FormLabel>
                <FormControl>
                  <Input
                    {...field}
                    autoComplete="username"
                    autoCapitalize="none"
                    autoCorrect="off"
                    spellCheck={false}
                    className={CHAMP}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <ChampMotDePasse control={form.control} name="motDePasse" />
        </fieldset>

        <fieldset className="space-y-4 rounded-2xl bg-mist-soft p-4">
          <legend className="sr-only">{m.vis_accords()}</legend>
          <CaseAccord control={form.control} name="charte" libelle={<LienCharte />} />
          <CaseAccord control={form.control} name="consentement" libelle={m.enc_accord()} />
        </fieldset>

        <Button
          type="submit"
          disabled={enCours}
          className="btn-fx h-12 w-full rounded-full text-base font-bold"
        >
          {enCours && <Loader2 className="h-5 w-5 animate-spin" />}
          {m.enc_envoyer()}
        </Button>
      </form>
    </Form>
  );
}
