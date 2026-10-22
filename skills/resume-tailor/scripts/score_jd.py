#!/usr/bin/env python3
"""Rank career-vault projects against a JD with profile-aware lexical scoring."""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import Counter
from datetime import date, datetime
from pathlib import Path

from vault_config import iter_markdown, resolve_vaults

PROJECT_DIR_MARKERS = ("10-projects", "10-项目案例")
PROFILE_PATH = Path(__file__).resolve().parents[1] / "references" / "job-family-profiles.json"

TERM_ALIASES: dict[str, tuple[str, ...]] = {
    "java": ("java",), "spring": ("spring",), "spring boot": ("spring boot", "springboot", "spring-boot"),
    "spring cloud": ("spring cloud", "springcloud", "spring-cloud"), "nacos": ("nacos",),
    "dubbo": ("dubbo",), "mybatis": ("mybatis", "mybatis-plus"),
    "postgresql": ("postgresql", "postgres", "pg"), "mysql": ("mysql",), "redis": ("redis",),
    "rocketmq": ("rocketmq", "rocket mq", "消息队列", "mq"), "kafka": ("kafka",),
    "elasticsearch": ("elasticsearch", "elastic search", "es "), "docker": ("docker",),
    "kubernetes": ("kubernetes", "k8s"), "microservice": ("microservice", "microservices", "微服务"),
    "oauth2": ("oauth2", "oauth 2", "oauth"), "jwt": ("jwt", "token", "令牌"),
    "payment": ("payment", "pay", "支付", "收银台", "退款"), "subscription": ("subscription", "subscribe", "订阅", "续费", "会员"),
    "ecommerce": ("ecommerce", "e-commerce", "商城", "电商"), "order": ("order", "订单"),
    "inventory": ("inventory", "库存", "扣减", "占用"), "idempotency": ("idempotent", "idempotency", "幂等"),
    "transaction": ("transaction", "事务", "一致性"), "cache": ("cache", "缓存"),
    "message queue": ("message queue", "消息队列", "mq"), "ci/cd": ("ci/cd", "cicd", "pipeline", "流水线"),
    "testing": ("test", "testing", "测试", "回归", "覆盖率"), "observability": ("observability", "监控", "日志", "追踪", "指标"),
    "performance": ("performance", "性能", "延迟", "吞吐", "qps"), "stability": ("stability", "稳定", "高可用", "容灾", "降级", "熔断"),
    "react": ("react",), "vue": ("vue",), "typescript": ("typescript", "ts"), "node": ("node.js", "nodejs", "node"),
    "python": ("python",), "go": ("golang", "go language", "go "), "sql": ("sql", "数据库", "database"),
    "linux": ("linux",), "git": ("git", "版本控制"), "agent": ("agent", "智能体", "多 agent", "multi-agent"),
    "skill": ("skill", "技能", "agent skill"), "platform": ("platform", "平台", "工作台", "工具链"),
    "architecture": ("architecture", "架构", "设计"), "payment gateway": ("payment gateway", "支付网关", "支付中心"),
    "webhook": ("webhook", "回调", "异步通知"), "apple": ("apple", "app store", "storekit"),
    "google play": ("google play", "google billing"), "useepay": ("useepay",),
    "mcp": ("mcp",), "code generation": ("code generation", "代码生成"), "migration": ("migration", "迁移"),
    "compatibility": ("compatibility", "兼容"), "legacy": ("legacy", "旧系统"),
}

STOPWORDS = {
    "the", "and", "for", "with", "from", "this", "that", "into", "your", "you", "are", "our",
    "使用", "负责", "参与", "以及", "相关", "项目", "进行", "一个", "能力", "问题", "支持",
}


def load_profiles() -> dict:
    if not PROFILE_PATH.exists():
        return {}
    return json.loads(PROFILE_PATH.read_text(encoding="utf-8"))


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


def term_present(term: str, text: str, profiles: dict) -> bool:
    aliases = set(TERM_ALIASES.get(term, (term,)))
    for profile in profiles.values():
        if term in profile.get("keywords", []):
            aliases.add(term)
    low = text.lower()
    return any(alias.lower() in low for alias in aliases)


def extract_terms(jd: str, profiles: dict) -> list[str]:
    text = jd.lower()
    terms = {term for term in TERM_ALIASES if term_present(term, text, profiles)}
    for profile in profiles.values():
        for term in profile.get("keywords", []):
            if term_present(term, text, profiles):
                terms.add(term)
    return sorted(terms)


def detect_job_family(jd: str, profiles: dict, explicit: str | None) -> tuple[str, float, str]:
    if explicit and explicit in profiles:
        return explicit, 1.0, profiles[explicit].get("label", explicit)
    best_key = "backend" if "backend" in profiles else next(iter(profiles), "backend")
    best_count = -1
    for key, profile in profiles.items():
        count = sum(1 for term in profile.get("keywords", []) if term_present(term, jd, profiles))
        if count > best_count:
            best_key, best_count = key, count
    profile = profiles.get(best_key, {})
    confidence = best_count / max(1, len(profile.get("keywords", [])))
    return best_key, round(min(1.0, confidence), 3), profile.get("label", best_key)


def tokenize(text: str) -> list[str]:
    low = text.lower()
    tokens = re.findall(r"[a-z][a-z0-9+#./-]{1,}", low)
    for chunk in re.findall(r"[\u4e00-\u9fff]{2,}", low):
        tokens.extend(chunk[i:i + 2] for i in range(max(1, len(chunk) - 1)))
    return [token for token in tokens if token not in STOPWORDS and len(token) > 1]


