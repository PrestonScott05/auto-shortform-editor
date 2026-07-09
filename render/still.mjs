// Render a single still frame to preview layout without a full render.
//   npm run still -- <videoId> <frame>
import { spawnSync } from "node:child_process";
import { existsSync, mkdirSync } from "node:fs";
import { resolve } from "node:path";

// Keep Remotion's temp bundle on this project's drive (system temp may be small/full).
const tmp = resolve("..", ".remotion-tmp");
mkdirSync(tmp, { recursive: true });
process.env.TMPDIR = process.env.TEMP = process.env.TMP = tmp;

// Ensure src/manifest.ts exists so the bundle compiles.
spawnSync("node", ["gen-manifest.mjs"], { stdio: "inherit", shell: true });

const id = process.argv[2];
const frame = process.argv[3] ?? "0";
if (!id) {
  console.error("usage: npm run still -- <videoId> <frame>");
  process.exit(1);
}
const props = resolve("public", id, "editplan.json");
if (!existsSync(props)) {
  console.error(`no editplan at ${props} — run stage s5 first`);
  process.exit(1);
}
const out = resolve("..", "out", `${id}_f${frame}.png`);
const args = [
  "remotion", "still", "TierList", out,
  `--props=${props}`,
  `--frame=${frame}`,
];
console.log("npx " + args.join(" "));
const r = spawnSync("npx", args, { stdio: "inherit", shell: true });
process.exit(r.status ?? 1);
