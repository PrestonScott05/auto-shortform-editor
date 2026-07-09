// Launch Remotion Studio with the video manifest generated and temp kept on this drive.
import { spawnSync } from "node:child_process";
import { mkdirSync } from "node:fs";
import { resolve } from "node:path";

const tmp = resolve("..", ".remotion-tmp");
mkdirSync(tmp, { recursive: true });
process.env.TMPDIR = process.env.TEMP = process.env.TMP = tmp;

spawnSync("node", ["gen-manifest.mjs"], { stdio: "inherit", shell: true });
const r = spawnSync("npx", ["remotion", "studio"], { stdio: "inherit", shell: true });
process.exit(r.status ?? 0);
