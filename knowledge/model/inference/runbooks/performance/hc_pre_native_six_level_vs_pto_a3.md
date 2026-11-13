---
{
  "type": "Runbook",
  "title": "PR#1211 hc_pre 原生六档 vs PTO 的 A3 复现",
  "description": "cann-recipes-infer PR（hc_pre 原生 AscendC 六档实现）在非验收硬件（A3/CANN 9.0.0）上复现性能与精度对比、评估 PTO/静态直调形态的场景。",
  "tags": [
    "task.testing",
    "topic.performance.analysis"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": [
    "a3"
  ]
}
---
# PR#1211 hc_pre 原生六档 vs PTO 的 A3 复现

## 适用场景
cann-recipes-infer PR（hc_pre 原生 AscendC 六档实现）在非验收硬件（A3/CANN 9.0.0）上复现性能与精度对比、评估 PTO/静态直调形态的场景。

## 触发与观测
本机为 Ascend910_93(A3) + CANN 9.0.0，需构建适配后以分进程 msprof 口径复测。

## 探针与操作
1) 构建：-c ascend910b 的包在 A3 加载报 161001 PARAM_NULLPTR → 改 -c ascend910_93；CANN 9.0.0 缺 ascend910_93 soc 映射 → PYTHONPATH sitecustomize.py shim 补映射。
2) 测量协议见工件（msprof --ascendcl=on --task-time=l1 --ai-core=on --aic-mode=task-based --type=text; HC_PRE_WARMUP=200 HC_PRE_MEASURE=3; op_summary 末3 Task Duration 中位）。
3) 静态直调：编译期固定 T 的 hc_pre_static_T* 二进制直接调用；PTO 静态 = PTO ISA 直调 verbatim 生成核（pto_generated/hc_*.cpp，依赖 pto-isa-327c）。

## 机制与判别
快路门控要求 24 AIC、至少 48 AIV，SoC Ascend910B/Ascend910_93，x 为 BF16 [B,S,4,4096]、weight FP32 [24,16384]。

机制片段：
```
"protocol": "msprof --ascendcl=on --task-time=l1 --ai-core=on --aic-mode=task-based --type=text; HC_PRE_WARMUP=200 HC_PRE_MEASURE=3; op_summary 末3 Task Duration 中位（2:5 取 AB 两轮 r1a 均值）"
```

## 验证信号
6 例初测与 14 例补全的分进程 msprof 表均为工具执行输出/报告产物。

## 适用与失效边界
结论需在「A3 + CANN 9.0.0」语境下解读：PR 保持草稿状态、最终达标以分进程口径为准；A5 分支未上板。

## 结论与证据边界
- PR#1211（hc_pre 原生六档实现）在本机 Ascend910_93(A3)+CANN 9.0.0 的复现适配：按 README -c ascend910b 构建的包在 A3 上加载报 161001 PARAM_NULLPTR，改用 -c ascend910_93 重建；CANN 9.0.0 工具链缺 ascend910_93 soc 映射，用 PYTHONPATH 的 sitecustomize.py shim 补映射后构建通过；对比口径为分进程 msprof、op_summary 末 3 次 Task Duration 中位数
