# Codex Skills

我在 [Codex](https://openai.com/codex) 里日常使用的自建 skill 合集。每个 skill 是一个独立目录，包含一份 `SKILL.md`（技能说明与执行规则），以及按需加载的 `references/`、`scripts/`、`assets/`。

这些 skill 解决的都不是「AI 不够聪明」，而是「默认问法得不到好结果」：问题问得太大、资料太多挑不出来、读完论文只剩模糊印象、链接懒得点开。把固定的工作流沉淀成 skill，以后一句话就能复用。

## 包含的 skill

| Skill | 用途 | 触发方式 |
| --- | --- | --- |
| [learn-anything](skills/learn-anything) | 把 Codex 当私人老师系统学一个新领域：学习阶梯、最关键的 20%、考官式测验、一页速查表、资源筛选、费曼复述 | 显式调用 `$learn-anything` |
| [paper-reading](skills/paper-reading) | 论文阅读工作流：证据链、结构化深读，并生成一页纸、深读笔记、综述矩阵、PPT、思维导图等交付物 | 自动触发 |
| [link-digest](skills/link-digest) | 丢一个链接过来，抓正文、提炼精华、跟读文中引用的其他链接，结构化输出 | 自动触发 |
| [optimize-prompt](skills/optimize-prompt) | 回答前先把问题改写成更能激发高质量回答的提示词，展示改写版再作答 | 自动触发 |

## 安装

前提：本机已安装 Codex，个人 skill 目录为 `~/.codex/skills`（若设置了 `CODEX_HOME`，则以它为准）。

### 方式一：一键安装（推荐）

```bash
git clone https://github.com/Simon-zj1/codex-skills.git
cd codex-skills
./scripts/install.sh
```

默认用**软链接**安装，之后 `git pull` 就能直接更新已装的 skill。

```bash
./scripts/install.sh --copy                       # 改为复制安装
./scripts/install.sh learn-anything link-digest   # 只安装指定 skill
./scripts/install.sh --force                      # 覆盖已存在的同名 skill（先自动备份）
```

脚本不会删除任何东西：遇到同名目录默认跳过，`--force` 时把原目录重命名为 `.bak-<时间戳>` 备份。

### 方式二：手动安装

```bash
cp -R skills/learn-anything ~/.codex/skills/
```

安装后重启 Codex 应用即可在 skill 列表中看到。

## 目录结构

```text
codex-skills/
|-- README.md
|-- LICENSE
|-- scripts/
|   `-- install.sh          把 skills/ 下的 skill 安装到 ~/.codex/skills
`-- skills/
    |-- learn-anything/
    |   |-- SKILL.md
    |   |-- agents/openai.yaml
    |   `-- references/     playbooks.md（六种模式的做法）、tracking.md（跨会话进度）
    |-- paper-reading/
    |   |-- SKILL.md
    |   |-- assets/         模板与 schema
    |   |-- references/     工作流与领域分类
    |   `-- scripts/        paper_workspace.py
    |-- link-digest/
    `-- optimize-prompt/
```

## 写一个新 skill

结构约定和上面一致，最小形态只需要一个目录加一份 `SKILL.md`：

```markdown
---
name: my-skill
description: 一句话说明它做什么、什么时候该用；再补一句什么时候不该用。
---

# My Skill

（面向 AI 的执行规则：目标、不可违反的约束、输出结构）
```

几条实践经验：

- **description 决定要不要触发**，写清适用场景，并顺手排除最容易混淆的相邻场景。
- **正文只写会改变决策的东西**，通用常识和重复铺垫删掉，长流程拆进 `references/`（用到才读）。
- **不想被自动触发就设 `agents/openai.yaml` 里的 `policy.allow_implicit_invocation: false`**，之后只响应显式调用 `$skill-name`。
- 让 AI 自己写 skill 时，可以直接用官方的 `skill-creator`。

## License

[MIT](LICENSE)。这些内容来自实际使用中的不断调整，欢迎取用和改写。
