---
type: API
title: 批量非极大抑制（torch_npu.npu_batch_nms）
description: torch_npu.npu_batch_nms：对 batch 内各类别的候选框按分数和 IoU 阈值筛选，并限制保留框数量。 以 batch、类别为单位抑制冗余检测框，返回保留检测框、类别、得分及相应计数；数量上限和阈值仍按该版参数核对。
tags:
- task.lookup
- topic.model_serving
status: draft
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/%EF%BC%88beta%EF%BC%89torch_npu-npu_batch_nms.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
created_at: '2026-11-10T03:38:53Z'
updated_at: '2026-11-10T11:59:36Z'
platforms: []
aliases:
- torch_npu.npu_batch_nms
- Non-Maximum Suppression
---

# 批量非极大抑制：torch_npu.npu_batch_nms

## 用途与语义

对 batch 内各类别的候选框按分数和 IoU 阈值筛选，并限制保留框数量。

## 输入、输出与行为

以 batch、类别为单位抑制冗余检测框，返回保留检测框、类别、得分及相应计数；数量上限和阈值仍按该版参数核对。

## 文档签名

```text
torch_npu.npu_batch_nms(self, scores, score_threshold, iou_threshold, max_size_per_class, max_total_size, change_coordinate_frame=False, transpose_box=False) -> (Tensor, Tensor, Tensor, Tensor)
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

## 适用范围与约束

该文档只使用旧的 Atlas 训练/推理产品名称，尚未定位到本仓 A2/A3/950 等规范产品范围；保留 draft 与空平台。可在未定位 API 查询中读取定义，不能作为目标平台已支持的证据。

源表分组：Beta。

## 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

## Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/%EF%BC%88beta%EF%BC%89torch_npu-npu_batch_nms.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）
