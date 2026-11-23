// Prompt Optimizer UI. Conversation state lives here; the server is stateless.
(() => {
  "use strict";
  const $ = (id) => document.getElementById(id);

  const state = {
    request: "",
    answers: [],          // [{question, answer}]
    pendingQuestion: "",
    current: null,        // latest confirmation {optimized_prompt, version, signature, ...}
    timeline: [],         // [{t, event, detail}]
    result: null,
  };

  // ---------- helpers ----------
  const escapeHtml = (s) =>
    s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
     .replace(/"/g, "&quot;").replace(/'/g, "&#39;");

  function log(event, detail = "") {
    const entry = { t: new Date().toISOString(), event, detail };
    state.timeline.push(entry);
    const li = document.createElement("li");
    li.textContent = `${entry.t.slice(11, 19)} — ${event}${detail ? ": " + detail : ""}`;
    $("timeline").appendChild(li);
  }

  function setStep(step) {
    const order = ["request", "clarify", "confirm", "answer"];
    const idx = order.indexOf(step);
    document.querySelectorAll(".steps li").forEach((li) => {
      const i = order.indexOf(li.dataset.step);
      li.classList.toggle("active", i === idx);
      li.classList.toggle("done", i < idx);
    });
  }

  function show(cardId) {
    ["card-clarify", "card-confirm", "card-answer"].forEach((id) =>
      $(id).classList.toggle("hidden", id !== cardId));
  }

  function status(msg, isError = false) {
    const el = $("status");
    if (!msg) { el.classList.add("hidden"); return; }
    el.textContent = msg;
    el.classList.toggle("error", isError);
    el.classList.remove("hidden");
  }

  function busy(on, label) {
    document.querySelectorAll("button").forEach((b) => (b.disabled = on));
    status(on ? label : "");
  }

  async function post(path, body) {
    const res = await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    let data = {};
    try { data = await res.json(); } catch (_) { /* non-JSON error */ }
    if (!res.ok) throw new Error(data.error || `Request failed (HTTP ${res.status}).`);
    return data;
  }

  function track(name) {
    fetch("/api/event", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name }),
    }).catch(() => {});
  }

  // Minimal, safe Markdown: escape first, then format headings, lists, tables, bold, code.
  function renderMarkdown(md) {
    const lines = escapeHtml(md).split("\n");
    const out = [];
    let i = 0;
    const inline = (s) => s
      .replace(/`([^`]+)`/g, "<code>$1</code>")
      .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
    while (i < lines.length) {
      const line = lines[i];
      if (/^\s*\|.*\|\s*$/.test(line)) {
        const rows = [];
        while (i < lines.length && /^\s*\|.*\|\s*$/.test(lines[i])) rows.push(lines[i++]);
        const cells = (r) => r.trim().replace(/^\||\|$/g, "").split("|").map((c) => inline(c.trim()));
        const isSep = (r) => /^\s*\|?\s*:?-{2,}/.test(r);
        let html = "<table>";
        rows.forEach((r, k) => {
          if (isSep(r)) return;
          const tag = k === 0 && rows[1] && isSep(rows[1]) ? "th" : "td";
          html += "<tr>" + cells(r).map((c) => `<${tag}>${c}</${tag}>`).join("") + "</tr>";
        });
        out.push(html + "</table>");
        continue;
      }
      let m;
      if ((m = line.match(/^(#{1,4})\s+(.*)$/))) {
        const level = Math.min(m[1].length + 2, 6);
        out.push(`<h${level}>${inline(m[2])}</h${level}>`);
      } else if (/^\s*([-*]|\d+\.)\s+/.test(line)) {
        const ordered = /^\s*\d+\./.test(line);
        const items = [];
        while (i < lines.length && /^\s*([-*]|\d+\.)\s+/.test(lines[i])) {
          items.push("<li>" + inline(lines[i].replace(/^\s*([-*]|\d+\.)\s+/, "")) + "</li>");
          i++;
        }
        out.push(`<${ordered ? "ol" : "ul"}>${items.join("")}</${ordered ? "ol" : "ul"}>`);
        continue;
      } else if ((m = line.match(/^&gt;\s?(.*)$/))) {
        out.push(`<blockquote>${inline(m[1])}</blockquote>`);
      } else if (line.trim()) {
        out.push(`<p>${inline(line)}</p>`);
      }
      i++;
    }
    return out.join("\n");
  }

  // ---------- rendering ----------
  function renderClarify(data) {
    state.pendingQuestion = data.question;
    $("clarify-question").textContent = data.question;
    $("clarify-round").textContent = `Question ${data.round} of up to ${data.max_rounds}`;
    const chips = $("clarify-options");
    chips.innerHTML = "";
    (data.options || []).forEach((opt) => {
      const b = document.createElement("button");
      b.className = "chip";
      b.type = "button";
      b.textContent = opt;
      b.addEventListener("click", () => { $("clarify-answer").value = opt; $("clarify-answer").focus(); });
      chips.appendChild(b);
    });
    $("clarify-answer").value = "";
    setStep("clarify");
    show("card-clarify");
    log(`Clarification question ${data.round}`, data.question);
    $("clarify-answer").focus();
  }

  function renderConfirm(data) {
    state.current = data;
    $("confirm-version").textContent = `Prompt version ${data.version}`;
    $("confirm-paraphrase").textContent = data.paraphrase;
    const ul = $("confirm-assumptions");
    ul.innerHTML = "";
    (data.assumptions || []).forEach((a) => {
      const li = document.createElement("li");
      li.textContent = "Assumption: " + a;
      ul.appendChild(li);
    });
    ul.classList.toggle("hidden", !(data.assumptions || []).length);
    $("cmp-original").textContent = state.request;
    $("cmp-optimized").textContent = data.optimized_prompt;
    const t = data.tokens;
    $("tok-original").textContent = `${t.original} tokens`;
    $("tok-optimized").textContent = `${t.optimized} tokens`;
    const diff = t.optimized - t.original;
    const method = t.method === "estimate" ? "character-based estimate (≈4 chars/token)" : `${t.model} tokenizer`;
    $("tok-note").textContent =
      `Input tokens counted with the ${method}. The optimized prompt is ${Math.abs(diff)} tokens ` +
      `${diff >= 0 ? "longer" : "shorter"}; the goal is fewer follow-up requests, not a shorter prompt.`;
    $("revise-box").classList.add("hidden");
    setStep("confirm");
    show("card-confirm");
    log(`Confirmation shown (v${data.version})`, `${t.original} → ${t.optimized} tokens`);
  }

  function renderAnswer(data) {
    state.result = data;
    $("answer").innerHTML = renderMarkdown(data.answer);
    $("answer-version").textContent = `Generated from confirmed prompt v${data.version}`;
    $("answer-truncated").classList.toggle("hidden", !data.truncated);
    setStep("answer");
    show("card-answer");
    log(`Answer generated from v${data.version}`, data.truncated ? "truncated at length limit" : "");
  }

  // ---------- actions ----------
  async function analyze() {
    const text = $("request").value.trim();
    if (text.length < 10) { status("Please describe your request (at least 10 characters).", true); return; }
    if (text !== state.request) { state.request = text; state.answers = []; }
    log("Request submitted", `${text.length} characters`);
    busy(true, "Analyzing your request…");
    try {
      const data = await post("/api/analyze", { request: state.request, answers: state.answers });
      busy(false);
      data.status === "clarify" ? renderClarify(data) : renderConfirm(data);
    } catch (e) { busy(false); status(e.message, true); }
  }

  async function sendAnswer() {
    const answer = $("clarify-answer").value.trim();
    if (!answer) { status("Please answer the question, or pick an option.", true); return; }
    state.answers.push({ question: state.pendingQuestion, answer });
    log("Answer given", answer);
    busy(true, "Updating my understanding…");
    try {
      const data = await post("/api/analyze", { request: state.request, answers: state.answers });
      busy(false);
      data.status === "clarify" ? renderClarify(data) : renderConfirm(data);
    } catch (e) { state.answers.pop(); busy(false); status(e.message, true); }
  }

  async function revise() {
    const feedback = $("revise-feedback").value.trim();
    if (feedback.length < 3) { status("Please say what should change.", true); return; }
    const c = state.current;
    log(`Declined v${c.version}`, feedback);
    busy(true, "Revising the prompt…");
    try {
      const data = await post("/api/revise", {
        request: state.request, answers: state.answers, feedback,
        prompt: c.optimized_prompt, version: c.version, signature: c.signature,
      });
      busy(false);
      $("revise-feedback").value = "";
      renderConfirm(data);
    } catch (e) { busy(false); status(e.message, true); }
  }

  async function generate() {
    const c = state.current; // always the latest confirmed version
    log(`Confirmed v${c.version}`);
    busy(true, "Generating the answer from the confirmed prompt… (this can take a minute)");
    try {
      const data = await post("/api/generate", {
        prompt: c.optimized_prompt, version: c.version, signature: c.signature,
      });
      busy(false);
      renderAnswer(data);
    } catch (e) { busy(false); status(e.message, true); }
  }

  function restart() {
    track("start_over");
    log("Started over");
    Object.assign(state, { request: "", answers: [], pendingQuestion: "", current: null, result: null });
    $("request").value = "";
    $("request-count").textContent = "0 / 4000";
    show(null);
    setStep("request");
    status("");
    $("request").focus();
  }

  function copy(text, what) {
    navigator.clipboard.writeText(text).then(
      () => { status(`${what} copied.`); track(what === "Prompt" ? "copy_prompt" : "copy_answer"); },
      () => status("Could not copy automatically; select the text and copy it.", true));
  }

  function downloadLog() {
    const payload = {
      app: "Prompt Optimizer",
      exported_at: new Date().toISOString(),
      request: state.request,
      clarifications: state.answers,
      confirmed_prompt: state.current && {
        version: state.current.version,
        paraphrase: state.current.paraphrase,
        optimized_prompt: state.current.optimized_prompt,
        tokens: state.current.tokens,
      },
      answer: state.result && {
        version: state.result.version, truncated: !!state.result.truncated, text: state.result.answer },
      timeline: state.timeline,
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `prompt-optimizer-session-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(a.href);
  }

  // ---------- wiring ----------
  $("request").addEventListener("input", (e) => {
    $("request-count").textContent = `${e.target.value.length} / 4000`;
  });
  $("btn-analyze").addEventListener("click", analyze);
  $("btn-answer").addEventListener("click", sendAnswer);
  $("btn-yes").addEventListener("click", generate);
  $("btn-no").addEventListener("click", () => {
    $("revise-box").classList.remove("hidden");
    $("revise-feedback").focus();
  });
  $("btn-cancel-revise").addEventListener("click", () => $("revise-box").classList.add("hidden"));
  $("btn-revise").addEventListener("click", revise);
  $("btn-restart-1").addEventListener("click", restart);
  $("btn-restart-2").addEventListener("click", restart);
  $("btn-copy-prompt").addEventListener("click", () => copy(state.current.optimized_prompt, "Prompt"));
  $("btn-copy-answer").addEventListener("click", () => copy(state.result.answer, "Answer"));
  $("btn-download-log").addEventListener("click", downloadLog);
  $("request").addEventListener("keydown", (e) => {
    if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) analyze();
  });

  // Exposed for manual testing in the browser console.
  window.__promptOptimizer = { state, renderMarkdown };
})();
