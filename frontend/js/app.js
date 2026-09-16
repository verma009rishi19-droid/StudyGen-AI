/**
 * StudyGen AI - Main Application Logic & View Controller
 */

document.addEventListener("DOMContentLoaded", async () => {
  await initApp();
});

async function initApp() {
  try {
    const status = await api.generation.status();
    appState.setAIStatus(status);
    updateAIStatusBadge(status);
  } catch (err) {
    console.warn("Could not check AI status:", err);
  }

  try {
    if (api.token) {
      const user = await api.auth.me();
      appState.setUser(user);
    }
  } catch (err) {
    api.setToken(null);
    appState.setUser(null);
  }

  updateAuthUI();
  setupEventListeners();

  if (appState.user) {
    await navigateTo("dashboard");
  } else {
    navigateTo("landing");
  }
}

function updateAIStatusBadge(status) {
  const dot = document.getElementById("aiStatusDot");
  const text = document.getElementById("aiStatusText");
  if (!status || !text) return;

  const provider = status.active_provider.toUpperCase();
  let model = status.gemini_model || "gemini-2.5-flash";
  if (status.active_provider === "openai") {
    model = status.openai_model;
  } else if (status.active_provider === "ollama") {
    model = status.ollama_model;
  }
  text.textContent = `AI: ${provider} (${model})`;
  if (dot) dot.style.backgroundColor = "var(--success)";
}

function updateAuthUI() {
  const user = appState.user;
  const userSection = document.getElementById("userNavSection");
  if (!userSection) return;

  if (user) {
    userSection.innerHTML = `
      <div style="display: flex; align-items: center; gap: 12px;">
        <span style="font-size: 0.9rem; color: var(--text-secondary);">👤 ${escapeHtml(user.name)}</span>
        <button class="btn btn-secondary btn-sm" id="logoutBtn">Log out</button>
      </div>
    `;
    document.getElementById("logoutBtn")?.addEventListener("click", handleLogout);
  } else {
    userSection.innerHTML = `
      <button class="btn btn-secondary btn-sm" id="openLoginBtn">Log in</button>
      <button class="btn btn-primary btn-sm" id="openRegisterBtn">Sign up</button>
    `;
    document.getElementById("openLoginBtn")?.addEventListener("click", () => Modal.open("loginModal"));
    document.getElementById("openRegisterBtn")?.addEventListener("click", () => Modal.open("registerModal"));
  }
}

function handleLogout() {
  api.setToken(null);
  appState.setUser(null);
  updateAuthUI();
  Toast.info("Logged out successfully.");
  navigateTo("landing");
}

async function navigateTo(viewName, params = {}) {
  appState.setView(viewName);
  document.querySelectorAll(".view-section").forEach(sec => sec.style.display = "none");

  const activeSec = document.getElementById(`view-${viewName}`);
  if (activeSec) {
    activeSec.style.display = "block";
  }

  if (viewName === "dashboard") {
    await loadDashboardData();
  } else if (viewName === "project" && params.projectId) {
    await loadProjectData(params.projectId);
  }
}
let dashboardFilterState = {
  search: "",
  subject: "",
  sort: "newest"
};

async function loadDashboardData() {
  try {
    const projects = await api.projects.list();
    appState.setProjects(projects);
    updateDashboardStats(projects);
    updateSubjectFilterOptions(projects);
    applyDashboardFiltersAndRender();
  } catch (err) {
    Toast.error(`Could not load projects: ${err.message}`);
  }
}

function updateDashboardStats(projects) {
  let totalDocs = 0;
  let totalPapers = 0;

  projects.forEach(p => {
    totalDocs += p.document_count || 0;
    totalPapers += p.question_paper_count || 0;
  });

  const pEl = document.getElementById("statTotalProjects");
  const dEl = document.getElementById("statTotalDocs");
  const qEl = document.getElementById("statTotalPapers");
  const qzEl = document.getElementById("statTotalQuizzes");
  if (pEl) pEl.textContent = projects.length;
  if (dEl) dEl.textContent = totalDocs;
  if (qEl) qEl.textContent = totalPapers;
  if (qzEl) qzEl.textContent = totalPapers;
}

function updateSubjectFilterOptions(projects) {
  const sel = document.getElementById("dashboardSubjectFilter");
  if (!sel) return;

  const subjects = Array.from(new Set(projects.map(p => p.subject).filter(Boolean))).sort();
  const currentVal = dashboardFilterState.subject;

  sel.innerHTML = `<option value="">All Subjects (${projects.length})</option>` +
    subjects.map(s => `<option value="${escapeHtml(s)}" ${s === currentVal ? "selected" : ""}>${escapeHtml(s)}</option>`).join("");
}

function applyDashboardFiltersAndRender() {
  const allProjects = appState.projects || [];
  const q = (dashboardFilterState.search || "").toLowerCase();
  const sub = dashboardFilterState.subject;
  const sort = dashboardFilterState.sort || "newest";

  let filtered = allProjects.filter(p => {
    const matchSearch = !q ||
      (p.name && p.name.toLowerCase().includes(q)) ||
      (p.subject && p.subject.toLowerCase().includes(q)) ||
      (p.description && p.description.toLowerCase().includes(q));

    const matchSubject = !sub || p.subject === sub;
    return matchSearch && matchSubject;
  });

  // Sorting
  filtered.sort((a, b) => {
    if (sort === "newest") return new Date(b.created_at) - new Date(a.created_at);
    if (sort === "oldest") return new Date(a.created_at) - new Date(b.created_at);
    if (sort === "name") return (a.name || "").localeCompare(b.name || "");
    if (sort === "papers") return (b.question_paper_count || 0) - (a.question_paper_count || 0);
    if (sort === "docs") return (b.document_count || 0) - (a.document_count || 0);
    return 0;
  });

  const countEl = document.getElementById("dashboardFilterCount");
  if (countEl) {
    if (q || sub) {
      countEl.style.display = "block";
      countEl.textContent = `Showing ${filtered.length} of ${allProjects.length} projects matching filters.`;
    } else {
      countEl.style.display = "none";
    }
  }

  renderProjectsGrid(filtered);
}

