# SysML v2 → FCSTM 实验

这是独立的公开研究仓库，用于把 SysML v2 单向导入 [pyfcstm](https://github.com/HansBug/pyfcstm)。Stateflow 实验位于[另一个仓库](https://github.com/HansBug/stateflow-experiments)。

当前主线使用官方 Pilot 的 Java/EMF typed 元素接口，保留状态、转移、继承、表达式、源位置和结构化映射；不在 Python 中重写 SysML parser，也不做反向转换。无法支持的构造会记录源文件、哈希、上下文、首个原因和目标诊断。

## 安装与运行

```bash
python -m pip install -r requirements.txt
python prepare_corpus.py
java -Xmx4g -cp /path/to/sysml-v2-pilot-gt-0.1.0-all.jar ExtractStates.java \
  /path/to/sysml.library artifacts/corpus-manifest.json artifacts/corpus-source.json
python check_import.py artifacts/corpus-source.json
python convert_corpus.py artifacts/corpus-source.json artifacts/converted
```

完整的 GitHub Actions 流程会固定公开数据集、Pilot JAR 与标准库版本，并上传源诊断、状态资产登记、FCSTM、映射和语义报告：

```bash
gh workflow run import.yml --repo HansBug/sysmlv2-experiment
gh run download RUN_ID --repo HansBug/sysmlv2-experiment --dir evidence
```

[解析器选择、公开数据集和历史覆盖](research/import-findings.zh.md) · [失败归因与修正后的状态清点](research/frontend-audit.zh.md) · [状态资产逐文件登记](research/state-assets.zh.md) · [学术公开资产盘点](research/academic-assets.zh.md)

## 当前证据

历史独立文件批次包含 1,332 个文件、24 个状态根、4 个通过根（2 个公开、2 个自建）。后续语法树清点确认公开文件中有 25 个语法有效且含状态元素、928 个语法有效且无状态元素、369 个有语法错误。完整上下文、跨文件继承和现代默认入口的对照审计见上述报告；目前没有确认官方核心 parser 缺陷。

项目级入口见 [`ExtractProject.java`](ExtractProject.java)：它会先索引整个工程目录，再按资源校验和抽取 typed 状态事实。`research/state-assets.json` 对每个状态候选保留源哈希、相对路径、上下文目录、状态节点数和基线状态。

已对 64 个公开语料上下文目录完成一次项目级扫描：162 个源文件、18 个状态根、4 个零错误目录；逐目录诊断见 [`research/project-context-observed.json`](research/project-context-observed.json)。将这 18 个已校验状态根接入目标检查后，得到 2 个 converted、16 个 unsupported。另已抽取官方 Pilot 的 255 个示例，其中 47 个状态根进入下一轮转换，证据见 [`research/official-pilot-observed.json`](research/official-pilot-observed.json)。

最新 CI 已在 [Actions 34708595195](https://github.com/HansBug/sysmlv2-experiment/actions/runs/34708595195) 复现 JAR 下载、语料抽取、语法清点、项目上下文步骤和 pyfcstm 检查，并上传全部中间产物。

接入官方 Pilot 255 个示例后的 [Actions 34709690957](https://github.com/HansBug/sysmlv2-experiment/actions/runs/34709690957) 也已通过：总计 1,587 个文件、71 个源状态根、6 个 converted。启用 typed `accept`→FCSTM event 后，[Actions 34711113632](https://github.com/HansBug/sysmlv2-experiment/actions/runs/34711113632) 将独立批次提升到 12 个 converted、项目级批次提升到 10 个 converted；完整对照见 [`research/events-observed.json`](research/events-observed.json)。

随后将 `ActionDefinition` 作为事件声明处理的 [Actions 34711931066](https://github.com/HansBug/sysmlv2-experiment/actions/runs/34711931066) 也已通过；总数保持 12/71 与 10/74，因为 StopWatch 随后触发了未定义出口优先级拒绝。

最新的全上下文扫描 [Actions 34710023025](https://github.com/HansBug/sysmlv2-experiment/actions/runs/34710023025) 对 76 个上下文、237 个上下文内文件执行了项目级加载，得到 74 个状态根，其中 4 个 converted、70 个明确 unsupported。汇总见 [`research/project-context-ci-observed.json`](research/project-context-ci-observed.json)。

## 转换范围

当前目标是 exclusive hierarchy、单默认入口、基本 scalar 数据、简单 guard、entry/exit 赋值、transition effect，以及由官方 typed `accept` 元素映射的 FCSTM event。带 payload/receiver 的消息、时间触发、并行、任意动作、非空 do action、未定义优先级、数组和无法解析的成员会明确拒绝。数值是数学域抽象，不自动等价于 Stateflow 或 SysML runtime 的位宽、溢出和调度语义。

## 公开资料与许可

数据集和论文链接、可下载模型文件类型、固定版本及本次状态覆盖见[学术资产盘点](research/academic-assets.zh.md)。第三方模型与工具保留原许可；本仓库只提交清单、哈希、统计和自写实验代码。实验代码采用 MIT。

Apollo 11 工程资产已固定到 `6e9c93fe7d80c5ca3534bb14b10ab374a643ef2d`，本地用同一官方 Pilot JAR 加载 28/28 文件并识别 18 个状态根；下一次 CI 会把它纳入全量批次。任务阶段根包含 15 个子状态和 14 条 typed 事件转移。严格 FCSTM profile 暂因继承的 `PerformActionUsage` 保留拒绝，不把删掉 do 行为后的骨架当作等价转换。 逐项证据见 [`research/apollo11-observed.json`](research/apollo11-observed.json) 和 [`research/state-assets.json`](research/state-assets.json)。
