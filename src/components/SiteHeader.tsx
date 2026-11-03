import { useState } from "react";
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
import { useMoi } from "@/hooks/use-moi";
import logo from "@/assets/logo.webp";

// Les pages pas encore construites n'ont pas de `href` : leur lien pointe vers « # ». Les ancres visent l'accueil, pour fonctionner depuis toutes les pages.
const menu: { t: string; items: { t: string; href?: string }[] }[] = [
  {
    t: "Vie du club",
    items: [
      { t: "Club santé", href: "/club-sante" },
      { t: "Les 7 axes", href: "/#univers" },
      { t: "Cartes des clubs", href: "/#clubs" },
      { t: "Bibliothèques" },
    ],
  },
  { t: "Génie Imhotep", items: [{ t: "Hall of Fame" }, { t: "Inscription" }] },
  { t: "Gamification", items: [{ t: "Jeux" }, { t: "Certification" }] },
  { t: "Actualités", items: [{ t: "Agenda", href: "/#agenda" }, { t: "Magazine" }] },
];

function Logo() {
  return (
    <img
      src={logo}
      alt="Club Santé SOS Docteur TV"
      width={1014}
      height={195}
      className="h-8 w-auto shrink-0 lg:h-11"
    />
  );
}

export function SiteHeader() {
  const [lang, setLang] = useState<"FR" | "EN">("FR");
  const langSwitch = (
    <button
      aria-label={lang === "FR" ? "Passer en anglais" : "Passer en français"}
      onClick={() => setLang(lang === "FR" ? "EN" : "FR")}
      className="btn-fx rounded-full border px-3 py-2 text-sm font-bold"
    >
      <span className={lang === "FR" ? "text-logo-blue" : "text-muted-foreground"}>FR</span>
      <span className="text-muted-foreground"> / </span>
      <span className={lang === "EN" ? "text-logo-blue" : "text-muted-foreground"}>EN</span>
    </button>
  );
  const join = (
    <button className="btn-fx whitespace-nowrap rounded-full bg-primary px-5 py-2.5 text-sm font-bold text-primary-foreground">
      Rejoindre le club
    </button>
  );
  const { data: moi } = useMoi();
  const login = (
    <Link
      to={moi ? "/mon-espace" : "/connexion"}
      className="btn-fx whitespace-nowrap rounded-full border border-logo-blue px-5 py-2.5 text-center text-sm font-bold text-logo-blue hover:bg-logo-blue hover:text-primary-foreground"
    >
      {moi ? "Mon espace" : "Se connecter"}
    </Link>
  );

  return (
    <header className="sticky top-0 z-20 border-b bg-background/90 backdrop-blur transition-shadow duration-300 data-[scrolled]:shadow-lg">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-3 px-5 py-3">
        <a href="/" className="transition hover:scale-105">
          <Logo />
        </a>
        <NavigationMenuPrimitive.Root aria-label="Menu principal" className="hidden xl:block">
          <NavigationMenuPrimitive.List className="flex items-center gap-1">
            {menu.map((m) => (
              <NavigationMenuPrimitive.Item key={m.t} className="relative">
                <NavigationMenuPrimitive.Trigger className="group relative flex items-center gap-1 rounded-md px-3 py-2 text-sm font-bold transition-colors after:absolute after:inset-x-3 after:bottom-1 after:h-0.5 after:origin-left after:scale-x-0 after:rounded-full after:bg-primary after:transition-transform after:duration-300 hover:text-logo-blue hover:after:scale-x-100 data-[state=open]:text-logo-blue data-[state=open]:after:scale-x-100">
                  {m.t}{" "}
                  <ChevronDown
                    aria-hidden
                    className="h-4 w-4 transition group-data-[state=open]:rotate-180"
                  />
                </NavigationMenuPrimitive.Trigger>
                <NavigationMenuPrimitive.Content className="absolute left-0 top-full pt-2 animate-in fade-in slide-in-from-top-2 duration-200">
                  <ul className="min-w-52 rounded-2xl border bg-popover p-2 shadow-card">
                    {m.items.map((i) => (
                      <li key={i.t}>
                        <NavigationMenuPrimitive.Link
                          href={i.href ?? "#"}
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
          <div className="hidden items-center gap-3 sm:flex">
            {join}
            {login}
            {langSwitch}
          </div>
          <Sheet>
            <SheetTrigger aria-label="Ouvrir le menu" className="rounded-full border p-2 xl:hidden">
              <Menu className="h-5 w-5" />
            </SheetTrigger>
            <SheetContent aria-describedby={undefined} className="flex flex-col overflow-y-auto">
              <SheetTitle className="text-xl text-logo-blue">Menu</SheetTitle>
              <Accordion type="single" collapsible>
                {menu.map((m) => (
                  <AccordionItem key={m.t} value={m.t}>
                    <AccordionTrigger className="text-base font-bold">{m.t}</AccordionTrigger>
                    <AccordionContent>
                      <ul>
                        {m.items.map((i) => (
                          <li key={i.t}>
                            <SheetClose asChild>
                              <a
                                href={i.href ?? "#"}
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
