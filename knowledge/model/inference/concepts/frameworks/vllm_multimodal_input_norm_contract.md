---
type: Concept
title: vLLM 多模态输入归一化（Multimodal Input Norm）：参数工厂与后端分派
description: 解释 FusedMMInputNorm 的 rescale/mean/std 折叠、processor 配置回退、容差恒等判断、视觉 dtype 转换及 CUDA/XPU/OOT 分派，区分框架数学合同与具体后端执行和性能证据。 Ascend补丁将派生weight/bias设为nonpersistent buffer，保持设备迁移并区分checkpoint参数。
aliases:
- Multimodal Input Norm
- mm_input_norm
- build_mm_input_norm
- FusedMMInputNorm
- NormParams
- IdentityInputNorm
- _load_norm_params
- fused_mm_input_norm_triton
- fused_mm_input_norm
- 多模态输入归一化
tags:
- task.implementation
- task.debugging
- topic.multimodal
- topic.precision
- topic.architecture
status: stable
sources:
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/model_executor/layers/fusion/mm_input_norm.py
  role: primary
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/model_executor/custom_op.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/transformers_utils/processor.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/worker/patch_mm_input_norm.py
  role: primary
created_at: '2026-10-31T20:30:25Z'
updated_at: '2026-11-03T05:22:33Z'
platforms:
- agnostic
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM 多模态输入归一化（Multimodal Input Norm）：参数工厂与后端分派

## 概念范围与 Agent 用途

FusedMMInputNorm 把图像 rescale 和按通道 mean/std 归一化合成仿射变换，并通过 factory 与 CustomOp 选择恒等、原生或特定后端实现。新模型把 CPU processor 的工作移到视觉设备时，需要保持参数来源、通道布局、归一化次数和视觉 dtype 一致。本卡的 agnostic 范围是框架数学、factory 和 fallback 接口；CUDA Triton、XPU 特化分别有自己的后端约束，不能由此宣称任意硬件都有同一个融合 kernel。

主来源为独立 Native vLLM 5df63a7203cdb9328d824a27b682e77c7b9928be 的 mm_input_norm.py 全文 361 行。custom_op.py 只阅读 102–211 行，transformers_utils/processor.py 只阅读 138–196 行。没有把这些共享文件的其余语义记为已闭合，也没有将它们与 Ascend Main 的配对 Native 544f182d9f0c9bfe8bd7645525951d5e3692a542 混作同一 ABI。

## 数学合同、通道与舍入边界

设 rescale_factor 为 s，通道 c 的 mean/std 为 m_c/t_c，预期变换是 `(x*s-m_c)/t_c`。实现折叠为 `w_c=s/t_c`、`b_c=-m_c/t_c`，计算 `x*w_c+b_c`。它们实数代数等价，浮点重结合、舍入和最终 dtype 转换不保证逐位相同。

输入接口为二维 `[patches,flattened_patch]`，flattened_patch 要能拆成 `[C,L]`，通道块连续，即 `[N,C,L]`。通道权重不能按 NHWC 或任意交错 layout 直接套用。channel 来自 image_mean/image_std 的长度，而不是总认为模型是 RGB；某些关闭 normalize 的默认分支使用 RGB 三通道，接入非 RGB 数据要先核对配置。

NormParams.is_identity 逐通道检查 s/std 以 rel_tol=1e-5、abs_tol=1e-8 接近 1，且 mean/std 以 abs_tol=1e-8 接近 0。这里允许近似恒等，不能改写成只接受精确 s=1、mean=0、std=1，也不能忽略很小但非零的归一化差异可能被 factory 跳过。

参数入口包含长度一致、非 None、Fused 构造的 channel 数和非零 rescale 断言；它没有为 std=0、NaN/Inf、任意异常配置建立完整安全校验。断言和 Python 数值运算不是通用用户输入验证协议，模型接入层仍需拒绝无效参数并记录原配置。

