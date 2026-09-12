# SysML v2 单向导入实验

## 前端选择

**当前主线用官方 Pilot 的 Java/EMF 元素接口。** 已有可直接运行的 [v0.1.0 wrapper JAR](https://github.com/HansBug/sysml-v2-pilot-gt/releases/tag/v0.1.0)，因此不需要在 Python 里重写 SysML parser，也不需要搭 LSP 服务。`ExtractStates.java` 直接读取 linked StateDefinition/StateUsage、TransitionUsage、StateSubactionMembership、AssignmentActionUsage、OperatorExpression 等对象，保留链接后的端点、表达式树、源位置和 ID。它不使用 wrapper 的泛化对象 JSON dump。

| 候选 | 实测结果 | 对本项目的结论 |
|---|---|---|
| 官方 Pilot，`801c6a881954987a9707d396d5767db1ec51d8cb`（2026-07） | 状态层次、跨文件类型链接、继承、转移端点、guard、赋值、source span、非法引用拒绝均通过定向探针；已连接 FCSTM | 当前成本最低的完整 typed 前端入口。Java 21 + 固定 JAR + 匹配标准库 |
| [sysml-2ls](https://github.com/sensmetry/sysml-2ls)，`a0b3ddbf783063dd7291aac0b51d4282decc789e`，0.9.1 | 用匹配的 2024 标准库时，定向状态机案例中的层次、guard、赋值、entry/do/exit 分类、跨文件 exhibit/继承、端点和 span 可提取；拒绝不存在的类型/目标 | 可作为受限旧语法方案。不能因年份旧而否定，但也不能把定向探针当完整版本兼容证明 |
| [Spec42](https://github.com/elan8/spec42) 相关工具调查 | [实测 v0.52.0](spec42-observed.json) CLI 的 model-summary 是 validation-only，成功验证的状态文件仍报告 nodes_total=0；存在更丰富的 WASM/generator API，未完成 typed state 导出验证 | 本次不接入；不能据旧版 CLI 结果推断其所有 API 都不可能提取状态 |

`FrontendProbe.java` 与 `legacy_probe.cjs` 分别保留可运行的验证代码，结果为 `pilot-observed.txt`、`legacy-observed.json`。批量转换另用 `ExtractStates.java`，两种实验不要混淆：前端探针证明可链接跨文件；当前批量器为隔离语料中的重复 package/name，**逐文件加标准库加载**，没有恢复各工程上下文。

## 2024—2026 是否影响状态机

[`version-diff/observed.json`](version-diff/observed.json) 固定官方 Pilot 2024-12 和 2026-08 源码。`StateDefinition` 到 `CalculationDefinition` 之前的核心状态文法段共 5,989 bytes，字节完全相同。但周围依赖发生了变化：

- States 库的 payload 由 `out` 改成 `inout`。
- StatePerformances 移除了只读 incomingTransitionTrigger 定义。
- TransitionPerformances 的 triggerTarget 从 `this` 改为 `accept.receiver ?? this`，并调整 receiver 相关定义。
- 共用文法的 `readonly`→`constant`、send/accept 和 typing 等变化会进入状态机的数据/动作部分。

同一 `constant attribute` 输入，当前官方前端接受，旧 JS 前端报 parser error。这已经否定“状态机相关内容整体没变”的强说法；但无消息、无新式数据声明的简单控制 HSM 仍有使用旧 JS 的空间。对当前只要求导入 FCSTM 的任务，已有官方 JAR 后再维护旧 JS 兼容层收益很小。状态核心文法未变，也不等于 runtime 语义或全体约束未变。

## 转换契约与边界

入口：`.sysml + 匹配标准库 → 官方解析/链接/校验 → typed source JSON → 子集检查与映射 → FCSTM DSL serialization → pyfcstm AST → StateMachine → inspect_model(enable_verify=True)`。

源元素依靠类型和链接映射；输出 DSL 是目标 AST 的规范序列化入口，不是用文本搜索改写源语言。依赖固定 `pyfcstm==0.6.0`，成功要求能构建 `StateMachineDSLProgram` 和 `StateMachine`，并且 inspect 无 error。warning/info 全部保留。

当前接受 exclusive hierarchy、同层转移、单一默认入口、基本 scalar 数值及显式初始化、简单表达式、entry/exit 赋值和 transition effect。没有显式 multiplicity 时，在本控制器 profile 下解释为一个实例；显式数组拒绝。并行、触发/消息、任意动作、非空 do action、多个未定义优先级的 outgoing、缺失默认入口、无法处理的成员类型明确拒绝。do action 没有直接映射为 during。数值是数学域抽象，变量类型的全部 SysML 不变量没有被编码进 FCSTM。

每个 accepted root 输出 `model.fcstm`、`inspect.json`、`mapping.json`；映射含源 SHA256、限定名、源 offset/length/line、目标状态/变量/动作/转移索引、上下文和假设。只做单向导入；此阶段不实现回写或修复算法。

[后续审计](frontend-audit.zh.md) 进一步限定上述入口支持：项目模式已索引用户工程文件并保留跨文件继承；转换器也已映射官方接受的 `first start then A` 默认入口。独立文件批次仍不具备工程上下文，历史转换统计尚未重跑。

`check_import.py` 验证官方源元素经过这条完整链路后的层次与赋值行为：Idle entry 将 x 置 1，下一拍 guard 成立、effect 将 x 置 4 并到 Active；另检查并行、数组、do action、无效引用拒绝。这个 FCSTM 轨迹检查是映射 profile 的回归门，不是独立 SysML execution oracle。

## 含模型文件的公开研究语料

| 来源 | 固定版本 | 本次选取文件 |
|---|---|---:|
| [GfSE/SysML-v2-Models](https://github.com/GfSE/SysML-v2-Models) | `ebbb0c39f4813b059e0bf14270ec58618aa012ca` | models 下 36 个 .sysml |
| [SysTemp benchmark](https://github.com/yasminebouamra/SysMLv2-Benchmark) | `dd41357921f23020aacdaaa063e0a4b31fc0b2b4` | data 下 243 个 .sysml |
| [Conformance-Driven Refinement dataset](https://github.com/cmuchancel/NL-to-SysMLv2-via-Conformance-Driven-Refinement) | `96c0e104f82a8da7a5edccca9b67040785b53bd3` | 604 positive artifacts + 439 negative artifacts |
| 自建最小源模型 | 本实验仓库版本 | 10 个 .sysml |

[SysTemp 论文](https://arxiv.org/abs/2506.21608) 直接链接前两者；[Refinement 论文](https://arxiv.org/abs/2607.14162) 链接第三者。Refinement 仓库还含 151 个 SysMBench prompts 和 trajectory corpus，本批次没有把 trajectory 中同一模型的副本再重复加入。正负标签来自作者的合规评价，不等于当前 Pilot 独立文件加载会给出相同结论。[SysMBench 论文](https://arxiv.org/abs/2508.03215) 本身不能替代实际可下载模型证据。

这些集合多用于语言建模、生成或 conformance；不都是可执行控制器，更不是等量独立系统。文件级 SHA256 用于复查重复，当前 1,332 文件包含 1,329 种内容。

## 实际覆盖

以下是历史的“先完整校验、再抽取”批次结果。[后续失败归因复核](frontend-audit.zh.md) 已补做独立语法树清点：公开的 1,322 个文件中，25 个语法有效且含状态元素、928 个语法有效且无状态元素、369 个有语法错误。原批次只进入了其中 11 个含状态元素的文件（18 个状态根），另 14 个语法有效候选被完整校验筛掉。不能用下表的状态根数代替语料中所有含状态元素的文件数。

批次摘要与逐项状态见 [`import-observed.json`](import-observed.json)。本地 Java 21 + 固定 JAR/标准库已执行全部 1,332 文件；[Actions 34703608767](https://github.com/HansBug/sysmlv2-experiment/actions/runs/34703608767) 成功复现相同统计，并保存完整源诊断和转换产物。

| 数据集 | 文件 | 源校验失败文件 | 成功解析但无状态机文件 | 接受的状态根 | 不支持的状态根 |
|---|---:|---:|---:|---:|---:|
| GfSE | 36 | 28 | 6 | 0 | 2 |
| SysTemp | 243 | 94 | 140 | 2 | 14 |
| Refinement positive | 604 | 127 | 477 | 0 | 0 |
| Refinement negative | 439 | 438 | 1 | 0 | 0 |
| 自建验证例 | 10 | 4 | 0 | 2 | 4 |

状态根与文件不在同一个计数层级，不能横向简单相加。总计 24 个成功解析的状态根中通过 4 个；去掉自建例，公开数据的 18 个候选通过 2 个。**本轮不能声称大部分公开模型可转换。** 也不能把 624 个没有状态机的文件算成转换失败，或把 691 个源校验失败全部说成原数据错误：包括旧语法、工具约束差异及我们尚未加载的跨文件工程上下文。

公开 accepted roots 来自 SysTemp 的 `6-Individual and Snapshots.sysml` 中 VehicleA::vehicleStates，以及 `10c-Fuel Economy Analysis.sysml` 中 transmission::transmissionState。这两个公开 accepted root 都是简单的无 guard/赋值状态链；带 guard 和赋值的转换证据目前来自自建例，不能写成复杂公开行为模型已经得到验证。其他候选的 first-blocker 包括不支持的成员、触发动作、空状态定义、并行和无默认入口。first-blocker 不是完整特征普查；同一个模型可能还有其他障碍。当前没有 source frontend exception 或 target AST/model error 被伪装成 unsupported。

## 对后续学术工作的含义

该入口足以建立源定位、环境假设与 FCSTM 诊断之间的映射实验。现有通用 SysML 语料中控制状态机密度低，继续扩大下载量的收益可能低于先恢复工程依赖、按 typed state 元素筛选、以及收集专门的行为模型。论文应分别报告语料可加载性、状态机候选数、规则覆盖率、目标有效性、与源语义的一致性证据；其中最后一项还需要进一步建立，不能用“能 parse”替代。
