---
type: Guide
title: 历史FrameworkPTAdapter发布说明的适用边界
description: 保留旧Adapter特性时间线、FP16/格式/通信/Apex限制与中英文覆盖差异，防止套到当前版本；补发布快照导入期拦截链与Tensor.type重定向。
tags:
- task.lookup
- topic.compilation
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/docs/RELEASENOTE_zh/RELEASENOTE.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/docs/RELEASENOTE_en/RELEASENOTE.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/utils/npu_intercept.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/utils/unsupport_api.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/utils/tensor_methods.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/utils/dtensor.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/utils/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/utils/storage.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_init/registry/registry_manager.py
  role: implementation
created_at: '2026-11-09T17:27:10Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 历史FrameworkPTAdapter发布说明的适用边界

## 固定来源与历史身份

依据发布快照f3ecfe4a7ef7395754da7ca2e35661a7132b519b内旧RELEASENOTE双语文件。英文标题止于FrameworkPTAdapter3.0.RC2，中文新增3.0.RC3、3.0.0及5.0.RC1。目录所在提交不改变正文时代，不能将Adapter产品号当PyTorch版本，也不回推为26.0/PT2.8或主线当前限制。

来源硬件为旧Atlas800-9010/9000，另有昇腾710推理；未提供A2/A3/950定位，本卡保留draft、platforms为空。没有执行历史软件、训练、加载dump或测量性能。

## 特性演进按阶段保留

| Adapter段 | 说明的能力与范围 |
| --- | --- |
| 2.0.2 | PyTorch1.5为主，训练精度定界工具、710在线推理、Ubuntu18.04.5/openEuler20.03；列YOLOv3/v4、DB、RFCN、CRNN、原文Densenset161/191七个训练模型名，没有输入/权重/精度指标，不能视为可复现模型配方 |
| 2.0.3 | 引入PyTorch1.8.1，当期仅ResNet50及DDP；Python3.8、IR级溢出提示、UOS ARM；26个模型名单本身不构成对1.8.1全覆盖或性能基线 |
| 2.0.4 | 1.5的IR↔TBE精度映射、NPU dump到GPU比较、E2E Profiling；1.8.1加入原生AMP/Profiling与Python3.9，增加Ubuntu20.04双架构/Euler2.10 ARM，仍提当期1.8.1只支持ResNet50 |
| 3.0.RC1 | 将1.8.1适配代码分离为torch_npu插件，支持AOE自动调优、扩展API；“功能基本保持一致”不等于全部API参数/数值/性能相同 |
| 3.0.RC2 | 进一步解耦、优化单算子下发和集合通信、补充API，无测量数据 |
| 3.0.RC3（仅中文） | 1.8.1精度CPU对比/自定义算子Profiling，1.11模型训练、Apex、DDP/E2E Profiling |
| 3.0.0（仅中文） | 1.8.1/1.11支持NPU Tensor直接序列化save/load与dump/溢出优化，1.11仍beta并建议优先1.8.1，这是当期建议 |
| 5.0.RC1（仅中文） | 1.8.1/1.11的设备内存分配优化、FX IR/代码生成、npu_fused_adam等融合优化器；未给当前后端/融合参数/产品合同 |

## 旧已知问题不变成当前全局规则

各段反复列FP16 inf/nan输入输出不支持、4D以上format不能降维、同训练任务各device执行图需相同、仅1/2/4/8P粒度、通信类型仅INT8/INT32/FP16/FP32，以及当期Apex主要Python实现、不支持其自定义CUDA Kernel优化。这些是上述旧Adapter段的声明，不解释成950/BF16训练、所有现代HCCL卡数或当前Apex/融合优化器的限制，也不以旧FP16文字推断现代溢出检测机制。

兼容性列旧CentOS7.6、Ubuntu18.04及后来20.04、BC-Linux7.6、Debian9.9/10、openEuler20.03，9000系列另列EulerOS2.8/2.10、KylinV10/UOS等。原文部分写Ubuntu“2.04”，保持其拼写不擅自补为有效发行版；新增特性明确20.04的地方单独使用。无当前驱动/CANN/Python完整矩阵，不拿旧OS列表建立新部署推荐。

中文多出的阶段和英文未覆盖分开；“不涉及/N/A”的修复/变更栏目不证明无bug。完整版本证据仍见[软件栈身份](../../../concepts/frameworks/ascend_software_stack_baselines.md)。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/docs/RELEASENOTE_zh/RELEASENOTE.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/docs/RELEASENOTE_en/RELEASENOTE.md)（constraint）

## 发布快照的导入期拦截链