function renderProjectsGrid(projects) {
  const container = document.getElementById("projectsContainer");
  if (!container) return;

  if (!projects || projects.length === 0) {
    const isFiltered = Boolean(dashboardFilterState.search || dashboardFilterState.subject);
    container.innerHTML = `
      <div style="grid-column: 1 / -1; text-align: center; padding: 48px 20px; background: var(--bg-surface); border: 1px dashed var(--border-medium); border-radius: var(--radius-lg);">
        <p style="font-size: 1.1rem; color: var(--text-secondary); margin-bottom: 16px;">
          ${isFiltered ? "No study projects match your current search or filters." : "No study projects yet."}
        </p>
        ${isFiltered ? `
          <button class="btn btn-secondary" onclick="document.getElementById('dashboardClearFiltersBtn').click()">Reset Filters</button>
        ` : `
          <button class="btn btn-primary" onclick="Modal.open('newProjectModal')">+ Create Your First Project</button>
        `}
      </div>
    `;
    return;
  }

  container.innerHTML = projects.map(p => `
    <div class="project-card" data-project-id="${p.id}">
      <div>
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
          <span class="project-badge">${escapeHtml(p.subject)}</span>
          <span style="font-size: 0.75rem; color: var(--text-muted);">${Utils.formatDate(p.created_at)}</span>
        </div>
        <h3 class="project-title">${escapeHtml(p.name)}</h3>
        <p class="project-desc">${escapeHtml(p.description || "No description provided.")}</p>
      </div>

      <div>
        <div class="project-footer">
          <span>📄 ${p.document_count || 0} Docs • 📝 ${p.question_paper_count || 0} Papers</span>
        </div>
        <div class="project-card-actions">
          <button class="btn btn-primary btn-sm open-workspace-btn" data-project-id="${p.id}" style="flex: 1;">Open Workspace →</button>
          ${(p.question_paper_count || 0) > 0 ? `
            <button class="btn btn-secondary btn-sm quick-quiz-btn" data-project-id="${p.id}" title="Launch practice quiz immediately">⚡ Quiz</button>
          ` : ''}
          <button class="btn btn-danger btn-sm delete-proj-btn" data-project-id="${p.id}" data-project-name="${escapeHtml(p.name)}" title="Delete project">🗑️</button>
        </div>
      </div>
    </div>
  `).join("");

  // Event handlers for project card actions
  container.querySelectorAll(".open-workspace-btn").forEach(btn => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      const pid = btn.getAttribute("data-project-id");
      navigateTo("project", { projectId: pid });
    });
  });

  container.querySelectorAll(".quick-quiz-btn").forEach(btn => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      const pid = btn.getAttribute("data-project-id");
      startQuickQuizForProject(pid);
    });
  });

  container.querySelectorAll(".delete-proj-btn").forEach(btn => {
    btn.addEventListener("click", async (e) => {
      e.stopPropagation();
      const pid = btn.getAttribute("data-project-id");
      const pname = btn.getAttribute("data-project-name");
      if (!confirm(`Are you sure you want to delete "${pname}" and all its study documents?`)) return;
      try {
        await api.projects.delete(pid);
        Toast.success(`Project "${pname}" deleted.`);
        await loadDashboardData();
      } catch (err) {
        Toast.error(`Delete failed: ${err.message}`);
      }
    });
  });

  // Clicking card background opens project
  container.querySelectorAll(".project-card").forEach(card => {
    card.addEventListener("click", () => {
      const pid = card.getAttribute("data-project-id");
      navigateTo("project", { projectId: pid });
    });
  });
}

async function startQuickQuizForProject(projectId) {
  try {
    AILoader.show(["Loading practice quiz...", "Preparing questions & options..."]);
    const papers = await api.questionPapers.list(projectId);
    if (!papers || papers.length === 0) {
      AILoader.hide();
      Toast.warning("No question papers generated in this project yet.");
      navigateTo("project", { projectId });
      return;
    }
    const paper = await api.questionPapers.get(papers[0].id);
    AILoader.hide();
    appState.startQuiz(paper);
    renderCurrentQuizQuestion();
  } catch (err) {
    AILoader.hide();
    Toast.error(`Could not start quiz: ${err.message}`);
  }
}

async function loadProjectData(projectId) {
  try {
    const project = await api.projects.get(projectId);
    appState.setActiveProject(project);

    document.getElementById("projectTitleHeader").textContent = project.name;
    document.getElementById("projectSubjectHeader").textContent = project.subject;
    document.getElementById("projectDescHeader").textContent = project.description || "";

    const docs = await api.documents.list(projectId);
    appState.setProjectDocuments(docs);
    renderDocumentsList(docs);

    switchProjectTab("material");

    if (docs.length > 0) {
      loadDocumentSummary(docs[0].id);
      loadDocumentTopics(docs[0].id);
    }
    loadProjectQuestionPapers(projectId);
    loadProjectHistory(projectId);
  } catch (err) {
    Toast.error(`Failed to load project: ${err.message}`);
    navigateTo("dashboard");
  }
}

function switchProjectTab(tabId) {
  appState.setActiveTab(tabId);
  document.querySelectorAll(".tab-btn").forEach(btn => {
    btn.classList.toggle("active", btn.getAttribute("data-tab") === tabId);
  });
  document.querySelectorAll(".tab-pane").forEach(pane => {
    pane.classList.toggle("active", pane.id === `tab-${tabId}`);
  });
}

function renderDocumentsList(docs) {
  const container = document.getElementById("documentsListContainer");
  const selector = document.getElementById("summaryDocSelector");
  const topicSelector = document.getElementById("topicsDocSelector");

  if (!container) return;

  if (docs.length === 0) {
    container.innerHTML = `<p style="color: var(--text-muted); font-size: 0.9rem;">No study materials added yet.</p>`;
    if (selector) selector.innerHTML = `<option value="">No documents available</option>`;
    if (topicSelector) topicSelector.innerHTML = `<option value="">No documents available</option>`;
    return;
  }

  const optionsHtml = docs.map(d => `<option value="${d.id}">${escapeHtml(d.filename)} (${d.char_count.toLocaleString()} chars)</option>`).join("");
  if (selector) selector.innerHTML = optionsHtml;
  if (topicSelector) topicSelector.innerHTML = optionsHtml;

  container.innerHTML = docs.map(d => {
    const isPdf = (d.file_type && d.file_type.includes("pdf")) || d.filename.toLowerCase().endsWith(".pdf");
    const badgeClass = isPdf ? "badge-pdf" : "badge-txt";
    const badgeText = isPdf ? "📕 PDF" : "📄 TXT";

    return `
      <div style="display: flex; justify-content: space-between; align-items: center; padding: 14px 16px; background: var(--bg-surface-elevated); border: 1px solid var(--border-subtle); border-radius: var(--radius-sm); margin-bottom: 8px;">
        <div>
          <div style="display: flex; align-items: center; gap: 8px; font-weight: 600;">
            <span class="file-type-badge ${badgeClass}">${badgeText}</span>
            <span>${escapeHtml(d.filename)}</span>
          </div>
          <div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 4px;">
            ${d.char_count.toLocaleString()} characters extracted • Added ${Utils.formatDate(d.created_at)}
          </div>
        </div>
        <div style="display: flex; gap: 8px;">
          <button class="btn btn-secondary btn-sm" onclick="triggerQuickSummary(${d.id})">Summarize</button>
          <button class="btn btn-secondary btn-sm" onclick="triggerQuickTopics(${d.id})">Topics</button>
          <button class="btn btn-danger btn-sm" onclick="deleteDocument(${d.id})">Delete</button>
        </div>
      </div>
    `;
  }).join("");
}

