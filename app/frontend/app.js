const state = {
  view: "all",
  jobs: [],
  bookmarks: [],
  applications: [],
};

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
  };
  return map[value] || value || "미분류";
}

async function fetchJson(url, options = {}) {
  const res = await fetch(url, options);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

async function loadData() {
  const search = document.getElementById("search-input").value.trim();
  const employment = document.getElementById("employment-filter").value;
  const sort = document.getElementById("sort-filter").value;

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
}

function renderStats(total) {
  const stats = document.getElementById("stats");
  stats.innerHTML = `
    <div class="stat">총 <b>${total}</b>건</div>
    <div class="stat">뷰: <b>${document.getElementById("view-title").textContent}</b></div>
  `;
}

function renderEmpty(message) {
  const cards = document.getElementById("cards");
  cards.innerHTML = `<div class="empty">${message}</div>`;
}

function makeJobCard(item) {
  const tpl = document.getElementById("job-card-template");
  const node = tpl.content.cloneNode(true);
  node.querySelector(".title").textContent = item.title;
  node.querySelector(".company").textContent = item.company_name;
  node.querySelector(".badge.role").textContent = item.role_type || "unknown";
  node.querySelector(".badge.employment").textContent = employmentLabel(item.employment_type);
  node.querySelector(".score").textContent = `신입적합도 ${item.new_grad_score ?? 0}`;
  node.querySelector(".posted").textContent = `등록 ${formatDate(item.posted_at)}`;
  node.querySelector(".link").href = item.url || "#";

  node.querySelector(".bookmark-btn").addEventListener("click", async () => {
    try {
      await fetchJson("/api/v1/bookmarks", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ job_id: item.job_id, memo: "대시보드에서 저장" }),
      });
      alert("북마크 저장됨");
    } catch (e) {
      alert(`북마크 실패: ${e.message}`);
    }
  });

  node.querySelector(".apply-btn").addEventListener("click", async () => {
    try {
      await fetchJson(`/api/v1/applications/${item.job_id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: "applied" }),
      });
      alert("지원 상태 업데이트됨");
    } catch (e) {
      alert(`업데이트 실패: ${e.message}`);
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

bindUi();
loadData().catch((e) => renderEmpty(`데이터 조회 실패: ${e.message}`));
