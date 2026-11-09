---
type: Guide
title: vLLM Ascend分布式缓存回归：传输、租约、PP布局与失败恢复矩阵
description: 为AscendStore、Mooncake、EC、D2RH、KV offload、EPLB和权重传输选择固定UT，核对buffer注册、物理层边界、异步完成、重复/失败与资源寿命；不把mock或结构断言提升为实际通信成功。
tags:
- task.testing
- task.debugging
- topic.model_adaptation
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/distributed/ascend_store/_mock_deps.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/distributed/ascend_store/test_ascend_store_connector.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/distributed/ascend_store/test_backend.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/distributed/ascend_store/test_coalesced_cache_transfer.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/distributed/ascend_store/test_coordinator.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/distributed/ascend_store/test_glm53_store.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/distributed/ascend_store/test_kv_transfer.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/distributed/ascend_store/test_layerwise_cache_layout.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/distributed/ascend_store/test_layerwise_keys.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/distributed/ascend_store/test_layerwise_strided_roundtrip.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/distributed/ascend_store/test_metadata.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/distributed/ascend_store/test_metrics.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/distributed/ascend_store/test_mooncake_hybrid.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/distributed/ascend_store/test_mooncake_layerwise.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/distributed/ascend_store/test_mooncake_pipeline.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/distributed/ascend_store/test_pool_scheduler.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/distributed/ascend_store/test_pool_worker.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/distributed/ascend_store/test_request_lifecycle.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/distributed/ascend_store/test_reuse_publication_fence.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/distributed/ascend_store/test_reuse_snapshot_blocks.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/distributed/ascend_store/test_reuse_snapshot_identity.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/distributed/ascend_store/test_segmented_cache_transfer.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/distributed/device_communicators/test_pyhccl.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/distributed/device_communicators/test_pyhccl_wrapper.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/distributed/ec_transfer/test_ec_mooncake_connector.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/distributed/ec_transfer/test_mooncake_memory.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/distributed/ec_transfer/test_mooncake_transfer.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/distributed/ec_transfer/test_mooncake_worker.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/distributed/eplb/test_policy_load_stats.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/distributed/eplb/test_state.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/distributed/kv_transfer/kv_p2p/test_remote_decode_lifecycle.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/distributed/kv_transfer/kv_p2p/test_remote_prefill_lifecycle.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/distributed/kv_transfer/sparse_kv_offload/test_sparse_kv_offload_manager.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/distributed/kv_transfer/test_connector_registration.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/distributed/kv_transfer/test_kv_transfer_failures.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/distributed/kv_transfer/test_utils.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/distributed/mooncake/test_mooncake_config_data.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/distributed/mooncake/test_mooncake_kv_transfer.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/distributed/test_ec_memcache_connector.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/distributed/test_parallel_state.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/distributed/test_yuanrong_backend.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/distributed/weight_transfer/test_e2e_weight_transfer_oracle.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/distributed/weight_transfer/test_hccl_engine.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/distributed/weight_transfer/test_npu_ipc_engine.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/distributed/weight_transfer/test_rlhf_http_hccl.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/eplb/adaptor/test_vllm_adaptor.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/eplb/core/policy/test_policy_factory.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/eplb/core/test_eplb_device_transfer_loader.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/eplb/core/test_eplb_utils.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/eplb/test_eplb_updator.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/kv_offload/mooncake_v2/helpers.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/kv_offload/mooncake_v2/test_base_scheduler.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/kv_offload/mooncake_v2/test_base_worker.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/kv_offload/mooncake_v2/test_connector.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/kv_offload/mooncake_v2/test_metadata.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/kv_offload/mooncake_v2/test_pull_scheduler.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/kv_offload/mooncake_v2/test_pull_worker.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/kv_offload/mooncake_v2/test_stats.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/kv_offload/mooncake_v2/test_utils.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/kv_offload/test_ascend_multi_connector.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/kv_offload/test_copy_sfa_dense_fill_offsets.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/kv_offload/test_copy_sfa_topk_slots.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/kv_offload/test_d2rh_compressed_block_coverage.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/kv_offload/test_d2rh_endpoint_hashes.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/kv_offload/test_d2rh_packed_views.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/kv_offload/test_d2rh_pp_components.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/kv_offload/test_d2rh_pp_host_validity.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/kv_offload/test_d2rh_pp_inheritance.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/kv_offload/test_d2rh_pp_lifetime.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/kv_offload/test_d2rh_pp_mapping.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/kv_offload/test_d2rh_transfer_dedup.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/kv_offload/test_hybrid_prefix_truncation.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/kv_offload/test_memfabric_transfer_engine.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/kv_offload/test_mooncake_d2rh_connector.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/kv_offload/test_mooncake_hybrid_connector.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/kv_offload/test_mooncake_layerwise_connector.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/kv_offload/test_native_cpu_offload.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/kv_offload/test_npu_offload_spec.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/kv_offload/test_pool_worker_pp_layer_count.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/kv_offload/test_pool_worker_pp_object_bounds.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/kv_offload/test_preempt_offload_connector.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/kv_offload/test_sfa_pd_peer_restart.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/kv_offload/test_sfa_pd_rd2h_connector.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/kv_offload/test_sfa_pd_rd2h_lifecycle.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/kv_offload/test_sfa_pd_slot_admission.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/kv_offload/test_sparse_kv_offload_external_plan.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/kv_offload/utils.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/kv_transfer/test_ascend_store_layerwise_lifecycle.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/kv_transfer/test_layerwise_dcp_sharding.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/kv_transfer/test_layerwise_multi_cache_spec.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/kv_transfer/test_layerwise_pp_global_layers.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/simple_kv_offload/test_simple_kv_offload.py
  role: evidence
