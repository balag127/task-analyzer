# Smart Task Analyzer

##  Overview
Smart Task Analyzer is a full-stack application that intelligently scores, ranks, and visualizes tasks based on urgency, importance, effort, and dependency impact. This project demonstrates backend design, algorithmic thinking, frontend development, and graph-based visualization.

##  Features
- Add tasks manually through UI  
- Bulk JSON input support  
- Weighted scoring algorithm  
- Multiple strategies (Smart Balance, Fastest Wins, High Impact, Deadline Driven)  
- Sorted task list with explanations and issue flags  
- Top 3 suggestions API  
- Circular dependency detection  
- Dependency graph visualization using Vis.js  

## Tech Stack

### Backend
- Python 3.8+
- Django 4+
- Django REST Framework
- django-cors-headers
- SQLite

### Frontend
- HTML / CSS
- JavaScript
- vis-network.js (graph visualization)

---

##  Project Structure
```
task-analyzer/
│
├── backend/
│   ├── manage.py
│   ├── requirements.txt
│   ├── task_analyzer/
│   │   ├── settings.py
│   │   ├── urls.py
│   └── tasks/
│       ├── scoring.py
│       ├── serializers.py
│       ├── views.py
│       ├── urls.py
│       ├── tests.py
│
└── frontend/
    ├── index.html
    ├── script.js
    └── styles.css
```

---

##  Setup Instructions

### 1️ Clone Repository
```bash
git clone https://github.com/balag127/task-analyzer.git
cd task-analyzer/backend
```

### 2️ Create Virtual Environment

#### Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

#### macOS / Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3️ Install Dependencies
```bash
pip install -r requirements.txt
```

### 4️ Run Backend Server
```bash
python manage.py migrate
python manage.py runserver
```
Backend runs at: http://localhost:8000/

### 5️ Run Frontend
```bash
cd ../frontend
python -m http.server 5500
```
Frontend runs at: http://localhost:5500/

---

##  Algorithm Explanation

Task prioritization blends urgency, importance, effort, and dependency impact.  
Each factor contributes to a weighted score between 0 and 1.

### **1. Urgency**
Calculated from days until due:

```
urgency_score = max(0, 1 - (days_until_due / 7))
```

### **2. Importance**
Normalized from user rating (1–10):

```
importance_score = importance / 10
```

### **3. Effort**
Lower effort means higher priority:

```
effort_score = 1 / (1 + estimated_hours)
```

### **4. Dependency Impact**
Blocking tasks increase score:  
```
dependency_score = 0.1 * (number_of_tasks_blocked)
```

### **5. Circular Dependency Detection**
Depth-first search (DFS) detects cycles.  
Circular tasks receive issue flags and penalties.

### **6. Smart Balance Weighted Score**
```
total_score =
  0.35 * urgency +
  0.35 * importance +
  0.15 * effort +
  0.15 * dependency
```

This creates a balanced and realistic prioritization.

---

##  Design Decisions
- Lightweight frontend without frameworks  
- REST API using DRF for clean JSON communication  
- In-memory suggestion caching  
- Added graph visualization for clarity  
- Flexible weighting strategy

---

##  Time Breakdown
| Task | Time |
|------|------|
| Algorithm design | 1 hr |
| Backend development | 1 hr |
| Frontend UI | 1 hr |
| API integration | 30 min |
| Graph visualization | 30 min |
| Debugging & polishing | 30 min |
| Extra work | 30 min | 
| **Total** | **5 hrs** |

---

##  Bonus Features Implemented
- ✔ Dependency Graph Visualization  
- ✔ Circular Dependency Highlighting  

---

##  Future Improvements
- Eisenhower Matrix  
- Database persistence for tasks  
- Custom user weight preferences  
- Holiday-aware urgency  
- Drag & drop interface  
- Dark mode  

---

##  License
MIT License — free to use and modify.

