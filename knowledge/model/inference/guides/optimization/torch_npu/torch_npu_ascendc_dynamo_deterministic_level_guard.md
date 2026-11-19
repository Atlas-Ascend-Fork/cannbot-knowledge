---
type: Guide
title: AscendC编译确定性Guard：有效等级检查与重编译边界
description: 追踪主线Inductor包装器安装Dynamo等级Guard的真实入口，区分TracingContext缺失、有效等级同步、缓存身份与已有捕获对象。
tags:
- task.implementation
- topic.compilation
- topic.precision
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/dynamo/_deterministic_guard.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/utils/_dynamo.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_init/patches/dynamo_patches.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_init/patches/patch_manager.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/utils/_dynamo.py
  role: implementation
created_at: '2026-11-10T15:09:42Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# AscendC编译确定性Guard：有效等级检查与重编译边界

## 固定版本与入口证据

定向核对PyTorch主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf的_deterministic_guard.py、编译包装器和初始化接线，并比较发布快照f3ecfe4a7ef7395754da7ca2e35661a7132b519b的对应wrapper。只有静态调用链证据，未导入、编译、检查实际Guard命中或执行NPU；整卡平台未知，保持draft与空平台。

主线torch_npu._initialize调用_apply_all_patches，PatchManager发现注册模块并调用dynamo组的apply_dynamo_methods_patch，后者调用add_dynamo_methods；该函数执行patch_inductor_wrapper，把_TorchCompileInductorWrapper.__call__替换为本地new_call。Guard helper因此有实际安装消费者，不能把它当成只定义未接通的样例。

## 仅在所选AscendC wrapper调用分支安装

new_call先按wrapper配置等解析backend，进入_NpuBackendEnvScope，执行compat_prepare_inductor_backend_for_call；只有精确backend=="ascendc"才调用install_npu_deterministic_level_guard，随后调用保存的原src_call。后端解析与选项语义见[Inductor配置](torch_npu_inductor_config_parsing.md)，不把拼写、其他后端或仅导入helper视为相同门控。

该函数是已替换wrapper的调用点；本卡没有展开上游TorchCompileInductorWrapper和所有Guard缓存消费者，**不声称每次compiled callable、每次模型推理或图replay都会重新安装Guard**。也不能从本分支证明其他后端完全没有确定性保护。

EnvScope在进入时保存并设置TORCHINDUCTOR_NPU_BACKEND，退出时恢复或删除先前不存在的值，且不抑制异常；这只是所读Python作用域管理，不是多线程修改环境和编译状态的隔离保证。

## 检查的是捕获时与复用时的有效整数等级

helper先取得TracingContext.try_get；为空即返回False，不读取等级，也不登记Guard。context存在时读取captured_level，再建立GlobalStateSource对应的Guard，加入tc.guards_context.dynamo_guards。其创建函数在guard manager根上登记lambda：每次该lambda被调用时重新读_get_deterministic_level，返回它是否等于captured_level；诊断代码字符串也记录同一等式。

不同非零等级即使都对应PyTorch确定性布尔True，这个整数相等条件仍可能不同。判断不依赖模型输入的某个Tensor形状，也不是把原布尔DETERMINISTIC_ALGORITHMS检查简单再写一次。

wrapper调用者没有检查helper返回的True/False，故“执行到AscendC分支”不等于已确认存在TracingContext并成功登记。若上下文缺失，它仍继续原src_call；不能把单次无重编译现象当成Guard已保护全部状态变化。

## getter在冲突时会同步状态

_get_deterministic_level先读取C++等级，再交给_sync_deterministic_level：等级0但torch.are_deterministic_algorithms_enabled为真时取1；等级>=1但布尔为假时取0；冲突时把新等级写回C++。无冲突则直接返回原等级。

捕获等级和lambda检查都使用这个getter，因此比较的是同步后的有效值，不是永久保存的“用户上一次请求值”。这里也不能将Guard当成纯观察无副作用函数：两套设置冲突时检查会参与状态同步。公开产品、CANN门槛和多线程限制仍按[set_deterministic_level](../../../../training/apis/torch_npu/set_deterministic_level.md)核对，不为命中图反复混配布尔开关和等级接口。

## Guard失效、缓存身份与设备对象各有范围

[AscendC确定性缓存身份](torch_npu_ascendc_deterministic_cache_identity.md)已解释FX/AOT缓存详情构造时添加等级字段。这张卡补Dynamo的状态相等谓词；字段记录与Guard登记是不同消费者，任一单独存在都不证明整个缓存/编译流程已正确隔离。

等级变化使这个lambda条件为假后，实际复用、失效、重编译和报错还由配套上游Guard机制及过滤配置决定；本卡没有运行该消费者，不承诺固定只新增一次编译或每个旧callable都会自动重建。通用[Guard过滤边界](dynamo_guards_and_backend_boundaries.md)仍适用，不能为压掉重编译就删除状态条件而不验数学语义。

该helper没有修改已经生成的kernel、已捕获的设备图或跨batch数值策略。Guard或缓存隔离成功，不等于任意算子已实现对应确定性等级，也不等于已有NPUGraph被重新配置、重新捕获或输出值已被保存。

## 发布版仅对照准确本地路径

发布wrapper的new_call先register_inductor_npu，再调用原src_call；所读patch_inductor_wrapper中没有主线的AscendC等级Guard调用。发布快照也缺少准确_deterministic_guard.py路径。该差异仅限定所查revision、文件和调用点，不否定发布组合的其他上游Guard、确定性机制或外部补丁，不把主线逻辑反向认证成发布能力。

实际核对时分别记录所选backend、wrapper是否进入、TracingContext、请求/有效等级及PyTorch布尔状态、Guard表达式与失败原因，再观察缓存查询、编译/捕获次数和数值。先保证设置与模型语义一致，再评价重编译开销；本次没有这些运行结果、性能数字或verified事件。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/dynamo/_deterministic_guard.py)（primary）：1–27。
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/utils/_dynamo.py)（implementation）：91–129、131–141、226–245、695–707。
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/__init__.py)（implementation）：702–717。
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/__init__.py)（implementation）：39–64。
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_init/patches/dynamo_patches.py)（implementation）：1–8。
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_init/patches/patch_manager.py)（implementation）：27–45、53–100、102–161、210–216。
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/utils/_dynamo.py)（implementation）：157–200、331–345。
