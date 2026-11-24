import { zodResolver } from "@hookform/resolvers/zod";
import { useQueryClient } from "@tanstack/react-query";
import { useRouter } from "@tanstack/react-router";
import { ArrowLeft, ArrowRight, Loader2 } from "lucide-react";
import { useRef, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { ChampEtablissement } from "@/components/inscription/ChampEtablissement";
import {
  SectionClub,
  SectionFamille,
  SectionLieu,
  SectionToi,
} from "@/components/inscription/ChampsFiche";
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
  inscrireEleve,
  type AxePublic,
  type Classe,
  type DrePublique,
} from "@/lib/api/client";
import { CHAMPS_ETAPES, FICHE_VIDE, ficheVersApi, schemaFiche } from "@/lib/fiche";
import { CLASSES } from "@/lib/classes";
import { erreurPseudonyme } from "@/lib/pseudonyme";
import {
  corpsEtablissement,
  manqueEtablissement,
  SAISIE_VIDE,
  type SaisieEtablissement,
} from "@/lib/saisie-etablissement";
import { useEtapesInscription } from "@/lib/activite";
import { m } from "@/paraglide/messages.js";

const schema = z.object({
  prenom: z.string().trim().min(1, "Indique ton prénom.").max(100, "Ce prénom est trop long."),
  nom: z.string().trim().min(1, "Indique ton nom.").max(100, "Ce nom est trop long."),
  pseudonyme: z.string().superRefine((valeur, ctx) => {
    const message = erreurPseudonyme(valeur);
    if (message) ctx.addIssue({ code: "custom", message });
  }),
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
  email: z
    .string()
    .trim()
    .max(254, "Cet email est trop long.")
    .refine((v) => v === "" || /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v), "Cet email n'est pas valide."),
  classe: z.string().min(1, "Choisis ta classe."),
  charte: z.boolean().refine((v) => v, "Tu dois accepter la charte."),
  consentement: z.boolean().refine((v) => v, "L'accord de ton parent ou tuteur est nécessaire."),
  // La fiche d'adhésion (spec 030).
  fiche: schemaFiche,
});

type Valeurs = z.infer<typeof schema>;

// Un refus de l'API qui nomme un champ est affiché sous ce champ.
const CHAMPS_NOMMES: [string, keyof Valeurs][] = [
  ["pseudonyme", "pseudonyme"],
  ["identifiant", "identifiant"],
  ["email", "email"],
  ["mot de passe", "motDePasse"],
  // Les mêmes mots en anglais et en allemand (spec 052).
  ["nickname", "pseudonyme"],
  ["username", "identifiant"],
  ["password", "motDePasse"],
  ["benutzername", "identifiant"],
  ["passwort", "motDePasse"],
];

// Les étapes, pour rester lisible sur un téléphone : chaque « Suivant » ne valide que les champs affichés.
const ETAPES = [
  {
    titre: m.elv_etape_compte,
    champs: ["prenom", "nom", "pseudonyme", "classe", "identifiant", "motDePasse", "email"],
  },
  {
    titre: m.elv_etape_toi,
    champs: [...CHAMPS_ETAPES.lieu, ...CHAMPS_ETAPES.toi].map((c) => `fiche.${c}`),
  },
  { titre: m.elv_etape_famille, champs: CHAMPS_ETAPES.famille.map((c) => `fiche.${c}`) },
  { titre: m.elv_etape_club, champs: [] },
] as const;

