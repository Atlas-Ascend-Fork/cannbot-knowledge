---
type: Guide
title: vLLM Ascend量化LightningIndexer V2 Host：尺度、候选块与分页stride
description: 沿量化LightningIndexer V2的Host、AICPU和两架构Device核对scale/page stride、FP32/half/BF16舍入、candidate source/consumer、无序TopK、FD工作区及图入口；保留offset哨兵、参考收集与缓存身份边界。 3164增量补align64 TopK内部宽度、LD逐segment读取和255-repeat分段向量循环，保留旧版不同工作区合同。
tags:
- task.implementation
- task.debugging
- topic.attention
- topic.precision
- topic.model_adaptation
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2/op_host/quant_lightning_indexer_v2_tiling.cpp
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2/op_host/vllm_ascend_quant_lightning_indexer_v2_def.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2/op_host/quant_lightning_indexer_v2_infershape.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2/quant_lightning_indexer_v2_torch_adpt.h
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2/tests/ut/op_host/arch22/test_quant_lightning_indexer_v2_tiling.cpp
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2/op_host/quant_lightning_indexer_v2_tiling.h
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2_metadata/CMakeLists.txt
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2_metadata/op_host/CMakeLists.txt
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2_metadata/op_host/quant_lightning_indexer_v2_metadata_check.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2_metadata/op_host/quant_lightning_indexer_v2_metadata_infershape.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2_metadata/op_host/op_api/aclnn_quant_lightning_indexer_v2_metadata.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2_metadata/op_host/op_api/aclnn_quant_lightning_indexer_v2_metadata.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2_metadata/op_host/op_api/quant_lightning_indexer_v2_metadata.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2_metadata/op_host/op_api/quant_lightning_indexer_v2_metadata.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2_metadata/op_api/aclnn_quant_lightning_indexer_v2_metadata.h
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2_metadata/op_api/aclnn_quant_lightning_indexer_v2_metadata.cpp
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2_metadata/op_api/quant_lightning_indexer_v2_metadata.h
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2_metadata/op_api/quant_lightning_indexer_v2_metadata.cpp
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2/op_kernel/quant_lightning_indexer_v2_metadata.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2_metadata/README.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2_metadata/docs/aclnnQuantLightningIndexerV2Metadata.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2_metadata/examples/test_aclnn_quant_lightning_indexer_v2_metadata.cpp
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2_metadata/examples/test_torch_quant_lightning_indexer_v2_metadata.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2_metadata/op_graph/quant_lightning_indexer_v2_metadata_proto.h
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2_metadata/op_kernel_aicpu/CMakeLists.txt
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2_metadata/op_kernel_aicpu/quant_lightning_indexer_v2_metadata_aicpu.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2_metadata/op_kernel_aicpu/quant_lightning_indexer_v2_metadata_aicpu.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2_metadata/op_kernel_aicpu/quant_lightning_indexer_v2_metadata_aicpu.json
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/common/op_kernel/aicpu_common.h
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/lightning_indexer_v2/op_kernel/arch35/vf/common/lightning_indexer_v2_vector1_base.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2/CMakeLists.txt
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2/README.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2/docs/aclnnQuantLightningIndexerV2.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2/docs/qli_v2_two_level_topk_design.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2/examples/test_aclnn_quant_lightning_indexer_v2.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2/op_host/CMakeLists.txt
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2/op_kernel/arch22/quant_lightning_indexer_v2_common_arch22.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2/op_kernel/arch22/quant_lightning_indexer_v2_kernel_arch22.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2/op_kernel/arch22/quant_lightning_indexer_v2_service_cube_arch22.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2/op_kernel/arch22/quant_lightning_indexer_v2_service_vector_arch22.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2/op_kernel/arch22/quant_lightning_indexer_v2_vector.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2/op_kernel/arch35/quant_lightning_indexer_v2_common_arch35.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2/op_kernel/arch35/quant_lightning_indexer_v2_kernel_arch35.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2/op_kernel/arch35/quant_lightning_indexer_v2_service_cube_arch35.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2/op_kernel/arch35/quant_lightning_indexer_v2_service_vector_arch35.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2/op_kernel/arch35/vf/quant_lightning_indexer_v2_topk.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2/op_kernel/arch35/vf/quant_lightning_indexer_v2_vector1.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2/op_kernel/arch35/vf/vf_topk.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2/op_kernel/arch35/vf/vf_topk_16_gather_quant_v2.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2/op_kernel/quant_lightning_indexer_v2.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2/op_kernel/quant_lightning_indexer_v2_template_tiling_key.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2/op_kernel/vllm_ascend_quant_lightning_indexer_v2.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2/tests/CMakeLists.txt
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2/tests/assets/compare_batch_outputs.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2/tests/assets/impl/batch_consistency.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2/tests/assets/impl/compare.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2/tests/assets/impl/golden.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2/tests/assets/impl/inputs.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2/tests/assets/impl/metadata_inputs.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2/tests/assets/impl/metadata_protocol.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2/tests/assets/impl/npu_preprocess.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2/tests/assets/spec.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2/tests/pytest/README.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2/tests/pytest/batch/list_pt_from_excel.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2/tests/pytest/batch/quant_lightning_indexer_v2_pt_loadprocess.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2/tests/pytest/batch/quant_lightning_indexer_v2_pt_save.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2/tests/pytest/batch_isolated_run.sh
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2/tests/pytest/collect_perf_data.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2/tests/pytest/pytest.ini
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2/tests/pytest/qliv2_parameter_normalization.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2/tests/pytest/qliv2_test_utils.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2/tests/pytest/quant_lightning_indexer_v2_acl_graph.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2/tests/pytest/quant_lightning_indexer_v2_golden.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2/tests/pytest/result_compare_method.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2/tests/pytest/test_qliv2_test_utils.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2/tests/pytest/test_quant_lightning_indexer_v2_batch.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2/tests/pytest/test_quant_lightning_indexer_v2_paramset.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2/tests/pytest/test_quant_lightning_indexer_v2_single.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2/tests/pytest/test_run.sh
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2/tests/ut/CMakeLists.txt
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2/tests/ut/op_host/CMakeLists.txt
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2/tests/ut/op_host/arch22/CMakeLists.txt
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2/tests/ut/op_host/arch35/CMakeLists.txt
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2/tests/ut/op_host/arch35/test_quant_lightning_indexer_v2_tiling.cpp
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2/tests/ut/op_host/test_quant_lightning_indexer_v2_infershape.cpp
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2/tests/ut/op_host/test_quant_lightning_indexer_v2_utils.h
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2/torch_extension/__init__.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2/torch_extension/csrc/quant_lightning_indexer.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2/torch_extension/graph_convert_quant_lightning_indexer.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/quant_lightning_indexer_v2/torch_extension/quant_lightning_indexer.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/csrc/attention/quant_lightning_indexer_v2/op_kernel/arch22/quant_lightning_indexer_v2_service_vector_arch22.h
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/csrc/attention/quant_lightning_indexer_v2/op_kernel/arch22/quant_lightning_indexer_v2_vector.h
  role: implementation
