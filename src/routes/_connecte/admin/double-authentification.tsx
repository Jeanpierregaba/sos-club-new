import { createFileRoute, useRouter } from "@tanstack/react-router";
import { Check, Copy, Download, KeyRound, Loader2, ShieldCheck, Smartphone } from "lucide-react";
import { useState } from "react";

import { ChampCode } from "@/components/admin/ChampCode";
import { EnTeteAdmin } from "@/components/admin/EnTeteAdmin";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
  commencerEnrolement,
  confirmerEnrolement,
  ErreurApi,
  MESSAGE_INDISPONIBLE,
  regenererCodesSecours,
  type Enrolement,
} from "@/lib/api/client";

export const Route = createFileRoute("/_connecte/admin/double-authentification")({
  component: DoubleAuthentification,
});

const message = (e: unknown) => (e instanceof ErreurApi ? e.message : MESSAGE_INDISPONIBLE);

function DoubleAuthentification() {
  const { admin } = Route.useRouteContext();
  const router = useRouter();
  const [enrolement, setEnrolement] = useState<Enrolement | null>(null);
  const [code, setCode] = useState("");
  const [codes, setCodes] = useState<string[] | null>(null);
  const [erreur, setErreur] = useState<string | null>(null);
  const [enCours, setEnCours] = useState(false);

  const commencer = async () => {
    setErreur(null);
    setEnCours(true);
    try {
      setEnrolement(await commencerEnrolement());
    } catch (e) {
      setErreur(message(e));
    } finally {
      setEnCours(false);
    }
  };

  const confirmer = async (saisie: string) => {
    if (enCours || saisie.length !== 6) return;
    setErreur(null);
    setEnCours(true);
    try {
      const reponse = admin.double_auth_active
        ? await regenererCodesSecours(saisie)
        : await confirmerEnrolement(saisie);
      setCodes(reponse.codes);
      setEnrolement(null);
    } catch (e) {
      setErreur(message(e));
      setCode("");
    } finally {
      setEnCours(false);
    }
  };

  if (codes) {
    return (
      <CodesDeSecours
        codes={codes}
        onTermine={async () => {
          await router.invalidate();
          await router.navigate({ to: "/admin" });
        }}
      />
    );
  }

  return (
    <div className="space-y-8">
      <EnTeteAdmin sur="Sécurité du compte" bleu="Double" vert="authentification">
        Un code à 6 chiffres, donné par une application sur ton téléphone, protège ton compte même
        si ton mot de passe est découvert.
      </EnTeteAdmin>

      {admin.double_auth_requise && (
        <Alert className="rounded-2xl border-sun bg-sun/15">
          <ShieldCheck className="size-4" />
          <AlertDescription className="font-semibold text-ink">
            Tes droits sont sensibles : active la double authentification pour accéder à l'espace
            admin.
          </AlertDescription>
        </Alert>
      )}
      {erreur && (
        <Alert variant="destructive">
          <AlertDescription>{erreur}</AlertDescription>
        </Alert>
      )}

      {admin.double_auth_active ? (
        <section className="max-w-xl rounded-3xl bg-white p-6 shadow-sm ring-1 ring-border">
          <p className="flex items-center gap-2 font-extrabold text-primary">
            <Check className="size-5" /> La double authentification est active.
          </p>
          <p className="mt-3 text-sm font-medium text-muted-foreground">
            Tu as perdu tes codes de secours, ou tu en as utilisé plusieurs ? Saisis un code de ton
            application pour en générer 10 nouveaux. Les anciens cesseront de fonctionner.
          </p>
          <div className="mt-5 space-y-3">
            <ChampCode
              id="code-regeneration"
              valeur={code}
              onChange={setCode}
              desactive={enCours}
            />
            <Button
              onClick={() => confirmer(code)}
              disabled={enCours || code.length !== 6}
              className="btn-fx h-11 w-full rounded-full font-bold"
            >
              {enCours && <Loader2 className="size-4 animate-spin" />}
              Générer de nouveaux codes de secours
            </Button>
          </div>
        </section>
      ) : enrolement ? (
        <section className="grid gap-6 rounded-3xl bg-white p-6 shadow-sm ring-1 ring-border md:grid-cols-[auto_1fr] md:p-8">
          <div className="mx-auto">
            <div
              className="rounded-2xl bg-white p-2 ring-1 ring-border [&>svg]:size-52"
              role="img"
              aria-label="QR code à scanner avec ton application d'authentification"
              // SVG produit par notre API (segno), sans contenu fourni par un utilisateur.
              dangerouslySetInnerHTML={{ __html: enrolement.qr_svg }}
            />
          </div>
          <div className="space-y-4">
            <ol className="space-y-2 text-sm font-medium">
              <li>
                <strong>1.</strong> Installe une application d'authentification : Google
                Authenticator, Microsoft Authenticator, 2FAS…
              </li>
              <li>
                <strong>2.</strong> Scanne le QR code. Sans appareil photo, saisis cette clé :
                <code className="mt-1 block break-all rounded-lg bg-mist-soft px-2 py-1 font-mono text-xs">
                  {enrolement.secret}
                </code>
              </li>
              <li>
                <strong>3.</strong> Saisis le code à 6 chiffres affiché par l'application.
              </li>
            </ol>
            <ChampCode
              id="code-enrolement"
              valeur={code}
              onChange={setCode}
              onComplet={confirmer}
              desactive={enCours}
            />
            <Button
              onClick={() => confirmer(code)}
              disabled={enCours || code.length !== 6}
              className="btn-fx h-11 w-full rounded-full font-bold"
            >
              {enCours && <Loader2 className="size-4 animate-spin" />}
              Activer
            </Button>
          </div>
        </section>
      ) : (
        <section className="max-w-xl rounded-3xl bg-white p-6 shadow-sm ring-1 ring-border">
          <Smartphone className="size-10 text-logo-blue" />
          <p className="mt-3 font-medium text-ink/80">
            Il te faut ton téléphone et une application d'authentification. L'activation prend une
            minute.
          </p>
          <Button
            onClick={commencer}
            disabled={enCours}
            className="btn-fx mt-5 h-11 rounded-full px-6 font-bold"
          >
            {enCours && <Loader2 className="size-4 animate-spin" />}
            Commencer
          </Button>
        </section>
      )}
    </div>
  );
}

