import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { PartieQuiz } from "./PartieQuiz";
import type { AppelsPartie, EtatPartie } from "@/lib/api/client";

afterEach(() => vi.useRealTimers());

const question = (rang: number, restant = 5000): EtatPartie => ({
  tentative_id: "t1",
  quiz_id: "q1",
  titre: "Quiz",
  total: 15,
  question: {
    rang,
    enonce: `Question ${rang} ?`,
    choix: ["Oui", "Non", "Peut-être"],
    temps_ms: 5000,
    restant_ms: restant,
  },
  resultat: null,
});

const fin = (score: number, points: number): EtatPartie => ({
  tentative_id: "t1",
  quiz_id: "q1",
  titre: "Quiz",
  total: 15,
  question: null,
  resultat: { score, total: 15, seuil: 12, reussie: score >= 12, points },
});

function appels() {
  return {
    repondre: vi.fn<AppelsPartie["repondre"]>(),
    reprendre: vi.fn<AppelsPartie["reprendre"]>(),
  };
}

describe("PartieQuiz", () => {
  it("envoie l'index du choix affiché et passe à la question suivante", async () => {
    const a = appels();
    a.repondre.mockResolvedValue(question(2));
    render(<PartieQuiz depart={question(1)} appels={a} avecPoints />);

    expect(screen.getByText("Question 1 / 15")).toBeInTheDocument();
    await act(async () => fireEvent.click(screen.getByRole("button", { name: /Non/ })));

    expect(a.repondre).toHaveBeenCalledWith("t1", 1, 1);
    expect(screen.getByText("Question 2 ?")).toBeInTheDocument();
  });

  it("à la fin du temps, bloque les choix et redemande l'état au serveur", async () => {
    vi.useFakeTimers();
    const a = appels();
    a.reprendre.mockResolvedValue(question(2));
    render(<PartieQuiz depart={question(1, 1000)} appels={a} avecPoints />);

    await act(async () => vi.advanceTimersByTime(1100));
    expect(screen.getByRole("button", { name: /Oui/ })).toBeDisabled();
    expect(screen.getByText(/Temps écoulé/)).toBeInTheDocument();

    await act(async () => vi.advanceTimersByTime(1000));
    expect(a.reprendre).toHaveBeenCalledWith("t1");
    expect(screen.getByText("Question 2 ?")).toBeInTheDocument();
  });

  it("affiche le score, la réussite et les points gagnés", () => {
    render(<PartieQuiz depart={fin(13, 50)} appels={appels()} avecPoints />);

    expect(screen.getByRole("status")).toHaveTextContent("Bravo, quiz réussi !");
    expect(screen.getByText("+50 points")).toBeInTheDocument();
  });

  it("dit qu'il manque des bonnes réponses, sans parler de points", () => {
    render(<PartieQuiz depart={fin(11, 0)} appels={appels()} avecPoints />);

    expect(screen.getByRole("status")).toHaveTextContent("il faut 12 bonnes réponses");
    expect(screen.queryByText(/points/)).not.toBeInTheDocument();
  });

  it("ne parle jamais de points pour un encadreur ou un essai", () => {
    render(<PartieQuiz depart={fin(15, 0)} appels={appels()} avecPoints={false} />);

    expect(screen.queryByText(/points/)).not.toBeInTheDocument();
  });

  it("propose de reprendre après une erreur réseau", async () => {
    const a = appels();
    a.repondre.mockRejectedValue(new Error("coupure"));
    a.reprendre.mockResolvedValue(question(2));
    render(<PartieQuiz depart={question(1)} appels={a} avecPoints />);

    await act(async () => fireEvent.click(screen.getByRole("button", { name: /Oui/ })));
    await act(async () => fireEvent.click(screen.getByRole("button", { name: "Reprendre" })));

    expect(screen.getByText("Question 2 ?")).toBeInTheDocument();
  });
});
