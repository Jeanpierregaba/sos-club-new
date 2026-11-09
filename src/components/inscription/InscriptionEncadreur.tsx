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
import {
  ErreurApi,
  inscrireEncadreur,
  MESSAGE_INDISPONIBLE,
  type DrePublique,
  type Fonction,
} from "@/lib/api/client";
import { FONCTIONS } from "@/lib/fonctions";
import {
  corpsEtablissement,
  manqueEtablissement,
  SAISIE_VIDE,
  type SaisieEtablissement,
} from "@/lib/saisie-etablissement";
import { normaliserTelephone, telephoneValide } from "@/lib/telephone";

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
          charte: true,
          consentement: true,
          ...corpsEtablissement(etablissement),
        });
        queryClient.setQueryData(CLE_MOI, moi);
        await router.navigate({ to: "/mon-espace", replace: true });
      } catch (e) {
        const message = e instanceof ErreurApi ? e.message : MESSAGE_INDISPONIBLE;
        // La saisie est gardée, sauf le mot de passe.
        form.resetField("motDePasse");
        const champ = CHAMPS_NOMMES.find(([mot]) => message.toLowerCase().includes(mot));
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
            <FormField
              control={form.control}
              name="prenom"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Prénom</FormLabel>
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
                  <FormLabel>Nom</FormLabel>
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
                <FormLabel>Ta fonction dans l'établissement</FormLabel>
                <FormControl>
                  <select {...field} className={LISTE}>
                    <option value="">Choisis ta fonction</option>
                    {FONCTIONS.map((f) => (
                      <option key={f.valeur} value={f.valeur}>
                        {f.libelle}
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
                  <FormLabel>Précise ta fonction</FormLabel>
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
                  Discipline, matière ou spécialité{" "}
                  <span className="font-medium text-muted-foreground">(facultatif)</span>
                </FormLabel>
                <FormControl>
                  <Input
                    {...field}
                    maxLength={100}
                    placeholder="ex. : SVT (Sciences de la Vie et de la Terre)"
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
              <dt className="font-semibold text-muted-foreground">Région (DRE)</dt>
              <dd className="font-bold text-ink">{etablissement.choix.dre}</dd>
            </div>
            <div>
              <dt className="font-semibold text-muted-foreground">Ville du lycée</dt>
              <dd className="font-bold text-ink">{etablissement.choix.localite ?? "—"}</dd>
            </div>
          </dl>
        )}

        <fieldset className="space-y-5">
          <legend className="mb-4 text-lg font-bold text-logo-blue">Pour te joindre</legend>
          <FormField
            control={form.control}
            name="email"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Email</FormLabel>
                <FormControl>
                  <Input
                    {...field}
                    type="email"
                    autoComplete="email"
                    autoCapitalize="none"
                    className={CHAMP}
                  />
                </FormControl>
                <FormDescription>Tu y recevras la réponse de l'équipe.</FormDescription>
                <FormMessage />
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name="telephone"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Téléphone / WhatsApp</FormLabel>
                <FormControl>
                  <Input {...field} type="tel" autoComplete="tel" className={CHAMP} />
                </FormControl>
                <FormDescription>
                  L'équipe peut t'appeler pour vérifier ton inscription. Il n'est jamais public.
                </FormDescription>
                <FormMessage />
              </FormItem>
            )}
          />
        </fieldset>

        <fieldset className="space-y-5">
          <legend className="mb-4 text-lg font-bold text-logo-blue">Tes accès</legend>
          <FormField
            control={form.control}
            name="identifiant"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Identifiant de connexion</FormLabel>
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
          <legend className="sr-only">Accords</legend>
          <CaseAccord control={form.control} name="charte" libelle={<LienCharte />} />
          <CaseAccord
            control={form.control}
            name="consentement"
            libelle="J'accepte que l'équipe des Clubs Santé utilise ces informations pour vérifier mon compte."
          />
        </fieldset>

        <Button
          type="submit"
          disabled={enCours}
          className="btn-fx h-12 w-full rounded-full text-base font-bold"
        >
          {enCours && <Loader2 className="h-5 w-5 animate-spin" />}
          Envoyer ma demande
        </Button>
      </form>
    </Form>
  );
}
