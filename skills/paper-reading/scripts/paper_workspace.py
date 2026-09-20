#!/usr/bin/env python3
"""Initialize, inspect, and validate paper-reading records."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


SKILL_ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = SKILL_ROOT / "assets" / "templates"
CONFIG_PATH = SKILL_ROOT / "assets" / "reading_profile.json"
PAPER_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]+$")

OUTPUT_TEMPLATE_MAP = {
    "00_one_page.md": "one_page.md",
    "01_deep_note.md": "deep_note.md",
    "mindmap.mmd": "mindmap.mmd",
    "deck_storyboard.md": "deck_storyboard.md",
}


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def resolve_workspace(args: argparse.Namespace) -> Path:
    return Path(args.workspace).expanduser().resolve()


def get_library(args: argparse.Namespace) -> Path:
    return resolve_workspace(args) / "papers" / "library"


def get_outputs(args: argparse.Namespace) -> Path:
    return resolve_workspace(args) / "outputs"


def load_config() -> dict[str, Any]:
    with CONFIG_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def replace_placeholders(text: str, values: dict[str, str]) -> str:
    for key, value in values.items():
        text = text.replace("{{" + key + "}}", value)
    return text


def init_paper(args: argparse.Namespace) -> int:
    paper_id = args.paper_id.strip().lower()
    if not PAPER_ID_RE.fullmatch(paper_id):
        print(
            "paper_id 必须是小写字母、数字和连字符，例如 yao-2022-react。",
            file=sys.stderr,
        )
        return 2

    paper_dir = get_library(args) / paper_id
    output_dir = get_outputs(args) / paper_id
    if paper_dir.exists() and not args.force:
        print(f"已存在：{paper_dir}。如需补齐缺失文件，请加 --force。", file=sys.stderr)
        return 2

    for directory in (
        paper_dir / "source",
        paper_dir / "extracted",
        output_dir,
    ):
        directory.mkdir(parents=True, exist_ok=True)

    timestamp = now_iso()
    meta_path = paper_dir / "meta.json"
    if not meta_path.exists() or args.force:
        write_json(
            meta_path,
            {
                "paper_id": paper_id,
                "title": args.title,
                "authors": [],
                "year": args.year,
                "venue": None,
                "domain": args.domain,
                "paper_type": args.paper_type,
                "status": "inbox",
                "source": {
                    "url_or_path": args.source,
                    "arxiv_id": args.arxiv_id,
                    "doi": args.doi,
                    "version": args.version,
                    "accessed_at": None,
                },
                "artifacts": {
                    "code": None,
                    "data": None,
                    "project_page": None,
                },
                "created_at": timestamp,
                "updated_at": timestamp,
            },
        )

    evidence_path = paper_dir / "evidence.jsonl"
    if not evidence_path.exists():
        evidence_path.write_text("", encoding="utf-8")

    values = {
        "TITLE": args.title,
        "PAPER_ID": paper_id,
        "DOMAIN": args.domain,
        "PAPER_TYPE": args.paper_type,
        "YEAR_VENUE": str(args.year or ""),
        "VERSION_SOURCE": args.version or args.source,
    }

    for output_name, template_name in OUTPUT_TEMPLATE_MAP.items():
        destination = output_dir / output_name
        if destination.exists() and not args.force:
            continue
        template = (TEMPLATES / template_name).read_text(encoding="utf-8")
        destination.write_text(
            replace_placeholders(template, values),
            encoding="utf-8",
        )

    readme_path = paper_dir / "README.md"
    if not readme_path.exists():
        readme_path.write_text(
            "\n".join(
                [
                    f"# {args.title}",
                    "",
                    "## 目录",
                    "",
                    "- `source/`：原始 PDF 或网页快照",
                    "- `extracted/`：解析后的 Markdown、图表和公式",
                    "- `meta.json`：元数据",
                    "- `evidence.jsonl`：证据链",
                    "",
                    f"- 输出目录：`outputs/{paper_id}/`",
                    "",
                ]
            ),
            encoding="utf-8",
        )

    print(f"已初始化 {paper_id}")
    print(f"论文目录：{paper_dir}")
    print(f"输出目录：{output_dir}")
    return 0


def list_records(args: argparse.Namespace) -> list[tuple[str, dict[str, Any], Path]]:
    library = get_library(args)
    if not library.exists():
        return []

    records: list[tuple[str, dict[str, Any], Path]] = []
    for meta_path in sorted(library.glob("*/meta.json")):
        try:
            with meta_path.open("r", encoding="utf-8") as handle:
                meta = json.load(handle)
        except (OSError, json.JSONDecodeError):
            meta = {"paper_id": meta_path.parent.name, "title": "<invalid meta>"}
        records.append((meta_path.parent.name, meta, meta_path))
    return records


def status(args: argparse.Namespace) -> int:
    records = list_records(args)
    if not records:
        print("论文库为空。")
        return 0

    print(f"{'paper_id':32} {'domain':10} {'status':12} title")
    print("-" * 100)
    for paper_id, meta, _ in records:
        print(
            f"{paper_id[:32]:32} "
            f"{str(meta.get('domain', '?'))[:10]:10} "
            f"{str(meta.get('status', '?'))[:12]:12} "
            f"{meta.get('title', '?')}"
        )
    return 0


def add_evidence(args: argparse.Namespace) -> int:
    paper_dir = get_library(args) / args.paper_id
    if not paper_dir.exists():
        print(f"论文不存在：{paper_dir}", file=sys.stderr)
        return 2

    record = {
        "claim": args.claim,
        "origin": args.origin,
        "evidence_type": args.evidence_type,
        "location": args.location,
        "quote_or_paraphrase": args.text,
        "value": args.value,
        "confidence": args.confidence,
        "notes": args.notes,
    }
    required = ("claim", "origin", "evidence_type", "location", "quote_or_paraphrase")
    missing = [key for key in required if not record.get(key)]
    if missing:
        print(f"缺少字段：{', '.join(missing)}", file=sys.stderr)
        return 2

    evidence_path = paper_dir / "evidence.jsonl"
    with evidence_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"已追加 1 条证据到 {evidence_path}")
    return 0


def validate_paper(args: argparse.Namespace) -> int:
    paper_id = args.paper_id
    paper_dir = get_library(args) / paper_id
    output_dir = get_outputs(args) / paper_id
    errors: list[str] = []
    warnings: list[str] = []

    if not paper_dir.exists():
        errors.append(f"论文目录不存在：{paper_dir}")
    if not output_dir.exists():
        errors.append(f"输出目录不存在：{output_dir}")

    meta_path = paper_dir / "meta.json"
    if not meta_path.exists():
        errors.append("缺少 meta.json")
    else:
        try:
            with meta_path.open("r", encoding="utf-8") as handle:
                meta = json.load(handle)
            for field in ("paper_id", "title", "domain", "status", "source", "created_at"):
                if field not in meta:
                    errors.append(f"meta.json 缺少字段：{field}")
        except json.JSONDecodeError as exc:
            errors.append(f"meta.json 不是合法 JSON：{exc}")

    evidence_path = paper_dir / "evidence.jsonl"
    evidence_count = 0
    if not evidence_path.exists():
        errors.append("缺少 evidence.jsonl")
    else:
        for line_number, line in enumerate(
            evidence_path.read_text(encoding="utf-8").splitlines(),
            start=1,
        ):
            if not line.strip():
                continue
            evidence_count += 1
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(f"evidence.jsonl 第 {line_number} 行不是合法 JSON：{exc}")
                continue
            for field in (
                "claim",
                "origin",
                "evidence_type",
                "location",
                "quote_or_paraphrase",
                "confidence",
            ):
                if field not in record:
                    errors.append(
                        f"evidence.jsonl 第 {line_number} 行缺少字段：{field}"
                    )
        if evidence_count == 0:
            warnings.append("evidence.jsonl 为空，尚未形成证据链")

    config = load_config()
    minimum_claims = int(config["evidence_policy"]["minimum_key_claims"])
    if 0 < evidence_count < minimum_claims:
        warnings.append(
            f"当前证据记录 {evidence_count} 条，建议至少 {minimum_claims} 条"
        )

    for output_name in config["default_outputs"]:
        path = output_dir / output_name
        if not path.exists():
            errors.append(f"缺少输出文件：{output_name}")
            continue
        text = path.read_text(encoding="utf-8")
        if "{{" in text or "}}" in text:
            errors.append(f"仍有未替换占位符：{output_name}")
        if path.stat().st_size < 50:
            warnings.append(f"文件内容过短：{output_name}")

    print(f"校验：{paper_id}")
    print(f"- 证据记录：{evidence_count}")
    for warning in warnings:
        print(f"- 警告：{warning}")
    if errors:
        for error in errors:
            print(f"- 错误：{error}")
        return 1

    print("- 结果：通过")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Initialize, inspect, and validate paper-reading records."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="初始化一篇论文")
    init_parser.add_argument(
        "--workspace",
        type=Path,
        default=Path.cwd(),
        help="项目工作区，默认当前目录",
    )
    init_parser.add_argument("--paper-id", required=True)
    init_parser.add_argument("--title", required=True)
    init_parser.add_argument("--source", required=True)
    init_parser.add_argument(
        "--domain",
        choices=("agent", "robotics", "general"),
        default="general",
    )
    init_parser.add_argument(
        "--paper-type",
        choices=(
            "method",
            "system",
            "benchmark",
            "survey",
            "position",
            "empirical",
            "unknown",
        ),
        default="unknown",
    )
    init_parser.add_argument("--year", type=int)
    init_parser.add_argument("--arxiv-id")
    init_parser.add_argument("--doi")
    init_parser.add_argument("--version")
    init_parser.add_argument("--force", action="store_true")
    init_parser.set_defaults(func=init_paper)

    status_parser = subparsers.add_parser("status", help="查看论文库状态")
    status_parser.add_argument(
        "--workspace",
        type=Path,
        default=Path.cwd(),
        help="项目工作区，默认当前目录",
    )
    status_parser.set_defaults(func=status)

    evidence_parser = subparsers.add_parser("add-evidence", help="追加一条证据")
    evidence_parser.add_argument(
        "--workspace",
        type=Path,
        default=Path.cwd(),
        help="项目工作区，默认当前目录",
    )
    evidence_parser.add_argument("paper_id")
    evidence_parser.add_argument("--claim", required=True)
    evidence_parser.add_argument(
        "--origin",
        choices=("paper_claim", "our_assessment", "external_context"),
        default="paper_claim",
    )
    evidence_parser.add_argument(
        "--type",
        dest="evidence_type",
        choices=(
            "problem",
            "assumption",
            "method",
            "implementation",
            "dataset",
            "metric",
            "result",
            "ablation",
            "limitation",
            "reproduction",
            "claim",
        ),
        required=True,
    )
    evidence_parser.add_argument("--location", required=True)
    evidence_parser.add_argument("--text", required=True)
    evidence_parser.add_argument("--value")
    evidence_parser.add_argument(
        "--confidence",
        choices=("high", "medium", "low", "unverified"),
        default="medium",
    )
    evidence_parser.add_argument("--notes")
    evidence_parser.set_defaults(func=add_evidence)

    validate_parser = subparsers.add_parser("validate", help="校验论文输出")
    validate_parser.add_argument(
        "--workspace",
        type=Path,
        default=Path.cwd(),
        help="项目工作区，默认当前目录",
    )
    validate_parser.add_argument("paper_id")
    validate_parser.set_defaults(func=validate_paper)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