async function handleAddPastedText() {
  const textInput = document.getElementById("pastedMaterialInput");
  const titleInput = document.getElementById("pastedMaterialTitle");
  const content = textInput.value.trim();
  const filename = titleInput.value.trim() || "Pasted Lecture Notes.txt";

  if (content.length < 10) {
    Toast.warning("Please paste at least 10 characters of study material.");
    return;
  }

  try {
    await api.documents.create({
      project_id: appState.activeProject.id,
      filename,
      content
    });
    textInput.value = "";
    titleInput.value = "";
    document.getElementById("pasteCharCounter").textContent = "0 characters";
    Toast.success("Study material added successfully!");

    const docs = await api.documents.list(appState.activeProject.id);
    appState.setProjectDocuments(docs);
    renderDocumentsList(docs);
  } catch (err) {
    Toast.error(`Failed to add material: ${err.message}`);
  }
}

async function handleFileUpload(file) {
  if (!file) return;

  const validExtensions = [".pdf", ".txt", ".md"];
  const lowerName = file.name.toLowerCase();
  const isValid = validExtensions.some(ext => lowerName.endsWith(ext));

  if (!isValid) {
    Toast.error("Please upload a .pdf, .txt, or .md file.");
    return;
  }

  const isPdf = lowerName.endsWith(".pdf");

  try {
    AILoader.show([
      `Uploading ${file.name}...`,
      isPdf ? "Parsing and extracting text from PDF pages..." : "Processing text document...",
      "Indexing into project study materials..."
    ]);
    await api.documents.upload(appState.activeProject.id, file);
    AILoader.hide();
    Toast.success(`Uploaded and extracted ${file.name} successfully!`);

    const docs = await api.documents.list(appState.activeProject.id);
    appState.setProjectDocuments(docs);
    renderDocumentsList(docs);
  } catch (err) {
    AILoader.hide();
    Toast.error(`Upload failed: ${err.message}`);
  }
}

async function deleteDocument(docId) {
  if (!confirm("Are you sure you want to delete this study document?")) return;
  try {
    await api.documents.delete(docId);
    Toast.success("Document deleted.");
    const docs = await api.documents.list(appState.activeProject.id);
    appState.setProjectDocuments(docs);
    renderDocumentsList(docs);
  } catch (err) {
    Toast.error(`Delete failed: ${err.message}`);
  }
}

window.triggerQuickSummary = (docId) => {
  switchProjectTab("summary");
  const sel = document.getElementById("summaryDocSelector");
  if (sel) sel.value = docId;
  triggerGenerateSummary();
};

window.triggerQuickTopics = (docId) => {
  switchProjectTab("topics");
  const sel = document.getElementById("topicsDocSelector");
  if (sel) sel.value = docId;
  triggerGenerateTopics();
};
async function triggerGenerateSummary() {
  const sel = document.getElementById("summaryDocSelector");
  const docId = sel ? parseInt(sel.value) : null;
  if (!docId) {
    Toast.warning("Please select a study document first.");
    return;
  }

  try {
    AILoader.show([
      "Analyzing study material...",
      "Extracting core concepts...",
      "Structuring executive summary...",
      "Compiling quick revision notes..."
    ]);

    const summary = await api.summaries.generate(docId);
    AILoader.hide();
    renderSummary(summary);
    Toast.success("AI Summary generated!");
    loadProjectHistory(appState.activeProject.id);
  } catch (err) {
    AILoader.hide();
    Toast.error(`Summary generation error: ${err.message}`);
  }
}

async function loadDocumentSummary(docId) {
  try {
    const summary = await api.summaries.getByDoc(docId);
    renderSummary(summary);
  } catch (err) {
    renderSummary(null);
  }
}

function renderSummary(summary) {
  const container = document.getElementById("summaryContentContainer");
  if (!container) return;

  if (!summary) {
    container.innerHTML = `
      <div style="text-align: center; padding: 48px 20px; color: var(--text-muted);">
        <div style="font-size: 2.5rem; margin-bottom: 12px;">📑</div>
        <p style="font-size: 1.05rem; margin-bottom: 16px;">No summary generated for this document yet.</p>
        <p style="font-size: 0.9rem;">Select a document above and click "Generate AI Summary".</p>
      </div>
    `;
    return;
  }

  container.innerHTML = `
    <div style="display: flex; flex-direction: column; gap: 24px;">
      <div style="background: var(--bg-surface-elevated); border: 1px solid var(--border-subtle); border-radius: var(--radius-md); padding: 24px;">
        <h3 style="font-size: 1.15rem; margin-bottom: 12px; color: var(--primary-light);">Executive Overview</h3>
        <p style="line-height: 1.7; color: var(--text-primary); font-size: 1rem;">${escapeHtml(summary.summary)}</p>
      </div>

      <div style="background: var(--bg-surface-elevated); border: 1px solid var(--border-subtle); border-radius: var(--radius-md); padding: 24px;">
        <h3 style="font-size: 1.15rem; margin-bottom: 14px; color: var(--primary-light);">Key Concepts</h3>
        <div style="display: flex; flex-wrap: wrap; gap: 8px;">
          ${(summary.key_concepts || []).map(c => `
            <span style="background: var(--primary-glow); border: 1px solid rgba(99, 102, 241, 0.4); color: var(--primary-light); padding: 6px 14px; border-radius: var(--radius-full); font-size: 0.85rem; font-weight: 600;">
              ${escapeHtml(c)}
            </span>
          `).join("")}
        </div>
      </div>

      <div style="background: var(--bg-surface-elevated); border: 1px solid var(--border-subtle); border-radius: var(--radius-md); padding: 24px;">
        <h3 style="font-size: 1.15rem; margin-bottom: 14px; color: var(--primary-light);">Important Exam Topics</h3>
        <ul style="padding-left: 20px; display: flex; flex-direction: column; gap: 8px; color: var(--text-secondary);">
          ${(summary.important_topics || []).map(t => `<li style="line-height: 1.5;">${escapeHtml(t)}</li>`).join("")}
        </ul>
      </div>

      <div style="background: var(--bg-surface-elevated); border: 1px solid var(--border-subtle); border-radius: var(--radius-md); padding: 24px;">
        <h3 style="font-size: 1.15rem; margin-bottom: 14px; color: var(--accent);">⚡ Quick Revision Points</h3>
        <div style="display: flex; flex-direction: column; gap: 10px;">
          ${(summary.quick_revision || []).map((pt, idx) => `
            <div style="display: flex; gap: 12px; align-items: flex-start;">
              <span style="color: var(--accent); font-weight: 700;">${idx + 1}.</span>
              <span style="color: var(--text-primary);">${escapeHtml(pt)}</span>
            </div>
          `).join("")}
        </div>
      </div>
    </div>
  `;
}

