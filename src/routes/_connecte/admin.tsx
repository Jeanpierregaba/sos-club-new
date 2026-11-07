import { useQueryClient } from "@tanstack/react-query";
import {
  createFileRoute,
  Link,
  Outlet,
  redirect,
  useRouter,
  useRouterState,
} from "@tanstack/react-router";
import {
  Download,
  ExternalLink,
  Flag,
  LayoutDashboard,
  LogOut,
  MapPinned,
  Menu,
  ScrollText,
  ShieldCheck,
  Star,
  UserCheck,
  UserCog,
  Users,
  type LucideIcon,
} from "lucide-react";
import { useState } from "react";

import logo from "@/assets/logo.webp";
import { ServiceIndisponible } from "@/components/ServiceIndisponible";
import { Sheet, SheetContent, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { CLE_MOI } from "@/hooks/use-moi";
import { peut, peutExporter, peutVoirInscrits } from "@/lib/admin";
import {
  chargerAdminMoi,
  chargerCatalogue,
  deconnecter,
  ErreurApi,
  type AdminMoi,
  type Catalogue,
} from "@/lib/api/client";

const PAGE_DOUBLE_AUTH = "/admin/double-authentification";

// Garde d'affichage : l'API refuse de toute façon chaque route à qui n'a pas le droit.
export const Route = createFileRoute("/_connecte/admin")({
  beforeLoad: async ({ context, location }) => {
    if (context.moi.role !== "admin") throw redirect({ to: "/mon-espace" });
    let admin: AdminMoi;
    try {
      admin = await chargerAdminMoi();
    } catch (erreur) {
      // Fin d'accès ou session coupée : retour à la connexion. Un 403 s'affiche sur place : renvoyer vers
      // /mon-espace ferait une boucle, puisque cette page renvoie elle-même un admin ici.
      if (erreur instanceof ErreurApi && erreur.statut === 401) {
        throw redirect({ to: "/connexion", search: { redirection: location.href } });
      }
      throw erreur;
    }
    if (admin.double_auth_requise && location.pathname !== PAGE_DOUBLE_AUTH) {
      throw redirect({ to: PAGE_DOUBLE_AUTH });
    }
    return { admin, catalogue: await chargerCatalogue() };
  },
  gcTime: 0,
  head: () => ({
    meta: [
      { title: "Espace admin — Club Santé SOS Docteur TV" },
      { name: "robots", content: "noindex" },
    ],
  }),
  errorComponent: (props) =>
    props.error instanceof ErreurApi && props.error.statut === 403 ? (
      <AccesRefuse />
    ) : (
      <ServiceIndisponible {...props} />
    ),
  component: EspaceAdmin,
});

type Entree = { to: string; libelle: string; i: LucideIcon; visible: boolean; compteur?: number };

function entrees(admin: AdminMoi): Entree[] {
  return [
    {
      to: "/admin",
      libelle: "Tableau de bord",
      i: LayoutDashboard,
      visible: peut(admin, "tableau_de_bord", "consulter"),
    },
    { to: "/admin/inscrits", libelle: "Inscrits", i: Users, visible: peutVoirInscrits(admin) },
    {
      to: "/admin/moderation",
      libelle: "Modération",
      i: ShieldCheck,
      visible: peut(admin, "moderation", "consulter"),
      compteur: admin.contenus_a_moderer ?? 0,
    },
    {
      to: "/admin/encadreurs",
      libelle: "Encadreurs",
      i: UserCheck,
      visible: peut(admin, "encadreurs", "consulter"),
      compteur: admin.encadreurs_a_verifier ?? 0,
    },
    {
      to: "/admin/clubs",
      libelle: "Clubs",
      i: Flag,
      visible: peut(admin, "clubs", "consulter"),
      compteur: admin.clubs_a_valider ?? 0,
    },
    { to: "/admin/exports", libelle: "Exports", i: Download, visible: peutExporter(admin) },
    {
      to: "/admin/referentiel",
      libelle: "Référentiel",
      i: MapPinned,
      visible: peut(admin, "clubs", "consulter"),
    },
    {
      to: "/admin/points",
      libelle: "Points",
      i: Star,
      visible: peut(admin, "points", "consulter"),
    },
    {
      to: "/admin/journal",
      libelle: "Journal d'audit",
      i: ScrollText,
      visible: peut(admin, "journal", "consulter"),
    },
    {
      to: "/admin/collaborateurs",
      libelle: "Collaborateurs",
      i: UserCog,
      visible: admin.super_admin,
    },
  ];
}

function Menu_({
  admin,
  catalogue,
  onNavigue,
}: {
  admin: AdminMoi;
  catalogue: Catalogue;
  onNavigue?: () => void;
}) {
  const chemin = useRouterState({ select: (s) => s.location.pathname });
  const queryClient = useQueryClient();
  const router = useRouter();
  const [enCours, setEnCours] = useState(false);
  const verrouille = admin.double_auth_requise;

  const seDeconnecter = async () => {
    setEnCours(true);
    try {
      await deconnecter();
    } finally {
      queryClient.setQueryData(CLE_MOI, null);
      await router.navigate({ to: "/", replace: true });
    }
  };

  return (
    <div className="flex h-full flex-col bg-night text-white">
      <Link to="/" className="m-5 self-start rounded-2xl bg-white px-3 py-2" onClick={onNavigue}>
        <img
          src={logo}
          alt="Club Santé SOS Docteur TV"
          width={1014}
          height={195}
          className="h-8 w-auto"
        />
      </Link>
      <p className="px-6 text-[11px] font-extrabold uppercase tracking-widest text-sun">
        Espace admin
      </p>
      <nav aria-label="Espace admin" className="mt-3 flex-1 overflow-y-auto px-3 pb-4">
        <ul className="space-y-1">
          {entrees(admin)
            .filter((e) => e.visible && !verrouille)
            .map(({ to, libelle, i: Icone, compteur }) => {
              const actif = to === "/admin" ? chemin === "/admin" : chemin.startsWith(to);
              return (
                <li key={to}>
                  <Link
                    to={to}
                    onClick={onNavigue}
                    aria-current={actif ? "page" : undefined}
                    className={`flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-bold transition ${
                      actif
                        ? "bg-white text-ink shadow-card"
                        : "text-white/80 hover:bg-white/10 hover:text-white"
                    }`}
                  >
                    <Icone className="size-[18px] shrink-0" />
                    {libelle}
                    {Boolean(compteur) && (
                      <span
                        aria-label={`${compteur} à vérifier`}
                        className="ml-auto rounded-full bg-logo-red px-2 py-0.5 text-xs font-extrabold text-white"
                      >
                        {compteur}
                      </span>
                    )}
                  </Link>
                </li>
              );
            })}
        </ul>
        <p className="mt-6 px-3 text-[11px] font-extrabold uppercase tracking-widest text-white/40">
          À venir
        </p>
        <ul className="mt-2 space-y-0.5">
          {catalogue.modules
            .filter((m) => !m.disponible)
            .map((m) => (
              <li
                key={m.id}
                className="flex items-center justify-between gap-2 rounded-xl px-3 py-1.5 text-sm font-semibold text-white/45"
              >
                {m.libelle}
                <span className="rounded-full bg-white/10 px-2 py-0.5 text-[10px] font-extrabold uppercase">
                  Bientôt
                </span>
              </li>
            ))}
        </ul>
      </nav>
      <div className="border-t border-white/10 p-4">
        <p className="truncate text-sm font-extrabold">
          {admin.prenom} {admin.nom}
        </p>
        <p className="truncate text-xs font-semibold text-white/60">
          {admin.super_admin ? "Super-administrateur" : "Collaborateur"} ·{" "}
          {admin.perimetre_dre ? `DRE ${catalogue.dre[admin.perimetre_dre]}` : "National"}
        </p>
        <div className="mt-3 grid gap-1 text-sm font-bold">
          <Link
            to={PAGE_DOUBLE_AUTH}
            onClick={onNavigue}
            className="flex items-center gap-2 rounded-lg px-2 py-1.5 text-white/80 hover:bg-white/10 hover:text-white"
          >
            <ShieldCheck className="size-4" /> Double authentification
          </Link>
          <a
            href="/"
            className="flex items-center gap-2 rounded-lg px-2 py-1.5 text-white/80 hover:bg-white/10 hover:text-white"
          >
            <ExternalLink className="size-4" /> Voir le site
          </a>
          <button
            type="button"
            onClick={seDeconnecter}
            disabled={enCours}
            className="flex items-center gap-2 rounded-lg px-2 py-1.5 text-left text-white/80 hover:bg-white/10 hover:text-white disabled:opacity-50"
          >
            <LogOut className="size-4" /> Me déconnecter
          </button>
        </div>
      </div>
    </div>
  );
}

function EspaceAdmin() {
  const { admin, catalogue } = Route.useRouteContext();
  const [ouvert, setOuvert] = useState(false);

  return (
    <div className="min-h-screen bg-mist-soft text-ink lg:grid lg:grid-cols-[17rem_1fr]">
      <aside className="sticky top-0 hidden h-screen lg:block">
        <Menu_ admin={admin} catalogue={catalogue} />
      </aside>

      <div className="min-w-0">
        <header className="sticky top-0 z-20 flex items-center justify-between gap-3 border-b bg-white/90 px-4 py-3 backdrop-blur lg:hidden">
          <img
            src={logo}
            alt="Club Santé SOS Docteur TV"
            width={1014}
            height={195}
            className="h-8 w-auto"
          />
          <Sheet open={ouvert} onOpenChange={setOuvert}>
            <SheetTrigger
              aria-label="Ouvrir le menu"
              className="inline-flex size-10 items-center justify-center rounded-full border"
            >
              <Menu className="size-5" />
            </SheetTrigger>
            <SheetContent side="left" className="w-72 border-0 p-0">
              <SheetTitle className="sr-only">Menu de l'espace admin</SheetTitle>
              <Menu_ admin={admin} catalogue={catalogue} onNavigue={() => setOuvert(false)} />
            </SheetContent>
          </Sheet>
        </header>
        <main className="mx-auto max-w-6xl px-4 py-6 sm:px-6 lg:px-10 lg:py-10">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

function AccesRefuse() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-mist-soft px-4">
      <div className="max-w-md text-center">
        <h1 className="text-3xl text-logo-blue">
          Accès <span className="text-primary">réservé</span>
        </h1>
        <p className="mt-3 font-medium text-muted-foreground">
          Ton compte n'a pas de profil dans l'espace admin. Demande à un super-administrateur de
          t'inviter.
        </p>
        <a href="/" className="mt-6 inline-block font-bold text-logo-blue hover:underline">
          Retour à l'accueil
        </a>
      </div>
    </main>
  );
}
