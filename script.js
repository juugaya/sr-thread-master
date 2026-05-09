const GAS_URL = "YOUR_GAS_URL_HERE";

let latestComments = [];
let checklist = {};
let threads = [];
let activeTab = "ALL";

// -----------------------------
// GAS からデータ取得（高速版）
// -----------------------------
function load() {
  fetch(GAS_URL)
    .then(r => r.json())
    .then(json => {
      const newComments = json.comments;

      // 新着コメント検出
      const oldLen = latestComments.length;
      const newLen = newComments.length;

      latestComments = newComments;
      checklist = groupChecklist(json.checklist);

      // タブと画面を更新
      renderTabs();
      renderWindows();

      // 新着コメントがあれば強調
      if (newLen > oldLen) {
        highlightNewComment(newComments[newLen - 1].timestamp);
      }
    });
}

// -----------------------------
// チェックリストを thread ごとに整理
// -----------------------------
function groupChecklist(list) {
  const out = {};
  list.forEach(c => {
    if (!out[c.thread]) out[c.thread] = [];
    out[c.thread].push(c);
  });
  return out;
}

// -----------------------------
// タブ描画
// -----------------------------
function renderTabs() {
  const tabArea = document.getElementById("tabs");
  const uniqueThreads = [...new Set(latestComments.map(c => c.thread || "general"))];

  threads = ["ALL", ...uniqueThreads, ...Object.keys(checklist).map(t => "TODO-" + t), "DONE"];

  tabArea.innerHTML = threads
    .map(t => `<button class="tab ${t === activeTab ? "active" : ""}" onclick="switchTab('${t}')">${t}</button>`)
    .join("");
}

// -----------------------------
// タブ切り替え
// -----------------------------
function switchTab(t) {
  activeTab = t;
  renderWindows();
}

// -----------------------------
// コメント & タスク描画
// -----------------------------
function renderWindows() {
  const area = document.getElementById("main");
  let html = "";

  if (activeTab === "ALL") {
    html = latestComments.map(c => commentHTML(c)).join("");
  } else if (activeTab.startsWith("TODO-")) {
    const thread = activeTab.replace("TODO-", "");
    const list = checklist[thread] || [];
    html = list.map(c => checklistHTML(c, thread)).join("");
  } else if (activeTab === "DONE") {
    html = latestComments
      .filter(c => c.status === "完了")
      .map(c => commentHTML(c))
      .join("");
  } else {
    html = latestComments
      .filter(c => c.thread === activeTab)
      .map(c => commentHTML(c))
      .join("");
  }

  area.innerHTML = html;
}

// -----------------------------
// コメント HTML
// -----------------------------
function commentHTML(c) {
  return `
    <div class="comment" id="c-${c.timestamp}">
      <b>${c.user}</b>: ${c.comment}
      <button onclick="addToChecklist('${c.thread}', '${c.timestamp}', '${c.user}', '${c.comment.replace(/'/g, "\\'")}')">＋</button>
      <button onclick="jumpToTask('${c.timestamp}')">📝</button>
    </div>
    <div class="comment">
      <span class="room-tag">${c.room}</span>
      <b>${c.user}</b>: ${c.comment}
    </div>
  `;
}

// -----------------------------
// チェックリスト HTML
// -----------------------------
function checklistHTML(c, thread) {
  return `
    <div class="task" data-timestamp="${c.timestamp}">
      <input type="checkbox" ${c.done ? "checked" : ""} onclick="toggleChecklist('${thread}', ${c.timestamp})">
      <b>${c.user}</b>: ${c.comment}
      <select onchange="changePriority('${c.timestamp}', this.value)">
        <option value="high" ${c.priority === "high" ? "selected" : ""}>高</option>
        <option value="medium" ${c.priority === "medium" ? "selected" : ""}>中</option>
        <option value="low" ${c.priority === "low" ? "selected" : ""}>低</option>
      </select>
      <button onclick="jumpToComment('${c.timestamp}', '${thread}')">💬</button>
    </div>
  `;
}

// -----------------------------
// 新着コメント強調
// -----------------------------
function highlightNewComment(ts) {
  const el = document.getElementById(`c-${ts}`);
  if (!el) return;
  el.style.background = "#fffa9e";
  setTimeout(() => (el.style.background = ""), 1200);
}

// -----------------------------
// コメント → タスクへジャンプ
// -----------------------------
function jumpToTask(timestamp) {
  let targetThread = null;

  Object.keys(checklist).forEach(t => {
    if (checklist[t].some(c => c.timestamp == timestamp)) {
      targetThread = t;
    }
  });

  if (!targetThread) return alert("タスクがありません");

  switchTab("TODO-" + targetThread);

  setTimeout(() => {
    const el = document.querySelector(`[data-timestamp="${timestamp}"]`);
    if (el) el.scrollIntoView({ behavior: "smooth", block: "center" });
  }, 200);
}

// -----------------------------
// タスク → コメントへジャンプ
// -----------------------------
function jumpToComment(timestamp, thread) {
  switchTab(thread);

  setTimeout(() => {
    const el = document.getElementById(`c-${timestamp}`);
    if (el) el.scrollIntoView({ behavior: "smooth", block: "center" });
  }, 200);
}

// -----------------------------
// チェックリスト操作
// -----------------------------
function addToChecklist(thread, timestamp, user, comment) {
  fetch(GAS_URL, {
    method: "POST",
    body: JSON.stringify({
      mode: "add_check",
      thread,
      timestamp,
      user,
      comment,
      order: checklist[thread]?.length || 0,
      priority: "medium"
    })
  }).then(load);
}

function toggleChecklist(thread, timestamp) {
  fetch(GAS_URL, {
    method: "POST",
    body: JSON.stringify({
      mode: "toggle_check",
      timestamp
    })
  }).then(load);
}

function changePriority(timestamp, priority) {
  fetch(GAS_URL, {
    method: "POST",
    body: JSON.stringify({
      mode: "priority",
      timestamp,
      priority
    })
  }).then(load);
}

// -----------------------------
// 自動更新（高速）
// -----------------------------
setInterval(load, 1500);
load();
