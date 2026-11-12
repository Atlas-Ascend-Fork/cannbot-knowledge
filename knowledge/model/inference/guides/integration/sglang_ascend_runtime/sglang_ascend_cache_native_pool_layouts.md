---
type: Guide
title: SGLang NPU原生KV池的FIA视图、NZ写入与PD字节布局
description: 区分MHA全层连续底座与FIA逐层视图、MLA分离/合并/FP8记录、DCP全局索引及CPU回缩的布局合同。
tags:
- task.implementation
- topic.kv_cache
- topic.data_movement.layout_transform
- topic.memory
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/memory_pool_npu.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/mem_cache/hisparse_memory_pool.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/mem_cache/device_pool_info.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/mem_cache/kv_cache_configurator.py
  role: implementation
created_at: '2026-11-08T11:53:41Z'
updated_at: '2026-11-09T04:33:25Z'
platforms: []
aliases:
- NPUMHATokenToKVPool
- NPUMLATokenToKVPool
- _mla_fia_nz_scatter_indices
---

# SGLang NPU原生KV池的FIA视图、NZ写入与PD字节布局

## MHA与FIA不是两份独立缓存

NPUMHATokenToKVPool以全层连续 [L,P,page_size,H,D] 分配K/V，额外页作padding。ASCEND_USE_FIA时对每层暴露Python list视图 [P*page_size,1,H,D]，仍共享连续底座，防止compile捕获整个多层Tensor；HiCache换维接口必须取get_hicache_transfer_buffers的原Tensor。不能把list重建为无关storage或按第一轴页号直接当token号。

常规writer按dtype/scale转换，store_dtype不同只做位视图。FIA或scatter-PA分支先核对loc行数与K/V元素数；SGLANG_NPU_USE_SCATTER_PA_KV_CACHE还要求底层op存在和store_dtype在FP16/BF16/INT8集合。否则FIA展平单例轴成3D scatter，避开部署版本对4D ScatterNdUpdate的限制；非FIA保留_reshape_and_cache。prefix-valid写入另有Triton opt-in，loc须rank2、commit_lens与设备布局配套，不能把padding候选都提交。

K-only池仅分配K并向量scatter，用于MiniMax sparse index-only层；MiniMax包装的主KV、index KV和index K仍是不同角色。

## MLA分配与opaque记录

MLA可分离K latent与RoPE，或以一个combined allocation分出共享视图。普通目标KV在DCP下rank-local，draft KV和复制的indexer保持global slots，因此padding页数、导出item_len、CPU回缩索引不能一套公式通用。启用稀疏KV卸载时native K/V为None，getter明确拒绝，必须走SparseKVCacheManager。

以下混合字节记录、Indexer scale 与 Hadamard128 说明仅适用于 `dsa_kv_cache_store_fp8=True` 的 packed DSA FP8 模式：构造条件是 index_head_dim 非空、dtype=float8_e4m3fn 且显式给出 kv_cache_dim；正常 _build_ascend_mla_kv_pool 构建路径还以 is_npu_arch35() 门控，其他架构传 None。该模式要求index_head_dim=128、latent宽度128整除，记录宽度为latent FP8字节 + RoPE BF16字节 +每128 latent一项FP32 scale；实际打包顺序为latent、RoPE、scale。它不是950共享KV API的RoPE开头/E8M0/640字节布局。indexer另有FP32 scale和Hadamard128，不能只传K位容器而漏元数据。

## FIA NZ的物理写地址

分配外壳仍为page-major，FIA按 [page,1,D/tile,page_size,tile] 读，其中tile=32/element_size。逻辑loc展开到每个D/tile块，物理行是 ((page*num_tiles+tile_id)*page_size+slot)，源按[token,tile]展平。不能用普通token-major scatter给NZ reader写入。combined与packed-FP8分支先于普通NZ分支，不能认为一个开关覆盖所有记录格式。

## 导出、回缩和状态

MHA导出K所有层后V所有层；FIA view的单row字节须乘page_size才是PD item_len。MLA导出按native/combined、indexer及scale顺序，并为global-slot条目把item_len乘DCP size；两端须同导出顺序、每项字节几何与layer映射。indexer写raw虚拟loc，不能先本地化；目标KV回缩要本地化，draft/indexer保留全局索引。FP8回缩按uint8复制opaque记录，不解量化/重新量化。

get_cpu_copy/load_cpu_copy显式NPU同步并分chunk，不是全异步零开销。conv状态辅助工厂统一成 [layers,pool,window,channels]，KDA与GDN输入轴解释不同，投机把window扩展draft_tokens-1。新增writer或PD接口时同时验证真实底座、slot映射、dtype、scale、PP/DCP与备份恢复后数值。

## 与通用HiSparse的区别

hisparse_memory_pool中的通用transfer_kv_all_layer_mla只导入CUDA/ROCm/XPU实现，其他后端为抛RuntimeError的stub。该类不是NPU sparsity-driven KV offload替代入口，不能因二者都称稀疏缓存就直接复用GPU Host/Device copy路径。

## 证据与验证边界

本卡记录固定提交的NPU分支实现合同，来源没有为本机制提供完整产品验收矩阵，保留草稿和未定位平台；源码路径存在不证明任意昇腾型号可用。本次知识摄取未执行上游代码、编译、模型推理、真机、数值或性能测试。
