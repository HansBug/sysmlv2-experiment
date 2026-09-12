# SysML v2 官方前端与链接探针

本目录复用官方 Pilot workspace API，验证状态、转移、继承、跨文件链接、源位置和非法引用诊断。探针不修改上游仓库；批量导入与语料结果见 [import-findings.zh.md](import-findings.zh.md)。

当前主线固定 Pilot commit `801c6a881954987a9707d396d5767db1ec51d8cb`、v0.1.0 JAR 和匹配标准库。`AuditFrontend.java` 对照官方链接事实与我们的跨文件导出、默认入口映射；`SysmlStateInventory.java` 在完整校验前统计 typed 状态节点；`ExtractProject.java` 先索引工程目录再逐资源校验和抽取。

```bash
java -Xmx3g -cp /path/to/sysml-v2-pilot-gt-0.1.0-all.jar \
  research/LinkedStateProbe.java /path/to/sysml.library
```

这些探针证明前端路径可复用，但不证明 SysML runtime 与 FCSTM 等价，也不覆盖所有继承、重定义、消息和约束语义。转换器只根据 typed 事件和目标元素类型判断互斥出口与标准库 `done` 终止端点，不用源文本匹配。每次运行应保存 JAR 哈希、标准库 commit、源文件哈希、上下文目录和诊断。

[状态资产逐文件登记](state-assets.zh.md) · [学术公开资产盘点](academic-assets.zh.md) · [失败归因复核](frontend-audit.zh.md)
