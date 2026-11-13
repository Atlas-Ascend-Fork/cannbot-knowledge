---
{
  "type": "Runbook",
  "title": "recipe_kimi-k2_quant0 32P 推理失败首报错：CANN 自定义算子库 dlopen GLIBCXX_3.4.29 缺失",
  "description": "kimi-k2 quant0 大规格 recipe（in3968/out128/gbs128/ep64/embtp16/lmhtp16/32P/ckpt0/eplb1/superkernel0，4 节点 × 16 卡 = 64 rank，Ascend910B 平台 version=A3，CANN 9.1.0）执行失败（fail|func、case_acc: F、NPU Util AVG=0.0），首报错为 CANN 自定义算子库 dlopen 时 GLIBCXX_3.4.29 not found。",
  "tags": [
    "task.debugging",
    "topic.model_serving"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": [
    "a2",
    "a3"
  ]
}
---
# recipe_kimi-k2_quant0 32P 推理失败首报错：CANN 自定义算子库 dlopen GLIBCXX_3.4.29 缺失

## 适用场景

- kimi-k2 quant0 大规格 recipe（in3968/out128/gbs128/ep64/embtp16/lmhtp16/32P/ckpt0/eplb1/superkernel0，4 节点 × 16 卡 = 64 rank，Ascend910B 平台 version=A3，CANN 9.1.0）执行失败（fail|func、case_acc: F、NPU Util AVG=0.0）。

## 触发与观测

- 首报错：

> 首报错信息（2026-07-31 02:13:56）：`[ERROR] Failed to load grouped_broadcast_custom library '/usr/local/Ascend/cann-9.1.0/opp/vendors/grouped_broadcast_custom/op_proto/lib/linux/aarch64//libcust_opsproto_rt2.0.so' via dlopen. Error detail: /usr/lib64/libstdc++.so.6: version 'GLIBCXX_3.4.29' not found`（op_impl/tbe/op_tiling 的 libcust_opmaster_rt2.0.so 同样报错）。

## 探针与操作

- rca-tools 7 步流水线（Windows）：环境检查 → 问题分类（规则快路径 RULE_ENV_ERROR）→ 组件分析 → 报告生成；execute_log 按节点/rank 枚举。
- rca-server 批量任务（Linux）：同日志目录的双分析器（non-cann-analyzer + hccl-analyzer）产出 ANALYSIS_RESULT JSON；workflow/engine 的 _unwrap 结构核验。

## 机制与判别

- 错误传播链（原文，机制单元）：

```
2026-07-31 02:13:56 [Env] GLIBCXX_3.4.29 not found → CANN自定义算子库dlopen失败
    → 2026-07-31 02:14:02 [App] 模型加载阶段HCCL通信组注册异常
    → 2026-07-31 02:33:17 [HCCL] socket establish timeout (1200s超时)
    → 2026-07-31 02:34:24 [App] UnicodeDecodeError + ERR99999
    → 2026-07-31 03:04:34 [App] DistStoreError: 32/64 clients joined
    → 任务失败: fail|func, case_acc: F
```

## 验证信号

- 产出物：`01_info_check.md (3808 bytes) 02_classification.md (7436 bytes) 03_non-cann_analysis.md (9150 bytes) recipe_...-DEBUG-REPORT.md (11595 bytes)`；Linux 侧报告 30002 bytes 落盘于指定 output_path。
- validation_scope：source_read + static_check（离线日志定界；两条独立流水线结论互相印证）。

## 适用与失效边界

- 失效边界：本卡仅保留首报错原文与传播链工件；逐主机定界、wave 时间线与修复结论未纳入本候选（定界/主机分布/wave 时间线/独立缺陷候选/修复建议各小节为空，相关断言未获采纳）。
