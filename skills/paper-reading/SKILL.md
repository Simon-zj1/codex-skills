---
name: paper-reading
description: Read, critique, synthesize, and visualize papers with page/section/figure-level evidence. Use for rapid screening, single-paper deep reads, multi-paper reviews, or paper-derived PDF, PPT, poster, and mind-map deliverables.
---

# 论文阅读工作流

把论文输入转成可核验、可复用的理解材料。默认不是生成一段摘要，而是建立证据链、结构化深读，并按用途生成不同交付物。

## 适用场景

用户提供 arXiv/DOI/论文链接、PDF、论文题目、论文首页截图或一组相关论文，并要求阅读、快速判断、精读、复现分析、方法迁移、多篇综述、PPT、PDF、海报或思维导图时使用。

只做翻译、格式转换，或用户已提供全文且明确不需要分析时，不启用本工作流。

## 核心约束

1. 先证据，后结论。关键结论尽量绑定 `p.5, Sec.3.2, Fig.4, Table 2` 一类准确定位。
2. 区分 `paper_claim`、`our_assessment` 和 `external_context`。不要把自己的推断写成作者结论。
3. 不编造数据集、指标、参数、硬件、基线、提示词或引用。无法确认时明确写“论文未明确”或“解析不确定”。
4. 数值必须回查正文或原表。比较提升时同时给出绝对值和相对值，并检查基线与预算是否公平。
5. 图表要说明“它证明了什么、证据强度如何、是否真正支持正文结论”，不能只复述图题。
6. 机器人、具身智能或 Agent 论文必须加载对应领域清单。
7. 多篇论文必须建立横向矩阵并分析共识、分歧、方法演化和研究空白，不能拼接摘要。
8. 任何重量级 PDF、PPT 或海报在交付前都要逐页渲染，检查引用、溢出、重叠和图像真实性。

## 执行流程

1. 归一化输入：识别版本、标题、作者、年份、venue、论文类型、领域和官方代码/数据/项目页。
2. 确定工作区：优先复用当前项目中已有的 `papers/library/`、`outputs/`、`evidence.jsonl` 和论文模板；没有时再初始化。
3. 分配稳定 `paper_id`，格式采用 `firstauthor-year-shorttitle`。原始文件放入 `papers/library/<paper_id>/source/`，解析结果放入 `extracted/`。
4. 检查解析完整性：正文、方法、实验、结论、图表标题和页码必须可追溯；抽查数字能回查原文后再进入深读。
5. 建立证据链 `papers/library/<paper_id>/evidence.jsonl`，至少覆盖问题、假设、方法、实现、数据、指标、主结果、消融、限制和复现信息。
6. 重建论文：问题 -> 缺口 -> 假设 -> 方法链 -> 数据与实验 -> 结果 -> 失败边界 -> 贡献与可迁移点。
7. 执行批判复核，把判断归入 `强证据`、`中等证据`、`弱证据` 或 `未验证`，并检查最强基线、数据规模、算力、长程/分布外、方差和负面结果。
8. 生成用户要求的输出，并运行交付前质量门槛。

需要完整解析门、证据字段、批判问题和质量门槛时，阅读 [references/workflow.md](references/workflow.md)。

## 领域路由

- 阅读 Agent、机器人、具身智能论文时，必须阅读 [references/agent-robotics-taxonomy.md](references/agent-robotics-taxonomy.md)。
- 其他领域使用通用维度：问题、缺口、假设、方法、数据、基线、指标、消融、限制和复现。

## 输出模式

- 用户未指定格式：生成 `00_one_page.md`、`01_deep_note.md`、`mindmap.mmd`、`deck_storyboard.md`，并保留 `evidence.jsonl`。
- 快速判断：只生成一页卡，但仍保留关键结论定位和证据强弱。
- 复现导向：增加环境、数据、训练、指标、成本、代码和数据缺口清单。
- 方法迁移：增加可迁移机制、适配假设、不可迁移部分和最小验证实验。
- 多篇综述：生成 `multi_paper_matrix.md`、`synthesis.md`、`research_gaps.md` 和 `reading_order.md`。
- 输出 PDF/PPT/海报/思维导图：先完成深读包，再按论点重新组织，不复用摘要换皮。

输出模板位于 `assets/templates/`。生成 PDF 时使用 `pdf` 技能，生成 PPT 时使用 `presentations` 技能，生成 DOCX 时使用 `documents` 技能；需要原创视觉资产时使用 `imagegen`，但论文原始图表必须保留来源页码和图号。

## 工作区脚本

需要初始化、查看或校验论文记录时，运行本 Skill 的 `scripts/paper_workspace.py`。脚本默认以当前目录为工作区，也可以显式传入 `--workspace`。

```bash
python3 scripts/paper_workspace.py init \
  --workspace "$PWD" \
  --paper-id yao-2022-react \
  --title "ReAct: Synergizing Reasoning and Acting in Language Models" \
  --source "https://arxiv.org/abs/2210.03629" \
  --domain agent

python3 scripts/paper_workspace.py status --workspace "$PWD"
python3 scripts/paper_workspace.py validate --workspace "$PWD" yao-2022-react
```

脚本只负责稳定目录、元数据、模板和格式检查，不能替代对论文内容和证据的阅读。
