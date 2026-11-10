---
type: Runbook
title: SGLang ACLGraph 排障：固定成功打印掩盖 eager NaN
description: EP128 多 shape 排障日志中 eager 被打印为成功，但数值探针已有 NaN；结合源码区分固定打印、有限性与独立 golden
  正确性。
tags:
- task.debugging
- task.testing
- topic.graph_execution
- topic.precision
status: draft
sources: []
created_at: '2026-10-29T07:47:19Z'
updated_at: "2026-10-29T08:06:03Z"
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - sglang
---

# SGLang ACLGraph 排障：固定成功打印掩盖 eager NaN

## 适用场景

SGLang/FluentLLM 的 NPU ACLGraph 多 shape 排障中，用 dispatch/combine 的 EP128 端到端复现脚本比较 eager、capture 与 replay。一次开发轨迹同时保留了脚本分支、既有运行日志及日志读取探针。硬件具体型号和依赖提交尚未核实，保持 draft、未知平台；不能从 EP128、节点数量或源码中的架构分支推导卡型。

## 触发与观测

复现日志出现 `ok=True (golden by construction)`，但同一 eager 阶段的数值探针显示 NaN，随后 replay 也失败。工具读取原日志得到：

```text
131:[verify rank=0 shape-T4 eager] ok=True (golden by construction)
```

同次读取还得到 `shape-T4 eager` 的 `nan=True nancnt=32768/32768`，以及 capture 阶段的相同非有限值。不能把第一行当成“eager 已正确，只有 replay 错”。

## 探针与操作

原轨迹执行的日志探针如下；文件名属于来源实验，使用时应定位本次实验的实际日志，不要求存在相同目录。

```bash
sed -n '125,160p' logstatic/ep128_e2e_logs_7/aclgraph_20261019_052059_bs1_node0.log | grep -E "verify|a2a-dbg|Phase|compile" | head -12
```

与日志一并检查原脚本中生成 golden 的完整分支。以下保留来源中的缩进和代码，不是独立启动脚本：

```python
            if REPRO_LEVEL >= 4:
                # 检测 eager 自身是否健康 (NaN/溢出)
                _nan = bool(torch.isnan(_out.float()).any().item())
                _inf = bool(torch.isinf(_out.float()).any().item())
                _ok = not _nan and not _inf
                print(f"[verify rank={RANK} shape-T{_t} eager] "
                      f"ok=True (golden by construction)", flush=True)
                _data[_t] = (_x, _ids, _sc, _out.cpu().float().clone())
```

## 机制与判别

所读源码把 eager 的成功打印写死；历史日志中相同的成功字符串与 NaN 并存，不能只凭打印判定基线正确。

在所读源码快照中，`_ok` 实际检查 `isnan` 与 `isinf`，并写入 `verdict["per_shape"][_t]["eager"]`；打印仍固定为 True。这只描述当前读取到的代码。历史 runner 日志另有 `eager=True` verdict，同时 eager 数值已经出现 NaN；不能用当前 `_ok` 的实现替历史运行解释这个 True。更不能把“输出全部有限”进一步等同于相对独立 golden 的数学正确性。该分支用 eager 输出自身构造后续参照，不能验证 eager 自身计算语义。

先核对同 shape、同 rank、同阶段的有限性输出与实际 verdict，再判断是 eager 已失败，还是只有 replay 偏离健康基线。原始日志已有 eager NaN 时，停止“仅图回放引入错误”的单点归因，回查 eager 计算及其输入、状态。

## 验证信号

- 日志读取工具在同一 eager 阶段同时返回写死的 `ok=True` 与 `nan=True nancnt=32768/32768`。（来源平台：未确认；证据等级：tool_observed；单条开发轨迹内的既有日志观测）
- 源码读取工具返回上述分支，明确展示固定打印、独立 `_ok` 计算以及 eager 输出成为参照的过程。（来源平台：未确认；证据等级：tool_observed；源码观测，不是新上板复测）

## 适用与失效边界

源码与历史运行尚未证明对应同一代码版本。工具列出的脚本修改时间为 `Oct 19 05:40`，日志名包含 `20261019_052059`；源码可能晚于该次运行，且时间格式/时区未独立复核。需要恢复实际执行版本后才能解释历史 verdict 的生成过程。前文对源码与历史日志分别取证，不将它们拼成一个已证实的运行实现。

只针对该复现脚本及具有相同“自建 golden + 固定成功打印”的验证逻辑。它不证明 SGLang 通用 eager 路径有错，也不证明 cache、tiling、通信或共享 graph pool 是 NaN 根因；本次没有重跑来源实验或修复底层问题。后续需确认平台与版本，并在独立参照和输入/状态一致的条件下分别验收 eager 与 replay。不要通过放宽容差、改期望或隐藏失败日志获得 PASS。
