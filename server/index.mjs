// Local dashboard: video select (upload or existing) -> run pipeline -> edit -> Studio.
// Ties together the Python pipeline (pipeline/orchestrate.py), the editplan editor
// (review/review.html), and Remotion Studio (render/) behind one localhost origin, so the
// editor's Save button can write files directly (browsers only allow that over http(s),
// not file://) and nothing requires opening a file manager.
import express from "express";
import multer from "multer";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";
import path from "node:path";
import fs from "node:fs";
import yaml from "js-yaml";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, "..");

// JSON_SCHEMA restricts parsing to plain JSON-compatible types (js-yaml's load() is
// already safe-by-default in v4, unlike Python's PyYAML, but this is the explicit belt-and-braces version).
const cfg = yaml.load(fs.readFileSync(path.join(ROOT, "config.yaml"), "utf8"), { schema: yaml.JSON_SCHEMA });
const VIDEOS_DIR = path.join(ROOT, cfg.paths.videos_dir);
const WORK_DIR = path.join(ROOT, cfg.paths.work_dir);
const PUBLIC_DIR = path.join(ROOT, cfg.paths.render_public);

fs.mkdirSync(VIDEOS_DIR, { recursive: true });
fs.mkdirSync(WORK_DIR, { recursive: true });

const PY = process.platform === "win32"
  ? path.join(ROOT, ".venv", "Scripts", "python.exe")
  : path.join(ROOT, ".venv", "bin", "python");

const app = express();
app.use(express.json({ limit: "50mb" })); // editplans can carry base64 image data URIs

// ---- static: dashboard, editor, and rendered assets (images/source videos/editplans) ----
app.use(express.static(path.join(__dirname, "public")));
app.use("/review", express.static(path.join(ROOT, "review")));
app.use("/render/public", express.static(PUBLIC_DIR));

// ============================== video listing ==============================
const VIDEO_EXTS = new Set([".mov", ".mp4", ".mkv", ".webm"]);

function readJsonSafe(p) {
  try {
    return JSON.parse(fs.readFileSync(p, "utf8"));
  } catch {
    return null;
  }
}

function listVideos() {
  if (!fs.existsSync(VIDEOS_DIR)) return [];
  return fs.readdirSync(VIDEOS_DIR)
    .filter((f) => VIDEO_EXTS.has(path.extname(f).toLowerCase()))
    .sort()
    .map((f) => {
      const id = path.parse(f).name;
      const wd = path.join(WORK_DIR, id);
      const has = (name) => fs.existsSync(path.join(wd, name));
      const cls = has("classification.json") ? readJsonSafe(path.join(wd, "classification.json")) : null;
      const plan = has("editplan.json") ? readJsonSafe(path.join(wd, "editplan.json")) : null;
      return {
        id,
        filename: f,
        stages: {
          transcript: has("transcript.json"),
          classified: has("classification.json"),
          extracted: has("events.json") || has("cuts.json"),
          images: has("events.json") ? (readJsonSafe(path.join(wd, "events.json"))?.items || []).every((it) => it.image) : null,
          editplan: has("editplan.json"),
        },
        category: cls?.category ?? null,
        label: cls?.label ?? null,
        template: plan?.template ?? null,
      };
    });
}

app.get("/api/videos", (req, res) => res.json(listVideos()));

// ============================== upload (select video files) ==============================
const upload = multer({
  storage: multer.diskStorage({
    destination: (req, file, cb) => cb(null, VIDEOS_DIR),
    filename: (req, file, cb) => cb(null, path.basename(file.originalname)),
  }),
  fileFilter: (req, file, cb) => cb(null, VIDEO_EXTS.has(path.extname(file.originalname).toLowerCase())),
});
app.post("/api/upload", upload.array("videos"), (req, res) => {
  res.json({ uploaded: (req.files || []).map((f) => f.filename) });
});

// ============================== editplan save (the editor's "Save" button) ==============================
app.put("/api/editplan/:id", (req, res) => {
  const id = req.params.id;
  const plan = req.body;
  if (!plan || typeof plan !== "object") return res.status(400).json({ error: "expected an editplan JSON body" });
  const pubDir = path.join(PUBLIC_DIR, id);
  if (!fs.existsSync(pubDir)) return res.status(404).json({ error: `unknown video id '${id}'` });
  fs.writeFileSync(path.join(pubDir, "editplan.json"), JSON.stringify(plan, null, 2));
  const workFile = path.join(WORK_DIR, id, "editplan.json");
  if (fs.existsSync(path.dirname(workFile))) fs.writeFileSync(workFile, JSON.stringify(plan, null, 2));
  res.json({ ok: true });
});

// ============================== pipeline runs ==============================
const jobs = new Map();
let nextJobId = 1;

function runJob(args) {
  const id = String(nextJobId++);
  const job = { id, status: "running", log: [], exitCode: null, args };
  jobs.set(id, job);
  const proc = spawn(PY, args, { cwd: ROOT });
  const onData = (buf) => {
    for (const line of buf.toString().split(/\r?\n/)) {
      if (line.trim()) job.log.push(line);
    }
    if (job.log.length > 3000) job.log.splice(0, job.log.length - 3000);
  };
  proc.stdout.on("data", onData);
  proc.stderr.on("data", onData);
  proc.on("close", (code) => { job.status = code === 0 ? "done" : "error"; job.exitCode = code; });
  proc.on("error", (err) => { job.status = "error"; job.log.push(`spawn error: ${err.message}`); });
  return job;
}

app.post("/api/run", (req, res) => {
  const { ids = [], only = [], force = false } = req.body || {};
  const args = [path.join(ROOT, "pipeline", "orchestrate.py"), ...ids];
  if (only.length) args.push(`--only=${only.join(",")}`);
  if (force) args.push("--force");
  const job = runJob(args);
  res.json({ jobId: job.id });
});

app.get("/api/run/:jobId", (req, res) => {
  const job = jobs.get(req.params.jobId);
  if (!job) return res.status(404).json({ error: "unknown job" });
  res.json(job);
});

// ============================== Remotion Studio launch ==============================
let studioProc = null;
app.post("/api/studio/launch", (req, res) => {
  if (studioProc && studioProc.exitCode === null) {
    return res.json({ url: "http://localhost:3000", already: true });
  }
  studioProc = spawn("npm", ["run", "studio"], {
    cwd: path.join(ROOT, "render"), shell: true, detached: true, stdio: "ignore",
  });
  studioProc.unref();
  res.json({ url: "http://localhost:3000", already: false });
});

const PORT = process.env.PORT || 4000;
app.listen(PORT, () => console.log(`Dashboard running at http://localhost:${PORT}`));
