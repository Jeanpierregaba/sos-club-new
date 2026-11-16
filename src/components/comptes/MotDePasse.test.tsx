import { act, fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  createMemoryHistory,
  createRootRoute,
  createRouter,
  RouterProvider,
} from "@tanstack/react-router";
import type { ReactNode } from "react";

import { ReinitialiserMembre } from "@/components/clubs/ReinitialiserMembre";
import { MotDePasseOublie } from "@/components/comptes/MotDePasseOublie";
import { NouveauMotDePasse } from "@/components/comptes/NouveauMotDePasse";
import { BandeauMotDePasse } from "@/components/espace/BandeauMotDePasse";

const api = vi.hoisted(() => ({
  reinitialiserMembre: vi.fn(),
  demanderLienMotDePasse: vi.fn(),
  choisirMotDePasse: vi.fn(),
}));
vi.mock("@/lib/api/client", async (original) => ({
  ...(await original<typeof import("@/lib/api/client")>()),
  ...api,
}));

beforeEach(() => vi.clearAllMocks());

describe("ReinitialiserMembre (spec 039)", () => {
  it("demande un motif puis montre le mot de passe provisoire une seule fois", async () => {
    api.reinitialiserMembre.mockResolvedValue({ mot_de_passe: "abcd2345efgh" });
    render(<ReinitialiserMembre affiliationId="a-1" pseudonyme="Yao" />);

    fireEvent.click(screen.getByRole("button", { name: "Réinitialiser le mot de passe de Yao" }));
    fireEvent.change(screen.getByRole("textbox"), {
      target: { value: "Mot de passe oublié en classe." },
    });
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Réinitialiser" }));
    });

    expect(api.reinitialiserMembre).toHaveBeenCalledWith("a-1", "Mot de passe oublié en classe.");
    expect(screen.getByLabelText("Mot de passe à donner à l’élève")).toHaveTextContent(
      "abcd2345efgh",
    );
    expect(screen.getByText(/en main propre/)).toBeInTheDocument();
  });

  it("affiche le refus de l'API, par exemple le plafond du jour", async () => {
    const { ErreurApi } = await import("@/lib/api/client");
    api.reinitialiserMembre.mockRejectedValue(
      new ErreurApi(429, "Tu as déjà fait 10 réinitialisations en 24 heures."),
    );
    render(<ReinitialiserMembre affiliationId="a-1" pseudonyme="Yao" />);

    fireEvent.click(screen.getByRole("button", { name: /Réinitialiser le mot de passe/ }));
    fireEvent.change(screen.getByRole("textbox"), {
      target: { value: "Mot de passe oublié en classe." },
    });
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Réinitialiser" }));
    });

    expect(screen.getByText(/10 réinitialisations en 24 heures/)).toBeInTheDocument();
    expect(screen.queryByLabelText("Mot de passe à donner à l’élève")).toBeNull();
  });
});

describe("BandeauMotDePasse (spec 039)", () => {
  it("conseille de choisir son mot de passe sans rien bloquer", () => {
    const onChanger = vi.fn();
    render(<BandeauMotDePasse onChanger={onChanger} />);

    fireEvent.click(screen.getByRole("button", { name: "Choisir mon mot de passe" }));

    expect(screen.getByRole("status")).toHaveTextContent("réinitialisé");
    expect(onChanger).toHaveBeenCalled();
  });
});

async function afficher(contenu: ReactNode) {
  const route = createRootRoute({ component: () => <>{contenu}</> });
  const router = createRouter({
    routeTree: route,
    history: createMemoryHistory({ initialEntries: ["/"] }),
  });
  render(<RouterProvider router={router} />);
  await act(() => router.load());
  await act(async () => {});
}

describe("ReinitialiserMembre, motif (spec 039)", () => {
  it("exige 10 caractères avant d'appeler l'API", async () => {
    render(<ReinitialiserMembre affiliationId="a-1" pseudonyme="Yao" />);
    fireEvent.click(screen.getByRole("button", { name: /Réinitialiser le mot de passe/ }));
    fireEvent.change(screen.getByRole("textbox"), { target: { value: "oublié" } });
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Réinitialiser" }));
    });

    expect(screen.getByText("Indique un motif d'au moins 10 caractères.")).toBeInTheDocument();
    expect(api.reinitialiserMembre).not.toHaveBeenCalled();
  });
});

