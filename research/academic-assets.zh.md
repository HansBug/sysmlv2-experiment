# SysML v2 学术公开资产盘点

本清单只登记公开可下载、包含模型文件或明确关联模型文件的研究资产；论文只有在能追到仓库/压缩包时才列为“有模型资产”。版本、提交号和许可必须在复现实验中再次核对。当前已将官方 Pilot 的 `sysml/src` 示例纳入下一轮批处理。

| 资产 | 论文/项目用途 | 模型文件与入口 | 当前状态 |
|---|---|---|---|
| [GfSE/SysML-v2-Models](https://github.com/GfSE/SysML-v2-Models) | 工程领域示例 | `models/**/*.sysml`，本实验固定 `ebbb0c39f4813b059e0bf14270ec58618aa012ca` | 已下载 36 个；4 个语法有效含状态元素 |
| [SysTemp benchmark](https://github.com/yasminebouamra/SysMLv2-Benchmark)；论文 [arXiv:2506.21608](https://arxiv.org/abs/2506.21608) | SysML v2 文本生成/理解 benchmark | `data/**/*.sysml`，固定 `dd41357921f23020aacdaaa063e0a4b31fc0b2b4` | 已下载 243 个；20 个语法有效含状态元素，需按目录补上下文 |
| [Conformance-Driven Refinement](https://github.com/cmuchancel/NL-to-SysMLv2-via-Conformance-Driven-Refinement)；论文 [arXiv:2607.14162](https://arxiv.org/abs/2607.14162) | LLM 生成与一致性改进 | `Open-Source Dataset Release/* artifacts/**/*.sysml`，固定 `96c0e104f82a8da7a5edccca9b67040785b53bd3` | 已登记 1,043 个；正集仅 1 个文件含状态元素，负集主要是语法错误产物 |
| [SysMBench](https://arxiv.org/abs/2508.03215) | SysML v2 生成评测 | 论文提供 prompts/任务描述；模型资产需从作者链接逐项取得 | 作为论文索引登记；不把 prompt 当模型文件，不计入转换分母 |
| [OMG SysML v2 Pilot Implementation](https://github.com/Systems-Modeling/SysML-v2-Pilot-Implementation) | 官方参考实现与验证示例 | `sysml/src/**/*.sysml`、`sysml.library`；与官方 Pilot JAR 配套 | 固定 commit 含 255 个 `.sysml`，其中 16 个文件含 47 个通过源校验的状态根；事件映射后独立批次有 5 个 converted |
| [Airbus Apollo 11 SysML v2](https://github.com/airbus/apollo-11-sysml-v2) | 公开工程任务模型，包含 Apollo 11 任务阶段状态机 | 仓库固定提交 `6e9c93fe7d80c5ca3534bb14b10ab374a643ef2d`，`**/*.sysml`；MPL-2.0 | 已下载 28 个文件；官方 Pilot 项目加载 28/28 通过，识别 18 个状态根，其中 1 个任务阶段根含 15 个子状态和 14 条事件转移；typed `PerformActionUsage` 与 `initial` usage 已能通过 abstract hook/默认入口映射；结构化结果见 [`apollo11-action-observed.json`](apollo11-action-observed.json) |
| [Sensmetry Advent of SysML v2](https://github.com/sensmetry/advent-of-sysml-v2) | 公开教学与示例模型，包含 Santa Sleigh 巡航控制状态机 | 固定提交 `83ba1f692072c9dffd7cdf873e11ae1e4a4f833f`，`lesson*/models/**/*.sysml`；MIT | 已下载 44 个文件；4 个文件含状态元素；完整仓库项目加载 44 个文件时有 2 条校验错误，4 个状态根中 3 个为目标行为候选，分别因数据类型、结构成员和并行语义拒绝 |
| [The SysML v2 Book examples](https://github.com/MBSE4U/the-sysmlv2-book-examples)；书籍页面 [Leanpub](https://leanpub.com/sysmlv2) | 面向工程实践的公开书籍示例，含无人机系统及 use case 行为模型 | 固定提交 `3bb66343ec18a40f5f851b97b3a19b2a7cc1efc4`，`examples/**/*.sysml`；Apache-2.0 | 已下载 1 个模型并加入 CI；当前 Pilot 报告全局校验错误，未产生 typed 状态根，因此不能进入严格转换分母；这条结果本身作为版本/约束兼容性证据保留 |
| [SysML v2 Release](https://github.com/Systems-Modeling/SysML-v2-Release) | 官方规范、语法和示例发布 | release 中的 `sysml.library`、示例和测试模型 | 已核对 2026-07 版本差异；待纳入项目级批处理 |
| [sysml-2ls](https://github.com/sensmetry/sysml-2ls) | 2024 年前后的语言服务器/解析器 | 仓库 tests/examples 中的 `.sysml` | 已做定向状态/继承对照；作为旧前端比较，不作为主导入器 |
| [SysML v2 Textual Notation Specification](https://www.omg.org/spec/)。 | 语法/语义规范 | 规范附带示例片段，不一定是独立可执行工程 | 用于解释版本变化和构造调用规则；不计入模型覆盖 |

## 论文资产的登记规则

每个资产登记 `paper_doi_or_arxiv`、作者仓库 URL、固定提交号、模型文件 glob、许可证、下载日期、文件 SHA-256、是否含 `StateDefinition`/`StateUsage`、项目上下文目录和转换结果。论文的“有 SysML v2 任务”不能替代可下载模型证据；同一模型的 prompt、轨迹和生成变体要用哈希去重。

当前可直接进入状态转换实验的优先顺序是：Apollo 11 任务阶段根、Sensmetry Advent 教学状态机、官方 Pilot 工程示例、SysTemp 中按工程目录成组的状态文件、GfSE 中能完整加载的领域模型。Apollo 11 的 28 文件工程已经证明官方 typed AST 能完整加载跨文件模型；其阶段行为现在保留为 abstract hook，后续仍需针对 action 内部时序建立更强的 FCSTM 表示，不能把当前结构化转换当作执行等价。官方 Pilot 抽取结果见 [`official-pilot-observed.json`](official-pilot-observed.json)，事件映射后的全量结果见 [`events-observed.json`](events-observed.json)。Refinement 的负样本适合测语法/校验拒绝，不应作为正向转换覆盖率分母。SysMBench 先作为任务索引，待取得实际模型后再登记。

## 与本仓库转换的关系

`research/state-assets.zh.md` 是“语法树中含状态元素”的逐文件登记；本表是“学术来源/论文资产”登记。前者回答“哪些文件可追溯”，后者回答“为什么选择这些文件以及模型从哪里来”。只有在完整项目上下文加载、官方校验通过、typed 状态抽取成功并通过 FCSTM 语义检查后，才把资产标为 converted。

下一阶段批处理应对每个 `context_directory` 调用 [`ExtractProject.java`](../ExtractProject.java)，输出项目级源事实，再调用 `convert_corpus.py`；任何跨文件继承都保留实际所属文件的 URI、哈希和 span。这样才能对“绝大部分正经资产”给出按工程分组的覆盖率，而不是把通用语料文件数当作状态机分母。
