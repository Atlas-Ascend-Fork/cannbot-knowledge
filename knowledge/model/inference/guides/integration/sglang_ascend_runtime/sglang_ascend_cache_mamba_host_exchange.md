---
type: Guide
title: SGLang Mamba与卷积状态的NPU HiCache搬运分支
description: 说明Mamba Host池对strided槽的staging、sync/async搬运、首层全层传输、conv-only空状态守卫和MTP独立分配回退。
tags:
- task.implementation
- topic.memory
- topic.data_movement
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/mem_cache/pool_host/mamba.py
  role: primary
created_at: '2026-11-08T12:04:51Z'
updated_at: '2026-11-08T12:04:51Z'
platforms: []
aliases:
- MambaPoolHost
- SGLANG_NPU_HICACHE_MAMBA_IO
---

# SGLang Mamba与卷积状态的NPU HiCache搬运分支

SGLANG_NPU_HICACHE_MAMBA_IO缺省sync，strip/lower后只接受sync或async，其他值抛ValueError。模块对transfer_mamba_state和direct state API分别尝试导入；导入失败只置空引用，不能由import成功推断所有分支可用。

page_first/page_first_direct且有transfer_mamba_state、无MTP draft时，H2D仅layer0一次搬全部层，后续调用跳过；temporal_state_elem_size=0时不传SSM，仍传各conv分量，适配conv-only。side slot state也在layer0先搬，必须在该层complete事件前完成，因为恢复槽的消费者等待该事件。

通用单层kernel_ascend用索引选取与to拷贝；page-first单层async调用transfer_state_per_layer_direct_pf_lf，sync用Host选层/index_select后index_copy。全层D2H对于连续Tensor，async调用direct全层API，sync优先transfer_mamba_state，否则张量搬运回退；若MTP草稿是独立分配的Sequence，bulk kernel不能直接接收，逐层选取复制。

统一状态view可能slot stride不连续，先index_select成连续staging，目标strided则传入临时连续Tensor再index_copy；必须保留该开销，不能以底层单次copy估算总恢复成本。名为MLA的通用copy被用于Mamba只因单池接口合适，不代表状态具备MLA语义。

验证需要SSM+多个conv、conv-only、slot side state、MTP、strided view与两方向；检查状态恢复后的连续生成精度以及每个slot/层映射，单KV前缀命中不能代替这些状态。async模式还需确认所需API确实可导入，不能靠模式参数保证非阻塞或收益。

## async构造期守卫

_configure_npu_mamba_io对async同时要求两个Python direct state函数非None和torch.ops.npu对应两个符号存在，否则构造期抛RuntimeError。sync日志称torch fallback，但load在原生transfer_mamba_state存在且无MTP时仍可走全层专用kernel，日志不能替代实际分支判断。

## 证据与验证边界

本卡记录固定提交的NPU分支实现合同，来源没有为本机制提供完整产品验收矩阵，保留草稿和未定位平台；源码路径存在不证明任意昇腾型号可用。本次知识摄取未执行上游代码、编译、模型推理、真机、数值或性能测试。
