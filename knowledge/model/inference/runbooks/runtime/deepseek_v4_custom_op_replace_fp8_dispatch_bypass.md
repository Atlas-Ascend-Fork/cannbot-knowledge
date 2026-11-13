---
{
  "type": "Runbook",
  "title": "deepseek-v4 自定义算子替换不生效：fp8 量化路径绕过被修改的模块",
  "description": "cann-recipes-infer deepseek-v4 接入自定义算子（npu_test::npu_grouped_matmul / MoeGatingTopKHash 等）后，推理日志不出现 [ATEN-REPLACE]/[KERNEL-REPLACE]/GroupedMatmul 打印、怀疑替换未生效的场景。",
  "tags": [
    "task.debugging",
    "topic.mixture_of_experts"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": []
}
---
# deepseek-v4 自定义算子替换不生效：fp8 量化路径绕过被修改的模块

## 适用场景
cann-recipes-infer deepseek-v4 接入自定义算子（npu_test::npu_grouped_matmul / MoeGatingTopKHash 等）后，推理日志不出现 [ATEN-REPLACE]/[KERNEL-REPLACE]/GroupedMatmul 打印、怀疑替换未生效的场景。

## 触发与观测
test.log 中 GroupedMatmul/SwigluGroupQuant/QuantBatchMatmul/npu_grouped_matmul 相关打印 grep 计数为 0；test.log 显示 (experts): FusedMoEGMM()、(moe_ffn): FusedMoEGMM()。

## 探针与操作
1) grep test.log 统计替换打印计数。
2) grep modeling_deepseek.py 的 quant_config/gmm_quant_mode/FusedMoEGMM 派发逻辑。
3) 读 module/fuse_moe_gmm.py 的 UnquantizedFusedMoEGMMMethod.apply（torch_npu.npu_grouped_matmul 调用点）。
4) 结合 test.log 生成时间 vs 修改/pyc 时间判断运行时实际走的模块。

## 机制与判别
判别链：config.json 只有 HuggingFace 的 quantization_config（quant_method=fp8），而 configuration_deepseek.py:217 读 quant_config（None）→ gmm_quant_mode="w16a16" → moe_ffn=FusedMoEGMM；自定义 npu_test::npu_grouped_matmul 只在 experts_w4a8int4 中被调用、从未 dispatch。彻底替换需改 fp8.py:300,326 两处 torch_npu.npu_grouped_matmul。

机制片段：
```
self.moe_ffn = self.experts_w4a8int4 if self.gmm_quant_mode == "w4a8int4" else self.experts
```

## 验证信号

源码读回显示 config 读取的是 `quant_config`；为 None 时 gmm_quant_mode 默认 w16a16 并选择 FusedMoEGMM，目标自定义算子调用则位于另一分派方法。只确认所读版本中的静态分派关系，没有修改后的前向数值或运行替换验证。

## 适用与失效边界
适用于 deepseek-v4 + FusedMoEGMM + fp8 quantization_config 组合；先确认运行时派发到哪个 quant 方法再改代码。相关会话 （QuantBatchMatmulV3 未打印替换日志）同环境同主题但在轨迹内未得出结论。

## 结论与证据边界
- 判别：第一层是 config 字段名不匹配——configuration_deepseek.py:217 读 quant_config（默认 None）而 config.json 只有 HuggingFace 的 quantization_config；gmm_quant_mode 判为 w16a16 时 moe_ffn=FusedMoEGMM，自定义 npu_test::npu_grouped_matmul 只在 experts_w4a8int4 方法中被调用、从未 dispatch；彻底替换需改 fp8.py:300,326 两处 torch_npu.npu_grouped_matmul
