---
type: Guide
title: vLLM Ascend自有SparseFlashMla Host：当前模板、分页stride与LSE
description: 串接自有SparseFlashMla的Torch输出、BF16 TND/PA_BBND Host门禁、AICPU metadata及arch22/arch35执行；核对S2块单位、稀疏有效前缀/页stride、split-G同步、softmax加权FD、sink与缓冲复用，保留大型Host剩余与SDK/数值/性能边界。
tags:
- task.implementation
- task.debugging
- topic.attention
- topic.model_adaptation
- topic.graph_execution
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_mla/sparse_flash_mla_torch_adpt.h
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_mla/op_host/sparse_flash_mla_def.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_mla/op_host/sparse_flash_mla_infershape.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_mla/op_host/checkers/checker_context.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_mla/op_host/checkers/checker_adapter.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_mla/op_host/checkers/checker_runner.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_mla/op_host/checkers/base_checker.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_mla/op_host/checkers/common_checker.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_mla/op_host/checkers/paged_attention_checker.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_mla/op_host/checkers/metadata_checker.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_mla/op_host/checkers/seq_len_checker.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_mla/op_host/checkers/sparse_compression_checker.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_mla/op_host/checkers/mask_checker.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_mla/op_host/checkers/sinks_checker.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_mla/op_host/checkers/softmax_lse_checker.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_mla/op_host/checkers/sparse_flash_mla_checker.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_mla/op_kernel/sparse_flash_mla.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_mla/op_host/sparse_flash_mla_tiling.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_mla_metadata/op_host/op_api/aclnn_sparse_flash_mla_metadata.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_mla_metadata/op_host/op_api/aclnn_sparse_flash_mla_metadata.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_mla_metadata/op_host/op_api/sparse_flash_mla_metadata.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_mla_metadata/op_host/op_api/sparse_flash_mla_metadata.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_mla_metadata/op_host/sparse_flash_mla_metadata_check.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_mla/op_kernel/sparse_flash_mla_kernel_metadata.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_mla_metadata/CMakeLists.txt
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_mla_metadata/op_host/CMakeLists.txt
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_mla_metadata/README.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_mla_metadata/docs/aclnnSparseFlashMlaMetadata.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_mla_metadata/examples/test_aclnn_sparse_flash_mla_metadata.cpp
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_mla_metadata/examples/test_torch_sparse_flash_mla_metadata.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_mla_metadata/op_kernel_aicpu/CMakeLists.txt
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_mla_metadata/op_kernel_aicpu/sparse_flash_mla_metadata_aicpu.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_mla_metadata/op_kernel_aicpu/sparse_flash_mla_metadata_aicpu.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_mla_metadata/op_kernel_aicpu/sparse_flash_mla_metadata_aicpu.json
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/common/op_kernel/aicpu_common.h
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_mla/CMakeLists.txt
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_mla/README.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_mla/docs/aclnnSparseFlashMla.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_mla/docs/design.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_mla/docs/ratio2_a2a3.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_mla/examples/test_aclnn_sparse_flash_mla.cpp
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_mla/op_host/CMakeLists.txt
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_mla/op_host/checkers/base_checker_sparse_flash_mla.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_mla/op_host/checkers/checker_runner.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_mla/op_host/checkers/checker_sources.cmake
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_mla/op_host/checkers/common_checker_sparse_flash_mla.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_mla/op_host/checkers/mask_checker_sparse_flash_mla.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_mla/op_host/checkers/metadata_checker_sparse_flash_mla.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_mla/op_host/checkers/paged_attention_checker_sparse_flash_mla.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_mla/op_host/checkers/seq_len_checker_sparse_flash_mla.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_mla/op_host/checkers/sinks_checker_sparse_flash_mla.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_mla/op_host/checkers/softmax_lse_checker_sparse_flash_mla.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_mla/op_host/checkers/sparse_compression_checker.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_mla/op_host/checkers/sparse_flash_mla_checker.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_mla/op_host/sparse_flash_mla_tiling.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_mla/op_kernel/arch22/sparse_flash_mla_arch22_metadata.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_mla/op_kernel/arch22/sparse_flash_mla_common_arch22.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_mla/op_kernel/arch22/sparse_flash_mla_csa_block_cube.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_mla/op_kernel/arch22/sparse_flash_mla_csa_block_vector.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_mla/op_kernel/arch22/sparse_flash_mla_csa_kernel.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_mla/op_kernel/arch22/sparse_flash_mla_swa_block_cube.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_mla/op_kernel/arch22/sparse_flash_mla_swa_block_vector.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_mla/op_kernel/arch22/sparse_flash_mla_swa_kernel.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_mla/op_kernel/arch35/common/buffers_policy_3buff_sfa.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_mla/op_kernel/arch35/common/flash_decode.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_mla/op_kernel/arch35/common/static_buffer.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_mla/op_kernel/arch35/common/static_matmul.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_mla/op_kernel/arch35/sparse_flash_mla_common_arch35.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_mla/op_kernel/arch35/sparse_flash_mla_csa_block_cube_arch35.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_mla/op_kernel/arch35/sparse_flash_mla_csa_block_vector_arch35.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_mla/op_kernel/arch35/sparse_flash_mla_csa_kernel_arch35.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_mla/op_kernel/arch35/sparse_flash_mla_kvcache.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_mla/op_kernel/arch35/sparse_flash_mla_swa_kernel_arch35.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_mla/op_kernel/arch35/util_regbase.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_mla/op_kernel/sparse_flash_mla_common.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_mla/op_kernel/sparse_flash_mla_template_tiling_key.h
  role: implementation