created_at: '2026-11-03T02:06:41Z'
updated_at: '2026-11-03T05:35:22Z'
platforms: []
aliases:
- QLIV2InfoParser
- QuantLightningIndexerV2Tiling
- QuantLightningIndexerCandidate
- ConstructQuantLightningIndexerOutputTensor
- VllmAscendQuantLightningIndexerV2
- aclnnVllmAscendQuantLightningIndexerV2MetadataGetWorkspaceSize
- QLIV2Vector.BuildCandidateMask
- QLIV2Vector.ProcessTopK
- quant_lightning_indexer_candidate_source
- quant_lightning_indexer_candidate_consumer
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend量化LightningIndexer V2 Host：尺度、候选块与分页stride

## 任务与固定范围

新稀疏模型接量化Indexer、切换量化格式、启用两级候选TopK或复用分页K view时，核对实际消费者而非只替换dtype。固定Main ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2，全文读取Host tiling1803行、OpDef192、infer133、既有owner的Torch adapter159和arch22 UT191；常量头仅读89–108，初组共2498选定行；再补metadata校验、两套API/推形/布局与构建调用13来源1200行。源码和测试只作数据，未导入上游、运行UT、编译、JIT或NPU；保持draft/空平台。

[既有V4.1范围](../models/vllm_ascend_deepseek_v41_platform_boundary.md)保留Torch源owner和模型/编译说明；本卡补Host细节，不由允许分支、dtype注册或UT预期升级成整项硬件支持。Indexer TopK不等于[SparseFlashMla读端](vllm_ascend_sparse_mla_host_dispatch_contract.md)本身，也不同于[SFA卸载的fused LIM](vllm_ascend_sparse_layerwise_offload.md)，其weights与scale ABI不能混用。

## 分架构门禁与量化组合

Host只接受DAV_2201/3510且AIC/AIV非0。Q/K dtype必须一致，两个descale dtype也必须一致；KV heads固定1，head_dim128。有效Torch输入各维为正且非空，G=Q heads/K heads在DAV_2201仅32或64，DAV_3510不超过64；UT注释仍写“必须64”，不能覆盖代码新增32路径。

| quant_mode | Q/K dtype | Q/K descale dtype | weights dtype |
|---|---|---|---|
| 1 FP8 | E4M3FN | FP32 | FP32 |
| 2 INT8 | INT8 | FP16 | FP16 |
| 3 MXFP8 | E4M3FN | E8M0 | FP32 |
| 4 HiFloat8 | HiFloat8 | FP32 | FP32 |
| 5 MXFP4 | E2M1 FP4 | E8M0 | FP32 |