def vectorize(documents: list[str]) -> list[dict[str, float]]:
    tokenized = [tokenize(doc) for doc in documents]
    if not tokenized:
        return []
    df = Counter()
    for tokens in tokenized:
        df.update(set(tokens))
    total = len(tokenized)
    vectors: list[dict[str, float]] = []
    for tokens in tokenized:
        counts = Counter(tokens)
        length = max(1, sum(counts.values()))
        vector = {term: (count / length) * (math.log((total + 1) / (df[term] + 1)) + 1.0) for term, count in counts.items()}
        norm = math.sqrt(sum(value * value for value in vector.values())) or 1.0
        vectors.append({term: value / norm for term, value in vector.items()})
    return vectors


def cosine(left: dict[str, float], right: dict[str, float]) -> float:
    if not left or not right:
        return 0.0
    return sum(value * right.get(term, 0.0) for term, value in left.items())


def parse_date(value: str | None, fallback: Path) -> date | None:
    if value:
        for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
            try:
                return datetime.strptime(value, fmt).date()
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


def score_projects(vaults: list[Path], jd: str, today: date, top: int, job_family: str | None, include_private: bool, config: dict) -> dict:
    profiles = load_profiles()
    family, confidence, family_label = detect_job_family(jd, profiles, job_family)
    weights = profiles.get(family, {}).get("weights", {"coverage": 0.45, "semantic": 0.15, "evidence": 0.20, "ownership": 0.10, "recency": 0.10})
    terms = extract_terms(jd, profiles)

    projects: list[dict] = []
    texts: list[str] = []
    for vault in vaults:
        for path in iter_markdown(vault, config, include_private=include_private):
            rel = path.relative_to(vault).as_posix()
            if not any(marker in rel for marker in PROJECT_DIR_MARKERS):
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            texts.append(text)
            projects.append({"path": path, "vault": vault, "rel": rel, "text": text})

    vectors = vectorize([jd] + texts)
    jd_vector = vectors[0] if vectors else {}
    scored: list[dict] = []
    for index, project in enumerate(projects, start=1):
        text = project["text"]
        fm = parse_frontmatter(text)
        matched = [term for term in terms if term_present(term, text, profiles)]
        missing = [term for term in terms if term not in matched]
        coverage = len(matched) / len(terms) if terms else 0.0
        semantic = cosine(jd_vector, vectors[index]) if index < len(vectors) else 0.0
        evidence = evidence_score(text, fm)
        ownership = ownership_score(text)
        project_date = parse_date(fm.get("last_verified") or fm.get("date"), project["path"])
        recency = recency_score(project_date, today)
        score = round(100 * (
            weights.get("coverage", 0.45) * coverage
            + weights.get("semantic", 0.15) * semantic
            + weights.get("evidence", 0.20) * evidence
            + weights.get("ownership", 0.10) * ownership
            + weights.get("recency", 0.10) * recency
        ), 1)
        recommendation = "main" if score >= 70 else "supporting" if score >= 45 else "skip"
        display_path = project["rel"] if len(vaults) == 1 else f"{project['vault'].name}/{project['rel']}"
        scored.append({
            "title": project_title(project["path"], text),
            "path": display_path,
            "score": score,
            "recommendation": recommendation,
            "coverage": round(coverage, 4),
            "semantic_score": round(semantic, 4),
            "evidence_score": round(evidence, 2),
            "ownership_score": round(ownership, 2),
            "recency_score": round(recency, 2),
            "matched_terms": matched,
            "missing_terms": missing,
            "ats_keywords": matched,
            "date": project_date.isoformat() if project_date else "",
        })
    scored.sort(key=lambda item: (-item["score"], item["title"].lower()))
    return {
        "vaults": [str(vault) for vault in vaults],
        "job_family": family,
        "job_family_label": family_label,
        "profile_confidence": confidence,
        "weights": weights,
        "jd_terms": terms,
        "ats_keywords": terms,
        "top": scored[:top],
        "all_projects": scored,
    }


def print_summary(result: dict) -> None:
    print(f"Job family: {result['job_family_label']} ({result['job_family']}, confidence {result['profile_confidence']})")
    print("JD terms:", ", ".join(result["jd_terms"]) or "(none detected)")
    print("Ranked projects:")
    for item in result["top"]:
        print(f"- {item['score']:5.1f}  {item['recommendation']:10s}  {item['title']}  ({item['path']})")
        print(f"          coverage={item['coverage']:.2f} semantic={item['semantic_score']:.2f} evidence={item['evidence_score']:.2f}")
        print(f"          matched: {', '.join(item['matched_terms']) or '-'}")
        print(f"          missing: {', '.join(item['missing_terms']) or '-'}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Rank career-vault projects against a JD.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--jd-file", help="Path to a JD text or Markdown file")
    source.add_argument("--jd-text", help="JD text")
    parser.add_argument("--vault", action="append", default=None, help="Career vault path; repeat for multiple vaults")
    parser.add_argument("--config", default=None, help="Path to career-vault.yaml or career-vault.json")
    parser.add_argument("--include-private", action="store_true", help="Include files matching private_globs")
    parser.add_argument("--job-family", default=None, help="Force backend, payment, platform, agent, or fullstack")
    parser.add_argument("--top", type=int, default=5)
    parser.add_argument("--today", default=None, help="Override today's date (YYYY-MM-DD) for deterministic tests")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    jd = Path(args.jd_file).read_text(encoding="utf-8", errors="replace") if args.jd_file else args.jd_text
    today = datetime.strptime(args.today, "%Y-%m-%d").date() if args.today else date.today()
    try:
        vaults, config = resolve_vaults(args.vault, args.config)
        result = score_projects(vaults, jd or "", today, max(1, args.top), args.job_family, args.include_private, config)
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print_summary(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
