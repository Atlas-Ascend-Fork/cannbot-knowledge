---
type: Guide
title: SGLang 昇腾集群测试模板的设备、网络与共享目录前提
description: 区分 Volcano 与 green StatefulSet、设备资源计数、hostNetwork 和共享源码挂载，说明 PD 模板迁移的验证边界。
tags:
- task.implementation
- topic.parallelism
- topic.model_serving
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/test/ascend/e2e/k8s_multi_pd_mix.yaml.jinja2
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/test/ascend/e2e/k8s_multi_pd_separation.yaml.jinja2
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/test/ascend/e2e/k8s_multi_pd_mix_green.yaml.jinja2
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/test/ascend/e2e/k8s_multi_pd_separation_green.yaml.jinja2
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/test/ascend/e2e/k8s_single.yaml.jinja2
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/test/ascend/e2e/run_npu_e2e_test.py
  role: supporting
created_at: '2026-11-09T04:33:51Z'
updated_at: '2026-11-09T06:11:06Z'
platforms: []
---

# SGLang 昇腾集群测试模板的设备、网络与共享目录前提

## 选择模板再解释资源

本卡说明固定 SGLang 快照的 Kubernetes 测试部署前提，不是生产部署的通用清单。`run_npu_e2e_test.py` 对 `single` 使用单节点模板；多节点 `multi-pd-mix` 和 `multi-pd-separation` 在 `env=green` 时改选各自的 green 模板。`env` 不能只当作日志标签，它改变资源控制器、设备资源名、存储和镜像拉取策略。

| 路线 | 控制器与副本 | 设备资源 |
|---|---|---|
| single | Volcano Job，1 个 pod | 按 `npu_size` 请求和限制设备数 |
| 非 green 的 PD mix | Volcano Job，`node_size` 个副本，`minAvailable=node_size` | 每个副本固定请求和限制 16 个设备资源 |
| 非 green 的 PD separation | Volcano Job，分别创建 prefill/decode/router task，`minAvailable` 为三者副本数之和 | 每个 P/D 副本固定 16 个设备资源；router 只请求/限制 4 CPU |
| green 的 PD mix/separation | StatefulSet，并分别配套 headless Service | mix/P/D 副本使用 `huawei.com/Ascend910:16`；router 只请求/限制 4 CPU |

非 green 模板中的 CI/debug 设备名是 `huawei.com/ascend-1980`；green 使用 `huawei.com/Ascend910`，节点选择器也不同。这里的 16 是 Kubernetes 设备资源数量，不自动等于 TP size、物理卡数或模型实例数；实例如何按 `nnodes` 分组见[多节点 PD harness](../../testing/sglang_ascend/sglang_ascend_test_multinode_pd_harness.md)。单节点模板的 CPU requests/limits 为 46，green 分支另配置 128Gi 内存；这些是该测试模板的声明，不是模型运行最低资源结论。

## 网络与地址发现

所有多节点模板均启用 `hostNetwork: True`，并把 `POD_IP` 设置为 `status.hostIP`。harness 发现的地址因而按该宿主机网络布局解释；换成隔离 pod 网络时，不能继续假设 hostIP 就是可用的模型/通信端点。端口和多实例映射仍由 harness 处理，启用 hostNetwork 不替代 bootstrap、MemFabric store 和 router 地址的一致性核对。

`k8s_single.yaml.jinja2` 没有声明 hostNetwork，虽然同样把 `POD_IP` 填为 hostIP，不能将多节点的网络前提推广给单节点模板。green 的 headless Service 使用 `clusterIP: None`，Service 中列出的 `80/dummy-port` 不是模型 API 端口配置；实际服务地址仍需按启动参数和角色注册核对。

## 驱动、共享源码与控制面

模板使用 privileged 容器并挂载宿主机 `/usr/local/Ascend/driver`；模型镜像与宿主驱动配合是运行前提，模板本身没有验证二者兼容。CI/debug 通过 PVC 提供共享目录；green 使用宿主机 `/home`。共享卷同时挂载到测试共享目录、`/root/.cache` 和 `/root/sglang`，后者使用 `sglang_source_relative_path` 子路径。多节点源码、权重和结果路径是否在各节点一致可见，需要在目标集群核对，不能仅凭 pod 成功创建判断。

多节点 PD 模板向容器注入 `KUBECONFIG`、`NAMESPACE`、`KUBE_CONFIG_MAP` 和运行标识等参数。single 模板只注入其中的 `KUBECONFIG`，没有 `NAMESPACE`、`KUBE_CONFIG_MAP`，其渲染上下文也不提供 `kube_config_map`。模板中设置 KUBECONFIG 路径不等于凭据文件已经存在或具备访问 ConfigMap 的权限。非 green PD 模板初始化空 ConfigMap，由测试编排继续发现和填充角色地址；它不是静态写死的服务发现表。

single 模板额外挂载 16Gi 内存型 `/dev/shm`；所列多节点模板没有同等的显式 shm 挂载，不能从 single 推导所有路线均具有相同共享内存配置。普通多节点模板使用 `imagePullPolicy: Always`，green 专用模板使用 `IfNotPresent`；因此复现时要保存实际镜像 digest，不能只凭相同 tag 判断各节点代码一致。

## 验证与失效边界

适配新集群时，先核对模板路线、设备资源名和节点标签，再确认驱动挂载、共享子目录、控制面访问及角色端口可达。渲染后的设备资源数量与模型并行参数应分别核验。完成 pod ready 和端口检查后，仍需通过 router 发出真实请求并验证 P→D KV 传输及输出；这些验证本次均未执行。

本文只读取固定模板和选择逻辑，没有创建 pod、渲染/执行模板、访问 Kubernetes 集群或验证模型吞吐。模板中与特定测试环境绑定的资源名、PVC 和标签不是其他集群的兼容承诺。
