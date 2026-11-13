---
{
  "type": "Runbook",
  "title": "mc2 moe_ep_dispatch+combine 级联 fp8 卡死定位：combine 543 行 while 循环等待 WaitDispatch，fp8 slot 布局额外携带 scales 而 host 缓冲区公式按 bf16 口径",
  "description": "moe_train_test.py 以 fp8 跑 mc2/moe_ep_dispatch+combine 级联时卡死在 moe_ep_combine 算子 543 行 while 循环、bf16 正常。",
  "tags": [
    "task.debugging",
    "topic.mixture_of_experts"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": []
}
---
# mc2 moe_ep_dispatch+combine 级联 fp8 卡死定位：combine 543 行 while 循环等待 WaitDispatch，fp8 slot 布局额外携带 scales 而 host 缓冲区公式按 bf16 口径


## 适用场景

moe_train_test.py 以 fp8 跑 mc2/moe_ep_dispatch+combine 级联时卡死在 moe_ep_combine 算子 543 行 while 循环、bf16 正常。两个定位会话的源码阅读证实：combine 的 RecvPhaseReduce 以 while (CompletedtokenNum != tPerCore_) 自旋，每个 token 只有 WaitDispatch 成功才计数，若远端 dispatch 数据/通知未按预期到达则永不退出；fp8_e5m2/e4m3 时每个 dispatch slot 额外携带 scales（scalesOffset_、metaOffset_ += scalesBytesAlign 仅 fp8 分支、tiling 含 SCALES_GROUP_SIZE_MXFP=32/SCALES_ALIGN_EVEN=2 等 fp8 专用常量），而 host 侧 MoEElasticBuffer.get_moe_ep_ccl_buffer_size 以 max_out_dtype_size=2（sizeof(bf16)）计算 dispatch_per_slot_bytes 且不含 scales 字节。两会话在给出最终结论前被截断，fp8/bf16 差异与缓冲区口径不一致是否即卡死根因未在轨迹内验证。

适用：mc2/moe_ep_dispatch+combine 级联在 fp8 下卡死、bf16 正常时的第一轮源码定位（等待循环 + slot 布局 + host 缓冲区口径三处对照）。失效/边界：本候选只到“结构差异已客观读出”层级；“fp8 slot 含 scales 而 host 缓冲区公式按 bf16 且不含 scales 导致窗口/通知错位进而死循环”是待验证假设，两会话均在结论前截断；未运行任何复现或 dump 实验。

## 触发与观测

### 事实 c1

卡死点定位（用户报告 + 源码证实）：mc2/moe_ep_combine 的 RecvPhaseReduce 在 moe_ep_combine.h:543 以 while (CompletedtokenNum != tPerCore_) 自旋——循环内对每个 token 先查 tokenStatusTensor，未完成者仅当 WaitDispatch(tokenIdx, copyCount, tStart_) 成功才 CompletedtokenNum++ 并置位；若远端 dispatch 数据/通知未按预期到达，CompletedtokenNum 永不等于 tPerCore_，与用户报告的 fp8 卡死、bf16 正常现象对应。


### 事实 c2

kernel 侧 fp8/bf16 结构性差异：x 为 fp8_e5m2_t/fp8_e4m3fn_t 时（dispatch_epilogue Init，仅 fp8 constexpr 分支）scalesOffset_ = Ceil((uint32_t)(axisH_ * sizeof(XType)), UB_ALIGN) * UB_ALIGN、scalesBytes_ = tilingData->cfg.scalesBytes、metaOffset_ += Ceil(scalesBytes_, UB_ALIGN) * UB_ALIGN，即每个 dispatch slot 在 token 数据之后额外携带 scales；dispatch tiling 侧存在 FP8_DTYPE_SIZE = 1UL、SCALES_GROUP_SIZE_MXFP = 32、SCALES_GROUP_SIZE_PERGROUP = 128、SCALES_ALIGN_EVEN = 2（fp8 align 2）等 fp8 专用常量；bf16 路径无该分支。


## 探针与操作

### 事实 c3

host 侧缓冲区公式按 bf16 口径：MoEElasticBuffer.get_moe_ep_ccl_buffer_size 以 max_out_dtype_size = 2（sizeof(bf16)）计算 hidden_align = inline_align(hidden * max_out_dtype_size, ub_align)、dispatch_per_slot_bytes = inline_align(hidden_align + metadata_bytes * 2 + ub_align, win_addr_align)、combine_per_slot_bytes = inline_align(hidden_align + ub_align, win_addr_align)，公式中不含 fp8 scales 字节。


### 事实 c4

> 该 claim 未被账本采纳（缺少逐字机制片段：绑定）；其边界性内容（两会话均在结论前截断、未运行复现）已并入『适用场景』与『适用与失效边界』，按待验证假设口径表述。


## 机制与判别

以下为轨迹事件原文中的完整机制单元：

### 补充机制片段

```
541:     uint32_t CompletedtokenNum = static_cast<uint32_t>(0);
542:     uint32_t copyCount = topK_ * FLOAT_PER_UB_ALIGN;
543:     while (CompletedtokenNum != tPerCore_) {
544:         for (uint32_t tokenIdx = tStart_; tokenIdx < tEnd_; ++tokenIdx) {
545:             if (tokenStatusTensor(tokenIdx - tStart_) == 1) {
546:                 continue;
547:             }
548:             if (!WaitDispatch(tokenIdx, copyCount, tStart_)) {
549:                 continue;
550:             }
551:             CompletedtokenNum++;
552:             tokenStatusTensor.SetValue(tokenIdx - tStart_, 1);
553:             ProcessTopKToken(tokenIdx);
554:             LocalTensor<XType> ubResultBf16 = ubX_;
555:             Cast(ubResultBf16, ubAccFp32_, RoundMode::CAST_RINT, axisH_);
556:             SyncFunc<AscendC::HardEvent::V_MTE3>();
557:             DataCopyPad(combinedXGm_[tokenIdx * axisH_], ubResultBf16, xCopyParams);
558:         }
559:     }
560: }
```

### 补充机制片段

```
251:     if constexpr (Std::IsSame<XType, fp8_e5m2_t>::value || Std::IsSame<XType, fp8_e4m3fn_t>::value) {
252:         scalesOffset_ = Ceil((uint32_t)(axisH_ * sizeof(XType)), UB_ALIGN) * UB_ALIGN;
253:         scalesBytes_ = tilingData->cfg.scalesBytes;
254:         scalesElems_ = (scalesBytes_ == 0U) ? 0U : (scalesBytes_ / sizeof(ScalesType));
255:         uint32_t scalesBytesAlign = Ceil(scalesBytes_, UB_ALIGN) * UB_ALIGN;
256:         metaOffset_ += scalesBytesAlign;
257:         tpipe_->InitBuffer(ubScalesBuf_, scalesBytesAlign);
258:         ubScales_ = ubScalesBuf_.Get<ScalesType>();
259:         recvScalesGm_.SetGlobalBuffer((__gm__ ScalesType *)recvScales);
260:     }
```

### 补充机制片段

```
83:         win_addr_align = 512
84:         ub_align = 32
85:         max_out_dtype_size = 2  # sizeof(bf16)
86:         metadata_dtype_size = 4 # sizeof(int32)/sizeof(float)
87:         state_dtype_size = 4  # sizeof(int32)
88:         mb_conversion = 1024 * 1024
89:         local_exerts_num = num_experts // world_size
90:
91:         # state
92:         dispatch_count_size = world_size * inline_align(local_exerts_num * state_dtype_size, win_addr_align)
93:         dispatch_notify_size = world_size * win_addr_align
94:         combine_state_size = num_max_tokens_per_rank * topk * win_addr_align + world_size * win_addr_align
95:         state_buffer_size = dispatch_count_size + dispatch_notify_size * 2 + combine_state_size
96:
97:         # data
98:         metadata_bytes = inline_align(topk * metadata_dtype_size, ub_align)
99:         hidden_align = inline_align(hidden * max_out_dtype_size, ub_align)
100:         dispatch_per_slot_bytes = inline_align(hidden_align + metadata_bytes * 2 + ub_align, win_addr_align)
101:         combine_per_slot_bytes = inline_align(hidden_align + ub_align, win_addr_align)
```

## 验证信号

本轨迹内验证层级：source_read（两个会话的纯源码阅读定位，未运行任何复现实验）。


## 适用与失效边界

适用：mc2/moe_ep_dispatch+combine 级联在 fp8 下卡死、bf16 正常时的第一轮源码定位（等待循环 + slot 布局 + host 缓冲区口径三处对照）。失效/边界：本候选只到“结构差异已客观读出”层级；“fp8 slot 含 scales 而 host 缓冲区公式按 bf16 且不含 scales 导致窗口/通知错位进而死循环”是待验证假设，两会话均在结论前截断；未运行任何复现或 dump 实验。
