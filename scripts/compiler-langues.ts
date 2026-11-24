// Compile les textes de l'interface (messages/*.json) dans src/paraglide, avec la même configuration que Vite.
// Le build et le serveur de développement le font seuls ; ce script sert à la vérification des types et aux tests.
import { compile } from "@inlang/paraglide-js";

import { OPTIONS_PARAGLIDE } from "../src/lib/langues-config.ts";

await compile(OPTIONS_PARAGLIDE);
