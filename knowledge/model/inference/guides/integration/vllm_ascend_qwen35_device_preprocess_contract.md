---
type: Guide
title: vLLM Ascend Qwen3.5 设备预处理：raw uint8、patch 顺序与归一化标记
description: 适配 Qwen3.5 Dense/MoE 的视觉输入，区分 CPU 回退和 raw uint8 路径、smart_resize 网格与设备 resize/patchify，核对 eager、DP 和 encoder graph 的切分单位及防止重复归一化的 marker 边界。
aliases:
- AscendQwen2VLImageProcessor
- _AscendVLPreprocessMixin
- _resize_and_patchify
- _all_uint8
- _DEVICE_PREPROCESS_DONE
- Qwen3.5设备预处理
tags:
- task.implementation
- task.debugging
- topic.multimodal
- topic.model_adaptation
- topic.precision
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/qwen3_5_vl.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/models/test_qwen3_5_vl_preprocess.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/__init__.py
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/support_matrix/supported_models.md
  role: constraint
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/model_executor/models/qwen3_vl.py
  role: primary
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/worker/encoder_cudagraph.py
  role: implementation
created_at: '2026-10-31T20:30:25Z'
updated_at: '2026-10-31T20:30:25Z'
platforms:
- a2
- a3
- '950'
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend Qwen3.5 设备预处理：raw uint8、patch 顺序与归一化标记

## 接入任务、模型与版本边界

Qwen3.5 将图像 resize、patchify 和归一化部分移到视觉设备时，CPU 字段切分、eager 入口、DP 重打包与 encoder graph 选择器必须共享同一个“数据处在哪一阶段”的合同。本卡描述 Main ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2 的 qwen3_5_vl.py：Dense 和 MoE 包装都组合 Native 类与 _AscendVLPreprocessMixin。注册存在不证明任意 Native、Transformers 或 checkpoint 自动兼容。

公开支持表中的 Qwen3.5 VL 行为 A2、A3、950 DT 提供模型范围；实际视觉 offload、图桶与每种变体仍需运行证据。310P 表中存在 Qwen3.5 Dense/文本支持，不能把 BF16 列的叉号解释为“310P 不支持 Qwen3.5 图像”，也不能反向据此声称本 raw pipeline 已在 310P 验收。Scope 只声明 vllm，不为未证明的并行模式或模型特征补值。

独立 Native 5df63a7203cdb9328d824a27b682e77c7b9928be 的 qwen3_vl.py 和 encoder_cudagraph.py 仅用于注明范围的接口对照；Main 配对 Native 544f182d9f0c9bfe8bd7645525951d5e3692a542 与它不同。部署媒体参数复用 [Qwen3-VL 输入与显存指南](../models/vllm_ascend_qwen3_vl_input_and_memory.md)，通用数学和 factory 复用 [多模态输入归一化契约](../../concepts/frameworks/vllm_multimodal_input_norm_contract.md)。

## raw uint8 的实际准入条件

AscendQwen2VLImageProcessor 的 _preprocess 只有在 do_resize=True、do_rescale=False、do_normalize=False、resample 为 BICUBIC，且 _all_uint8(images) 为真时采用 raw 路径。_all_uint8 只接受 uint8 的 Torch Tensor 或 NumPy array；浮点图片即使值域在 0..255，也不因此成为 uint8。

只要一项不满足，就完整调用 stock Qwen2VLImageProcessor 的 CPU 路径。自定义 processor 的安装本身是无条件的；实际是否卸载到设备由这组有效 flags 和输入 dtype 决定，不能只观察引擎的一个开关。输出中的 image_hw 才是该批数据仍为 raw 图像的重要结构标志。

raw 路径仍在 CPU 调用 smart_resize 计算目标尺寸和 image_grid_thw，保持 token/grid 预算与原 processor 一致；它不在 CPU 完成图像 resize、归一化和时间维复制。每图仅展平原始 CHW uint8，发出 image_hw=[H,W]，grid 为 [1,gh,gw]。_preprocess 自身没有为空列表拼接添加通用保护，不可将设备 helper 的空输出规则外推到所有上游空输入。

## 两种切分单位：原图像素和视觉 patches

存在 image_hw 时，ProcessingInfo 以每图 C*H*W 为 pixel_values flat size，把 image_hw 保留在 CPU；缺少 image_hw 时委托父类按常规 patch 规则处理。CPU 上记录的目标 grid 与原始 H/W 是不同坐标，不能拿目标 gh*gw 去切尚未 resize 的 raw 像素。

_AscendVLPreprocessMixin 初始化时建立 input_norm，保存通道数、patch_size、temporal_patch_size 和 merge_size；同时把 visual.input_norm 替换成 IdentityInputNorm。后者仍把输入转换到 visual_dtype，目的是避免 Native 视觉路径第二次归一化，而不是删除必要的 dtype cast。迁移时只把它换成 nn.Identity 可能改变后续线性层实际收到的 dtype。

解析入口区分 image_embeds 与 pixel_values，并保留可选 image_hw。预计算 embedding 路径转换到 visual dtype，按 grid.prod()/merge_size² 切分；它不再走原始图像 resize。字段名相同或总 numel 接近，不足以把这三种阶段的数据互换。

## 设备 resize 和精确 patch 顺序