async function triggerGenerateTopics() {
  const sel = document.getElementById("topicsDocSelector");
  const docId = sel ? parseInt(sel.value) : null;
  if (!docId) {
    Toast.warning("Please select a study document first.");
    return;
  }

  try {
    AILoader.show([
      "Analyzing document for exam patterns...",
      "Extracting critical topics...",
      "Synthesizing detailed topic explanations...",
      "Ranking topic relevance..."
    ]);

    const topics = await api.topics.generate(docId);
    AILoader.hide();
    renderTopics(topics);
    Toast.success("Important topics extracted!");
    loadProjectHistory(appState.activeProject.id);
  } catch (err) {
    AILoader.hide();
    Toast.error(`Topics generation failed: ${err.message}`);
  }
}

async function loadDocumentTopics(docId) {
  try {
    const topics = await api.topics.getByDoc(docId);
    renderTopics(topics);
  } catch (err) {
    renderTopics([]);
  }
}

function renderTopics(topics) {
  const container = document.getElementById("topicsGridContainer");
  if (!container) return;

  if (!topics || topics.length === 0) {
    container.innerHTML = `
      <div style="grid-column: 1 / -1; text-align: center; padding: 48px 20px; color: var(--text-muted);">
        <div style="font-size: 2.5rem; margin-bottom: 12px;">💡</div>
        <p style="font-size: 1.05rem; margin-bottom: 8px;">No important topics extracted yet.</p>
        <p style="font-size: 0.9rem;">Select a document and click "Extract Important Topics".</p>
      </div>
    `;
    return;
  }

  container.innerHTML = topics.map(t => {
    const impClass = t.importance === "Critical" ? "importance-critical" : (t.importance === "High" ? "importance-high" : "importance-medium");
    return `
      <div class="topic-card">
        <div class="topic-header">
          <h4 class="topic-title">${escapeHtml(t.topic)}</h4>
          <span class="importance-pill ${impClass}">${escapeHtml(t.importance)}</span>
        </div>
        <p style="color: var(--text-secondary); font-size: 0.95rem; line-height: 1.5; flex: 1;">${escapeHtml(t.explanation)}</p>
        <div class="concept-tags">
          ${(t.related_concepts || []).map(rc => `<span class="concept-tag">${escapeHtml(rc)}</span>`).join("")}
        </div>
      </div>
    `;
  }).join("");
}

async function loadProjectQuestionPapers(projectId) {
  try {
    const papers = await api.questionPapers.list(projectId);
    renderQuestionPapers(papers);
  } catch (err) {
    console.error("Failed to load question papers:", err);
  }
}

function renderQuestionPapers(papers) {
  const container = document.getElementById("questionPapersContainer");
  if (!container) return;

  if (!papers || papers.length === 0) {
    container.innerHTML = `
      <div style="text-align: center; padding: 48px 20px; color: var(--text-muted); background: var(--bg-surface); border-radius: var(--radius-md);">
        <div style="font-size: 2.5rem; margin-bottom: 12px;">📝</div>
        <p style="font-size: 1.05rem; margin-bottom: 16px;">No question papers generated yet.</p>
        <button class="btn btn-primary" onclick="Modal.open('generatePaperModal')">+ Generate Question Paper</button>
      </div>
    `;
    return;
  }

  container.innerHTML = papers.map(p => `
    <div style="background: var(--bg-surface); border: 1px solid var(--border-subtle); border-radius: var(--radius-md); padding: 24px; margin-bottom: 20px;">
      <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 12px; margin-bottom: 16px;">
        <div>
          <h3 style="font-size: 1.25rem; font-weight: 700; margin-bottom: 6px;">${escapeHtml(p.title)}</h3>
          <div style="display: flex; gap: 10px; font-size: 0.85rem; color: var(--text-secondary);">
            <span>📊 Total Marks: <strong>${p.total_marks}</strong></span>
            <span>⏱ Duration: <strong>${p.duration} mins</strong></span>
            <span>🎯 Difficulty: <strong>${p.difficulty}</strong></span>
            <span>📋 Type: <strong>${p.question_type}</strong></span>
          </div>
        </div>
        <div style="display: flex; gap: 10px;">
          <button class="btn btn-primary btn-sm" onclick="startQuizMode(${p.id})">🚀 Interactive Quiz</button>
          <button class="btn btn-secondary btn-sm" onclick="togglePaperQuestions(${p.id})">View Questions (${(p.questions || []).length})</button>
          <button class="btn btn-danger btn-sm" onclick="deleteQuestionPaper(${p.id})">Delete</button>
        </div>
      </div>

      <div id="paper-questions-${p.id}" style="display: none; border-top: 1px solid var(--border-subtle); padding-top: 18px; margin-top: 16px;">
        ${(p.questions || []).map((q, idx) => `
          <div style="margin-bottom: 18px; padding-bottom: 14px; border-bottom: 1px solid var(--border-subtle);">
            <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
              <span style="font-weight: 700; color: var(--primary-light);">Q${idx + 1}. [${q.question_type}]</span>
              <span style="font-size: 0.85rem; color: var(--text-muted);">${q.marks} Mark${q.marks > 1 ? 's' : ''}</span>
            </div>
            <p style="font-size: 1rem; color: var(--text-primary); margin-bottom: 8px;">${escapeHtml(q.question_text)}</p>
            ${q.options && q.options.length > 0 ? `
              <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 10px;">
                ${q.options.map(opt => `<div style="background: var(--bg-input); padding: 8px 12px; border-radius: var(--radius-sm); font-size: 0.9rem;">${escapeHtml(opt)}</div>`).join("")}
              </div>
            ` : ''}
            <div style="font-size: 0.85rem; color: var(--success); font-weight: 600;">Answer: ${escapeHtml(q.correct_answer)}</div>
            ${q.explanation ? `<div style="font-size: 0.85rem; color: var(--text-muted); margin-top: 4px;">Explanation: ${escapeHtml(q.explanation)}</div>` : ''}
          </div>
        `).join("")}
      </div>
    </div>
  `).join("");
}

window.togglePaperQuestions = (paperId) => {
  const el = document.getElementById(`paper-questions-${paperId}`);
  if (el) {
    el.style.display = el.style.display === "none" ? "block" : "none";
  }
};

