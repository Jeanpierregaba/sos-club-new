import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { TexteArticle } from "./TexteArticle";

describe("TexteArticle", () => {
  it("rend les intertitres, le gras et les listes", () => {
    const { container } = render(
      <TexteArticle texte={"## Pourquoi\n\nParce que **les mains** comptent.\n\n- savon\n- eau"} />,
    );

    expect(container.querySelector("h2")?.textContent).toBe("Pourquoi");
    expect(container.querySelector("strong")?.textContent).toBe("les mains");
    expect(container.querySelectorAll("li")).toHaveLength(2);
  });

  it("n'interprète jamais de HTML", () => {
    const { container } = render(
      <TexteArticle texte={'<script>alert(1)</script>\n\n<img src="x" onerror="alert(2)">'} />,
    );

    expect(container.querySelector("script")).toBeNull();
    expect(container.querySelector("img")).toBeNull();
  });

  it("ne garde que le texte d'un lien ou d'une image", () => {
    const { container } = render(
      <TexteArticle
        texte={"Voir [ce site](javascript:alert(1)) et ![photo](https://exemple.tg/x.png)"}
      />,
    );

    expect(container.querySelector("a")).toBeNull();
    expect(container.querySelector("img")).toBeNull();
    expect(container.textContent).toContain("ce site");
  });
});
