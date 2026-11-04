import { zodResolver } from "@hookform/resolvers/zod";
import { useQueryClient } from "@tanstack/react-query";
import { createFileRoute, Link, redirect, useRouter } from "@tanstack/react-router";
import { ArrowLeft, Eye, EyeOff, Lock, Loader2, School, Sparkles } from "lucide-react";
import { useRef, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import logo from "@/assets/logo.webp";
import mascottesEquipe from "@/assets/mascottes-equipe.webp";
import { ChoixEtablissement, type EtablissementChoisi } from "@/components/ChoixEtablissement";
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
  chargerDre,
  chargerEtatInscription,
  chargerMoi,
  ErreurApi,
  inscrireEleve,
  MESSAGE_INDISPONIBLE,
  type Classe,
} from "@/lib/api/client";
import { CLASSES } from "@/lib/classes";
import { erreurPseudonyme } from "@/lib/pseudonyme";

export const Route = createFileRoute("/inscription")({
  beforeLoad: async () => {
    const moi = await chargerMoi().catch(() => null);
    if (moi) throw redirect({ to: "/mon-espace" });
  },
  // API en panne : la page s'affiche et explique pourquoi l'inscription n'est pas possible.
  loader: async () => {
    const [etat, dre] = await Promise.all([
      chargerEtatInscription().catch(() => null),
      chargerDre().catch(() => []),
    ]);
    return { etat, dre };
  },
  head: () => ({
    meta: [
      { title: "Inscription — Club Santé SOS Docteur TV" },
      {
        name: "description",
        content:
          "Crée ton compte élève des Clubs Santé : quiz, points, classements et certification.",
      },
    ],
  }),
  component: Inscription,
});

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
});

type Valeurs = z.infer<typeof schema>;

// Un refus de l'API qui nomme un champ est affiché sous ce champ.
const CHAMPS_NOMMES: [string, keyof Valeurs][] = [
  ["pseudonyme", "pseudonyme"],
  ["identifiant", "identifiant"],
  ["email", "email"],
  ["mot de passe", "motDePasse"],
];

const atouts = [
  "Des points de bienvenue dès ton inscription",
  "Des quiz santé et la certification Génie Imhotep",
  "Ton pseudonyme dans les classements, jamais ton nom",
];

