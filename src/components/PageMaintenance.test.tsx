import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { PageMaintenance } from "./PageMaintenance";

describe("PageMaintenance", () => {
  it("affiche le message fixe et les mascottes de l'équipe", () => {
    render(<PageMaintenance />);

    expect(
      screen.getByText(
        "La plateforme est actuellement en maintenance et sera de nouveau disponible.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByAltText("Les sept mascottes des Clubs Santé")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Connexion de l'équipe" })).toHaveAttribute(
      "href",
      "/connexion",
    );
  });
});