created_at: '2026-11-03T04:56:46Z'
updated_at: '2026-11-04T02:58:49Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend分布式缓存回归：传输、租约、PP布局与失败恢复矩阵

## 传输正确性不只是一轮copy相等

AscendStore测试将metadata/save范围、key、prefix截断、pool scheduler、worker和具体backend分开。断言覆盖tenant类型、TP mismatch、无cache group、空group、load/save失败、陈旧计划、物理block内部contiguous，以及segmented/coalesced地址和PP物理层扩张。snapshot identity、block lease与publication fence是独立检查，不从最终bytes相等推已正确发布或失败可重试。

Mooncake V2的scheduler/worker/metadata与pull路径分别覆盖role单选、DP隔离、PP层数/blocks、远端TP整比映射和endpoint一致性；测试明确拒绝KVPP+DCP、缺少local DP rank及不兼容层布局等场景。fixture构造的握手和Mock原生engine不构成真实网络、注册内存或跨版本wire ABI验收。

D2RH/混合缓存要核两跳的有效性和资源寿命：块hash、压缩覆盖、packed view、组件位置、PP层名、pin/free队列、失败释放及peer restart分别有回归。SFA PD测试还区分scale presence、slot admission、outstanding reads与Decode进程身份；仅收到完成消息不能替代全部预期层/组件就绪。

EC传输测试核2MiB对齐可注册区间、staging/bounce容量、entry owner/user、batch register/unregister和异步Future失败。NPU/CPU offload检查canonical data refs、共享view与block非连续拒绝；不能从配置了buffer device就推所有dtype/layout兼容。

EPLB/通信测试覆盖ctypes签名、close失败/幂等、路由表shape、background worker fatal传播、load-stat commit与映射generation；权重HCCL/IPC另核wire参数、tensor_sizes必需与load失败。注册表存在、controller更新和测试oracle读到同值不是所有rank真实完成。

参见具体AscendStore实现合同和[多节点测试](vllm_ascend_multi_node_test_contract.md)选择下一层运行证据。

## 按断言职责选择源测试

下表是静态语法定位材料：从固定源码的AST遍历函数、assert与assert*/raises调用，保留test*函数计数和摘选谓词，未逐行完成fixture、callee与每条断言的语义复核。原自动聚类的“数值比较”“掩码/有效行”等宽标签不再作为覆盖结论列出；一般相等断言、mock调用或helper名称不能独立证明对应设备语义。摘选谓词帮助回源，不是完整用例正文。名称计数不是pytest实际收集量，fixture命名与参数化实例须另核。参数fixture、mock、skip条件和设备前提仍需打开对应固定来源核实；没有执行或证明任何用例通过。文件无断言时列其fixture/工具接口，不冒充独立数值检查。