DAV_2201只允许mode2、K为PA_BBND、TopK在1..2048、cmp_ratio为1..128的二次幂且不返回values；DAV_3510 Host有表中五路、TopK在1..8192、cmp_ratio在1..128及return_value0/1。两端mask只接受0/3，max_seqlen_q>=-1。OpDef默认quant_mode1/layout BSND不是跨架构可直接启动的默认配方；Host允许也不证明当前编译模板/安装包包含全部分支。

## scale的shape不是统一per-token向量

普通FP8/INT8的scale比对应Q/K少最后feature维，保留其余各轴；HiFloat8分别要求单元素向量[1]。MX模式scale比对应Q/K多一维，前缀保持一致，最后两维为[D/64,2]，D128时即[2,2]。E8M0两个字节合计对应每32个feature一个scale，不能flatten后按FP16 per-head尺度交给同一kernel。

weights的token/batch/query/head轴必须匹配Q，sparse indices的KV-head轴与TopK尾轴匹配实际K和配置；输出INT32，values声明BF16。shape正确不证明checkpoint校准、scale数值或量化误差合格；本Host没有运行这些数值验证。

## 长度与分页输入按布局给出

PA K要求四维[blocks,block_size,1,128]、block_size为16倍数且在1..1024，block table二维、seqused_k必传且INT32，cu_seqlens_k必须不传。非PA不能传block table；TND K要cu_seqlens_k，BSND K不接该数组。layout映射中出现PA_BSND别名不代表早先属性校验开放该字符串；以完整调用链为准。

TND Q需要cu_seqlens_q，B从其元素数减1取得，并与PA seqused_k/block table或TND K的cu数组对齐；总T来自query.shape[0]。GetS1Size明确不在tiling读取TND tensor内容，批前缀由Device读取，不能为推最大query在Host强行GetData。BSND Q不传cu_seqlens_q，可选seqused_q按相应规则给出。

cmp_ratio不等于1且mask非0时必须有INT32 residual，元素数对应B；其他条件反而要求residual缺省。metadata虽然声明optional，tiling要求非空指针且总元素数1024，OpDef指定INT32。单有1024个元素的检查不等于已验证其rank、内容和producer对应；下文补其Host校验与launcher，本节只到Host，后文补AICPU排程。

部分错误文案把B、B+1或参数名写混，定位时对照真实比较表达式和输入快照。已读代码没有把所有cu单调/末值、block ID范围、residual值与TopK排序/数值都验完；shape通过不是缓存可读性证明。

## candidate source、consumer与off不是同一协议

candidate_mode1输出候选块，mode2消费既有候选，mode3关闭；非off当前只在DAV_2201实现。candidate_topk_blocks实际校验为(0,2048]内64的倍数，block size固定8；头文件/属性注释称“仅2048”不替代已经放宽的校验。consumer必须提供INT32候选，按BSND的B×S×Nkv×blocks或TND的T×Nkv×blocks检查总元素数；这不充分验证每个轴或候选块内容合法。

这里存在真实接口层差异：Torch构造和tiling的candidate分支允许TND，要求cu_seqlens_q与PA K；GE infer却在candidate source mode1时显式只接受BSND。Meta Torch返回前没有调用GE/tiling，因此Meta输出成功不能证明TND source真实执行成功。保留这项版本/入口待验边界，不把某一层“支持”描述成完整协议已通。

候选块必须与对应请求、query行、层策略、原K与压缩比一致，不能因numel相同而复用另一批候选。下文已补Device二级TopK的选块、合并和排序实现，仍不声称跨层选择质量或加速已经通过。

## 实际Torch出口与推形范围

Torch根据Q layout与K的head轴分配indices：[B,S,Nkv,TopK]或[T,Nkv,TopK]。当前QuantLightningIndexerCandidate在调用前固定return_value=0，values为空BF16；仅mode1分配候选输出，其他mode返回空INT32候选。A5 Host/GE存在return_value1分支，不代表这个当前Torch出口已经导出scores，更不能把空values当零分数。

输出indices只是位置结果；output_idx_offset存在不证明跨序列/压缩坐标转换正确。记录输入、候选、偏移与最终indices使用的坐标空间，并在真正Attention消费前校验可见长度和页边界。GE推形/Meta不执行TopK、CANN或设备读写。

## 页stride、FP4单位与大地址边界

K与K-scale的OpDef是IgnoreContiguous。tiling优先采用GetDynamicInputStride描述；aclnn动态图可能缺该描述，因此Torch显式把两者stride(0)传属性兜底，再没有才使用紧凑语义。PA只允许第0轴padding，内轴要匹配连续布局；描述缺失时部分内轴检查也无法证明真实几何，不能把缺少错误当任意view支持。

