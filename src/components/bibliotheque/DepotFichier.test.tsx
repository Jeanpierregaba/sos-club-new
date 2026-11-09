import { act, fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ErreurApi } from "@/lib/api/client";

import { DepotFichier } from "./DepotFichier";

const pdf = () => new File(["%PDF-1.7"], "guide.pdf", { type: "application/pdf" });

describe("DepotFichier", () => {
  it("envoie le fichier choisi dès sa sélection", async () => {
    const envoie = vi.fn().mockResolvedValue(undefined);
    render(
      <DepotFichier
        libelle="Déposer le PDF"
        accept="application/pdf"
        aide="20 Mo au plus."
        onEnvoie={envoie}
      />,
    );
    const fichier = pdf();

    await act(async () =>
      fireEvent.change(screen.getByLabelText("Déposer le PDF"), { target: { files: [fichier] } }),
    );

    expect(envoie).toHaveBeenCalledWith(fichier, expect.any(Function));
    expect(screen.queryByRole("alert")).toBeNull();
  });

  it("affiche le refus de l'API", async () => {
    const envoie = vi.fn().mockRejectedValue(new ErreurApi(422, "Ce PDF contient du JavaScript."));
    render(
      <DepotFichier libelle="Déposer le PDF" accept="application/pdf" aide="" onEnvoie={envoie} />,
    );

    await act(async () =>
      fireEvent.change(screen.getByLabelText("Déposer le PDF"), { target: { files: [pdf()] } }),
    );

    expect(screen.getByRole("alert")).toHaveTextContent("Ce PDF contient du JavaScript.");
  });

  it("montre la progression pendant l'envoi", async () => {
    let finir: () => void = () => {};
    const envoie = vi.fn((_: File, progression: (f: number) => void) => {
      progression(0.4);
      return new Promise<void>((r) => (finir = r));
    });
    render(
      <DepotFichier libelle="Déposer le PDF" accept="application/pdf" aide="" onEnvoie={envoie} />,
    );

    await act(async () =>
      fireEvent.change(screen.getByLabelText("Déposer le PDF"), { target: { files: [pdf()] } }),
    );

    expect(screen.getByRole("progressbar")).toHaveAttribute("aria-valuenow", "40");
    await act(async () => finir());
    expect(screen.queryByRole("progressbar")).toBeNull();
  });
});
