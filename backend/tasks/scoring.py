from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import List, Dict, Tuple, Optional, Set


@dataclass
class TaskData:
    id: int
    title: str
    due_date: Optional[date]
    estimated_hours: float
    importance: int
    dependencies: List[int]
    # Computed fields:
    issues: List[str] = field(default_factory=list)
    cycle_member: bool = False


def _build_task_map(tasks: List[dict]) -> Dict[int, TaskData]:
    task_map: Dict[int, TaskData] = {}
    next_id = 1

    for raw in tasks:
        tid = raw.get("id")
        if tid is None:
            tid = next_id
            next_id += 1

        task = TaskData(
            id=tid,
            title=raw["title"],
            due_date=raw.get("due_date"),
            estimated_hours=float(raw.get("estimated_hours", 1.0)),
            importance=int(raw.get("importance", 5)),
            dependencies=list(raw.get("dependencies", [])),
        )
        task_map[tid] = task

    # Clean dependencies (remove unknown ones and add issue)
    for task in task_map.values():
        cleaned_deps = []
        for dep_id in task.dependencies:
            if dep_id in task_map:
                cleaned_deps.append(dep_id)
            else:
                task.issues.append(f"Unknown dependency id {dep_id} ignored.")
        task.dependencies = cleaned_deps
    return task_map


def _detect_cycles(task_map: Dict[int, TaskData]) -> None:
    """
    Simple DFS-based cycle detection. Marks tasks that are part of a cycle.
    """
    visited: Set[int] = set()
    stack: Set[int] = set()

    def dfs(tid: int):
        if tid in stack:
            # Cycle found: mark all in stack
            for sid in stack:
                task_map[sid].cycle_member = True
                if "Circular dependency detected." not in task_map[sid].issues:
                    task_map[sid].issues.append("Circular dependency detected.")
            return
        if tid in visited:
            return

        visited.add(tid)
        stack.add(tid)
        for dep in task_map[tid].dependencies:
            dfs(dep)
        stack.remove(tid)

    for tid in list(task_map.keys()):
        if tid not in visited:
            dfs(tid)


def _compute_reverse_dependencies(task_map: Dict[int, TaskData]) -> Dict[int, int]:
    """
    For each task, count how many tasks depend on it (directly).
    """
    count: Dict[int, int] = {tid: 0 for tid in task_map}
    for task in task_map.values():
        for dep in task.dependencies:
            if dep in count:
                count[dep] += 1
    return count


def _urgency_score(due: Optional[date], today: date) -> float:
    if not due:
        return 0.3  # unknown due date -> low urgency baseline

    delta_days = (due - today).days
    if delta_days < 0:
        # Overdue: more urgent than everything
        return 1.2
    # Within 0–30 days we scale from 1.0 down to ~0.4
    return max(0.4, 1.0 - (delta_days / 30.0))


def _importance_score(importance: int) -> float:
    return max(1, min(importance, 10)) / 10.0


def _effort_desirability(estimated_hours: float) -> float:
    # Lower hours -> closer to 1.0, large tasks -> lower values
    if estimated_hours <= 0:
        estimated_hours = 1.0
    return 1.0 / (1.0 + (estimated_hours / 4.0))


def _dependency_score(num_dependents: int) -> float:
    # Use a simple nonlinear scaling to avoid blowing up for many dependents
    if num_dependents <= 0:
        return 0.0
    return min(1.0, 0.3 + 0.1 * num_dependents)


def _priority_label(score: float) -> str:
    if score >= 0.9:
        return "High"
    if score >= 0.6:
        return "Medium"
    return "Low"


def _compute_score_for_strategy(
    strategy: str,
    urgency: float,
    importance: float,
    effort: float,
    dependency: float,
    overdue: bool,
    in_cycle: bool,
) -> float:
    """
    Strategy weights:
      - fastest_wins: favour effort
      - high_impact: favour importance
      - deadline_driven: favour urgency
      - smart_balance: combine all with penalties/bonuses
    """

    if strategy == "fastest_wins":
        base = (
            0.5 * effort
            + 0.2 * urgency
            + 0.2 * importance
            + 0.1 * dependency
        )
    elif strategy == "high_impact":
        base = (
            0.6 * importance
            + 0.2 * urgency
            + 0.2 * dependency
        )
    elif strategy == "deadline_driven":
        base = (
            0.6 * urgency
            + 0.2 * importance
            + 0.1 * effort
            + 0.1 * dependency
        )
    else:  # smart_balance
        base = (
            0.35 * urgency
            + 0.35 * importance
            + 0.15 * effort
            + 0.15 * dependency
        )

    # Adjustments
    if overdue:
        base += 0.1  # gently boost overdue tasks

    if in_cycle:
        base -= 0.1  # penalize tasks with circular dependencies

    # Clamp to reasonable range
    return max(0.0, min(base, 1.5))


def score_tasks(tasks: List[dict], strategy: str = "smart_balance") -> List[dict]:
    """
    Main scoring function used by views and tests.
    Returns a list of task dicts with added: score, priority_label, issues, explanation.
    """
    today = date.today()
    task_map = _build_task_map(tasks)
    _detect_cycles(task_map)
    reverse_deps = _compute_reverse_dependencies(task_map)

    scored: List[Tuple[float, dict]] = []

    for t in task_map.values():
        urgency = _urgency_score(t.due_date, today)
        importance = _importance_score(t.importance)
        effort = _effort_desirability(t.estimated_hours)
        dependency = _dependency_score(reverse_deps.get(t.id, 0))
        overdue = bool(t.due_date and t.due_date < today)

        score = _compute_score_for_strategy(
            strategy=strategy,
            urgency=urgency,
            importance=importance,
            effort=effort,
            dependency=dependency,
            overdue=overdue,
            in_cycle=t.cycle_member,
        )

        explanation_parts = []

        if overdue:
            explanation_parts.append("Overdue task (higher urgency).")
        elif t.due_date:
            explanation_parts.append(f"Due on {t.due_date.isoformat()}.")

        explanation_parts.append(f"Importance: {t.importance}/10.")
        explanation_parts.append(f"Estimated effort: {t.estimated_hours}h.")

        num_dependents = reverse_deps.get(t.id, 0)
        if num_dependents > 0:
            explanation_parts.append(
                f"Blocks {num_dependents} other task(s)."
            )

        if strategy == "fastest_wins":
            explanation_parts.append("Strategy: Fastest Wins (favoring low effort).")
        elif strategy == "high_impact":
            explanation_parts.append("Strategy: High Impact (favoring importance).")
        elif strategy == "deadline_driven":
            explanation_parts.append("Strategy: Deadline Driven (favoring due date).")
        else:
            explanation_parts.append("Strategy: Smart Balance (balancing all factors).")

        if t.cycle_member:
            explanation_parts.append(
                "Part of a circular dependency (slightly penalized)."
            )

        explanation = " ".join(explanation_parts)

        result_task = {
            "id": t.id,
            "title": t.title,
            "due_date": t.due_date,
            "estimated_hours": t.estimated_hours,
            "importance": t.importance,
            "dependencies": t.dependencies,
            "score": round(score, 3),
            "priority_label": _priority_label(score),
            "issues": t.issues,
            "explanation": explanation,
        }
        scored.append((score, result_task))

    # Sort by score (desc), then by earlier due date, then by importance
    scored.sort(
        key=lambda tup: (
            -tup[0],
            tup[1]["due_date"] or date.max,
            -tup[1]["importance"],
        )
    )

    return [t for _, t in scored]