async function handleGeneratePaperSubmit() {
  const title = document.getElementById("qpTitleInput").value.trim();
  const numQuestions = parseInt(document.getElementById("qpNumQuestionsInput").value);
  const totalMarks = parseInt(document.getElementById("qpTotalMarksInput").value);
  const difficulty = document.getElementById("qpDifficultyInput").value;
  const questionType = document.getElementById("qpTypeInput").value;
  const duration = parseInt(document.getElementById("qpDurationInput").value);

  Modal.close("generatePaperModal");

  try {
    AILoader.show([
      "Reviewing project study documents...",
      "Formulating questions according to marks & difficulty...",
      "Generating multiple choice options & rubrics...",
      "Attaching grounded explanations..."
    ]);

    await api.questionPapers.generate({
      project_id: appState.activeProject.id,
      title: title || `${appState.activeProject.name} Exam Paper`,
      num_questions: numQuestions,
      total_marks: totalMarks,
      difficulty,
      question_type: questionType,
      duration
    });

    AILoader.hide();
    Toast.success("Question paper generated!");
    loadProjectQuestionPapers(appState.activeProject.id);
    loadProjectHistory(appState.activeProject.id);
  } catch (err) {
    AILoader.hide();
    Toast.error(`Generation failed: ${err.message}`);
  }
}

async function deleteQuestionPaper(paperId) {
  if (!confirm("Are you sure you want to delete this question paper?")) return;
  try {
    await api.questionPapers.delete(paperId);
    Toast.success("Question paper deleted.");
    loadProjectQuestionPapers(appState.activeProject.id);
  } catch (err) {
    Toast.error(`Delete failed: ${err.message}`);
  }
}
window.startQuizMode = async (paperId) => {
  try {
    AILoader.show(["Preparing interactive quiz...", "Loading question data..."]);
    const paper = await api.questionPapers.get(paperId);
    AILoader.hide();

    if (!paper.questions || paper.questions.length === 0) {
      Toast.warning("This paper has no questions to quiz.");
      return;
    }

    appState.startQuiz(paper);
    renderCurrentQuizQuestion();
  } catch (err) {
    AILoader.hide();
    Toast.error(`Could not start quiz: ${err.message}`);
  }
};

function renderCurrentQuizQuestion() {
  const quiz = appState.activeQuiz;
  if (!quiz) return;

  const total = quiz.paper.questions.length;
  const currentIdx = quiz.currentIndex;
  const q = quiz.paper.questions[currentIdx];

  document.getElementById("quizHeaderTitle").textContent = quiz.paper.title;
  document.getElementById("quizStepIndicator").textContent = `Question ${currentIdx + 1} of ${total}`;
  const progressPercent = Math.round(((currentIdx) / total) * 100);
  document.getElementById("quizProgressFill").style.width = `${progressPercent}%`;

  document.getElementById("quizBadgeDifficulty").textContent = q.difficulty;
  document.getElementById("quizBadgeMarks").textContent = `${q.marks} Mark${q.marks > 1 ? 's' : ''}`;
  document.getElementById("quizQuestionText").textContent = q.question_text;

  const optionsContainer = document.getElementById("quizOptionsContainer");
  const letters = ["A", "B", "C", "D", "E", "F"];

  const savedAnswer = quiz.answers[q.id];
  const savedEval = quiz.evaluations[q.id];

  if (q.question_type === "MCQ" && q.options && q.options.length > 0) {
    optionsContainer.innerHTML = `
      <div class="quiz-options-list">
        ${q.options.map((opt, i) => {
          const isSelected = savedAnswer === opt;
          let extraClass = isSelected ? "selected" : "";
          if (savedEval) {
            if (opt === q.correct_answer) extraClass += " is-correct";
            else if (isSelected && !savedEval.is_correct) extraClass += " is-incorrect";
          }
          return `
            <div class="quiz-option-item ${extraClass} ${savedEval ? 'disabled' : ''}" onclick="selectQuizOptionByIndex(${i})">
              <div class="quiz-option-letter">${letters[i] || (i + 1)}</div>
              <div class="quiz-option-text">${escapeHtml(opt)}</div>
            </div>
          `;
        }).join("")}
      </div>
    `;
  } else {
    optionsContainer.innerHTML = `
      <textarea id="quizTextAnswerInput" class="quiz-text-answer" placeholder="Type your answer here..." ${savedEval ? 'disabled' : ''}>${escapeHtml(savedAnswer || "")}</textarea>
    `;
    const textarea = document.getElementById("quizTextAnswerInput");
    if (textarea && !savedEval) {
      textarea.addEventListener("input", (e) => {
        quiz.answers[q.id] = e.target.value;
      });
    }
  }

  const feedbackContainer = document.getElementById("quizFeedbackContainer");
  if (savedEval) {
    const isCorr = savedEval.is_correct;
    feedbackContainer.innerHTML = `
      <div class="quiz-feedback-box ${isCorr ? 'feedback-correct' : 'feedback-incorrect'}">
        <div class="feedback-status">
          <span>${isCorr ? '✓ Correct!' : '✕ Incorrect'}</span>
        </div>
        <div class="feedback-explanation">${escapeHtml(q.explanation || "Verified against study notes.")}</div>
        ${!isCorr ? `<div class="feedback-correct-answer">Correct Answer: ${escapeHtml(q.correct_answer)}</div>` : ''}
      </div>
    `;
  } else {
    feedbackContainer.innerHTML = "";
  }

  const submitBtn = document.getElementById("quizSubmitAnswerBtn");
  const nextBtn = document.getElementById("quizNextQuestionBtn");

  if (savedEval) {
    submitBtn.style.display = "none";
    nextBtn.style.display = "inline-flex";
    nextBtn.textContent = (currentIdx === total - 1) ? "Finish Quiz & View Results 🎉" : "Next Question →";
  } else {
    submitBtn.style.display = "inline-flex";
    nextBtn.style.display = "none";
  }
}

window.selectQuizOptionByIndex = (idx) => {
  const quiz = appState.activeQuiz;
  if (!quiz) return;
  const q = quiz.paper.questions[quiz.currentIndex];
  if (quiz.evaluations[q.id]) return;

  if (q.options && q.options[idx] !== undefined) {
    quiz.answers[q.id] = q.options[idx];
    renderCurrentQuizQuestion();
  }
};

function handleQuizSubmitCurrent() {
  const quiz = appState.activeQuiz;
  if (!quiz) return;
  const q = quiz.paper.questions[quiz.currentIndex];
  const userAns = quiz.answers[q.id] || "";

  if (!userAns.trim()) {
    Toast.warning("Please choose or provide an answer before submitting.");
    return;
  }

  let isCorrect = false;
  if (q.question_type === "MCQ") {
    isCorrect = (userAns.trim().toLowerCase() === q.correct_answer.trim().toLowerCase());
  } else {
    isCorrect = (userAns.trim().toLowerCase() === q.correct_answer.trim().toLowerCase() || userAns.length > 20);
  }

  quiz.evaluations[q.id] = {
    is_correct: isCorrect,
    user_answer: userAns,
    correct_answer: q.correct_answer
  };

  renderCurrentQuizQuestion();
}

