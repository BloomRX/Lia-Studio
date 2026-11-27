"use strict";
/* Forge V1 raw-spec editor. No conversion from Studio drafts, no runtime action. */
(function () {
  const $ = id => document.getElementById(id);
  const input = $("forge-file"), source = $("forge-source");
  const status = $("forge-status"), details = $("forge-details");
  const check = $("forge-check"), save = $("forge-export");
  const maxBytes = 4 * 1024 * 1024;
  const decoder = new TextDecoder("utf-8", { fatal: true, ignoreBOM: true });
  const encoder = new TextEncoder();
  let imported = null;
  let verified = null;
  let pendingCheck = null;
  let generation = 0;
  let loading = false;
  const renderStatus = text => { status.textContent = text; };

  function updateButtons() {
    check.disabled = loading || pendingCheck !== null;
    save.disabled = verified === null;
  }

  function invalidate() {
    verified = null;
    pendingCheck?.abort();
    pendingCheck = null;
    details.replaceChildren();
    updateButtons();
  }

  function sameValue(left, right) {
    if (left === right) return true;
    if (left === null || right === null || typeof left !== "object" || typeof right !== "object") return false;
    if (Array.isArray(left) !== Array.isArray(right)) return false;
    const keys = Object.keys(left);
    return keys.length === Object.keys(right).length &&
      keys.every(key => Object.prototype.hasOwnProperty.call(right, key) && sameValue(left[key], right[key]));
  }

  function isNewerVersion(candidate, previous) {
    const current = candidate.split(".");
    const original = previous.split(".");
    for (let i = 0; i < current.length; i += 1) {
      const next = current[i].replace(/^0+(?=\d)/, "");
      const before = original[i].replace(/^0+(?=\d)/, "");
      if (next.length !== before.length) return next.length > before.length;
      if (next !== before) return next > before;
    }
    return false;
  }

  async function inspect(bytes, signal, allowInvalid = false) {
    if (bytes.byteLength > maxBytes) throw Error("A especificação excede 4 MiB.");
    const result = await fetch("/api/animation/forge-v1/inspect", {
      method: "POST",
      headers: { "Content-Type": "application/vnd.lia.forge-spec+json" },
      body: bytes,
      signal,
    });
    if (allowInvalid && result.status === 400) return null;
    const data = await result.json();
    if (!result.ok) throw Error(data.error || "A especificação não passou pela validação.");
    return data;
  }

  async function getVerifiedExport(snapshot, original, signal) {
    if (original?.view === snapshot) {
      const meta = original.meta ?? await inspect(original.bytes, signal);
      original.meta = meta;
      return { bytes: original.bytes, meta, preserved: true };
    }

    if (snapshot.length > maxBytes) throw Error("A especificação excede 4 MiB.");
    const bytes = encoder.encode(snapshot);
    const meta = await inspect(bytes, signal);
    if (original) {
      const baseline = original.meta ?? await inspect(original.bytes, signal, true);
      if (baseline) {
        original.meta = baseline;
        if (sameValue(JSON.parse(original.text), JSON.parse(snapshot))) {
          return { bytes: original.bytes, meta: baseline, preserved: true };
        }
        if (!isNewerVersion(meta.version, baseline.version)) {
          throw Error("Aumente a versão do JSON para exportar uma alteração no conteúdo.");
        }
      }
    }
    return { bytes, meta, preserved: false };
  }

  source.addEventListener("input", () => {
    generation += 1;
    loading = false;
    invalidate();
    renderStatus("Conteúdo alterado. Verifique novamente antes de exportar.");
  });
  input.addEventListener("change", async () => {
    const file = input.files?.[0];
    input.value = "";
    if (!file) return;
    const opening = ++generation;
    loading = false;
    invalidate();
    if (file.size > maxBytes) {
      renderStatus("Arquivo acima de 4 MiB. A importação foi recusada.");
      return;
    }
    loading = true;
    updateButtons();
    renderStatus("Abrindo arquivo local…");
    try {
      const bytes = await file.arrayBuffer();
      if (opening !== generation) return;
      const text = decoder.decode(bytes);
      if (text.startsWith("\uFEFF")) throw Error("O arquivo deve usar UTF-8 sem BOM.");
      source.value = text;
      imported = { bytes, text, view: source.value, meta: null };
      renderStatus("Arquivo aberto localmente. Clique Verificar contrato.");
      source.focus();
    } catch (error) {
      if (opening === generation) {
        renderStatus(error instanceof TypeError
          ? "O arquivo deve usar UTF-8 válido."
          : "Falha ao abrir o arquivo. " + (error.message || ""));
      }
    } finally {
      if (opening === generation) {
        loading = false;
        updateButtons();
      }
    }
  });
  check.addEventListener("click", async () => {
    invalidate();
    const snapshot = source.value;
    if (!snapshot) { renderStatus("Abra uma especificação JSON para verificar."); return; }
    const operation = new AbortController();
    pendingCheck = operation;
    updateButtons();
    renderStatus("Verificando estrutura do Forge V1 localmente…");
    try {
      const result = await getVerifiedExport(snapshot, imported, operation.signal);
      if (pendingCheck !== operation || snapshot !== source.value) return;
      verified = { ...result, snapshot };
      const data = result.meta;
      const rows = [
        ["Identificador", data.id], ["Versão", data.version],
        ["Duração", data.duration + " segundos"], ["Perfil", data.rigProfile],
        ["Trilhas ósseas", data.boneTracks], ["Expressões", data.expressions],
        ["Beats", data.beats], ["SHA-256 da exportação", data.sourceSha256],
      ];
      for (const [name, value] of rows) {
        const li = document.createElement("li");
        const strong = document.createElement("strong");
        strong.textContent = name + ": ";
        li.append(strong, document.createTextNode(String(value)));
        details.append(li);
      }
      renderStatus(result.preserved
        ? "Estrutura inspecionada. A exportação preserva os bytes originais."
        : "Nova revisão inspecionada. Recomponha no Forge e solicite nova aprovação para distribuir.");
    } catch (error) {
      if (pendingCheck === operation) {
        renderStatus("Falha na inspeção: " + (error.message || String(error)));
      }
    } finally {
      if (pendingCheck === operation) {
        pendingCheck = null;
        updateButtons();
      }
    }
  });
  save.addEventListener("click", () => {
    if (!verified || source.value !== verified.snapshot) {
      invalidate();
      renderStatus("Conteúdo alterado. Verifique novamente antes de exportar.");
      return;
    }
    const bytes = new Blob([verified.bytes], { type: "application/json;charset=utf-8" });
    const url = URL.createObjectURL(bytes);
    try {
      const link = document.createElement("a");
      link.href = url;
      link.download = verified.meta.id + "-forge-v1-spec.json";
      link.click();
      if (!verified.preserved) {
        imported = { bytes: verified.bytes, text: verified.snapshot, view: verified.snapshot, meta: verified.meta };
      }
      renderStatus(verified.preserved
        ? "JSON original exportado com os mesmos bytes."
        : "Nova revisão exportada. Refaça a composição e a aprovação no Forge antes de publicar.");
    } finally {
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    }
  });
})();
