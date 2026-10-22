#!/usr/bin/env python3
"""Rank career-vault project notes against a job description using a transparent heuristic."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path

IGNORE_DIRS = {".git", ".obsidian", "node_modules", ".tmp", "target", "dist", "build"}
PROJECT_DIR_MARKERS = ("10-projects", "10-项目案例")

# English and Chinese aliases are matched case-insensitively as substrings.
TERM_ALIASES: dict[str, tuple[str, ...]] = {
    "java": ("java",),
    "spring": ("spring",),
    "spring boot": ("spring boot", "springboot", "spring-boot"),
    "spring cloud": ("spring cloud", "springcloud", "spring-cloud"),
    "nacos": ("nacos",),
    "dubbo": ("dubbo",),
    "mybatis": ("mybatis", "mybatis-plus"),
    "postgresql": ("postgresql", "postgres", "pg"),
    "mysql": ("mysql",),
    "redis": ("redis",),
    "rocketmq": ("rocketmq", "rocket mq", "消息队列", "mq"),
    "kafka": ("kafka",),
    "elasticsearch": ("elasticsearch", "elastic search", "es "),
    "docker": ("docker",),
    "kubernetes": ("kubernetes", "k8s"),
    "microservice": ("microservice", "microservices", "微服务"),
    "oauth2": ("oauth2", "oauth 2", "oauth"),
    "jwt": ("jwt", "token", "令牌"),
    "payment": ("payment", "pay", "支付", "收银台", "退款"),
    "subscription": ("subscription", "subscribe", "订阅", "续费", "会员"),
    "ecommerce": ("ecommerce", "e-commerce", "商城", "电商"),
    "order": ("order", "订单"),
    "inventory": ("inventory", "库存", "扣减", "占用"),
    "idempotency": ("idempotent", "idempotency", "幂等"),
    "transaction": ("transaction", "事务", "一致性"),
    "cache": ("cache", "缓存"),
    "message queue": ("message queue", "消息队列", "mq"),
    "ci/cd": ("ci/cd", "cicd", "pipeline", "流水线"),
    "testing": ("test", "testing", "测试", "回归", "覆盖率"),
    "observability": ("observability", "监控", "日志", "追踪", "指标"),
    "performance": ("performance", "性能", "延迟", "吞吐", "qps"),
    "stability": ("stability", "稳定", "高可用", "容灾", "降级", "熔断"),
    "react": ("react",),
    "vue": ("vue",),
    "typescript": ("typescript", "ts"),
    "node": ("node.js", "nodejs", "node"),
    "python": ("python",),
    "go": ("golang", "go language", "go "),
    "sql": ("sql", "数据库", "database"),
    "linux": ("linux",),
    "git": ("git", "版本控制"),
    "agent": ("agent", "智能体", "多 agent", "multi-agent"),
    "skill": ("skill", "技能", "agent skill"),
    "platform": ("platform", "平台", "工作台", "工具链"),
    "architecture": ("architecture", "架构", "设计"),
    "payment gateway": ("payment gateway", "支付网关", "支付中心"),
    "webhook": ("webhook", "回调", "异步通知"),
    "apple": ("apple", "app store", "storekit"),
    "google play": ("google play", "google billing"),
    "useepay": ("useepay",),
}

PREFIXES = ("java", "spring", "redis", "mysql", "postgres", "kafka", "docker", "kubernetes", "react", "vue", "typescript", "python", "golang", "oauth", "jwt", "mq")


def should_ignore(path: Path, root: Path) -> bool:
    try:
        return any(part in IGNORE_DIRS for part in path.relative_to(root).parts)
    except ValueError:
        return False


def parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end == -1:
        return {}
    data: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if ":" in line and not line.startswith((" ", "-")):
            key, value = line.split(":", 1)
            data[key.strip()] = value.strip().strip("\"'")
    return data


def extract_terms(jd: str) -> list[str]:
    text = jd.lower()
    terms = [term for term, aliases in TERM_ALIASES.items() if any(alias.lower() in text for alias in aliases)]
    # Preserve useful technical tokens that are not in the curated dictionary.
    for token in re.findall(r"\b[A-Za-z][A-Za-z0-9.+#/-]{2,}\b", jd):
        low = token.lower()
        if low.startswith(PREFIXES) and low not in terms:
            terms.append(low)
    return sorted(set(terms))


def parse_date(value: str | None, fallback: Path) -> date | None:
    for raw in (value, None):
        if raw:
            for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
                try:
                    return datetime.strptime(raw, fmt).date()
                except ValueError:
                    pass
    try:
        return datetime.fromtimestamp(fallback.stat().st_mtime).date()
    except OSError:
        return None


def recency_score(project_date: date | None, today: date) -> float:
    if project_date is None:
        return 0.6
    days = max(0, (today - project_date).days)
    if days <= 365:
        return 1.0
    if days <= 730:
        return 0.8
    if days <= 1460:
        return 0.6
    return 0.4


def evidence_score(text: str, fm: dict[str, str]) -> float:
    raw = (fm.get("evidence_level") or fm.get("evidence") or "").upper()
    if raw.startswith("A"):
        return 1.0
    if raw.startswith("B"):
        return 0.75
    if raw.startswith("C"):
        return 0.35
    if raw.startswith("D"):
        return 0.0
    if re.search(r"^#{1,4}\s+(evidence|sources|证据|来源)\b", text, re.MULTILINE | re.IGNORECASE):
        return 0.8
    return 0.45


def ownership_score(text: str) -> float:
    low = text.lower()
    if any(word in low for word in ("主导", "独立负责", "独立完成", "led ", "owned ")):
        return 1.0
    if any(word in low for word in ("参与", "协助", "contributor", "participated")):
        return 0.6
    return 0.78


def project_title(path: Path, text: str) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return path.stem


def score_project(path: Path, root: Path, terms: list[str], today: date) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    fm = parse_frontmatter(text)
    low = text.lower()
    matched = [
        term for term in terms
        if any(alias.lower() in low for alias in TERM_ALIASES.get(term, (term,)))
    ]
    missing = [term for term in terms if term not in matched]
    coverage = len(matched) / len(terms) if terms else 0.0
    evidence = evidence_score(text, fm)
    ownership = ownership_score(text)
    project_date = parse_date(fm.get("last_verified") or fm.get("date"), path)
    recency = recency_score(project_date, today)
    score = round(100 * (0.50 * coverage + 0.25 * evidence + 0.15 * ownership + 0.10 * recency), 1)
    if score >= 70:
        recommendation = "main"
    elif score >= 45:
        recommendation = "supporting"
    else:
        recommendation = "skip"
    return {
        "title": project_title(path, text),
        "path": path.relative_to(root).as_posix(),
        "score": score,
        "recommendation": recommendation,
        "coverage": round(coverage, 4),
        "evidence_score": round(evidence, 2),
        "ownership_score": round(ownership, 2),
        "recency_score": round(recency, 2),
        "matched_terms": matched,
        "missing_terms": missing,
        "date": project_date.isoformat() if project_date else "",
    }


def score_vault(vault: Path, jd: str, today: date, top: int) -> dict:
    vault = vault.resolve()
    if not vault.exists() or not vault.is_dir():
        raise ValueError(f"Vault directory does not exist: {vault}")
    terms = extract_terms(jd)
    projects = []
    for path in vault.rglob("*.md"):
        if should_ignore(path, vault):
            continue
        rel = path.relative_to(vault).as_posix()
        if not any(marker in rel for marker in PROJECT_DIR_MARKERS):
            continue
        projects.append(score_project(path, vault, terms, today))
    projects.sort(key=lambda item: (-item["score"], item["title"].lower()))
    return {
        "vault": str(vault),
        "jd_terms": terms,
        "top": projects[:top],
        "all_projects": projects,
    }


def print_summary(result: dict) -> None:
    print("JD terms:", ", ".join(result["jd_terms"]) or "(none detected)")
    print("Ranked projects:")
    for item in result["top"]:
        print(f"- {item['score']:5.1f}  {item['recommendation']:10s}  {item['title']}  ({item['path']})")
        print(f"          matched: {', '.join(item['matched_terms']) or '-'}")
        print(f"          missing: {', '.join(item['missing_terms']) or '-'}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Rank career-vault projects against a JD.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--jd-file", help="Path to a JD text or Markdown file")
    source.add_argument("--jd-text", help="JD text")
    parser.add_argument("--vault", required=True, help="Career vault path")
    parser.add_argument("--top", type=int, default=5, help="Number of projects to show")
    parser.add_argument("--today", default=None, help="Override today's date (YYYY-MM-DD) for deterministic tests")
    parser.add_argument("--json", action="store_true", help="Print JSON")
    args = parser.parse_args()

    jd = Path(args.jd_file).read_text(encoding="utf-8", errors="replace") if args.jd_file else args.jd_text
    today = datetime.strptime(args.today, "%Y-%m-%d").date() if args.today else date.today()
    try:
        result = score_vault(Path(args.vault), jd or "", today, max(1, args.top))
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print_summary(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