async function handleQuizNext() {
  const quiz = appState.activeQuiz;
  if (!quiz) return;

  const total = quiz.paper.questions.length;
  if (quiz.currentIndex < total - 1) {
    quiz.currentIndex += 1;
    renderCurrentQuizQuestion();
  } else {
    await finishQuizSubmission();
  }
}

async function finishQuizSubmission() {
  const quiz = appState.activeQuiz;
  if (!quiz) return;

  const answersPayload = quiz.paper.questions.map(q => ({
    question_id: q.id,
    user_answer: quiz.answers[q.id] || ""
  }));

  try {
    AILoader.show(["Grading quiz answers...", "Compiling score summary..."]);
    const attemptResult = await api.quizzes.submit({
      question_paper_id: quiz.paper.id,
      answers: answersPayload
    });
    AILoader.hide();

    quiz.finalResult = attemptResult;
    renderQuizResultPage(attemptResult);
  } catch (err) {
    AILoader.hide();
    Toast.error(`Quiz grading error: ${err.message}`);
  }
}

function renderQuizResultPage(result) {
  document.getElementById("quizActiveQuestionSection").style.display = "none";
  const resultSection = document.getElementById("quizResultSection");
  resultSection.style.display = "block";

  document.getElementById("quizScorePercent").textContent = `${Math.round(result.percentage)}%`;
  document.getElementById("quizScoreRatio").textContent = `${result.correct_count} of ${result.total_questions} correct`;
  document.getElementById("quizMetricEarnedMarks").textContent = result.score;
  document.getElementById("quizMetricCorrect").textContent = result.correct_count;
  document.getElementById("quizMetricIncorrect").textContent = result.incorrect_count;

  const reviewContainer = document.getElementById("quizReviewBreakdown");
  reviewContainer.innerHTML = (result.details || []).map((item, idx) => `
    <div class="review-card ${item.is_correct ? 'correct' : 'incorrect'}">
      <div class="review-header">
        <span>Question ${idx + 1}: ${escapeHtml(item.question_text)}</span>
        <span style="color: ${item.is_correct ? 'var(--success)' : 'var(--danger)'};">
          ${item.is_correct ? '✓ Correct' : '✕ Incorrect'}
        </span>
      </div>
      <div style="font-size: 0.9rem; margin-bottom: 4px;"><strong>Your Answer:</strong> ${escapeHtml(item.user_answer || "No answer provided")}</div>
      ${!item.is_correct ? `<div style="font-size: 0.9rem; color: var(--success); margin-bottom: 4px;"><strong>Correct Answer:</strong> ${escapeHtml(item.correct_answer)}</div>` : ''}
      <div style="font-size: 0.85rem; color: var(--text-muted); margin-top: 6px;">Explanation: ${escapeHtml(item.explanation)}</div>
    </div>
  `).join("");
}

function exitQuizMode() {
  document.getElementById("quizActiveQuestionSection").style.display = "block";
  document.getElementById("quizResultSection").style.display = "none";
  appState.activeQuiz = null;
  navigateTo("project", { projectId: appState.activeProject?.id });
}

async function loadProjectHistory(projectId) {
  try {
    const history = await api.generation.history(projectId);
    renderHistoryTable(history);
  } catch (err) {
    console.error("Failed to load generation history:", err);
  }
}

function renderHistoryTable(history) {
  const container = document.getElementById("historyTableBody");
  if (!container) return;

  if (!history || history.length === 0) {
    container.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--text-muted); padding: 24px;">No generation history recorded yet.</td></tr>`;
    return;
  }

  container.innerHTML = history.map(h => `
    <tr style="border-bottom: 1px solid var(--border-subtle);">
      <td style="padding: 12px 16px; font-weight: 600; text-transform: capitalize;">${escapeHtml(h.generation_type.replace('_', ' '))}</td>
      <td style="padding: 12px 16px; font-family: var(--font-mono); font-size: 0.85rem; color: var(--primary-light);">${escapeHtml(h.model_used)}</td>
      <td style="padding: 12px 16px;">
        <span style="display: inline-block; padding: 2px 8px; border-radius: var(--radius-full); font-size: 0.75rem; font-weight: 700; ${h.status === 'SUCCESS' ? 'background: var(--success-bg); color: var(--success);' : 'background: var(--danger-bg); color: var(--danger);'}">
          ${escapeHtml(h.status)}
        </span>
      </td>
      <td style="padding: 12px 16px; font-size: 0.85rem; color: var(--text-muted);">${escapeHtml(h.error_message || "—")}</td>
      <td style="padding: 12px 16px; font-size: 0.85rem; color: var(--text-muted);">${Utils.formatDate(h.created_at)}</td>
    </tr>
  `).join("");
}