function Inscription() {
  const { etat } = Route.useLoaderData();

  return (
    <main className="grid min-h-screen bg-carnet lg:grid-cols-[0.9fr_1.1fr]">
      <section className="relative isolate hidden overflow-hidden bg-linear-to-br from-logo-blue to-night p-10 text-white lg:flex lg:flex-col xl:p-14">
        <div aria-hidden className="pointer-events-none absolute inset-0 -z-10">
          <div className="absolute inset-0 bg-[radial-gradient(oklch(1_0_0/0.14)_1.5px,transparent_1.5px)] bg-size-[22px_22px] [mask-image:linear-gradient(to_bottom,black,transparent_70%)]" />
          <div className="absolute -right-40 -top-40 size-[36rem] rounded-full border-[3rem] border-white/5" />
          <div className="absolute -bottom-24 left-1/4 size-96 rounded-full bg-primary/25 blur-3xl" />
        </div>
        <Link
          to="/"
          aria-label="Retour à l'accueil"
          className="self-start rounded-2xl bg-white px-4 py-2.5 shadow-card transition hover:scale-105"
        >
          <img src={logo} alt="" width={1014} height={195} className="h-9 w-auto" />
        </Link>
        <p className="mt-12 font-display text-5xl leading-[0.95] xl:text-6xl">
          <span className="block">Rejoins</span>
          <span className="block text-sun">les Clubs Santé</span>
        </p>
        <ul className="mt-8 space-y-3">
          {atouts.map((t) => (
            <li key={t} className="flex items-center gap-3 font-semibold text-white/90">
              <span className="inline-flex size-9 shrink-0 items-center justify-center rounded-xl bg-white/10 text-sun ring-1 ring-white/15">
                <Sparkles className="size-5" />
              </span>
              {t}
            </li>
          ))}
        </ul>
        <img
          src={mascottesEquipe}
          alt="Les sept mascottes des Clubs Santé"
          width={1122}
          height={1402}
          className="mx-auto -mb-10 mt-auto w-full max-w-sm pt-8 drop-shadow-[0_24px_40px_oklch(0_0_0/0.35)] xl:-mb-14"
        />
      </section>

      <section className="flex flex-col items-center px-4 py-10 sm:px-8">
        <Link
          to="/"
          aria-label="Retour à l'accueil"
          className="transition hover:scale-105 lg:hidden"
        >
          <img
            src={logo}
            alt="Club Santé SOS Docteur TV"
            width={1014}
            height={195}
            className="h-11 w-auto"
          />
        </Link>
        <div className="mt-8 w-full max-w-xl lg:mt-0">
          <p className="flex items-center gap-3 text-sm font-extrabold uppercase tracking-widest text-logo-red">
            <span className="h-1 w-8 rounded-full bg-primary" />
            Compte élève
          </p>
          <h1 className="mt-3 text-4xl leading-tight md:text-5xl">
            <span className="text-logo-blue">Crée ton</span>{" "}
            <span className="text-primary">compte</span>
          </h1>
          <p className="mt-2 mb-8 text-lg font-medium text-muted-foreground">
            Quelques minutes suffisent. Tu peux participer même si ton établissement n'a pas encore
            de Club Santé.
          </p>
          <div className="rounded-3xl bg-white p-6 shadow-card ring-1 ring-border sm:p-8">
            {etat === null ? (
              <Alert variant="destructive">
                <AlertDescription>{MESSAGE_INDISPONIBLE}</AlertDescription>
              </Alert>
            ) : !etat.ouvertes ? (
              <div className="flex items-start gap-3 rounded-2xl bg-mist-soft p-4">
                <Lock aria-hidden className="mt-0.5 size-5 shrink-0 text-logo-blue" />
                <p className="font-medium text-ink/80">
                  Les inscriptions ne sont pas encore ouvertes. Elles ouvriront avec le lancement
                  officiel de la plateforme : reviens bientôt !
                </p>
              </div>
            ) : (
              <FormulaireInscription />
            )}
          </div>
          <p className="mt-6 text-center text-sm font-semibold text-muted-foreground">
            Déjà un compte ?{" "}
            <Link
              to="/connexion"
              className="font-bold text-logo-blue underline-offset-4 hover:underline"
            >
              Connecte-toi
            </Link>
          </p>
          <Link
            to="/"
            className="mx-auto mt-3 flex w-fit items-center gap-1.5 text-sm font-bold text-logo-blue underline-offset-4 hover:underline"
          >
            <ArrowLeft className="size-4" /> Retour à l’accueil
          </Link>
        </div>
      </section>
    </main>
  );
}

const CHAMP = "h-12 text-base";
const LISTE =
  "h-12 w-full rounded-md border border-input bg-white px-3 text-base font-medium outline-none focus-visible:ring-2 focus-visible:ring-ring";