_resize_and_patchify 先将整段 flat 像素搬到 visual.device（non_blocking=True）并转为 float，再按各图 C*H*W 切分；每图进行 bicubic、antialias resize，随后 clamp(0,255).round。non_blocking 参数不是已证明端到端 H2D 与计算重叠的性能结果。

设目标网格为 gh/gw、空间 merge 为 m、patch 为 p。resize 后 reshape 为 `[C,gh/m,m,p,gw/m,m,p]`，再 permute(1,4,2,5,0,3,6)，把 merge 分组、组内位置、通道和 patch 内坐标排列成 Native 视觉层预期的顺序。随后 unsqueeze/expand temporal_patch_size 次并 reshape 为 `[gh*gw,C*temporal_patch_size*p*p]`。这里无外层 batch，时间维展开后是八维中间表示，不能照搬带 batch 的九维版本。

设备 helper 对空选择返回形状 `(0,C*temporal_patch_size*p*p)` 的张量。原始 flat 长度、实际 resize 尺寸、grid、空间 merge 顺序及时间复制均应逐项对齐；只检查 patch 数或最终隐藏维无法发现通道/时间排列错误。

源码注释的 cosine 近似值和约 8 倍传输缩减是上游说明，本卡未复测，不作数值保证。raw 传输与 CPU patch 传输的字节比取决于原始/目标尺寸、dtype、通道和 temporal_patch_size；它不是恒定 8 倍，也不能直接推出 TTFT 或整模型吞吐收益。不同 resize 实现的舍入与插值仍需按实际依赖做精度对照。

## eager、DP 与 marker 的作用域

普通 _process_image_input 对 raw 分支执行设备 resize/patchify 再 input_norm；stock patch 分支也经过 input_norm。_run_visual 在 DP 场景调用 run_dp_sharded_mrope_vision_model、使用 rope_type="rope_3d"；其余调用 visual 后按 grid 切分。视频输入按既有 patches 做归一化，不借用 image_hw 的 raw 图像规则。

_DEVICE_PREPROCESS_DONE 对应字典键 _ascend_device_preprocess_done。select_encoder_cudagraph_items 在 raw 图像上先按原 C*H*W offset 选图，收集对应 grid/hw，再设备预处理并归一化一次，最后把 marker 置 True。indices 为空时跳过 resize 和 norm，返回 visual dtype/device 的零行 patches 和 marker。

对已是 stock image/video patches 的输入，选择器按 t*h*w 切分；只有 indices 非空、marker 尚未设置且设备归一化开关启用时才执行 norm，然后输出 marker=True。DP 重打包或嵌套 selector 因而能看见已处理状态；关闭相应开关时维持 stock 传递语义。

该 marker 保护的是选取/重打包链路。普通 eager _process_image_input 的 stock 分支仍直接调用 input_norm，不按 marker 自动跳过；不能把已选取、已归一化的 patches 随意送回 eager 入口，再宣称“全系统幂等”。接入 Agent 应记录每次调用前后的 raw/patch/embedding 阶段、image_hw 是否存在、marker、有效 flags 和 norm 次数。

## Native graph 接口与读到的边界

Native qwen3_vl.py 1646–1660 行的字段配置签名与当前两参数 override 对照；2189–2303 行的 stock selector 按 patch 数选择，没有 Main 的 raw image_hw 单位。若只继承 stock 切片而移走 CPU patchify，会在选择阶段就截断或混合原始图像。

Native encoder_cudagraph.py 358–402 行的 _select_items 在 gpu_sync_allowed 中调用模型 select_encoder_cudagraph_items，再提取 capture 轴字段并返回选择结果。这支持“选择器是 graph 数据准备边界”的结论，不闭合整个 graph manager、DP 分布式执行、捕获桶和重放生命周期；实际 Ascend graph 仍需对应版本和设备验证。

## 验证矩阵与回退

结构检查应覆盖 do_resize/do_rescale/do_normalize/resample/uint8 准入的每个反例，确认回退确实走 stock CPU，而不是产生半处理张量。分别测试不同原图尺寸、不同 target grid、多图子集、重复选择、空 indices、视频、预计算 embeddings、Dense/MoE、DP 与 graph/eager，并检查每次 flat size、选图次序、patch 顺序、visual dtype 和 marker。

数值验收需固定输入媒体、processor/依赖和模型权重，逐阶段比较 CPU reference、设备 resize 后值、归一化 patches、patch embedding 和完整视觉输出，再测模型任务精度。性能比较同时记录传输字节、H2D、预处理时间、TTFT 与总吞吐，不只引用缩减比例。出现偏差时保留各阶段数据与开关，回到配对版本支持的 stock 路径；关闭开关后还要确认有效 flags 与输出字段已真正恢复 CPU 合同。

## Evidence 与未执行项

qwen3_5_vl.py 全文 406 行与 test_qwen3_5_vl_preprocess.py 全文 501 行作为数据阅读。测试含 CPU stubs、_CountingNorm、选择器/空选择/开关路径，以及一个实际 Native ViT.forward 探针；后者在 patch embedding 前截停，没有覆盖真实层计算。源码中的参数化用例不是本次已运行结果，更不是 NPU 或端到端图执行证明。

注册表全文与支持表注明行提供架构/硬件上下文；Native 只覆盖上面标注的方法范围，其余共享文件语义保持后续阅读任务。本次没有导入 Torch/vLLM/Transformers，没有执行 UT、模型、分布式、图捕获、编译、NPU、精度或性能实验，未填写 verified 事件。
