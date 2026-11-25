---
{
  "type": "Runbook",
  "title": "daVinci-MagiHuman gelu7 手动实现替换 torch_npu.npu_fast_gelu（clamp 前置，公式范围与实机平台分开）",
  "description": "模型/框架：daVinci-MagiHuman（DiT 音视频生成，15B，40 层，其中 layers 0-3 用 GELU7 激活），cann-recipes 推理仓单卡 NPU（实际型号未确认，原记录65GB HBM，ASCEND_RT_VISIBLE_DEVICES=13），torch_npu 推理。",
  "tags": [
    "task.implementation",
    "topic.implementation.debugging"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:06Z",
  "updated_at": "2026-11-24T01:53:53Z",
  "platforms": []
}
---

# daVinci-MagiHuman gelu7 手动实现替换 torch_npu.npu_fast_gelu（clamp 前置，公式范围与实机平台分开）

## 适用场景

- 平台范围未定位：下文A2/A3公式是所引接口说明的适用范围，不作为本次设备判型或跨产品实测证明。

- 模型/框架：daVinci-MagiHuman（DiT 音视频生成，15B，40 层，其中 layers 0-3 用 GELU7 激活），cann-recipes 推理仓单卡 NPU（实际型号未确认，原记录65GB HBM，ASCEND_RT_VISIBLE_DEVICES=13），torch_npu 推理。
- 任务：t2v 视频生成 denoise 阶段性能优化（distill 8 步 / base 32 步）。
- 缺失信息：torch/torch_npu/CANN 具体版本号未在本轨迹出现（progress.md 记录的另一工作目录为 PyTorch 2.10.0/torch_npu 2.10.0/CANN 9.0.0，不能直接套用本目录）。

## 触发与观测

优化前 profiling（distill 8 步、采样 1 步，source 0 seq 60，tool_observed）中 gelu7 相关小算子开销：

```text
13,Mul,AI_VECTOR_CORE,56,9550.352,...,1.789
13,ClipByValueV2,AI_VECTOR_CORE,4,4969.119,...,0.931
13,Sigmoid,AI_VECTOR_CORE,44,2209.523,...,0.414
```

其中 gelu7 贡献 4 次 InplaceSigmoid（约 474us/次）与部分 Mul；attention gating 的 `sigmoid(g)` 为 40 次小 sigmoid（约 25us/次），无对应融合算子（不同张量逐元素 `a*sigmoid(b)`，npu_silu 仅支持同张量形式），不改。

## 探针与操作

替换（source 0 seq 121，编辑工具 before/after 逐字）：

before：

```python
def gelu7(x, alpha: float = 1.702, limit: float = 7.0, out_dtype: Optional[torch.dtype] = None):
    out_dtype = x.dtype if out_dtype is None else out_dtype
    x = x.to(torch.float32)
    x.clamp_(max=limit)
    sig = torch.mul(x, alpha)
    sig.sigmoid_()
    x.mul_(sig)
    return x.to(out_dtype)
```

after：

```python
def gelu7(x, alpha: float = 1.702, limit: float = 7.0, out_dtype: Optional[torch.dtype] = None):
    out_dtype = x.dtype if out_dtype is None else out_dtype
    x = x.to(torch.float32)
    x.clamp_(max=limit)
    x = torch_npu.npu_fast_gelu(x)
    return x.to(out_dtype)
```

语义依据：A2 上 `npu_fast_gelu(x) = x / (1 + e^(-1.702x)) = x * sigmoid(1.702x)`，与 clamp 后的 gelu7（alpha=1.702 默认）逐元素等价；clamp(max=7.0) 仍前置保留（官方算子无 clamp 参数，source 0 seq 74/79/104 文档与推理记录）。4 算子/层/步 → 2 算子。

## 机制与判别

- 等价条件：alpha 必须为 1.702（npu_fast_gelu 硬编码）；显式传入不同 alpha 的调用不可用此替换（源码签名保留 alpha 参数但 NPU 路径忽略之——本模型实际只用默认值）。
- 收益定位（profiling 前后对比，source 0 seq 60 vs seq 169，tool_observed）：Sigmoid 44→40 次、2209.5→312.6us（余下为 attention gating）；Mul 56→48 次、9550.4→3255.4us；新增 FastGelu 4 次 2435.3us。gelu7 链路净省约 5.75ms/步（agent 汇总，seq 190）。
- 未验证推断：逐元素数值等价未单独做单算子比对；「输出视频正常」以文件生成与大小近似判断（691978 vs 基线 693545 字节，source 0 seq 149/150），无像素级/VBench 评测。

## 验证信号

- 替换后完整推理多次成功，输出 `output_distill_5s_448x256.mp4` 正常生成（source 0 seq 138、149，tool_observed）。
- distill denoise（8 步，Step3→Step6 墙钟）3 次运行：4.897/4.948/4.906s（均值 4.917s，source 0 seq 144，tool_observed）。
- base denoise（32 步）2 次运行：35.775/35.598s（均值 35.686s，source 0 seq 155，tool_observed）。
- 基线（同 workload、同口径 Step3→Step6）：distill 5.04s、base 36.67s，来自项目 progress.md 既往记录（source 0 seq 12，已记录基线，非本轨迹当次实测）。
- 性能对比（本次观测，非通用承诺）：distill 8 步 5.04→4.917s（约 -2.4%）、base 32 步 36.67→35.686s（约 -2.7%）；单卡、bf16、同一 prompt/分辨率/步数；基线为记录值而非同批重测，属边界条件。

## 适用与失效边界

- 适用：Ascend A2/A3 上 `x*sigmoid(1.702x)` 形式且带 `clamp(max=7)` 的 GELU 变体（daVinci-MagiHuman GELU7 层）；fp32 中间计算 + 输出回原 dtype 的路径。
- 失效：alpha≠1.702、需要 clamp 下限（min clip）、或需要与 flash-attn gelu 的 tanh 近似严格一致的场景；attention gating 式 `a*sigmoid(b)`（两不同张量）无对应融合算子，不要强行替换。
- 回退条件：若输出视频质量异常，直接回退该函数为手动实现（单函数改动，无状态）。
- 同模型早前一次扫描（2026-06-11，另一工作目录）曾将 GELU 标记为 No-Go（无匹配算子），本轨迹（2026-07-14）以公式核对+端到端运行证伪该结论——采用本卡时以本轨迹证据为准。

## 附：断言存档

- gelu7 的 clamp_+mul+sigmoid_+mul_（4算子）可替换为 clamp_+torch_npu.npu_fast_gelu（2算子）：A2 上 npu_fast_gelu(x)=x*sigmoid(1.702x) 与 alpha=1.702 的 gelu7 逐元素等价，clamp(max=7.0) 前置保留。
- 替换后 distill 8步 denoise 3 次运行 4.897/4.948/4.906s（均值4.917s），对 progress.md 记录基线 5.04s 约 -2.4%；base 32步 2 次运行 35.775/35.598s（均值35.686s）对记录基线 36.67s 约 -2.7%（基线为既往记录值，非同批重测；单卡单次批量，不外推通用加速）。
- profiling 前后对比：Sigmoid 44次2209.5us→40次312.6us、Mul 56次9550.4us→48次3255.4us、新增 FastGelu 4次2435.3us；输出视频正常生成（691978B vs 基线记录693545B，无像素级验证）。

```text
"newString": "def gelu7(x, alpha: float = 1.702, limit: float = 7.0, out_dtype: Optional[torch.dtype] = None):\n    out_dtype = x.dtype if out_dtype is None else out_dtype\n    x = x.to(torch.float32)\n    x.clamp_(max=limit)\n    x = torch_npu.npu_fast_gelu(x)\n    return x.to(out_dtype)", "oldString": "def gelu7(x, alpha: float = 1.702, limit: float = 7.0, out_dtype: Optional[torch.dtype] = None):\n    out_dtype = x.dtype if out_dtype is None else out_dtype\n    x = x.to(torch.float32)\n    x.clamp_(max=limit)\n    sig = torch.mul(x, alpha)\n    sig.sigmoid_()\n    x.mul_(sig)\n    return x.to(out_dtype)"
```

```text
9: 13,Mul,AI_VECTOR_CORE,56,9550.352,1.82,170.542,948.479,1.789
10: 13,Index,AI_VECTOR_CORE,168,6943.323,14.32,41.329,55.641,1.301
11: 13,ConcatD,AI_VECTOR_CORE,168,5686.193,2.68,33.846,280.926,1.065
12: 13,Slice,AI_VECTOR_CORE,214,5647.95,2.94,26.392,62.721,1.058
13: 13,ClipByValueV2,AI_VECTOR_CORE,4,4969.119,1107.802,1242.28,1389.168,0.931
14: 13,RmsNorm,AI_VECTOR_CORE,117,4948.926,8.14,42.299,86.522,0.927
15: 13,RotaryPositionEmbedding,MIX_AIV,80,3513.927,20.561,43.924,71.041,0.658
16: 13,AsStrided,AI_VECTOR_CORE,152,3230.12,5.16,21.251,47.281,0.605
17: 13,MatMulV2,MIX_AIC,8,2941.058,301.366,367.632,433.529,0.551
18: 13,Sigmoid,AI_VECTOR_CORE,44,2209.523,7.6,50.216,477.469,0.414
```
