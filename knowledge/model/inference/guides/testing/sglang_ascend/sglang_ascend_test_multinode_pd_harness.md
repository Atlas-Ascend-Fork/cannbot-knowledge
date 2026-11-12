---
type: Guide
title: SGLang NPU多节点PD测试的角色、实例分组与服务地址
description: 说明Kubernetes测试按pod编号和nnodes构造P/D实例、MemFabric store与bootstrap端口映射、router只注册实例master及ready信号的边界。
tags:
- task.testing
- topic.parallelism
- topic.model_serving
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/test/ascend/e2e/test_npu_multi_node_utils.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/test/ascend/disaggregation_utils.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/manual/ascend/disaggregation_utils.py
  role: supporting
created_at: '2026-11-08T12:20:22Z'
updated_at: '2026-11-08T12:32:08Z'
platforms: []
---

# SGLang NPU多节点PD测试的角色、实例分组与服务地址

上游测试harness按hostname数字后缀取得pod_index，按名字prefill/decode识别角色，经ConfigMap找各自master。未显式--node-rank且nnodes>1时，以floor(index/nnodes)分组，node_rank=index%nnodes，master取该组首pod；nnodes1或显式node-rank路径按独立实例处理。名称或ConfigMap错误会在模型计算前破坏拓扑。

ASCEND_MF_STORE_URL缺省构造为第一个Prefill master的tcp端口24666；分组Prefill的bootstrap端口在基础值上加group_index，独立实例加pod_index。各角色env随后可覆盖，需检查最终值而非只看统一设置日志。服务参数未显式给时补device=npu、attention=ascend、transfer=ascend。

router只注册多节点实例的master URL和对应bootstrap端口，不把每个worker当独立服务；等待端口后以pd-disaggregation/cache_aware启动。端口打开、/health HTTP200与整个P→D KV内容/首token一致性不同，验收必须包含真实路由请求。

check_role装饰器在不匹配角色返回None，这表示该节点跳过动作，不是测试成功。单机TestDisaggregationBase还可从SGLANG_TEST_PD_DISAGG_BACKEND/DEVICES配置传输；get_rdma_devices_args历史按CUDA_VISIBLE_DEVICES及mlx5列表推导，不能直接当昇腾网络自动发现工具。

测试环境的ConfigMap、服务端口、共享盘和pod命名是harness假设，不是生产部署唯一要求。本次未创建pod、访问集群或启动服务。
