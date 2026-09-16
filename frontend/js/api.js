/**
 * StudyGen AI - Centralized REST API Client
 */

const API_BASE = "/api";

class ApiService {
  constructor() {
    this.token = localStorage.getItem("studygen_token") || null;
  }

  setToken(token) {
    this.token = token;
    if (token) {
      localStorage.setItem("studygen_token", token);
    } else {
      localStorage.removeItem("studygen_token");
    }
  }

  async request(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    const headers = options.headers || {};

    if (this.token) {
      headers["Authorization"] = `Bearer ${this.token}`;
    }

    if (!(options.body instanceof FormData) && !headers["Content-Type"]) {
      headers["Content-Type"] = "application/json";
    }

    const config = {
      ...options,
      headers
    };

    try {
      const response = await fetch(url, config);
      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        if (response.status === 404 && (endpoint.includes("/summaries/document/") || endpoint.includes("/topics/document/"))) {
          return null;
        }
        const errorDetail = data.detail || response.statusText || "Request failed";
        throw new Error(errorDetail);
      }

      return data;
    } catch (error) {
      if (endpoint.includes("/summaries/document/") || endpoint.includes("/topics/document/")) {
        return null;
      }
      console.error(`API Error [${endpoint}]:`, error);
      throw error;
    }
  }

  // Authentication
  auth = {
    register: (userData) => this.request("/auth/register", { method: "POST", body: JSON.stringify(userData) }),
    login: (credentials) => this.request("/auth/login", { method: "POST", body: JSON.stringify(credentials) }),
    me: () => this.request("/auth/me")
  };

  // Projects
  projects = {
    list: () => this.request("/projects"),
    create: (data) => this.request("/projects", { method: "POST", body: JSON.stringify(data) }),
    get: (id) => this.request(`/projects/${id}`),
    update: (id, data) => this.request(`/projects/${id}`, { method: "PUT", body: JSON.stringify(data) }),
    delete: (id) => this.request(`/projects/${id}`, { method: "DELETE" })
  };

  // Documents
  documents = {
    list: (projectId) => this.request(`/documents/project/${projectId}`),
    create: (data) => this.request("/documents", { method: "POST", body: JSON.stringify(data) }),
    upload: (projectId, file) => {
      const formData = new FormData();
      formData.append("project_id", projectId);
      formData.append("file", file);
      return this.request("/documents/upload", { method: "POST", body: formData });
    },
    get: (id) => this.request(`/documents/${id}`),
    delete: (id) => this.request(`/documents/${id}`, { method: "DELETE" })
  };

  // Summaries
  summaries = {
    generate: (documentId) => this.request("/summaries/generate", { method: "POST", body: JSON.stringify({ document_id: documentId }) }),
    getByDoc: (documentId) => this.request(`/summaries/document/${documentId}`)
  };

  // Important Topics
  topics = {
    generate: (documentId) => this.request("/topics/generate", { method: "POST", body: JSON.stringify({ document_id: documentId }) }),
    getByDoc: (documentId) => this.request(`/topics/document/${documentId}`)
  };

  // Question Papers
  questionPapers = {
    generate: (config) => this.request("/question-papers/generate", { method: "POST", body: JSON.stringify(config) }),
    list: (projectId) => this.request(`/question-papers/project/${projectId}`),
    get: (id) => this.request(`/question-papers/${id}`),
    delete: (id) => this.request(`/question-papers/${id}`, { method: "DELETE" })
  };

  // Quizzes
  quizzes = {
    submit: (answersData) => this.request("/quizzes/submit", { method: "POST", body: JSON.stringify(answersData) }),
    getAttempts: (paperId) => this.request(`/quizzes/paper/${paperId}/attempts`),
    getAttempt: (attemptId) => this.request(`/quizzes/attempts/${attemptId}`)
  };

  // Generation & Status
  generation = {
    history: (projectId) => this.request(`/generation/project/${projectId}`),
    status: () => this.request("/generation/status")
  };
}

window.api = new ApiService();
