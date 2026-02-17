const state = {
  view: "all",
  jobs: [],
  bookmarks: [],
  applications: [],
  apiBase: "",
};

function resolveApiBase() {
  const forced = window.localStorage.getItem("JOBLOG_API_BASE");
  if (forced) return forced.replace(/\/$/, "");

  const { hostname, port, origin } = window.location;

  // If served through reverse proxy on standard ports, use same-origin /api.
  if (!port || port === "80" || port === "443") return origin;

  // Local frontend port direct access fallback.
  if (port === "40000") return `${window.location.protocol}//${hostname}:40001`;

  return origin;
}

function apiPath(path) {
  const normalized = path.startsWith("/") ? path : `/${path}`;
  return `${state.apiBase}${normalized}`;
}

const endpoints = {
  all: () => "/api/v1/jobs",
  today: () => "/api/v1/jobs/today",
  bookmarks: () => "/api/v1/bookmarks",
  applications: () => "/api/v1/applications",
};

function formatDate(iso) {
  if (!iso) return "-";
  return new Date(iso).toLocaleDateString("ko-KR");
}

function employmentLabel(value) {
  const map = {
    intern_convertible: "채용연계형",
    intern_experience: "체험형",
    new_grad: "신입",
    experienced: "경력",
    unknown: "미분류",
    planned: "지원예정",
    applied: "지원완료",
    interview: "면접",
    rejected: "불합격",
    pass: "최종합격",
  };
  return map[value] || value || "미분류";
}

function setError(message = "") {
  const banner = document.getElementById("error-banner");
  if (!message) {
    banner.classList.add("hidden");
    banner.textContent = "";
    return;
  }
  banner.classList.remove("hidden");
  banner.textContent = message;
}

async function fetchJson(path, options = {}) {
  const url = apiPath(path);
  const res = await fetch(url, options);
  if (!res.ok) {
    const msg = await res.text();
    throw new Error(`${res.status} ${res.statusText} (${msg || "no body"})`);
  }
  return res.json();
}

async function loadData() {
  setError("");

  const search = document.getElementById("search-input").value.trim();
  const employment = document.getElementById("employment-filter").value;
  const sort = document.getElementById("sort-filter").value;

  try {
    if (state.view === "all" || state.view === "today") {
      const params = new URLSearchParams();
      if (search) params.set("q", search);
      if (employment) params.set("employment_type", employment);
      params.set("sort", sort);
      const data = await fetchJson(`${endpoints[state.view]()}?${params.toString()}`);
      state.jobs = data.items || [];
      renderJobs(state.jobs);
      renderStats(data.total ?? state.jobs.length);
      return;
    }

    if (state.view === "bookmarks") {
      const data = await fetchJson(endpoints.bookmarks());
      state.bookmarks = data.items || [];
      renderBookmarkCards(state.bookmarks);
      renderStats(data.total ?? state.bookmarks.length);
      return;
    }

    const data = await fetchJson(endpoints.applications());
    state.applications = data.items || [];
    renderApplicationCards(state.applications);
    renderStats(data.total ?? state.applications.length);
  } catch (error) {
    renderEmpty("데이터를 불러오지 못했습니다.");
    setError(`통신 실패: ${error.message} | API BASE: ${state.apiBase}`);
  }
}

function renderStats(total) {
  const stats = document.getElementById("stats");
  stats.innerHTML = `
    <div class="stat"><span>총 건수</span><b>${total}</b></div>
    <div class="stat"><span>현재 뷰</span><b>${document.getElementById("view-title").textContent}</b></div>
    <div class="stat"><span>API 대상</span><b>${state.apiBase}</b></div>
  `;
}

function renderEmpty(message) {
  const cards = document.getElementById("cards");
  cards.innerHTML = `<div class="empty panel">${message}</div>`;
}

function makeJobCard(item) {
  const tpl = document.getElementById("job-card-template");
  const node = tpl.content.cloneNode(true);

  node.querySelector(".title").textContent = item.title || "제목 없음";
  node.querySelector(".company").textContent = item.company_name || "회사 미상";
  node.querySelector(".badge.role").textContent = (item.role_type || "unknown").toUpperCase();
  node.querySelector(".badge.employment").textContent = employmentLabel(item.employment_type);
  node.querySelector(".score").textContent = `신입적합도 ${item.new_grad_score ?? 0}`;
  node.querySelector(".posted").textContent = `등록 ${formatDate(item.posted_at)}`;

  const link = node.querySelector(".link");
  link.href = item.url || "#";
  if (!item.url) {
    link.classList.add("disabled");
    link.textContent = "링크 없음";
  }

  node.querySelector(".bookmark-btn").addEventListener("click", async () => {
    try {
      await fetchJson("/api/v1/bookmarks", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ job_id: item.job_id, memo: "대시보드에서 저장" }),
      });
      setError("✅ 북마크 저장 완료");
      setTimeout(() => setError(""), 1200);
    } catch (e) {
      setError(`북마크 실패: ${e.message}`);
    }
  });

  node.querySelector(".apply-btn").addEventListener("click", async () => {
    try {
      await fetchJson(`/api/v1/applications/${item.job_id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: "applied" }),
      });
      setError("✅ 지원 상태 업데이트 완료");
      setTimeout(() => setError(""), 1200);
    } catch (e) {
      setError(`업데이트 실패: ${e.message}`);
    }
  });

  return node;
}

function renderJobs(items) {
  if (!items.length) return renderEmpty("표시할 공고가 없습니다.");
  const cards = document.getElementById("cards");
  cards.innerHTML = "";
  items.forEach((item) => cards.appendChild(makeJobCard(item)));
}

function renderBookmarkCards(items) {
  if (!items.length) return renderEmpty("북마크가 없습니다.");
  renderJobs(
    items.map((x) => ({
      ...x,
      employment_type: "unknown",
      role_type: "backend",
      new_grad_score: 0,
      posted_at: x.created_at,
    }))
  );
}

function renderApplicationCards(items) {
  if (!items.length) return renderEmpty("지원 현황이 없습니다.");
  renderJobs(
    items.map((x) => ({
      ...x,
      employment_type: x.status,
      role_type: "backend",
      new_grad_score: 0,
      posted_at: x.updated_at,
    }))
  );
}

function bindUi() {
  document.querySelectorAll(".nav-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      document.querySelectorAll(".nav-btn").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      state.view = btn.dataset.view;
      document.getElementById("view-title").textContent = btn.textContent;
      await loadData();
    });
  });

  document.getElementById("refresh-btn").addEventListener("click", loadData);
  document.getElementById("search-input").addEventListener("keydown", (e) => {
    if (e.key === "Enter") loadData();
  });
  document.getElementById("employment-filter").addEventListener("change", loadData);
  document.getElementById("sort-filter").addEventListener("change", loadData);
}

function init() {
  state.apiBase = resolveApiBase();
  document.getElementById("api-base").textContent = state.apiBase;
  bindUi();
  loadData();
}

init();
