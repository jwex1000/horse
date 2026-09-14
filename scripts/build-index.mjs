#!/usr/bin/env node
// Builds index.json at the repo root: the catalog the companion site fetches.
// Reads frontmatter from every <element>/prompts/*.md. No dependencies.

import { readFileSync, writeFileSync, readdirSync, existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");

// HORSE order, with the display word and the site route for each element.
const ELEMENTS = [
  { key: "harness", word: "Harness", path: "/harness" },
  { key: "objective", word: "Objective", path: "/objective" },
  { key: "role", word: "Role", path: "/role" },
  { key: "scope", word: "Scope", path: "/scope" },
  { key: "evaluate", word: "Evaluate", path: "/evaluate" },
];

function parseFrontmatter(text) {
  if (!text.startsWith("---")) return {};
  const end = text.indexOf("\n---", 3);
  if (end === -1) return {};
  const block = text.slice(3, end).trim();
  const data = {};
  for (const line of block.split("\n")) {
    const i = line.indexOf(":");
    if (i === -1) continue;
    const key = line.slice(0, i).trim();
    let value = line.slice(i + 1).trim();
    value = value.replace(/^["']|["']$/g, "");
    data[key] = value;
  }
  return data;
}

const prompts = [];
for (const el of ELEMENTS) {
  const dir = join(root, el.key, "prompts");
  if (!existsSync(dir)) continue;
  const files = readdirSync(dir).filter((f) => f.endsWith(".md")).sort();
  for (const file of files) {
    const fm = parseFrontmatter(readFileSync(join(dir, file), "utf8"));
    const slug = file.replace(/\.md$/, "");
    prompts.push({
      element: el.key,
      slug,
      title: fm.title ?? "",
      level: fm.level ?? "",
      style: fm.style ?? "",
      summary: fm.summary ?? "",
      use_when: fm.use_when ?? "",
      path: `${el.key}/prompts/${file}`,
      is_start_here: slug === "start-here",
    });
  }
}

const index = {
  generated_at: new Date().toISOString(),
  elements: ELEMENTS,
  prompts,
};

writeFileSync(join(root, "index.json"), JSON.stringify(index, null, 2) + "\n");
console.log(`Wrote index.json — ${prompts.length} prompts across ${ELEMENTS.length} elements.`);
