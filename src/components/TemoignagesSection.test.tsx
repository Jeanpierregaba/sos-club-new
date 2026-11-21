import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { TemoignagesSection } from "./TemoignagesSection";

describe("TemoignagesSection", () => {
  it("fait défiler les témoignages avec les flèches et les points", () => {
    render(<TemoignagesSection />);
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

  it("déplie la suite d'un témoignage", () => {
    render(<TemoignagesSection />);
    fireEvent.click(screen.getByRole("button", { name: "Témoignage 3 sur 4" }));

    fireEvent.click(screen.getByRole("button", { name: "Lire la suite" }));

    expect(screen.getByText(/rend plus intelligents sur notre santé/)).toBeVisible();
  });

  it("ne montre jamais le nom de famille complet d'un élève", () => {
    const { container } = render(<TemoignagesSection />);
    for (let i = 1; i <= 4; i++) {
      fireEvent.click(screen.getByRole("button", { name: `Témoignage ${i} sur 4` }));
      expect(container).not.toHaveTextContent(/KPONOUME|DANSOU|ASSOU/);
    }
  });
});