function setupEventListeners() {
  // Brand logo home navigation: single click goes to Home / Overview
  document.getElementById("brandHomeLink")?.addEventListener("click", () => {
    navigateTo("landing");
    Toast.info("Navigated to Home.");
  });

  // Double-click brand logo to sync/refresh data
  document.getElementById("brandHomeLink")?.addEventListener("dblclick", () => {
    triggerAppSync();
  });

  // Header reload button
  document.getElementById("headerReloadBtn")?.addEventListener("click", () => {
    triggerAppSync();
  });

  document.getElementById("navDashboardLink")?.addEventListener("click", (e) => {
    e.preventDefault();
    navigateTo("dashboard");
  });

  document.getElementById("landingCtaStart")?.addEventListener("click", () => {
    navigateTo("dashboard");
  });

  // Dashboard Toolbar Controls (Search, Filter, Sort, Clear)
  document.getElementById("dashboardSearchInput")?.addEventListener("input", (e) => {
    dashboardFilterState.search = e.target.value.trim().toLowerCase();
    applyDashboardFiltersAndRender();
  });

  document.getElementById("dashboardSubjectFilter")?.addEventListener("change", (e) => {
    dashboardFilterState.subject = e.target.value;
    applyDashboardFiltersAndRender();
  });

  document.getElementById("dashboardSortSelect")?.addEventListener("change", (e) => {
    dashboardFilterState.sort = e.target.value;
    applyDashboardFiltersAndRender();
  });

  document.getElementById("dashboardClearFiltersBtn")?.addEventListener("click", () => {
    dashboardFilterState = { search: "", subject: "", sort: "newest" };
    const sInput = document.getElementById("dashboardSearchInput");
    const subSel = document.getElementById("dashboardSubjectFilter");
    const sortSel = document.getElementById("dashboardSortSelect");
    if (sInput) sInput.value = "";
    if (subSel) subSel.value = "";
    if (sortSel) sortSel.value = "newest";
    applyDashboardFiltersAndRender();
    Toast.info("Dashboard filters reset.");
  });

  document.getElementById("dashboardRefreshBtn")?.addEventListener("click", () => {
    loadDashboardData();
    Toast.success("Projects synchronized!");
  });

  // Sample Presets for Quick Testing
  const samplePresets = {
    wsn: {
      subject: "IoT & Networking",
      title: "Wireless_Sensor_Networks.txt",
      text: "Wireless Sensor Networks (WSNs) consist of spatially dispersed autonomous devices called sensor nodes that monitor environmental conditions such as temperature, sound, and pressure. Each node typically comprises a sensing unit, a processing microcontroller, a radio transceiver, and a battery power unit. Energy efficiency is the paramount design constraint in WSNs because nodes are often deployed in inaccessible areas where battery replacement is infeasible. Key routing protocols include Directed Diffusion, LEACH (Low-Energy Adaptive Clustering Hierarchy), and PEGASIS. Security challenges encompass eavesdropping, node compromise, and denial-of-service attacks."
    },
    ai: {
      subject: "Artificial Intelligence",
      title: "Machine_Learning_Core.txt",
      text: "Artificial Intelligence (AI) enables machines to perform cognitive tasks including reasoning, learning, and pattern recognition. Machine learning (ML) constructs mathematical models trained on empirical data. Supervised learning algorithms learn mapping functions from labeled input-output training pairs, encompassing continuous regression (such as property valuations) and discrete classification (such as fraud detection). Unsupervised learning uncovers latent structures in unlabeled data using k-means clustering, hierarchical clustering, and principal component analysis (PCA). Reinforcement learning trains autonomous agents to maximize cumulative rewards through trial and error in dynamic environments."
    },
    bio: {
      subject: "Cell Biology & Genetics",
      title: "Molecular_Genetics_DNA.txt",
      text: "Genetics is the biological study of genes, genetic variation, and heredity in living organisms. Deoxyribonucleic acid (DNA) is the hereditary material containing biological instructions. DNA forms a double-helical structure composed of two complementary polynucleotide chains linked by hydrogen bonds: Adenine pairs with Thymine, and Cytosine pairs with Guanine. In the central dogma of molecular biology, DNA replicates during cell division, is transcribed into messenger RNA (mRNA) in the nucleus, and is translated into functional proteins by cytoplasmic ribosomes. Mutations represent heritable alterations in nucleotide sequences."
    }
  };

  // Sample preset click listeners
  document.querySelectorAll(".sample-preset-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const presetKey = btn.getAttribute("data-preset");
      const preset = samplePresets[presetKey];
      if (preset) {
        document.getElementById("quickSubjectInput").value = preset.subject;
        document.getElementById("quickDocTitleInput").value = preset.title;
        document.getElementById("quickStudyMaterialInput").value = preset.text;
        Toast.info(`Loaded sample: ${preset.subject}`);
      }
    });
  });

  // Instant Study Kit Generator
  document.getElementById("quickGenerateStudyKitBtn")?.addEventListener("click", async () => {
    const subject = document.getElementById("quickSubjectInput").value.trim() || "Computer Science";
    const docTitle = document.getElementById("quickDocTitleInput").value.trim() || "Study_Notes.txt";
    let content = document.getElementById("quickStudyMaterialInput").value.trim();

    if (!content || content.length < 20) {
      const defaultPreset = samplePresets.wsn;
      document.getElementById("quickSubjectInput").value = defaultPreset.subject;
      document.getElementById("quickDocTitleInput").value = defaultPreset.title;
      document.getElementById("quickStudyMaterialInput").value = defaultPreset.text;
      content = defaultPreset.text;
      Toast.info("Auto-loaded sample study notes!");
    }

    const wantSummary = document.getElementById("quickCheckSummary").checked;
    const wantTopics = document.getElementById("quickCheckTopics").checked;
    const wantQuiz = document.getElementById("quickCheckQuiz").checked;

    try {
      AILoader.show([
        "Creating study project workspace...",
        "Uploading & analyzing study notes...",
        wantSummary ? "Generating AI summary & key concepts..." : "Analyzing structure...",
        wantTopics ? "Extracting prioritized exam topics..." : "Synthesizing notes...",
        wantQuiz ? "Synthesizing practice quiz questions..." : "Finalizing kit..."
      ]);

      const proj = await api.projects.create({
        name: docTitle.replace(/\.[^/.]+$/, ""),
        subject,
        description: `Automated study project for ${subject}.`
      });

      const doc = await api.documents.create({
        project_id: proj.id,
        filename: docTitle,
        content
      });

      if (wantSummary) {
        await api.summaries.generate(doc.id);
      }
      if (wantTopics) {
        await api.topics.generate(doc.id);
      }
      if (wantQuiz) {
        await api.questionPapers.generate({
          project_id: proj.id,
          title: `${proj.name} Practice Quiz`,
          num_questions: 5,
          total_marks: 25,
          difficulty: "Medium",
          question_type: "MCQ",
          duration: 20
        });
      }

      AILoader.hide();
      Toast.success("Study Kit generated successfully! 🎉");
      navigateTo("project", { projectId: proj.id });
    } catch (err) {
      AILoader.hide();
      Toast.error(`Generation error: ${err.message}`);
    }
  });

  document.getElementById("landingCtaDemo")?.addEventListener("click", async () => {
    try {
      AILoader.show([
        "Initializing demo study project...",
        "Analyzing notes with AI...",
        "Generating executive summary & key concepts...",
        "Extracting prioritized exam topics...",
        "Synthesizing practice quiz questions..."
      ]);
      const project = await api.projects.create({
        name: "Wireless Sensor Networks",
        subject: "IoT & Networking",
        description: "Sensor nodes, power optimization, routing protocols, and IoT integration."
      });
      const sampleText = samplePresets.wsn.text;
      const doc = await api.documents.create({
        project_id: project.id,
        filename: "WSN_Foundations.txt",
        content: sampleText
      });

      await api.summaries.generate(doc.id);
      await api.topics.generate(doc.id);
      await api.questionPapers.generate({
        project_id: project.id,
        title: "WSN Foundations & Protocols Quiz",
        num_questions: 5,
        total_marks: 25,
        difficulty: "Medium",
        question_type: "MCQ",
        duration: 20
      });

      AILoader.hide();
      Toast.success("Full demo kit generated! Ready to study.");
      navigateTo("project", { projectId: project.id });
    } catch (err) {
      AILoader.hide();
      Toast.error(`Demo creation failed: ${err.message}`);
    }
  });

  document.getElementById("btnGenerateAllStudyKit")?.addEventListener("click", async () => {
    if (!appState.activeProject) return;
    const docs = appState.projectDocuments;
    if (!docs || docs.length === 0) {
      Toast.warning("Please add or paste at least one study document first.");
      switchProjectTab("material");
      return;
    }
    const targetDoc = appState.activeDocument || docs[0];

    try {
      AILoader.show([
        "Generating comprehensive AI summary...",
        "Extracting prioritized exam topics...",
        "Synthesizing practice quiz questions..."
      ]);

      await api.summaries.generate(targetDoc.id);
      await api.topics.generate(targetDoc.id);
      await api.questionPapers.generate({
        project_id: appState.activeProject.id,
        title: `${appState.activeProject.name} Practice Exam`,
        num_questions: 5,
        total_marks: 25,
        difficulty: "Medium",
        question_type: "MCQ",
        duration: 25
      });

      AILoader.hide();
      Toast.success("All study assets generated! 🎉");
      await loadProjectData(appState.activeProject.id);
      switchProjectTab("summary");
    } catch (err) {
      AILoader.hide();
      Toast.error(`Generation failed: ${err.message}`);
    }
  });

  document.getElementById("backToDashboardBtn")?.addEventListener("click", () => {
    navigateTo("dashboard");
  });

  document.querySelectorAll(".tab-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const tabId = btn.getAttribute("data-tab");
      switchProjectTab(tabId);
    });
  });

  document.getElementById("savePastedMaterialBtn")?.addEventListener("click", handleAddPastedText);
  document.getElementById("pastedMaterialInput")?.addEventListener("input", (e) => {
    document.getElementById("pasteCharCounter").textContent = `${e.target.value.length.toLocaleString()} characters`;
  });

  const fileInput = document.getElementById("fileUploadInput");
  fileInput?.addEventListener("change", (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFileUpload(e.target.files[0]);
    }
  });

  const dropZone = document.getElementById("fileDropZone");
  if (dropZone) {
    dropZone.addEventListener("dragover", (e) => {
      e.preventDefault();
      dropZone.style.borderColor = "var(--primary)";
      dropZone.style.background = "var(--bg-surface-hover)";
    });
    dropZone.addEventListener("dragleave", () => {
      dropZone.style.borderColor = "var(--border-medium)";
      dropZone.style.background = "var(--bg-input)";
    });
    dropZone.addEventListener("drop", (e) => {
      e.preventDefault();
      dropZone.style.borderColor = "var(--border-medium)";
      dropZone.style.background = "var(--bg-input)";
      if (e.dataTransfer.files && e.dataTransfer.files[0]) {
        handleFileUpload(e.dataTransfer.files[0]);
      }
    });
  }

  document.getElementById("btnGenerateSummary")?.addEventListener("click", triggerGenerateSummary);
  document.getElementById("btnGenerateTopics")?.addEventListener("click", triggerGenerateTopics);

  document.getElementById("newProjectForm")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const name = document.getElementById("newProjName").value.trim();
    const subject = document.getElementById("newProjSubject").value.trim();
    const desc = document.getElementById("newProjDesc").value.trim();

    try {
      const created = await api.projects.create({ name, subject, description: desc });
      Modal.close("newProjectModal");
      document.getElementById("newProjectForm").reset();
      Toast.success("Project created!");
      navigateTo("project", { projectId: created.id });
    } catch (err) {
      Toast.error(`Could not create project: ${err.message}`);
    }
  });

  document.getElementById("generatePaperForm")?.addEventListener("submit", (e) => {
    e.preventDefault();
    handleGeneratePaperSubmit();
  });

  document.getElementById("deleteProjectBtn")?.addEventListener("click", async () => {
    if (!confirm(`Are you sure you want to delete "${appState.activeProject?.name}" and all its documents?`)) return;
    try {
      await api.projects.delete(appState.activeProject.id);
      Toast.success("Project deleted.");
      navigateTo("dashboard");
    } catch (err) {
      Toast.error(`Delete failed: ${err.message}`);
    }
  });

  document.getElementById("quizSubmitAnswerBtn")?.addEventListener("click", handleQuizSubmitCurrent);
  document.getElementById("quizNextQuestionBtn")?.addEventListener("click", handleQuizNext);
  document.getElementById("quizExitBtn")?.addEventListener("click", exitQuizMode);
  document.getElementById("quizResultReturnBtn")?.addEventListener("click", exitQuizMode);
  document.getElementById("quizResultRetakeBtn")?.addEventListener("click", () => {
    document.getElementById("quizResultSection").style.display = "none";
    document.getElementById("quizActiveQuestionSection").style.display = "block";
    appState.startQuiz(appState.activeQuiz.paper);
    renderCurrentQuizQuestion();
  });

  document.getElementById("loginForm")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const email = document.getElementById("loginEmail").value.trim();
    const password = document.getElementById("loginPassword").value;

    try {
      const res = await api.auth.login({ email, password });
      api.setToken(res.access_token);
      appState.setUser(res.user);
      Modal.close("loginModal");
      updateAuthUI();
      Toast.success(`Welcome back, ${res.user.name}!`);
      navigateTo("dashboard");
    } catch (err) {
      Toast.error(`Login failed: ${err.message}`);
    }
  });

  document.getElementById("registerForm")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const name = document.getElementById("regName").value.trim();
    const email = document.getElementById("regEmail").value.trim();
    const password = document.getElementById("regPassword").value;

    try {
      const res = await api.auth.register({ name, email, password });
      api.setToken(res.access_token);
      appState.setUser(res.user);
      Modal.close("registerModal");
      updateAuthUI();
      Toast.success(`Account created! Welcome, ${res.user.name}!`);
      navigateTo("dashboard");
    } catch (err) {
      Toast.error(`Registration failed: ${err.message}`);
    }
  });

  document.querySelectorAll(".modal-backdrop").forEach(backdrop => {
    backdrop.addEventListener("click", (e) => {
      if (e.target === backdrop) {
        backdrop.classList.remove("open");
      }
    });
  });
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

async function triggerAppSync() {
  try {
    const status = await api.generation.status();
    appState.setAIStatus(status);
    updateAIStatusBadge(status);

    if (appState.currentView === "dashboard") {
      await loadDashboardData();
    } else if (appState.currentView === "project" && appState.activeProject) {
      await loadProjectData(appState.activeProject.id);
    }
    Toast.success("All data synchronized! 🔄");
  } catch (err) {
    Toast.error(`Sync error: ${err.message}`);
  }
}