上文各节是历史 Adapter 发布说明的适用边界；本节以发布快照 f3ecfe4 源码记录该 pin 在 import torch_npu 期发生的检查、拦截与方法注入，与上文历史文档互不推导。主线 ac0e1564 固定提交内 `utils/npu_intercept.py`、`utils/unsupport_api.py`、`utils/tensor_methods.py`、`utils/dtensor.py` 四个文件不存在（find 清单比对），`_add_intercept_methods`、`unsupported_Tensor_api`、`_NPUTensortypeCache`、`_register_ops_under_dtensor_rules` 全树 rg 零命中，报错文本 "is not supported in npu" 在主线 torch_npu 内零命中——整条拦截链 release-only；`_cann_package_check` 是例外（见下表第一行的版本边界）。不能据此宣称主线已移除全部同类拦截，主线等价行为未逐主题核对，本卡不作断言。

| 实际门槛 | 动作 | 失败/版本边界 |
| --- | --- | --- |
| import torch_npu（release `torch_npu/__init__.py:101`，模块级） | `_cann_package_check()`（npu_intercept.py:25-70）：检查 ASCEND_HOME_PATH 存在性、ASCEND_OPP_PATH 已设置且存在、`<home>/runtime` 与 `<home>/compiler` 子目录存在；CANN 版本命中映射表（6.0.RC1–6.3.RC2 ↔ torch 1.8.1–2.0.0.rc1）时核对 torch_npu.__version__ 是否在对应清单 | 每项失败 raise Exception（带 pta_error NOT_FOUND 与 "source set_env.sh" 提示）；版本不匹配或未设 ASCEND_HOME_PATH 仅 print Warning 不中断。主线同函数移至 `_init/registry/registry_manager.py:19` 并由 `_register_npu_backend()`（:82）调用，映射表内容两版相同——此项非 release-only，只是位置不同 |
| import torch_npu 的 `_apply_class_patches()`（:169-188，release `__init__.py`） | `_add_intercept_methods()`（:176→npu_intercept.py:102-104）按 unsupport_api 名单逐项 setattr 包装：`torch.nn.Module.share_memory` 与 `torch.jit.ScriptModule` 的 add_module/bfloat16/register_buffer/register_parameter/register_module（unsupport_api.py:11-17） | 触发条件分两类：Tensor 检查 `_is_tensor_npu_supported`（首参是 NPU tensor 才抛）因 `unsupported_Tensor_api` 为空 dict（:8-9）当前不生效；Module 检查 `_is_module_parameters_supported`（首个带 `_modules` 的 nn.Module 参数的任一 named_parameter 在 npu 上才抛）。命中即 RuntimeError "<func> is not supported in npu."。share_memory 是 Module 方法，与 Tensor.share_memory_/Storage 侧留空契约（见[发布快照运行工具](torch_npu_release_native_runtime_contracts.md)）是不同对象，不互相推导 |
| 同一 `_apply_class_patches()`（:174） | `_add_tensor_methods()`（tensor_methods.py:85-88）：先存 `torch.Tensor.type_raw = torch.Tensor.type`，再把 `Tensor.type` 换成 `_npu_type`——dtype 为 None 直接走原 type；字符串或类命中 `_NPUTensortypeCache`（torch_npu.npu.*Tensor 与 torch.*Tensor 双键映射 10 种 npu 张量类型类，:22-68）时执行 `self.to(dtype, device='npu')`；未命中回退 type_raw。另绑 `Tensor.__reduce_ex__ = storage._reduce_ex`（storage.py:50 起） | 旧式 `Tensor.type("torch.FloatTensor")` 在发布版被重定向到 npu 设备，不再是纯元信息查询；非命中分支保持原语义。文件内 `_npu`/`_is_npu`（:13-19，直通 `torch_npu._C.npu/is_npu`）在该固定树内未见 Python 侧挂接或消费点（全树 rg），不推断其历史用途 |
| import torch_npu 模块级尾段（:301） | `_register_ops_under_dtensor_rules()`（dtensor.py:15-50）：为 DTensor 注册传播规则——pointwise：aten.isclose/isfinite 与 npu.fast_gelu/npu_fast_gelu/npu_layer_norm_eval/npu_fast_gelu_backward；bmm：npu_bmmV2；view：npu_transpose 的 dim_maps 与 register_op_strategy_map | 只影响 `torch.distributed.tensor` 下的策略推导，不等价于这些算子在 eager 已可用；`_npu_type` 与 DTensor 规则都不做数值或性能承诺 |

上述全部为发布快照源码静态直读；报错文本与 Warning 输出未实际触发验证。

## 发布快照来源

- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/utils/npu_intercept.py)（primary，全文 1–104）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/utils/unsupport_api.py)（primary，全文 1–18）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/utils/tensor_methods.py)（primary，全文 1–88）
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/utils/dtensor.py)（primary，全文 1–50）
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/__init__.py)（implementation，70–120、160–200、285–305）
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/utils/__init__.py)（implementation，全文 1–31）
- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/utils/storage.py)（implementation，50–64）
- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_init/registry/registry_manager.py)（implementation，1–95）
