import { act, fireEvent, render, screen } from "@testing-library/react";
import {
  createMemoryHistory,
  createRootRoute,
  createRouter,
  RouterProvider,
} from "@tanstack/react-router";
import { describe, expect, it } from "vitest";

import { TemoignagesSection } from "./TemoignagesSection";

// « Lire la suite » est un lien du routeur : la section se rend dans un routeur de test.
async function afficher() {
  const router = createRouter({
    routeTree: createRootRoute({ component: TemoignagesSection }),
    history: createMemoryHistory({ initialEntries: ["/"] }),
  });
  const rendu = render(<RouterProvider router={router} />);
  await act(() => router.load());
  return rendu;
}

describe("TemoignagesSection", () => {
  it("fait défiler les témoignages avec les flèches et les points", async () => {
    await afficher();
    expect(screen.getByText("Ayiman N.")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Témoignage suivant" }));
    expect(screen.getByText("François Léger Koffi K.")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Témoignage 4 sur 4" }));
    expect(screen.getByText("Jérémie A.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Témoignage 4 sur 4" })).toHaveAttribute(
      "aria-current",
      "true",
    );

    // Après le dernier, on revient au premier.
    fireEvent.click(screen.getByRole("button", { name: "Témoignage suivant" }));
    expect(screen.getByText("Ayiman N.")).toBeInTheDocument();
  });

  it("renvoie la suite d'un témoignage vers sa page", async () => {
    await afficher();
    fireEvent.click(screen.getByRole("button", { name: "Témoignage 3 sur 4" }));

    expect(screen.getByRole("link", { name: "Lire la suite" })).toHaveAttribute(
      "href",
      "/temoignages#koffi-semanou-d",
    );
  });

  it("ne montre jamais le nom de famille complet d'un élève", async () => {
    const { container } = await afficher();
    for (let i = 1; i <= 4; i++) {
      fireEvent.click(screen.getByRole("button", { name: `Témoignage ${i} sur 4` }));
      expect(container).not.toHaveTextContent(/KPONOUME|DANSOU|ASSOU/);
    }
  });
});
