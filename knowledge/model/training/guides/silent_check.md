---
type: Guide
title: silent_check三代算子：v1 ACE、v2/v3 aclnn的梯度静默校验与fail-closed兼容
description: 保存三版schema的原地更新标注语义、统计状态张量、参数下采样、v3视图元数据透传与DO_COMPATIBILITY双路失败行为，区分op层与ASD框架层；并给出 npu_asd_detect 的取值来源与 NPU_ASD_ENABLE 模式枚举（0..3 的两处独立解析与失败文案）。
tags:
- task.lookup
- task.debugging
- topic.precision
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/SilentCheckKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/SilentCheckV2KernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/SilentCheckV3KernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: header
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/SilentCheckKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/SilentCheckV2KernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/SilentCheckV3KernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/register/OptionsManager.h
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/register/OptionsManager.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/utils/_step.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/asd/asd.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/distributed/ProcessGroupHCCL.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/register/OptionsManager.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/register/OptionsManager.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/utils/_step.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/asd/asd.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/distributed/ProcessGroupHCCL.cpp
  role: implementation

created_at: '2026-11-12T05:36:44Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# silent_check三代算子：v1 ACE、v2/v3 aclnn的梯度静默校验与fail-closed兼容

## 版本与范围

本卡依据 OpPlugin 主线候选 d84e9b1d6a558e5f27973cd4329f62968e46fdda 与发布 dedc316708372c9a8bfde4527abd2a94b74840f5：三个实现文件两 pin 注释/空白归一化后 token 等价（仅排版差异），yaml schema 登记原文相同。三个入口均为下划线内部算子：无官方 API 文档页、无 codegen docstring、无 `derivatives.yaml` 自动微分接线、无 `_meta_registrations.py` 推导、无官方测试用例。v1 登记 `acl_op: all_version`（旧 ACE 路径），v2/v3 登记 `op_api: all_version`。本文为静态源码审阅，未执行。

## 三代入口对比

| 版本 | schema 要点 | 设备入口 | result 分配 | 机制特点 |
|--|--|--|--|--|
| `_npu_silent_check` | `input_grad(a!), val, pre_val(b!), min_val(c!), max_val(d!), val_counter, c_min_steps, c_thresh_l1, c_coeff_l1, c_thresh_l2, c_coeff_l2` | 旧 ACE `OpCommand("SilentCheck")`（非 aclnn） | `apply_tensor(val_counter)`，沿用 val_counter 形状/dtype | 统计状态（前值/min/max/计数）全部由调用方张量持有 |
| `_npu_silent_check_v2` | `val, input_grad(a!), sfda(b!), step(c!), c_min_steps, c_thresh_l1, c_coeff_l1, c_thresh_l2, c_coeff_l2, npu_asd_detect` | `aclnnSilentCheck` | `step` 形状、dtype 固定 Int | 新增 `sfda` 状态张量与 `npu_asd_detect` 整型标志；`c_min_steps` int64→int32、阈值/系数 double→float 下采样 |
| `_npu_silent_check_v3` | `val, input_grad(a!), step(b!), max(c!), avg(d!), c_thresh_l1, c_thresh_l2, betal, npu_asd_detect` | `aclnnSilentCheckV2` | `step` 形状、dtype 固定 Int | `max/avg` 状态张量与 `betal` 系数（设备侧更新方程不可见，语义不由参数名推定）；向设备侧透传 `input_grad` 的 size/stride/storage_offset 元数据，转发本身不承诺任意非连续视图支持 |

## 原地语义

- 三版的 `input_grad` 都标注 `(a!)`：含义是允许设备侧原地更新该张量，不等于每次成功调用都必然改写其中每个梯度；设备侧是否及如何改写，本层源码不可见。不能把该算子当只读探针使用；调用后不要假设梯度保持原值，梯度正确性复核需另行留副本。
- v1 的 `pre_val/min_val/max_val`、v2 的 `sfda/step`、v3 的 `step/max/avg` 同为原地更新标注参数：设备侧被允许更新这些状态张量，是否及如何更新由设备侧决定（v1 的 OpCommand 将 `input_grad` 与三个状态张量绑定为 Output，是该更新权限的静态来源）。跨步统计状态的初始化与复用由调用方（ASD 框架层）管理，本层不做保证。
- 返回值 `result`：v1 经 `apply_tensor(val_counter)` 沿用 val_counter 的形状与 dtype（options 继承，wrapper 不强制整型）；v2/v3 显式 `at::kInt`（Int32）并按 step 形状分配。其元素语义（异常标志/计数/掩码）由设备侧定义，本层源码不可见，不要按形状猜测含义。

## 兼容失败行为（v2/v3）

`DO_COMPATIBILITY(aclnnSilentCheck / aclnnSilentCheckV2, aclnnNotFound*)` 在运行库缺少对应符号时：

- aclnn-only 模式：`TORCH_CHECK false`（NOT_SUPPORT，"Current device only support aclnn operators, but ... not found"）；
- 非 aclnn-only 模式：打 warning 后调用 fallback，而 fallback 是无条件 `TORCH_CHECK false`（INTERNAL，"aclnnSilentCheck(V2) not found."）。

