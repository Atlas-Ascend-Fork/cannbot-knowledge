---
type: API
title: custom.npu_gather_selection_kv_cache：A3 选择缓存与原地元数据
description: 说明稀疏 Gather 的四个原地输入、实际长度返回和 TopK 分块限制，区分函数化五返回。
tags:
- task.lookup
- topic.kv_cache
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/ops/ascendc/docs/custom-npu_gather_selection_kv_cache.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/ops/ascendc/torch_ops_extension/custom_ops/csrc/npu_gather_selection_kv_cache.cpp
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/ops/ascendc/torch_ops_extension/custom_ops/csrc/ops_def_registration.cpp
  role: header
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/ops/ascendc/torch_ops_extension/custom_ops/__init__.py
  role: constraint
created_at: '2026-11-09T02:45:42Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a3
---

# custom.npu_gather_selection_kv_cache：A3 选择缓存与原地元数据

## 来源与交付范围

依据 Recipes 固定提交 `944d2d3ece86f7df33dbb0cb155c72ca619a9c66` 的独立接口文档、Schema 与 PyTorch 包装层。该接口在 `torch.ops.custom` 注册；安装并导入对应 custom_ops 包后才可能挂到 torch_npu，不能据同名前缀认定为标准 TorchNPU/OpPlugin 内置接口。来源的产品支持和软件配套分别核对；这不是 `ascend_26_0_pt28` 标准包已内置该接口的声明。

## 接口

```text
custom.npu_gather_selection_kv_cache(Tensor(a!) selection_k_rope, Tensor(b!) selection_kv_cache, Tensor(c!) selection_kv_block_table, Tensor(d!) selection_kv_block_status, Tensor selection_topk_indices, Tensor full_k_rope,  Tensor full_kv_cache, Tensor full_kv_block_table, Tensor full_kv_actual_seq, Tensor full_q_actual_seq, *,  int selection_topk_block_size=64) -> Tensor
```

## 缓存与输出语义

根据稀疏 TopK 索引从 full KV Cache Gather 到 selection Cache；full_kv_cache 可在 Host 或 Device，不限于 Host Offload。前四个输入 selection_k_rope、selection_kv_cache、selection_kv_block_table、selection_kv_block_status 均由 Schema 标记 mutation。普通入口只返回 INT32 的 selection_kv_actual_seq，shape 为 (B*S*H,)，不是返回新 Cache。

包装层的 functional 变体先复制四个原地输入，返回 (actual_seq,k_rope,kv_cache,block_table,block_status) 共五项。不要用该变体的解包方式调用普通入口；Meta 存在也不代替真实存储更新。

## 形状与条件

- 产品表只确认 A3 推理。各输入连续、ND；H 当前只能 1，TOPK≤2048。
- 两类 Cache 的 shape 为 (block_num,BLOCK_SIZE,D)，dtype 为 FP16/BF16/INT8；INT8 的 k_rope 分支只接受空 Tensor，不能随意提供非空 INT8 RoPE。
- selection 块表为 INT32(B*S*H,S_MAX_BLOCK_NUM)，状态为 INT32(B,S,H,TOPK+1) 或 packed (B*S,H,TOPK+1)，索引少一列为 TOPK。状态不仅是工作区，需保留其跨次复用语义。
- full 块表为 INT32(B,F_MAX_BLOCK_NUM)，两个实际长度为 INT32(B,)。packed T 必须可被 B 整除，不把两者长度语义推定为任意其他接口的累计边界。
- 必须满足 BLOCK_SIZE % selection_topk_block_size == 0，选择块数须满足 S_BLOCK_NUM≥B*S*H*S_MAX_BLOCK_NUM。默认 selection_topk_block_size=64，但 TOPK>32 时只支持 1，真实 TopK2048 场景必须显式改为 1。
- 来源明确支持 aclgraph，但图捕获还需保留四个 mutation 的函数化/重原地适配和地址生命周期。

应覆盖 TopK 有效/无效索引、前后步复用及原地元数据变化，并以返回实际长度限制下游读取。

- [模型中的 Offload 与缓存复用场景](../../concepts/kernels/gather_selection_kv_cache.md)


## 验证边界

核对自定义 .so、Schema、PrivateUse1/Meta 注册及所用图后端，分别比较输出、原地行为和多次调用。仅完成文档和包装层静态审阅；未分析完整 Device Kernel/Host/Tiling，未加载 .so、执行上游代码或进行设备数值和性能验证。

- [自定义算子交付与图适配](../../guides/integration/torchair/custom_operator_graph_contract.md)
- [软件栈基线](../../concepts/frameworks/ascend_software_stack_baselines.md)

## Evidence

- [固定来源 1](https://gitcode.com/cann/cann-recipes-infer/blob/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/ops/ascendc/docs/custom-npu_gather_selection_kv_cache.md)（primary）
- [固定来源 2](https://gitcode.com/cann/cann-recipes-infer/blob/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/ops/ascendc/torch_ops_extension/custom_ops/csrc/npu_gather_selection_kv_cache.cpp)（implementation）
- [固定来源 3](https://gitcode.com/cann/cann-recipes-infer/blob/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/ops/ascendc/torch_ops_extension/custom_ops/csrc/ops_def_registration.cpp)（header）
- [固定来源 4](https://gitcode.com/cann/cann-recipes-infer/blob/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/ops/ascendc/torch_ops_extension/custom_ops/__init__.py)（constraint）
