---
{
  "type": "Runbook",
  "title": "npu_swiglu halves 交换修复的 NPU bf16 单元等价验证（vs 原始 chunk+SiLU+mul）",
  "description": "npu_swiglu 替换 SwiGLU 的 halves 交换修复在 NPU bf16 单元验证中与原始 chunk+SiLU+mul 实现 max abs diff 0.0039、cosine similarity≈1.0，判定 bf16 精度范围内等价。",
  "tags": [
    "task.debugging",
    "topic.precision"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": []
}
---
# npu_swiglu halves 交换修复的 NPU bf16 单元等价验证（vs 原始 chunk+SiLU+mul）


## 适用场景
diffusers 系生成式模型在 NPU 上以 npu_swiglu 融合算子替换 SwiGLU 类前向的场景；用于修复后与原始实现的数值等价验证。

## 触发与观测
触发：diffusers 系模型在 NPU 上以 npu_swiglu 融合算子替换 SwiGLU 后需要数值等价验证（场景见适用场景）。

## 探针与操作
写 NPU bf16 单元脚本模拟修复前后向并计算 max abs diff / rel diff / cosine similarity（脚本见机制片段：）。

## 机制与判别
机制与判别：以 NPU bf16 单元脚本对比修复后与原始 chunk+SiLU+mul 实现的数值等价性（见来源结论 与机制片段：）。

### 关键结论


- 验证：在 NPU 上以 bf16 Linear(64,128) 模拟 SwiGLU 前向，修复后与原始 chunk+SiLU+mul 实现对比 max abs diff 0.00390625、max rel diff 0.0078125、cosine similarity≈1.0，判定 Pass: True（bf16 精度范围内等价）。


### 补充机制片段

工件：

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

## 验证信号
单元级 NPU bf16 数值等价验证：max abs diff 0.00390625、max rel diff 0.0078125、cosine similarity≈1.0、Pass: True。轨迹内未做端到端视频复跑。

## 适用与失效边界
适用于 npu_swiglu 替换 SwiGLU 的单元级数值等价验证场景；失效边界：单元级验证不覆盖端到端行为。