两条路径都 fail-closed：不会静默跳过检查、不会自动回退 CPU、不会返回未定义结果。v1 无兼容门，ACE OpCommand 直接下发，缺失时的失败形态由旧算子分发层决定（本卡不展开）。

## 与 ASD 框架层的关系

- torch_npu Python 侧的 `NPU_ASD_CONFIG` 框架（梯度特征值检测、冷却与三振）见[特征值检测指南](torch_npu_feature_value_detection.md)：其 `_step.py` 按底层 silent-check 版本选择兼容分支并提示升级，即本卡三版算子是那条框架链的设备执行环节之一；v2/v3 schema 中的 `npu_asd_detect` 整型标志透传设备侧。
- [matmul_checksum](../../inference/apis/torch_npu/matmul_checksum.md)（matmul ABFT 校验）与特征值检测是相互独立的校验路径，三者不互相替代，也不共享阈值参数。
- 阈值（`c_thresh_l1/l2`）、系数（`c_coeff_l1/l2`）、`c_min_steps`、`sfda` 内容与 `betal` 的设备侧语义不在本仓（ops/ascendc 无 aclnnSilentCheck/aclnnSilentCheckV2 设备文档），不能从参数名推导判定规则。

## 失效边界

- 三版行为全部来自实现静态阅读，无任何官方用例或文档页；未运行验证。
- `all_version` 标注只是本固定源的注册证据，不证明所有 CANN/torch_npu 组合都装载了对应符号；部署前应按实际运行库确认走 v1/v2/v3 哪一代（框架层的版本选择逻辑见上节指南卡）。
- `result` 的元素语义与异常上报路径（是否写 Event/日志、是否触发框架三振）由设备侧与 Python 框架侧共同决定，本层不可见。

## npu_asd_detect的取值来源与NPU_ASD_ENABLE模式枚举（增补）

上文三代对比表把`npu_asd_detect`记为“整型标志透传设备侧”；本节给出它的取值来源与模式枚举（TorchNPU两pin：主线`ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`、发布`f3ecfe4a7ef7395754da7ca2e35661a7132b519b`）。枚举定义在torch_npu仓（两pin同文）：`enum SilenceCheckMode { CHECK_CLOSE = 0, PRINT_WARN_LOG = 1, REPORT_ALARM = 2, PRINT_ALL_LOG = 3 }`（主线OptionsManager.h:34–39、发布:20–25）。

| 解析/消费点 | 实际门槛→动作 | 失败/边界 |
| --- | --- | --- |
| C++解析`OptionsManager::GetSilenceCheckFlag()`（主线OptionsManager.cpp:464–488、发布:387–412） | 函数局部`static` lambda只解析一次并缓存；`get_and_log_env("NPU_ASD_ENABLE")`、`strtol` base 10、未设置按0；switch 0/1/2/3映射四个枚举名，其余值`TORCH_CHECK(false, "NPU_ASD_ENABLE should be 0, 1, 2 or 3", PTA_ERROR(VALUE))`；返回原始uint32值（非枚举体） | 静态缓存意味着首次调用后环境变量修改不再生效（与特征值检测指南卡“初始化前设置”口径一致）；非数字字符串经strtol截断后落入default分支照抛 |
| Python独立解析（`torch_npu/utils/_step.py`旧入口分支，仅`NPU_ASD_CONFIG`完全未设置时到达；主线:284–307、发布:271–291） | 值域字面`["0","1","2","3"]`，否则`ValueError`，文案给出运行语义：0 as `ASD closed`、1 as `ASD opened, print error logs`、2 as `ASD opened, print error logs and raise exception`、3 as `ASD opened, print debug logs and raise exception`；`asd_enable>0`时按`_get_silent_check_version()`分叉：==1（旧CANN）仅值1可降级到V1补丁路径并告警；否则告警后`silent_check.set_check_enable(asd_enable)`；任一使能结尾`Module.__call__ = _custom_call` | 文案与C++枚举名的对应（PRINT_WARN_LOG↔只打印、REPORT_ALARM↔打印并抛异常、PRINT_ALL_LOG↔debug日志并抛）是本节对照记录，不由名字互推；C++ static缓存与Python分支是**两处独立解析**，取值一致性不在此层保证；`_get_silent_check_version`的取值实现不在本卡来源内 |
| asd_flag流（`torch_npu/asd/asd.py`主线:123–158） | `set_check_enable`存的值经`_input_hook(idx, check_enable)`传入`_SilentFaultDetectorV2.silent_fault_check`（grad为None或既非bfloat16也非float32直接返回；`val = torch.norm(grad)`）后调用`torch_npu._npu_silent_check_v2(..., asd_flag)`——**npu_asd_detect承载的就是NPU_ASD_ENABLE原始值1/2/3** | hook链在训练Module首尾权重上安装（first/last weight），非逐层；FP16梯度命中dtype过滤器时整链关闭（asd.py内的check_dtype路径，字面照录） |
| V1补丁路径（asd.py `_asd_patch`主线:108–116，由`_init/patches/asd_patches.py`安装时调用） | 仅接受0/1：`env_value not in ["0","1"]`即`ValueError "NPU_ASD_ENABLE should be 0 or 1!"`；值为1时patch `torch.nn.functional.layer_norm`/`embedding`挂梯度钩子，走本卡V1表（`torch_npu._npu_silent_check`→ACE SilentCheck） | 0/1域与_step.py的0..3域是不同层约束——旧CANN上设2/3在_asd_patch处报错（_step.py:294注释同口径）；V1补丁与V2 hook是互斥路径（版本门决定） |
| HCCL调用面（`ProcessGroupHCCL.cpp`） | 触发门`GetSilenceCheckFlag() != CHECK_CLOSE`（主线:4516–4522，三同构入口）；实际调用`op_plugin::_npu_silent_check_v2(..., static_cast<int64_t>(GetSilenceCheckFlag()))`（主线:4251–4261、发布:3617–3620）——HCCL侧npu_asd_detect来自C++ static缓存而非Python分支 | C++与Python两处解析的首次触发时序（谁先固化缓存）未在本层确定；HCCL触发的完整过滤链（L_TRAIN/opType/反向窗口/ALLREDUCE numel）属ProcessGroupHCCL主题，本节只钉flag来源 |
| op-plugin侧透传（本卡主对象） | `_npu_silent_check_v2`/`_npu_silent_check_v3`把npu_asd_detect按int64**原样**传入aclnnSilentCheck/aclnnSilentCheckV2（见上文三代对比表：阈值/系数double→float下采样，标志位无转换）；注册面`_npu_silent_check`仅acl_op、`_v2`/`_v3`仅op_api（op_plugin_functions.yaml主线:5754–5761、发布:5514–5521） | **设备侧对1/2/3的解释（对应何种日志/告警/抛出行为）不在本仓源集**——Python文案只约束框架层动作，不把“print error logs and raise exception”外推为aclnn内核行为 |

