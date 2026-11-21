import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { PartieQuiz } from "./PartieQuiz";
import { Vies } from "./Vies";
import type { EtatPartie } from "@/lib/api/client";

const vies = (restantes: number) => ({ total: 7, restantes, perdues: 7 - restantes, en_cours: 0 });

const fin = (vies_restantes: number | null): EtatPartie => ({
  tentative_id: "t1",
  quiz_id: "q1",
  titre: "Quiz",
  total: 15,
  question: null,
  resultat: { score: 3, total: 15, seuil: 12, reussie: false, points: 0 },
  vies_restantes,
});

const appels = { repondre: vi.fn(), reprendre: vi.fn() };

describe("Vies (spec 048)", () => {
  it("montre un cœur plein par vie restante", () => {
    render(<Vies vies={vies(5)} />);

    expect(screen.getByRole("img", { name: "5 vies sur 7 aujourd'hui" })).toBeInTheDocument();
    expect(screen.getByText(/Jeux et certification partagent/)).toBeInTheDocument();
  });

  it("annonce la recharge de minuit quand il n'en reste plus", () => {
    render(<Vies vies={vies(0)} />);

    expect(screen.getByRole("status")).toHaveTextContent(
      "Tu as utilisé tes 7 vies aujourd'hui. Reviens demain, elles se rechargent à minuit.",
    );
  });

  it("n'affiche rien pour un invité", () => {
    const { container } = render(<Vies vies={null} />);
    expect(container).toBeEmptyDOMElement();
  });

  it("donne les vies restantes en fin de partie, et bloque « Rejouer » à 0", () => {
    const rejouer = vi.fn();
    const { rerender } = render(
      <PartieQuiz depart={fin(4)} appels={appels} avecPoints onRejouer={rejouer} />,
    );
    expect(screen.getByText("Il te reste 4 vies aujourd'hui.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Rejouer/ })).toBeEnabled();

    rerender(
      <PartieQuiz key="zero" depart={fin(0)} appels={appels} avecPoints onRejouer={rejouer} />,
    );
    expect(screen.getByText(/Tu as utilisé tes 7 vies aujourd'hui/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /Rejouer/ }));
    expect(screen.getByRole("button", { name: /Rejouer/ })).toBeDisabled();
    expect(rejouer).not.toHaveBeenCalled();
  });
});
