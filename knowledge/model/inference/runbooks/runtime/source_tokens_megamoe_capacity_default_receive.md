---
{
  "type": "Runbook",
  "title": "Kimi-K3 128K prefill OOM 预算缺口定位：MegaMoE 每 rank 持久 CCL 预留（URMA4 ~8.09 GiB / MTE ~1.02 GiB）与 intermediate_hidden 双倍放大",
  "description": "模型/框架：Kimi-K3（TP16 + EP32 + DSpark，E896/TopK16，routed width 3584，expert intermediate 3072），cann-recipes-infer_kimik3 私仓；MegaMoE 取自 ops-transformer",
  "tags": [
    "task.debugging",
    "topic.implementation.debugging"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:05Z",
  "updated_at": "2026-11-24T01:53:53Z",
  "platforms": []
}
---

# Kimi-K3 128K prefill OOM 预算缺口定位：MegaMoE 每 rank 持久 CCL 预留（URMA4 ~8.09 GiB / MTE ~1.02 GiB）与 intermediate_hidden 双倍放大

## 适用场景

- 模型/框架：Kimi-K3（TP16 + EP32 + DSpark，E896/TopK16，routed width 3584，expert intermediate 3072），cann-recipes-infer_kimik3 私仓；MegaMoE 取自 ops-transformer（HEAD `921356e3ce34126d5b209f23c05efeb6150bd4b5`，Ascend950/arch35_92 分支）。
- 源码/任务目标：Atlas A5 / Ascend 950、32P；每卡约96G是任务背景。该来源为源码级内存核算和CPU算术验证，未确认当前实机设备，不据此填写950。
- 工作负载：128K（131072 token）全长 prefill 的显存预算与 OOM 归因（用户实测 32P 直接 OOM，且 chunk prefill 8192 + chunk moe 12800 时占用已达 87G）。

## 触发与观测

用户报告理论显存估计与实跑差距大（source 0 seq 53、1416）；算子侧同事确认 128K 场景 MegaMoE 整体占用约 16 GiB（含输入输出与中间量，user_reported，source 0 seq 564）。

## 探针与操作

方法（source 0 seq 579、586，工具读到的 findings.md/analyze.py）：`analyze.py` 从 ops-transformer 抽取真实 `BuildMemoryBudgetParams`/`CalcCclBufferSizeA5` 与纯 C++ 内存布局头，在 CPU 上编译执行分配算术——这是源码级算术验证，不是 NPU 实测。

关键参数推导（逐字，source 0 seq 579）：

```text
Local source tokens = 131072/16 = 8192. One MegaMoE call capacity is
min(8192,12800/32)=400; 20 full calls plus a 192-token tail per MoE layer.
Default receive capacity R=400*32*min(16,896/32)=204800 routed token-expert rows.
```

## 机制与判别

逐字结论（source 0 seq 579）：

- 每 rank 持久 CCL 预留（不随调用/层数放大）：`Total persistent custom CCL allocation` MTE = 1.024302959 GiB；URMA（4 UB domains）= 8.085751772 GiB（精确 8682009856 字节）。该分配是每模型/rank 一次直接 `aclrtMalloc` 并注册为 CCL 内存，跨调用与层复用，位于 PyTorch caching allocator 之外："Do not multiply by 21 calls, 92 MoE layers, or EP32 for a per-rank estimate."
- 拓扑选择由 RankGraph 而非机器卡数决定：URMA 2/4/8/16/32 UB domains 预留 8.0827–8.1289 GiB，需查 `mega_sym_buffer.topo_type`、`rank_num_per_server`、`ccl_buffer_size`。
- 参数语义缺陷（可节约项）：MegaMoE API 的 `intermediate_hidden` 期望的是激活后宽度；模型侧 `modeling_kimi_k3.py:1034` 传入 `2*moe_intermediate_size=6144`，而分配器内部再乘 2，导致 GMM1 宽度按 12288 预算。改为传 3072 后 URMA4 = 5.114722490 GiB，节约 2.971029282 GiB（MTE 反而微升至 1.032033443 GiB：更窄维度增加计划 wave group 与 ring 容量）。未改代码，集成与 NPU 验证仍需进行。
- 旧估计更正：此前"5.075 GiB 临时 workspace + 0.045 GiB 常驻通信内存"的记账被本实现取代；替换时必须同时移除旧两项，不能只叠加新 CCL 项。

## 验证信号

- tool_observed（source 0 seq 579，本轨迹读取的 findings.md 全文）：分配表、精确字节数、持久性声明与参数修正推导；并明确标注"This validates source allocation arithmetic on CPU; it is not an NPU measurement."
- tool_observed（source 0 seq 567，MEMORY.md 摘要）：`intermediate_hidden=2*moe_intermediate_size` 导致 CCL over-reservation 的先前记录。
- user_reported（source 0 seq 564）：算子同事确认 128K 下 MegaMoE 整体占用 16 GiB（含 I/O 与中间量）。
- 未取得：NPU 上按 rank 的分配实测与 OOM 现场allocator trace（findings.md 自述"the exact OOM cause remains conditional"）。

## 适用与失效边界

- 适用于 Kimi-K3/A5 上 MegaMoE 显存预算：把"持久 CCL 预留"作为独立常驻项计入（按拓扑 MTE/URMA 取值），不要再按层/调用放大。
- `intermediate_hidden` 修正（6144→3072）是源码级建议，未见 NPU 验证；采纳前需集成回归。
- 失效边界：数值绑定 128K/TP16/EP32/moe_chunk_max_len=12800 组合；chunk moe/不同 EP/UB domain 数需按 `CalcCclBufferSizeA5` 重算。16 GiB 的"整体占用"口径（含输入输出与中间量）与 8.09 GiB 的"CCL 持久预留"口径不同，混用时须分别列账。
- 停止条件：预算合计仍显著小于实跑占用时，转向 platform/KDA workspace 与 eager 调试打印（用户已在推进，本卡不覆盖）。

## 附：断言存档

- MegaMoE 在 128K/TP16/EP32 配置下每 rank 持久 CCL 预留：MTE 1.024302959 GiB、URMA4 8.085751772 GiB（8682009856 字节）；为每模型/rank 一次直接 aclrtMalloc、注册为 CCL 内存、跨调用与层复用、位于 PyTorch caching allocator 之外，不能按 21 次调用/92 层/EP32 放大
- MegaMoE API 的 intermediate_hidden 语义为激活后宽度；模型侧传 2*3072=6144 被分配器再次乘 2（GMM1 按 12288 预算）。改传 3072 后 URMA4=5.1147 GiB、节约 2.971 GiB（MTE 微升至 1.032 GiB）；源码级修正，未做 NPU 验证