## processor 配置优先级与 flags

get_processor_config 依次检查 processor_config.json、preprocessor_config.json、tokenizer_config.json；返回第一个非空且包含 processor_class 的配置，否则返回空字典。文件存在、文件内容非空与确实具有 processor_class 是不同条件，不应把任意第一个 JSON 直接当作图像配置。

_load_norm_params 先从 get_processor_config 返回配置的 image_processor 子项取值；若 do_normalize、do_rescale、image_mean、image_std 四个键均未出现，则回退 model_config.hf_image_processor_config，再经 get_media_proc_cfg 取得有效媒体配置。该 helper 的完整内部处理不在已读范围，不能把当前优先级外推为所有 processor/remote-code 的统一行为。

只有 mean 与 std 同时存在才算 has_norm_params；两个 flags 的缺省值都取该判断。do_rescale=False 时直接采用 s=1，不去解析一个已禁用的 rescale_factor。do_rescale=True 时默认 1/255，并要求结果不是 None。do_normalize=False 时使用 mean=[0,0,0]、std=[1,1,1]；启用时读取对应参数。最后检查 mean/std 长度并转换为浮点列表。

因此“缺少 flag”不等于“统一关闭”，“配置中的 factor 无效”也不意味着关闭 rescale 时一定触发同样错误。适配 Agent 应保存命中的配置文件、image_processor 子项、回退来源、有效 flags 和最终参数，避免只抄默认 ImageNet mean/std。

## factory 与 IdentityInputNorm

build_mm_input_norm(model_config) 在没有 multimodal_config 或 mm_device_do_normalize 开关关闭时返回 IdentityInputNorm；开关打开后加载 NormParams，容差恒等也返回 Identity，否则创建通道数为 len(mean) 的 FusedMMInputNorm。先核对实际 factory 结果，再决定 CPU 与设备哪一侧负责数值转换。

IdentityInputNorm.input_dtype 为 None，forward(pixel_values,visual_dtype) 执行 `.to(visual_dtype,copy=False)`。它保留视觉 dtype cast，未必返回同一底层存储，不能替换为无条件原样返回的 nn.Identity 后就认为语义完全相同。FusedMMInputNorm.input_dtype=uint8 是输入提示，不是 forward 对所有其他 dtype 的完整拒绝校验。

Fused 构造时先建立 CPU FP32 mean/std，计算折叠后的 weight=rescale_factor/std 与 bias=-mean/std，再移到当前默认 device 并以 weight、bias 两个名字注册为 buffers。后续模块迁移遵循 buffer 语义；当前默认 device 与传入张量 device 不一致时，接入方仍需核对真实对象的设备状态。

## 原生 fallback 与数值域

forward_native 经 _unpack_2d 断言 rank=2，确认 flattened_patch 能被 channel 整除，再 view 成 `[N,C,L]`，按通道广播 x*w+b，恢复二维并转换到 visual_dtype。uint8 和常见 FP16/BF16/FP32 输入与 FP32 buffers 的运算使用预期的 FP32 路径；源码没有在这里无条件 x.float()，不能把“总是 FP32”扩大到任意 FP64 输入。

连续性和 view 的可行性仍需看实际输入；本卡不为所有非连续 tensor 补造自动 reshape/copy 合同。输出是否落到 visual_dtype、是否只归一化一次，应在视觉塔调用边界检查，不能仅靠结果 shape 或 factory 名称判断。

## CUDA Triton 与 XPU 的局部约束

forward_cuda 预分配连续输出；fused_mm_input_norm_triton 接受 `[N,C,L]`，要求输出形状完全相同且连续、w/b 元素数为 C，并对输入和 w/b 使用 contiguous。它不会对调用者输出偷偷创建替代 buffer，否则可能失去调用方期待的写回/别名语义。

