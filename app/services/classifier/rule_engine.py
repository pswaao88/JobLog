from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


@dataclass
class Rule:
    category: str
    target_value: str
    keyword: str
    match_type: str
    priority: int
    weight: int
    is_negation: bool


def _normalize(value: str | None) -> str:
    if not value:
        return ""
    return value.lower()


def _matches(match_type: str, keyword: str, haystack: str) -> bool:
    if not keyword:
        return False
    k = _normalize(keyword)
    h = _normalize(haystack)

    if match_type == "exact":
        return h == k
    # MVP: regex is treated as contains for now
    return k in h


def _build_text_blob(job: dict[str, Any]) -> str:
    fields = [
        job.get("title"),
        job.get("description_text"),
        job.get("employment_text_raw"),
        job.get("experience_text_raw"),
        job.get("tech_stack_text"),
    ]
    return "\n".join([str(v) for v in fields if v])


def _pick_employment(employment_rules: list[Rule], text_blob: str) -> tuple[str, list[dict[str, Any]]]:
    matches: list[tuple[int, str, Rule]] = []
    matched_keywords: list[dict[str, Any]] = []

    for rule in employment_rules:
        if _matches(rule.match_type, rule.keyword, text_blob):
            matches.append((rule.priority, rule.target_value, rule))
            matched_keywords.append(
                {
                    "category": "employment",
                    "target_value": rule.target_value,
                    "keyword": rule.keyword,
                    "priority": rule.priority,
                }
            )

    if not matches:
        return "unknown", matched_keywords

    matches.sort(key=lambda x: x[0])
    return matches[0][1], matched_keywords


def _pick_role(role_rules: list[Rule], exclude_rules: list[Rule], text_blob: str) -> tuple[str, list[dict[str, Any]]]:
    matched_keywords: list[dict[str, Any]] = []

    excluded = False
    for rule in exclude_rules:
        if _matches(rule.match_type, rule.keyword, text_blob):
            excluded = True
            matched_keywords.append(
                {
                    "category": "exclude",
                    "target_value": rule.target_value,
                    "keyword": rule.keyword,
                    "priority": rule.priority,
                }
            )

    role_matches: list[tuple[int, str, Rule]] = []
    for rule in role_rules:
        if _matches(rule.match_type, rule.keyword, text_blob):
            role_matches.append((rule.priority, rule.target_value, rule))
            matched_keywords.append(
                {
                    "category": "role",
                    "target_value": rule.target_value,
                    "keyword": rule.keyword,
                    "priority": rule.priority,
                }
            )

    if excluded or not role_matches:
        return "unknown", matched_keywords

    role_matches.sort(key=lambda x: x[0])
    return role_matches[0][1], matched_keywords


def _compute_score(score_rules: list[Rule], text_blob: str) -> tuple[int, list[dict[str, Any]]]:
    score = 50
    matched_keywords: list[dict[str, Any]] = []

    for rule in score_rules:
        if _matches(rule.match_type, rule.keyword, text_blob):
            score += rule.weight
            matched_keywords.append(
                {
                    "category": "score",
                    "target_value": rule.target_value,
                    "keyword": rule.keyword,
                    "weight": rule.weight,
                }
            )

    score = max(0, min(100, score))
    return score, matched_keywords


def _compute_confidence(employment_type: str, role_type: str, score_match_count: int) -> float:
    confidence = 0.5
    if employment_type != "unknown":
        confidence += 0.2
    if role_type != "unknown":
        confidence += 0.2
    confidence += min(0.1, score_match_count * 0.03)
    return round(min(1.0, confidence), 3)


def classify_jobs(db: Session, rule_version: str, limit: int = 200) -> dict[str, Any]:
    rule_rows = db.execute(
        text(
            """
            SELECT category, target_value, keyword, match_type, priority, weight, is_negation
            FROM classification_rules
            WHERE rule_version = :rule_version
              AND is_active = true
            ORDER BY category, priority ASC, id ASC
            """
        ),
        {"rule_version": rule_version},
    ).mappings().all()

    if not rule_rows:
        raise ValueError(f"No active rules found for rule_version={rule_version}")

    grouped: dict[str, list[Rule]] = {"employment": [], "role": [], "exclude": [], "score": []}
    for row in rule_rows:
        grouped.setdefault(row["category"], []).append(
            Rule(
                category=row["category"],
                target_value=row["target_value"],
                keyword=row["keyword"],
                match_type=row["match_type"],
                priority=row["priority"],
                weight=row["weight"],
                is_negation=row["is_negation"],
            )
        )

    jobs = db.execute(
        text(
            """
            SELECT
              j.id,
              j.title,
              j.description_text,
              j.employment_text_raw,
              j.experience_text_raw,
              j.tech_stack_text
            FROM jobs j
            ORDER BY j.updated_at DESC, j.id DESC
            LIMIT :limit
            """
        ),
        {"limit": limit},
    ).mappings().all()

    classified_count = 0

    for job in jobs:
        text_blob = _build_text_blob(job)

        employment_type, employment_matches = _pick_employment(grouped.get("employment", []), text_blob)
        role_type, role_matches = _pick_role(grouped.get("role", []), grouped.get("exclude", []), text_blob)
        score, score_matches = _compute_score(grouped.get("score", []), text_blob)

        matched_keywords = employment_matches + role_matches + score_matches
        confidence = _compute_confidence(employment_type, role_type, len(score_matches))

        reasoning = (
            f"employment={employment_type}, role={role_type}, score={score}, "
            f"matches={len(matched_keywords)}"
        )

        db.execute(
            text(
                """
                INSERT INTO job_classifications (
                    job_id, rule_version, employment_type, role_type,
                    new_grad_score, confidence, matched_keywords, reasoning, created_at
                ) VALUES (
                    :job_id, :rule_version, :employment_type, :role_type,
                    :new_grad_score, :confidence, CAST(:matched_keywords AS jsonb), :reasoning, NOW()
                )
                ON CONFLICT (job_id, rule_version)
                DO UPDATE SET
                    employment_type = EXCLUDED.employment_type,
                    role_type = EXCLUDED.role_type,
                    new_grad_score = EXCLUDED.new_grad_score,
                    confidence = EXCLUDED.confidence,
                    matched_keywords = EXCLUDED.matched_keywords,
                    reasoning = EXCLUDED.reasoning,
                    created_at = NOW()
                """
            ),
            {
                "job_id": job["id"],
                "rule_version": rule_version,
                "employment_type": employment_type,
                "role_type": role_type,
                "new_grad_score": score,
                "confidence": confidence,
                "matched_keywords": json.dumps(matched_keywords, ensure_ascii=False),
                "reasoning": reasoning,
            },
        )
        classified_count += 1

    db.commit()

    return {
        "rule_version": rule_version,
        "processed_count": len(jobs),
        "classified_count": classified_count,
    }
