---
{
  "type": "Runbook",
  "title": "FP8 W8A8 静态激活量化前必须 clamp(-448, 448)：E4M3 越界 cast 产生 NaN",
  "description": "Hunyuan-A13B-Instruct-FP8（W8A8，checkpoint 自带静态 per-tensor input_scale/weight_scale）在 NPU 上用 npu_quant_matmul 做激活量化时，本环境探针中 500、1000、-1000、1e5 直接 .to(float8_e4m3fn) 得到 NaN，不能依赖该 cast 自动饱和；激活先除以 input_scale 再 cast 前必须 clamp(-448,448)，否则量化激活出现 NaN、输出全 NaN。clamp 后单层误差 max 0.0596 / 平均绝对误差/参考平均幅度约 2.6%，全模型与 CPU BF16 黄金参考贪心 token 完全一致、prefill logits 余弦 0.99985。",
  "tags": [
    "task.debugging",
    "topic.precision",
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
# FP8 W8A8 静态激活量化前必须 clamp(-448, 448)：E4M3 越界 cast 产生 NaN

## 适用场景

- 模型/框架：Hunyuan-A13B-Instruct-FP8（checkpoint 自带 W8A8，`quantization_config.quant_method=fp8`、`activation_scheme=static`、per-tensor `input_scale`/`weight_scale`），在 Ascend NPU 上用 `torch_npu.npu_quant_matmul` 直接消费 FP8 权重；对其他"激活除以静态 scale 再 cast E4M3"的静态量化路径同样适用。
- 平台：Ascend950PR_9589 单卡，CANN 9.1.0（完整 ops_nn 安装），torch_npu 2.12.0 / torch 2.12.0+cpu。
- 目标：静态激活量化后 matmul 输出全 NaN 的判别与修复。
- 缺失信息说明：未在 GPU/其他 torch 版本上对比；未验证 per-channel scale 场景。

## 触发与观测

触发：用 checkpoint 的 `input_scale` 做静态激活量化（`x/input_scale` 后直接 `.to(torch.float8_e4m3fn)`）再调 `npu_quant_matmul`。客观观测（本轨迹逐字输出）：

- 事件 277（未 clamp，真实 q_proj 权重单层对拍）：`xq sat: nan Wt dtype torch.float8_e4m3fn`、`nan? True maxdiff nan`
- 事件 273（同一对拍的另一种 scale 组合）：`max abs diff nan`、`mean abs diff nan`、`ref abs mean 0.47733187675476074`、`no-actscale max diff 13819.59375`
- 事件 281（fp8 cast 越界行为探针，CPU 与 NPU 一致）：
```
v=       0.0 cpu->fp8 back=       0.0  npu->fp8 back=       0.0
v=       1.0 cpu->fp8 back=       1.0  npu->fp8 back=       1.0
v=     100.0 cpu->fp8 back=      96.0  npu->fp8 back=      96.0
v=     448.0 cpu->fp8 back=     448.0  npu->fp8 back=     448.0
v=     500.0 cpu->fp8 back=       nan  npu->fp8 back=       nan
v=    1000.0 cpu->fp8 back=       nan  npu->fp8 back=       nan
v=   -1000.0 cpu->fp8 back=       nan  npu->fp8 back=       nan
v=  100000.0 cpu->fp8 back=       nan  npu->fp8 back=       nan
isnan cpu True
```

## 探针与操作

clamp 修复后的单层数值探针（逐字，事件 284；scale = `input_scale * weight_scale`）：

```
W=load('model.layers.0.self_attn.q_proj.weight')
ws=load('model.layers.0.self_attn.q_proj.weight_scale').float()
ins=load('model.layers.0.self_attn.q_proj.input_scale').float()
x=torch.randn(8,4096,dtype=torch.bfloat16)*0.5   # realistic-ish
Wref=(W.float()*ws).to(torch.bfloat16)
ref=torch.nn.functional.linear(x,Wref)
xq=torch.clamp(x.float()/ins,-448,448).to(torch.float8_e4m3fn).npu()
Wt=W.t().contiguous().npu()
scale=(ins*ws).float().reshape(1).npu()
out=torch_npu.npu_quant_matmul(xq,Wt,scale,output_dtype=torch.bfloat16).cpu()
```

生产实现（`FP8Linear.forward`，逐字，含原始行号，事件 19·阶段 2 轨迹读取的 `models/modeling_hunyuan.py`）：

```
74:     def forward(self, x: Tensor) -> Tensor:
75:         orig_shape = x.shape
76:         x2 = x.reshape(-1, self.in_features)
77:         if self.quantized and x2.device.type == "npu":
78:             xq = torch.clamp(
79:                 x2.float() / self.input_scale, -FP8_MAX, FP8_MAX
80:             ).to(torch.float8_e4m3fn)
81:             scale = (self.input_scale * self.weight_scale).reshape(1)
82:             out = torch_npu.npu_quant_matmul(
83:                 xq, self.weight, scale, output_dtype=x.dtype
84:             )
```

其中 `FP8_MAX = 448.0`（E4M3 最大常规值）。失败路线（不可采用）：不 clamp 直接 `.to(torch.float8_e4m3fn)`——越界 cast 可产生 NaN 并传播到 matmul 输出；影响范围取决于越界元素位置；也不能省略激活 scale（`no-actscale max diff 13819.59375`，误差爆炸）。

## 机制与判别

- 结论 a1：本环境对 500.0、1000.0、-1000.0、1e5 直接执行 .to(torch.float8_e4m3fn) 得到 NaN，NPU 与 CPU 采样行为一致；未采样紧邻 448 的舍入临界点，不能断言所有绝对值刚大于 448 的数都立即为 NaN（本次采样中 0、1、100、448 可得到有限结果）。（证据：探针事件 280，结果事件 281）
- 结论 a2：激活按 checkpoint 静态 input_scale 量化前必须先 clamp(-448,448)：不 clamp 时量化后激活出现 nan、单层输出 max abs diff 为 nan；clamp 后单层 q_proj 的 npu_quant_matmul 与 BF16 反量化参考 max diff 0.0596、平均绝对误差与参考平均幅度之比约 2.6%（单层、单次观测）。（证据：事件 273/277 失败态，事件 285 修复态 `maxdiff 0.0595703125 meandiff 0.0063459924422204494 ref absmean 0.2442949414253235` / `rel 0.025976765900850296`）
- 结论 a3：全模型按 clamp + npu_quant_matmul(xq, W[in,out], input_scale*weight_scale) 实现后，与 CPU BF16 黄金参考贪心 token 完全一致 [27, 9399, 397, 60704]、prefill logits 余弦 0.99985、top-10 全命中（token_match=true，first_divergence_step=null）。（证据：事件 659 `agentic/golden/npu_vs_cpu.json`）
- 可区分解释：输出全 NaN 且 ref 本身正常 → 量化输入越界（本问题）；仅个别 token 错 → scale 组合/语义问题；`no-actscale` 巨大误差 → 漏乘 input_scale。clamp 引入的是有界饱和误差（单层 mean(abs_error)/mean(abs_reference) ~2.6%），与"NaN 污染"可区分。
- 未验证推断：clamp 对最终精度的影响仅通过贪心 token 一致 + 余弦 0.99985 间接评估，未做逐层误差传播分析。

## 验证信号

- 事件 281：cast 越界探针（500.0 → nan，CPU/NPU 一致）——机制证据。
- 事件 285（单次观测，Ascend950PR_9589 + CANN 9.1.0 完整安装）：`maxdiff 0.0595703125 meandiff 0.0063459924422204494 ref absmean 0.2442949414253235` / `rel 0.025976765900850296`。
- 事件 659（全模型 80GB 权重、固定 21 token 输入、单次运行）：`token_match: true`、`prefill_cosine: 0.9998509287834167`、`prefill_top10_overlap: 10`、`first_divergence_step: null`。
- 输出正确性旁证：全模型生成 `<answer>\nParis.\n</answer>`。
- 证据等级：单机单卡、单次运行；数值探针为单层（q_proj）单次。

## 适用与失效边界

- 适用：静态 per-tensor 激活 scale（`activation_scheme=static`）的 W8A8 E4M3 路径；动态量化（`npu_dynamic_quant` 自带 rowMax/448 缩放）不适用本 clamp 前置。
- clamp 边界 448 是 E4M3 最大常规值（FP8_MAX）；若换 E5M2 等格式边界不同，需相应调整。
- 饱和截断 vs NaN 的取舍：clamp 会把极端激活压到 ±448，属于有偏但有界的处理；对异常大激活敏感的模型需评估该误差。
- 停止/回退条件：若 clamp 后贪心 token 仍发散，应检查 scale 语义（是否漏乘 input_scale 或权重未转置到 [in,out]），而不是继续放宽 clamp。
- 未验证：clamp 与 per-channel/per-group scale 组合、训练场景（梯度）不适用。