created_at: '2026-11-03T01:56:48Z'
updated_at: '2026-11-03T06:11:48Z'
platforms: []
aliases:
- npu_sparse_flash_mla
- SparseFlashMlaChecker
- SMLAInfoParser
- TilingForSparseFlashMla
- MakeSparseFlashMlaOutputs
- aclnnSparseFlashMlaMetadataGetWorkspaceSize
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend自有SparseFlashMla Host：当前模板、分页stride与LSE

## 任务与固定范围

适配新模型的SWA/压缩KV，或遇到“Python签名接受但Host拒绝”、分页view读错和LSE轴错位时，沿当前可达入口核对。本卡固定Main ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2，选定2489行真实源码：17份adapter/定义/推形/checker/dispatch全文，加2575行大tiling的482行明确选段。随后补读metadata Host校验/API及布局头6份1487行全文，两组共3976选定行；legacy checker、其余parser辅助、AICPU排程实现及大型Device模板没有因此完成摄取。

未导入或执行上游、UT、编译、JIT、设备、网络或NPU。OpDef的硬件注册和dynamic flags、kernel分支存在均不是平台验收；保持draft/空平台。这是自有csrc Host/dispatch知识，不宣称完整Operator实现、CANN执行器、数值或性能闭包。

## 先确认消费者是哪一个

| 入口 | 本卡可确认的差异 |
|---|---|
| 自有npu_sparse_flash_mla | 本地Torch adapter→aclnnSparseFlashMla；当前parser收窄BF16、TND query/PA_BBND KV、SWA或CSA模板，shared checker的query/KV head维为512 |
| 外部FlashMLA | [另一合同](vllm_ascend_flashmla_dcp_execution_contract.md)维护576维query、128-token页、NTD输出及DCP schedule；不能搬它的shape/LSE轴来调用本入口 |
| MixedQuant/TurboQuant | [量化执行](vllm_ascend_turboquant_execution_contract.md)维护不同quant mode、紧凑行和外部adapter，不能把共享checker中的variant枚举当本算子已支持量化 |

Python端Tensor可创建、OpDef可推形、parser可选择模板、tiling可生成key和Device真正执行，是不同门禁。失败先定位哪一层，不通过改dtype、删mask或临时contiguous复制掩盖消费者不匹配。

## 当前parser比签名和枚举更窄

入口先取platform/core信息，仅接DAV_2201与DAV_3510且AIC/AIV都非0。Parse在通用layout/template解析后，明确拒绝非TND query、非PA_BBND KV、非BF16 query以及非SWA/CSA模板。OpDef默认BSND、通用checker列出FP16/BSND/HCA/ORI_SPARSE、kernel中有FP16分支，不开放这些当前被更早parser挡住的组合。

