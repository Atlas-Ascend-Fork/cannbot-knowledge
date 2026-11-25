---
{
  "type": "Runbook",
  "title": "diffusers SwiGLU 接入 npu_swiglu：半区交换诊断、同源单元验证与回退边界",
  "description": "MiniMax-H3中diffusers与npu_swiglu的激活半区相反；合并既有同源NPU bf16单元验证，并修订重复投影的CPU回退建议，整网生成质量仍待验。",
  "tags": [
    "task.debugging",
    "topic.implementation.debugging"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-23T06:30:53Z",
  "platforms": []
}
---


# diffusers SwiGLU 接入 npu_swiglu：半区交换诊断、同源单元验证与回退边界

## 适用场景

- 模型/框架：MiniMax-H3（H3-Omni-Transformer 33B/50 层，diffusers `SwiGLU` FFN）NPU 推理适配，torch_npu（skip-import 提示 torch 2.10.0），单/多卡。
- 任务：npu_rms_norm / npu_swiglu / npu_rotary_mul 三项融合算子替换后，视频画面与音频同时异常的精度诊断与修复。
- 缺失信息：NPU 型号未记录。

## 触发与观测

用户报告三融合算子优化（git 9e81a20 + 03134d8）后视频画面异常、音频异常。NPU 数值探针（bf16, [2,8,16] 随机张量，source 0 seq 128，tool_observed）：

```text
Max diff between original and npu_swiglu: 1.59375
Max diff between original and swapped npu_swiglu: 0.0078125
RMSNorm max diff: 0.0
RoPE max diff: 0.03125
```

探针对比三方：diffusers 语义 `a * silu(b)`、直连 `npu_swiglu(x)`、交换 halves 后 `npu_swiglu(cat([b,a]))`。

## 探针与操作

源码与API对照：diffusers前向先 `self.proj`，再做 `first_half * silu(second_half)`（source 0 seq90）；`npu_swiglu` 是 `swish(first_half) * second_half`（seq74）。因此该模型NPU分支需要交换halves。

原轨迹seq141修复了NPU分支，但其非NPU回退仍把已投影的张量交给原forward，造成第二次 `self.proj`；这是历史补丁中未被NPU单元测试覆盖的缺陷，不能直接照抄整个wrapper。

复用时的控制流修正如下：设备判断放在投影之前；保存原始forward后再安装patch。这段是本轮根据源码修订的建议，原轨迹设备验证仅覆盖下面单元脚本中的NPU交换操作，不表示此wrapper已做NPU整网回归。

```python
_orig_swiglu_forward = SwiGLU.forward


def _npu_swiglu_forward(self, hidden_states):
    if hidden_states.device.type != "npu":
        return _orig_swiglu_forward(self, hidden_states)
    projected = self.proj(hidden_states)
    value, gate = projected.chunk(2, dim=-1)
    return torch_npu.npu_swiglu(torch.cat([gate, value], dim=-1), dim=-1)


SwiGLU.forward = _npu_swiglu_forward
```

同源验证的完整NPU bf16单元脚本保留如下；它与原先本卡的Linear(64,128)结果是同一个实验，不增加独立复现数：

```
import torch
import torch_npu
from torch_npu.contrib import transfer_to_npu

torch_npu.npu.set_compile_mode(jit_compile=False)
torch.npu.config.allow_internal_format = False

# Simulate SwiGLU forward with the fix
class FakeSwiGLU:
    def __init__(self):
        self.proj = torch.nn.Linear(64, 128, bias=False).to('npu', dtype=torch.bfloat16)
    def forward_fixed(self, hidden_states):
        hidden_states = self.proj(hidden_states)
        a, b = hidden_states.chunk(2, dim=-1)
        return torch_npu.npu_swiglu(torch.cat([b, a], dim=-1), dim=-1)
    def forward_original(self, hidden_states):
        hidden_states = self.proj(hidden_states)
        hidden_states, gate = hidden_states.chunk(2, dim=-1)
        return hidden_states * torch.nn.functional.silu(gate)

model = FakeSwiGLU()
x = torch.randn(1, 16, 64, dtype=torch.bfloat16, device='npu')

with torch.no_grad():
    orig = model.forward_original(x)
    fixed = model.forward_fixed(x)

diff = (orig - fixed).abs().max().item()
rel_diff = (orig - fixed).abs() / (orig.abs() + 1e-6)
print(f'Max abs diff: {diff}')
print(f'Max rel diff: {rel_diff.max().item()}')
print(f'Cosine sim: {torch.nn.functional.cosine_similarity(orig.flatten(), fixed.flatten(), dim=0).item()}')
print(f'Pass: {diff < 0.01}')
```

## 机制与判别

- 源码给出了激活半区的语义差异；随机bf16样例的max diff由1.59375降至交换后的0.0078125，与这一判断一致（source 0 seq90/127/128）。
- 同次RMSNorm样例diff=0.0、RoPE样例diff=0.03125，只是所测小张量结果；没有真实模型的整网消融，不能据此排除这两项补丁的问题或宣称“已验证无害”。
- 交换需要cat；原轨迹没有完整测量其性能代价，也没有验证最终视频/音频质量。

## 验证信号

- 原轨迹source 0 seq165/166的NPU bf16 Linear(64→128)单元复测：max abs diff0.00390625、max rel diff0.0078125、日志 `Cosine sim: 1.0078125`、`Pass: True`。单元Pass依据脚本中的 `diff < 0.01`，不代表数学余弦超过1，也不代表整网精度通过。
- 该结果与既有卡中的同一脚本/观测合并，仅记一次设备单元实验。
- wrapper的非NPU回退控制流属于本轮修订；需分别验证只投影一次与NPU交换路径，不能把历史NPU样例当作CPU回退验证。

## 适用与失效边界

- 适用于已从源码确认gate在后半的SwiGLU实现；若原实现为 `silu(first)*second`，不能再次交换。
- 出现生成质量异常时，应回退对应patch并对RMSNorm、RoPE和SwiGLU分别做整网消融；本记录没有证明另外两项补丁无害。
- 单次NPU bf16小张量验证不覆盖其它dtype、真实激活分布或端到端视频。非NPU回退必须传入原始张量，不能先投影再调用原forward。
- 同模型注意力布局微基准见[MiniMax-H3融合性能诊断](../performance/environ_setdefault_diffusers_attn_backend_native_npu_diffusers_models.md)；其保留SwiGLU建议同样必须满足这里的半区条件。

## 附：断言存档

- diffusers本例与npu_swiglu的激活半区不同，NPU分支通过交换halves对齐；同源Linear单元结果只记一次。
- 原wrapper的CPU回退重复投影未被NPU测试覆盖；修订建议把设备判断放在投影前。整网质量与其它融合patch仍需独立验收。
