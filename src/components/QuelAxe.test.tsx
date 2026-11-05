import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { QuelAxe } from "./QuelAxe";

const repondre = (...textes: string[]) => {
  for (const t of textes) fireEvent.click(screen.getByRole("button", { name: new RegExp(t) }));
};

describe("QuelAxe", () => {
  it("propose l'axe le plus choisi, avec le lien vers sa section", () => {
    render(<QuelAxe />);
    repondre("Bouger", "sang-froid", "prix", "créativité");

    expect(screen.getByRole("status")).toHaveTextContent("Sport & secourisme");
    expect(screen.getByRole("link", { name: /Découvrir cet axe/ })).toHaveAttribute(
      "href",
      "/les-7-axes#axe-4",
    );
  });

  it("à égalité, retient l'axe de la réponse la plus récente", () => {
    render(<QuelAxe />);
    // Axes 3, 6, 5 puis 3 : l'axe 3 l'emporte avec deux voix.
    repondre("Filmer", "organise", "prix", "créativité");
    expect(screen.getByRole("status")).toHaveTextContent("Axe 3");

    fireEvent.click(screen.getByRole("button", { name: /Recommencer/ }));
    // Axes 1, 6, 5, 2 : quatre axes à une voix, le dernier choisi l'emporte.
    repondre("culture générale", "organise", "prix", "empathie");
    expect(screen.getByRole("status")).toHaveTextContent("Santé sexuelle & EVSS");
  });

  it("permet de revenir à la question précédente", () => {
    render(<QuelAxe />);
    repondre("Jardiner");
    expect(screen.getByText("Question 2 sur 4")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /Question précédente/ }));
    expect(screen.getByText("Question 1 sur 4")).toBeInTheDocument();
  });
});
