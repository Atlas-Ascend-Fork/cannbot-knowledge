---
type: API
title: 兼容实现API：开关查询、算子名单与首次读取
description: 区分实现选择和CPU回退，保留发布七类入口、主线SDPA补充与查询含义。
tags:
- task.lookup
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-npu/torch_npu-npu-are_compatible_impl_enabled.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/torch_npu-npu-are_compatible_impl_enabled.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/torch_npu-npu-are_compatible_impl_enabled.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-npu/torch_npu-npu-use_compatible_impl.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/torch_npu-npu-use_compatible_impl.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/torch_npu-npu-use_compatible_impl.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/op_execution/TORCH_NPU_USE_COMPATIBLE_IMPL.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/op_execution/TORCH_NPU_LEGACY_IMPL_LIST.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/interface/EnvVariables.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/register/OptionRegister.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/register/OptionRegister.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/interface/EnvVariables.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/RandomUtil.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/distributed/tensor/_matrix_ops.py
  role: constraint
created_at: '2026-11-09T19:31:30Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# 兼容实现API：开关查询、算子名单与首次读取

## 固定版本与证据范围

文档固定为OpPlugin发布dedc316708372c9a8bfde4527abd2a94b74840f5及主线d84e9b1d6a558e5f27973cd4329f62968e46fdda，区分发布中文与主线中英文。发布配对TorchNPU为f3ecfe4a7ef7395754da7ca2e35661a7132b519b；补充的独立主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf不视为与OpPlugin main已配套。

产品逐接口、参数和版本消费；主线新增950DT不回推发布、不扩到950PR。旧Atlas产品保留来源身份，不由其名字推定其他型号。以下为静态审阅，没有导入上游、加载库、操作设备、采集或性能测试，知识卡stable不代表运行verified。


## 设置与查询

`use_compatible_impl(is_enable)`设置兼容策略；`are_compatible_impl_enabled()->bool`查询配置，不提供实际Kernel、每次读标志或全模型逐位等价的证据。发布页列GELU、LayerNorm、all_to_all、scatter、gather、MaxPool2d、functional.max_pool2d；主线增加SDPA，允许配合MATH后端选择。环境变量页还有自己的短名单，不能把任一页面当完整穷举。

两固定npu/__init__.py将值truthiness转TORCH_NPU_USE_COMPATIBLE_IMPL的1/0，读取非空且为1才True；这段Python没有额外bool类型检查，不把类型注解变为运行保证。发布支持A2/A3训练/推理等，主线另列950DT。

OpPlugin某些重载首次调用会static缓存策略，因此运行中查询True不保证该重载重新选路。[执行路径指南](../../guides/optimization/torch_npu/torch_npu_cpu_fallback_and_compatible_impl.md)已区分GELU/SDPA的实际分支。实现选择不等于CPU fallback，不把“与社区对齐”扩成所有API、内存布局或数值都相同。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-npu/torch_npu-npu-are_compatible_impl_enabled.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/torch_npu-npu-are_compatible_impl_enabled.md)（primary）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/torch_npu-npu-are_compatible_impl_enabled.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-npu/torch_npu-npu-use_compatible_impl.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/torch_npu-npu-use_compatible_impl.md)（primary）
- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/torch_npu-npu-use_compatible_impl.md)（constraint）
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/__init__.py)（implementation）
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/__init__.py)（implementation）

## USE_COMPATIBLE_IMPL/LEGACY_IMPL_LIST 惰性解析与选项注册表实现

主线 `ac0e1564…` 的 op_execution 两页（`TORCH_NPU_USE_COMPATIBLE_IMPL.md`、`TORCH_NPU_LEGACY_IMPL_LIST.md`）与 C++ 选项层逐句对照。`TORCH_NPU_USE_COMPATIBLE_IMPL` 走选项注册表：`REGISTER_OPTION_INIT_BY_ENV`（EnvVariables.cpp :293）展开为 type="env" 的 `OptionInterfaceBuilder`，在 C++ 模块加载时一次性 `getenv` 并 `Set` 入注册表（OptionRegister.h :107-113；OptionRegister.cpp :67-75）；`CheckCompatibleImpl` 每次调用经 `GetOption` 现场取值、`value_or("0")=="1"` 判真（OptionRegister.h :123-130）——仅精确字符串 "1" 为真，"01"/"true"/带空格值静默判假、无告警。运行中经 `use_compatible_impl`/`SetOption` 改写注册表对后续 `CheckCompatibleImpl` 调用可见；文档「import torch 之前配置」是环境变量路线的正确约束（本卡前文的 OpPlugin 重载首次调用 static 缓存是另一层，两层并存）。文档「配置=1 时自动配置 use_compatible_impl(True)」在实现上是同一选项键的共享状态（本卡前文 `_npu_getOption` 读取面），不是导入期调用该 Python API。