function FormulaireInscription() {
  const { dre } = Route.useLoaderData();
  const queryClient = useQueryClient();
  const router = useRouter();
  const haut = useRef<HTMLDivElement>(null);
  const [erreur, setErreur] = useState<string | null>(null);
  const [afficher, setAfficher] = useState(false);
  const [etablissement, setEtablissement] = useState<EtablissementChoisi | null>(null);
  const [proposer, setProposer] = useState(false);
  const [dreProposee, setDreProposee] = useState("");
  const [iesgProposee, setIesgProposee] = useState("");
  const [nomPropose, setNomPropose] = useState("");
  const [erreurEtablissement, setErreurEtablissement] = useState<string | null>(null);

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
    },
  });
  const inspections = dre.find((d) => d.code === dreProposee)?.iesg ?? [];

  const verifierEtablissement = () => {
    if (!proposer && !etablissement) return "Choisis ton établissement dans la liste.";
    if (proposer && (!iesgProposee || nomPropose.trim().length < 2))
      return "Indique ta DRE, ton inspection et le nom de ton établissement.";
    return null;
  };

  const envoyer = form.handleSubmit(
    async (v) => {
      const manque = verifierEtablissement();
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
          ...(proposer
            ? { proposition: { iesg_id: iesgProposee, nom: nomPropose } }
            : { etablissement_id: etablissement?.id ?? null }),
        });
        queryClient.setQueryData(CLE_MOI, moi);
        await router.navigate({ to: "/mon-espace", search: { bienvenue: true }, replace: true });
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
    () => setErreurEtablissement(verifierEtablissement()),
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

        <fieldset className="space-y-3">
          <legend className="mb-2 flex items-center gap-2 text-lg font-bold text-logo-blue">
            <School aria-hidden className="size-5" /> Ton établissement
          </legend>
          {proposer ? (
            <div className="space-y-4 rounded-2xl bg-mist-soft p-4">
              <p className="text-sm font-medium text-ink/80">
                L'équipe nationale vérifiera ton établissement avant de l'ajouter à la liste. Tu
                peux utiliser la plateforme dès maintenant.
              </p>
              <label className="block space-y-2">
                <span className="text-sm font-semibold">Direction régionale (DRE)</span>
                <select
                  value={dreProposee}
                  onChange={(e) => {
                    setDreProposee(e.target.value);
                    setIesgProposee("");
                  }}
                  aria-invalid={Boolean(erreurEtablissement) && !dreProposee}
                  className={LISTE}
                >
                  <option value="">Choisis ta DRE</option>
                  {dre.map((d) => (
                    <option key={d.code} value={d.code}>
                      {d.nom}
                    </option>
                  ))}
                </select>
              </label>
              <label className="block space-y-2">
                <span className="text-sm font-semibold">Inspection (IESG)</span>
                <select
                  value={iesgProposee}
                  onChange={(e) => setIesgProposee(e.target.value)}
                  disabled={!dreProposee}
                  aria-invalid={Boolean(erreurEtablissement) && !iesgProposee}
                  className={LISTE}
                >
                  <option value="">Choisis ton inspection</option>
                  {inspections.map((i) => (
                    <option key={i.id} value={i.id}>
                      {i.nom}
                      {i.zone ? ` — ${i.zone}` : ""}
                    </option>
                  ))}
                </select>
              </label>
              <label className="block space-y-2">
                <span className="text-sm font-semibold">Nom de l'établissement</span>
                <Input
                  value={nomPropose}
                  onChange={(e) => setNomPropose(e.target.value)}
                  aria-invalid={Boolean(erreurEtablissement) && nomPropose.trim().length < 2}
                  maxLength={150}
                  className={CHAMP}
                />
              </label>
              <button
                type="button"
                onClick={() => setProposer(false)}
                className="text-sm font-bold text-logo-blue underline-offset-4 hover:underline"
              >
                Revenir à la recherche
              </button>
            </div>
          ) : (
            <>
              <ChoixEtablissement
                valeur={etablissement}
                onChoix={(choix) => {
                  setEtablissement(choix);
                  if (choix) setErreurEtablissement(null);
                }}
                invalide={Boolean(erreurEtablissement)}
              />
              {!etablissement && dre.length > 0 && (
                <button
                  type="button"
                  onClick={() => setProposer(true)}
                  className="text-sm font-bold text-logo-blue underline-offset-4 hover:underline"
                >
                  Je ne trouve pas mon établissement
                </button>
              )}
            </>
          )}
          {erreurEtablissement && (
            <p role="alert" className="text-sm font-medium text-destructive">
              {erreurEtablissement}
            </p>
          )}
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
                <FormDescription>Il reste secret : note-le bien.</FormDescription>
                <FormMessage />
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name="motDePasse"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Mot de passe</FormLabel>
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
                    aria-label={afficher ? "Masquer le mot de passe" : "Afficher le mot de passe"}
                    className="absolute inset-y-0 right-0 flex w-12 items-center justify-center rounded-r-md text-muted-foreground transition hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  >
                    {afficher ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                  </button>
                </div>
                <FormDescription>Au moins 8 caractères.</FormDescription>
                <FormMessage />
              </FormItem>
            )}
          />
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

        <fieldset className="space-y-4 rounded-2xl bg-mist-soft p-4">
          <legend className="sr-only">Accords</legend>
          <Case
            nom="charte"
            form={form}
            libelle={
              <>
                J'ai lu et j'accepte la{" "}
                <a
                  href="/charte"
                  target="_blank"
                  rel="noreferrer"
                  className="font-bold text-logo-blue underline underline-offset-4"
                >
                  charte des Clubs Santé
                </a>
                .
              </>
            }
          />
          <Case
            nom="consentement"
            form={form}
            libelle="Mon parent ou tuteur est d'accord pour que je m'inscrive."
          />
        </fieldset>

        <Button
          type="submit"
          disabled={enCours}
          className="btn-fx h-12 w-full rounded-full text-base font-bold"
        >
          {enCours && <Loader2 className="h-5 w-5 animate-spin" />}
          Créer mon compte
        </Button>
      </form>
    </Form>
  );
}

function Case({
  nom,
  form,
  libelle,
}: {
  nom: "charte" | "consentement";
  form: ReturnType<typeof useForm<Valeurs>>;
  libelle: React.ReactNode;
}) {
  return (
    <FormField
      control={form.control}
      name={nom}
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
