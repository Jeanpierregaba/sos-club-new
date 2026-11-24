import { Link } from "@tanstack/react-router";
import * as NavigationMenuPrimitive from "@radix-ui/react-navigation-menu";
import { ChevronDown, Menu } from "lucide-react";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Sheet, SheetClose, SheetContent, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { Cloche } from "@/components/notifications/Cloche";
import { SelecteurLangue } from "@/components/SelecteurLangue";
import { useMoi } from "@/hooks/use-moi";
import { langueCourante, localiser } from "@/lib/langues";
import { m } from "@/paraglide/messages.js";
import logo from "@/assets/logo.webp";

// Une page par entrée de menu, rangées par rubrique. Une fonction : les textes suivent la langue de la page.
const menu = (): { t: string; items: { t: string; href: string }[] }[] => [
  {
    t: m.menu_vie_du_club(),
    items: [
      { t: m.menu_club_sante(), href: "/club-sante" },
      { t: m.menu_7_axes(), href: "/les-7-axes" },
      { t: m.menu_carte_des_clubs(), href: "/carte-des-clubs" },
      { t: m.menu_bibliotheque(), href: "/bibliotheque" },
      { t: m.menu_galerie(), href: "/galerie" },
    ],
  },
  {
    t: m.menu_genie_imhotep(),
    items: [
      { t: m.menu_description(), href: "/genie-imhotep/description" },
      { t: m.menu_hall_of_fame(), href: "/genie-imhotep/hall-of-fame" },
      { t: m.menu_palmares(), href: "/genie-imhotep/palmares" },
    ],
  },
  {
    t: m.menu_gamification(),
    items: [
      { t: m.menu_jeux(), href: "/jeux" },
      { t: m.menu_certification(), href: "/certification" },
      { t: m.menu_classements(), href: "/hall-of-fame" },
    ],
  },
  {
    t: m.menu_actualites(),
    items: [
      { t: m.menu_agenda(), href: "/agenda" },
      { t: m.menu_magazine(), href: "/magazine" },
    ],
  },
];

function Logo() {
  return (
    <img
      src={logo}
      alt={m.entete_logo()}
      width={1014}
      height={195}
      className="h-8 w-auto shrink-0 lg:h-11"
    />
  );
}

export function SiteHeader() {
  const langue = langueCourante();
  const rubriques = menu();
  const lien = (href: string) => localiser(href, langue);
  const langSwitch = <SelecteurLangue />;
  const { data: moi } = useMoi();
  // Un élève déjà inscrit n'a plus besoin de ce bouton : il retrouve son espace avec « Mon espace ».
  const join = moi ? null : (
    <Link
      to="/inscription"
      className="btn-fx btn-brille whitespace-nowrap rounded-full bg-primary px-5 py-2.5 text-center text-sm font-bold text-primary-foreground"
    >
      {m.entete_rejoindre()}
    </Link>
  );
  const login = (
    <Link
      to={moi ? "/mon-espace" : "/connexion"}
      className="btn-fx whitespace-nowrap rounded-full border border-logo-blue px-5 py-2.5 text-center text-sm font-bold text-logo-blue hover:bg-logo-blue hover:text-primary-foreground"
    >
      {moi ? m.entete_mon_espace() : m.entete_se_connecter()}
    </Link>
  );

  return (
    <header className="sticky top-0 z-20 border-b bg-background/90 backdrop-blur transition-shadow duration-300 data-[scrolled]:shadow-lg">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-3 px-5 py-3">
        <a href={lien("/")} aria-label={m.entete_accueil()} className="transition hover:scale-105">
          <Logo />
        </a>
        <NavigationMenuPrimitive.Root aria-label={m.menu_principal()} className="hidden xl:block">
          <NavigationMenuPrimitive.List className="flex items-center gap-1">
            {rubriques.map((r) => (
              <NavigationMenuPrimitive.Item key={r.t} className="relative">
                <NavigationMenuPrimitive.Trigger className="group relative flex items-center gap-1 rounded-md px-3 py-2 text-sm font-bold transition-colors after:absolute after:inset-x-3 after:bottom-1 after:h-0.5 after:origin-left after:scale-x-0 after:rounded-full after:bg-primary after:transition-transform after:duration-300 hover:text-logo-blue hover:after:scale-x-100 data-[state=open]:text-logo-blue data-[state=open]:after:scale-x-100">
                  {r.t}{" "}
                  <ChevronDown
                    aria-hidden
                    className="h-4 w-4 transition group-data-[state=open]:rotate-180"
                  />
                </NavigationMenuPrimitive.Trigger>
                <NavigationMenuPrimitive.Content className="absolute left-0 top-full pt-2 animate-in fade-in slide-in-from-top-2 duration-200">
                  <ul className="min-w-52 rounded-2xl border bg-popover p-2 shadow-card">
                    {r.items.map((i) => (
                      <li key={i.t}>
                        <NavigationMenuPrimitive.Link
                          href={lien(i.href)}
                          className="block rounded-lg px-3 py-2 text-sm font-semibold transition hover:translate-x-1 hover:bg-mist hover:text-logo-blue"
                        >
                          {i.t}
                        </NavigationMenuPrimitive.Link>
                      </li>
                    ))}
                  </ul>
                </NavigationMenuPrimitive.Content>
              </NavigationMenuPrimitive.Item>
            ))}
          </NavigationMenuPrimitive.List>
        </NavigationMenuPrimitive.Root>
        <div className="flex items-center gap-3">
          <Cloche />
          <div className="hidden items-center gap-3 sm:flex">
            {join}
            {login}
            {langSwitch}
          </div>
          <Sheet>
            <SheetTrigger
              aria-label={m.menu_ouvrir()}
              className="rounded-full border p-2 xl:hidden"
            >
              <Menu className="h-5 w-5" />
            </SheetTrigger>
            <SheetContent aria-describedby={undefined} className="flex flex-col overflow-y-auto">
              <SheetTitle className="text-xl text-logo-blue">{m.menu_titre()}</SheetTitle>
              <Accordion type="single" collapsible>
                {rubriques.map((r) => (
                  <AccordionItem key={r.t} value={r.t}>
                    <AccordionTrigger className="text-base font-bold">{r.t}</AccordionTrigger>
                    <AccordionContent>
                      <ul>
                        {r.items.map((i) => (
                          <li key={i.t}>
                            <SheetClose asChild>
                              <a
                                href={lien(i.href)}
                                className="block rounded-lg px-3 py-2 font-semibold hover:bg-mist hover:text-logo-blue"
                              >
                                {i.t}
                              </a>
                            </SheetClose>
                          </li>
                        ))}
                      </ul>
                    </AccordionContent>
                  </AccordionItem>
                ))}
              </Accordion>
              <div className="mt-auto grid gap-3 pt-6 sm:hidden">
                {join}
                {login}
                {langSwitch}
              </div>
            </SheetContent>
          </Sheet>
        </div>
      </div>
    </header>
  );
}
