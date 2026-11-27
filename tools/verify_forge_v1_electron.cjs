"use strict";

// Gate em Windows com navegador e compositor reais, sem dependências do Studio.
const assert = require("node:assert/strict");
const { execFile, spawn } = require("node:child_process");
const { createHash } = require("node:crypto");
const { mkdir, readFile, writeFile } = require("node:fs/promises");
const path = require("node:path");
const { createInterface } = require("node:readline");
const { setTimeout: delay } = require("node:timers/promises");
const { parseArgs, promisify } = require("node:util");

const run = promisify(execFile);
const studio = path.resolve(__dirname, "..");
const examples = ["concordancia", "curiosidade", "negacao", "ocioso", "saudacao"];
const sha256 = bytes => createHash("sha256").update(bytes).digest("hex");
const readJson = async file => JSON.parse(await readFile(file, "utf8"));
const json = value => Buffer.from(JSON.stringify(value, null, 2) + "\n");
const maxBytes = 4 * 1024 * 1024;

async function withStudio(output, python, use) {
  const service = spawn(python, ["-u", "-c", [
    "from app.server import Handler, ThreadingHTTPServer",
    "server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)",
    "print(server.server_port, flush=True)",
    "server.serve_forever()",
  ].join("\n")], {
    cwd: studio,
    env: { ...process.env, LIA_PROJECTS_DIR: path.join(output, "workspace"), PYTHONDONTWRITEBYTECODE: "1" },
    stdio: ["ignore", "pipe", "inherit"],
  });
  const closed = new Promise(resolve => service.once("close", resolve));
  const lines = createInterface({ input: service.stdout });
  const started = new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(Error("Studio não iniciou em 15 segundos")), 15_000);
    const settle = fn => value => { clearTimeout(timer); fn(value); };
    service.once("error", settle(reject));
    service.once("exit", settle(code => reject(Error(`Studio encerrou: ${code}`))));
    lines.once("line", settle(port => resolve(Number(port))));
  });
  try {
    const port = await started;
    assert.ok(Number.isInteger(port) && port > 0 && port <= 65535);
    await use(port);
  } finally {
    lines.close();
    service.kill();
    await closed;
  }
}

async function verifyForge(output, forge) {
  const compose = (source, destination, approval) => run(process.execPath, [
    "scripts/animation-pipeline.mjs", source, destination, ...(approval ? [approval] : []),
  ], { cwd: forge, timeout: 30_000 });
  const report = [];
  for (const id of examples) {
    const original = await readFile(path.join(forge, "examples", "animation", id + ".json"));
    const fixture = await readFile(path.join(studio, "tests", "fixtures", "forge-v1-official", id + ".json"));
    assert.deepEqual(fixture, original);
    const spec = JSON.parse(original);
    const saved = path.join(output, id + "-original.json");
    const edited = path.join(output, id + "-revised.json");
    assert.deepEqual(await readFile(saved), original);

    const approval = {
      id, version: spec.version, sourceSha256: sha256(original), license: spec.provenance.license,
      reviewer: "Fixture de QA", decision: "approved",
    };
    const approvalFile = path.join(output, id + "-approval.fixture.json");
    await writeFile(approvalFile, json(approval));
    const approvedDir = path.join(output, id + "-package-original");
    const revisedDir = path.join(output, id + "-package-revised");
    await compose(saved, approvedDir, approvalFile);
    const approved = await readJson(path.join(approvedDir, "manifest.json"));
    assert.equal(approved.rights.state, "approved");
    assert.equal(approved.files["spec.json"], approval.sourceSha256);

    await assert.rejects(compose(edited, path.join(output, id + "-stale-approval"), approvalFile),
      error => error.code === 1 && /aprova|decis[aã]o/i.test(error.stderr));
    await compose(edited, revisedDir);
    const revised = await readJson(path.join(revisedDir, "manifest.json"));
    assert.equal(revised.id, id);
    assert.equal(revised.version, "1.0.1");
    assert.deepEqual(revised.provenance, spec.provenance);
    assert.equal(revised.rights.state, "review-required");
    assert.equal(revised.rights.redistributable, false);
    assert.notEqual(revised.files["spec.json"], approved.files["spec.json"]);
    for (const [name, digest] of Object.entries(revised.files)) {
      assert.equal(sha256(await readFile(path.join(revisedDir, name))), digest);
    }
    report.push({ id, original: approved.files["spec.json"], edited: revised.files["spec.json"],
      approvalPreserved: true, oldApprovalRejectedForRevision: true, newRights: revised.rights.state });
    console.log(`PASS Forge → Studio → Forge: ${id}`);
  }
  const invalid = path.join(output, "invalid-quaternion.json");
  await assert.rejects(compose(invalid, path.join(output, "invalid-package")),
    error => error.code === 1 && error.stderr.includes("Quaternion deve ser unitário"));
  return report;
}

