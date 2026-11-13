---
{
  "type": "Runbook",
  "title": "PyPTO W811 回退 allow_internal_format=False 后 npu_format_cast 到 FRACTAL_NZ 仍可用：int8/bf16 转换与 reshape/.npu() 格式保持",
  "description": "deepseek_v4 test_mla_prolog_quant_v4 运行报 W811（设备仅支持 allow_internal_format=False，请求 True 被回退）并抛 FeError F00002：第 2 输入 ND 与输入定义 TileOpFormat.TILEOP_NZ 不匹配。npu_format_cast+get_npu_format 探针证明 allow_internal_format=False 时 int8/bf16 张量仍能转成 FRACTAL_NZ 且格式经 reshape/.npu() 保持——排除\"设备无法创建 NZ 张量\"的解释。",
  "tags": [
    "task.debugging",
    "topic.compilation"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": []
}
---
# PyPTO W811 回退 allow_internal_format=False 后 npu_format_cast 到 FRACTAL_NZ 仍可用：int8/bf16 转换与 reshape/.npu() 格式保持

## 适用场景

deepseek_v4 test_mla_prolog_quant_v4 运行报 W811（设备仅支持 allow_internal_format=False，请求 True 被回退）并抛 FeError F00002：第 2 输入 ND 与输入定义 TileOpFormat.TILEOP_NZ 不匹配。npu_format_cast+get_npu_format 探针证明 allow_internal_format=False 时 int8/bf16 张量仍能转成 FRACTAL_NZ 且格式经 reshape/.npu() 保持——排除"设备无法创建 NZ 张量"的解释。


## 触发与观测


W811 环境关闭 allow_internal_format 后仍需判断能否显式构造 NZ 张量，而不能只根据默认工厂告警认定设备不支持 NZ。

## 探针与操作

- W811 回退 allow_internal_format=False 并不阻止 npu_format_cast 到 FRACTAL_NZ：int8 与 bf16 张量转换后 get_npu_format 返回 FRACTAL_NZ，且经同形 reshape 与 .npu() 后格式保持不变——排除"设备无法创建 NZ 张量"的解释。

## 机制与判别

（机制片段：如下）

机制片段：

```
python3 -c "
import torch
import torch_npu
torch_npu.npu.config.allow_internal_format = False
torch.npu.set_device(0)

# Create int8 tensor
t = torch.randn(4096, 1024).to(torch.int8).npu()
print('Before convert - get_npu_format:', torch_npu.get_npu_format(t))

# Convert to NZ
t_nz = torch_npu.npu_format_cast(t.clone(), torch_npu.Format.FRACTAL_NZ)
print('After convert - get_npu_format:', torch_npu.get_npu_format(t_nz))
print('After convert - shape:', t_nz.shape)

# Also test bf16
t2 = torch.randn(4096, 1024, dtype=torch.bfloat16).npu()
print('BF16 Before convert - get_npu_format:', torch_npu.get_npu_format(t2))
t2_nz = torch_npu.npu_format_cast(t2.clone(), torch_npu.Format.FRACTAL_NZ)
print('BF16 After convert - get_npu_format:', torch_npu.get_npu_format(t2_nz))
" 2>&1
```

## 验证信号


工具输出显示 int8 与 BF16 从 ND 转换后 `get_npu_format` 为 FRACTAL_NZ；后续输出依次为 `After NZ convert: FRACTAL_NZ`、`After reshape (same shape): FRACTAL_NZ`、`After .npu(): FRACTAL_NZ`。只确认所测转换，不等于故障 kernel 的格式声明已匹配或数值已通过。

## 适用与失效边界

适用：PyPTO 算子测试出现 W811 allow_internal_format 回退 + FeError F00002 输入格式不匹配的排障。判别要点：先用 npu_format_cast 探针确认设备能否建 NZ（本例能）。失效边界：allow_internal_format=True 的请求仅告警回退、不阻断运行；日志落盘位置由 ASCEND_WORK_PATH 决定而非默认路径。
