# CLAUDE.md

This file provides repository-level guidance for Claude Code when working in this repository.

## 仓库定位

这是 `product-research` Claude Code Skill 的开发仓库，用于评估候选产品是否适合跨境电商；它不是普通应用。

主要职责分为：

* **Skill 层**：`SKILL.md`、`references/`、`docs/`，定义 Agent 的研究流程、证据规则、评分与输出契约。
* **确定性引擎层**：`product_research/`，负责 Evidence 处理、领域分析、Unit Economics、评分与决策等确定性逻辑。
* **OpenSpec 层**：`openspec/specs/` 定义 living specifications，`openspec/changes/` 定义正在规划或实施的行为变化。

不要在本文件维护当前已实现 / 未实现能力清单。能力状态以 `SKILL.md`、OpenSpec、代码和测试为准。

## 修改前先确认事实

进行设计或代码修改前，按任务范围检查：

1. 相关 OpenSpec living spec。
2. 相关 active change。
3. 当前实现和测试。
4. `SKILL.md` 及相关 `references/` 中的 runtime contract。

Active change 表示相对 living spec 的预期变化；代码和测试表示当前实际实现。

如果 OpenSpec、Skill 文档、代码或测试之间存在无法解释的冲突，不要静默假设其中一方正确。明确指出冲突，并在修改时保持相关契约同步。

## 核心工程约束

### Deterministic core

`product_research/` 中的确定性分析、计算和决策逻辑必须保持可重复：

* 不依赖网络、系统时钟或随机源。
* 金额、权重和评分等精确计算使用 `Decimal`，沿用现有 rounding semantics。
* 不在 deterministic engine 中隐式执行外部 research 或 provider acquisition。

### Fail closed

缺失、异常、无效或无法判定的输入必须产生明确的结构化失败或 unresolved 状态。

不得：

* 把缺失值当作 `0`。
* 把未知事实推断成已知事实。
* 因异常而静默降级为成功结果。
* 为了得到完整评分或结论而补造输入。

### Immutable domain values

沿用现有 immutable value-object / closed-vocabulary 模式。

构造时完成合法性校验；创建后不得修改值。

不要无必要扩大公开词汇表、公开 API 或模块职责。

### Preserve architecture boundaries

保持现有 acquisition、Evidence、assessment、domain analysis、Unit Economics、scoring / decision 的职责边界和依赖方向。

特别注意：

* acquisition 中间值不等同于规范化 `Evidence`。
* 分析模块只消费调用方明确提供的语义和既有 Evidence，不自行推断未声明业务含义。
* 不擅自改写 Evidence 的 confidence、status 或 provenance。
* 分析模块不执行外部 research，也不自行生成缺乏依据的评分或 policy inputs。
* 不绕过既有 contract，不引入反向依赖或跨层职责泄漏。

## 测试

运行全部自动化测试：

```bash
python3 -m unittest discover -s tests
```

运行单个测试模块：

```bash
python3 -m unittest tests.test_scoring_decision
```

测试以 contract-style `unittest` 为主，重点保护：

* closed vocabulary
* immutable values
* deterministic behavior
* fail-closed semantics
* public contract
* boundary behavior

修改行为时优先增加或更新表达契约的测试，而不是只验证 happy path。

`tests/scenarios.md` 是 Agent 行为的 RED / GREEN 场景测试协议，不是自动化单元测试。

沿用当前测试和依赖体系；除非相关变更明确需要，否则不要为局部实现引入新的测试框架或第三方依赖。

## OpenSpec 工作流

仓库采用 spec-driven OpenSpec workflow。

对于新增能力、行为变化或 contract 变化：

1. 先检查相关 living spec 和 active changes。
2. 在实现前创建或更新对应 OpenSpec change。
3. proposal / planning 阶段只定义问题、范围、设计和任务，不修改项目实现。
4. implementation 阶段按 change 修改代码和测试。
5. 完成后验证代码、测试、living spec、`SKILL.md` 和相关 `references/` 是否保持一致，再归档 change。

当实现改变实际 capability boundary 时，必须同步检查 Skill contract、OpenSpec 和测试。

不要在 `CLAUDE.md` 中复制 OpenSpec 已经定义的 command、workflow 或 artifact 规则。

## 语言约定

* 面向用户的输出和 Skill 文档默认使用中文。
* 代码、标识符、测试和 OpenSpec artifacts 默认使用英文，并遵循现有仓库风格。

## CLAUDE.md 维护原则

本文件只保存长期稳定、会直接影响 Agent 开发行为的 repository-level constraints。

不要加入容易随单个迭代过期的信息，例如：

* 当前 active change 名称。
* 当前未实现能力清单。
* 临时 roadmap 或 milestone 状态。
* 本地工具生成的 command 路径。
* 可直接从代码目录推导出的完整文件清单。
* 某个阶段暂时成立的 implementation snapshot。

如果某项规则已经由 OpenSpec、`SKILL.md`、reference 或测试精确定义，应避免在这里复制其详细内容。