显式正stride需至少容纳紧凑块，描述路径对FP4 K的stride要求2元素对齐、MX scale也要求2元素打包。GenerateInfo在FP4动态描述分支把logical stride0除2转为packed uint8单位，而显式属性分支直接使用传入值；必须按实际torch/CANN版本核对两路单位，不能只凭dtype名认为等价。目录内参考torch_extension还有入口差别：普通QuantLightningIndexer显式传两个0禁用stride属性兜底，Candidate入口才传key.stride(0)和scale.stride(0)；不能把某个adapter的兜底能力视为所有导出都具备。

另有宽度边界：Torch属性入口是int64，Host当前以int32属性指针读取，再把结果存到uint32 tiling字段。不能把调用者Python int64推成任意大page pitch已安全；记录实际tensor stride、属性、描述和最终tiling数值，对大跨度与混合打包单独取证。本卡没有运行并确认溢出或单位错误，保留为静态适配风险。

## tiling、graph与测试证据的停止点

workspace按架构、真实core数、序列容量及中间TopK缓冲计账，使用的最大TopK预算在两架构不同；代码中的“6M/48k”注释不能当所有配置的实测字节或时延。tiling写入quant/candidate/ratio、stride及长度几何，key按Q/K/output dtype、是否paged与两layout生成，schedule mode1。key没有单独列出某属性不代表其运行时tiling字段可删除。

图捕获需继续固定cache/scale/metadata、候选与输出存储的真实寿命及刷新；DynamicShape/Rank标记不保证同graph任意shape或换backing。下文已补两架构主Indexer、量化matmul、TopK和候选模板；外部CANN执行器、MicroAPI/编译器语义与实机尚未闭合，不把源码阅读当完整Operator验收。

所读arch22 UT静态定义INT8 PA路径、mask/residual以及dtype、layout、TopK、ratio、head/block与metadata拒绝；本次又补默认CaseParam/helper、arch35 tiling及推形UT，均未运行。新模型先保存实际架构/入口、mode/dtype/scale shape、候选身份、长度与stride证据，再与参考位置/分数及下游Attention比较，最后测量Host、量化、TopK和整体性能。

## Metadata：同名两套API不能视为相同检查路径

该目录存在op_host/op_api与平行根op_api两套导出。前者包含quant_lightning_indexer_v2_metadata_check.h并调用完整ParamsCheckQliV2；根op_api/aclnn实现则在本翻译单元定义同名检查函数，直接返回ACLNN_SUCCESS。后者不由名称或注释自动继承前者的538行检查。两个CMake这里只确认子目录遍历与add_modules_sources调用，没有展开构建helper或核验真实所链接二进制；适配要保存实际源码/构建产物身份，不能默认任一已安装库必走完整检查。

两套API都创建executor，读取真实SoC与core，对非nullptr长度输入安排Contiguous，再添加AICPU metadata任务；返回workspace/executor后，由Phase2的CommonOpExecutorRun在指定stream执行。workspace查询或任务入队成功都不证明metadata已写完、Attention已可跨stream读取。caller维持输入/输出、workspace/executor的实际异步寿命并建立依赖；同shape不允许跨配置或换device盲复用旧内容。

L0 launcher的两份cpp经逐字节SHA对比一致，同名公开header也一致；这两对按同SHA全文复用记录，不把其他有差异的文件伪装成相同版本。AICPU获得5个可选长度/residual输入及heads、TopK、quant、layout、mask、ratio、core和SoC属性，没有candidate mode/候选块身份参数。metadata成功不能证明另一路candidate source/consumer已关联到正确请求、层和K版本。

## Checked metadata分支的允许矩阵与值域边界

完整Host检查与主tiling共同要求KV heads1、head_dim128；非950的Q heads32/64、TopK<=2048、mode2和二次幂ratio，950分支Q heads1..64、TopK<=8192、mode1..5及ratio1..128。max_seqlen_q/k允许-1，但BSND要求相应正上界。这是所读checked分支的行为，不外推到平行stub或实际AICPU数值/硬件能力。

长度存在性按非空指针、rank>0和第0维>0判断，Torch helper将None转成空INT32占位。query batch优先seqused_q长度，再TND cu长度减1，最后batch_size属性；K同理，Host核两端batch及同时传cu/seqused的B/B+1关系。部分K来源的诊断字符串误写Q名称，按真实取值对象定位，不因报错标签把两套tensor交换。

