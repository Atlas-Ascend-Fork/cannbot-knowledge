---
{
  "type": "Runbook",
  "title": "候选卡片：deepseek-v4 推理未打印 ATEN-REPLACE/KERNEL-REPLACE：替换打印源自算子实现自身，调用点受 mm_quant_mode 守卫",
  "description": "deepseek-v4 自定义算子替换推理中 [ATEN-REPLACE]/[KERNEL-REPLACE] 打印缺失：替换打印源自算子实现自身（torch 绑定与 kernel 入口 AscendC::printf），消息缺失首先指向算子调用未发生而非日志级别问题；调用点受 mm_quant_mode==w8a8mxfloat8 守卫，quant_config 为 None 时默认 w16a16 不触发量化路径。",
  "tags": [
    "task.debugging",
    "topic.model_serving"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": []
}
---
# 候选卡片：deepseek-v4 推理未打印 ATEN-REPLACE/KERNEL-REPLACE：替换打印源自算子实现自身，调用点受 mm_quant_mode 守卫


## 适用场景

在 cann-recipes-infer 上做 deepseek-v4 自定义算子替换并依赖 [ATEN-REPLACE]/[KERNEL-REPLACE] 打印来验证替换生效的团队；适用于"替换日志未出现"类问题的第一轮定界。

## 触发与观测

触发条件与客观观测（期望的替换打印缺失；历史输出证明打印格式）：

- 来源结论：[ATEN-REPLACE]/[KERNEL-REPLACE] 消息由自定义算子实现自身打印：历史 stdout 中 [ATEN-REPLACE] QuantBatchMatmulV3 (npu_quant_batch_matmul_torch) called 来自 torch 绑定，[KERNEL-REPLACE] QuantBatchMatmulV3 kernel called 来自 kernel 入口的 AscendC::printf（仅 GetBlockIdx()==0 时打印）；因此推理日志中消息缺失首先指向算子调用/kernel 未执行，而非日志级别或环境开关问题。

- 来源结论：QuantBatchMatmulV3 走 namespace 策略（需手动改模型调用点）而非 aten 自动拦截：modeling_deepseek.py 中原 torch_npu.npu_transpose_quant_batchmatmul 调用被注释（旁注 [CANNOT-REPLACE]），改为 torch.ops.npu_test.npu_quant_batch_matmul，该调用点受 `if self.mm_quant_mode == "w8a8mxfloat8":` 守卫，而 mm_quant_mode 在 quant_config 为 None 时默认 "w16a16"；模型仓库的 YAML/JSON 中均检索不到 mm_quant_mode/w8a8mxfloat8，当前配置下该量化路径未被触发，替换日志自然缺失。


## 探针与操作

1) 全仓 grep "ATEN-REPLACE"/"KERNEL-REPLACE" 与 "QuantBatchMatmulV3|quant_batch_matmul"，确认打印来源与调用点分布。
2) 读 set_env.sh 与构建产物清单（libcustom_ops/CMakeLists.txt、ops_config.yaml），确认算子是否编译进 .so。
3) grep 模型目录 *.py/*.yaml/*.json 中 mm_quant_mode/w8a8mxfloat8/quant_config，确认量化分支的实际取值路径。

## 机制与判别

机制与判别：
- 打印由算子实现自身产生（torch 绑定打印 ATEN-REPLACE；kernel 入口 AscendC::printf 打印 KERNEL-REPLACE，且仅 GetBlockIdx()==0 时输出）→ 消息缺失首先指向调用未发生，而非日志级别/环境变量问题。
- 调用点为 namespace 策略（手动改 torch.ops.npu_test.npu_quant_batch_matmul，注释旁标注 [CANNOT-REPLACE]），受 mm_quant_mode=="w8a8mxfloat8" 守卫；quant_config 为 None 时默认 w16a16，仓库 YAML/JSON 均无该键 → 量化路径未触发。

关键原文工件：

工件：

```text
6: extern "C" __global__ __vector__ void quant_batch_matmul_v3_kernel(
7:     GM_ADDR output_gm, GM_ADDR tiling_gm)
8: {
9:     if (AscendC::GetBlockIdx() == 0) {
10:         AscendC::printf("[KERNEL-REPLACE] QuantBatchMatmulV3 kernel called\n");
11:     }
12: }
```

工件：

```text
5: TORCH_LIBRARY_FRAGMENT(npu_test, m) {
6:     m.def(
7:         "npu_quant_batch_matmul("
8:         "Tensor x, "
9:         "Tensor weight, "
10:         "Tensor scale, "
11:         "Tensor? offset=None, "
12:         "Tensor? pertoken_scale=None, "
13:         "Tensor? bias=None, "
14:         "bool transpose_x=False, "
15:         "bool transpose_weight=False, "
16:         "ScalarType? output_dtype=None, "
17:         "ScalarType? scale_dtype=None, "
18:         "ScalarType? pertoken_scale_dtype=None, "
19:         "int[] group_sizes=[]"
20:         ") -> Tensor");
21: }
22:
23: TORCH_LIBRARY_IMPL(npu_test, PrivateUse1, m) {
24:     m.impl("npu_quant_batch_matmul", TORCH_FN(ascend_kernel::npu_quant_batch_matmul_torch));
25: }
```

## 验证信号

验证层级：source_read（静态代码/配置核对；本会话在读取 ops_replacement 配置后结束，未输出最终结论，也未复跑推理验证）。
- 历史运行输出（moererounting_stdout.log:175-185,228-229）证明两类打印的正常形态。
- kernel 入口与注册代码原文见下方工件。

## 适用与失效边界

适用：deepseek-v4 量化分支/算子替换打印缺失的第一轮定界。
边界：
- 未读取实际加载权重目录中的 config.json，mm_quant_mode 的最终取值未 100% 闭合（存在权重侧 quant_config 注入的可能）；引用本卡时需先核对实际加载的模型配置。
- AscendC kernel printf 的输出通道受运行配置影响（如 dump/日志级别），本卡结论限定于"调用点未执行"这一最强解释。
- 会话未交付最终结论，本卡由轨迹内客观证据链重构。
