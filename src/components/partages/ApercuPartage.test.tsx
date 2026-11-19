import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ApercuPartage } from "./ApercuPartage";

describe("ApercuPartage", () => {
  it("montre le réseau et ouvre le lien sans transmettre l'adresse de l'admin", () => {
    render(
      <ApercuPartage
        champs={{
          reseau: "tiktok",
          nature: "partage",
          lien: "https://www.tiktok.com/@ama/video/1",
        }}
      />,
    );

    expect(screen.getByText("Partage de son propre article")).toBeInTheDocument();
    expect(screen.getByText(/sur TikTok/)).toBeInTheDocument();
    const lien = screen.getByRole("link", { name: "https://www.tiktok.com/@ama/video/1" });
    expect(lien).toHaveAttribute("target", "_blank");
    expect(lien).toHaveAttribute("rel", "noopener noreferrer nofollow");
  });

  it("n'ouvre jamais un lien qui n'est pas en https", () => {
    render(
      <ApercuPartage
        champs={{ reseau: "facebook", nature: "republication", lien: "javascript:alert(1)" }}
      />,
    );

    expect(screen.getByText("Republication d'un article du site")).toBeInTheDocument();
    expect(screen.queryByRole("link")).not.toBeInTheDocument();
    expect(screen.getByText("javascript:alert(1)")).toBeInTheDocument();
  });
});