存在一个静态raw-pointer边界：checked CheckConsistencyQliV2在判断IsTensorExist之前就读取cmpResidualKOptional的view首维。Torch的[0]空占位与直接C接口传nullptr不是同一输入，不能由optional签名承诺raw nullptr安全；本卡未执行并确认故障，也不通过吞检查或随意制造数据掩盖不匹配。无mask或ratio1的主Indexer还要求residual缺省，须同时满足producer与消费者的实际约定。

metadata推形只给[1024] INT32，不运行输入校验；Torch的Meta路径也直接返回预分配shape而不调用真实API。布局头规定AIC最多36、AIV最多72，LI/LD各核8字段，共864项落在1024容量内；它不同于SparseFlashMla的900项布局，不能互换同为1024-word的buffer。完整Host检查没有读取cu/seq/residual数值证明单调、可见长度或任务排程正确。后文分别补AICPU与Device，所有路径均未运行，不能把形状、stub返回或Meta成功写成执行验收。


## AICPU producer：运行阶段才检查长度值

继续全文读取QuantLightningIndexerV2Metadata的AICPU cpp960行、头326行、公共属性helper148行，以及固定README/API说明、两个样例、proto和构建注册，共新增10来源。API文档代码块与已读C++样例逐行对照，差异含公开名与带VllmAscend前缀的实际调用名；没有把文档块当已执行样例，也未运行AICPU。

Compute先Prepare，失败返回KERNEL_STATUS_PARAM_INVALID；成功后按BalanceSchedule再GenMetadata执行，不进入Indexer数值计算。Prepare要求core数、SoC、heads、D和TopK属性；读取batch/max-length/layout/mask/ratio可选值。虽然proto要求quant_mode、类也保留quantMode_，当前Prepare没有读取该属性，调度模型不能替代Host对量化格式的验证。

cu数组在TND且数据存在时检查首项0、后项不减，允许相邻相等的空请求；seqused检查非负，并在BSND下不超过max、在TND且cu存在时不超过相应前缀差。residual若存在要求0<=value<cmp_ratio。缺数据指针时这些检查直接返回true，不在AICPU层补齐必传存在性、shape、dtype、core上下界或1024容量检查；正确调用仍依赖前述Host入口。平行stub API不能因最终也会调用AICPU而被视为与checked入口完全等价。

B优先seqused_q首维，再TND cu_q长度减1，最后batch属性；每请求Q/K长度优先seqused，再TND相邻cu差，最后maxSeqlen。压缩K的原坐标长度为`K_cmp*cmp_ratio+residual`，residual缺省时省略尾项。保持压缩坐标与原始causal对齐，不把metadata内的S2块坐标或raw token长度混作相同单位。

## AICPU负载与FD边界

SoC字符串包含Ascend950时选择950计划，其他字符串退到910B计划；这是内部分类，不是允许任意未知硬件。910B使用每Q块4行、S2块2048；950通常4行/S2块128，TopK>6144时Q块改2行。分组G=Hq/Hkv，M块为Q行数*G。真正支持范围仍以前述Host及公开产品表交叉核对。

AICPU按Q/K长度分别ceil-div得到行块与S2块，跟踪最大K长度。950仅在最大K不少于TopK、且大于`5*128`时开放FD，其他情况不启用；910B这份producer默认不启用FD。不是每个950请求都拆S2，也不能把任意短序列的FD关闭解释成故障。

无mask使用全部还原K范围；right-down causal以原K长度减Q长度对齐，每个Q块的末行确定可见右端。范围先clip到原K，再按压缩率整除得到有效压缩长度和S2块上界。整除余数与residual共同影响边界；metadata不计算具体TopK分数，不能替代主kernel的数值与mask验证。

单块成本为`6*ceil(M/16)+10*ceil(S2/64)`，区分行尾/列尾；这些是调度权重，不是测得微秒。分配先尝试整batch，再整行；允许FD时才继续按块或强制至少一个块。预算由剩余cost/剩余AIC重算，非FD至少容纳最重一行。不能仅按请求数均分推断每核执行量，也不把源码中的cost当端到端性能。

跨核切开的同一行记录BN2/M、首个partial workspace索引、S2分份数和有效Q行数，再按分份数*行数把归并工作拆给AIV。LI范围的BN2/M/S2起点来自前核终点，终点为本核游标；LD给出具体归并任务和M起点/行数。所有字段需与主Indexer的当前metadata/partial workspace解释一致，不能复用另一个TopK、ratio或长度快照生成的计划。

## 全空初始化、布局与图重放责任

全部请求的Q或K工作域为空时，producer仍启用1个AIC、范围结束BN2=B*Hkv、M/S2终点0。一般计划分完正cost后，还把尾随零cost请求纳入最后AIC范围，以便下游初始化对应输出。直接跳过metadata/主Indexer而保留上次输出不是这份空工作量协议；更不能与KPool的追加dummy request机制互换。