// Le formulaire d'inscription d'un élève (spec 017), avec sa fiche d'adhésion (spec 030).
export function InscriptionEleve({ dre, axes }: { dre: DrePublique[]; axes: AxePublic[] }) {
  // Spec 051 : formulaire ouvert, puis commencé à la première saisie (événements anonymes).
  const commencer = useEtapesInscription("eleve");
  const queryClient = useQueryClient();
  const router = useRouter();
  const haut = useRef<HTMLDivElement>(null);
  const [erreur, setErreur] = useState<string | null>(null);
  const [etablissement, setEtablissement] = useState<SaisieEtablissement>(SAISIE_VIDE);
  const [erreurEtablissement, setErreurEtablissement] = useState<string | null>(null);
  const [etape, setEtape] = useState(0);

  const form = useForm<Valeurs>({
    resolver: zodResolver(schema),
    defaultValues: {
      prenom: "",
      nom: "",
      pseudonyme: "",
      identifiant: "",
      motDePasse: "",
      email: "",
      classe: "",
      charte: false,
      consentement: false,
      fiche: FICHE_VIDE,
    },
  });

  const allerA = (numero: number) => {
    setEtape(numero);
    haut.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  };
  const suivant = async () => {
    const champs = ETAPES[etape]?.champs ?? [];
    const valide = await form.trigger(champs as unknown as (keyof Valeurs)[], {
      shouldFocus: true,
    });
    if (etape === 0) {
      const manque = manqueEtablissement(etablissement);
      setErreurEtablissement(manque);
      if (manque) return;
    }
    if (valide) {
      // Les champs des étapes suivantes n'ont pas encore été remplis : pas d'erreur avant d'y arriver.
      form.clearErrors();
      allerA(etape + 1);
    }
  };

  const envoyer = form.handleSubmit(
    async (v) => {
      const manque = manqueEtablissement(etablissement);
      setErreurEtablissement(manque);
      if (manque) return;
      setErreur(null);
      try {
        const moi = await inscrireEleve({
          prenom: v.prenom,
          nom: v.nom,
          pseudonyme: v.pseudonyme,
          identifiant: v.identifiant,
          mot_de_passe: v.motDePasse,
          email: v.email || null,
          classe: v.classe as Classe,
          charte: true,
          consentement_parent: true,
          ...corpsEtablissement(etablissement),
          fiche: ficheVersApi(v.fiche),
        });
        queryClient.setQueryData(CLE_MOI, moi);
        await router.navigate({ to: "/mon-espace", search: { bienvenue: true }, replace: true });
      } catch (e) {
        const message = e instanceof ErreurApi ? e.message : m.erreur_indisponible();
        // La saisie est gardée, sauf le mot de passe.
        form.resetField("motDePasse");
        const champ = CHAMPS_NOMMES.find(([mot]) => message.toLowerCase().includes(mot));
        if (champ) {
          // Ces champs sont sur la première étape.
          setEtape(0);
          form.setError(champ[1], { message }, { shouldFocus: true });
        } else {
          setErreur(message);
          haut.current?.scrollIntoView({ behavior: "smooth", block: "center" });
        }
      }
    },
    (erreurs) => {
      setErreurEtablissement(manqueEtablissement(etablissement));
      // Une erreur restée sur une étape précédente : on y retourne.
      const premiere = ETAPES.findIndex((e) =>
        e.champs.some((c) => {
          const [racine, sous] = c.split(".");
          return sous
            ? erreurs.fiche?.[sous as keyof typeof erreurs.fiche]
            : erreurs[racine as keyof Valeurs];
        }),
      );
      if (premiere >= 0 && premiere < etape) allerA(premiere);
    },
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

        <ol className="flex gap-2" aria-label={m.elv_etapes()}>
          {ETAPES.map((e, i) => (
            <li key={i} className="min-w-0 flex-1">
              <span
                aria-current={i === etape ? "step" : undefined}
                className={`block h-1.5 rounded-full ${i <= etape ? "bg-primary" : "bg-border"}`}
              />
              <span
                className={`mt-1.5 block truncate text-xs font-bold ${
                  i === etape ? "text-ink" : "text-muted-foreground"
                }`}
              >
                {i + 1}. {e.titre()}
              </span>
            </li>
          ))}
        </ol>

        <div hidden={etape !== 0} className="space-y-6">
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
            <p className="-mt-2 text-sm font-medium text-muted-foreground">{m.elv_prives()}</p>
            <FormField
              control={form.control}
              name="pseudonyme"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>{m.elv_pseudonyme()}</FormLabel>
                  <FormControl>
                    <Input {...field} autoComplete="nickname" className={CHAMP} />
                  </FormControl>
                  <FormDescription>{m.elv_pseudonyme_aide()}</FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="classe"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>{m.elv_classe()}</FormLabel>
                  <FormControl>
                    <select {...field} className={LISTE}>
                      <option value="">{m.elv_choisis_classe()}</option>
                      {CLASSES.map((c) => (
                        <option key={c.valeur} value={c.valeur}>
                          {c.libelle}
                        </option>
                      ))}
                    </select>
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
                  <FormDescription>{m.elv_identifiant_aide()}</FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />
            <ChampMotDePasse control={form.control} name="motDePasse" />
            <FormField
              control={form.control}
              name="email"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>
                    {m.elv_email()}{" "}
                    <span className="font-medium text-muted-foreground">{m.vis_facultatif()}</span>
                  </FormLabel>
                  <FormControl>
                    <Input
                      {...field}
                      type="email"
                      autoComplete="email"
                      autoCapitalize="none"
                      className={CHAMP}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </fieldset>
        </div>

        <div hidden={etape !== 1} className="space-y-8">
          <SectionLieu />
          <SectionToi />
        </div>
        <div hidden={etape !== 2}>
          <SectionFamille />
        </div>
        <div hidden={etape !== 3} className="space-y-6">
          <SectionClub axes={axes} />

          <fieldset className="space-y-4 rounded-2xl bg-mist-soft p-4">
            <legend className="sr-only">{m.vis_accords()}</legend>
            <CaseAccord control={form.control} name="charte" libelle={<LienCharte />} />
            <CaseAccord
              control={form.control}
              name="consentement"
              libelle={m.elv_accord_parent()}
            />
          </fieldset>
        </div>

        <div className="flex gap-3">
          {etape > 0 && (
            <Button
              type="button"
              variant="outline"
              onClick={() => allerA(etape - 1)}
              className="h-12 rounded-full px-5 text-base font-bold"
            >
              <ArrowLeft className="h-5 w-5" /> {m.cnx_retour()}
            </Button>
          )}
          {etape < ETAPES.length - 1 ? (
            <Button
              type="button"
              onClick={() => void suivant()}
              className="btn-fx h-12 flex-1 rounded-full text-base font-bold"
            >
              {m.elv_suivant()} <ArrowRight className="h-5 w-5" />
            </Button>
          ) : (
            <Button
              type="submit"
              disabled={enCours}
              className="btn-fx h-12 flex-1 rounded-full text-base font-bold"
            >
              {enCours && <Loader2 className="h-5 w-5 animate-spin" />}
              {m.elv_creer()}
            </Button>
          )}
        </div>
      </form>
    </Form>
  );
}