ori KV始终必需。无compressed KV的普通原缓存选择SWA；compressed KV加compressed sparse indices选择CSA；有compressed KV但无其indices选择HCA后被当前模板门禁拒绝。A5上original sparse indices可选择ORI_SPARSE或ORI_CMP_SPARSE，仍不能越过SWA/CSA门禁；DAV_2201的original-sparse特例走SWA并先要求ori_mask_mode=0。不能把这条兼容路径推广到A5或全部DSpark配置。

后续DAV_2201走旧SMLATilingCheck，其他已接受架构走SparseFlashMlaChecker和共享checker链。本卡完整阅读后者，旧checker只确认调用边界；shared规则不自动成为所有架构的完整允许矩阵。[V4.1编译范围](../models/vllm_ascend_deepseek_v41_platform_boundary.md)中的收窄说明也不替代每层实际Host校验。

## 声明optional不等于可以省略

当前parser要求ori KV、PA original block table和sink；CSA还要求compressed KV及compressed sparse indices。共享checker另要求metadata为INT32向量[1024]，sink为FP32向量[query heads]，不是任意标量或一个“占位None”。metadata与sink在OpDef和Torch签名标optional只是接口声明。

Torch metadata helper先按第一份存在的长度/TopK tensor选择输出device，没有输入时默认npu；缺失的可选长度在此helper中转为同device空INT32 tensor，输出固定1024个INT32。它调用独立aclnnSparseFlashMlaMetadata生成内容，下文补齐其Host校验与launcher，AICPU内的排程/内容生成仍未读。空占位约定不能机械套到主Attention的必需sink、metadata或KV。

固定1024容量不证明metadata内容适用于新batch。producer与消费者的heads、压缩比、mask/window、layout、长度和有效TopK必须对应，图重放也要保持真实刷新与存储寿命；不能只复用同shape或清零metadata后宣称有效。

## 长度、分页和TopK合同

shared checker要求ND描述、正shape，query heads在1..128、KV heads为1，未量化query和KV末维512且dtype一致；当前入口还先限定BF16。PA block size的通用范围是1..1024，不等于任意值都已完成模板/真实性能验收。

TND query需要INT32 cu_seqlens_q[B+1]；PA KV使用各自INT32 block table[B,正容量]与seqused长度[B]，不是传KV的TND cu数组。当前parser的GetActualseqInfo对可达SWA/CSA仍要求original seqused；shared helper里“有TopK长度可省seqused”的局部逻辑与错误文案不能越过这项更早约束。DAV_2201还明确拒绝非空compressed TopK length。

TND sparse indices形状为[T,1,K]、TopK length为[T,1]，不能把一个batch的长度向量冒充逐query有效TopK。存在compressed KV时ratio在1..128；缺compressed KV时ratio只接受0/1，并拒绝其indices、block table、residual、长度等悬空输入。compressed causal mask3且ratio不等于1时需要INT32 residual[B]。无mask的sparse分支另需要对应TopK length，但该局部条件不开放parser未编译的模板。

ori mask只允许0/3/4，compressed mask只允许0/3；window>=-1，非Band ori mode4时两window必须-1，没有compressed KV时compressed mask必须0。shared checker还要求softmax_scale有限。所读checker以描述/存在性/形状为主，未闭合全部parser内容处理、所有block ID/indices范围、cu单调/末值、真实padding与metadata数值安全；这些必须按实际producer和设备另外验证。

## IgnoreContiguous与页stride的实际边界

OpDef让ori/cmp KV IgnoreContiguous，只表示不强制自动整理，并非任意view都正确。tiling优先从可选输入stride API取stride0，再试InputIsView/GetInputStride；SDK不给有效值时，会告警并用storage shape推连续stride0。非连续页在这条fallback中不能凭shape获得真实pitch，必须核对所装CANN接口与日志。

parser还收集dynamic input stride向量。CheckContiguous对PA从axis1开始、其他layout从axis0开始，校验向量长度并比较该起始轴与计算出的连续stride；其实现不是逐轴验证全部stride。不能把注释“其余轴连续”误读为已完整证明任意高维alias/stride安全，更不能通过构造某个相等轴绕过真实布局合同。

tiling将ori/cmp stride0分别送入参数。验证须保存view自身地址、storage offset、真实page pitch及所需extent，并检查与block table/注册地址相容；不要contiguous后沿用旧写端、传输或graph地址。

