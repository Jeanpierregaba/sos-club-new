import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  Outlet,
  createRootRouteWithContext,
  redirect,
  useRouter,
  useRouterState,
  HeadContent,
  Scripts,
  type ErrorComponentProps,
} from "@tanstack/react-router";
import { useEffect, type ReactNode } from "react";

import appCss from "../styles.css?url";
import { RetourEnHaut } from "@/components/RetourEnHaut";
import { endroitDuClic, lienInscription, pageVue, signaler } from "@/lib/activite";
import { origineDuSite } from "@/lib/origine";
import { chargerAdminMoi, chargerEtatSite } from "@/lib/api/client";
import {
  langueCourante,
  langueDeLAdresse,
  liensHreflang,
  localiser,
  redirectionLangue,
} from "@/lib/langues";
import { m } from "@/paraglide/messages.js";

function NotFoundComponent() {
  // Spec 052 : une adresse inconnue sous `/en` ou `/de` répond dans la langue de son préfixe.
  const langue = useRouterState({
    select: (etat) => langueDeLAdresse(etat.location.publicHref),
  });
  const options = { locale: langue };
  // Spec 051 : la page introuvable compte, avec l'adresse demandée (l'API n'en garde qu'un premier segment lisible).
  useEffect(() => {
    signaler({ type: "erreur", chemin: window.location.pathname.slice(0, 200), detail: "404" });
  }, []);
  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="max-w-md text-center">
        <h1 className="text-7xl font-bold text-foreground">404</h1>
        <h2 className="mt-4 text-xl font-semibold text-foreground">
          {m.erreur404_titre({}, options)}
        </h2>
        <p className="mt-2 text-sm text-muted-foreground">{m.erreur404_texte({}, options)}</p>
        <div className="mt-6">
          <a
            href={localiser("/", langue)}
            className="inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
          >
            {m.commun_retour_accueil({}, options)}
          </a>
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
        <h1 className="text-xl font-semibold tracking-tight text-foreground">{m.erreur_titre()}</h1>
        <p className="mt-2 text-sm text-muted-foreground">{m.erreur_texte()}</p>
        <div className="mt-6 flex flex-wrap justify-center gap-2">
          <button
            onClick={() => {
              router.invalidate();
              reset();
            }}
            className="inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
          >
            {m.erreur_reessayer()}
          </button>
          <a
            href={localiser("/", langueCourante())}
            className="inline-flex items-center justify-center rounded-md border border-input bg-background px-4 py-2 text-sm font-medium text-foreground transition-colors hover:bg-accent"
          >
            {m.commun_retour_accueil()}
          </a>
        </div>
      </div>
    </div>
  );
}

export const Route = createRootRouteWithContext<{
  queryClient: QueryClient;
  pageExiste: (chemin: string) => boolean;
}>()({
  // Garde d'affichage du mode maintenance (spec 047) : l'API bloque de toute façon chaque route.
  beforeLoad: async ({ location, context }) => {
    // Langues (spec 052) : `/fr/...` n'existe pas (une seule adresse par page), et une page non traduite sous `/en`
    // ou `/de` s'ouvre en français ; une page inconnue y reste une 404 dans la langue du préfixe.
    const versLaLangue = redirectionLangue(location.pathname, context.pageExiste);
    if (versLaLangue !== null) throw redirect({ href: versLaLangue + location.searchStr });

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
      { name: "description", content: m.commun_description_defaut() },
      { name: "author", content: "Club Santé SOS Docteur TV" },
      { property: "og:title", content: "Club Santé" },
      { property: "og:description", content: m.commun_description_defaut() },
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
  // La langue de l'adresse : celle de la page, et aussi celle d'une 404 sous `/en` ou `/de`.
  const langue = useRouterState({ select: (etat) => langueDeLAdresse(etat.location.publicHref) });
  return (
    <html lang={langue}>
      <head>
        <HeadContent />
        <VersionsDeLaPage />
      </head>
      <body>
        {children}
        <Scripts />
      </body>
    </html>
  );
}

/** Les versions de la page dans chaque langue, pour les moteurs de recherche (spec 052). */
function VersionsDeLaPage() {
  const { pathname, searchStr } = useRouterState({ select: (etat) => etat.location });
  return liensHreflang(pathname, searchStr, origineDuSite()).map((lien) => (
    <link key={lien.hreflang} rel="alternate" hrefLang={lien.hreflang} href={lien.href} />
  ));
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
