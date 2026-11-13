---
{
  "type": "Runbook",
  "title": "Ascend950PR FP8 matmul 参数探针：两种调用失败，预转float8后npu_quant_matmul组合通过",
  "description": "在 Ascend950PR_9589 + CANN 9.1.0（完整 ops_nn 安装）+ torch_npu 2.12.0 上，torch._scaled_mm（fp8 输入）报 aclnnQuantMatmulV5 failed error 161002，npu_quantize(..., torch.float8_e4m3fn, div_mode=False) 报 aclnnAscendQuantV3 failed；可行路径是两侧输入各自 .to(torch.float8_e4m3fn) 后调 torch_npu.npu_quant_matmul（本探针中该组合 OK，并被全模型 W8A8 推理与黄金参考对齐佐证）。单次探测，未在其他版本复测。",
  "tags": [
    "task.debugging",
    "topic.graph_execution",
    "topic.model_serving",
    "topic.attention"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-03T12:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": [
    "950"
  ]
}
---
# Ascend950PR FP8 matmul 参数探针：两种调用失败，预转float8后npu_quant_matmul组合通过

## 适用场景

- 模型/框架：在 Ascend NPU 上做 FP8（E4M3）量化矩阵乘的推理代码（本例 Hunyuan-A13B-Instruct-FP8 W8A8 静态量化）；候选 API：`torch._scaled_mm`、`torch_npu.npu_quantize`、`torch_npu.npu_quant_matmul`。
- 平台：Ascend950PR_9589 单卡，CANN 9.1.0（含 ascend950 ops_nn 的完整安装），torch_npu 2.12.0 / torch 2.12.0+cpu。
- 目标：选择该栈上实际可用的 FP8 matmul 入口。
- 缺失信息说明：仅单次探测、bf16 小张量（[8,64]×[64,32] 量级）；未在其他 CANN/torch_npu 版本或 SoC 上复测，不能外推为版本通用结论。

## 触发与观测

触发：探测三种 FP8 matmul API 组合（事件 264）。客观观测（事件 265 逐字）：

```
FAIL quant_matmul_fp8_x2t npu_quantize_by_ascend_quant:../third_party/op-plugin/op_plugin/ops/opapi/QuantizeKernelNpuOpApi.cpp:117 NPU function error: call aclnnAscendQuantV3 failed, err
OK   quant_matmul_fp8_both (torch.bfloat16, (8, 32))
FAIL _scaled_mm _scaled_mm:../third_party/op-plugin/op_plugin/ops/opapi/ScaledMmKernelNpuOpApi.cpp:433 NPU function error: call aclnnQuantMatmulV5 failed, error code is 161002
```

即：`torch._scaled_mm`（fp8 输入）失败（aclnnQuantMatmulV5，error 161002）；`npu_quantize` 量化到 float8_e4m3fn 失败（aclnnAscendQuantV3）；只有两侧输入先各自 `.to(torch.float8_e4m3fn)` 再调 `npu_quant_matmul` 的组合成功。

## 探针与操作

探针脚本（事件 264，逐字；x/w 为 bf16 NPU 张量，t() 打印 OK/FAIL）：

```
def f1():
    xq=torch_npu.npu_quantize(x, torch.tensor(1.0/xs), None, torch.float8_e4m3fn, div_mode=False)
    wq=w.to(torch.float8_e4m3fn)
    return torch_npu.npu_quant_matmul(xq, wq.t(), torch.tensor([1.0],device='npu'), output_dtype=torch.bfloat16)
t("quant_matmul_fp8_x2t", f1)
def f2():
    xq=x.to(torch.float8_e4m3fn)
    wq=w.to(torch.float8_e4m3fn)
    return torch_npu.npu_quant_matmul(xq, wq.t(), torch.tensor([1.0],device='npu'), output_dtype=torch.bfloat16)
t("quant_matmul_fp8_both", f2)
def f3():
    return torch._scaled_mm(x.to(torch.float8_e4m3fn), w.t().to(torch.float8_e4m3fn), scale_a=torch.tensor(1.0,device='npu'), scale_b=torch.tensor(1.0,device='npu'), out_dtype=torch.bfloat16)
t("_scaled_mm", f3)
```