GenMetadata将QliV2Metadata结构清零，再写每AIC的8项LI范围和每AIV的LD归并字段，未使用core enable=0。结构大小为864个uint32，输出容量仍声明1024个INT32；本函数只清该结构，不证明尾部160项已清零或可携带自定义数据。输出1024容量与SparseFlashMla相同，布局仍不兼容。

主Indexer对LI/LD的消费、分数/TopK/归并及同步已在下文补充，AICPU结果仍必须属于当前输入长度、heads、TopK、mask、ratio和实际core快照；graph重放不能只因buffer地址/shape没变就省略内容刷新。JSON注册的flagAsync=False描述内核注册，不等于外层stream已对caller同步，也不是跨stream可见性保证。

AICPU CMake在安装CANN依赖构建条件下收集cpp/json，并注册DNN_VM_AICPU、RunCpuKernel和libtransformer_aicpu_kernels.so。存在源码不证明安装产物含相应注册或运行库；缺kernel错误应核实际构建/包与符号，不能靠切换metadata内容绕过。

## 公开说明和样例的版本差异

固定README/API产品表声明950PR/950DT、A2/A3支持，推理310系列与旧训练系列不支持；A2/A3文档仍限定Hq=64，而checked Host已允许32/64。因此Hq32是实现可见范围，不提升为文档已承诺或实机已验证范围。平台声明只针对该metadata接口，不把整张Indexer/模型卡升级为稳定平台覆盖。

API页使用aclnnQuantLightningIndexerV2Metadata名称，仓内C++样例调用带VllmAscend前缀的名称；Torch样例又通过cann_ops_transformer.quant_lightning_indexer_metadata入口。新框架先核所链接导出与实际构建，不按标题替换符号。C++样例初始化TopK=0、Hq=1、BSND K，与文档有效TopK及非950门禁不一致；它只能作生命周期/打印布局示例，不能直接当可运行的支持配方。

样例在阶段二之后明确同步stream再D2H读结构，最终释放tensor、workspace与设备/stream；这说明读取依赖的调用位置，不证明本次执行成功。真实Agent验收分别记录阶段一、阶段二与同步返回，检查长度拒绝、全空初始化、末尾零cost批、FD分核和对应下游结果，再测实际性能；当前仍未做编译、真机、数值或性能测试。

## 主Indexer Device：架构、舍入与同步不能合并成一条公式

本轮完整读取本族61个剩余文件及直接引用的LightningIndexer向量公共base：C++采用去注释的全结构投影和两架构完整新增/上下文diff，Python采用完整AST投影；文档全文读取，重复C++样例与实际样例作完整差异对照。只有修改路径的辅助脚本replace_path.py在全文审阅后排除于生产sources；它不参与算子计算。固定源码中的实现、参考及历史记录分别解释，不执行其中任何代码。

顶层按__CCE_AICORE__==310选择arch35，并在该分支按quantMode实例化五类Q/K/scale；另一分支固定INT8并连接candidate入口。合法Host属性仍须匹配真实编译模板。arch35不接candidate张量；不能把arch22的候选共享功能附到950调用。主kernel不为未知quantMode统一报错，错误输入应在Host门禁处拒绝。

| 执行路径 | QK、weight/scale与打分 | TopK数据域 |
| --- | --- | --- |
| arch22 INT8 | INT8 QK在INT32累加；Fixpipe以位型0x3a800000即1/1024反量化、ReLU并落half L1；weight*qScale先以half相乘，再由Cube沿G求和为FP32，Vector乘half kScale | FP32分数与INT32索引pair，Sort32/MrgSort维护每行2048上界 |
| arch35普通FP8 | QK为FP32，Vector将ReLU(QK)与FP32 weight*qScale加权归约，再乘kScale | 先舍入BF16，再变换为可比较uint16 key |
| arch35 INT8 | INT32 QK转FP32，1/1024后RINT为half再扩回FP32；weight*qScale也先half舍入，后续加权归约与kScale在FP32 | 最终BF16及uint16 key；不是全程INT32精确排序 |
| arch35 HiFloat8 | Q/K HiFloat8，Q/K单元素scale在Vector取第0项，按per-tensor路线计算 | BF16及uint16 key |
| arch35 MXFP8 | E8M0以每32逻辑feature一组进入Cube的MX LoadData，Vector不再重复乘普通per-token descale | FP32加权归约，最终BF16及uint16 key |
| arch35 MXFP4 | 每字节两个E2M1，GM feature宽为D/2；Cube融合E8M0尺度，Fixpipe ReLU后转BF16；weight转BF16，逐G以BF16 MulAddDst累加 | BF16及uint16 key，不能用MXFP8的FP32累加参考替代 |

