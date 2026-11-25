---
{
  "type": "Runbook",
  "title": "torchtitan-npu QAT/MXFP8 导出 HF bf16 权重不保留量化行为（量化只活在 forward 计算图）",
  "description": "框架：torchtitan-npu（torchtitan NPU 插件仓）+ torchao_npu QAT（DeepSeek V4 / DSV4.1 Flash：MXFP8 真量化、moe.experts MXFP4 伪量化 + Block FP8，commit e483aee/7f9bc99）。",
  "tags": [
    "task.implementation",
    "topic.implementation.debugging"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:03Z",
  "updated_at": "2026-11-20T14:17:03Z",
  "platforms": []
}
---

# torchtitan-npu QAT/MXFP8 导出 HF bf16 权重不保留量化行为（量化只活在 forward 计算图）

## 适用场景

- 框架：torchtitan-npu（torchtitan NPU 插件仓）+ torchao_npu QAT（DeepSeek V4 / DSV4.1 Flash：MXFP8 真量化、moe.experts MXFP4 伪量化 + Block FP8，commit e483aee/7f9bc99）。
- 任务：判断"把 QAT 训练产出的 checkpoint 导出为 HF bf16 权重、再用 lm-eval 单机评测"能否反映量化模型精度。

## 触发与观测

- 结论原文（source 0 seq 82）："量化行为(尤其是激活量化)**只活在被 converter 改造过的 forward 计算图里,不在权重张量里**。导出 HF bf16 权重只会保存底层的高精度权重(`_data`),丢掉了:激活量化、MXFP8/Block-FP8 的动态权重量化行为、以及 MXFP4 的伪量化误差。用一个无量化算子的普通 HF modeling 加载这些权重跑推理,得到的是'未量化的原始高精度模型'的精度,**无法反映训练时量化模型的真实精度,激活量化部分根本无法复现**。"

## 探针与操作

- 关键证据链（均为 source_observed 代码事实，source 0 seq 82）：
  - wrapper 存储：`wrapper_tensors/base_wrapper_tensor.py` 第 127 行 `self._data = tensor`；第 249-254 行 `__tensor_flatten__` 返回 `["_data"]`；`to_original()` 直接返回 `self._data`——checkpoint 保存/加载只看到高精度 `_data`。
  - 量化时机：`mx_wrapper_tensor.py` 第 60-71 行拦截 `linear`/`_grouped_mm`，文档明确 "Data stays in low-precision throughout the matmul, in contrast to fake-quantize wrappers which quantize then dequantize back to high precision before the matmul"。
  - 激活量化在算子内现算：`ops/mx_ops.py` `to_mx_then_mm` 第 80-93 行对激活 A 与权重 B 都调用 `npu_dynamic_mx_quant_with_dual_axis` 再 `npu_quant_matmul`（source 0 seq 81 逐字代码）。
  - MXFP4 伪量化：`mxfp4_fake_quantize` forward quantize→dequantize，误差只在前向数值，不改权重存储。
  - 无固化路径：全仓 grep 无 `_data.copy_`/post_optimizer 改权重；`post_optimizer_hook` 均为 pass/return。
  - 导出脚本：`convert_to_hf` 在 CPU、无 converter 的裸模型上 `dcp.load`（DCP 存的即 `_data`），`export_dtype` 只做 `v.to(target_dtype)` 纯 cast。

## 机制与判别

- 机制：QAT=训练时在 converter 改造后的 forward/backward 图里做动态量化；权重张量始终高精度存储，量化行为不固化。
- 判别：DCP/HF 导出看到的都是 `_data`（高精度）——导出物与"量化模型"解耦；要复现训练量化精度必须沿用 converter 量化路径（或显式做权重量化折叠）评测。
- 未验证推断：无（本结论为代码级确定性事实）；但"导出后精度差异幅度"未实测。

## 验证信号

- source_observed：上述逐文件行号代码证据（wrapper/mx_ops/convert 脚本/git commit 描述）。
- 无设备运行；属静态代码核实（调研任务目标即静态判定）。

## 适用与失效边界

- 适用于：torchtitan-npu + torchao_npu QAT（MXFP8/MXFP4/BlockFP8）训练导出与评测决策。
- 失效边界：若未来加入 post-optimizer 权重固化/折叠工具（把量化写回权重）则结论改变；本仓 `_DEFAULT_CONVERTERS`（npu_gmm 等）本身纯 bf16 不含量化，勿混淆。
- 停止条件：导出评测前先确认评测路径是否挂接同等 converter 量化；否则结果只能代表高精度基线。

## 附：断言存档

- torchtitan-npu QAT/MXFP8 的量化行为只活在 converter 改造的 forward 计算图：wrapper 以 self._data 存高精度权重（__tensor_flatten__ 只暴露 _data），量化在 __torch_function__/matmul 时动态发生（npu_dynamic_mx_quant_with_dual_axis 后 npu_quant_matmul），激活与权重均前向现算；导出 HF bf16（convert_to_hf 裸模型 dcp.load + export_dtype 纯 cast）只得到高精度原始权重。