## 输出和LSE轴不能照搬FlashMLA

Torch adapter先检查query非空及BSND/TND rank，再用empty_like(query)分配Attention输出。return_softmax_lse=False时返回空FP32向量；True时从存在的KV取head数，TND LSE分配为[KV heads,T,query heads/KV heads]，BSND形状为[B,KV heads,S,group]。当前单KV head下TND就是[1,T,Hq]，不是外部FlashMLA的[Hq,T]。

GE推形同样让attention_out复制query shape，LSE dtype为FP32；shared checker在需要LSE时核对head整分和对应shape。只有推形成功不能证明真实数值、空请求、全mask、sink语义或跨rankLSE合并正确。图/通信消费者必须按实际返回轴变换，不能仅因最后维是heads就广播通过。

## tiling、workspace与graph责任

DoOpTiling读取真实AIC/AIV，计算blockDim，分配库workspace并加按架构/模板产生的staging需求；还调用稀疏物理地址向量化和FlashDecode staging预算函数。本卡只读调用与最终记账，未把这些预算helper及Device消费逐项闭合，不从一个默认值推全部UB/HBM成本。

tiling记录mask、window、两个block size、各自stride与compressed参数。最终key含layout、template、splitG、headRatioOne、batch consistency和vectorize标志；DAV_3510在G>64时选splitG。第一个FLASH_DECODE字段当前传0，不能因模板参数名或staging函数名推断另一FlashDecode模式已可达。schedule mode1和某个key成功生成，不代表所有资源大小、capture或数值已运行通过。

OpDef注册ascend910b/910_93/950及DynamicShape/Rank等能力，实际parser、编译key和二进制仍收窄。Torch convenience入口会准备输出/metadata存储；CANN workspace/executor、原地输入刷新、输出与sink/metadata保活、capture/replay地址是否稳定，均需沿具体运行环境验证。这里没有把dynamic flag当作任意shape可在同一graph重放的承诺。

## dispatch停止于Device模板入口

已读131行kernel入口按__CCE_AICORE__分arch35与arch22头文件，再按dtype和SWA/CSA等模板调用Init/Process。__CCE_AICORE__==310是编译架构分支标识，不能按数字把它解释为310P硬件支持。混合Cube/Vector任务、tiling结构匹配和参数顺序可在此追踪；所包含的数千行CSA/SWA/softmax/KVCache模板、内存隔离、并发与性能没有因此完成分析。

接入先留actual op/包/架构、当前模板key、query/KV/TopK/长度/sink/metadata、page stride及workspace证据，再比较参考数值和未选页隔离。随后覆盖空/PAD、跨页、compressed residual、graph多次刷新与错误恢复，最后测Host开销、临时显存和Attention时延。本次没有执行这些步骤；不删除Host拒绝来制造新模型可用结论。

## Metadata生产端：workspace准备与真正执行分开

aclnnSparseFlashMlaMetadataGetWorkspaceSize先拒绝空workspaceSize/executor输出指针，创建本次executor，读取实际SoC、Cube/Vector core及系统deterministic等级。等级3映射batch consistency；查询失败只warning，不能把日志或默认值当当前确定性已生效。通过ParamsCheck后对非nullptr长度/TopK输入加入Contiguous步骤，再把AICPU任务加入executor，最后返回workspace字节与executor；Phase2才在调用者stream上CommonOpExecutorRun。

因此workspace查询成功不是metadata已经写完，Phase2提交也不能由此推导跨stream消费者已同步。caller须保证输入、输出metadata、workspace/executor覆盖实际异步寿命，并在Attention读取前建立依赖。Contiguous可能增加拷贝/临时分配，不能从便捷API名推“Host完全无开销”；具体capture、executor重用和SDK完成语义没有运行验证。

L0层用静态AicpuTaskSpace登记9个可选长度/TopK输入及heads、ratio、mask/window、SoC/core和一致性等属性，输出直接是caller给的metadata。布局头固定1024个INT32，AIC最多36核、每核9字段，AIV最多72核、每核8字段，结构900项小于总容量；这是编译ABI，不是本次设备core实测。1638行AICPU排程主体与398行配套头未读，不能凭launcher和容量推断每字段内容、负载均衡或数值已闭合。

