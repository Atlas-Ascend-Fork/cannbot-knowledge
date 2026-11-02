---
type: Guide
title: "最近邻 Resize：先固定坐标规则，再按原 dtype 搬移数值"
description: "将最近邻坐标选择与数值搬移分开；区分 nearest、nearest-exact 和原任务分支，用同输入 CPU 索引真值检验 Ascend C 实现。"
aliases: ["nearest resize coordinate gather"]
tags: [task.implementation, topic.precision]
status: draft
sources:
  - resource: https://gitcode.com/sijiaali/ascendc-kernelgen-data/blob/167feb7024500cd594de63497972560ea721070c/npu_benchmark/level3/20_resize_nearest.py
    role: primary
  - resource: https://github.com/pytorch/pytorch/blob/449b1768410104d3ed79d3bcfe4ba1d65c7f22c0/aten/src/ATen/native/UpSample.h
    role: implementation
created_at: "2026-10-22T03:26:49Z"
updated_at: "2026-10-22T03:26:49Z"
platforms: ["950"]
---

# 最近邻 Resize：先固定坐标规则，再按原 dtype 搬移数值

## 经验与适用范围

为 Ascend950 生成 NCHW 最近邻重采样实现时，先将“选哪个源元素”与“如何搬移元素”分开。最近邻不是线性插值；不需要把选出的原生 FP16/BF16/FP32 数值重新加权。高精度 CPU 诊断可以用于坐标计算，但输入仍应是实际生成的原 dtype 值，不能重新生成另一组 FP64 随机输入。

## 事实与依据

1. 原任务 `Model.forward`：`half_pixel_centers` 为真时调用 `nearest-exact`；否则在 `align_corners=False` 时调用 `nearest`；最后一支显式计算角点对齐索引。这三个分支不能互换。原文件 SHA256 为 `62740e387c82b3397548fa6916913a21f8a2d89375890c54fdbdabb70fbdf478`。
2. PyTorch 固定源码 `nearest_neighbor_compute_source_index`：普通 nearest 使用 `floorf(dst_index * scale)` 并限制到 `input_size-1`。
3. 同一头文件 `nearest_neighbor_exact_compute_source_index`：exact 使用 `floorf((dst_index+0.5)*scale)`。不能把它当作普通 nearest 的精度修复。
4. `nearest_idx` 对输出尺寸等于输入和两倍输入分别保留复制、右移快速路径；其他尺寸用 FP32 scale。以上是该固定 PyTorch 实现的事实，不能直接声称所有 CANN kernel 都采用相同算术顺序。

## 可执行配方

先冻结输入形状、目标尺寸、两项布尔属性和输出 dtype；按原任务实际分支建立独立 CPU 索引表。将实际原生输入按该表 gather，保留最终原生输出类型。Ascend C 实现按 N、C、输出空间分片，先计算对应输入偏移再搬移元素；具体 DMA、对齐及尾块策略需另读目标版本 API，不从此卡推出合法的搬运重载。

逐例比较完整输出，并加入能区分相邻坐标的输入。出现错误时先比索引表，再检查数据偏移、尾块覆盖和 dtype 位型；不能因为数值“接近”便忽略选中了相邻像素。理想实数/FP64 坐标与某个 FP32 reference 在整数边界可能不同，必须分别保留，不能暗换精度 reference。

## 已有观测与边界

原任务的50例中两项布尔属性均为 False；其已复核经验只覆盖普通 nearest。该集合下同输入独立 CPU 索引真值和实际 NPU 完整输出已有通过记录。其他两个源码分支、任意新形状和新的 DSO 均需独立验证；本卡没有新增设备实验，也不转授历史倍率、基础性能资格或带宽利用率。

## 生产与消费谱系

经验由原任务生成及完整输出复核产生，本次经 a5ops-knowledge-ingest 与 a5ops-knowledge-dedup 整理，回到上述原任务与 PyTorch 函数核对。这里只提供算法与辨别方法，未提供历史候选源码。新 BLACK_BOX 消费仍须完成 Query、全文 Read、独立生成以及新 P/F；卡片存在不证明已消费。

## 相关卡片

- [nearest 采样在半整数判定前保留仿射坐标残差](../runbooks/precision/grid_sample_nearest_affine_residual_before_rne.md)——同一坐标判定的浮点机制：提前舍到中点会选错邻点，先定坐标规则才有意义。