async function orchestrate() {
  const { values } = parseArgs({ options: {
    electron: { type: "string" }, forge: { type: "string" }, output: { type: "string" },
    python: { type: "string", default: "python" },
  } });
  if (!values.electron || !values.forge || !values.output) {
    throw Error("Use --electron <electron.exe> --forge <checkout> --output <novo diretório> [--python <executável>]");
  }
  const output = path.resolve(values.output);
  await mkdir(output);
  await withStudio(output, values.python, async port => {
    const env = { ...process.env, LIA_STUDIO_FORGE_E2E_OUTPUT: output, LIA_STUDIO_FORGE_E2E_PORT: String(port) };
    delete env.ELECTRON_RUN_AS_NODE;
    try {
      const { stdout, stderr } = await run(path.resolve(values.electron), [__filename], { env, timeout: 120_000 });
      await writeFile(path.join(output, "electron.log"), stdout + stderr);
    } catch (error) {
      await writeFile(path.join(output, "electron.log"), (error.stdout ?? "") + (error.stderr ?? ""));
      throw error;
    }
  });
  const renderer = await readJson(path.join(output, "renderer.json"));
  const roundTrip = await verifyForge(output, path.resolve(values.forge));
  await writeFile(path.join(output, "report.json"), json({ platform: process.platform, renderer, roundTrip }));
  console.log(`Evidências em ${output}`);
}

async function until(predicate, message) {
  const end = Date.now() + 10_000;
  while (Date.now() < end) {
    if (await predicate()) return;
    await delay(25);
  }
  assert.fail(message);
}