## Metadata校验与Attention允许矩阵取交集

Host要求KV heads1、head_dim512、query heads在1..128；SoC字符串包含Ascend950时接受该范围内head ratio，其余要求ratio为二次幂。Cube/Vector core必须在1..36/1..72，query heads128还拒绝任一core数为1。这些是该版本静态边界，不适合手填核数来伪造另一设备支持。

max_seqlen各属性要求非负，BSND另需相应正上界；这不同于外部FlashMLA用-1的协议。metadata仍保留BSND/TND等更宽接口，而主Attention当前parser只编译TND/PA_BBND SWA/CSA，所以metadata成功不能解除前文门禁。非950的compressed TopK只允许0/512/1024，非零CSA ratio为1/2/4，零TopK的HCA要求ratio128；HCA的metadata可准备不等于主入口可运行HCA。

950的compressed ratio可在1..128、mask可0/3；Band ori mask4要求oriTopk=0，窗口可用-1表示无限。非950的普通Band窗口固定127/0，original TopK非零分支要求mask0及非负窗口，并在同时有compressed KV时继续保留限制。无compressed KV时，非950 metadata强制ratio0；950的这一分支没有同样的ratio检查，主Attention仍有自己的缺cmp仅0/1规则。不能拿producer一处未拒绝当作端到端允许。

## 空占位、batch来源与尚未验证的内容

IsTensorExist以非空指针、rank>0且第0维>0判断存在，空INT32占位被当作缺省；它不是主Attention所有optional参数的通用空值协议。query batch优先从seqused_q向量长度取得，其次TND cu长度减1，最后才用batch_size属性；ori/cmp KV也按各自来源推导并比较。记录实际来源，不能只把一个batch_size标量视作所有producer的一致性证明。

同时传seqused与TND cu时核对B和B+1；metadata输出必须[1024] INT32，非950 compressed TopK length保留字段不接受非空。TND TopK length的Host检查核rank2及KV-head轴，但没有query总token属性来证明其首轴等于真实T；主Attention还会独立检查。Host校验没有读取cu/seq/TopK各元素证明单调性、可见长度、索引范围或实际metadata内容，输入的值域仍须由真实producer与设备取证。

这些补充仅闭合Host存在性/shape/选路与双阶段launcher。仍未执行metadata或Attention，没有将声明dynamic shape、空占位、Contiguous、AICPU任务入队或返回成功改写为graph安全、生成正确或性能结果。


## AICPU metadata：长度、mask与真实输入身份

继续全文读取SparseFlashMlaMetadata的AICPU cpp1638行及头398行，补其README/API、两个例子及构建注册10来源，并复用前述QLI已读的公共属性helper。头部与QLI头逐行diff、C++例子与已读QLI例子diff、API代码与本族独立例子diff后审阅全部差异；它们仅减少重复阅读，不把两套metadata ABI视为相同。以下为固定源码分析，未执行编译、真机、数值或性能测试。

Compute依次Prepare、BalanceSchedule、GenMetadata，失败返回KERNEL_STATUS_PARAM_INVALID。AICPU额外检查TND各cu首项0且不减，seqused非负且不超过BSND max或TND前缀差，cmp residual在[0,ratio)。ori/cmp检查受has_ori_kv/has_cmp_kv控制；缺输入数据指针时部分检查直接跳过，因此Host必传、shape、dtype和core容量检查仍不能省略。

TopK长度值的全数组非负检查仅在该侧TopK非0、mask0且数据存在时进入，并要求元素容量不小于有效query总数。它没有在该循环完整验证每项<=TopK；主调用者仍须保持左对齐有效索引、TopK末轴、长度与当前请求/层相符。不能以AICPU成功证明稀疏索引每个值都可访问。

B优先seqused_q首维，再TND cu_q长度减1，最后batch属性；每请求长度优先seqused，再cu相邻差，最后max属性。PA的稀疏侧缺长度时，内部可用UINT32_MAX作上界哨兵，再由TopK约束切片；这不是物理页容量，也不解除主Attention仍需seqused_ori_kv的要求。压缩侧先恢复`cmp_len*ratio+residual`原坐标长度，以此对齐causal/band，再转回压缩索引。

