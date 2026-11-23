import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { afterEach, describe, expect, it, vi } from "vitest";

import { endroitDuClic, lienInscription, pageVue, signaler } from "./activite";

const CHEMINS: string[] = JSON.parse(
  readFileSync(resolve(__dirname, "../../backend/app/activite/chemins.json"), "utf8"),
);

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  document.body.innerHTML = "";
});

describe("liste blanche des chemins de l'API", () => {
  it("contient chaque page publique du site, et aucune page de l'équipe", () => {
    const arbre = readFileSync(resolve(__dirname, "../routeTree.gen.ts"), "utf8");
    const union = arbre.slice(arbre.indexOf("fullPaths:"), arbre.indexOf("fileRoutesByTo"));
    const pages = new Set(
      [...union.matchAll(/'([^']*)'/g)]
        .map(([, c = ""]) => (c !== "/" && c.endsWith("/") ? c.slice(0, -1) : c))
        .filter((c) => !c.startsWith("/admin")),
    );
    expect(pages.size).toBeGreaterThan(40);
    expect(new Set(CHEMINS)).toEqual(pages);
  });
});

// jsdom n'a pas Blob.text() : FileReader le lit.
function lireBlob(blob: Blob): Promise<string> {
  return new Promise((ok) => {
    const lecteur = new FileReader();
    lecteur.onload = () => ok(String(lecteur.result));
    lecteur.readAsText(blob);
  });
}

describe("signaler", () => {
  it("envoie l'événement en JSON par sendBeacon", async () => {
    const sendBeacon = vi.fn().mockReturnValue(true);
    vi.stubGlobal("navigator", { ...navigator, sendBeacon });
    signaler({ type: "page_vue", chemin: "/jeux" });
    expect(sendBeacon).toHaveBeenCalledOnce();
    const [adresse, corps] = sendBeacon.mock.calls[0] ?? [];
    expect(adresse).toBe("/api/activite/evenements");
    expect(JSON.parse(await lireBlob(corps as Blob))).toEqual({
      type: "page_vue",
      chemin: "/jeux",
    });
  });

  it("n'envoie rien quand le navigateur demande à ne pas être suivi", () => {
    const sendBeacon = vi.fn();
    const envoi = vi.fn();
    vi.stubGlobal("fetch", envoi);
    vi.stubGlobal("navigator", { ...navigator, sendBeacon, globalPrivacyControl: true });
    signaler({ type: "page_vue", chemin: "/" });
    expect(sendBeacon).not.toHaveBeenCalled();
    expect(envoi).not.toHaveBeenCalled();
  });

  it("se replie sur fetch sans jamais lever", () => {
    const envoi = vi.fn().mockRejectedValue(new Error("hors ligne"));
    vi.stubGlobal("fetch", envoi);
    vi.stubGlobal("navigator", { ...navigator, sendBeacon: undefined });
    expect(() => signaler({ type: "page_vue", chemin: "/" })).not.toThrow();
    expect(envoi).toHaveBeenCalledWith(
      "/api/activite/evenements",
      expect.objectContaining({ method: "POST", keepalive: true }),
    );
  });
});

describe("pageVue", () => {
  it("garde le gabarit de la route, sans barre finale", () => {
    expect(pageVue({ fullPath: "/quiz/", params: {} }, null)).toEqual({
      type: "page_vue",
      chemin: "/quiz",
    });
  });

  it("ne compte pas les pages de l'équipe", () => {
    expect(pageVue({ fullPath: "/admin/inscrits/$id", params: { id: "x" } }, null)).toBeNull();
  });

  it("compte un article par son adresse, jamais un autre paramètre", () => {
    expect(
      pageVue({ fullPath: "/articles/$adresse", params: { adresse: "Se-Laver-Les-Mains" } }, null)
        ?.detail,
    ).toBe("se-laver-les-mains");
    expect(
      pageVue({ fullPath: "/carte/$code", params: { code: "SECRET" } }, null)?.detail,
    ).toBeUndefined();
  });

  it("donne la provenance à la page d'entrée seulement", () => {
    expect(
      pageVue(
        { fullPath: "/", params: {} },
        { referent: "https://www.facebook.com/", recherche: "?utm_source=affiche-lome" },
      ),
    ).toEqual({
      type: "page_vue",
      chemin: "/",
      entree: true,
      referent: "https://www.facebook.com/",
      utm_source: "affiche-lome",
    });
  });
});

describe("clics « S'inscrire »", () => {
  function lien(html: string): HTMLAnchorElement {
    document.body.innerHTML = html;
    return document.querySelector("a")!;
  }

  it("reconnaît un lien vers l'inscription, pas celui de Génie Imhotep", () => {
    expect(
      lienInscription(lien('<a href="/inscription?profil=eleve"><span>Go</span></a>')),
    ).not.toBeNull();
    expect(lienInscription(lien('<a href="/genie-imhotep/inscription">Go</a>'))).toBeNull();
    expect(lienInscription(lien('<a href="https://ailleurs.tg/inscription">Go</a>'))).toBeNull();
  });

  it("nomme l'endroit du clic", () => {
    expect(endroitDuClic(lien('<header><a href="/inscription">x</a></header>'), "/jeux")).toBe(
      "menu",
    );
    expect(endroitDuClic(lien('<footer><a href="/inscription">x</a></footer>'), "/")).toBe(
      "pied-de-page",
    );
    expect(endroitDuClic(lien('<a href="/inscription">x</a>'), "/")).toBe("accueil");
    expect(
      endroitDuClic(lien('<div role="dialog"><a href="/inscription">x</a></div>'), "/jeux"),
    ).toBe("menu-mobile");
    expect(endroitDuClic(lien('<a href="/inscription">x</a>'), "/quiz/abc")).toBe("quiz");
    expect(endroitDuClic(lien('<a href="/inscription">x</a>'), "/charte")).toBe("autre");
  });
});
