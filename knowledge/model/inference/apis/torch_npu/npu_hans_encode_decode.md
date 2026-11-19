---
type: API
title: npu_hans_encode与npu_hans_decode：Host交换内存路径的PDF直方图无损压缩编解码
description: 保留pdf/mantissa/fixed/var缓冲区字节账、statistic/reshuff语义、压缩上界公式与A2/A3边界，衔接swapped memory特殊Tensor的六算子约束。
tags:
- task.lookup
- topic.memory
- topic.data_movement
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/codegen/templates/_op_plugin_docs.py
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: header
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_hans_compress.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-empty_with_swapped_memory.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-empty_with_swapped_memory.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/codegen/templates/_op_plugin_docs.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_hans_compress.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-empty_with_swapped_memory.md
  role: constraint
created_at: '2026-11-12T05:36:44Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# npu_hans_encode与npu_hans_decode：Host交换内存路径的PDF直方图无损压缩编解码

## 版本与范围

本卡依据 OpPlugin 主线候选 d84e9b1d6a558e5f27973cd4329f62968e46fdda 与发布 dedc316708372c9a8bfde4527abd2a94b74840f5：两算子的 codegen docstring 区块、yaml gen_opapi 登记与往返用例在两 pin 逐字相同（仅用例文件末尾换行差异）。OpPlugin 没有独立 API 文档页，接口说明以 codegen 注入 torch_npu 命名空间的 docstring 为准；实现为 gen_opapi 自动生成包装（encode exec 参数序 `aclnnHansEncode, input, pdf, statistic, reshuff, mantissa, fixed, var`；decode 直接绑定 `aclnnHansDecode`）。本文为静态审阅，未运行。

## 机制与调用

```python
pdf, mantissa, fixed, var = torch_npu.npu_hans_encode(
    input, statistic, reshuff, out=(pdf, mantissa, fixed, var))
recover = torch_npu.npu_hans_decode(mantissa, fixed, var, pdf, reshuff, out=recover)
```

- 无损压缩基于输入**指数位字节的概率密度分布（PDF）**：`mantissa` 保留每个元素的尾数字节，指数位字节按 PDF 统计编码拆为定长部分 `fixed` 与变长部分 `var`；`pdf` 是 `[1, 256]` INT32 直方图，每个元素值等于对应索引的字节值在 input 中的出现次数。
- `statistic=True` 重新统计 input 指数位 PDF 并覆盖传入 pdf；`False` 使用传入 pdf 压缩（可跨步复用历史分布）。
- `reshuff=True` 把多核压缩结果在 `fixed` 中连续化，此时 `var` 失效，且要求 `fixed` 自身不小于压缩上界；解码必须传相同的 `reshuff` 值，两端不一致的后果无来源说明。

## 缓冲区字节账（docstring 约束）

| 缓冲 | dtype/形状 | 字节约束 |
|--|--|--|
| `pdf` | INT32 `[1, 256]`（Device） | 固定 |
| `mantissa` | 同 input（Device，或 Host 映射内存） | `numel*es == input.numel()*(input.es-1)`，可精确计算 |
| `fixed` | 同 input（仅 Device） | ≥512 字节（压缩元信息下限）；`reshuff=True` 时须单独 ≥ 压缩上界 |
| `var` | 同 input（Device，或 Host 映射内存） | 与 fixed 合计 ≥ `input.numel() + input.numel()/64 + 8448*当前硬件Vector核数` |

- `input` 与解码 `out` 的元素数都必须是 64 的倍数且 ≥32768；dtype 支持 FP16/BF16/FP32。解码侧 mantissa 字节账按 `out` 同公式核对。
- docstring 仅允许 `mantissa/var` 可为 Device 侧 Tensor 或 **Host 侧内存经虚拟内存映射至 Device** 的存储；`fixed` 与 `pdf` 是 Device 侧 Tensor，编码 `input` 与解码 `out` 同为 Device 侧——这是与 swapped memory 特殊 Tensor 的衔接点。
- 压缩上界公式中的"当前硬件 Vector 核数"需按实际芯片取值，docstring 未给数值表。官方用例的 `mantissa_numel = numel*(es-1)` 是**字节**数，随后除以 `element_size()` 才得到 mantissa 的**元素**数（≈ `numel*(es-1)/es`，不是 `numel*(es-1)` 个元素）；`fixed/var` 各按 `numel` 个元素预分配。该分配是否满足上界取决于实际 Vector 核数，静态读码不能判定。另记一处来源内不一致：docstring 声明 pdf 形状为 `[1, 256]`（二维），被跳过的用例却以一维 `torch.zeros(256)` 预分配；不能据用例宣称一维 pdf 受支持。

## 支持范围与相邻链路

- docstring 支持表仅列 Atlas A2/A3 训练系列；未列 950，不能据 TorchNPU 整体支持 950 反向补入。
- [empty_with_swapped_memory](empty_with_swapped_memory.md) 申请的特殊 Tensor 当前仅允许六类算子消费（`aten::fill_`、`aten::zero_`、`aten::mul_`、`npu_apply_adam_w`、`npu_hans_encode`、`npu_hans_decode`），C++ 侧合同见[同名卡](cpp_swapped_memory.md)；hans 二元组是其中压缩/解压环节。
- 机制组合（设计推断，非来源流程）：六类允许算子只证明对 swapped memory 特殊 Tensor **允许哪些操作**，不构成官方编排流程；allocator 衔接（特殊 Tensor 的申请与消费约束）有来源覆盖。"优化器状态经 swapped memory 落 Host、`npu_apply_adam_w` 原地更新后 `npu_hans_encode` 压缩驻留、需要参与计算时 `npu_hans_decode` 还原"这一序列是本卡的设计推断，来源未提供该编排。实际节省取决于 Host 容量、往返带宽与 Vector 核数上界配置，来源未给测量。

## 失效边界

- 官方往返用例整体 `@unittest.skip("skip test_hans_compress now")`：无损性、往返正确性与上述字节账均无 CI 证据；本卡未运行。
- 压缩率、时延、与 `mul_`/`fill_` 的交互无来源数据，不做承诺；"无损"是 docstring 声明，未验证。
- "Host 侧内存通过虚拟内存映射至 Device"的具体映射与页对齐机制在 allocator/aclnn 侧，本层不可见；PDF 编码的熵编码类别等算法细节不在 docstring，不推测。
- 两 pin 无差异不等于后续版本稳定：gen_opapi 自动包装意味着 schema 变更会直接改变 Python 签名，升级时按 yaml 登记复核。
