document.addEventListener("DOMContentLoaded", () => {
  const selectedAgents = new Set();

  const fileInput = document.getElementById("fileInput");
  const runBtn = document.getElementById("runBtn");
  const statusText = document.getElementById("statusText");

  const summaryCard = document.getElementById("summaryCard");
  const formalCard = document.getElementById("formalCard");
  const semanticCard = document.getElementById("semanticCard");

  const metricsEl = document.getElementById("metrics");
  const downloadsEl = document.getElementById("downloads");
  const formalResultsEl = document.getElementById("formalResults");
  const semanticResultsEl = document.getElementById("semanticResults");

  document.querySelectorAll(".agent-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const agent = btn.dataset.agent;

      if (selectedAgents.has(agent)) {
        selectedAgents.delete(agent);
        btn.classList.remove("active");
      } else {
        selectedAgents.add(agent);
        btn.classList.add("active");
      }

      statusText.textContent = `Выбрано агентов: ${selectedAgents.size}`;
    });
  });

  function statusLabel(status) {
    if (status === "pass") return "Соответствует";
    if (status === "warn") return "Замечание";
    if (status === "fail") return "Требует внимания";
    return status;
  }

  function renderMetrics(summary) {
    metricsEl.innerHTML = `
      <div class="metric"><strong>Соответствует</strong><br>${summary.passed}</div>
      <div class="metric"><strong>Замечания</strong><br>${summary.warned}</div>
      <div class="metric"><strong>Требует внимания</strong><br>${summary.failed}</div>
      <div class="metric"><strong>Всего проверок</strong><br>${summary.total}</div>
    `;
  }

  function renderResults(container, results) {
    container.innerHTML = "";

    if (!results || results.length === 0) {
      container.innerHTML = `<p class="muted">Нет результатов для выбранных агентов.</p>`;
      return;
    }

    results.forEach((item) => {
      const div = document.createElement("div");
      div.className = "result-item";

      let evidenceHtml = "";
      if (item.evidence && item.evidence.length) {
        evidenceHtml = `
          <details>
            <summary>Основания вывода</summary>
            <pre>${item.evidence.slice(0, 5).join("\n")}</pre>
          </details>
        `;
      }

      let recHtml = "";
      if (item.recommendations && item.recommendations.length) {
        recHtml = `
          <details>
            <summary>Рекомендации</summary>
            <pre>${item.recommendations.slice(0, 5).join("\n")}</pre>
          </details>
        `;
      }

      div.innerHTML = `
        <div><span class="status">${statusLabel(item.status)}</span><strong>${item.criterion_name}</strong></div>
        <div style="margin-top:6px;">${item.message}</div>
        <div style="margin-top:8px;">${evidenceHtml}${recHtml}</div>
      `;

      container.appendChild(div);
    });
  }

  runBtn.addEventListener("click", async () => {
    const file = fileInput.files[0];

    if (!file) {
      statusText.textContent = "Сначала выберите файл.";
      return;
    }

    if (selectedAgents.size === 0) {
      statusText.textContent = "Выберите хотя бы один агент.";
      return;
    }

    runBtn.disabled = true;
    statusText.textContent = "Идет анализ...";

    const formData = new FormData();
    formData.append("file", file);
    formData.append("formal", selectedAgents.has("formal") ? "true" : "false");
    formData.append("structure", selectedAgents.has("structure") ? "true" : "false");
    formData.append("semantic", selectedAgents.has("semantic") ? "true" : "false");

    try {
      const response = await fetch("/analyze", {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (!data.ok) {
        statusText.textContent = data.message || "Ошибка анализа.";
        runBtn.disabled = false;
        return;
      }

      statusText.textContent = `Готово. Активные агенты: ${data.enabled_agents.join(", ")}`;

      renderMetrics(data.summary);

      downloadsEl.innerHTML = `
        <a href="${data.downloads.json}" target="_blank">Скачать JSON</a>
        <a href="${data.downloads.pdf}" target="_blank">Скачать PDF</a>
      `;

      renderResults(formalResultsEl, data.formal_results);
      renderResults(semanticResultsEl, data.semantic_results);

      summaryCard.classList.remove("hidden");

      if (data.formal_results && data.formal_results.length > 0) {
        formalCard.classList.remove("hidden");
      } else {
        formalCard.classList.add("hidden");
      }

      if (data.semantic_results && data.semantic_results.length > 0) {
        semanticCard.classList.remove("hidden");
      } else {
        semanticCard.classList.add("hidden");
      }

    } catch (error) {
      console.error(error);
      statusText.textContent = "Ошибка при обращении к серверу.";
    } finally {
      runBtn.disabled = false;
    }
  });
});