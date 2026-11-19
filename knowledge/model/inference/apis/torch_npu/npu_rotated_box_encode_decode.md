---
type: API
title: npu_rotated_box_encode/npu_rotated_box_decode：旋转检测框编解码对
description: 记录两个无文档页入口的注册面与host合同（weight强制CPU FP32后以属性下发）、文档模板三处缺陷、ONNX导出绑定与FP32/FP16基线用例边界。
tags:
- task.lookup
- topic.precision
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/RotatedBoxEncodeKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/RotatedBoxDecodeKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/RotatedBoxEncodeKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/RotatedBoxDecodeKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: header
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: header
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/codegen/templates/_op_plugin_docs.py
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/codegen/templates/_op_plugin_docs.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_base_ops/test_rotated_box.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_base_ops/test_rotated_box.py
  role: example
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/onnx/wrapper_onnx_ops.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/onnx/wrapper_onnx_ops.py
  role: implementation
created_at: '2026-11-12T08:30:08Z'
updated_at: '2026-11-14T01:59:28Z'
platforms: []
---

# npu_rotated_box_encode/npu_rotated_box_decode：旋转检测框编解码对

## 版本与范围

本卡覆盖 OpPlugin 两固定 pin（主线 d84e9b1d6a558e5f27973cd4329f62968e46fdda、发布 dedc316708372c9a8bfde4527abd2a94b74840f5）中旋转检测框的 encode/decode 注册对：两份 aclops 包装全文（33/34 行逐字读毕，发布侧经全文件 diff 与空白归一复验）、yaml 登记、codegen 文档模板与基线用例。两入口在两 pin 的 docs/zh、docs/en 全树检索均无页面，deprecated.yaml、derivatives.yaml、`op_plugin/python/meta/_meta_registrations.py` 亦均零命中（负向核实即上述全树检索）；canonical 中 `npu_rotated_box` 前缀经 rg 全树零命中。相邻覆盖只链接不重复：轴对齐的 bounding_box encode/decode 及分配链见[旧检测框编码与分配](legacy_box_encoding_and_assignment.md)，同族旋转 IoU/重叠面积见[旧IoU家族](legacy_iou_family.md)，npu_nms_rotated 见[旧NMS](legacy_nms.md)，contrib Python 层 bbox coder 见[contrib BBox编解码](contrib_bbox_coders.md)。全部为静态源码与官方用例审阅，未执行任何上游或设备测试；本卡不归属任何模型，不承诺整模型训练或精度收益。

## 接口与注册面

```text
npu_rotated_box_encode(Tensor self, Tensor gt_bboxes, Tensor weight) -> Tensor
npu_rotated_box_decode(Tensor self, Tensor deltas, Tensor weight) -> Tensor
```

- yaml 登记（主线 6864–6868、发布 6664–6668）：两 schema 均仅 `acl_op: all_version`——无 op_api 路径、无 exposed 标注；对照相邻的 npu_rotated_iou/npu_rotated_overlaps 均带 `exposed: all_version` 且有文档页，本对两者皆无。
- Python 可调用面不在 yaml 标签内：TorchNPU 两固定 pin（ac0e1564…/f3ecfe4a…）的 `torch_npu/onnx/wrapper_onnx_ops.py` 手工注册 `torch_npu.npu_rotated_box_encode/decode = _wrapper_*`，包装为只定义 forward 与 symbolic 的 `torch.autograd.Function`（forward 直通 `torch.ops.npu.npu_rotated_box_*`）；两 pin 的 test_public_bindings.py 均列出这两个 `torch_npu.*` 名字（绑定存在性证据，生成机制未审阅）。torchair 两固定 pin 对本对无显式同名 converter/引用；名字扫描不排除通用回退或自定义图路由，不据此断言全部图模式行为缺席。
- ONNX 导出口子：symbolic 分别产出 `npu::NPURotatedBoxEncode(self, gt_bboxes, weight)` 与 `npu::NPURotatedBoxDecode(self, deltas, weight)`——在导出图里 weight 是普通输入节点，与其在 host 侧被吸收为属性的路径不同；converter 侧对这些私有域算子的支持不在本卡范围。

## 实际门槛与动作（host 实检）

| 事项 | 事实（encode 22–32 / decode 23–33，两 pin 同构） |
| --- | --- |
| 唯一 TORCH_CHECK | weight 转 CPU FP32 后 `data_ptr<float>()` 非空；encode 报错文案 `weight_cpu is null`、decode 报错文案 `weight_ptr is nullptr.`（均 VALUE 类）——两入口文案不一致属源码原文 |
| weight 下发路径 | `weight.to(at::Device(at::kCPU), at::kFloat)` 强制搬 CPU 并转 FP32，随后以 `ArrayRef<float>` 形式作为单次 OpCommand 的 `weight` **属性**下发；weight 不是设备输入张量。FP16/NPU 上的 weight 也被 host 吸收（官方用例即传 `.npu()` FP16 张量），其原 dtype 不参与设备合同 |
| 其余输入 | self、gt_bboxes/deltas 直传设备输入；**本地包装**未显式检查它们的 rank、shape、dtype 与相互一致性——apply_tensor 分配路径与 OpCommand 下发/框架层校验不在已读来源内，不能断言全部 host/框架校验缺席 |
| 输出分配 | `OpPreparation::apply_tensor(self)` 沿用 self 的 sizes/options 分配同形输出；encode/decode 输出均与 self（锚框）同形同 dtype |
| 动作 | 单次旧 ACE `OpCommand("RotatedBoxEncode"/"RotatedBoxDecode")`：`.Input(self).Input(gt_bboxes|deltas).Output(result).Attr("weight", weight_list).Run()`；设备侧 RotatedBoxEncode/RotatedBoxDecode 语义不在本仓来源 |