普通ori/cmp范围独立计算：ori先进入展平S2任务区，cmp紧接其后。原始窗口和压缩序列的token位置、S2块索引、TopK列表槽、最终物理页地址是不同单位，不根据一个字段名直接交换。Sparse-ori且无cmp的路径按行块内最大ori_topk_length规划，并截到oriTopK；一个块覆盖多query行时不能只取首行长度作为全块预算。

## 架构分块与batch consistency来自运行栈

非950内部计划S2块512；若该侧稀疏，则M通常为G，否则dense M为`floor(256/G)*G`。950 M为G、S2块128；G>64时标记split-G并把有效调度AIC数减半，序列化时为每个逻辑计划写两份相同FA范围，供两半head并行消费。不能把设备物理核数、逻辑计划核数与重复FA条目数当作同一个变量。

本族L2在查询阶段通过aclrtGetSysParamOpt读取ACL_OPT_DETERMINISTIC，值恰为3才传is_batch_consistency=True；读取失败只告警，初始值0使该开关保持False。它是运行栈系统参数，公开函数原型没有单独布尔参数；不能仅在caller配置里写同名字段就认为实际AICPU已开启。

batch consistency开启时允许FD，并按本行ori+cmp有效总长计算归约块：先整除32，再向S2基础块对齐，最小一个基础块。ori/cmp各自ceil-div为归约块数；真实基础S2 loop数另行记录，不能用归约块数替代算子缓冲轮次。归约块由行自身决定，意图是减少周围batch变化对归约树的影响；这不是本次测得的跨batch bitwise一致性。

未开启时supportFd默认False，不将类存在FD代码描述成默认所有SWA/CSA都会切S2。分配优先整batch、整M行；FD允许后再按归约块切分并强制非空核至少分一个块。单块cost仍以16行/64列对齐，权重6/10，区分ori/cmp及尾块；cost是源码负载估计，不是毫秒或真实性能。

## FD workspace与输出初始化的差异

跨核切开的行记录BN2/M、首个partial workspace索引、分份数与M范围；batch consistency额外把尚未处理的归约块计入分份数，保持同一行后续partial索引连续。FD再按split份数*M量分给AIV。此处fdMSize保留S1G/M大小，QLI的相应字段会除以G转Q行，不能复用两族字段单位或同容量buffer。

GenMetadata清零SmlaMetadata结构，写每AIC 9项FA与每AIV 8项FD，共900个uint32；1024容量的剩余124项没有由本函数保证清零。非split-G路径第9个FA字段保持清零默认；split-G路径把观测到的最大S2 loop数写入两份FA字段。只靠API页将其泛称max_s2_block_num不足以覆盖该实际写入条件。

全空Q/K工作域仍生成至少1个AIC，终点为B*Hkv、M/S2终点0，AIV归并保持关闭。所读SparseMLA CalcSplitPlan在cost分完即停止，没有QLI producer里额外把尾随零cost batch推到末核范围的专用分支；不能从QLI的初始化规则外推本族所有混合零cost边界已验证。全空、部分空、尾随零cost和稀疏长度0需分别与主kernel结果检查，当前未执行并确认缺陷。

## 文档、安装与实际主算子必须成套

固定metadata文档声明A2/A3与950PR/950DT支持，并声明该接口支持aclgraph；这限定metadata接口，不能解除本卡前述实际主parser仅BF16 TND/PA_BBND与SWA/CSA的范围。HCA、BSND或更一般KV布局可出现在metadata说明/样例中，计划可生成不证明当前主算子模板可执行。

API页把s2BaseSize写为固定512、mBaseSize写为G，是非950某些路径的概述；当前源码950用128、dense非950 M可能大于G，以真实分支为准。A2/A3稀疏ori模式要求TopK=indices末轴K，ori_topk_length在[0,K]且左对齐；局部metadata长度可选不解除配套主算子的页长度必传。文档与源码各自的范围保留，不把说明书一个“支持”词提升为整模型验证。

构建遍历子目录，Host登记aclnn，AICPU仅在安装CANN依赖构建分支收集cpp/json，注册SparseFlashMlaMetadata与libtransformer_aicpu_kernels.so；安装包/生成器/运行栈仍需匹配。JSON的flagAsync=False不使外层API同步，workspace查询成功也不是任务写完。

