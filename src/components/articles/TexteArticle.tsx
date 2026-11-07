import Markdown from "react-markdown";

// Le texte d'un article (spec 023) : un sous-ensemble de Markdown. Seuls les paragraphes, intertitres, gras,
// italique et listes sont rendus ; un lien, une image ou un tableau ne garde que son texte, et le HTML écrit dans
// l'article s'affiche comme du texte, jamais interprété.
const ELEMENTS = ["p", "h2", "h3", "strong", "em", "ul", "ol", "li", "br"];

export function TexteArticle({ texte, className = "" }: { texte: string; className?: string }) {
  return (
    <div
      className={`space-y-4 text-base leading-relaxed text-ink/85 [&_h2]:mt-8 [&_h2]:font-display [&_h2]:text-2xl [&_h2]:text-ink [&_h3]:mt-6 [&_h3]:font-display [&_h3]:text-xl [&_h3]:text-ink [&_ol]:list-decimal [&_ol]:space-y-1 [&_ol]:pl-6 [&_strong]:font-bold [&_strong]:text-ink [&_ul]:list-disc [&_ul]:space-y-1 [&_ul]:pl-6 ${className}`}
    >
      <Markdown allowedElements={ELEMENTS} unwrapDisallowed urlTransform={() => ""}>
        {texte}
      </Markdown>
    </div>
  );
}
