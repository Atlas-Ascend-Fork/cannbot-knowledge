---
{
  "type": "Runbook",
  "title": "CustomPass 替换 MatMulV3 后 op_summary 缺失：FE 覆写裸 MIX + DoProf 未覆盖 launch node",
  "description": "nz_weight_pass 将 MatMulV2 替换为 MatMulV3（x2 转 FRACTAL_NZ）后，task_time.csv 有 te_matmulv3 记录但 op_summary.csv 缺失。两条机制：一是 FE 的 OpImplTypeJudge 从算子 kernel info 读 core_type 无条件覆写 _cube_vector_core_type 为裸 \"MIX\"，而 exe_graph_serializer.cc 的 task_type_str_to_int 只含 AIV/MIX_AIC/MIX_AIV/AI_CORE/AI_CPU，裸 MIX 查找失败置 UINT32_MAX 并告警 Unsupported task type MIX；",
  "tags": [
    "task.debugging",
    "topic.performance.analysis"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": []
}
---
# CustomPass 替换 MatMulV3 后 op_summary 缺失：FE 覆写裸 MIX + DoProf 未覆盖 launch node

## 适用场景

nz_weight_pass 将 MatMulV2 替换为 MatMulV3（x2 转 FRACTAL_NZ）后，task_time.csv 有 te_matmulv3 记录但 op_summary.csv 缺失。两条机制：一是 FE 的 OpImplTypeJudge 从算子 kernel info 读 core_type 无条件覆写 _cube_vector_core_type 为裸 "MIX"，而 exe_graph_serializer.cc 的 task_type_str_to_int 只含 AIV/MIX_AIC/MIX_AIV/AI_CORE/AI_CPU，裸 MIX 查找失败置 UINT32_MAX 并告警 Unsupported task type MIX；二是 DoProf 43 次调用 node_id 最大 949，未覆盖 MatMulV3 的 launch node 952+，node basic info 未上报 msprof。

适用于通过 CustomPass（如 nz_weight_pass）把图中 MatMul/MatMulV2 替换为 MatMulV3（权重 ND→FRACTAL_NZ 重排）后，msprof profiling 采集出现 task_time.csv 有 kernel 记录但 op_summary.csv 缺算子、且伴随 Unsupported task type MIX warning 的场景。

## 触发与观测

warning 日志：[exe_graph_serializer.cc:176] SerializeDfxExtendInfo:Unsupported task type MIX. node name is MatMul_96/v2_v3；op_summary.csv 无 MatMulV3 而 task_time.csv 有 te_matmulv3。

### 结论与证据边界

CustomPass 将 MatMulV2 替换为 MatMulV3 后 op_summary.csv 缺失该算子而 task_time.csv 有 te_matmulv3 kernel 执行记录，直接原因是 DoProf 未被调用到 MatMulV3 的 launch node：日志中 43 次 DoProf 调用 node_id 最大到 949，而 InitNameAndTypeWithHash 显示 node_id 952（node_name MatMulV2_v3，node_type MatMulV3）等才是 MatMulV3 的 LaunchKernelWithHandle 节点，node basic info 未上报 msprof，硬件 task 数据无法关联到 op name/type。

### 结论与证据边界

序列化侧 warning 的机制：FE 在子图优化阶段（tbe_json_parse.cc ProcMixCoreType 早返回未细化 + op_impl_type_judge.cc 无条件覆写）把 MatMulV3 的 _cube_vector_core_type 置为裸 "MIX"（日志 GetCoreType: Get attr: _cube_vector_core_type of op[MatMulV2_v3, MatMulV3] is MIX），而 runtime/v2 exe_graph_serializer.cc 的 task_type_str_to_int 映射表只含 AIV/MIX_AIC/MIX_AIV/AI_CORE/AICPU 五键，裸 MIX 查找失败 task_type 置 UINT32_MAX 并触发 SerializeDfxExtendInfo:Unsupported task type MIX. node name is MatMul_96/v2_v3；运行时 InitNodeContextInfo 经 FFTS+ 路径仍正确识别 prof task type:4 (MIX_AIC)，说明仅序列化阶段属性值传递断裂，不影响算子执行。

## 探针与操作

1) grep 业务日志 InitNameAndTypeWithHash 找各算子 launch node_id（MatMulV2_v3 的 LaunchKernelWithHandle node_id 952/968/1006/1029/1071…）；2) grep DoProf 统计调用次数与最大 node_id（43 次、最大 949）；3) 读 ge/runtime/v2/lowering/exe_graph_serializer.cc 的 task_type_str_to_int；4) 读 op_impl_type_judge.cc / tbe_json_parse.cc ProcMixCoreType 与算子 binary json（其中无 core_type）；5) 对比同为 MIX 的 FusedInferAttentionScore 为何出现在 op_summary（FFTS+ 路径经 _mix_is_aiv 直接设 engine_type）。

