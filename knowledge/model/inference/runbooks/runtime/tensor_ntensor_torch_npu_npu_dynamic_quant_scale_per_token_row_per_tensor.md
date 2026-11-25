---
{
  "type": "Runbook",
  "title": "npu_dynamic_quant 语义探针：逐行对称 scale=amax/127，输出范围不含 -128，零行 scale=0",
  "description": "框架/模型：cann-recipes-infer Kimi K3 适配线的 routed expert W4A8 动态量化链路设计（SiTU dynamic quant 自定义算子的激活量化语义参照）。；对象：`torch_npu.npu_dynamic_quant`（int8 对称动态量化）的 scale 粒度、scale 公式与饱和行为。",
  "tags": [
    "task.debugging",
    "topic.implementation.debugging"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:05Z",
  "updated_at": "2026-11-24T01:53:53Z",
  "platforms": [
    "a3"
  ]
}
---

# npu_dynamic_quant 语义探针：逐行对称 scale=amax/127，输出范围不含 -128，零行 scale=0

## 适用场景

- 平台范围依据：source 0 seq 1371的实际环境/设备记录确认本次为Atlas A3；这里不扩展未记录的产品或版本。

- 框架/模型：cann-recipes-infer Kimi K3 适配线的 routed expert W4A8 动态量化链路设计（SiTU dynamic quant 自定义算子的激活量化语义参照）。
- 对象：`torch_npu.npu_dynamic_quant`（int8 对称动态量化）的 scale 粒度、scale 公式与饱和行为。
- 平台：Atlas A3，`source <internal_build_path>` 后的 torch_npu 环境。

## 触发与观测

- 触发：SiTU 自定义算子开工审计（source 0 seq 1473-1490 起的四算子并行开发回合）需要确定动态量化 epilog 的数值契约；审计结论建议 SiTU 拆分为 `npu_situ` 与 `npu_situ_dynamic_quant`（source 0 seq 1645）。
- 观测一（零输入，source 0 seq 1619）：`x=torch.zeros((2,64), bf16)` → 输出 int8 全 0，scale 返回 `tensor([0., 0.])`——**每个 batch 行一个 scale 元素**。
- 观测二（边界值，source 0 seq 1630）：`x=torch.tensor([[1.,-2.,127.,-128.]], bf16)` → `y=[[1,-2,126,-127]] (int8)`，`s=[1.0079]`。

## 探针与操作

逐字（source 0 seq 1622 tool_call / 1630 tool_result）：

```python
import torch, torch_npu
x=torch.tensor([[1.,-2.,127.,-128.]],device='npu:0',dtype=torch.bfloat16)
y,s=torch_npu.npu_dynamic_quant(x)
torch.npu.synchronize()
print(y.cpu(),s.cpu())
```

```text
tensor([[   1,   -2,  126, -127]], dtype=torch.int8) tensor([1.0079])
```

零输入探针（source 0 seq 1614 / 1619）：`(2,64)` 全零张量 → `tensor([0, 0, ...], dtype=torch.int8)`、`tensor([0., 0.])`。

## 机制与判别

- scale 粒度：**(2,64) 输入返回 2 个 scale 元素** → 逐行（per-token-row）scale，不是 per-tensor（source 0 seq 1619）。
- scale 公式：观测二行内 amax=128，s=1.0079≈128/127，与 `scale = amax / 127` 一致（对称量化，非 amax/128）（source 0 seq 1630）。
- 编码行为：`y = round(x/s)` 且对称范围 **[-127, 127]**：127/1.0079≈126.008→126（证明是舍入不是截断/直接映射），-128/1.0079=-127.0→-127（**int8 的 -128 码点未被使用**）。
- 零行退化：全零行 scale=0.0（非 1.0），输出全 0（source 0 seq 1619）。
- 判别要点：设计依赖「量化后恒等还原 x≈y*s」的 epilog（如 SwiGLU/SiTU 量化链）时，-128 输入饱和到 -127 与零行 scale=0 都会影响数值契约和除零保护。

## 验证信号

- tool_observed（source 0 seq 1615/1619）：零输入探针脚本执行完成，输出逐字在案。
- tool_observed（source 0 seq 1623/1630）：边界值探针脚本执行完成，输出逐字在案。
- agent_narrative（source 0 seq 1645）：SiTU 审计结论把动态量化版算子限定用于 routed expert W4A8 链路（基础 SiTU 走非量化路径）。

## 适用与失效边界

- 适用于：torch_npu `npu_dynamic_quant` 在 A3 + 会话时点 CANN 版本的激活 int8 对称量化语义（scale 粒度/公式/饱和边界），作为 W4A8/W8A8 动态量化链数值契约设计依据。
- 失效/边界：仅两组小 shape 探针（(2,64) 零张量、(1,4) 边界值）；逐行粒度在 >2 行、含 head/group 维度的真实张量上未复测；CANN/torch_npu 具体版本号未在探针回合记录（unknown）；未测 NaN/Inf 输入行为。

## 附：断言存档

- torch_npu.npu_dynamic_quant 的 scale 为逐行（per-token-row）粒度：(2,64) 输入返回两个 scale 元素（全零输入时 tensor([0., 0.])），不是 per-tensor

```text
tensor([0, 0, 0, 0, 0, 0, 0, 0], dtype=torch.int8)\ntensor([0., 0.])
```
