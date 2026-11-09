---
type: Guide
title: vLLM Ascend Triton Mamba 状态寻址、复制与线性注意力契约
description: 区分 Mamba selected-row gather/scatter、物理页步长、投机解码 pre/post copy 和 LightningAttention 四阶段状态更新；供 GDN 与混合模型缓存适配、图重放和正确性诊断。
aliases:
- gather_ssm_states scatter_ssm_states_ gather_initial_states
- precopy_mamba_align_fused_kernel postprocess_mamba_fused_kernel
- LightningAttention exclusive KV history
tags:
- task.implementation
- topic.model_serving
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/mamba/causal_conv1d.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/mamba/lightning_attn.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/mamba/postprocess.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/mamba/state_index.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/mamba/state_ops.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/v2/mamba/precopy.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/docs/gather_initial_states.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/docs/mamba_state_index.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/docs/postprocess_mamba.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/docs/lightning_attn.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/v2/mamba/docs/mamba_precopy.md
  role: constraint
created_at: '2026-11-03T06:08:49Z'
updated_at: '2026-11-03T06:08:49Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend Triton Mamba 状态寻址、复制与线性注意力契约

## 证据范围与接口分离

固定 vLLM Ascend `ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2`，程序以完整 AST 投影读取，五份文档原文读取；没有新 NPU、JIT、图或性能运行。以下四类接口共享状态概念，地址单位、索引空间和调用语义分别保留，不能互换。

## Selected-row 状态 I/O

`mamba/state_index.py` 的 `gather_ssm_states` / `scatter_ssm_states_` 将 `[N,*inner]` 视为 R 元素行，按 1024 元素 tile 复制选中的**物理行**。每行须连续，行间可有 padding 与非零 storage offset；用真实 stride(0)，不是逻辑 R 推算页距。wrapper 检查 ndim、非空池、row stride、indices 的一维 int32/int64 与同 device；gather 另检查 BOOL mask。false mask 输出零且不读对应 history，可提供被屏蔽的 sentinel；true mask 的 index 范围由 caller 保证。gather 可重复读，scatter 的重复目的行可能竞态，需要唯一索引与无跨 program alias。输出 dtype 与 scatter store 可转换，纯复制验证应先做同样转换再精确比较，并检查未选行和 padding 未改。

`mamba/state_ops.py::gather_initial_states` 是另一公开 helper。NPU 使用最多 16KiB tile，mask 同时保护 index 与 state load，不按全池 contiguous 复制；空 batch/空行直接返回。非 NPU 先选 row0 再 where 置零，不能获得 NPU 的 no-read 保证且需要有效 row0。它的输入检查、返回 dtype 和可选参数与 state_index 不是同一 ABI。GLM 文档描述的 scatter 是模型 helper 调用原地 `npu_scatter_nd_update_`，不能据此宣称走 state_index 的 Triton scatter。

`mamba/causal_conv1d.py::extract_last_width` 从每请求 end position 减 width 取历史列并重排；本 helper 不补齐短请求边界。caller 必须保证窗口不跨相邻 packed request，并遵守导出的 Native PAD_SLOT_ID 协议。

## 投机解码前后复制

`mamba/postprocess.py` 计算 `running=computed+scheduled-draft`、`new=running+accepted-1`；PRECOMPUTED 模式反推 running。`aligned=floor(new/block_size)*block_size`，仅当 aligned>=running 才复制；`bias=aligned-running`、目的列 `aligned/block_size-1`。conv 复制有效尾 `width-bias`，temporal 从源列+bias 取整行。源目的列相同会把 accepted 更新为1，bias=0 时无需复制。输出 accepted buffer 与原地更新是不同版本调用契约。

每个 state 用 group id 选择其 block table，batch 行与 req-slot 由 idx_mapping 分开；负 req-slot 跳过。block ID 转 int64 后乘**字节**页距，实际复制长度为逻辑数据量，不能把 padding 整页搬走。temporal 对齐地址用 uint64，尾字节由 tile0 处理；未对齐有 byte fallback。SD/DS conv 布局需匹配 dim-row 元数据。文档同时记录版本门禁的 2D/3D grid；本固定实现的分支与 caller launch 必须成对，不能把 TEMPORAL_TILES 套在所有版本上。特别核对 DS 分支的多 tile 参与条件，避免未经 caller 约束就宣称无重复写。

`v2/mamba/precopy.py` 在 forward 前由 `(num_reqs,num_states,TEMPORAL_TILES)` grid 复制旧 running state；src_col<0 或 src_col==dst_col 跳过，DS/SD conv 只有 tile0 搬有效尾，temporal 多 tile 拆分 uint64 主体再由 tile0 搬尾。与 postprocess 不同，这个实现没有未对齐的 byte-only 主体 fallback，因此 temporal 的基址与页距应满足 8-byte 对齐；bias、列与 block id 的有效范围由 caller 保证。复制接口不提供请求生命周期、跨设备一致性或 sealed plan 本身。

## LightningAttention 四阶段及易错边界

`mamba/lightning_attn.py` 的 BailingMoE prefill 顺序为 diagonal output → block KV outer-product → exclusive KV prefix scan → 非对角累加。固定 BLOCK=256，即使传其他 block_size 也不改变 tile。返回的 KV[i] 是第 i 块**之前**的 state，最后一项才是最终 state；外层函数 clone history，底层 apply/reduce 会原地写入，生产 prefix wrapper 再复制最终 state 回 cache。

同块衰减为 `exp(-s*(t-j))`，跨块遵循来源现有实现的 `exp(-s*(t-j-1))`，额外因子 exp(s) 是移植约定。独立参考若套统一精确 recurrence 会得出另一数值，修改前先与上游协调。分段 prefill 只有 256 对齐切分才保留该块约定。diagonal store 后再次累加会发生一次输入 dtype 舍入；FP32 KV 并不等于输出全程无舍入。

部署入口 batch=1；d、e 要满足 power-of-two，e 可二等分，可靠范围 d<=128。外层 d>128 的分块未同步切 history 且只返回末块 KV，不能推广为任意 head dim 支持。代码为 inference forward，没有 backward。diagonal 对尾行有额外 where 清零以避免 cube 收到残留 NaN，其他阶段的 masked load 不能自动继承该保证。没有 do_not_specialize，新增形状可能增加四个 kernel 的编译变体。文档记录 A2/A3/950 路径及既有测试，310P 是另一 fallback；这些不构成本次硬件运行。

## Agent 验收与定位

先记录 state 的逻辑 shape、真实 stride、storage offset、dtype、每 group 的物理 block table、request mapping 与 accepted 语义；再验证 fresh/history、重复读、唯一写、负 sentinel、1023/1024/1025 行尾、字节尾和 padding guard。graph replay 用同一 buffer 改 indices、flags、accepted 与 state 内容检查 device 侧读到新值，禁止用 host 预读替代。纯搬运精确比较；LightningAttention 采用其块衰减参考与分阶段舍入，并检查长尾 NaN/Inf。上游测试命令和历史 A3 测量可作为复现入口，不能写作本次已跑或跨硬件性能保证。