## 机制与判别

见上方结论原文与下方机制片段；判别性证据与边界适用讨论见“适用与失效边界”节。

### 补充机制片段

```
35: const std::unordered_map<std::string, MsprofGeTaskType> task_type_str_to_int = {
36:     {ge::kTaskTypeAiv, MSPROF_GE_TASK_TYPE_AIV},
37:     {ge::kTaskTypeMixAic, MSPROF_GE_TASK_TYPE_MIX_AIC},
38:     {ge::kTaskTypeMixAiv, MSPROF_GE_TASK_TYPE_MIX_AIV},
39:     {ge::kTaskTypeAicore, MSPROF_GE_TASK_TYPE_AI_CORE},
40:     {ge::kTaskTypeAicpu, MSPROF_GE_TASK_TYPE_AI_CPU}};
```

### 补充机制片段

```
62: static std::vector<uint8_t> ConvertNdToFractalNz(const uint8_t *src,
63:                                                   int64_t k_dim, int64_t n_dim, int64_t elem_size) {
64:     int64_t K1 = (k_dim + 15) / 16;
65:     int64_t N1 = (n_dim + 15) / 16;
66:     size_t nz_size = static_cast<size_t>(N1 * K1 * 16 * 16) * static_cast<size_t>(elem_size);
67:     std::vector<uint8_t> nz_data(nz_size, 0);
68:     for (int64_t n1 = 0; n1 < N1; n1++) {
69:         for (int64_t k1 = 0; k1 < K1; k1++) {
70:             for (int64_t r = 0; r < 16; r++) {
71:                 int64_t sk = k1 * 16 + r;
72:                 if (sk >= k_dim) break;
73:                 for (int64_t c = 0; c < 16; c++) {
74:                     int64_t sn = n1 * 16 + c;
75:                     if (sn >= n_dim) break;
76:                     size_t src_off = static_cast<size_t>(sk * n_dim + sn) * static_cast<size_t>(elem_size);
77:                     size_t dst_off = static_cast<size_t>(((n1 * K1 + k1) * 16 + r) * 16 + c) * static_cast<size_t>(elem_size);
78:                     std::memcpy(&nz_data[dst_off], src + src_off, static_cast<size_t>(elem_size));
79:                 }
80:             }
81:         }
82:     }
83:     return nz_data;
84: }
```

## 验证信号

各层观测均为日志/源码客观证据：bg_core_type.cc GetCoreType: _cube_vector_core_type of op[MatMulV2_v3, MatMulV3] is MIX；cann_profiler_v2.cc InitNodeContextInfo: Op(MatMulV2_v3) prof task type:4, is fftsplus task:1（运行时识别正确）。

## 适用与失效边界

适用：GE fast_v2 执行图 + msprof 链路。判别要点：问题不影响算子执行与调度，仅 profiling 数据关联断裂。局限：修复方向（更晚 pass 阶段设置属性、或序列化层补 MIX 键、或让 DoProf 覆盖 952+ launch node）均为分析建议，轨迹内未实施验证；pass 侧设置 "AiCore" 还存在值不匹配问题（表中键为 AI_CORE/MIX_AIC 全大写形式）。