describe("MotDePasseOublie (spec 039)", () => {
  it("renvoie l'élève vers son encadreur et confirme l'envoi sans rien révéler", async () => {
    api.demanderLienMotDePasse.mockResolvedValue({
      message: "Si cette adresse correspond à un compte, un lien vient d'y être envoyé.",
    });
    await afficher(<MotDePasseOublie />);
    expect(screen.getByText(/Tu es élève/)).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Ton adresse e-mail"), {
      target: { value: " prof@ecole.tg " },
    });
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Recevoir un lien" }));
    });

    expect(api.demanderLienMotDePasse).toHaveBeenCalledWith("prof@ecole.tg");
    expect(screen.getByRole("status")).toHaveTextContent("Si cette adresse correspond à un compte");
  });
});

describe("NouveauMotDePasse (spec 039)", () => {
  it("dit qu'un lien expiré ne sert plus et propose d'en demander un autre", async () => {
    await afficher(<NouveauMotDePasse jeton="x" valide={false} />);
    expect(screen.getByRole("alert")).toHaveTextContent("Ce lien a expiré ou a déjà servi.");
    expect(screen.getByRole("link", { name: "Demander un nouveau lien" })).toBeInTheDocument();
  });

  it("vérifie la longueur et la confirmation avant l'envoi", async () => {
    await afficher(<NouveauMotDePasse jeton="j" valide />);
    fireEvent.change(screen.getByLabelText("Nouveau mot de passe"), { target: { value: "court" } });
    fireEvent.change(screen.getByLabelText("Répète-le"), { target: { value: "court" } });
    fireEvent.click(screen.getByRole("button", { name: "Enregistrer" }));
    expect(screen.getByRole("alert")).toHaveTextContent("au moins 8 caractères");

    fireEvent.change(screen.getByLabelText("Nouveau mot de passe"), {
      target: { value: "un-secret-long" },
    });
    fireEvent.change(screen.getByLabelText("Répète-le"), { target: { value: "un-autre-secret" } });
    fireEvent.click(screen.getByRole("button", { name: "Enregistrer" }));
    expect(screen.getByRole("alert")).toHaveTextContent("pas identiques");
    expect(api.choisirMotDePasse).not.toHaveBeenCalled();
  });

  it("enregistre, puis efface le jeton de l'adresse", async () => {
    api.choisirMotDePasse.mockResolvedValue(undefined);
    const onFait = vi.fn();
    await afficher(<NouveauMotDePasse jeton="j" valide onFait={onFait} />);
    fireEvent.change(screen.getByLabelText("Nouveau mot de passe"), {
      target: { value: "un-secret-long" },
    });
    fireEvent.change(screen.getByLabelText("Répète-le"), { target: { value: "un-secret-long" } });
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Enregistrer" }));
    });

    expect(api.choisirMotDePasse).toHaveBeenCalledWith("j", "un-secret-long");
    expect(onFait).toHaveBeenCalled();
    expect(screen.getByRole("status")).toHaveTextContent("Ton mot de passe est changé");
  });

  it("affiche le refus de l'API, par exemple un lien devenu invalide", async () => {
    const { ErreurApi } = await import("@/lib/api/client");
    api.choisirMotDePasse.mockRejectedValue(
      new ErreurApi(410, "Ce lien a expiré ou a déjà servi."),
    );
    await afficher(<NouveauMotDePasse jeton="j" valide />);
    fireEvent.change(screen.getByLabelText("Nouveau mot de passe"), {
      target: { value: "un-secret-long" },
    });
    fireEvent.change(screen.getByLabelText("Répète-le"), { target: { value: "un-secret-long" } });
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Enregistrer" }));
    });

    expect(screen.getByRole("alert")).toHaveTextContent("Ce lien a expiré ou a déjà servi.");
  });
});
