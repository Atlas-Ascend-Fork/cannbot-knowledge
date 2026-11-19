---
type: Guide
title: TorchNPU26.1版本说明：能力变更、CANN门槛和兼容边界
description: 将同提交26.1发布说明与主线配套分开，记录接口变更分组、950DT限制及GDN异步资源修复的证据范围。
tags:
- task.lookup
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/release_notes.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/release_notes.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/COMPATIBILITY.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/COMPATIBILITY.en.md
  role: constraint
created_at: '2026-11-09T16:42:20Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# TorchNPU26.1版本说明：能力变更、CANN门槛和兼容边界

## 固定来源及发布身份

固定主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf中的中英文release_notes仍描述TorchNPU26.1.0、2026年7月发布，配CANN9.1.0。它不是当前主线推荐2.14/CANN9.2的完整说明，也不覆盖锁定26.0/PyTorch2.8。平台只登记该说明涉及的A2/A3及950DT，具体API的产品、shape/dtype和版本要另查。

分支名采用v{PyTorch}-{产品版本}；本页2.7.1/2.9/2.10/2.11/2.12分别对应包2.7.1.post8、2.9.0.post6、2.10.0.post4、2.11.0、2.12.0。2.7.1列Python3.9..3.13，后四行3.10..3.13；不能以较新的主线配套页含Python3.14覆盖此发布说明。

## 兼容表与特性门槛

发布说明把TorchNPU7.3.X/26.0.X/26.1.X与CANN8.5.X/9.0.X/9.1.X全部标Y。这是粗粒度兼容说明，不保证每个新增接口都在最旧CANN存在；新增算子仍受各行依赖、框架暴露及设备范围限制，也不据Y宣称任意混装已验证。

本页新增Eager DVM融合、LibTorch Stable ABI、关键计算API的CPU标量Tensor+NPU非标量异构输入、全轴动态输入编译和950DT适配；这些是能力摘要，不承诺任意CPU/NPU混合输入、任意动态shape或任意库二进制都兼容。品牌统一为TorchNPU，但导入名torch_npu和wheel前缀保留。

## 接口变更要按类别和CANN要求消费

下表是本发布说明的变更索引，名称均在torch_npu下；它只给变更/依赖，不能替代API原型、输入约束或实际实现。原表v2.7.1后注明2.9/2.10/2.11/2.12变更同前，不将这个继承范围回推到2.8，也不当新主线完整接口列表。

| 类别 | CANN说明 | 本页接口名称 |
| --- | --- | --- |
| 新增 | >=8.5.0 | print_npugraph_tensor、npu_chunk_gated_delta_rule |
| 新增 | >=9.0.0 | npu_add_quant_matmul_、npu_dynamic_dual_level_mx_quant、npu_grouped_dynamic_block_quant、npu_mhc_post、npu_transpose_quant_batchmatmul |
| 新增 | 9.1.0 | npu_rotate_quant、npu_alltoallv_quant_gmm、npu_fused_causal_conv1d、npu_masked_causal_conv1d、npu_mhc_pre、npu_mhc_sinkhorn |
| 新增 | 不依赖特定CANN版本（原表措辞） | npu_apply_rotary_pos_emb；不等于无需CANN或可跨任意历史CANN |
| 修改 | >=8.5.0 | save_npugraph_tensor |
| 修改 | >=9.0.0 | npu_grouped_matmul_swiglu_quant_v2、npu_mla_prolog_v3 |
| 修改 | 9.1.0 | npu_rms_norm_quant、npu_scaled_masked_softmax、npu_cross_entropy_loss、npu_attention_update、npu_fusion_attention、npu_gelu_mul、npu_top_k_top_p、npu_gather_sparse_index、npu_swiglu_quant、npu_add_rms_norm、apply_rotary_pos_emb、npu_lightning_indexer、npu_quant_lightning_indexer、npu_sparse_flash_attention，以及beta的npu.finalize_dump/npu.init_dump/npu.set_dump/npu_ciou/npu_iou |

原表没有给“修改”的参数差异，不据此补造新默认值、反向或输入支持；9.1.0行也没有统一写“及以后”，保留原版本措辞。npu_apply_rotary_pos_emb与apply_rotary_pos_emb分别列新增/修改，不能按近似名字合并。

特别是npu_chunk_gated_delta_rule在此表写>=8.5，而既有部署案例报告仅CANN9.1支持且特定2.8post4未暴露。来源时期、包构建和实际实现层次不同，目前不据此发布“8.5上任意2.8即可用”的配方；应核对精确包/提交和API实证。这一分歧保留供定位，不静默覆盖部署案例。

## 950DT与已解决问题

26.1说明明确950DT的部分算子/通信约束不同于A2/A3，Inductor当时仅Triton/DVM、不支持MLIR。它不否定较新内部主线AKG/MLIR特性页，但也不能用新特性回填旧发布能力；950PR不在此表范围。

GDN自定义适配修复项同时描述aclnn_extension未传stream造成顺序/同步异常，以及EXEC_NPU_CMD_V1_EXT/V2_EXT的内存/workspace申请释放未与标准宏配套、可能影响精度。说明称已对齐标准宏且整网精度恢复，是来源报告，未经本卡复现。不能把它缩成“任意取stream即可”，异步顺序、workspace和对象寿命仍须共同核验。

本页“无遗留问题”“无漏洞修复”及历史病毒扫描只是发布声明，不证明所有模型/环境无问题；升级章节仍说业务会中断（英文may），通信无影响也不是在线业务无中断保证。实际升级需安排业务窗口并按目标组件配套处理。未升级、扫描或执行测试。

- [版本基线](../../../concepts/frameworks/ascend_software_stack_baselines.md)
- [TaskQueue算子资源契约](torch_npu_custom_op_taskqueue_adaptation.md)

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/release_notes.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/release_notes.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/COMPATIBILITY.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/COMPATIBILITY.en.md)（constraint）