// Montrés une seule fois : l'API n'en garde que l'empreinte.
function CodesDeSecours({ codes, onTermine }: { codes: string[]; onTermine: () => void }) {
  const [copie, setCopie] = useState(false);
  const [note, setNote] = useState(false);
  const texte = `Codes de secours — Espace admin Clubs Santé\nChaque code ne sert qu'une fois.\n\n${codes.join("\n")}\n`;

  return (
    <div className="space-y-6">
      <EnTeteAdmin sur="Dernière étape" bleu="Tes codes" vert="de secours">
        Si tu perds ton téléphone, chacun de ces codes remplace une fois le code de l'application.
        Ils ne seront plus jamais affichés : garde-les en lieu sûr.
      </EnTeteAdmin>
      <section className="max-w-xl rounded-3xl bg-white p-6 shadow-sm ring-1 ring-border">
        <ul className="grid grid-cols-2 gap-2 font-mono text-sm">
          {codes.map((c) => (
            <li key={c} className="rounded-lg bg-mist-soft px-3 py-2 text-center">
              {c}
            </li>
          ))}
        </ul>
        <div className="mt-4 flex flex-wrap gap-2">
          <Button
            variant="outline"
            className="rounded-full font-bold"
            onClick={async () => {
              await navigator.clipboard.writeText(texte);
              setCopie(true);
            }}
          >
            {copie ? <Check className="size-4" /> : <Copy className="size-4" />}
            {copie ? "Copiés" : "Copier"}
          </Button>
          <Button asChild variant="outline" className="rounded-full font-bold">
            <a
              href={`data:text/plain;charset=utf-8,${encodeURIComponent(texte)}`}
              download="codes-de-secours-clubs-sante.txt"
            >
              <Download className="size-4" /> Télécharger
            </a>
          </Button>
        </div>
        <label className="mt-6 flex items-start gap-3 text-sm font-semibold">
          <input
            type="checkbox"
            checked={note}
            onChange={(e) => setNote(e.target.checked)}
            className="mt-0.5 size-4 accent-[var(--primary)]"
          />
          J'ai noté mes codes de secours en lieu sûr.
        </label>
        <Button
          onClick={onTermine}
          disabled={!note}
          className="btn-fx mt-4 h-11 w-full rounded-full font-bold"
        >
          <KeyRound className="size-4" /> Continuer
        </Button>
      </section>
    </div>
  );
}
