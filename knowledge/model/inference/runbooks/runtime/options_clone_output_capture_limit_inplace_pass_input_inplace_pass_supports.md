---
{
  "type": "Runbook",
  "title": "npugraph_ex 副流读 host-swapped KV 窗口触发 507011（aivec EL0003 / DDR out of range）",
  "description": "Ascend NPU 上以 `npugraph_ex`（aclgraph capture & replay）运行 KVCache offload 模型（本例 GLM-5.2 缩放 sim：dies0-7 world8、32k/batch64、cp1、next_n=3、`enable_offload` + `enable_gather_prefetch` + `enable_prefetch_side_stream`）。",
  "tags": [
    "task.debugging",
    "topic.implementation.debugging"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:03Z",
  "updated_at": "2026-11-20T14:17:03Z",
  "platforms": []
}
---

# npugraph_ex 副流读 host-swapped KV 窗口触发 507011（aivec EL0003 / DDR out of range）

## 适用场景

Ascend NPU 上以 `npugraph_ex`（aclgraph capture & replay）运行 KVCache offload 模型（本例 GLM-5.2 缩放 sim：dies0-7 world8、32k/batch64、cp1、next_n=3、`enable_offload` + `enable_gather_prefetch` + `enable_prefetch_side_stream`），decode warm-up/捕获期崩溃并报 507011 `model stream execute failed` 的诊断。同场景也覆盖 eager 副流（无图捕获）的同族崩溃。

## 触发与观测

- npugraph_ex ON（副流预取）：8 rank 全崩于 decode warm-up（= aclgraph capture/首 replay）。底层真错（progress 记录 + 助手分析一致）：aivec `VEC supports illegal configurations in commands`（EL0003 Invalid_Argument），全部 vector core 同一 PC `0x12e6dbfed060`（单 kernel），带 MTE error（mte error info 0xe106000033），最终 `rtDeviceSynchronizeWithTimeout ... the model stream execute failed`（507011）。
- OFF 同配置完全跑通（MainModel decode 12.33ms/step 中位、8/8 success）→ 崩溃由 `enable_gather_prefetch=True`（副流）引入。
- eager + 副流：跑到 decode 第 ~5-6 步崩，`error code = 0x800000` "The DDR address of the MTE instruction is out of range"，与 npugraph_ex 崩溃同 PC（0x12e6dbfed060）、同 vec-error（0xb800000092）→ 同一 gather kernel、同族故障。

## 探针与操作

决定性四运行分叉（全部 32k/b64/cp1/next_n=3）：

| 配置 | 结果 | 证据 |
|---|---|---|
| npugraph_ex ON 副流 | CRASH 507011 | aivec `VEC illegal config` @aclgraph capture，PC `0x12e6dbfed060` |
| npugraph_ex ON 主流（enable_prefetch_side_stream=False） | 8/8 success | 同 gather、无副流；输出与 OFF 一致 |
| eager ON 副流 | CRASH @step~5-6 | `0x800000 DDR out of range`，同 PC/vec-error |

- bypass 探针（env 门控 `SA_ACLGRAPH_SAFE_OPTS=1`，测后已回退）：在 npugraph_ex `cache_compile` 的 compile_options 上加图模式技能的 canonical aclgraph 修复 `options={clone_output:True, capture_limit:256, inplace_pass:False, input_inplace_pass:False}` → **仍 507011，同签名**。
- 判读 op_statistic：npugraph_ex OFF/ON(main-stream) 均无 ge_graph 的 `[2064,128,1,512]` MlaProlog staging TensorMove，只有 ~50us 的小 selection-cache TensorMove（`[512,128,512]`/`[512,128,64]`/`[32,64,256]`）→ ge_graph 的 elide-break 回归在 npugraph_ex 不存在。

## 机制与判别

- 根因：副流 gather 读 follower 层的 `empty_with_swapped_memory` KV 窗口。设备页映射（halMemMap）是 stream-local 的——仅在拥有它的主流上建立/重映射（prefill `copy_` + 每步 MlaProlog in-place 写）。副流上的 gather 读到未同步的映射 → MTE 故障（eager 直接表现为 0x800000 DDR 越界；aclgraph capture 下表现为 aivec "非法配置" 后 507011）。
- 判别链：主流预取（读同一 follower 窗口）成功 → 故障与流归属相关，非 gather 算子或 MTP clamp 本身；canonical aclgraph 选项无效 → 非 aclgraph 子图隔离/stale-pointer 问题，而是 swapped-memory 原始读故障；eager 同 PC 崩溃 → 与图捕获正交。
- 未验证推断：EL0003 与 0x800000 是"同族不同表现"由同 PC 归纳；halMemMap stream-local 语义来自项目记忆与实验分叉，未读 CDD 源码确认。

## 验证信号

- 设备端错误原文（用户/日志等级）：EL0003 errorStr、0x800000 DDR out of range、507011（等级：设备功能观测）。
- 四运行分叉与 op_statistic 对比（等级：设备功能+性能观测，单次 campaign）。
- 主流 ON 相对 OFF：decode 13.40 vs 12.33 ms/step（+1.07ms）；ON 增量 = +44 个 GatherSelectionKvCache（+1080us）+76 个小 TensorMove，纯串行 gather 开销（单次观测）。

## 适用与失效边界

- 适用：offload（host-swapped KV）+ 副流读历史的任何 npugraph_ex/eager 组合；判别"崩在副流归属还是算子本身"的主流/副流分叉法。
- 边界：模型/配置层不可修——需框架级 halMemMap 跨流一致性，或把 follower 窗口常驻（违背 offload 初衷）；clamp-to-prefill-region 与 event/record_stream 改写被论证排除（崩溃发生时只读 prefill 区域、页表一致性无法表达为张量依赖）。本卡不覆盖修复本身（未修复），也不外推到非 swapped-memory 的副流场景（那类可用 `record_stream` 模板）。

## 附：断言存档

- npugraph_ex 开启副流预取（enable_gather_prefetch=True）在 decode warm-up（aclgraph capture/首 replay）全 rank 崩溃：底层为 aivec VEC supports illegal configurations in commands（EL0003），全部 vector core 同一 PC 0x12e6dbfed060（单 kernel），带 MTE error（0xe106000033），最终 507011 model stream execute failed；同配置 OFF 8/8 成功（12.33ms/step）→ 崩溃由副流预取引入。
- eager + 副流在 decode 第 ~5-6 步崩 error code = 0x800000（The DDR address of the MTE instruction is out of range），与 npugraph_ex 崩溃同 PC（0x12e6dbfed060）、同 vec-error（0xb800000092）→ 同一 gather kernel 同族故障。根因：副流 gather 读 follower 层 empty_with_swapped_memory 的 KV 窗口，设备页映射（halMemMap）是 stream-local，仅在拥有它的主流上建立/重映射，副流读到未同步映射即 MTE 故障。
- 图模式技能的 canonical aclgraph 修复 options（clone_output:True, capture_limit:256, inplace_pass:False, input_inplace_pass:False；env 门控探针，测后回退）对该崩溃无效——仍 507011 同 kernel 同签名 → 非 aclgraph 子图隔离/stale-pointer 问题，而是 swapped-memory 原始读故障；模型/配置层不可修（需框架级 halMemMap 跨流一致性或 follower 窗口常驻）。
