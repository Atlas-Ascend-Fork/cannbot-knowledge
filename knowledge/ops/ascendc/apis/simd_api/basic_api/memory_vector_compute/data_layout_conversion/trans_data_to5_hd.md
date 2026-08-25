---
type: API
title: TransDataTo5HD
description: 将NCHW格式转换为NC1HWC0格式，也可用于二维矩阵数据块转置，单次repeat可处理512字节数据。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.data_movement.layout_transform]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/data_layout_conversion/TransDataTo5HD.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# TransDataTo5HD

数据格式转换接口，将数据转换为 5HD（NC1HWC0）格式。头文件 `basic_api/kernel_operator_vec_intf.h`。支持 950/a2/a3。

<!-- cannbot:related:start -->
## 相关

- [数据排布格式](../../../../../guides/technical_appendix/concepts_and_terms/neural_networks_and_operators/data_layout.md)（`explains`）：TransDataTo5HD 与《数据排布格式》的实质衔接是：TransDataTo5HD 将张量转为 NC1HWC0；布局转换/格式说明、TransData 与 C API AscTransto5hd共同确定源目格式和对应入口。
- [AscTransto5hd](../../../c_api/vector_compute/asc_transto5hd.md)（`related`）：两卡均执行 NCHW→NC1HWC0/5HD 转换；C 接口补充 512B repeat 和 stride 规则，基础 API 提供 LocalTensor 入口。
- [TransData](../../../adv_api/tensor_transform/trans_data.md)（`related`）：TransData 描述通用布局转换能力，TransDataTo5HD 是把输入专门转换到 5HD 的低层路径；选择 5HD 目标布局时后者落实前者的一种转换方向。
- [数据排布转换](data_layout_conversion.md)（`same_topic`）：TransDataTo5HD 与《数据排布转换》的实质衔接是：TransDataTo5HD 将张量转为 NC1HWC0；布局转换/格式说明、TransData 与 C API AscTransto5hd共同确定源目格式和对应入口。
<!-- cannbot:related:end -->
