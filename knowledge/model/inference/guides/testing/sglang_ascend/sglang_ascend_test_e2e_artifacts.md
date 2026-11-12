---
type: Guide
title: SGLang NPU集群测试产物的状态、基线与源码身份
description: 说明E2E harness的single/PD-mix/PD-separation资源区别、运行隔离、日志metric与baseline分离和metrics.json状态不等于技术验收。
tags:
- task.testing
- topic.model_serving
- topic.parallelism
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/test/ascend/e2e/run_npu_e2e_test.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/.github/workflows/nightly-test-npu-e2e-multi-node.yml
  role: supporting
created_at: '2026-11-08T12:21:43Z'
updated_at: '2026-11-09T04:35:53Z'
platforms: []
---

# SGLang NPU集群测试产物的状态、基线与源码身份

run_npu_e2e_test_case区分single的npu_size、PD-mix的node_size、PD-separation的prefill/decode/router_size，分别渲染Kubernetes模板。每次生成随机job/configmap名，并将run_id注入隔离标签；多节点先等pods ready再收集pod IP填ConfigMap。单卡资源数、node数与TP size不是同一个指标。

支持install_sglang_from_source与使用镜像包，两种模式需记录实际导入路径/commit；测试checkout版本可以只提供helper。所引 nightly workflow 构造的持久化路径含 branch、run attempt、workflow/镜像等身份；harness 仅在 /output/ 后至少4段时取前两段为 run_label，较短布局只取第二段，缺少该布局则为 unknown。其他调用布局须另外保存运行身份，不能依赖 run_label 自动具备同样字段，避免不同 CANN/A3/950 文件误合并。

generate_metrics_json从test_output.log读取[METRIC] key=value，将_baseline键拆到baselines，其余到metrics，另存test_case/test_type/status。status来自monitor_pod_logs是否成功返回，解析不到指标仍可能生成空metrics；JSON文件存在、status=pass或pod ready都不能代替具体数值、断言与完整退出日志。test_type从目录形状推导，目录变更也会影响分类。

finally通常删除pod与生成YAML，trouble_shotting模式保留用于排障；本文只记录代码职责，不执行集群创建或清理。复核应同时保存每rank日志、工具版本、模型/权重、resolved参数、负载、metrics与baseline以及skip/失败信号，比较前检查两边测量条件一致。
