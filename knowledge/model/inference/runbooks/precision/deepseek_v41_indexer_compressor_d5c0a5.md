---
{
  "type": "Runbook",
  "title": "DeepSeek-V4.1 indexer/compressor 权重精度降级（665d5c0a5：bf16 权重乘法与 FP32→BF16 投影权重）引入精度波动",
  "description": "vllm-ascend DeepSeek-V4.1 适配中，提交 665d5c0a5 将 indexer 的 head 权重乘法从 weights.float() * weights_scale 改为 bf16 tensor 直接乘（bf16 结果），softmax 前权重先在 bf16 舍入；ratio=2 compressor 的 wkv/wgate 构造为 FP32 但 process_weights_after_loading 加载后统一转 BF16，与 README 声明的 C2 保留 FP32 投影计算矛盾。相邻分数接近时 indexer top-k 选择可能翻转，产生随批量/量化噪声的非确定性稀疏索引差异并放大为输出波动；C2 层（2/8/14）压缩 KV 表示质量受投影精度影响。两条独立审查轨迹分别从不同侧面发现该问题。",
  "tags": [
    "task.debugging",
    "topic.precision",
    "topic.model_serving"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-03T12:00:00Z",
  "updated_at": "2026-11-03T12:00:00Z",
  "platforms": [
    "agnostic"
  ]
}
---

# DeepSeek-V4.1 indexer/compressor 权重精度降级（665d5c0a5：bf16 权重乘法与 FP32→BF16 投影权重）引入精度波动

## 适用场景

- 模型/框架：DeepSeek V4.1（DSA 注意力：indexer top-k 选择 + C2 compressor 投影），vllm-ascend 硬件插件，分支 releases/v0.27.1rc，审查区间 `git log 09220f435~1..HEAD`（共 112 个提交，HEAD=6746201ec）。
- 平台：Ascend NPU（A5 生产：deepseek_v4_fp8 + weight_nz_mode=2 + eager/FULL_DECODE_ONLY + TP/EP）。
- 工作负载：用户报告"精度波动"（weight_nz_mode=2 + fp8 量化适配背景下）。
- 该问题由两条独立审查轨迹分别从不同侧面发现（DSA 注意力审查 P2-1/P2-2 与模型侧审查 P1-4）。

## 触发与观测

触发 = 所有 DeepSeek-V4.1 前向都会经过 indexer 权重乘法与 C2 compressor 投影；影响面是 indexer top-k 选择的确定性与 C2 层（2/8/14）压缩 KV 的表示质量。

审查观测到的客观代码事实：

1. 提交 665d5c0a5 的 diff（事件 82，`git show 665d5c0a5 -- vllm_ascend/models/deepseek_v41/indexer.py vllm_ascend/models/deepseek_v41/compressor.py`，逐字）：

```
-        weights = weights.float() * self.weights_scale
+        weights = weights * self.weights_scale
```

```
-        self.wkv = nn.Linear(dim, self.width, bias=False, dtype=torch.float32 if ratio == 2 else torch.bfloat16)
+        self.wkv = nn.Linear(dim, self.width, bias=False, dtype=torch.bfloat16)
         self.norm = DeepseekV41RMSNorm(self.width, _read(config, "rms_norm_eps"))
         if ratio == 2:
-            self.wgate = nn.Linear(dim, self.width, bias=False, dtype=torch.float32)
+            self.wgate = nn.Linear(dim, self.width, bias=False, dtype=torch.bfloat16)
```

2. 当前 HEAD 的 indexer 代码（事件 27，indexer.py 全文读取，逐字）：

```
164:         weights = self._output(self.weights_proj, hidden_states)
165:         weights = weights * self.weights_scale
```

3. 当前 HEAD 的 compressor 权重处理（事件 26，compressor.py 全文读取，逐字；构造器 ratio==2 时 wkv/wgate 为 FP32，加载后统一转 BF16）：

```
129:     def process_weights_after_loading(self):
130:         if self.ratio == 1:
131:             self.wkv.weight.data = maybe_trans_nz(self.wkv.weight.data)
132:         elif self.ratio == 2:
133:             self.wkv.weight.data = self.wkv.weight.data.to(torch.bfloat16)
134:             self.wgate.weight.data = self.wgate.weight.data.to(torch.bfloat16)
```

4. README 声明（事件 138，README.md 读取，逐字）：

```
188: C2 retains the existing FP32 projection weights and computation. The projected
189: Triton entry point pools current-chunk rows plus prior ring residuals before
190: updating the last 16 rows of the ring. State remains FP32, including values
191: that BF16 would round away. The pooled output is BF16 and passes through the
192: existing model RMSNorm, preserving its epsilon and rounding order. C1 and the
193: standalone Triton compressor API retain their paths.
```

## 探针与操作

核查命令（审查会话实际执行）：

```
git show 665d5c0a5 --stat | head -30; echo =====; git show 665d5c0a5 -- vllm_ascend/models/deepseek_v41/indexer.py vllm_ascend/models/deepseek_v41/compressor.py | head -300
```

以及读取 `vllm_ascend/models/deepseek_v41/compressor.py`（95-134 行）与 `indexer.py`（138-179 行）当前态。

本条为只读审查发现，未实施修复；"恢复先 .float() 再乘 scale（一行改动，无性能代价——后续本来就是 fp32 消费）"与"确认 CANN compressor_v2 的 ABI 是否强制 bf16 权重"的修复方向均未经验证。

## 机制与判别

结论 1：665d5c0a5 将 indexer 权重乘法从 weights.float() * self.weights_scale 改为 weights * self.weights_scale（bf16 tensor × python float → bf16 结果），softmax 融合前的 head 权重先在 bf16 中舍入再上采，属确定性精度损失。
- 证据：事件 82（diff 逐字）+ 事件 27（当前态 164-165 行逐字）。

结论 2：ratio=2 compressor 的 wkv/wgate 构造为 FP32，但 process_weights_after_loading 加载后统一 .to(torch.bfloat16)，与 README "C2 retains the existing FP32 projection weights and computation ... State remains FP32, including values that BF16 would round away" 的声明矛盾；checkpoint dtype 未在轨迹内确认。
- 证据：事件 26（129-134 行逐字）+ 事件 138（README 188-193 行逐字）。
- 判别：若 checkpoint 的 compressor.wkv/wgate 本为 BF16，则 fp32→bf16 往返无损，风险仅在融合算子内部累加精度；若 checkpoint 为 FP32 权重，则是有意的精度削减（提交链：30c0c0a6d "convert V4.1 compressor and indexer matmul weights to NZ format" → 571c907f7 "skip NZ for ratio=2 compressor weights, add model-level process_weights hook"）。

结论 3：indexer 打分在相邻分数接近时 top-k 选择可能翻转，随批量/量化噪声出现非确定性稀疏索引差异并放大为输出波动；C2 层（2/8/14）压缩 KV 表示质量受投影精度影响——两者均为代码级推断，轨迹内未做消融验证。
- 可区分解释分支：
  - 波动若集中于长上下文检索任务且分层消融显示 C2 层（2/8/14）敏感 → 指向 compressor 投影精度（结论 2）。
  - 波动若表现为稀疏索引（TopK 选择）随批量组成非确定变化 → 指向 indexer bf16 乘法（结论 1）。
  - 参考实现对照：原 Triton 参考实现（ops/triton/compressor/compressor_triton.py:70,509-515,583-584）投影累加器和 kv/score 输出均为 FP32（F.linear(xs.float(), wkv.float())），UT 对拍时容差需相应调整。

## 验证信号

- 信号等级：代码事实（git show/read 工具结果），非运行验证。
- 本轨迹内观测到的客观信号：事件 82（665d5c0a5 diff 逐字，含 indexer 乘法与 compressor dtype 两处变更）、事件 27（indexer 当前态 164-165 行）、事件 26（compressor process_weights_after_loading 129-134 行）、事件 138（README 188-193 行声明原文）。
- 平台：Ascend NPU（A5）。双轨迹交叉（DSA 审查与模型侧审查均引用 665d5c0a5/compressor 精度）。
- 无性能/精度数值结论（只读审查，未运行消融或基准）。

## 适用与失效边界

- 适用：DeepSeek-V4.1 全部前向（indexer 权重乘法）；C2/ratio=2 compressor 层（2/8/14）的投影路径。
- 不适用：C1/ratio=1 compressor（wkv 转 NZ，权重处理路径不同）；README 声明覆盖的 pooled 输出 BF16 与 RMSNorm epsilon/舍入顺序（这部分与实现一致）。
- 版本边界：665d5c0a5（"opt indexer and compressor"，2026-09-21）引入；其后构造器曾回到 fp32-if-ratio-2（当前 HEAD compressor.py:103），但 process_weights_after_loading 仍统一转 bf16——净效果是 C2 投影以 bf16 权重运行。若 checkpoint 本为 bf16 权重则往返无损。
- 停止/回退条件：确认 checkpoint dtype 为 BF16 后，结论 2 降级为"与 README 文档矛盾"的可维护性问题；确认 CANN compressor_v2 ABI 强制 bf16 权重后，修复方向应为在 README/提交中明确记录该精度取舍。
- 修复方向（未验证）：indexer 恢复 `weights = weights.float() * self.weights_scale`；compressor 侧确认 ABI 后恢复 fp32 或记录取舍。