kernel 要求 numel<2**31，BLOCK_SIZE=1024、num_warps=4。flat offset 的通道索引是 `(offs//L)%C`，masked load 后转 FP32，计算 x*w+b，再按输出 dtype store；末块 mask 不能省略。输入变连续可能引入复制，性能比较须计入该成本。

forward_xpu 在 uint8 输入时调用 xpu_fused_input_norm，其他 dtype 转入 forward_cuda。这里记录的是固定 Native 的分支，不是 Ascend NPU 的 kernel 合同。源码的 GB200 计时注释没有本次独立复测，不可作为跨设备选型、NPU 收益或端到端时延承诺。

## CustomOp：注册覆盖先于实例分派

FusedMMInputNorm 以 fused_mm_input_norm 注册，自身 enabled 返回 True。CustomOp.__new__ 先按 cls.__name__ 查 op_registry_oot；若有注册的 override，就创建该类。因此在 Ascend 插件环境中，仅阅读 Native 基类不能证明实际实例仍是该类，更不能直接认定它走 Triton 或某个专用 NPU kernel。

无覆盖时，CustomOp 初始化按 current_platform 选择实现：ROCm→forward_hip（默认委托 CUDA）、CPU→forward_native、TPU→forward_native、XPU→forward_xpu、OOT→forward_oot、其他→forward_cuda。基类 forward_oot 回退原生实现。该选择基于构造时的平台状态，不是每次 forward 都按输入张量 device 动态选择。

接入 Agent 需确认 override 是否注册、实际实例类、绑定的 forward、w/b buffers 和输入 device。不能把“OOT 回退可用”写成“融合 NPU 算子已实现”，也不能把 enabled=True 当作跳过所有 factory 条件或已经通过设备精度验证。

## 与模型预处理配合的检查信号

在 [Qwen3.5 设备预处理](../../guides/integration/vllm_ascend_qwen35_device_preprocess_contract.md) 中，外层完成 norm 后把 visual.input_norm 置为 IdentityInputNorm，以保留 cast 并避免特定调用链重复变换。该模型的 marker 另有作用域，不能由本概念推导任意 eager 输入自动幂等。另见 [多模态配置与 OOT 算子诊断](../../runbooks/runtime/mm_bringup_config_scan_and_oot_op_rank_contract.md)，用于定位嵌套配置与实际覆写对象；本卡不复制其故障处置链。

最小验证应覆盖配置命中/回退、四键缺失、flags 独立开关、精确/近似恒等、非三通道参数、无效 std/factor、uint8 与浮点输入、视觉 dtype、不同 N/C/L、末块和 numel 边界。逐通道手算 affine 作为 reference，再比较 CPU fallback 与实际后端；另外记录非连续输入/输出的接受或拒绝、真实 CustomOp override 与归一化次数。

回退时同时恢复 processor 的数值处理和设备 factory 选择，避免两边都做或两边都跳过。数值误差、吞吐和传输收益应在固定媒体、模型、软件、硬件、并发和 dtype 条件下各自测量。以上均为验证方法；本次仅作固定源码数据阅读，未导入上游模块、运行测试/模型、编译、执行 Triton/XPU/NPU 或进行性能实验，未填写 verified 事件。


## Ascend补丁的buffer持久性不改变数学

另按Ascend Main ceac1a2 的 patch_mm_input_norm.py27原始行整文件AST投影核对：包装FusedMMInputNorm.__init__，先运行原构造，再将同名weight/bias重新register_buffer(persistent=False)。_ascend_nonpersistent_norm标记用于避免重复包装。它保留buffer的设备迁移语义，但从state_dict持久项移除，避免将由processor配置导出的归一化量当checkpoint待加载参数。

这项Ascend增量不改变上文独立Native的affine数学、factory与backend范围；也不自动刷新已经构造的实例，不证明旧/新Native ABI已匹配。适配时检查实际实例buffers、state_dict键、processor重建参数和Native loader missing/unexpected keys，再验证归一化恰执行一次。此次没有应用补丁或运行权重加载。
