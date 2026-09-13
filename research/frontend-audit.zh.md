# SysML v2 失败归因与状态语料复核

**目前没有确认官方 Pilot 核心解析器缺陷；已确认我们在项目加载、跨文件元素导出和默认入口映射上有缺口，语料还存在版本与约束差异。** 官方解析、链接/校验、我们的抽取、FCSTM 转换是不同环节，不能拿最终通过率倒推解析器质量。

本轮继续使用 Java 21、同一个 v0.1.0 JAR（SHA256 `1bb02b3865e6830687f4c4f80afbfe8d670f6fb6df305f6844833543320fa989`）及匹配的官方 Pilot/标准库 commit `801c6a881954987a9707d396d5767db1ec51d8cb`。本轮审计在本地完成，历史完整转换另有 [Actions 34703608767](https://github.com/HansBug/sysmlv2-experiment/actions/runs/34703608767)；不把两者混成同一 CI 实验。

## 到底有多少文件含状态元素

此前先做完整校验，失败就丢弃资源，再清点状态。这会漏掉语法有效、但缺工程上下文或不满足语义约束的候选。

这次通过官方 `SysMLInteractive.createInstance()` 初始化 Xtext/EMF 资源，**先遍历语法 AST 中的 StateDefinition / StateUsage，再独立对照完整校验结果**。不搜索 `state` 字符串；错误恢复树与语法有效树分开统计。与原批次每一个通过完整校验的文件逐一交叉检查，状态元素是否存在完全一致。

| 公开语料 | 文件总数 | 语法有效且含状态元素 | 语法有效且无状态元素 | 有语法错误 |
|---|---:|---:|---:|---:|
| GfSE | 36 | 4 | 23 | 9 |
| SysTemp | 243 | 20 | 219 | 4 |
| Refinement positive | 604 | 1 | 603 | 0 |
| Refinement negative | 439 | 0 | 83 | 356 |
| 合计 | **1,322** | **25** | **928** | **369** |

另外 10 个自建文件语法均有效且含状态元素，不计入上表。逐文件源哈希、typed 节点数及校验状态保存在 [state-inventory-observed.json](state-inventory-observed.json)。

所以，大部分所选公开文件确实不含状态元素：**928/1,322 = 70.2%** 已由有效语法树确认；如果只看语法有效的 953 个文件，无状态元素占 **97.4%**。这批通用建模/生成/合规语料不能用作同等数量的状态机转换 benchmark。

25 个语法有效候选中，原先只有 **11 个文件通过完整校验，包含 18 个状态根**，另 **14 个文件** 被完整校验筛掉。18 不是状态机文件数，25 也不是可执行控制器数：其中仍可能有空的状态定义、snapshot 或类型不合法的状态 usage。

369 个语法错误文件中，67 个错误恢复树出现状态节点，302 个未出现。这些都不能当作已经成功识别的完整状态模型；大量错误文件本就是作者标为 negative 的生成产物。外部语料的 687 个完整校验失败，拆成 **369 个语法失败 + 318 个语法有效但链接/约束失败**；尚未把后 318 个逐个归为原模型错误、版本差异或缺上下文。

## 同一官方前端的对照实验

[AuditFrontend.java](AuditFrontend.java) 保留实验代码，[frontend-observed.json](frontend-observed.json) 保留源事实、源诊断及我们的转换拒绝。

| 对照 | 实测 | 归因 |
|---|---|---|
| 同时加载 `types.sysml` 与 `app.sysml` | 官方链接后，controller 的 inherited membership 含 Idle、Active；修复后的项目模式能输出 Idle、Active 两个 children；旧独立模式曾输出空 children | 原实现把跨文件用户定义误当成 library；项目模式现已按 input resource 区分 |
| 当前默认入口 `first start then A` | 官方校验通过，导出边 source 为 `States::StateAction::start`；修复后的 Python `lower()` 已将该边转换为 FCSTM 默认入口 | 原实现只识别显式 entry；现在识别 `States::StateAction::start` |
| `send Signal()` 与 `send new Signal()`，Signal 是 attribute definition | 旧写法被当前官方校验拒绝：Must invoke a behavior or a behavioral feature；新写法通过 | 具体的旧构造调用与当前规则不匹配，不是官方无法解析状态机 |
| SysTemp 的 6 个 Interaction Sequencing 文件，逐文件与一起索引加载 | 错误总数从 338 降到 18；失败文件从 5 个降到 4 个 | 我们缺工程上下文是实际原因之一，但不能解释全部剩余错误 |

最后一项使用同一批原文件、同一解析器/标准库，无源文本修补。`ServerSequenceModelOutside.sysml` 从 24 条错误变成完全通过；两个含状态的 `*-2.sysml` 分别从 46、52 条错误降到各 6 条，仍未通过。剩余 18 条是 12 条构造调用相关约束、6 条 connector related features 约束，不能把这 4 个文件算作已恢复的有效模型。

随后对登记表中的 64 个上下文目录逐一运行 [`ExtractProject.java`](../ExtractProject.java)。64 个目录、162 个源文件均完成项目级读取，得到 18 个状态根；4 个目录零校验错误，其余目录共 1,500 条错误（旧批次）。机器可读汇总见 [`project-context-observed.json`](project-context-observed.json)。再经过 pyfcstm 目标检查，18 个项目级状态根中 2 个 converted、16 个因目标 profile 特性拒绝，结果见 [`project-conversion-observed.json`](project-conversion-observed.json)。这说明“补全上下文”是必要条件，但对当前语料仍不足以带来全面通过；剩余错误必须按构造调用、connector、旧版本写法等类型继续处理。

接入官方 Pilot、Apollo 11、Advent 和 SysML v2 Book 示例后，CI 扫描了 78 个上下文、309 个上下文内文件，得到 96 个状态根，其中 50 个控制状态候选，16 个 converted、80 个明确 unsupported。Apollo 11 作为完整 28 文件根目录加载时为 0 条校验错误、18 个状态根；此前按子目录拆分造成的 842 条错误已确认是我们的上下文分组缺陷。Book 示例的全局校验错误使其没有进入 typed 状态根项目扫描。该结果包含同一概念在不同公开数据集中的重复版本，不能按状态根数宣称独立系统数量；汇总见 [`project-context-ci-observed.json`](project-context-ci-observed.json)。

公开旧例 `training/24. Transitions/Transition Actions.sysml` 与当前官方 Pilot `sysml/src/training/25. Transitions/Transition Actions.sysml` 还实际展示了 `send ControllerStartSignal()` → `send new ControllerStartSignal()`、`entry; then off` → `first start then off` 的变化。核心 state grammar 相同，不代表共享动作规则和标准库没变化。不能承诺 2024 前端无条件覆盖 2026 状态模型。

跨文件导出不能只删掉那一行过滤：还要区分项目输入与标准库资源，并为继承元素保留它实际所属文件的 URI/哈希/span，否则当前根文件的 provenance 会被错误套在别的文件上。当前 `ExtractStates.span()` 已记录元素资源 URI 和输入文件 SHA-256；官方已有 `readAll(..., true, ".sysml")`、资源索引及 `isInputResource()` 等接口可复用，不需要重写 parser 或重新设计服务。

## 哪些结论还不能下

没有把 318 个语法有效的校验失败全归为缺 import；也没有把 369 个语法失败全归为原语料写错，其中仍可能有版本差异。要确认官方缺陷，需要匹配版本和完整上下文下、符合相应规则的最小复现；本轮未得到这样的证据。

单独裸调 Xtext `IParser` 的早期诊断脚本曾缺少 EPackage/setting delegate 初始化，导致代理或 NPE 错误；换成官方完整 workspace 初始化后消失，这是我们的探针接法问题。已有 wrapper 的泛化 JSON 序列化异常也不能直接归到官方语法解析器，本导入路径不使用那个 serializer。

最新独立文件转换结果为 **82 个抽取状态根中 20 个 converted**；最新项目级上下文扫描为 **96 个状态根中 50 个控制状态候选、16 个 converted**。[Actions 34727402230](https://github.com/HansBug/sysmlv2-experiment/actions/runs/34727402230) 进一步验证了 typed 事件互斥出口、标准库 `done` 终止端点、带 library 单位的数量值、动作参数引用登记，将官方 `Base::Anything` 时间/变化触发拒绝为 `time_trigger`，并为 `FeatureChainExpression` 保留目标 feature 定位；总计独立文件批次为 1,665 个文件、52 个控制候选、20 个 converted（其中 7 个为自建 fixture）。member kind、消息 payload/receiver、no control states、parallel、时间触发、复杂 feature chain、任意 action 和未定义优先级仍是映射实现或 profile 的边界，不是 parser failure，也不是已经证明无法表示。带 guard/赋值的目标轨迹验证仍来自自建例。

工程上下文补全已经覆盖登记的公开项目；当前 `PerformActionUsage`/`SendActionUsage` 的有名字调用已能保留为 abstract hook，`initial` usage 也能映射为默认入口。Apollo 11 的完整项目上下文因此从 18 个全部拒绝变为 1 个控制状态根通过目标 AST/语义检查；这只是结构化 hook 表示，不是 action 内部执行等价。剩余拒绝主要是带赋值的 do action、并行、结构成员、时间/消息语义和未定义优先级。带 library 单位的数量值、可证明互斥的简单 guard，以及带结构化诊断的非线性 action succession 已加入受限映射。下一步仍应逐类建立 typed 最小复现，不通过删除行为来提高数字。通用文件总数不宜再作为状态机覆盖率的分母；论文需要分别报告源语法/链接有效性、候选状态根、实际支持范围、目标语义检查及源行为对照。

当前对未参与控制表达式的 `ReferenceUsage`、`PartUsage`、`PortUsage` 采用显式 `ignored_structural` 登记。已增加一个严格的 typed FeatureChain 子集：单实例 part 到标量数值 attribute 的一层链可映射为带结构来源的 FCSTM 变量，并验证初始化、赋值和 guard 使用同一链；多实例、数组、跨对象和更深链仍拒绝，避免把结构成员的行为依赖误当成可忽略元数据。

本轮还复现并修复了一个纯转换器问题：父状态的引用收集曾递归扫描子状态整棵子树，子状态动作参数因此被错误地报告为父状态的 `member_kind` 缺口。提交 [`4d3f8af`](https://github.com/HansBug/sysmlv2-experiment/commit/4d3f8af) 将引用范围限制在当前状态的直接行为；官方 Pilot 训练项目 `23. States` 的本地对照从 1/3 个控制候选转换成功提升到 2/3，剩余失败分别是并行语义和无状态子根。这一变化属于我们自己的抽取器修正，不是官方前端修复。

## 复现

先按主 README 准备 requirements、固定语料、v0.1.0 JAR 和匹配标准库。使用历史完整批次或重新抽取的 `artifacts/corpus-source.json` 交叉检查状态清点：

```bash
mkdir -p artifacts/audit-classes
javac -cp /path/to/sysml-v2-pilot-gt-0.1.0-all.jar -d artifacts/audit-classes \
  ExtractStates.java research/AuditFrontend.java research/SysmlStateInventory.java
java -Xmx3g -cp /path/to/sysml-v2-pilot-gt-0.1.0-all.jar:artifacts/audit-classes \
  SysmlStateInventory artifacts/corpus-manifest.json artifacts/syntax-state-inventory.json \
  artifacts/corpus-source.json
java -Xmx3g -cp /path/to/sysml-v2-pilot-gt-0.1.0-all.jar:artifacts/audit-classes \
  AuditFrontend /path/to/sysml.library artifacts/frontend-audit.json
python research/check_frontend_audit.py artifacts/frontend-audit.json artifacts/frontend-checked.json
python check_import.py artifacts/corpus-source.json
```

上述 classpath 使用 Linux/macOS 分隔符；Windows 使用 `;`。回归断言固定了项目级抽取和 modern start 转换；后续扩展语义规则时应同步更新报告。审计同时修复了两个已确认的转换缺口；历史全量统计尚未重跑，因此不把这两个探针转换计入公开语料成功率。

`research/cases/perform-sequence.sysml` 是新增的 typed 回归例：它用 `first start`、两个有类型的 `ActionUsage` 和 `done` 构成线性 succession。`check_import.py` 会验证官方抽取出的 `sequence`、abstract hook 映射、FCSTM AST 解析和目标语义检查；Apollo 11 的项目级结果摘要保存在 [`apollo11-action-observed.json`](apollo11-action-observed.json)。