## 文档模板与基线用例

- 文档模板（codegen/templates/_op_plugin_docs.py，两 pin 相同块）：anchor 为 (B,5,N) 3D 张量，5 值标注「x0」「x1」「y0」「y1」「angle」；gt_bboxes/deltas 同 (B,5,N)、float32(float16)；weight 标注「Tensor，默认值为[1.0, 1.0, 1.0, 1.0, 1.0]」的浮点列表。模板 FP16 示例输出与基线用例期望值逐值一致。
- 缺陷一：decode 的功能描述写作「旋转标注框编码」，与 encode 相同（复制残留）；方向只能由参数名（gt_bboxes vs deltas）与 ACE 命令名区分，不能按描述文字判断。
- 缺陷二：weight 的「默认值为[1.0×5]」只是文档口径的典型取值；schema 三参数均必选、无任何缺省，不能读成可选参数。
- 缺陷三：5 值顺序标注为 x0,x1,y0,y1——与同族 npu_rotated_iou 的 xywht/xyxyt 双约定并存，本层源码不实现坐标重排，真实坐标顺序与编码公式未验证；轴对齐 bounding_box 卡同记 (x0,x1,y0,y1) 与 (x0,y0,x1,y1) 混用，本卡同样不拼出已验证公式。
- 基线用例（test_base_ops/test_rotated_box.py，两 pin 字节相同）：encode/decode 各 FP32、FP16 两条；输入均 (1,5,1)，weight 为 5 元素 ones；`assertRtolEqual` 对照固定期望输出；无 skip 装饰、无 SupportedDevices 门。覆盖边界：仅 B=1、N=1、5 通道、单位 weight；无反向用例、无 batch/框数大于 1 的用例、无非单位 weight 用例，不外推。

## 失效与版本边界

- 两 pin 行为一致：yaml 登记原文逐字相同；两 cpp 全文件 raw diff 后空白归一（去除全部空白字符）字符流完全相等（发布仅 4 空格缩进与签名/链式调用换行重排）；文档模板目标块 diff 相同；用例字节相同。
- 注册面无 derivatives 接线、无 deprecated.yaml 登记、无 Meta 注册，包装层 Function 亦未定义 backward——两层均无登记的反向路径，这是静态事实；运行时反向行为与设备内核能力未验证，不据此断言「永不支持训练」。
- 「计划废弃、底层不维护」结论只属于有文档页的 npu_rotated_iou/npu_rotated_overlaps（见旧IoU家族卡）；本对无文档页，不继承该结论。
- 设备侧 RotatedBoxEncode/RotatedBoxDecode 的坐标编码公式、dtype 支持矩阵、非法 shape 行为不在本仓来源；ONNX symbolic 只证明导出口子存在。
- apply_tensor 分配路径与 OpCommand 下发链不在已读来源内；本卡所有「未显式检查」的缺席结论只覆盖本地包装函数体，不断言框架/SDK 层校验缺席。
- 静态口径：未运行任何用例；无模型归属。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/RotatedBoxEncodeKernelNpu.cpp)（primary，1–33 全文逐字阅读）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/RotatedBoxDecodeKernelNpu.cpp)（primary，1–34 全文逐字阅读）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/RotatedBoxEncodeKernelNpu.cpp)（primary，42 行发布对应文件经全文件 raw diff 与空白归一等值复验，仅缩进/换行重排，无独立逐行读）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/RotatedBoxDecodeKernelNpu.cpp)（primary，35 行发布对应文件同上复验）
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（header，6864–6868 两 schema 登记定向读）
- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（header，6664–6668 同两 schema 定向读）
- [固定来源 7](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/codegen/templates/_op_plugin_docs.py)（primary，3650–3701 encode/decode 两个文档模板块定向读）
- [固定来源 8](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/codegen/templates/_op_plugin_docs.py)（implementation，3534–3585 对应块与主线 diff 相同复验）
- [固定来源 9](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_base_ops/test_rotated_box.py)（example，1–52 全文逐字阅读）
- [固定来源 10](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_base_ops/test_rotated_box.py)（example，与主线字节相同（sha256 一致），主线全文读覆盖发布字节）
- [固定来源 11](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/onnx/wrapper_onnx_ops.py)（implementation，368–382/455–505/1115–1180/1320–1336 绑定与 ONNX 包装定向读）
- [固定来源 12](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/onnx/wrapper_onnx_ops.py)（implementation，对应区段与主线 diff 相同复验；test_public_bindings.py 四名均在两 pin 列表中，绑定存在性证据）
