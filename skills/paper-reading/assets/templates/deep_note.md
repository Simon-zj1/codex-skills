# {{TITLE}}：结构化深读

## 0. 速览

- `paper_id`：{{PAPER_ID}}
- 发布：{{VENUE_YEAR}}
- 领域：{{DOMAIN}}
- 阅读版本：{{VERSION}}
- 一句话总结：{{ONE_SENTENCE_TAKEAWAY}}
- 推荐阅读等级：{{READING_LEVEL}}

## 1. 研究问题

### 1.1 问题背景

{{BACKGROUND}}

### 1.2 现有方法的缺口

{{GAP}}

### 1.3 论文的核心假设

- {{ASSUMPTION_1}}
- {{ASSUMPTION_2}}

## 2. 核心思想

{{CORE_IDEA}}

用非领域语言解释：

{{PLAIN_LANGUAGE_EXPLANATION}}

## 3. 方法

### 3.1 总体流程

```mermaid
flowchart LR
    A[{{INPUT}}] --> B[{{STATE_REPRESENTATION}}]
    B --> C[{{PLANNER_MODEL_POLICY}}]
    C --> D[{{ACTION_OR_OUTPUT}}]
    D --> E[{{FEEDBACK_OR_ENVIRONMENT}}]
    E --> B
```

### 3.2 关键模块

| 模块 | 作用 | 输入/输出 | 关键设计 | 证据定位 |
|---|---|---|---|---|
| {{MODULE}} | {{PURPOSE}} | {{IO}} | {{DESIGN}} | {{LOCATION}} |

### 3.3 训练或推理目标

{{OBJECTIVE}}

### 3.4 关键实现细节

- 模型 / 策略：{{MODEL}}
- 参数量与推理硬件：{{COMPUTE}}
- 动作空间或输出空间：{{ACTION_SPACE}}
- 上下文、记忆或历史窗口：{{CONTEXT}}
- 超参数与训练预算：{{TRAINING_BUDGET}}

## 4. 数据、环境和实验

### 4.1 数据

| 数据来源 | 规模 | 采集方式 | 任务/场景覆盖 | 潜在偏差 |
|---|---|---|---|---|
| {{DATA}} | {{SIZE}} | {{COLLECTION}} | {{COVERAGE}} | {{BIAS}} |

### 4.2 环境与机器人设置

{{ENVIRONMENT}}

### 4.3 基线

| 基线 | 为什么合理 | 是否公平比较 | 证据定位 |
|---|---|---|---|
| {{BASELINE}} | {{WHY}} | {{FAIRNESS}} | {{LOCATION}} |

### 4.4 指标

{{METRICS}}

## 5. 结果

### 5.1 主结果

| 任务/环境 | 方法结果 | 最强基线 | 绝对提升 | 相对提升 | 定位 |
|---|---:|---:|---:|---:|---|
| {{TASK}} | {{RESULT}} | {{BASELINE_RESULT}} | {{ABS_GAIN}} | {{REL_GAIN}} | {{LOCATION}} |

### 5.2 消融

| 移除或改变的组件 | 影响 | 说明核心机制是否必要 | 定位 |
|---|---|---|---|
| {{ABLATION}} | {{EFFECT}} | {{INTERPRETATION}} | {{LOCATION}} |

### 5.3 泛化、真机或失败分析

{{GENERALIZATION_AND_FAILURES}}

## 6. 图表解读

### 图 1：{{FIGURE_TITLE}}

- 来源：{{FIGURE_LOCATION}}
- 它展示什么：{{FIGURE_CONTENT}}
- 它支持什么结论：{{FIGURE_CLAIM}}
- 证据强度：{{FIGURE_EVIDENCE}}
- 需要注意：{{FIGURE_CAVEAT}}

### 表 1：{{TABLE_TITLE}}

- 来源：{{TABLE_LOCATION}}
- 关键数字：{{TABLE_NUMBERS}}
- 公平性检查：{{TABLE_FAIRNESS}}
- 遗漏信息：{{TABLE_MISSING}}

## 7. 批判性评估

### 7.1 强证据

- {{STRONG_EVIDENCE}}

### 7.2 中等或弱证据

- {{WEAK_EVIDENCE}}

### 7.3 作者结论是否超出证据

{{OVERCLAIM_ASSESSMENT}}

### 7.4 可复现性

{{REPRODUCIBILITY}}

### 7.5 安全、成本和部署风险

{{SAFETY_COST_RISK}}

## 8. 与相关工作的关系

| 相关工作 | 与本文关系 | 本文真正增量 | 是否被公平比较 |
|---|---|---|---|
| {{RELATED_WORK}} | {{RELATION}} | {{DELTA}} | {{COMPARISON}} |

## 9. 可迁移点

### 可复用的机制

- {{REUSABLE_MECHANISM}}

### 可复用的数据或评测

- {{REUSABLE_EVAL}}

### 不适合直接迁移的部分

- {{NON_TRANSFERABLE}}

## 10. 未解决问题

1. {{OPEN_QUESTION_1}}
2. {{OPEN_QUESTION_2}}
3. {{OPEN_QUESTION_3}}

## 11. 最小验证实验

| 想验证的假设 | 最小实验 | 成功标准 | 预估成本 |
|---|---|---|---|
| {{HYPOTHESIS}} | {{EXPERIMENT}} | {{SUCCESS_CRITERION}} | {{COST}} |

## 12. 结论

{{FINAL_ASSESSMENT}}
