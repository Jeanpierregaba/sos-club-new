import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  Outlet,
  Link,
  createRootRouteWithContext,
  redirect,
  useRouter,
  HeadContent,
  Scripts,
  type ErrorComponentProps,
} from "@tanstack/react-router";
import { useEffect, type ReactNode } from "react";

import appCss from "../styles.css?url";
import { RetourEnHaut } from "@/components/RetourEnHaut";
import { endroitDuClic, lienInscription, pageVue, signaler } from "@/lib/activite";
import { chargerAdminMoi, chargerEtatSite } from "@/lib/api/client";

function NotFoundComponent() {
  // Spec 051 : la page introuvable compte, avec l'adresse demandée (l'API n'en garde qu'un premier segment lisible).
  useEffect(() => {
    signaler({ type: "erreur", chemin: window.location.pathname.slice(0, 200), detail: "404" });
  }, []);
  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="max-w-md text-center">
        <h1 className="text-7xl font-bold text-foreground">404</h1>
        <h2 className="mt-4 text-xl font-semibold text-foreground">Page introuvable</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          La page que tu cherches n'existe pas ou a été déplacée.
        </p>
        <div className="mt-6">
          <Link
            to="/"
            className="inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
          >
            Retour à l'accueil
          </Link>
        </div>
      </div>
    </div>
  );
}

function ErrorComponent({ error, reset }: ErrorComponentProps) {
  console.error(error);
  const router = useRouter();

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="max-w-md text-center">
        <h1 className="text-xl font-semibold tracking-tight text-foreground">
          Cette page n'a pas pu se charger
        </h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Un problème est survenu de notre côté. Tu peux réessayer ou revenir à l'accueil.
        </p>
        <div className="mt-6 flex flex-wrap justify-center gap-2">
          <button
            onClick={() => {
              router.invalidate();
              reset();
            }}
            className="inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
          >
            Réessayer
          </button>
          <a
            href="/"
            className="inline-flex items-center justify-center rounded-md border border-input bg-background px-4 py-2 text-sm font-medium text-foreground transition-colors hover:bg-accent"
          >
            Retour à l'accueil
          </a>
        </div>
      </div>
    </div>
  );
}

export const Route = createRootRouteWithContext<{ queryClient: QueryClient }>()({
  // Garde d'affichage du mode maintenance (spec 047) : l'API bloque de toute façon chaque route.
  beforeLoad: async ({ location }) => {
    if (["/maintenance", "/connexion", "/activation"].includes(location.pathname)) return;

    let etat;
    try {
      etat = await chargerEtatSite();
    } catch {
      // API injoignable : les pages affichent leur propre erreur, ce n'est pas la maintenance.
      return;
    }
    if (!etat.maintenance) return;

    // Seul un super-administrateur connecté contourne la maintenance, comme côté API.
    try {
      const admin = await chargerAdminMoi();
      if (admin.super_admin) return;
    } catch {
      // Visiteur, élève, encadreur ou collaborateur non super-admin : on affiche la page.
    }
    throw redirect({ to: "/maintenance" });
  },
  head: () => ({
    meta: [
      { charSet: "utf-8" },
      { name: "viewport", content: "width=device-width, initial-scale=1" },
      { title: "Club Santé" },
      { name: "description", content: "Club Santé — jeunes en bonne santé" },
      { name: "author", content: "Club Santé SOS Docteur TV" },
      { property: "og:title", content: "Club Santé" },
      { property: "og:description", content: "Club Santé — jeunes en bonne santé" },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
    links: [
      {
        rel: "stylesheet",
        href: appCss,
      },
      { rel: "preconnect", href: "https://fonts.googleapis.com" },
      {
        rel: "stylesheet",
        href: "https://fonts.googleapis.com/css2?family=Lilita+One&family=Caveat+Brush&family=Outfit:wght@400;500;600;700;800&display=swap",
      },
      { rel: "icon", href: "/favicon.ico", type: "image/x-icon" },
      { rel: "apple-touch-icon", href: "/apple-touch-icon.png" },
    ],
  }),
  shellComponent: RootShell,
  component: RootComponent,
  notFoundComponent: NotFoundComponent,
  errorComponent: ErrorComponent,
});

function RootShell({ children }: { children: ReactNode }) {
  return (
    <html lang="fr">
      <head>
        <HeadContent />
      </head>
      <body>
        {children}
        <Scripts />
      </body>
    </html>
  );
}

function RootComponent() {
  const { queryClient } = Route.useRouteContext();

  return (
    <QueryClientProvider client={queryClient}>
      {/* Required: nested routes render here. Removing <Outlet /> breaks all child routes. */}
      <Outlet />
      <RetourEnHaut />
      <SuiviActivite />
    </QueryClientProvider>
  );
}

/** Pages vues et clics « S'inscrire » (spec 051) : des événements anonymes, sans cookie. */
function SuiviActivite() {
  const router = useRouter();
  useEffect(() => {
    let derniere: string | null = null;
    const cheminActuel = () => {
      const correspondance = router.state.matches.at(-1);
      if (!correspondance) return null;
      const route = router.routesById[correspondance.routeId as keyof typeof router.routesById] as {
        fullPath: string;
      };
      return { fullPath: route.fullPath, params: correspondance.params as Record<string, string> };
    };
    const surPage = () => {
      // Une même page ne compte qu'une fois, même résolue deux fois au chargement ou quand seuls ses filtres
      // (`?…`) changent.
      const adresse = router.state.location.pathname;
      if (adresse === derniere) return;
      const introuvable = router.state.matches.some(
        (m) => m.status === "notFound" || (m as { globalNotFound?: boolean }).globalNotFound,
      );
      const actuel = cheminActuel();
      if (introuvable || !actuel) return;
      const evenement = pageVue(
        actuel,
        derniere === null
          ? { referent: document.referrer, recherche: window.location.search }
          : null,
      );
      derniere = adresse;
      if (evenement) signaler(evenement);
    };
    const surClic = (e: MouseEvent) => {
      const lien = lienInscription(e.target);
      const actuel = cheminActuel();
      if (!lien || !actuel) return;
      const page = pageVue(actuel, null)?.chemin ?? "autre";
      signaler({
        type: "clic_inscription",
        chemin: page,
        detail: endroitDuClic(lien, window.location.pathname),
      });
    };
    surPage();
    const desabonner = router.subscribe("onResolved", surPage);
    document.addEventListener("click", surClic, true);
    return () => {
      desabonner();
      document.removeEventListener("click", surClic, true);
    };
  }, [router]);
  return null;
}
