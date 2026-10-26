"""Offline data integrity and quality metrics, separate from network checks."""

from __future__ import annotations

from collections import Counter
from datetime import date
import json
import math
from pathlib import Path
import re
from urllib.parse import urlsplit

from .catalog import DATA_DIR
from .skill_extractor import normalize_skill


def top_skills(roles: list[dict], limit: int = 30) -> list[dict]:
    """Count each skill once per role; ties by NFC canonical Unicode order."""
    counts = Counter(skill for role in roles for skill in {normalize_skill(s["name"]) for s in role["skills"]})
    return [{"name": name, "role_count": count} for name, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:limit]]


def inspect_data(roles, resources, aliases, extra_skills, banks) -> dict:
    errors, warnings = [], []

    def require(condition, path, message):
        if not condition:
            errors.append(f"{path}: {message}")
        return bool(condition)

    def identifier(value):
        return isinstance(value, str) and re.fullmatch(r"[a-z0-9][a-z0-9_-]*", value) is not None

    def canonical(value):
        return isinstance(value, str) and bool(value) and value == normalize_skill(value)

    def positive(value):
        return not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value) and value > 0

    def level(value):
        return type(value) is int and 1 <= value <= 3

    def url(value):
        try:
            return isinstance(value, str) and value == value.strip() and urlsplit(value).scheme in {"http", "https"} and bool(urlsplit(value).netloc)
        except (ValueError, TypeError):
            return False

    def valid_date(value):
        try:
            return isinstance(value, str) and date.fromisoformat(value) <= date.today()
        except (ValueError, TypeError):
            return False

    role_ids, role_skills = set(), {}
    require(isinstance(roles, list), "roles", "must be a list")
    for i, role in enumerate(roles if isinstance(roles, list) else []):
        p = f"roles[{i}]"
        if not require(isinstance(role, dict), p, "must be object"):
            continue
        rid = role.get("id")
        if require(identifier(rid), p + ".id", "invalid ID"):
            require(rid not in role_ids, p + ".id", "duplicate ID")
            role_ids.add(rid)
        for field in ("name", "name_vi"):
            require(isinstance(role.get(field), str) and bool(role[field].strip()) and role[field] == role[field].strip(), p + "." + field, "nonempty trimmed label required")
        skills = role.get("skills")
        if not require(isinstance(skills, list) and bool(skills), p + ".skills", "nonempty list required"):
            continue
        names = set()
        for j, skill in enumerate(skills):
            sp = f"{p}.skills[{j}]"
            if not require(isinstance(skill, dict), sp, "must be object"):
                continue
            name = skill.get("name")
            if require(canonical(name), sp + ".name", "canonical name required"):
                require(name not in names, sp, "duplicate skill")
                names.add(name)
            require(level(skill.get("level")), sp + ".level", "expected level 1..3")
            require(positive(skill.get("weight")), sp + ".weight", "positive finite weight required")
        if isinstance(rid, str):
            role_skills[rid] = names
    vocabulary = set().union(*role_skills.values()) if role_skills else set()
    require(isinstance(extra_skills, list), "skill_catalog", "must be list")
    extras = set()
    for i, name in enumerate(extra_skills if isinstance(extra_skills, list) else []):
        if require(canonical(name), f"skill_catalog[{i}]", "canonical name required"):
            require(name not in extras, f"skill_catalog[{i}]", "duplicate skill")
            extras.add(name)
    vocabulary |= extras
    require(isinstance(aliases, dict), "aliases", "must be object")
    aliases = aliases if isinstance(aliases, dict) else {}
    for alias, target in aliases.items():
        require(canonical(alias) and canonical(target), f"aliases.{alias}", "canonical alias/target required")
        require(isinstance(target, str) and target in vocabulary, f"aliases.{alias}", "target absent from recognition catalog")
        require(isinstance(target, str) and target not in aliases, f"aliases.{alias}", "alias chains/cycles not allowed")
        require(alias not in vocabulary, f"aliases.{alias}", "alias shadows canonical skill")

    require(isinstance(resources, dict), "resources", "must be object")
    resources = resources if isinstance(resources, dict) else {}
    ids, rows, urls = set(), [], set()
    for skill, group in resources.items():
        p = f"resources.{skill}"
        require(canonical(skill) and skill in vocabulary, p, "unknown/noncanonical skill key")
        if not require(isinstance(group, dict), p, "must be object"):
            continue
        require(group.get("skill_name") == skill, p, "skill_name must match key")
        require(isinstance(group.get("category"), str) and bool(group["category"]), p, "category required")
        records = group.get("resources")
        if not require(isinstance(records, list), p, "resources list required"):
            continue
        for i, record in enumerate(records):
            rp = f"{p}[{i}]"
            if not require(isinstance(record, dict), rp, "must be object"):
                continue
            rows.append((skill, record))
            resource_id = record.get("id")
            if require(identifier(resource_id), rp + ".id", "invalid ID"):
                require(resource_id not in ids, rp + ".id", "duplicate resource record ID")
                ids.add(resource_id)
            for field in ("title", "provider"):
                require(isinstance(record.get(field), str) and bool(record[field].strip()), rp + "." + field, "nonempty string required")
            if require(url(record.get("url")), rp + ".url", "HTTP(S) URL required"):
                urls.add(record["url"])
            require(record.get("language") in ("vi", "en", "multilingual"), rp, "invalid language")
            require(record.get("cost") in ("free", "freemium", "paid", "unknown"), rp, "invalid cost")
            require(record.get("type") in ("course", "book", "doc", "article", "video", "module"), rp, "invalid type")
            require(type(record.get("verified")) is bool, rp, "verified must be boolean")
            require(level(record.get("level_from")) and level(record.get("level_to")) and record["level_from"] <= record["level_to"], rp, "invalid level range")
            require("duration_hours" in record and (record["duration_hours"] is None or positive(record["duration_hours"])), rp, "duration must be positive or null")
            if record.get("duration_hours") is not None:
                require(url(record.get("duration_source")) and bool(record.get("duration_basis")), rp, "published duration requires source and basis")
            if record.get("estimated_duration_hours") is not None:
                require(positive(record["estimated_duration_hours"]) and bool(record.get("duration_basis")), rp, "estimate requires positive hours and basis")
            for field in ("last_checked", "content_reviewed_at", "duration_checked_at"):
                if record.get(field) is not None:
                    require(valid_date(record[field]), rp + "." + field, "ISO date not in future required")
            if record.get("content_review_status") is not None:
                require(record["content_review_status"] in ("reviewed", "partial", "unsuitable", "unreviewed", "blocked"), rp, "invalid review status")
                if record["content_review_status"] in ("reviewed", "partial", "unsuitable"):
                    require(bool(record.get("review_note")) and valid_date(record.get("content_reviewed_at")), rp, "review requires note and date")
                if record["content_review_status"] in ("unsuitable", "blocked"):
                    require(record.get("verified") is False, rp, "unsuitable/blocked resource cannot be verified")

    required = set().union(*role_skills.values()) if role_skills else set()
    for name in sorted(required):
        require(name in resources and isinstance(resources[name], dict) and bool(resources[name].get("resources")), f"role_resource.{name}", "role skill lacks resource link")
    uncovered = sorted(vocabulary - {skill for skill, _ in rows})
    for skill in uncovered:
        warnings.append(f"recognition_only.{skill}: no learning resource")
    question_ids, question_roles = set(), set()
    question_quality = Counter()
    for filename, bank in banks:
        mapping = bank.get("roles") if isinstance(bank, dict) else None
        if not require(isinstance(mapping, dict), filename, "roles object required"):
            continue
        for rid, questions in mapping.items():
            p = f"{filename}.{rid}"
            require(rid in role_ids, p, "unknown role ID")
            require(rid not in question_roles, p, "duplicate role question bank")
            question_roles.add(rid)
            if not require(isinstance(questions, list) and bool(questions), p, "nonempty question list required"):
                continue
            for i, question in enumerate(questions):
                qp = f"{p}[{i}]"
                if not require(isinstance(question, dict), qp, "must be object"):
                    continue
                qid = question.get("id")
                if require(identifier(qid), qp, "invalid question ID"):
                    require(qid not in question_ids, qp, "duplicate question ID")
                    question_ids.add(qid)
                skill = question.get("skill")
                require(canonical(skill), qp, "canonical skill/alias required")
                resolved = aliases.get(skill, skill) if isinstance(skill, str) else None
                require(resolved in role_skills.get(rid, set()), qp, "question skill not required by role")
                require(level(question.get("level")) and positive(question.get("weight")), qp, "invalid level/weight")
                require(question.get("type") in ("technical", "scenario"), qp, "invalid question type")
                require(isinstance(question.get("question"), str) and bool(question["question"].strip()), qp, "question text required")
                require(bool(question.get("reference_answer")) or bool(question.get("good_answer_points")), qp, "answer guidance required")
                quality = question.get("quality", "unreviewed")
                allowed_quality = ("reviewed", "ai_reviewed_internal", "template", "unreviewed")
                require(quality in allowed_quality, qp + ".quality", "invalid guidance review status")
                question_quality[quality if quality in allowed_quality else "invalid"] += 1
                if quality in ("reviewed", "ai_reviewed_internal"):
                    sources = question.get("quality_sources")
                    require(bool(question.get("quality_review_note")) and valid_date(question.get("quality_reviewed_at")),
                            qp + ".quality_review", "review note and date required")
                    require(isinstance(sources, list) and bool(sources) and all(url(source) for source in sources),
                            qp + ".quality_sources", "reviewed guidance requires HTTP(S) sources")
                    if quality == "ai_reviewed_internal":
                        require(bool(question.get("quality_reviewer")) and "AI" in str(question.get("quality_reviewer")),
                                qp + ".quality_reviewer", "AI-assisted review must be labeled")
                        require("not an independent" in str(question.get("quality_review_note", "")).casefold(),
                                qp + ".quality_review_note", "AI-assisted review must state it is not independent")
    for rid in sorted(role_ids - question_roles):
        errors.append(f"questions.{rid}: role has no question bank")
    statistics = {"roles": len(role_ids), "role_skills": len(required), "recognition_skills": len(vocabulary),
                  "resource_records": len(rows), "unique_urls": len(urls), "unverified": sum(r.get("verified") is False for _, r in rows),
                  "languages": dict(Counter(str(r.get("language")) for _, r in rows)),
                  "published_durations": sum(r.get("duration_hours") is not None for _, r in rows),
                  "published_duration_urls": len({r["url"] for _, r in rows if r.get("duration_hours") is not None and url(r.get("url"))}),
                  "estimated_durations": sum(r.get("estimated_duration_hours") is not None for _, r in rows),
                  "content_reviews": dict(Counter(str(r.get("content_review_status", "unreviewed")) for _, r in rows)),
                  "questions": len(question_ids), "question_guidance_reviews": dict(question_quality),
                  "recognition_without_resources": uncovered}
    return {"errors": errors, "warnings": warnings, "stats": statistics}


def audit_project(data_dir: Path = DATA_DIR) -> dict:
    def read(name):
        return json.loads((data_dir / name).read_text(encoding="utf-8"))
    directory = data_dir / "interview_question"
    if not directory.is_dir():
        directory = data_dir / "interview_questions"
    banks = [(p.name, json.loads(p.read_text(encoding="utf-8"))) for p in sorted(directory.glob("*.json"))]
    roles = read("roles.json")
    result = inspect_data(roles, read("resources.json"), read("skill_aliases.json"), read("skill_catalog.json"), banks)
    result["top30"] = top_skills(roles)
    return result