C++样例按两阶段执行、同步stream后D2H读900字段，并借ScopeGuard释放各输入、输出和workspace；Torch例子则给具体CSA参数。这些是调用示意，未执行且不可作为主Attention或图捕获成功记录。新模型分别核实际API导出、系统确定性级别、当前长度/TopK/页身份、计划中的FA/FD单位与下游workspace，再比较输出和时延；主Attention Device计算、归约同步和数值闭包继续待完成。


## Device增补范围与当前可达模板

本节继续摄取本族余下41份来源、17413行的程序/文档语义，包括arch22与arch35的CSA/SWA Cube、Vector、kernel，KV取址、FlashDecode、静态buffer/matmul和tiling结构。代码采用完整去注释结构投影；同族实现先读基线，再审阅所有新增/替换程序和复用映射，保留同步、宏与尾块分支。API页保留比较表达式与全部例子程序，不把HTML空白投影称为原始全文。前文“Device未读”的历史范围由本节具体范围补齐；2575行Host tiling仍只读原明确选段，外部SDK、未引用公共模板与实机数值/性能没有因此闭合。

当前编译键继续以Host/parser交集为准：arch22的SWA/CSA保留head-ratio-one分支；arch35保留split-G与CSA物理地址向量化分支。FLASH_DECODE字段仍固定0，内部FD归约阶段的存在不开放另一个模板模式。公开README更宽的FP16/BSND/HCA/原始稀疏声明及kernel潜在分支不能解除当前BF16、TND/PA_BBND、SWA/CSA门禁。D=512表示K与V各512，非外部FlashMLA的另一组维度；不能因其中含448+64分量而缩短V。

## 同族执行差异矩阵

| 维度 | arch22 | arch35 |
|---|---|---|
| 计划基础S2 | 512；CSA gather使用3个GM槽 | 128；metadata的S2区间还需乘归约块所含基础块数 |
| 调度流水 | CSA/SWA使用3份RunInfo、预取/排空3级，head-ratio-one有专门FIX/MTE3同步 | CSA有4份RunInfo与3级预取/排空；SWA为3份RunInfo、PRELOAD_NUM=2，无CSA gather前级 |
| head拆分 | head-ratio-one不是通用G分支的简单改shape | G>64的split-G由两AIC各处理一半head，两个逻辑计划共享gather槽，AIV再分搬运任务 |
| KV地址 | PA使用真实page stride，稀疏索引经逻辑token→page→页内偏移 | 可先向量化为64位元素偏移；不是绝对指针或字节地址 |
| 跨S2结果 | 在线softmax后累积输出 | 在线softmax、跨核FD及batch-consistency固定归约块，三者不可互换 |

arch35分核后没有工作量的AIC仍需消费与同伴对应的FA_S2_MAX_NUM同步轮次，包含flag15的空轮次；新模型改head布局时不能直接提前return。arch22的head-ratio-one路径也换用了专门跨核flag/pipe和MM2写出路径，不能只验证矩阵维度就复用另一分支。

## 稀疏列表、长度与PA地址的责任

CSA的有效稀疏计数使用“有效非负前缀，随后负值padding”的布局，arch22还通过二分查找首个负值。arch35搬运的整组快速分支不会为每个位置重复通用合法性检查，尾组可在两索引均负时停止；不能把任意内部空洞的稀疏列表当作受支持布局。per-query TopK length与末轴容量、实际KV长度必须一致；metadata成功只证明已读producer所检查的内容，不证明每个稀疏ID合法。

arch22原始稀疏取址会拒绝负值或超过该请求实际长度的逻辑索引；部分压缩/arch35快速路径主要拒绝负值，没有统一验证正索引、block-table页ID和物理页容量。跳过的搬运行也不能一概推为已清零：需同时核最终mask、有效前缀和复用槽。caller必须提供合法逻辑索引及实际可访问页，不能靠输出“看起来有限”证明无越界。

PA地址由pageId乘各自stride0再加页内偏移得到；不能用block_size*D替代非连续cache的page pitch。arch35向量化先按log2(block_size)拆页号，再用MULL/进位生成64位元素偏移，两uint32交错存储；尾部无效槽可写全1表示-1。其移位依赖Host相应的二次幂门禁，不能从另一个通用checker允许1..1024推得全部数值可用。正的稀疏ID仍需caller在取block-table前保证范围。