排查NPU_ASD相关问题时先钉三件事：实际生效的解析点（C++缓存触发者与Python分支是否同值）、`_get_silent_check_version()`的实际版本（决定V1补丁/V2 hook路径）、以及npu_asd_detect最终进入哪代算子（v2的aclnnSilentCheck还是v3的aclnnSilentCheckV2）。`NPU_ASD_CONFIG`新入口对旧变量的优先关系与三振/冷却框架见[特征值检测指南](torch_npu_feature_value_detection.md)。本节静态阅读：未运行钩子、未设环境变量、未执行任何设备代码。

### npu_asd_detect增补证据

- [OptionsManager.h ac0e156](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/register/OptionsManager.h)（primary）：34–39；SilenceCheckMode枚举完整定义。
- [OptionsManager.cpp ac0e156](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/register/OptionsManager.cpp)（primary）：464–488；GetSilenceCheckFlag完整函数体（static缓存+switch+default TORCH_CHECK）。
- [OptionsManager.h f3ecfe4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/register/OptionsManager.h)（implementation）：20–25；同枚举。
- [OptionsManager.cpp f3ecfe4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/register/OptionsManager.cpp)（implementation）：387–412；同函数体（TORCH_CHECK在:407），与主线去空白字符流相同（仅排版）。
- [_step.py ac0e156](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/utils/_step.py)（primary）：284–307；NPU_ASD_ENABLE旧入口分支完整段（ValueError文案+版本门+set_check_enable+Module.__call__包装）。
- [_step.py f3ecfe4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/utils/_step.py)（implementation）：271–291；同分支（告警文案措辞略异，逻辑同构）。
- [asd.py ac0e156](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/asd/asd.py)（primary）：108–116（_asd_patch 0/1域）、123–158（_SilentFaultDetectorV2.silent_fault_check与_input_hook）；V2检测器调用链完整段。
- [asd.py f3ecfe4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/asd/asd.py)（implementation）：106–114、121–158；同两段（f-string告警为旧式格式化，逻辑同构）。
- [ProcessGroupHCCL.cpp ac0e156](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/distributed/ProcessGroupHCCL.cpp)（primary）：4251–4261（static_cast传参）、4516–4522（触发门）。
- [ProcessGroupHCCL.cpp f3ecfe4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/distributed/ProcessGroupHCCL.cpp)（implementation）：3617–3620、3848–3852；同两处（行号不同，逻辑一致）。
- [op_plugin_functions.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：5754–5761；_npu_silent_check三条目（该文件已列于frontmatter来源）；发布5514–5521同文。
- 负向证据：本仓知识正文对 `SilenceCheckMode|PRINT_WARN_LOG|REPORT_ALARM|PRINT_ALL_LOG|set_check_enable` 的覆盖仅有本卡前文与HCCL watchdog卡的调用面记录——两处均把模式枚举归op-plugin/ASD侧；本节为该枚举取值与消费链在本仓的首次系统化记录。