async function verifyEditor(app, BrowserWindow) {
  const output = process.env.LIA_STUDIO_FORGE_E2E_OUTPUT;
  const origin = "http://127.0.0.1:" + process.env.LIA_STUDIO_FORGE_E2E_PORT;
  assert.ok(path.isAbsolute(output));
  app.setPath("userData", path.join(output, "electron-profile"));
  await app.whenReady();
  const window = new BrowserWindow({
    show: false, width: 1280, height: 850,
    webPreferences: { contextIsolation: true, nodeIntegration: false, sandbox: true, backgroundThrottling: false },
  });
  const { debugger: browser, session } = window.webContents;
  const evaluate = (source, gesture = false) => window.webContents.executeJavaScript(source, gesture);
  session.webRequest.onBeforeRequest(({ url }, callback) => callback({ cancel: new URL(url).origin !== origin }));
  window.webContents.setWindowOpenHandler(() => ({ action: "deny" }));
  await window.loadURL(origin + "/static/forge-animation.html");
  browser.attach();
  const control = expression => evaluate(`(() => {
    const $ = selector => document.querySelector(selector);
    return ${expression};
  })()`);
  const status = () => control('$("#forge-status").textContent');
  const exportDisabled = () => control('$("#forge-export").disabled');
  const results = {};

  async function open(file, message = "Arquivo aberto localmente") {
    const { root } = await browser.sendCommand("DOM.getDocument");
    const { nodeId } = await browser.sendCommand("DOM.querySelector", { nodeId: root.nodeId, selector: "#forge-file" });
    await browser.sendCommand("DOM.setFileInputFiles", { nodeId, files: [file] });
    await until(async () => (await status()).includes(message), `Importação sem estado esperado: ${message}`);
    assert.equal(await exportDisabled(), true);
  }

  async function edit(source) {
    await control(`(() => {
      const input = $("#forge-source");
      input.value = ${JSON.stringify(source)};
      input.dispatchEvent(new Event("input", { bubbles: true }));
    })()`);
    assert.equal(await exportDisabled(), true);
  }

  async function verify(expected, expectedError) {
    await control('$("#forge-check").click()');
    await until(() => control('!$("#forge-check").disabled'), "Inspeção não terminou");
    if (expectedError) {
      assert.match(await status(), expectedError);
      assert.equal(await exportDisabled(), true);
      return;
    }
    assert.equal(await exportDisabled(), false, await status());
    assert.ok((await control('$("#forge-details").textContent')).includes(sha256(expected)));
  }

  async function download(filename, expected) {
    const destination = path.join(output, filename);
    const onDownload = (_, item) => item.setSavePath(destination);
    session.once("will-download", onDownload);
    try {
      await evaluate('document.querySelector("#forge-export").click()', true);
      await until(async () => expected.equals(await readFile(destination).catch(() => Buffer.alloc(0))),
        `Download divergente: ${filename}`);
    } finally {
      session.removeListener("will-download", onDownload);
    }
    return destination;
  }

  for (const id of examples) {
    const fixture = path.join(studio, "tests", "fixtures", "forge-v1-official", id + ".json");
    const original = await readFile(fixture);
    await open(fixture);
    await verify(original);
    await download(id + "-original.json", original);
    const revision = JSON.parse(original);
    revision.timeline[1].intensity *= 0.9;
    if (id === "saudacao") {
      await edit(json(revision).toString());
      await verify(null, /Aumente a versão/);
    }
    revision.version = "1.0.1";
    const edited = json(revision);
    await edit(edited.toString());
    await verify(edited);
    assert.match(await status(), /nova aprovação/);
    if (id === "saudacao") {
      await control(`new Promise(resolve => {
        window.scrollTo(0, 0);
        $("#forge-source").scrollTop = 0;
        requestAnimationFrame(() => requestAnimationFrame(resolve));
      })`);
      await writeFile(path.join(output, "review-revision.png"), (await window.capturePage()).toPNG());
    }
    const downloadPath = await download(id + "-revised.json", edited);
    if (id === "saudacao") {
      revision.timeline[1].intensity *= 0.9;
      await edit(json(revision).toString());
      await verify(null, /Aumente a versão/);
      revision.version = "1.0.2";
      const nextRevision = json(revision);
      await edit(nextRevision.toString());
      await verify(nextRevision);
      await download(id + "-second-revision.json", nextRevision);
      results.sequentialRevisionRejected = true;
    }
    await open(downloadPath);
    await verify(edited);
    results[id] = { original: sha256(original), revised: sha256(edited), reimported: true };
  }

  const original = JSON.parse(await readFile(path.join(output, "saudacao-original.json")));
  original.provenance.author = "João • ação 🎮";
  const unicodeLF = json(original);
  const unicodeCRLF = Buffer.from(unicodeLF.toString().replaceAll("\n", "\r\n"));
  for (const [name, input] of [["unicode-lf", unicodeLF], ["unicode-crlf", unicodeCRLF]]) {
    const file = path.join(output, name + "-source.json");
    await writeFile(file, input);
    await open(file);
    await verify(input);
    await edit(JSON.stringify(original));
    await verify(input);
    await download(name + "-export.json", input);
  }
  const invalid = structuredClone(original);
  const pose = Object.values(invalid.poses).find(value => Object.keys(value.rotations).length > 0);
  pose.rotations[Object.keys(pose.rotations)[0]] = [0, 0, 0, 0];
  const invalidFile = path.join(output, "invalid-quaternion.json");
  await writeFile(invalidFile, json(invalid));
  await open(invalidFile);
  await verify(null, /rotação ou osso inválido/);

  const sizeFile = path.join(output, "size-limit.json");
  const atLimit = Buffer.alloc(maxBytes, 32);
  unicodeLF.copy(atLimit);
  for (let i = unicodeLF.length + 1000; i < maxBytes; i += 1001) atLimit[i] = 10;
  await writeFile(sizeFile, atLimit);
  await open(sizeFile);
  await verify(atLimit);
  await download("size-limit-export.json", atLimit);
  const oversizeFile = path.join(output, "oversize.json");
  await writeFile(oversizeFile, Buffer.concat([atLimit, Buffer.from("\n")]));
  await open(oversizeFile, "Arquivo acima de 4 MiB");

  const invalids = [
    ["encoding", Buffer.from([0xff]), "UTF-8 válido"],
    ["bom", Buffer.concat([Buffer.from([0xef, 0xbb, 0xbf]), unicodeLF]), "UTF-8 sem BOM"],
    ["json", Buffer.from("{ invalid"), "Arquivo aberto localmente"],
  ];
  for (const [name, raw, message] of invalids) {
    const file = path.join(output, name + "-input.json");
    await writeFile(file, raw);
    await open(file, message);
  }
  await verify(null, /JSON ilegível/);
  await writeFile(path.join(output, "renderer.json"), json({
    electron: process.versions.electron, results, sameVersionRejected: true,
    unicode: { lf: sha256(unicodeLF), crlf: sha256(unicodeCRLF), formattingOnlyPreserved: true },
    invalidQuaternionRejected: true, invalidUtf8Rejected: true, bomRejected: true, invalidJsonRejected: true,
    maxBytes: atLimit.length, oversizedRejected: true,
  }));
}

if (process.versions.electron) {
  const { app, BrowserWindow } = require("electron");
  verifyEditor(app, BrowserWindow).then(
    () => app.exit(0),
    error => { console.error(error); app.exit(1); },
  );
} else {
  orchestrate().catch(error => { console.error(error); process.exitCode = 1; });
}
