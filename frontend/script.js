const API_BASE = "http://localhost:8000/api/tasks";

let tasks = [];
let nextId = 1;

// DOM elements
const taskForm = document.getElementById("task-form");
const bulkJsonTextarea = document.getElementById("bulk-json");
const loadJsonBtn = document.getElementById("load-json");
const taskList = document.getElementById("task-list");
const analyzeBtn = document.getElementById("analyze-btn");
const suggestBtn = document.getElementById("suggest-btn");
const strategySelect = document.getElementById("strategy");
const statusEl = document.getElementById("status");
const resultsEl = document.getElementById("results");
const suggestionsEl = document.getElementById("suggestions");

// Set status
function setStatus(message, type = "") {
    statusEl.textContent = message;
    statusEl.className = "status";
    if (type) statusEl.classList.add(type);
}

// Render task list
function renderTaskList() {
    taskList.innerHTML = "";
    tasks.forEach(t => {
        const li = document.createElement("li");
        li.textContent = `ID ${t.id}: ${t.title} (due: ${t.due_date || "n/a"})`;
        taskList.appendChild(li);
    });
}

// Add single task
taskForm.addEventListener("submit", e => {
    e.preventDefault();

    const title = document.getElementById("title").value.trim();
    if (!title) return setStatus("Title required.", "error");

    const dueDate = document.getElementById("due_date").value;
    const estimatedHours = parseFloat(document.getElementById("estimated_hours").value);
    const importance = parseInt(document.getElementById("importance").value, 10);
    const deps = document.getElementById("dependencies").value;

    const dependencies = deps
        ? deps.split(",").map(x => parseInt(x.trim(), 10)).filter(x => !isNaN(x))
        : [];

    const task = {
        id: nextId++,
        title,
        due_date: dueDate || null,
        estimated_hours: estimatedHours || 1,
        importance: importance || 5,
        dependencies
    };

    tasks.push(task);
    renderTaskList();
    taskForm.reset();
    setStatus("Task added.", "success");
});

// Load JSON tasks
loadJsonBtn.addEventListener("click", () => {
    try {
        const arr = JSON.parse(bulkJsonTextarea.value);
        if (!Array.isArray(arr)) throw new Error("JSON must be an array");

        tasks = arr.map(t => ({
            id: t.id ?? nextId++,
            title: t.title,
            due_date: t.due_date || null,
            estimated_hours: t.estimated_hours ?? 1,
            importance: t.importance ?? 5,
            dependencies: t.dependencies ?? []
        }));

        nextId = Math.max(...tasks.map(t => t.id)) + 1;
        renderTaskList();
        setStatus("JSON loaded successfully.", "success");
    } catch (err) {
        setStatus("Invalid JSON: " + err.message, "error");
    }
});

// Analyze tasks
async function analyzeTasks() {
    if (tasks.length === 0) {
        return setStatus("Add tasks first.", "error");
    }

    setStatus("Analyzing...", "");

    try {
        const strategy = strategySelect.value;

        const response = await fetch(`${API_BASE}/analyze/`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ strategy, tasks })
        });

        const data = await response.json();

        if (!response.ok) {
            return setStatus(data.detail || "Error analyzing tasks.", "error");
        }

        // Update local tasks (optional but cleaner)
        tasks = data.tasks.map(t => ({
            id: t.id,
            title: t.title,
            due_date: t.due_date,
            estimated_hours: t.estimated_hours,
            importance: t.importance,
            dependencies: t.dependencies
        }));

        renderTaskList();
        renderResults(data.tasks);
        renderDependencyGraph(data.tasks);

        setStatus("Analysis complete.", "success");

    } catch (err) {
        setStatus("Failed to analyze: " + err.message, "error");
    }
}

// Render results
function renderResults(scoredTasks) {
    resultsEl.innerHTML = "";
    scoredTasks.forEach(t => {
        const card = document.createElement("div");
        card.className = "task-card " +
            (t.priority_label === "High"
                ? "priority-high"
                : t.priority_label === "Medium"
                    ? "priority-medium"
                    : "priority-low");

        card.innerHTML = `
      <header>
        <span class="task-title">${t.title}</span>
        <span class="task-score">Score: ${t.score}</span>
      </header>

      <div class="task-meta">
        ID: ${t.id} • Due: ${t.due_date || "n/a"} • Hours: ${t.estimated_hours}
        • Importance: ${t.importance} • Priority: ${t.priority_label}
      </div>

      ${t.issues.length > 0 ? `<div class="task-issues">Issues: ${t.issues.join(" | ")}</div>` : ""}
      <div class="task-explanation">${t.explanation}</div>
    `;
        resultsEl.appendChild(card);
    });
}

// Render graph
function renderDependencyGraph(tasks) {
    const container = document.getElementById("dependency-graph");

    const nodes = [];
    const edges = [];

    tasks.forEach(task => {
        nodes.push({
            id: task.id,
            label: `${task.id}: ${task.title}`,
            color: task.issues.includes("Circular dependency detected.")
                ? "#f87171"
                : "#60a5fa"
        });

        task.dependencies.forEach(dep => {
            edges.push({
                from: dep,
                to: task.id,
                arrows: "to",
                color: task.issues.includes("Circular dependency detected.")
                    ? { color: "red" }
                    : { color: "#3b82f6" }
            });
        });
    });

    new vis.Network(
        container,
        { nodes: new vis.DataSet(nodes), edges: new vis.DataSet(edges) },
        {
            nodes: { shape: "box", font: { bold: true } },
            edges: { smooth: true },
            physics: { enabled: true }
        }
    );
}

// Suggest tasks
async function suggestTasks() {
    setStatus("Fetching suggestions...", "");

    try {
        const response = await fetch(`${API_BASE}/suggest/`);
        const data = await response.json();

        if (!response.ok) {
            return setStatus(data.detail || "Analyze tasks first.", "error");
        }

        suggestionsEl.innerHTML = "";
        renderResultsToElement(data.suggested, suggestionsEl);

        setStatus("Top 3 tasks suggested.", "success");

    } catch (err) {
        setStatus("Failed to fetch suggestions: " + err.message, "error");
    }
}

function renderResultsToElement(tasks, container) {
    container.innerHTML = "";
    tasks.forEach(t => {
        const card = document.createElement("div");
        card.className = "task-card priority-high";

        card.innerHTML = `
      <header>
        <span class="task-title">${t.title}</span>
        <span class="task-score">Score: ${t.score}</span>
      </header>
      <div class="task-explanation">${t.explanation}</div>
    `;
        container.appendChild(card);
    });
}

analyzeBtn.addEventListener("click", analyzeTasks);
suggestBtn.addEventListener("click", suggestTasks);