scale与ReLU的位置不能在任意值域下随意交换。源码Host没有逐值证明scale为正、weight非负或输入有限；适配须保存实际量化数值约定。uint16 key是BF16位型经符号掩码/XOR得到的排序表示，不是量化概率或原始token ID；转换只对指定NaN位型另作处理，不应概括为完整NaN/Inf策略已验证。

arch22的4行Q/S2=2048宏块、256/128行Cube子块与两任务预取交错运行：Vec0提供weight*qScale，Cube写GM分数，Vec1消费上一任务。两个槽位通过mode2跨核flag及MTE/FIX事件保护，末尾额外一次循环排空；空请求分支也需要消费待完成任务。arch35的S2=128，TopK>6144时Q行块从4降到2；Q双buffer、K三buffer、L0双buffer，mode4同时等待两个AIV（第二个flag偏移16）再复用结果区。不能把修改循环次数、提前return或删空行当单纯调度优化。

arch35在0<=maxSeqlenQ<=4时将K L1一次加载256个位置，以缓存命中覆盖相邻128位置任务；其他情况按128加载。缓存首个S2任务清无效，范围全部消费或该行结束后释放K buffer。这是一次kernel内部的缓存，不是跨请求或跨graph重放的KV身份缓存。MX尺度用BF16 view搬运两个E8M0字节，再以E8M0解释进入MX LoadData，并非把尺度数值转换成BF16。

## Candidate source/consumer：压缩坐标、最后一块与真实成本

arch22 source在乘kScale后的分数上按8个压缩位置取max；尾部无效位置填负无穷，块号为压缩位置整除8。每行最后一个可见压缩位置所在块会将块分数置正无穷以保留，再独立sort/merge候选块。source自己的位置TopK仍使用原分数，候选pin不会把位置分数也改为正无穷。causal时最后块由该行可见压缩长度确定，无mask时由请求K长度确定。

consumer每行首次S2任务读入候选列表，将块号转float并排序；随后CountGE二分得到当前tile的候选窗口，以块号距离最小值构造成员mask，展开到8个位置后给候选外分数施加约−1e30罚分。这里没有让Cube只gather候选K：QK、尺度和weight归约仍覆盖原任务S2域，新增mask还有排序/标量窗口成本。不能仅因候选数较少就承诺读带宽、Cube耗时或整体时延降低。

候选buffer按每AIV的innerS1Idx分区，避免同核两行在不同tile间覆盖；块分数merge以INT32视图Adds(+0)回拷，保留−1索引位型，不能改成float算术复制。CountGE读取向量排序结果前有V_S等待；PIPE_V barrier不是标量/向量或MTE之间的通用fence。source和consumer须同forward、同请求/Q行、同压缩K快照及block_size；该来源没有生产侧跨step失效通知器。

output_idx_offset作用于最终sparse_indices，不作用于candidate相对块号。arch22位置输出和LD分支直接对sparseCount个槽位做Adds，没有逐槽过滤−1；因此“非零offset后padding仍一定是−1”的设计文档陈述不能直接采用，须对短K、全mask及padding实测。文档保留了早期不支持offset/仅G64、TND与TND K等中间方案，当前Host/接线不同；遇冲突按固定实现逐层核对。文档声称87或76例通过也不等于本次在该SHA重现。

## 950 TopK/FD：无序集合、短序列和工作区

950先把每行uint16 score写到GM，再在最后S2任务进行TopK。uint16版本先按高8位、再低8位直方图寻找阈值，先输出大于阈值的位置，再按扫描顺序补等于阈值的位置；它没有对所有已选元素按分数再排序。有效K少于TopK时直接输出0..validLen−1并填其余−1，返回values时保持索引与值配对。下游若要求位置升序或分数降序，需显式排序并同步重排values，不能依赖结果碰巧有序。

TopK按K预算选择trunkLen：<=2048取16384，<=3072取12288，<=4096取8192，<=5120取4096，<=6144取2048，再大取12288。跨trunk维护选中的值和历史索引，新的trunk索引经gather还原；临时uint16索引只在局部拼接段使用，不能直接作为完整长上下文坐标。padding score key用0作中性最小值，index用−1；FD merge的values通过专门InfMask把无效key还原负无穷。

FD由AICPU的LI范围与LD条目驱动，同一行的不同S2片段先写局部TopK score/index；全部AIV经过SyncAll后再做LD归并。arch22保留LD实现但当前metadata producer不开FD，不能因死分支代码存在就认为candidate能安全任意S2跨核。arch35 LD先Reset管道缓冲，再按248KiB预算、TopK向256对齐后推导trunk；这只是固定实现的资源模型，不是实际设备可用UB保证。

GM工作区也不同：arch22保留QK/权重/LD的双buffer空间；arch35每AIC有Q块×对齐K长度的uint16 score区，另外有局部TopK score与INT32 index区，随core数、K长度、Q块与TopK增长。不要只报告最终indices的T×TopK内存。每段page copy都通过block_table取physical block；负页或越界值没有在Cube重新全面验证，不能用输出无效索引规则替代输入页表合法性。