`TORCH_NPU_LEGACY_IMPL_LIST` 不进选项注册表：`GetCompatibleConfig` 为函数内 static（EnvVariables.cpp :296-299），首次 `CheckCompatibleImplBlackListFor`/`CheckCompatibleImplFor` 查询才 `getenv` 解析——惰性读取而非进程启动时；「必须在启动 Python 进程前配置」是保守表述，首次受影响调用前在进程内改 `os.environ` 仍会被读到，首次查询后永久缓存。解析为逗号切分+空白 trim、空 token 跳过（:45-52、:66-95），未知项 `TORCH_CHECK` 并在错误信息中列出支持项（:96-107；`CompatibleKeyOptionsToString` :54-64；当前仅 `randomness`，:28-33）；文档「逗号分隔/区分大小写/异常提示支持项」与实现一致。优先级 `CheckCompatibleImplFor(key)`=名单命中即 legacy、否则回落全局开关（:306-311），与两页「列表优先级高于全局开关、未列入不受该变量影响」一致。

随机数消费者的实际取值路径：OpPlugin `RandomUtil.h` 的 `is_randomness_legacy_impl` 只查 `CheckCompatibleImplBlackListFor(Randomness)` 且自身 static 缓存（:143-147），不查全局开关——全局 `TORCH_NPU_USE_COMPATIBLE_IMPL` 不翻转随机数路线。950（`IsAclnnOnly`）上 `prepare_randomness_compatible` 默认社区对齐路线，仅名单命中时经 `configure_cann_randomness_once` 用 `GetOpApiFuncAddr("aclnnSetPytorchRandom")` 动态解析并以 0/1 配置 legacy/compat（:122-140），符号缺失仅 LOGI 跳过并保持默认——文档「CANN 不支持该能力时保留默认实现」的行级锚定；`std::call_once` 单次生效。

`CheckCompatibleImpl` 的树内消费面超出文档页的四个算子名单：`isDeviceCtxActive` 在兼容模式改查 primary context（NPUFunctions.cpp :357），CachingHostAllocator 的 Host 分配 device guard 同理（CachingHostAllocator.cpp :199），`currentStreamCaptureStatus/Id` 在兼容模式要求设备上下文已激活（NPUGraphsUtils.h :75-96），ProcessGroupHCCL 在 gather/scatter/alltoall 读同一开关（:6995/:7143/:7905；gather 读窗确认 `!use_compatible_impl || !is_compatible_soc` 即 runtime_error NOT_SUPPORT，scatter/alltoall 仅锚定标志读取）。DTensor matmul 策略门用裸 `os.getenv` 于导入时分支（_matrix_ops.py :62），与选项注册表不同源，语义归[DTensor 布局卡](../../../training/guides/torch_npu_dtensor_matmul_gradient_layouts.md)。

发布差异：发布 `EnvVariables.cpp` :172-173 与主线同有 `INIT_BY_ENV`+`BOOL_FUNCTION` 布尔门；但 `CompatibleConfig`/`TORCH_NPU_LEGACY_IMPL_LIST`/`CheckCompatibleImplFor` 在发布 csrc 全树 rg 零命中，发布 docs 亦无 environment_variable 树——legacy 名单与 per-key 优先级是主线能力，不回推发布版。

## 环境变量与选项注册表来源

- [op_execution/TORCH_NPU_USE_COMPATIBLE_IMPL.md @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/op_execution/TORCH_NPU_USE_COMPATIBLE_IMPL.md)（primary；:1-45 全文）
- [op_execution/TORCH_NPU_LEGACY_IMPL_LIST.md @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/op_execution/TORCH_NPU_LEGACY_IMPL_LIST.md)（primary；:1-48 全文）
- [主线 EnvVariables.cpp @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/interface/EnvVariables.cpp)（primary；:1-150 与 :240-369）
- [主线 OptionRegister.h @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/register/OptionRegister.h)（implementation；:1-177 全文）
- [主线 OptionRegister.cpp @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/register/OptionRegister.cpp)（implementation；:1-120）
- [发布 EnvVariables.cpp @f3ecfe4a](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/interface/EnvVariables.cpp)（implementation；:160-180；负向证据：发布 csrc 全树 rg CompatibleConfig/LEGACY_IMPL_LIST/CheckCompatibleImplFor 零命中）
- [OpPlugin RandomUtil.h @d84e9b1d](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/RandomUtil.h)（implementation；:1-60 与 :110-160）
- [主线 _matrix_ops.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/distributed/tensor/_matrix_ops.py)（constraint；:55-75）
