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
  MESSAGE_INDISPONIBLE,
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
];

// Les étapes, pour rester lisible sur un téléphone : chaque « Suivant » ne valide que les champs affichés.
const ETAPES = [
  {
    titre: "Ton compte",
    champs: ["prenom", "nom", "pseudonyme", "classe", "identifiant", "motDePasse", "email"],
  },
  {
    titre: "Toi",
    champs: [...CHAMPS_ETAPES.lieu, ...CHAMPS_ETAPES.toi].map((c) => `fiche.${c}`),
  },
  { titre: "Ta famille", champs: CHAMPS_ETAPES.famille.map((c) => `fiche.${c}`) },
  { titre: "Ton club", champs: [] },
] as const;

// Le formulaire d'inscription d'un élève (spec 017), avec sa fiche d'adhésion (spec 030).
export function InscriptionEleve({ dre, axes }: { dre: DrePublique[]; axes: AxePublic[] }) {
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
    if (valide) allerA(etape + 1);
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
        const message = e instanceof ErreurApi ? e.message : MESSAGE_INDISPONIBLE;
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
      <form onSubmit={envoyer} noValidate className="space-y-6">
        <div ref={haut}>
          {erreur && (
            <Alert variant="destructive" role="alert">
              <AlertDescription>{erreur}</AlertDescription>
            </Alert>
          )}
        </div>

        <ol className="flex gap-2" aria-label="Étapes de l'inscription">
          {ETAPES.map((e, i) => (
            <li key={e.titre} className="min-w-0 flex-1">
              <span
                aria-current={i === etape ? "step" : undefined}
                className={`block h-1.5 rounded-full ${i <= etape ? "bg-primary" : "bg-border"}`}
              />
              <span
                className={`mt-1.5 block truncate text-xs font-bold ${
                  i === etape ? "text-ink" : "text-muted-foreground"
                }`}
              >
                {i + 1}. {e.titre}
              </span>
            </li>
          ))}
        </ol>

        <div hidden={etape !== 0} className="space-y-6">
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
            <p className="-mt-2 text-sm font-medium text-muted-foreground">
              Ton prénom et ton nom restent privés : seule l'équipe nationale les voit.
            </p>
            <FormField
              control={form.control}
              name="pseudonyme"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Pseudonyme</FormLabel>
                  <FormControl>
                    <Input {...field} autoComplete="nickname" className={CHAMP} />
                  </FormControl>
                  <FormDescription>
                    C'est ton nom public, dans les classements. Il ne peut pas être ton identifiant.
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="classe"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Classe</FormLabel>
                  <FormControl>
                    <select {...field} className={LISTE}>
                      <option value="">Choisis ta classe</option>
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
                  <FormDescription>Il reste secret : note-le bien.</FormDescription>
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
                    Email <span className="font-medium text-muted-foreground">(facultatif)</span>
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
            <legend className="sr-only">Accords</legend>
            <CaseAccord control={form.control} name="charte" libelle={<LienCharte />} />
            <CaseAccord
              control={form.control}
              name="consentement"
              libelle="Mon parent ou tuteur est d'accord pour que je m'inscrive."
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
              <ArrowLeft className="h-5 w-5" /> Retour
            </Button>
          )}
          {etape < ETAPES.length - 1 ? (
            <Button
              type="button"
              onClick={() => void suivant()}
              className="btn-fx h-12 flex-1 rounded-full text-base font-bold"
            >
              Suivant <ArrowRight className="h-5 w-5" />
            </Button>
          ) : (
            <Button
              type="submit"
              disabled={enCours}
              className="btn-fx h-12 flex-1 rounded-full text-base font-bold"
            >
              {enCours && <Loader2 className="h-5 w-5 animate-spin" />}
              Créer mon compte
            </Button>
          )}
        </div>
      </form>
    </Form>
  );
}
