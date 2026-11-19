---
type: API
title: stress_detect：在线硬件检测模式、返回码与作业限制
description: 区分检测执行失败和硬件故障，保留HCCS建组、10GB及同节点作业条件。
tags:
- task.lookup
- task.debugging
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-npu/（beta）torch_npu-npu-stress_detect.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/（beta）torch_npu-npu-stress_detect.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/(beta)torch_npu-npu-stress_detect.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/utils.py
  role: implementation
created_at: '2026-11-09T19:31:30Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# stress_detect：在线硬件检测模式、返回码与作业限制

## 固定版本与证据范围

文档固定为OpPlugin发布dedc316708372c9a8bfde4527abd2a94b74840f5及主线d84e9b1d6a558e5f27973cd4329f62968e46fdda，区分发布中文与主线中英文。发布配对TorchNPU为f3ecfe4a7ef7395754da7ca2e35661a7132b519b；补充的独立主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf不视为与OpPlugin main已配套。

产品逐接口、参数和版本消费；主线新增950DT不回推发布、不扩到950PR。旧Atlas产品保留来源身份，不由其名字推定其他型号。以下为静态审阅，没有导入上游、加载库、操作设备、采集或性能测试，知识卡stable不代表运行verified。


## 模式与返回

`torch_npu.npu.stress_detect(detect_type='aic')`支持aic与hccs；无效类型在所查包装警告后返回1。文档0检测通过、1执行失败、2硬件故障，不把1解释为无故障或可继续训练。产品发布A2/A3训练，主线另列950DT。

hccs要求先初始化全局ProcessGroup并为本机卡建组。两固定utils.py还读取RANK/LOCAL_WORLD_SIZE/WORLD_SIZE，缺项返回1；按连续本机rank分组并缓存hccl_detect_group，假设world/local world和rank布局正确。它不是任意拓扑、弹性变更或单rank单独调用的现成配方；通信/环境误配失败与硬件故障区分。

## 调用窗口和样例边界

文档要求预留10GB；建议训练前后或step间，不支持同节点多个训练作业，不建议多线程；分区场景不进行调压。调压恢复失败574007附带外部恢复/重启说明，没有在本次执行，也不把机器重启作为自动动作。

示例返回1仅打印继续、其他非0才抛异常；那不是“所有失败已被拦截”的验收逻辑。检测有执行和资源成本，不能用一次0替代长期硬件/数值诊断或模型优化收益测量。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-npu/（beta）torch_npu-npu-stress_detect.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/（beta）torch_npu-npu-stress_detect.md)（primary）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/(beta)torch_npu-npu-stress_detect.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/utils.py)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/utils.py)（implementation）