长度优先实际seqused，再cu相邻差，再静态上界。query的累积长度使用带零头的B+1协议；compressed长度恢复为`actual_cmp*ratio+residual`后对齐causal边界。arch22 CSA局部计算仍从cu相邻差取compressed数量，文档提示TND padding相关差异；当前parser主路径是PA，不能把潜在非PA问题直接宣称为当前PA已复现缺陷。

## Metadata单位、split与空工作

metadata的S2 start/end是归约块坐标。arch35消费者把它换成`block_index*baseBlockNumPerReductionBlock*128`，先定位ori段、再定位cmp段，最后应用mask/window与首尾边界。它不是GM行偏移，也不等于稀疏数组槽号。batch consistency把行的总可见负载按32分份并向128对齐、至少128；实现最多为33个归约块预留相应区间。固定分块意图不能描述成已测跨batch bitwise一致。

全空与部分空不能合并处理。kernel在needInit时先把输出和LSE清零并做全局同步；部分query/KV不可见时，实际core计划、needInit及FD条目仍决定哪些位置写出。ori实际长度为0可使SWA/CSA本轮提前无任务，即使另一侧存在缓存；caller应与Host的ori必需合同一并核对，不能仅看cmp非空推断有输出。LSE初始化为0是实现行为，不把它包装为所有全mask场景的数学定义。

## Softmax、sink与FD合并

QK/softmax累计使用FP32，中间P与最终输出按模板dtype和CAST_ROUND等分支回写。sink相当于值为0的额外注意力项：改变分母，不增加KV token。它只在首个S2 split及一致性归约块0加入，其他partial从负有限max/零sum开始；跨核FD不能再次加入sink。

FD暂存的是已经按各partial归一化的FP32输出及该partial的max/sum。合并权重为`exp(partial_max-global_max)*partial_sum`，先加权再归一化；不能直接平均partial输出，也不能把归约树改成按rank无权求和。多于两份的一致性路径按实际次序逐次合并，并用合并LSE/max表达继续下一轮；是否返回单独LSE还有独立copy分支。移植到DCP或其他归约器时必须保留单位、权重和sink只计一次。

## 缓冲容量、别名与同步

arch35 Cube把P两槽置于L1首32KiB，随后Q三槽各32KiB及KV三槽各128KiB，总512KiB；L0A双16KiB、L0B双32KiB、L0C双128KiB。Q的512维搬运拆256+256，并在最后S2轮次推进Q环；Q/KV、P和RunInfo的mod3/mod2/mod4不是同一个游标。Fixpipe双目标与两AIV的等待配对，不能把一方完成当双方可覆写。

arch35普通稀疏且返回LSE的静态UB区域合计216576字节；batch consistency另加4096至220672字节，含共用softmax/统计、stage0/2及P区域。物理地址预处理与FD阶段复用相同UB，不应把各阶段容量相加制造不存在的同时峰值，也不能在跨阶段缺同步时视为天然安全。GM另有3槽gather、辅助索引、向量化地址及FD/intra/cross-core区域；split-G时逻辑槽数与GetBlockNum的预算项不同。实际Host总workspace仍应与未读tiling剩余helper及库workspace对齐，不能只从某个Device局部公式决定分配大小。

## 静态风险与适配验收材料

固定arch35物理地址预处理在compressed causal分支存在直接读取residual的路径，而前述Host在ratio=1时未必强制该输入；另一个消费者路径有nullptr保护。这里只记录跨路径静态合同差异，不宣称已经运行复现：需检查真实caller是否总传residual、实际所选vectorize键及当前SDK行为。

API样例提供FP16与一种LSE存储示意，当前parser却收窄BF16、Torch输出LSE轴也有精确约定；示例代码不等于当前所有样例参数都能运行。适配Agent应保存实际Host拒绝、编译key、输入dtype/stride、有效前缀/页身份、metadata内容与workspace分区，再分别比较跨页、负padding、空/部分空、split-G、sink、FD和图多次刷新；本次没有执行这些设备验收或报告数值/性能成绩。
