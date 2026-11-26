"use strict";
/* Forge V1 raw-spec editor. No conversion from Studio drafts, no runtime action. */
(function () {
  const $ = id => document.getElementById(id);
  const input = $("forge-file"), source = $("forge-source");
  const status = $("forge-status"), details = $("forge-details");
  const check = $("forge-check"), save = $("forge-export");
  let lastVerifiedText = null;
  let lastVerifiedMeta = null;
  const renderStatus = text => { status.textContent = text; };
  function invalidate() {
    lastVerifiedText = null;
    lastVerifiedMeta = null;
    save.disabled = true;
    details.replaceChildren();
  }
  source.addEventListener("input", () => {
    invalidate();
    renderStatus("Conteúdo alterado. Verifique novamente antes de exportar.");
  });
  input.addEventListener("change", async () => {
    invalidate();
    const file = input.files?.[0];
    input.value = "";
    if (!file) return;
    if (file.size > 2 * 1024 * 1024) {
      renderStatus("Arquivo acima de 2 MB: importação recusada.");
      return;
    }
    try {
      source.value = await file.text();
      renderStatus("Arquivo aberto localmente. Clique Verificar contrato.");
      source.focus();
    } catch {
      renderStatus("Falha ao ler o arquivo selecionado.");
    }
  });
  check.addEventListener("click", async () => {
    invalidate();
    const snapshot = source.value;
    if (!snapshot) { renderStatus("Abra uma especificação JSON para verificar."); return; }
    check.disabled = true;
    renderStatus("Verificando estrutura do Forge V1 localmente…");
    try {
      const result = await fetch("/api/animation/forge-v1/inspect", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sourceText: snapshot }),
      });
      const data = await result.json();
      if (!result.ok) throw Error(data.error || "A especificação não passou pela validação.");
      if (snapshot !== source.value) {
        renderStatus("Texto modificado durante a verificação. Verifique novamente.");
        return;
      }
      lastVerifiedText = snapshot;
      lastVerifiedMeta = data;
      const rows = [
        ["Identificador", data.id], ["Versão", data.version],
        ["Duração", data.duration + " segundos"], ["Perfil", data.rigProfile],
        ["Trilhas ósseas", data.boneTracks], ["Expressões", data.expressions],
        ["Beats", data.beats], ["SHA-256 do texto", data.sourceSha256],
      ];
      for (const [name, value] of rows) {
        const li = document.createElement("li");
        const strong = document.createElement("strong");
        strong.textContent = name + ": ";
        li.append(strong, document.createTextNode(String(value)));
        details.append(li);
      }
      save.disabled = false;
      renderStatus("Estrutura inspecionada. Refaça composição, exportação e aprovação no Forge.");
    } catch (error) {
      renderStatus("Falha na inspeção: " + (error.message || String(error)));
    } finally {
      check.disabled = false;
    }
  });
  save.addEventListener("click", () => {
    if (lastVerifiedText === null || source.value !== lastVerifiedText || !lastVerifiedMeta) {
      invalidate();
      renderStatus("Conteúdo alterado. Verifique novamente antes de exportar.");
      return;
    }
    const bytes = new Blob([lastVerifiedText], { type: "application/json;charset=utf-8" });
    const url = URL.createObjectURL(bytes);
    try {
      const link = document.createElement("a");
      link.href = url;
      link.download = lastVerifiedMeta.id + "-forge-v1-spec.json";
      link.click();
      renderStatus("JSON exportado. Valide novamente no Forge antes de publicar um pacote.");
    } finally {
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    }
  });
})();
