---
type: Guide
title: TorchNPU旧接口迁移：废弃清单、形状接线与版本差异
description: 区分固定发布和主线的计划废弃列表，保留替代方向、别名与形状约束及清单错误。
tags:
- task.migration
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/scrap_API.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/scrap_API.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/scrap_API.md
  role: constraint
created_at: '2026-11-09T21:13:31Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
---

# TorchNPU旧接口迁移：废弃清单、形状接线与版本差异

## 固定版本及使用范围

依据OpPlugin发布dedc316708372c9a8bfde4527abd2a94b74840f5与主线d84e9b1d6a558e5f27973cd4329f62968e46fdda废弃列表。发布69条、主线中英文各46条，条数只是列表大小，不是接口覆盖、支持率或删除数量。这里讨论既有模型迁移，单接口产品、dtype、反向和模式按相应API核对，不从本指南平台声明推定列表中每个旧接口都在这些设备可运行。

“计划废弃”与已删除不同；有些条目明确底层不再维护、性能和精度不保证。一个条目从主线列表消失，也不证明废弃撤销或源码消失；不能自动把对应知识卡标成deprecated，卡片仍可正确记录旧契约。

## 发布版给出的迁移方向

| 旧入口 | 来源建议及迁移时要保留的语义 |
| --- | --- |
| copy_memory_、empty_with_format、one_ | Tensor.copy_、torch.empty、填充/ones_like方向；核对原地别名、设备、dtype及物理格式，普通empty不等于保证旧格式。 |
| npu_broadcast、npu_reshape、npu_min、npu_sort_v2、npu_dtype_cast | broadcast_to、reshape、min、sort、类型转换方向；核对广播/视图或复制、轴、排序索引与返回结构。文档的torch.to记法不作为可直接执行代码，Tensor.to(dtype=...)按实际调用消费。 |
| npu_conv2d/3d、npu_convolution、转置卷积族 | functional.conv2d/3d及conv_transpose2d/3d；维数选择、权重布局、padding/output_padding、groups及反向逐项保持。 |
| npu_apply_adam、npu_gru、npu_layer_norm_eval | Adam优化器、原生GRU、functional.layer_norm方向；不能把带out状态和额外训练中间量的低层API直接换成同名高层调用。 |
| npu_mish/npu_silu、contrib.module.Mish/SiLU | functional或nn对应激活；核对原地选项、数值模式和梯度。 |
| contrib.DCNv2、FusedColorJitter、LinearA8W8Quant | 分别指向ModulationDeformConv、torchvision.transforms.ColorJitter、LinearQuant；替换方向不等于参数、随机数、量化格式或权重检查点自动兼容。 |
| contrib.npu_fused_attention_with_layernorm | fusion_attention与LayerNorm组合；输入布局、mask、dropout、归一化域及反向接线仍需保持。 |

发布表将contrib.Swish指向ModulationDeformConv，激活与可变形卷积职责不符，本卡保留来源错误，**不将此行变成迁移配方**。原生GRU等名字也只表示方向，不越过公开限制。

## 两版本保留的组合与状态操作

npu_bmmV2的主线说明明确：先view/expand做1D扩展与batch广播，再bmm，最后view到目标形状；仅写bmm+view会漏掉批次广播和输出协议。npu_confusion_transpose应按原操作顺序组合view和permute，英文用“or”不能理解成任取一个便等价。

ExternalEvent.reset计划废弃，文档说明ExternalEvent.wait自动复位；这不是设备同步或跨流依赖全部完成的证明。npu_pad与npu_transpose建议functional.pad/permute；npu_slice表写torch.slice，但该名字不作为本卡可执行配方，切片轴、起点、长度和步长需按真实公开入口核对。npu_nms_rotated与contrib.BiLSTM只建议小算子拼接，没有给完整可替换的数值与反向实现。

## 不再维护的旧算子及新旧列表边界

两版都列出旧PTIoU/IoU/GIoU/DIoU/CIoU及contrib变体、rotated_iou/overlaps、bounding_box_encode/decode、grid_assign_positive、anchor_response_flags；同时列batch_nms、nms_v4、nms_with_mask、ps_roi_pooling。它们没有被“同族当前接口”自动替换，尤其box布局、转置、阈值、有效数量和梯度不同。

其他共同条目包括float_status分配/清零/读取、bert_apply_adam、indexing、one_hot、random_choice_with_mask、sign_bits_pack/unpack、softmax_cross_entropy_with_logits、yolo_boxes_encode、multi_head_attention、dropout_with_add_softmax与contrib.function.dropout_with_byte_mask。不要将“不维护”读成运行必错，也不要将保留源码读成仍获精度/性能承诺。

npu_fused_attention_score建议fusion_attention，仍需重建旧输出/中间量及mask等接线；npu_mla_prolog在两表保留计划废弃，不能因另有现代API文档便忽略该状态。主线另列contrib.module.npu_modules.DropoutWithByteMask，与function入口分别记录；发布含许多原生替代建议而主线不再列它们，不据列表删减推断恢复维护。

## 验证与导航

按原模型固定输入、随机状态、shape、dtype、布局和训练模式，分别检查返回结构、状态/别名、数值与梯度，再比较稳态性能及显存；旧名与新名相似不构成等价证明。仅文档静态审阅，未执行迁移、设备或性能实验。

- [框架及公开接口边界](../../../concepts/frameworks/torch_npu_framework_layers.md)
- [旧形状变换](../../../apis/torch_npu/legacy_shape_transforms.md)
- [旧Adam状态](../../../../training/apis/torch_npu/legacy_adam_updates.md)
- [旧视觉IoU](../../../apis/torch_npu/legacy_iou_family.md)
- [原生RNN限制](../../../../training/guides/torch_npu_native_recurrent_constraints.md)

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/scrap_API.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/scrap_API.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/scrap_API.md)（constraint）
