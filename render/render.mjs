// Render a final mp4 for one video id.
//   npm run render -- <videoId>
// Reads props from public/<id>/editplan.json, encodes to ../out/<id>.mp4 with GPU accel.
import { spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import { resolve } from "node:path";

// Ensure src/manifest.ts exists so the bundle compiles.
spawnSync("node", ["gen-manifest.mjs"], { stdio: "inherit", shell: true });

const id = process.argv[2];
if (!id) {
  console.error("usage: npm run render -- <videoId>");
  process.exit(1);
}

const props = resolve("public", id, "editplan.json");
if (!existsSync(props)) {
  console.error(`no editplan at ${props} — run the pipeline (stage s5) first`);
  process.exit(1);
}

const out = resolve("..", "out", `${id}.mp4`);
const args = [
  "remotion", "render", "TierList", out,
  `--props=${props}`,
  "--hardware-acceleration=if-possible",
  "--concurrency=50%",
];
console.log("npx " + args.join(" "));
const r = spawnSync("npx", args, { stdio: "inherit", shell: true });
process.exit(r.status ?? 1);