本次原样调用失败（不能据此判整个API不可用）：`f1`（npu_quantize 产 fp8 激活）与 `f3`（torch._scaled_mm）。可行路线：`f2`（双侧预转 float8_e4m3fn + npu_quant_matmul，scale 传 [1] 或 input_scale*weight_scale 组合，见[FP8 W8A8 静态激活量化前必须 clamp(-448, 448)：E4M3 越界 cast 产生 NaN](../precision/fp8_w8a8_clamp_e4m3_cast.md) 的 clamp 约束）。

## 机制与判别

- 结论 a1：在 Ascend950PR_9589 + CANN 9.1.0 + torch_npu 2.12.0 上，torch._scaled_mm（fp8 输入）报 "call aclnnQuantMatmulV5 failed, error code is 161002"，npu_quantize(..., torch.float8_e4m3fn, div_mode=False) 报 "call aclnnAscendQuantV3 failed"（单次探测，bf16 小张量）。（证据：事件 264 探针，事件 265 结果）
- 结论 a2：npu_quant_matmul 在两侧输入先各自 .to(torch.float8_e4m3fn) 后可用（同探针 OK），并被全模型 W8A8 推理与 CPU 黄金参考对齐（余弦 0.99985、贪心 token 一致）佐证为本环境可行的 FP8 matmul 路径。（证据：事件 265 `OK quant_matmul_fp8_both`；事件 659 全模型对齐）
- 可区分解释：本次f1在量化阶段失败、f3在matmul阶段返回161002，f2组合成功；这说明这些具体调用的结果不同。探针未排查scale的device/shape、stride及其他参数契约，不能由此断言aclnnAscendQuantV3的整个dtype路径不可用，或把_scaled_mm失败归为后端不支持。
- 未验证推断：`npu_quantize` 是否支持其他 dst_type（int8 等）未测；`torch._scaled_mm` 在其他 torch_npu 版本是否可用未测。

## 验证信号

- 事件 265（单次探测，Ascend950PR_9589 / CANN 9.1.0 完整安装 / torch_npu 2.12.0）：`OK quant_matmul_fp8_both (torch.bfloat16, (8, 32))`；`FAIL ... aclnnAscendQuantV3 ...`；`FAIL ... aclnnQuantMatmulV5 failed, error code is 161002`。
- 事件 659（全模型 80GB W8A8、固定 21 token 输入、单次运行，采用 f2 路线 + clamp）：`token_match: true`、`prefill_cosine: 0.9998509287834167`、`prefill_top10_overlap: 10`。
- 证据等级：API 可用性为单次探测；全模型可行性为单次运行。

## 适用与失效边界

- 已观测失败条件：仅覆盖上文f1/f3的完整参数组合与该设备/版本；其中161002属于本次参数错误信号，根因未定位。不能外推为相同版本的所有合法调用都失败。
- 可行替代：两侧输入各自 `.to(torch.float8_e4m3fn)`（注意越界 NaN，见[FP8 W8A8 静态激活量化前必须 clamp(-448, 448)：E4M3 越界 cast 产生 NaN](../precision/fp8_w8a8_clamp_e4m3_cast.md) 的 clamp(-448,448)）后调 `torch_npu.npu_quant_matmul(xq, wq.t(), scale, output_dtype=torch.bfloat16)`；权重在加载期一次性转置到 [in,out] 可免每次 t()。
- 不外推：其他 torch_npu/CANN 版本、其他 SoC、其他 dst_type 未测；升级版本后应重跑本探针再下结论。
- 停止条件：若 `npu_quant_matmul` 也报错，先确认环境（ops_nn，见[Ascend950 CANN 缺 ops_nn 算子包的判别与 env.sh 双条件自动探测修复](ascend950_cann_ops_nn_envsh.md)）与输入 dtype/shape（scale 形状 [1] 或 [N]）。
