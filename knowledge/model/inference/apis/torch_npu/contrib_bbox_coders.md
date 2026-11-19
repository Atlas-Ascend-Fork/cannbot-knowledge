---
type: API
title: contrib BBox编解码：坐标、归一化及YOLO步长
description: 分别记录三种格式转换和默认值，修正stride限制误植并保留dtype检查缺口。
tags:
- task.lookup
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-contrib/（beta）torch_npu-contrib-function-npu_bbox_coder_decode_xywh2xyxy.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-contrib/（beta）torch_npu-contrib-function-npu_bbox_coder_decode_xywh2xyxy.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-contrib/(beta)torch_npu-contrib-function-npu_bbox_coder_decode_xywh2xyxy.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-contrib/（beta）torch_npu-contrib-function-npu_bbox_coder_encode_xyxy2xywh.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-contrib/（beta）torch_npu-contrib-function-npu_bbox_coder_encode_xyxy2xywh.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-contrib/(beta)torch_npu-contrib-function-npu_bbox_coder_encode_xyxy2xywh.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-contrib/（beta）torch_npu-contrib-function-npu_bbox_coder_encode_yolo.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-contrib/（beta）torch_npu-contrib-function-npu_bbox_coder_encode_yolo.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-contrib/(beta)torch_npu-contrib-function-npu_bbox_coder_encode_yolo.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/contrib/function/bbox_coder.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/contrib/function/bbox_coder.py
  role: implementation
created_at: '2026-11-09T19:49:40Z'
updated_at: '2026-11-09T19:49:40Z'
platforms:
- a2
- a3
---

# contrib BBox编解码：坐标、归一化及YOLO步长

## 固定版本与产品

依据OpPlugin发布dedc316708372c9a8bfde4527abd2a94b74840f5中文页、主线d84e9b1d6a558e5f27973cd4329f62968e46fdda中英文页及各自实际收录范围。TorchNPU实现分别为发布f3ecfe4a7ef7395754da7ca2e35661a7132b519b与独立主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf，不把两个仓库main当已配套。

默认A2/A3只指页面所列训练系列；推理产品及其他入口的扩展另说明，旧Atlas不自动映射新型号。此批contrib页面没有950DT确认，不由底层算子或框架总览扩展。这里只做静态阅读，没有导入上游、加载模型、运行设备、反向或性能实验；stable不表示运行verified。


## 三个入口

| 入口 | 参数与结果 |
| --- | --- |
| npu_bbox_coder_decode_xywh2xyxy | bboxes,pred_bboxes,means=None,stds=None,max_shape=None,wh_ratio_clip=16/1000，返回(N,4)的tl_x/tl_y/br_x/br_y |
| npu_bbox_coder_encode_xyxy2xywh | bboxes,gt_bboxes,means=None,stds=None,is_normalized=False,normalized_scale=10000.，返回回归deltas |
| npu_bbox_coder_encode_yolo | bboxes,gt_bboxes,stride，返回YOLO式deltas |

文档源框与目标框通常(N,4)、FP16/FP32；两固定包装只显式检查首维相等及末维均4，没有完整二维、全shape和所有合法坐标校验。means默认四个0、stds默认四个1，decode须与编码一致；max_shape源码None后置[9999,9999]，文档原型直接该列表并称“不受限制”，不能解释成任意大图都无裁剪。wh_ratio_clip为宽高比裁剪配置。

encode_xyxy归一化True会同时乘normalized_scale恢复坐标，再调用npu_bounding_box_encode。YOLO需一维stride且长度与框数一致，底层performance_mode=False以避免文档所述高性能模式精度风险；源码注释不支持动态shape。decode注释支持动态shape但仍要求二维同dtype和两个max_shape数，不扩大全部编码入口。

## 文档和包装需一起消费

xyxy编码页误写“第三输入stride必须一维”，但该签名第三项是means；stride条款实际对应YOLO，不据错误移植句为means补一个Tensor条件。发布randint框和YOLO stride例的默认整型与文档浮点/torch.int不完全一致，主线为decode/xyxy例补了浮点转换。

_box_dtype_check/_stride_dtype_check比较的是Tensor对象是否在dtype列表，而非读取tensor.dtype；其意图转float/int不构成可靠的FP16保留、全部类型验证或零拷贝保证。输入合法域、坐标顺序与下游数值仍需按实际固定包验证，未运行编码/解码。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-contrib/（beta）torch_npu-contrib-function-npu_bbox_coder_decode_xywh2xyxy.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-contrib/（beta）torch_npu-contrib-function-npu_bbox_coder_decode_xywh2xyxy.md)（primary）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-contrib/(beta)torch_npu-contrib-function-npu_bbox_coder_decode_xywh2xyxy.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-contrib/（beta）torch_npu-contrib-function-npu_bbox_coder_encode_xyxy2xywh.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-contrib/（beta）torch_npu-contrib-function-npu_bbox_coder_encode_xyxy2xywh.md)（primary）
- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-contrib/(beta)torch_npu-contrib-function-npu_bbox_coder_encode_xyxy2xywh.md)（constraint）
- [固定来源 7](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-contrib/（beta）torch_npu-contrib-function-npu_bbox_coder_encode_yolo.md)（constraint）
- [固定来源 8](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-contrib/（beta）torch_npu-contrib-function-npu_bbox_coder_encode_yolo.md)（primary）
- [固定来源 9](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-contrib/(beta)torch_npu-contrib-function-npu_bbox_coder_encode_yolo.md)（constraint）
- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/contrib/function/bbox_coder.py)（implementation）
- [固定来源 11](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/contrib/function/bbox_coder.py)（implementation）
