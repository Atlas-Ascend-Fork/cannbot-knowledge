# Issue 报告

用于把知识内容、检索、图谱、编译、治理或下游 agent 问题整理成可受理、可复现的材料。缺少事实时列 `needs-info`，不要猜测。

## 必备材料

1. 问题类型、期望行为、实际行为和最小复现路径。
2. 知识仓 remote、branch、commit、tag、dirty 状态及相关 diff。
3. 使用的 Plugin/Skill commit 与安装路径；未使用时明确写出。
4. 执行器、版本、Python、OS；涉及模型时记录完整模型标识和用途。
5. 完整原始 Prompt/Query、触发命令、实际生效配置和 stdout/stderr，逐字保留。
6. 涉及 agent/LLM 时保存 session、model request/response、tool calls 和生成 diff。
7. 工具、检索和 agent 问题优先汇总至少三次已有运行记录，并记录 y 次中出现 x 次；不足三次时如实记录样本数和缺口。仅在当前任务已授权且符合只读边界时补充复现；不因整理 Issue 自动回放原始 Prompt、构建、设备实验或有写入副作用的命令。确定性内容错误可说明无需重复运行。
8. 受影响 Concept ID/path、section/anchor、status、platform、CANN version、sources 和 card SHA-256。
9. 官方文档、固定 commit、源码路径、trace、日志、错误信号或建议 patch。

敏感信息可以脱敏，但不能删除配置结构。内容、平台或版本冲突进入治理流程，不直接覆盖已有知识。

## 推荐附件

```text
knowledge-issue-<date>-<title>/
├── README.md
├── environment.txt
├── command.txt
├── prompt.txt
├── terminal.log
├── configs/
├── sessions/
├── knowledge/
│   ├── git-status.txt
│   ├── git-diff.patch
│   └── affected-files.txt
└── reproduction/
    ├── run-1/
    ├── run-2/
    └── run-3/
```

## 正文模板

```markdown
# 问题摘要

## 问题类型
- <内容错误/缺失/检索/图谱/编译/lint/下游使用/其他>

## 版本与环境
- knowledge commit / dirty：
- Plugin/Skill commit：
- CLI、Python、OS：
- 模型完整标识与用途：

## 完整原始 Prompt / Query
<逐字内容；未使用则明确说明>

## 完整触发命令与配置
<命令；配置见附件>

## 完整终端输出与运行记录
<见附件，不只保留最后几行>

## 复现率
- Run 1/2/3：
- 运行 y 次，出现 x 次：

## 受影响知识
- Concept ID/path/anchor：
- platform/version/status/card SHA-256：
- sources：

## 期望行为
<应发生什么>

## 实际行为
<实际发生什么>

## 证据与建议修复
<固定来源、trace、日志或 patch>

## Needs info
- <缺失材料；没有则写无>
```

生成附件包或向外部系统提交 Issue 都需要用户明确授权；本工作流默认只整理本地材料。
