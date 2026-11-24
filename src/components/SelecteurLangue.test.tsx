import { render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { dateCourte } from "@/lib/dates";
import { overwriteGetLocale } from "@/paraglide/runtime.js";

import { ContenuEnFrancais } from "./ContenuEnFrancais";
import { SelecteurLangue } from "./SelecteurLangue";
import { SiteFooter } from "./SiteFooter";

const etat = { location: { pathname: "/articles/mon-article", searchStr: "?page=2", hash: "" } };
vi.mock("@tanstack/react-router", async (original) => ({
  ...(await original<typeof import("@tanstack/react-router")>()),
  useRouterState: ({ select }: { select: (e: typeof etat) => unknown }) => select(etat),
}));

const parler = (langue: "fr" | "en" | "de") => overwriteGetLocale(() => langue);

afterEach(() => {
  parler("fr");
  etat.location.pathname = "/articles/mon-article";
});

describe("sélecteur de langue (spec 052)", () => {
  it("ouvre la même page dans chaque langue et signale la langue active", () => {
    parler("en");
    render(<SelecteurLangue />);
    const choix = screen.getByRole("navigation", { name: "Site language" });
    expect(
      within(choix).getByRole("link", { name: "Lire cette page en Français" }),
    ).toHaveAttribute("href", "/articles/mon-article?page=2");
    const anglais = within(choix).getByRole("link", { name: "Read this page in English" });
    expect(anglais).toHaveAttribute("href", "/en/articles/mon-article?page=2");
    expect(anglais).toHaveAttribute("aria-current", "true");
    expect(
      within(choix).getByRole("link", { name: "Diese Seite auf Deutsch lesen" }),
    ).toHaveAttribute("href", "/de/articles/mon-article?page=2");
  });

  it("n'apparaît pas sur une page restée en français", () => {
    etat.location.pathname = "/mon-espace";
    const { container } = render(<SelecteurLangue />);
    expect(container).toBeEmptyDOMElement();
  });
});

describe("cadre commun traduit", () => {
  it("le pied de page suit la langue", () => {
    parler("de");
    render(<SiteFooter />);
    expect(screen.getByRole("heading", { name: "Unsere offiziellen Medien" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Abonnieren/ })).toBeInTheDocument();
  });

  it("la mention des contenus en français n'apparaît qu'en anglais et en allemand", () => {
    const { container, rerender } = render(<ContenuEnFrancais />);
    expect(container).toBeEmptyDOMElement();
    parler("en");
    rerender(<ContenuEnFrancais key="en" />);
    expect(screen.getByText("Content available in French")).toBeInTheDocument();
  });

  it("écrit les dates dans la langue de la page", () => {
    const jour = "2026-11-24T12:00:00Z";
    expect(dateCourte(jour)).toBe("24 novembre 2026");
    parler("en");
    expect(dateCourte(jour)).toBe("November 24, 2026");
    parler("de");
    expect(dateCourte(jour)).toBe("24. November 2026");
  });
});
