import { zodResolver } from "@hookform/resolvers/zod";
import { useQueryClient } from "@tanstack/react-query";
import { useRouter } from "@tanstack/react-router";
import { Loader2 } from "lucide-react";
import { useRef, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { CaseAccord, ChampMotDePasse, LienCharte } from "@/components/inscription/commun";
import { ConfirmationEmail } from "@/components/inscription/ConfirmationEmail";
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
import {
  ErreurApi,
  inscrireVisiteur,
  MESSAGE_INDISPONIBLE,
  type Moi,
  type Region,
  type Sexe,
} from "@/lib/api/client";
import { SEXES } from "@/lib/fiche";
import { REGIONS } from "@/lib/visiteurs";
import { normaliserTelephone, telephoneValide } from "@/lib/telephone";

const schema = z.object({
  nom: z.string().trim().min(1, "Indique ton nom.").max(100, "Ce nom est trop long."),
  prenom: z.string().trim().min(1, "Indique tes prénoms.").max(100, "C'est trop long."),
  telephone: z
    .string()
    .max(30, "Ce numéro est trop long.")
    .refine((v) => normaliserTelephone(v) !== "", "Indique ton téléphone ou ton WhatsApp.")
    .refine(telephoneValide, "De 8 à 15 chiffres, avec « + » au début si besoin."),
  ville: z.string().trim().min(1, "Indique ta ville.").max(100, "C'est trop long."),
  email: z
    .string()
    .trim()
    .min(1, "Indique ton adresse e-mail : ton code y sera envoyé.")
    .max(254, "Cette adresse est trop longue.")
    .regex(/^[^\s@]+@[^\s@]+\.[^\s@]+$/, "Cette adresse n'est pas valide."),
  region: z.string(),
  sexe: z.string(),
  statut: z.string().trim().max(100, "C'est trop long."),
  motDePasse: z
    .string()
    .min(8, "Au moins 8 caractères.")
    .max(256, "Ce mot de passe est trop long."),
  charte: z.boolean().refine((v) => v, "Tu dois accepter la charte."),
  accord: z.boolean().refine((v) => v, "Cette confirmation est nécessaire."),
});

type Valeurs = z.infer<typeof schema>;

const CHAMPS_NOMMES: [string, keyof Valeurs][] = [
  ["email", "email"],
  ["téléphone", "telephone"],
  ["mot de passe", "motDePasse"],
];

// Le compte visiteur (spec 030) : un compte léger, confirmé par un code reçu par e-mail, pour jouer aux quiz.
export function InscriptionVisiteur() {
  const queryClient = useQueryClient();
  const router = useRouter();
  const haut = useRef<HTMLDivElement>(null);
  const [erreur, setErreur] = useState<string | null>(null);
  const [attente, setAttente] = useState<{ email: string; test: string | null } | null>(null);

  const form = useForm<Valeurs>({
    resolver: zodResolver(schema),
    defaultValues: {
      nom: "",
      prenom: "",
      telephone: "",
      ville: "",
      email: "",
      region: "",
      sexe: "",
      statut: "",
      motDePasse: "",
      charte: false,
      accord: false,
    },
  });

  const confirme = async (moi: Moi) => {
    queryClient.setQueryData(CLE_MOI, moi);
    await router.navigate({ to: "/mon-espace", search: { bienvenue: true }, replace: true });
  };

  const envoyer = form.handleSubmit(async (v) => {
    setErreur(null);
    try {
      const reponse = await inscrireVisiteur({
        nom: v.nom,
        prenom: v.prenom,
        telephone: normaliserTelephone(v.telephone),
        ville: v.ville,
        email: v.email,
        region: (v.region || null) as Region | null,
        sexe: (v.sexe || null) as Sexe | null,
        statut: v.statut || null,
        mot_de_passe: v.motDePasse,
        charte: true,
        majeur_ou_accord: true,
      });
      setAttente({ email: reponse.email, test: reponse.code_de_test ?? null });
      haut.current?.scrollIntoView({ behavior: "smooth", block: "center" });
    } catch (e) {
      const message = e instanceof ErreurApi ? e.message : MESSAGE_INDISPONIBLE;
      form.resetField("motDePasse");
      const champ = CHAMPS_NOMMES.find(([mot]) => message.toLowerCase().includes(mot));
      if (champ) form.setError(champ[1], { message }, { shouldFocus: true });
      else {
        setErreur(message);
        haut.current?.scrollIntoView({ behavior: "smooth", block: "center" });
      }
    }
  });
  const enCours = form.formState.isSubmitting;

  if (attente) {
    return (
      <div ref={haut}>
        <ConfirmationEmail
          email={attente.email}
          codeDeTest={attente.test}
          onConfirme={(moi) => void confirme(moi)}
        />
      </div>
    );
  }

  const texte = (
    name: "nom" | "prenom" | "ville" | "statut",
    libelle: React.ReactNode,
    placeholder: string,
    autoComplete: string,
  ) => (
    <FormField
      control={form.control}
      name={name}
      render={({ field }) => (
        <FormItem>
          <FormLabel>{libelle}</FormLabel>
          <FormControl>
            <Input
              {...field}
              placeholder={placeholder}
              autoComplete={autoComplete}
              className={CHAMP}
            />
          </FormControl>
          <FormMessage />
        </FormItem>
      )}
    />
  );
  const facultatif = <span className="font-medium text-muted-foreground">(facultatif)</span>;

  return (
    <Form {...form}>
      <form onSubmit={envoyer} noValidate className="space-y-6">
        <div ref={haut}>
          {erreur && (
            <Alert variant="destructive" role="alert">
              <AlertDescription>{erreur}</AlertDescription>
            </Alert>
          )}
        </div>

        <fieldset className="space-y-5">
          <legend className="mb-4 text-lg font-bold text-logo-blue">Qui es-tu ?</legend>
          <div className="grid gap-5 sm:grid-cols-2">
            {texte("nom", "Nom", "ex. : AMÉGAN", "family-name")}
            {texte("prenom", "Prénoms", "ex. : Koffi Jean", "given-name")}
          </div>
          <div className="grid gap-5 sm:grid-cols-2">
            <FormField
              control={form.control}
              name="telephone"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Téléphone / WhatsApp</FormLabel>
                  <FormControl>
                    <Input
                      {...field}
                      type="tel"
                      inputMode="tel"
                      placeholder="ex. : +228 90 12 34 56"
                      autoComplete="tel"
                      className={CHAMP}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            {texte("ville", "Ville", "ex. : Lomé", "address-level2")}
          </div>
          <div className="grid gap-5 sm:grid-cols-2">
            <FormField
              control={form.control}
              name="region"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Région {facultatif}</FormLabel>
                  <FormControl>
                    <select {...field} className={LISTE}>
                      <option value="">Choisis ta région</option>
                      {REGIONS.map((r) => (
                        <option key={r.valeur} value={r.valeur}>
                          {r.libelle}
                        </option>
                      ))}
                    </select>
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="sexe"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Sexe {facultatif}</FormLabel>
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
          </div>
          {texte(
            "statut",
            <>Statut ou profession {facultatif}</>,
            "ex. : étudiant, parent, professionnel de santé…",
            "organization-title",
          )}
        </fieldset>

        <fieldset className="space-y-5">
          <legend className="mb-4 text-lg font-bold text-logo-blue">Tes accès</legend>
          <FormField
            control={form.control}
            name="email"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Adresse e-mail</FormLabel>
                <FormControl>
                  <Input
                    {...field}
                    type="email"
                    autoComplete="email"
                    autoCapitalize="none"
                    placeholder="ex. : ton.adresse@gmail.com"
                    className={CHAMP}
                  />
                </FormControl>
                <FormDescription>
                  Tu y recevras ton code de confirmation. Elle te sert aussi à te connecter.
                </FormDescription>
                <FormMessage />
              </FormItem>
            )}
          />
          <ChampMotDePasse control={form.control} name="motDePasse" />
        </fieldset>

        <fieldset className="space-y-4 rounded-2xl bg-mist-soft p-4">
          <legend className="sr-only">Accords</legend>
          <CaseAccord control={form.control} name="charte" libelle={<LienCharte />} />
          <CaseAccord
            control={form.control}
            name="accord"
            libelle="J'ai 18 ans ou plus, ou mon parent ou tuteur est d'accord pour que je m'inscrive."
          />
        </fieldset>

        <Button
          type="submit"
          disabled={enCours}
          className="btn-fx h-12 w-full rounded-full text-base font-bold"
        >
          {enCours && <Loader2 className="h-5 w-5 animate-spin" />}
          Recevoir mon code
        </Button>
      </form>
    </Form>
  );
}