## Python参考入口、图及测试参考如何使用

参考torch_extension将HiFloat8的uint8改成ACL_HIFLOAT8；MXFP4允许原生packed dtype或uint8并改成ACL_FLOAT4_E2M1；MX scale要求原生E8M0且storage_offset能被2整除。reinterpret是ABI描述，不是重新量化或校准。普通接口返回两元组，candidate固定三元组且values为空；source/consumer新规范包装又分别返回四元组和两元组，不能只按名称替换调用。

新规范包装的seqused_q实际映射为K有效长度seqused_k；source输出candidate_block_length是每行可见压缩K长度，consumer收该参数却不消费。没有cu_seqlens_q时仅允许B=1并给Q/weight/scale补batch维；多请求必须TND前缀。metadata缺省时通过max().item()取Host值并自动生成，带设备同步，不能放进图后期待零Host依赖；手传metadata仍需caller维护其身份和刷新。

metadata的GE converter明确抛不支持错误，allow_in_graph或fake返回[1024]不会消除该限制。所读graph测试将metadata在编译外生成，主网络以fullgraph=False、dynamic=False编译；有这个测试文件不证明纯完整图、动态shape或所有量化路径已通过。

参考golden分别保留INT8的1/1024和half中间舍入、MXFP8逐G FP32累加、MXFP4逐G BF16 FMA舍入（以FP64重建再RNE模拟），并从随机置换页表还原逻辑K和scale。比较器先排序整行索引作多重集合比较；失败行按gold有效前缀检查重复/范围，再允许相对TopK边界0.001误差。这个fallback按gold有效计数切npu前缀，不能独立证明npu全部padding数正确；Agent验收应另外记录有效槽数。返回values需按实际NPU选中索引从完整参考score gather比较，不能只对齐CPU另一套并列TopK的槽位。

batch一致性工具对相关Q切片用独立seed生成相同Q/K/scale及offset，严格约束逻辑跨度、K长度、residual和共享物理页所有者；跨case比较上下文、shape和原始输出字节。它只比较output0，不证明values逐位一致；NOT_APPLICABLE也不是存在两组关系的PASS。辅助metadata预处理只以非零内容判复用，不能移植成生产缓存失效策略。

当前paramset模块还有静态可见的测试收集边界：950启用列表引用6个未在TEST_PARAMS字典定义的MXFP8/MXFP4名称，另只为910_93/950分支赋ENABLED_PARAMSETS。不能从README或enable列表认定这些用例实际执行，更不能以此补全硬件矩阵。本轮仅阅读并记录，未运行收集或修改上游。

性能脚本按PROF目录mtime关联结果行，选第一份op_summary CSV的首个QuantLightningIndexerV2项，并以绝对10微秒差阈值作比较；不是端到端延迟、分位数或自动可信的case身份绑定。实际包中的VllmAscend前缀也需匹配过滤名。隔离shell会清理旧结果/PROF目录，属于实验工具行为，不应直接嵌入生产Agent。诊断应保留实际二进制、输入快照、page/scale stride、metadata/候选身份、真实所走key、数值参考和独立计时；本卡仍为draft，无实机支持、精度或性能结论。

## 固定3164增量：小TopK的内部宽度与长向量repeat

ceac→3164adc8fe75892fbf7f99f524bb72fddf1e6efd仅新增本节两份arch22程序delta；上文ceac规则继续按原版本使用。新版topkWidth=align64(sparseCount)，pairWidth=2*topkWidth，不再把所有排序UB、跨核LD输出和部分TopK工作区硬编码成2048/4096。Init/清空、每route stride、Extract、MrgSort4的长度及最终归并拷贝都改随该宽度走；公开TopK形状与Host准入仍需取实际当前调用，不因内部对齐就放宽支持矩阵。

LD读取多个segment改为逐segment的一次DataCopyPad，源步长为s1BaseSize*pairWidth；不能将旧大TopK下的一条strided copy公式原样带入小TopK版本。vec辅助新增VecRepeatPlan：每次最多VEC_REPEAT_MAX(255)个64-FP32 repeat，短尾用真实mask；Max/Min/Abs/Mins/Maxs/Sub/Adds/Mul、候选mask与integer-bit算术的长向量全部显式循环推进offset。因此大candidate向量不再把repeat数直接截成uint8，尾部stride也按Unary/BinaryRepeatParams准确区分。

移植要同时保存外部sparseCount、内部align64宽度、workspace实例与LD分片；只改一个allocation或把旧2048常量全局替换仍可能错位。新代码只是静态修订，尚未执行小TopK、跨255-repeat边界、LD尾segment或真实NPU精度/性能验收。
