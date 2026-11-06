import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { BulleDefi } from "./BulleDefi";
import { ErreurApi, type DefiDuJour } from "@/lib/api/client";

const api = vi.hoisted(() => ({ chargerDefiDuJour: vi.fn(), corrigerDefi: vi.fn() }));
vi.mock("@/lib/api/client", async (original) => ({
  ...(await original<typeof import("@/lib/api/client")>()),
  ...api,
}));

const defi: DefiDuJour = {
  id: "defi-1",
  categorie: "Hygiène",
  question: "Combien de temps faut-il se laver les mains ?",
  options: ["Cinq secondes", "Au moins 20 secondes, avec du savon", "Une seconde"],
};

function afficher() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <BulleDefi />
    </QueryClientProvider>,
  );
}

async function repondre(option: string) {
  fireEvent.click(await screen.findByRole("button", { name: "Ouvrir le défi du jour" }));
  fireEvent.click(screen.getByRole("button", { name: new RegExp(option) }));
  await act(async () => fireEvent.click(screen.getByRole("button", { name: "Valider" })));
}

beforeEach(() => vi.clearAllMocks());

describe("BulleDefi", () => {
  it("affiche la question du jour et la correction de l'API", async () => {
    api.chargerDefiDuJour.mockResolvedValue(defi);
    api.corrigerDefi.mockResolvedValue({
      correcte: true,
      bonne_reponse: 1,
      explication: "Frotter 20 secondes élimine la plupart des microbes.",
    });
    afficher();

    await repondre("Au moins 20 secondes");

    expect(api.corrigerDefi).toHaveBeenCalledWith("defi-1", 1);
    expect(screen.getByRole("status")).toHaveTextContent("Bravo, c'est la bonne réponse !");
    expect(screen.getByText(/élimine la plupart des microbes/)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Valider" })).not.toBeInTheDocument();
  });

  it("signale une mauvaise réponse et montre la bonne", async () => {
    api.chargerDefiDuJour.mockResolvedValue(defi);
    api.corrigerDefi.mockResolvedValue({ correcte: false, bonne_reponse: 1, explication: "." });
    afficher();

    await repondre("Cinq secondes");

    expect(screen.getByRole("status")).toHaveTextContent("la bonne réponse est en vert");
    expect(screen.getByRole("button", { name: /Au moins 20 secondes/ })).toHaveClass("bg-leaf");
  });

  it("ne s'affiche pas sans défi", async () => {
    api.chargerDefiDuJour.mockRejectedValue(new ErreurApi(404, "Aucun défi."));
    const { container } = afficher();

    await act(async () => {});

    expect(container).toBeEmptyDOMElement();
  });
});
