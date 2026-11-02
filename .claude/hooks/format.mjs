// PostToolUse : formate automatiquement chaque fichier modifié par l'agent.
import { spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import path from "node:path";
import { projectDir, readStdinJson, relativeToProject } from "./lib.mjs";

// Le chemin du fichier est ajouté à la fin de la commande.
const PRETTIER_COMMAND = "npx prettier --write --ignore-unknown";
const RUFF_COMMAND = "uv run --directory backend ruff format";

const input = readStdinJson();
const filePath = input.tool_input?.file_path;
if (!filePath) process.exit(0);

const absolute = path.resolve(projectDir, filePath);
const rel = relativeToProject(absolute);
// Uniquement les fichiers du projet, hors dépendances.
if (rel.startsWith("..") || /(^|\/)node_modules\//.test(rel) || !existsSync(absolute))
  process.exit(0);

const command = absolute.endsWith(".py") ? RUFF_COMMAND : PRETTIER_COMMAND;
const result = spawnSync(`${command} ${JSON.stringify(absolute)}`, {
  cwd: projectDir,
  shell: true,
  encoding: "utf8",
});

if (result.status !== 0) {
  // Code 1 = erreur non bloquante : affichée à l'utilisateur, l'agent continue.
  process.stderr.write(`Formatage échoué pour ${rel} :\n${result.stderr || result.stdout || ""}`);
  process.exit(1);
}
