#!/usr/bin/env bash
#
# 把本仓库中的 skill 安装到 Codex 个人 skills 目录。
#
#   ./scripts/install.sh                              全部安装（软链接，默认）
#   ./scripts/install.sh --copy                       复制安装
#   ./scripts/install.sh learn-anything link-digest   只安装指定 skill
#   ./scripts/install.sh --force                      覆盖同名 skill（先备份原目录）
#
# 安装目标是 ${CODEX_HOME:-$HOME/.codex}/skills。

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILLS_SRC="$REPO_ROOT/skills"
CODEX_HOME_DIR="${CODEX_HOME:-$HOME/.codex}"
DEST_ROOT="$CODEX_HOME_DIR/skills"

MODE="link"
FORCE=0
declare -a REQUESTED=()

usage() {
  sed -n '2,10p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
}

for arg in "$@"; do
  case "$arg" in
    --copy) MODE="copy" ;;
    --link) MODE="link" ;;
    --force) FORCE=1 ;;
    -h|--help) usage; exit 0 ;;
    -*) echo "未知参数：$arg" >&2; usage >&2; exit 1 ;;
    *) REQUESTED+=("$arg") ;;
  esac
done

if [[ ! -d "$SKILLS_SRC" ]]; then
  echo "找不到 skills 目录：$SKILLS_SRC" >&2
  exit 1
fi

if [[ ${#REQUESTED[@]} -gt 0 ]]; then
  TARGETS=("${REQUESTED[@]}")
else
  TARGETS=()
  for d in "$SKILLS_SRC"/*/; do
    [[ -d "$d" ]] || continue
    TARGETS+=("$(basename "$d")")
  done
fi

mkdir -p "$DEST_ROOT"

installed=0
skipped=0
missing=0

for name in "${TARGETS[@]}"; do
  src="$SKILLS_SRC/$name"
  dest="$DEST_ROOT/$name"

  if [[ ! -f "$src/SKILL.md" ]]; then
    echo "找不到 skill ${name}：${src} 下没有 SKILL.md" >&2
    missing=$((missing + 1))
    continue
  fi

  if [[ -e "$dest" || -L "$dest" ]]; then
    if [[ $FORCE -eq 1 ]]; then
      backup="$dest.bak-$(date +%Y%m%d%H%M%S)"
      mv "$dest" "$backup"
      echo "  已备份原目录 → ${backup}"
    else
      echo "跳过 ${name}：${dest} 已存在（加 --force 可覆盖，会先备份）"
      skipped=$((skipped + 1))
      continue
    fi
  fi

  if [[ "$MODE" == "copy" ]]; then
    cp -R "$src" "$dest"
    echo "已复制 ${name} → ${dest}"
  else
    ln -s "$src" "$dest"
    echo "已软链接 ${name} → ${dest}"
  fi
  installed=$((installed + 1))
done

echo
echo "完成：安装 ${installed} 个，跳过 ${skipped} 个。目标目录：${DEST_ROOT}"
echo "重启 Codex 应用后生效。"

if [[ $missing -gt 0 ]]; then
  echo "有 ${missing} 个指定名称在仓库中不存在。" >&2
  exit 1
fi