| 固定测试文件 | AST test*函数数（非收集量） | 可定位的谓词或失败约束 |
| --- | --- | --- |
| ut/distributed/ascend_store/_mock_deps.py | 0 | _make_pkg; __init__; __init__; __getattr__; __init__ |
| ut/distributed/ascend_store/test_ascend_store_connector.py | 37 | ev._aggregator.clear_events.assert_called_once(); self.assertRaisesRegex(ValueError, 'does not support use_layerwise') |
| ut/distributed/ascend_store/test_backend.py | 150 | store.init.assert_called_once_with(2, init_bm=False); self.assertRaises(TypeError); self.assertRaisesRegex(TypeError, 'tenant_id must be a string or null'); self.assertRaises(RuntimeError); self.assertRaises(ValueError); self.assertRaises(backend_base.BatchResultShapeError); self.assertRaisesRegex(RuntimeError, 'returned 0 results for 1 keys'); self.assertRaisesRegex(ValueError, 'not valid JSON'); self.assertRaises(AssertionError); self.assertRaisesRegex(RuntimeError, 'store init failed'); self.assertRaisesRegex(ValueError, 'same length'); self.assertRaisesRegex(ValueError, '\\[0, 4\\]'); self.assertRaises(error); self.assertRaisesRegex(ValueError, 'QoS must be an integer'); self.assertRaisesRegex(ValueError, 'kv_connector_extra_config'); self.assertRaisesRegex(ValueError, 'must be a JSON object'); self.assertRaisesRegex(ValueError, 'memcache_dp_init_barrier.*boolean') |
| ut/distributed/ascend_store/test_coalesced_cache_transfer.py | 6 | worker._get_combined_cache_transfer_segments((first, second), 0) is None; cursor == len(payload) |
| ut/distributed/ascend_store/test_coordinator.py | 14 | derive.assert_called_once() |
| ut/distributed/ascend_store/test_glm53_store.py | 7 | torch.testing.assert_close(cache[dst], cache[src]); self.assertRaisesRegex(RuntimeError, 'save failed') |
| ut/distributed/ascend_store/test_kv_transfer.py | 53 | thread is not None; store.batch_write_finish.assert_called_once_with(['k0'], [0]); self.assertRaisesRegex(RuntimeError, 'asynchronous transfer'); self.assertRaisesRegex(RuntimeError, 'save thread failed'); self.assertRaises(RuntimeError) |
| ut/distributed/ascend_store/test_layerwise_cache_layout.py | 27 | layout.has_layer_reuse is False; kv_cache_config.kv_cache_tensors == original_tensors; pytest.raises(TypeError); pytest.raises(ValueError); pytest.raises(NotImplementedError, match='attention cache specs only'); pytest.raises(NotImplementedError, match='contiguous per-layer pages'); pytest.raises(ValueError, match='exceeds its backing allocation') |
| ut/distributed/ascend_store/test_layerwise_keys.py | 5 | self.assertRaisesRegex(ValueError, 'empty groups') |
| ut/distributed/ascend_store/test_layerwise_strided_roundtrip.py | 6 | all((torch.equal(actual, expected) for actual, expected in zip(dst_storage, expected_storage))); sizes == dst_sizes |
| ut/distributed/ascend_store/test_metadata.py | 77 | self.assertRaises(ValueError) |
| ut/distributed/ascend_store/test_metrics.py | 2 | first.reduce() == {'ascend_store_delayed_release_requests': 2, 'ascend_store_delayed_release_blocks': 5, 'ascend_store_load_get_count': 2, 'ascend_store_load_get_avg_ms': 15.0, 'ascend_store_load_get_keys': 8} |
| ut/distributed/ascend_store/test_mooncake_hybrid.py | 18 | worker.layer_save_finished_events is not None; worker.token_database.load_mask.assert_called_with(request.block_hashes, 32); self.assertRaisesRegex(RuntimeError, 'refusing incomplete'); self.assertRaisesRegex(RuntimeError, 'allocator disconnected'); self.assertRaisesRegex(RuntimeError, 'failed during asynchronous transfer'); self.assertRaises(RuntimeError); self.assertRaisesRegex(AssertionError, 'unreachable state') |
| ut/distributed/ascend_store/test_mooncake_layerwise.py | 16 | store.batch_commit.assert_called_once_with(['key']) |
| ut/distributed/ascend_store/test_mooncake_pipeline.py | 11 | self.assertRaisesRegex(RuntimeError, 'no KV cache group'); self.assertRaisesRegex(ValueError, 'empty groups'); self.assertRaisesRegex(ValueError, 'context parallelism') |
| ut/distributed/ascend_store/test_pool_scheduler.py | 85 | scheduler.num_speculative_blocks_by_group == ({} if num_speculative_blocks is None else {1: num_speculative_blocks}); keys == target_keys + expected_draft; scheduler.layerwise_keys.make_hit_check_keys.assert_called_once_with(0, 'block-hash', 1); self.assertRaisesRegex(ValueError, 'TP mismatch') |
| ut/distributed/ascend_store/test_pool_worker.py | 131 | save_request.save_keys is not None; np.testing.assert_array_equal(first.shared_block_data.block_ids_arr, [10] if case == 'partial' else [10, 11]); worker.kv_recv_thread.set_finished_request.assert_called_once_with('loaded-request'); self.assertRaisesRegex(RuntimeError, 'send failed'); self.assertRaisesRegex(RuntimeError, 'receive failed'); self.assertRaisesRegex(ValueError, 'TP mismatch'); self.assertRaises(ValueError); self.assertRaisesRegex(RuntimeError, f'{missing} is not initialized'); self.assertRaises(RuntimeError) |
| ut/distributed/ascend_store/test_request_lifecycle.py | 2 | pool.use_eagle == (speculative_method is not None); isinstance(pool.kv_recv_thread, KVCacheStoreRecvingThread) == load_async; pytest.raises(AssertionError, match='AscendStore requires at least one prefix-cacheable KV cache group') |
| ut/distributed/ascend_store/test_reuse_publication_fence.py | 2 | self.assertRaisesRegex(RuntimeError, 'save failed') |
| ut/distributed/ascend_store/test_reuse_snapshot_blocks.py | 8 | set((w.m_store.data[k] for k in meta.save_keys)) == set(addresses.values()); query.assert_called_once() |
| ut/distributed/ascend_store/test_reuse_snapshot_identity.py | 2 | self.assertTrue(meta.can_save); self.assertEqual(tracker.last_layerwise_snapshot_end_token, 7) |
| ut/distributed/ascend_store/test_segmented_cache_transfer.py | 6 | worker.group_kv_caches_base_addr[0] == [cache.data_ptr()]; sizes == restored_sizes; pytest.raises(ValueError, match='contiguous data inside each physical block') |
| ut/distributed/device_communicators/test_pyhccl.py | 7 | synchronize.assert_called_once_with(comm.device); self.assertRaisesRegex(RuntimeError, 'closed'); self.assertRaisesRegex(RuntimeError, 'close failed') |
| ut/distributed/device_communicators/test_pyhccl_wrapper.py | 14 | mock_fn.assert_called_once(); self.assertRaises(ValueError); self.assertRaises(OSError); self.assertRaises(RuntimeError) |
| ut/distributed/ec_transfer/test_ec_mooncake_connector.py | 4 | connector._worker is expected_worker; register_connector.assert_called_once_with('ECMooncakeConnector', 'vllm_ascend.distributed.ec_transfer.ec_connector.mooncake.connector', 'AscendECMooncakeConnector') |
| ut/distributed/ec_transfer/test_mooncake_memory.py | 22 | tensor.dtype == torch.uint8; raw_tensor.data_ptr() % alignment != 0; tensor.data_ptr() == raw_tensor.data_ptr() + expected_offset; empty.assert_called_once_with(capacity + alignment - 1, dtype=torch.uint8, device=device); pytest.raises(RuntimeError, match='configured_staging=.*effective_staging=0.*padding=0.*bounce=.*registered=.*allocation='); pytest.raises(RuntimeError, match='configured_staging=.*effective_staging=.*bounce=0'); pytest.raises(ValueError, match='arena capacity') |
| ut/distributed/ec_transfer/test_mooncake_transfer.py | 22 | plan.owner is tensor; plan.prefix_nbytes == 0; set_device.assert_called_once_with(3); pytest.raises(RuntimeError, match='status 7'); pytest.raises(ValueError, match='no 2 MiB-aligned bytes'); pytest.raises(ValueError, match='before the aligned registration') |
| ut/distributed/ec_transfer/test_mooncake_worker.py | 21 | 'direct/bounce fallback is disabled' in str(failure); _flatten_transfer_wave(wave, 1000) == [_TransferFragmentPlan(0, 100, 0, 10), _TransferFragmentPlan(1, 1000, 0, 3), _TransferFragmentPlan(1, 200, 3, 7), _TransferFragmentPlan(2, 1003, 0, 5)]; producer_memory.acquire_bounce.assert_called_once_with(0); pytest.raises(RuntimeError, match='registration failed'); pytest.raises(RuntimeError, match='release failed'); pytest.raises(ValueError, match="mooncake_protocol='ascend'"); pytest.raises(ValueError, match="ec_buffer_device='npu'"); pytest.raises(ValueError, match='ascend_mooncake_bounce_arena_size') |
| ut/distributed/eplb/test_policy_load_stats.py | 8 | result is not None; state._num_recorded_load_steps == 2; state.get_rank_node_ids.assert_called_once_with() |
| ut/distributed/eplb/test_state.py | 20 | state.model_states['target'] is model_state; events == ['update', 'refresh']; update.assert_called_once_with(model_config, mapping); pytest.raises(RuntimeError, match='background worker terminated'); pytest.raises(TypeError, match='required by the selected vLLM release'); pytest.raises(SystemExit, match='worker must terminate'); pytest.raises(RuntimeError, match='Cannot add'); pytest.raises(RuntimeError, match='registration failed') |
| ut/distributed/kv_transfer/kv_p2p/test_remote_decode_lifecycle.py | 2 | output.kv_transfer_params is None; len(scheduler.requests) == 1 |
| ut/distributed/kv_transfer/kv_p2p/test_remote_prefill_lifecycle.py | 3 | block._block_hash is None; len(scheduler.running) == 0 |
| ut/distributed/kv_transfer/sparse_kv_offload/test_sparse_kv_offload_manager.py | 14 | tp_group.barrier.assert_called_once_with(); self.assertRaisesRegex(RuntimeError, 'Sparse KV offload is only support on A3'); self.assertRaisesRegex(ValueError, 'host-resident'); self.assertRaisesRegex(ValueError, 'exceeds DRAM limit'); self.assertRaisesRegex(ValueError, message) |
| ut/distributed/kv_transfer/test_connector_registration.py | 14 | d2rh.MooncakeConnector is d2rh.MooncakeD2RHConnectorV1; registrations == [('FooConnector', 'some.module', 'FooConnector')]; logger.warning.assert_called_once(); pytest.raises(ValueError, match='already registered') |
| ut/distributed/kv_transfer/test_kv_transfer_failures.py | 16 | mock_logger.error.assert_called_once() |
| ut/distributed/kv_transfer/test_utils.py | 9 | log.info.assert_called_once(); self.assertRaises(ValueError) |
| ut/distributed/mooncake/test_mooncake_config_data.py | 10 | self.assertRaises(ValueError); self.assertRaises(TypeError) |
| ut/distributed/mooncake/test_mooncake_kv_transfer.py | 1 | self.assertEqual(len(store.put_calls), 1); self.assertEqual(len(put_keys), 2) |
| ut/distributed/test_ec_memcache_connector.py | 12 | [embedding.shape[0] for embedding in embeddings if embedding is not None] == [5, 5, 10]; embeddings is not None; _get_recv_buffer_tokens(vllm_config) == expected; connector._backend.batch_get_key_info.assert_called_once_with(['key0', 'key1']); pytest.raises(ValueError, match='recv_buffer_tokens must be an integer'); pytest.raises(ValueError, match='recv_buffer_tokens must be between'); pytest.raises(ValueError, match='requires ec_transfer_config') |
| ut/distributed/test_parallel_state.py | 5 | parallel_state._KVPP is None; get_global_rank(parallel_config) == expected; node_partition.assert_called_once_with(8, 4, 2); pytest.raises(AssertionError, match='output tensor parallel group is not initialized') |
| ut/distributed/test_yuanrong_backend.py | 20 | YuanrongBackend.requires_exists_before_put is False; backend.get(keys, addrs, sizes) == [0]; backend.store.mget_h2d_from_multi_buffers.assert_called_once_with(keys, addrs, sizes, 1234); pytest.raises(ValueError, match='expected a dictionary/object'); pytest.raises(ValueError, match='YR_CONFIG_PATH') |
| ut/distributed/weight_transfer/test_e2e_weight_transfer_oracle.py | 3 | lane['--enable-sleep-mode'] is reference['--enable-sleep-mode'] is True; lane.pop('--load-format') == 'dummy' |
| ut/distributed/weight_transfer/test_hccl_engine.py | 20 | engine.model_update_group is None; worker_init_payload(init_info) == dict(master_address='host', master_port=1234, rank_offset=1, world_size=2); initialize.assert_called_once_with(engine.model); pytest.raises(ValueError, match=match); pytest.raises(ValueError, match=name); pytest.raises(RuntimeError); pytest.raises(RuntimeError, match='send failed') |
| ut/distributed/weight_transfer/test_npu_ipc_engine.py | 13 | mock_consumer.assert_called_once_with(ipc_handle=update_info.ipc_handles, physical_npu_id='node-0', names=update_info.names, shapes=update_info.shapes, dtype_names=update_info.dtype_names, tensor_sizes=update_info.tensor_sizes, device_index=0); engine.source is source; captured['args'] == ('config', 'vllm_config', device, 'model'); events == expected_chunk * 2; pytest.raises(ValueError, match='tensor_sizes.*required'); pytest.raises(RuntimeError, match='load failed') |
| ut/distributed/weight_transfer/test_rlhf_http_hccl.py | 1 | spec is not None and spec.loader is not None; events.mock_calls == expected; pytest.raises(RuntimeError) |
| ut/eplb/adaptor/test_vllm_adaptor.py | 7 | self.assertRaisesRegex(AssertionError, 'EPLB expert weight shapes mismatch') |
| ut/eplb/core/policy/test_policy_factory.py | 2 | self.assertLessEqual(update_mean, 1.08); self.assertLessEqual(update_mean, 1.1) |
| ut/eplb/core/test_eplb_device_transfer_loader.py | 5 | mock_p2p.call_args_list[0].args[1] is mock_adaptor.buffer_tensor_list['weight_key'][0][0]; loader_obj.state == loader.ExpertWeightUpdateState.TRANSFERRING; mock_adaptor.do_update_expert_map.assert_called_once() |
| ut/eplb/core/test_eplb_utils.py | 9 | mock_determine.assert_called_once() |
| ut/eplb/test_eplb_updator.py | 2 | self.assertEqual(moe_load.shape, (58, self.world_size, 100, 8)); self.assertTrue('moe_load' in self.updator.shared_dict) |
| ut/kv_offload/mooncake_v2/helpers.py | 0 | make_kv_cache_tensor; make_full_spec; make_sliding_spec; make_mamba_spec; make_circular_spec |
| ut/kv_offload/mooncake_v2/test_base_scheduler.py | 13 | scheduler.ascend_config is ascend_config; scheduler.engine_id == 'engine-d'; init_ascend_config.assert_called_once_with(config); pytest.raises(ValueError, match='exactly one KV transfer role'); pytest.raises(NotImplementedError) |
| ut/kv_offload/mooncake_v2/test_base_worker.py | 19 | metadata.block_shapes == [[tuple(cache.shape[1:]) for cache in caches]]; worker.xfer_handshake_metadata.kv_caches_base_addr == [[caches[names[target_index]].data_ptr()], [caches[names[4]].data_ptr()]]; worker.xfer_handshake_metadata.layer_names == [names[target_index], names[4]]; transfer_engine.register_buffer.assert_called_once(); pytest.raises(ValueError, match='exactly one KV transfer role'); pytest.raises(ValueError, match='requires a local DP rank'); pytest.raises(NotImplementedError) |
| ut/kv_offload/mooncake_v2/test_connector.py | 8 | MooncakeConnector is MooncakePullConnector; connector.get_loaded_kv_cache_group_ids(MagicMock()) == (0, 2); connector.connector_scheduler.update_state_after_alloc.assert_called_once_with(request, blocks, 8); pytest.raises(NotImplementedError, match='not implemented') |
| ut/kv_offload/mooncake_v2/test_metadata.py | 6 | metadata.layer_names == ['layer.0', 'layer.1']; pytest.raises(ValueError, match='group_indices.*1 layers, expected 2'); pytest.raises(ValueError, match='layer_block_sizes.*1 layers, expected 2'); pytest.raises(ValueError, match="layer 'layer.0'.*block_strides") |
| ut/kv_offload/mooncake_v2/test_pull_scheduler.py | 38 | request.prompt_embeds.shape[0] == num_tokens - 1; decoded.use_kv_pp is False; pp_metadata.layer_names == first.layer_names; thread._get_remote_socket.assert_called_once_with(path); pytest.raises(ValueError, match='KVPP cannot be combined with DCP'); pytest.raises(ValueError, match='different KV-cache layers while KVPP is disabled'); pytest.raises(ValueError, match='incomplete PCP ranks'); pytest.raises(ValueError, match='incomplete TP ranks'); pytest.raises(ValueError, match='mismatch in.*block_lens'); pytest.raises(KeyboardInterrupt); pytest.raises(RuntimeError, match='Unexpected.*completion response'); pytest.raises(_StopLoop) |
| ut/kv_offload/mooncake_v2/test_pull_worker.py | 59 | first is second; MooncakePullRecvingThread._get_remote_endpoint({('host', 1)}) == ('host', 1); get_remote_groups.assert_called_once_with(remote_tp_size=4, remote_pcp_size=2, local_dcp_size=expected_local_dcp_size, remote_dcp_size=expected_remote_dcp_size, total_num_kv_heads=1); pytest.raises(ValueError, match='must share one scheduler endpoint'); pytest.raises(ValueError, match='integer ratio'); pytest.raises(ValueError, match='producer cannot enable KV parallel and DCP together'); pytest.raises(ValueError, match='missing layers.*missing'); pytest.raises(ValueError, match='exactly one block'); pytest.raises(ValueError, match='equal P/D physical block counts'); pytest.raises(RuntimeError, match='transfer failed'); pytest.raises(RuntimeError, match='returned no transfer metadata'); pytest.raises(ValueError, match=expected_error); pytest.raises(_StopWorkerLoop); pytest.raises(ValueError, match='circular cache layout mismatch'); pytest.raises(RuntimeError, match='timed out'); pytest.raises(ValueError, match='inconsistent total KV head counts'); pytest.raises(RuntimeError, match='submit failed') |
| ut/kv_offload/mooncake_v2/test_stats.py | 2 | stats.aggregate(empty) is stats; reduced['Num successful transfers'] == 2 |
| ut/kv_offload/mooncake_v2/test_utils.py | 12 | regions.ptrs == [backing.data_ptr()]; as_kv_cache_tensors(first) == (first,); context.destroy.assert_called_once_with(linger=0); pytest.raises(TypeError, match='must be a tensor'); pytest.raises(ValueError, match='Unexpected socket type'); pytest.raises(RuntimeError, match='Failed to send'); pytest.raises(RuntimeError, match='Failed to receive') |
| ut/kv_offload/test_ascend_multi_connector.py | 17 | connector._requires_full_dspark_prompt is (full_prompt and pd_connector == 'SfaRemoteD2HConnector'); connector._requests_to_connector == {}; connector.get_kv_connector_kv_cache_events() is None; pytest.raises(ValueError, match='exactly one') |
| ut/kv_offload/test_copy_sfa_dense_fill_offsets.py | 1 | count.dtype == torch.int32; sources.tolist() == [host_bases[layer][component] + block_id * 4 * stride for component, stride in enumerate(token_bytes) for block_id in values[1][:2]]; copy.call_count == num_layers |
| ut/kv_offload/test_copy_sfa_topk_slots.py | 25 | allocator.get('req-a') is None; copy_sfa_pool_capacity(8) == 10; pytest.raises(RuntimeError, match='exhausted'); pytest.raises(RuntimeError, match='binding changed'); pytest.raises(RuntimeError, match='still owned'); pytest.raises((ValueError, RuntimeError), match='slot'); pytest.raises(ValueError, match='duplicate') |
| ut/kv_offload/test_d2rh_compressed_block_coverage.py | 4 | all((value is not None for value in before + after)); transferred == (list(range(1, expected_blocks + 1)),); base.assert_called_once_with(group) |
| ut/kv_offload/test_d2rh_endpoint_hashes.py | 10 | scheduler._d2rh_get_decode_endpoint_hashes(request, ([1],)) is None; before[:3] == after[:3] |
| ut/kv_offload/test_d2rh_packed_views.py | 7 | cpu_data.data_ptr() == cpu_packed.data_ptr(); cpu_scale.data_ptr() == cpu_packed.data_ptr() + 128 |
| ut/kv_offload/test_d2rh_pp_components.py | 7 | self.assertRaisesRegex(RuntimeError, 'incompatible'); self.assertRaisesRegex(RuntimeError, 'Out-of-range') |
| ut/kv_offload/test_d2rh_pp_host_validity.py | 5 | next_hits == {(0, 20 + index, 0) for index in range(hbm_blocks, 2)}; pytest.raises(RuntimeError, match='hop1 transfer failed') |
| ut/kv_offload/test_d2rh_pp_inheritance.py | 3 | d2rh.MooncakeConnector.__init__ is not v1.MooncakeConnector.__init__; len(worker.kv_caches_base_addr) == 23; scheduler.assert_called_once_with(config, 'engine', cache) |
| ut/kv_offload/test_d2rh_pp_lifetime.py | 13 | obj.encoder.encode.assert_called_once_with((d2rh.DONE_RECVING_MSG, 'P-request', {})); self.assertRaisesRegex(RuntimeError, 'injected') |
| ut/kv_offload/test_d2rh_pp_mapping.py | 15 | self.assertRaisesRegex(RuntimeError, 'requires cache layer names'); self.assertRaisesRegex(RuntimeError, 'does not contain layer'); self.assertRaisesRegex(RuntimeError, 'misaligned'); self.assertRaisesRegex(RuntimeError, 'incompatible'); self.assertRaisesRegex(RuntimeError, 'Incomplete D2RH PP layer coverage') |
| ut/kv_offload/test_d2rh_transfer_dedup.py | 1 | groups[0][1] == original_indices; worker._stash_pending_reformat.assert_called_once_with('d-request', 0, [(0, [[3]], 1, [0])]) |
| ut/kv_offload/test_hybrid_prefix_truncation.py | 1 | starts[0] == 384 |
| ut/kv_offload/test_memfabric_transfer_engine.py | 9 | manager.unique_id == '192.168.1.10:23456'; module.set_log_level.assert_called_once_with(2); pytest.raises(RuntimeError, match='already configured'); pytest.raises(ValueError, match='counts differ'); pytest.raises(RuntimeError, match='initialization failed'); pytest.raises(RuntimeError, match='has not been initialized'); pytest.raises(ValueError, match='Invalid MemFabric transfer_protocol'); pytest.raises(RuntimeError, match='initialized for hostname') |
| ut/kv_offload/test_mooncake_d2rh_connector.py | 42 | metadata.block_strides == [[256, 256]]; d2rh.get_d2rh_zmq_port(config, tp_rank=1, pp_rank=1) == 38107; scheduler._return_remote_socket.assert_called_once_with(socket, 'd-host', 38100); pytest.raises(RuntimeError, match='timeout'); pytest.raises(RuntimeError, match='missing key'); pytest.raises(RuntimeError, match='block map missing for request') |
| ut/kv_offload/test_mooncake_hybrid_connector.py | 17 | register_buffer.assert_called_once_with([backing.data_ptr()], [backing_size]); thread.executor.submit.assert_called_once_with(thread._handle_peer_requests, peer_key); self.assertRaises(RegistrationCaptured) |
| ut/kv_offload/test_mooncake_layerwise_connector.py | 66 | worker.layer_storage_slots[1] == worker.layer_storage_slots[4]; worker._cache_write_events == [None]; all((not event.is_set() for event in worker.storage_send_done_events)); unittest.TestCase().assertRaisesRegex(RuntimeError, 'write failed'); self.assertRaises(SystemExit); self.assertRaises(ValueError); self.assertRaises(RuntimeError); self.assertRaisesRegex(NotImplementedError, 'does not support packed SFA main KV caches'); self.assertRaisesRegex(NotImplementedError, 'DCP replicated indexer cache'); self.assertRaisesRegex(AssertionError, 'must share one KV cache group'); self.assertRaisesRegex(NotImplementedError, 'one contiguous packed cache tensor') |
| ut/kv_offload/test_native_cpu_offload.py | 13 | [view.shape for view, _ in views] == [(4, 12), (4, 12)]; spec_cls is NPUOffloadingSpec; spec.num_chunks == 10; pytest.raises(ValueError, match='block payload is non-contiguous') |
| ut/kv_offload/test_npu_offload_spec.py | 9 | captured_cpu_tensors[0][0].shape == (3, 8); worker._mmap_region is None; calls == [('store', 1, 'npu', 'cpu'), ('load', 2, 'cpu', 'npu')]; pytest.raises(AttributeError, match='create_next_view') |
| ut/kv_offload/test_pool_worker_pp_layer_count.py | 3 | meta is not None; local_map == {4: 1, 5: 2, 6: 3, 7: 4}; worker.sync_save_events[-1].record.assert_called_once_with() |
| ut/kv_offload/test_pool_worker_pp_object_bounds.py | 6 | builder.layer_byte_offset == dcp_rank * stride + 42 * mib; copied_bytes == sum(worker.group_block_len[0]) |
| ut/kv_offload/test_preempt_offload_connector.py | 39 | worker.gpu_kv_caches[first_name].shape == large.shape; metadata.need_flush is False; merged.completed_store_events == {1: 1, 2: 5, 4: 1}; connector.build_connector_worker_meta().completed_store_events == {3: 1} |
| ut/kv_offload/test_sfa_pd_peer_restart.py | 10 | thread.storage_send_done_events[0].is_set(); _messages(first) == [MF_META, READ_READY_BATCH, READ_READY_BATCH]; not thread.storage_send_done_events[0].is_set(); pytest.raises(RuntimeError, match='outstanding KV reads'); pytest.raises(RuntimeError, match='different Decode processes'); pytest.raises(RuntimeError, match='engine ID disappeared') |
| ut/kv_offload/test_sfa_pd_rd2h_connector.py | 72 | connector.connector_scheduler is scheduler.return_value; infer_sfa_component_group_ids(config) == (1, 0); scheduler.assert_called_once_with(config, cache_config, 'prefill'); pytest.raises(RuntimeError, match=f'indexer scale presence mismatch.*P={p_has_scale}, D={d_has_scale}'); pytest.raises(RuntimeError, match='built no transfer descriptors'); pytest.raises(RuntimeError, match='no destination blocks'); pytest.raises(RuntimeError, match='indexer destination range is incomplete'); pytest.raises(RuntimeError, match='cmpl-parent-1'); pytest.raises(RuntimeError, match='send thread stopped'); pytest.raises(RuntimeError, match='memfabric read failed'); pytest.raises(RuntimeError, match='mapping is missing layer 1'); pytest.raises(RuntimeError, match='register_kv_caches\\(\\)'); pytest.raises(ValueError); pytest.raises(RuntimeError, match='PP-aware D') |
| ut/kv_offload/test_sfa_pd_rd2h_lifecycle.py | 3 | sender.mark_layer_pending.call_count == 6; start_load.assert_called_once_with(metadata) |
| ut/kv_offload/test_sfa_pd_slot_admission.py | 4 | allocator.get('waiting') is None; scheduler.get_num_new_matched_tokens(request, 128) == (470, True) |
| ut/kv_offload/test_sparse_kv_offload_external_plan.py | 13 | sources.dtype == torch.int64; membership_again.data_ptr() == membership.data_ptr(); req_ids.np.tolist() == [adler32(b'first'), adler32(b'second'), 0, 0]; sparse_kv_ops.sparse_kv_warmup_lru_resident_threads.assert_called_once_with(8); pytest.raises(ValueError, match='same device') |
| ut/kv_offload/utils.py | 0 | len(scheduler.requests) == 0 |
| ut/kv_transfer/test_ascend_store_layerwise_lifecycle.py | 1 | pool.kv_send_thread.token_database is pool.token_database; pool.grouped_block_size == [16, 32] |
| ut/kv_transfer/test_layerwise_dcp_sharding.py | 8 | worker._is_layerwise_save_leader() is False; leaders == [0, 1] |
| ut/kv_transfer/test_layerwise_multi_cache_spec.py | 8 | layout.layer_cache_specs[0].indexer is None; len(layout.layer_cache_specs) == 4; pytest.raises(ValueError, match='no main cache spec') |
| ut/kv_transfer/test_layerwise_pp_global_layers.py | 7 | _layer_ids(_key(), 44) == list(range(44)) |
| ut/simple_kv_offload/test_simple_kv_offload.py | 10 | views['layer'].shape == (4, 6); flattened[0] is key_cache; registrations['SimpleCPUOffloadConnector'] == ('vllm_ascend.distributed.kv_transfer.kv_pool.kv_offload.simple.simple_cpu_offload_connector', 'AscendSimpleCPUOffloadConnector') |

## 使用边界

AST结构、断言存在及配置参数不是运行记录。新模型变更应由真实调用链选择源测试及其参数，再分别留收集数量、skip、失败、真实退出和数值/性能原始结果。CPU mock只证明被断言的Host行为；涉及torch_npu、分布式、编译或外部权重的路径必须在目标依赖与设备上另验。本次未导入/运行上游、未编译、未调用NPU或Agent A/B；未摘选的精确参数与完整Device语义不由本矩阵补造。
