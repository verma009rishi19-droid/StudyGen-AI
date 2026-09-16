/**
 * StudyGen AI - Centralized Reactive State Store
 */

class StateStore {
  constructor() {
    this.user = null;
    this.currentView = "landing";
    this.projects = [];
    this.activeProject = null;
    this.projectDocuments = [];
    this.activeDocument = null;
    this.activeTab = "material";
    this.activeQuiz = null; // { paper: null, currentIndex: 0, answers: {}, evaluations: null }
    this.aiStatus = null;
    this.listeners = [];
  }

  subscribe(listener) {
    this.listeners.push(listener);
    return () => {
      this.listeners = this.listeners.filter(l => l !== listener);
    };
  }

  notify(event, payload) {
    this.listeners.forEach(listener => listener(event, payload));
  }

  setUser(user) {
    this.user = user;
    this.notify("USER_CHANGED", user);
  }

  setView(viewName) {
    this.currentView = viewName;
    this.notify("VIEW_CHANGED", viewName);
  }

  setProjects(projects) {
    this.projects = projects;
    this.notify("PROJECTS_UPDATED", projects);
  }

  setActiveProject(project) {
    this.activeProject = project;
    this.activeDocument = null;
    this.notify("ACTIVE_PROJECT_CHANGED", project);
  }

  setProjectDocuments(docs) {
    this.projectDocuments = docs;
    if (docs.length > 0 && !this.activeDocument) {
      this.activeDocument = docs[0];
    }
    this.notify("DOCUMENTS_UPDATED", docs);
  }

  setActiveDocument(doc) {
    this.activeDocument = doc;
    this.notify("ACTIVE_DOCUMENT_CHANGED", doc);
  }

  setActiveTab(tabName) {
    this.activeTab = tabName;
    this.notify("TAB_CHANGED", tabName);
  }

  setAIStatus(status) {
    this.aiStatus = status;
    this.notify("AI_STATUS_UPDATED", status);
  }

  startQuiz(paper) {
    this.activeQuiz = {
      paper,
      currentIndex: 0,
      answers: {},
      evaluations: {},
      isCompleted: false,
      finalResult: null
    };
    this.setView("quiz");
    this.notify("QUIZ_STARTED", this.activeQuiz);
  }
}

window.appState = new StateStore();
