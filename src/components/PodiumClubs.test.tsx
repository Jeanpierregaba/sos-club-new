import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  createMemoryHistory,
  createRootRoute,
  createRouter,
  RouterProvider,
} from "@tanstack/react-router";
import { act, fireEvent, render, screen, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { PodiumClubs } from "./PodiumClubs";

const api = vi.hoisted(() => ({
  chargerChiffresAccueil: vi.fn(),
  chargerClassementPublic: vi.fn(),
}));
vi.mock("@/lib/api/client", async (original) => ({
  ...(await original<typeof import("@/lib/api/client")>()),
  ...api,
}));

async function afficher() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const route = createRootRoute({
    component: () => (
      <QueryClientProvider client={client}>
        <PodiumClubs />
      </QueryClientProvider>
    ),
  });
  const router = createRouter({
    routeTree: route,
    history: createMemoryHistory({ initialEntries: ["/"] }),
  });
  render(<RouterProvider router={router} />);
  await act(() => router.load());
  await act(async () => {});
}

const page = (categorie: string, periode: string, lignes: object[]) => ({
  categorie,
  niveau: "national",
  dre: null,
  periode,
  semestre: periode === "semestre" ? { id: "s1", libelle: "Semestre 1 2026-2027" } : null,
  page: 1,
  par_page: 5,
  total: lignes.length,
  lignes,
});

const eleve = (rang: number, nom: string, points: number) => ({
  rang,
  nom,
  points,
  club: "Club Tokoin",
  dre: "Grand Lomé",
});
const club = (rang: number, nom: string, points: number) => ({
  rang,
  club_id: `club-${rang}`,
  nom,
  etablissement: `Lycée ${rang}`,
  dre: "Grand Lomé",
  points,
});

type Filtres = { categorie: string; periode: string };
function classements(reponses: Record<string, object[]>) {
  api.chargerClassementPublic.mockImplementation(async (f: Filtres) =>
    page(f.categorie, f.periode, reponses[`${f.categorie}/${f.periode}`] ?? []),
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  // Animations réduites : les compteurs affichent tout de suite leur valeur.
  vi.stubGlobal("matchMedia", (requete: string) => ({ matches: true, media: requete }));
  api.chargerChiffresAccueil.mockResolvedValue({ eleves: 0, clubs: 0, quiz: 0, points: 0 });
  classements({});
});

describe("PodiumClubs", () => {
  it("montre le Top 5 des élèves du semestre par leur pseudonyme, et les liens", async () => {
    classements({
      "eleves/semestre": [
        eleve(1, "Ama du Golfe", 900),
        eleve(2, "Kofi", 700),
        eleve(3, "Yawa", 650),
        eleve(4, "Edem", 400),
        eleve(5, "Afi", 300),
      ],
    });
    await afficher();

    const top = await screen.findByRole("list", { name: "Top 5 des élèves" });
    const lignes = within(top).getAllByRole("listitem");
    expect(lignes).toHaveLength(5);
    expect(lignes[0]).toHaveTextContent("Ama du Golfe");
    expect(lignes[0]).toHaveTextContent("Club Tokoin · Grand Lomé");
    expect(lignes[0]).toHaveTextContent(/900\s*pts/);
    expect(screen.getByText(/Top 5 – Semestre 1 2026-2027/)).toBeInTheDocument();
    expect(api.chargerClassementPublic).toHaveBeenCalledWith({
      categorie: "eleves",
      niveau: "national",
      periode: "semestre",
      par_page: 5,
    });
    expect(screen.getByRole("link", { name: /Découvrir les jeux/ })).toHaveAttribute(
      "href",
      "/jeux",
    );
    expect(screen.getByRole("link", { name: /Découvrir le classement/ })).toHaveAttribute(
      "href",
      "/hall-of-fame",
    );
    expect(screen.getByRole("link", { name: /Voir tout le classement/ })).toHaveAttribute(
      "href",
      "/hall-of-fame",
    );
  });

  it("passe au Top 5 des clubs, avec un lien vers chaque club", async () => {
    classements({ "clubs/semestre": [club(1, "Club Tokoin", 15800), club(2, "Club Kara", 900)] });
    await afficher();

    fireEvent.click(screen.getByRole("tab", { name: /Clubs/ }));
    const top = await screen.findByRole("list", { name: "Top 5 des clubs" });
    const lignes = within(top).getAllByRole("listitem");
    expect(lignes).toHaveLength(2);
    expect(lignes[0]).toHaveTextContent("Lycée 1");
    expect(lignes[0]).toHaveTextContent(/15\s800\s*pts/);
    expect(screen.getByRole("link", { name: /Lycée 1/ })).toHaveAttribute("href", "/clubs/club-1");
    expect(screen.getByRole("tab", { name: /Clubs/ })).toHaveAttribute("aria-selected", "true");
  });

  it("montre le classement depuis le début quand le semestre n'a pas encore de points", async () => {
    classements({ "eleves/historique": [eleve(1, "Ama du Golfe", 50)] });
    await afficher();

    expect(await screen.findByRole("list", { name: "Top 5 des élèves" })).toHaveTextContent(
      "Ama du Golfe",
    );
    expect(screen.getByText(/Top 5 – Depuis le début/)).toBeInTheDocument();
  });

  it("montre les chiffres du programme", async () => {
    api.chargerChiffresAccueil.mockResolvedValue({
      eleves: 12480,
      clubs: 423,
      quiz: 96320,
      points: 148360,
    });
    await afficher();

    const chiffres = await screen.findByRole("list", { name: "Le programme en chiffres" });
    expect(chiffres).toHaveTextContent(/12 480\s*Élèves inscrits/);
    expect(chiffres).toHaveTextContent(/423\s*Clubs Santé/);
  });

  it("annonce le classement tant que personne n'a de points, ou si l'API ne répond pas", async () => {
    api.chargerChiffresAccueil.mockRejectedValue(new Error("hors ligne"));
    api.chargerClassementPublic.mockRejectedValue(new Error("hors ligne"));
    await afficher();

    expect(await screen.findByText("Le classement arrive bientôt !")).toBeInTheDocument();
    expect(screen.queryByRole("listitem", { name: /pts/ })).not.toBeInTheDocument();
  });

  it("garde 5 lignes, donc la même hauteur, dans chaque onglet et chaque état", async () => {
    // Deux élèves classés, aucun club : liste complétée d'un côté, annonce de l'autre.
    classements({ "eleves/semestre": [eleve(1, "Kofi", 300), eleve(2, "Ama", 120)] });
    await afficher();
    const panneau = () => screen.getByRole("tabpanel");
    const lignes = () => panneau().querySelectorAll("li, [aria-hidden].h-14").length;

    expect(await within(panneau()).findByText("Kofi")).toBeInTheDocument();
    expect(lignes()).toBe(5);

    fireEvent.click(screen.getByRole("tab", { name: /Clubs/ }));
    expect(within(panneau()).getByText("Le classement arrive bientôt !")).toBeInTheDocument();
    expect(lignes()).toBe(5);
    // Les deux classements sont chargés d'avance : revenir aux élèves ne relance rien.
    const appels = api.chargerClassementPublic.mock.calls.length;
    fireEvent.click(screen.getByRole("tab", { name: /Élèves/ }));
    expect(within(panneau()).getByText("Kofi")).toBeInTheDocument();
    expect(api.chargerClassementPublic.mock.calls.length).toBe(appels);
  });
});
