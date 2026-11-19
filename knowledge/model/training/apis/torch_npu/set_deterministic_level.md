---
type: API
title: set_deterministic_level：全局等级、布尔状态与 CANN 门槛
description: 说明 0..3 等级、动态修改、失败恢复和 Runtime/算子包双重条件，避免只检查 Python 标志。
tags:
- task.lookup
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/torch_npu-npu-set_deterministic_level.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/npu/Module.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUFunctions.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/GetCANNInfo.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/OpParamMaker.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-npu/torch_npu-npu-set_deterministic_level.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/torch_npu-npu-set_deterministic_level.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/__init__.py
  role: implementation
created_at: '2026-11-09T08:47:30Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# set_deterministic_level：全局等级、布尔状态与 CANN 门槛

## 固定版本与接口

依据OpPlugin `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 完整接口页与TorchNPU `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` Python/C++实现，产品范围A2/A3训练与推理、950DT；其他产品不在本卡筛选范围。适用于全局CANN确定性配置，不直接替代图内局部scope。

```python
torch_npu.npu.set_deterministic_level(level)  # 无返回值
```

level为整数0/1/2/3，默认请求值0；0关闭，1开启确定性，2强一致性，3 Batch一致性。API页当前仅确认level2影响torch.mm，不能据“强一致性”名称推导所有算子都改变算法；level3的目标为跨batch大小的一致性，也不自动证明模型包含的所有算子已满足该能力。

## 版本门槛与实际等级

文档要求CANN≥8.5.0支持0/1/2、≥9.2.0支持3。主线C++对3还检查Runtime≥9.2.0，并要求下列两组算子包之一满足≥9.2.0：OPP与OPP_KERNEL均满足，或按SoC选择的拆分ops包全部满足。只升级Runtime而遗留旧算子包仍可能报错；未取得版本信息也不能当作满足。版本检查结果在进程内缓存，更新安装后应重新启动，不在当前进程中靠再次调用探测新安装。

选择拆分包时，旧SoC分支检查ops_math、ops_nn、ops_cv、ops_legacy，其余分支还包含ops_transformer；这只是当前实现的判断，不是本卡宣称所有产品任意配置都具备level3。CANN9.0发布基线不满足该门槛。

Python封装会协调torch.use_deterministic_algorithms的布尔状态：设0而已开启时先关闭，设≥1而未开启时先开启，均给Warning；随后调用C++。如调用失败，会恢复本卡调整过的布尔状态并重抛异常。不能只看到Warning或布尔值改变就判定请求等级已成功应用。

C++保存requested_level；捕获实际状态时布尔开关False对应effective_level=0，True且请求值0则为1，否则取请求值。Python封装还警告调用本接口后不要再用torch.use_deterministic_algorithms混配；它们不是独立开关。无需为“确保生效”在两者之间反复来回切换。

## 动态配置与实现边界

接口页允许动态修改，后续新下发算子使用新等级，不支持多线程配置。主线ApplyDeterministicSnapshot仅对已应用level0且仍为0的线程状态快速返回；变化后的level会进入应用路径，并区分Legacy和V2后端。V2通过ACL_OPT_DETERMINISTIC直接设有效等级；不能把文档中旧式两选项映射表机械当作V2的逐行调用轨迹。

这不保证已经捕获/编译的图会自动重新配置，也不保证多线程竞争安全。固定主线总览的“同线程只认第一次有效设置”与本接口和当前实现存在冲突，详见[确定性范围](../../guides/torch_npu_deterministic_algorithm_scope.md)。

## 核验

记录同一进程中的软件包、Runtime/算子包版本、requested与effective状态，检查新下发算子及CANN应用日志，再比较相同输入多次输出。跨batch一致性、torch.mm强一致性和普通重复执行分别验收，不用设置成功替代数值验证。本文未执行上游、NPU或性能测试。

- [图内确定性与控核](../../../inference/guides/optimization/torchair/torchair_core_limits_and_determinism.md)

## 发布页及主线英文的保留差异

发布文档只列0/1/2、CANN>=8.5且禁止动态修改；主线中文新增level3、CANN>=9.2并允许后续下发算子动态使用新等级，英文主线仍保留禁止动态修改和覆盖全局布尔的旧说明。不能将中文新说明回推发布，也不以英文旧句删除当前主线实现；不支持多线程的限制保留。

发布Python会直接改变torch确定性布尔再设C++，没有主线新增的失败回滚；主线同步effective等级的helper也不同。来源旧表对level1有多余“关闭确定性”单元格，按各版本正文与实现解释，不能机械复制成一个自洽矩阵。legacy两选项映射0=(0,0)、1=(1,0)、2=(1,1)、3=(3,1)，仍不代替前述V2实际路径。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/torch_npu-npu-set_deterministic_level.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/__init__.py)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/npu/Module.cpp)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUFunctions.cpp)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/GetCANNInfo.cpp)（implementation）
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/OpParamMaker.cpp)（implementation）

- [固定来源 7](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-npu/torch_npu-npu-set_deterministic_level.md)（constraint）

- [固定来源 8](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/torch_npu-npu-set_deterministic_level.md)（constraint）

- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/__init__.py)（implementation）
