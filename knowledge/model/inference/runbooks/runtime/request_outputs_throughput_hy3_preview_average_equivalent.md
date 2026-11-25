---
{
  "type": "Runbook",
  "title": "HCCL_OP_EXPANSION_MODE=AIV 对 hy3_preview MTP decode 的正确性依赖与 MTP accept-rate 虚假加速陷阱（AIV-OFF 输出病理退化但等效时延假低）",
  "description": "模型/任务：hy3_preview（295B MoE）decode 1k input / batch16 / ge_graph / MTP1（next_n=1），16 die A3，profiling YAML（prof_mtp）。",
  "tags": [
    "task.debugging",
    "topic.implementation.debugging"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:05Z",
  "updated_at": "2026-11-24T01:53:53Z",
  "platforms": [
    "a3"
  ]
}
---

# HCCL_OP_EXPANSION_MODE=AIV 对 hy3_preview MTP decode 的正确性依赖与 MTP accept-rate 虚假加速陷阱（AIV-OFF 输出病理退化但等效时延假低）

## 适用场景

- 平台范围依据：source 0 seq 41、source 0 seq 42、source 0 seq 172、source 0 seq 239的实际环境/设备记录确认本次为Atlas A3；这里不扩展未记录的产品或版本。

- 模型/任务：hy3_preview（295B MoE）decode 1k input / batch16 / ge_graph / MTP1（next_n=1），16 die A3，profiling YAML（prof_mtp）。
- 框架行为前提（本轨迹源码核查）：`function.sh set_hccl()` 在 MTP 配置（无 platform_version/micro_batch_mode 字段）下**默认 export HCCL_OP_EXPANSION_MODE=AIV**——即历史 roundH 基线（31.47ms/t）本就是 AIV-ON。
- 对照设计：AIV-ON（默认）vs AIV-OFF（HCCL_OP_EXPANSION_MODE unset），同会话暖编译缓存、同输入、同 16 rank。

## 触发与观测

A/B 结果全部 tool_observed（source 0）：

- AIV-ON（seq 172）：
  ```
  hy3_preview main and mtp model average inference time cost is 46.22 ms
  hy3_preview model average equivalent latency of MTP1 is 29.92 ms
  The speculation accept length: 1.5448
  The speculation accept rate: 0.5448
  ```
  Req0-3 输出为连贯技术文本（quantization/mixed precision 讨论等）。
- AIV-OFF（env 确认 `HCCL_OP_EXPANSION_MODE=<unset>`，seq 198；结果 seq 239）：
  ```
  hy3_preview main and mtp model average inference time cost is 49.73 ms
  hy3_preview model average equivalent latency of MTP1 is 25.31 ms
  The speculation accept length: 1.9649
  The speculation accept rate: 0.9649
  ```
  Req0-3 输出全部退化为 ` throughput!!!!!!!!!!!!!!!!!!...`（首 token 后无限重复 '!'）。
- 全 rank 核查（seq 243）：16/16 rank 到达 accept rate、0 crash、log_8 同样垃圾输出——"能跑完但输出坏"。

## 探针与操作

1. 源码核查 set_hccl 默认行为（发现历史基线已是 AIV-ON，实验重构为 ON 复锚 vs OFF 反事实）。
2. AIV-ON 复锚运行（暖缓存，与 roundH 31.47ms 对比确立 ~5% 运行间噪声：29.92 vs 31.47，accept 1.5448 vs 1.5377）。
3. AIV-OFF 反事实运行（仅 unset 该环境变量，其余配置与运行脚本相同）。
4. 双侧快照 log_0 + rank0 decode kernel_details.csv（5440 行）供 profiling 复核。

## 机制与判别

- 正确性依赖：unset AIV 后模型不崩溃但输出病理退化（全 rank 一致），而 AIV-ON 输出连贯——AIV（HCCL 算子 Vector 扩展开启）在该模型+MTP+ge_graph 组合下是输出正确性的必要条件。底层算子级机制（哪个 HCCL 算子在 AIV-OFF 下产生数值错误）本轨迹未定位，为 unknown。
- 指标陷阱：AIV-OFF 的垃圾重复输出使 draft token 极易被接受 → accept rate 0.9649（vs 0.5448）→ 等效时延 25.31ms "优于" AIV-ON 29.92ms 是假象；真实单前向 49.73ms 反而慢于 AIV-ON 46.22ms。凡 MTP/投机解码的性能结论必须先过输出质量门，否则 accept-rate 抬升会伪造加速。
- 判别强度：单变量 A/B、同会话暖缓存、双方向复跑，输出与指标差异同时观测。

## 验证信号

- 两组逐字指标与输出样本（seq 172/239，tool_observed）；env 生效确认（seq 198 `[roundE][AIV-OFF] HCCL_OP_EXPANSION_MODE=<unset>`）。
- 全 rank 16/16 完成无 crash + 垃圾输出跨 rank 一致（seq 243）。
- 运行间噪声参考：同配置两次 AIV-ON 29.92 vs 31.47 ms/t（~5%）。

## 适用与失效边界

- 适用：hy3_preview 类 MoE + MC2 通信 + ge_graph + MTP 组合下调优/关闭 HCCL_OP_EXPANSION_MODE 前的正确性风险；以及一切 MTP 等效时延评测的质量门要求。
- 失效/不覆盖：AIV 影响的底层算子与数值机制未定位；其他模型/不含 MC2 通信的组合未测试；"AIV 必需"结论绑定该框架 set_hccl 默认导出行为与该硬件/版本组合。
- 停止条件：unset 或覆盖 HCCL_OP_EXPANSION_MODE 的性能实验必须先对输出做逐位/可读性检查再采信时延数字。

## 附：断言存档

- hy3_preview MTP1 decode（1k/16b/ge_graph，同会话暖缓存 A/B）：AIV-ON（默认 set_hccl 导出 HCCL_OP_EXPANSION_MODE=AIV）输出连贯、等效时延 29.92ms/t、accept rate 0.5448、单前向 46.22ms；AIV-OFF（unset）全 16 rank 输出退化为 throughput!!!... 病理重复（0 crash、16/16 完成）——AIV 为该组合输出正确性必要条件。
- MTP 指标陷阱：AIV-OFF 垃圾重复输出使 accept rate 升至 0.9649、等效时延假低 25.31ms（<AIV-ON 29.92），但真实单前向 49.73ms 慢于 AIV-ON 46.22ms——MTP 等效时延结论必须先过输出质量门。

```text
[INFO][2026-07-05 20:59:50.142][infer.py:86] Request 0: outputs:  throughput!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
[INFO][2026-07-05 20:59:50.142][infer.py:86] Request 1: outputs:  throughput!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
```

```text
[INFO][2026-07-05 20:54:05.402][infer.py:108] hy3_preview model average equivalent latency of MTP1 is 29.92 ms
[INFO][2026-07-05 20:54:05.403][infer.py:111] The speculation accept length: 1.5448
[INFO][2026-07-05 20:54:05.404][infer.py:112] The speculation accept rate: 0.5448
```
