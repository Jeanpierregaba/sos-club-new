import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { DUREE_RETOUR_MS, PartieQuiz } from "./PartieQuiz";
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

  it("fait clignoter en vert une bonne réponse, puis passe à la suite", async () => {
    vi.useFakeTimers();
    const a = appels();
    a.repondre.mockResolvedValue({
      ...question(2, 20000),
      correction: { rang: 1, juste: true, choix_joueur: 0, choix_attendu: 0 },
    });
    render(<PartieQuiz depart={question(1)} appels={a} avecPoints={false} />);

    await act(async () => fireEvent.click(screen.getByRole("button", { name: /Oui/ })));

    expect(screen.getByRole("button", { name: /Oui/ })).toHaveAttribute("data-correction", "juste");
    expect(screen.getByText("Bonne réponse !")).toBeInTheDocument();
    expect(screen.getByText("Question 1 ?")).toBeInTheDocument();

    await act(async () => vi.advanceTimersByTime(DUREE_RETOUR_MS));
    expect(screen.getByText("Question 2 ?")).toBeInTheDocument();
    // Le serveur ne démarre le chrono de la question suivante qu'après la pause : il reste entier.
    expect(screen.getByText("20 s")).toBeInTheDocument();
  });

  it("montre en rouge le mauvais choix et en vert la bonne réponse", async () => {
    vi.useFakeTimers();
    const a = appels();
    a.repondre.mockResolvedValue({
      ...question(2),
      correction: { rang: 1, juste: false, choix_joueur: 1, choix_attendu: 2 },
    });
    render(<PartieQuiz depart={question(1)} appels={a} avecPoints={false} />);

    await act(async () => fireEvent.click(screen.getByRole("button", { name: /Non/ })));

    expect(screen.getByRole("button", { name: /Non/ })).toHaveAttribute("data-correction", "faux");
    expect(screen.getByRole("button", { name: /Peut-être/ })).toHaveAttribute(
      "data-correction",
      "juste",
    );
    expect(screen.getByText(/la bonne réponse était « Peut-être »/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Oui/ })).toBeDisabled();
  });

  it("corrige aussi une question dont le temps est écoulé", async () => {
    vi.useFakeTimers();
    const a = appels();
    a.reprendre.mockResolvedValue({
      ...question(2),
      correction: { rang: 1, juste: false, choix_joueur: null, choix_attendu: 0 },
    });
    render(<PartieQuiz depart={question(1, 1000)} appels={a} avecPoints={false} />);

    await act(async () => vi.advanceTimersByTime(2100));

    expect(screen.getByRole("button", { name: /Oui/ })).toHaveAttribute("data-correction", "juste");
    expect(screen.getByText(/Temps écoulé : la bonne réponse était « Oui »/)).toBeInTheDocument();
    await act(async () => vi.advanceTimersByTime(DUREE_RETOUR_MS));
    expect(screen.getByText("Question 2 ?")).toBeInTheDocument();
  });

  it("sans correction (certification), passe directement à la suite sans couleur", async () => {
    const a = appels();
    a.repondre.mockResolvedValue(question(2));
    render(<PartieQuiz depart={question(1)} appels={a} avecPoints />);

    await act(async () => fireEvent.click(screen.getByRole("button", { name: /Non/ })));

    expect(screen.getByText("Question 2 ?")).toBeInTheDocument();
    expect(screen.queryByText(/bonne réponse/i)).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Non/ })).toHaveAttribute(
      "data-correction",
      "neutre",
    );
  });

  it("récapitule à la fin les questions ratées et leurs bonnes réponses", () => {
    render(
      <PartieQuiz
        depart={{
          ...fin(13, 0),
          resultat: {
            ...fin(13, 0).resultat!,
            erreurs: [
              {
                rang: 4,
                enonce: "Comment se transmet le VIH ?",
                ta_reponse: "Par la salive",
                reponse_attendue: "Par le sang",
                explication: "Le VIH ne se transmet pas par la salive.",
              },
              {
                rang: 9,
                enonce: "Combien de temps se laver les mains ?",
                ta_reponse: null,
                reponse_attendue: "30 secondes",
                explication: null,
              },
            ],
          },
        }}
        appels={appels()}
        avecPoints={false}
      />,
    );

    expect(screen.getByText(/Tes erreurs \(2\)/)).toBeInTheDocument();
    expect(screen.getByText("Ta réponse : Par la salive")).toBeInTheDocument();
    expect(screen.getByText("Bonne réponse : Par le sang")).toBeInTheDocument();
    expect(screen.getByText("Pas de réponse à temps")).toBeInTheDocument();
    expect(screen.getByText(/ne se transmet pas par la salive/)).toBeInTheDocument();
  });
});
