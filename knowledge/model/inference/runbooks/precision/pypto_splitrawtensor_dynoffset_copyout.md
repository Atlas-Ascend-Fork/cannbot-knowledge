---
{
  "type": "Runbook",
  "title": "PyPTO 算子精度失败的 pass 级定位：SplitRawTensor UpdateDynOffset 无条件减法根因",
  "description": "PyPTO 算子精度失败的 pass 级定位：根因 Pass_08 SplitRawTensor 的 staged 改动把 UpdateDynOffset 从条件减法改为无条件减法、SplitLogicalTensor 末尾保留 rebased 动态 offset，错误 offset 传播到 CopyOutResolve。",
  "tags": [
    "task.debugging",
    "topic.precision"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": []
}
---
# PyPTO 算子精度失败的 pass 级定位：SplitRawTensor UpdateDynOffset 无条件减法根因

> 验证层级：device_functional（真机复现 + 检查点/dump 图分析；修复仅给方向，本轨迹不修）

## 适用场景

PyPTO 编译器管线上的算子精度失败，且精度工具（只校验计算 op）无法定位问题的场景。特征是：计算路径检查点全部正确，但最终输出大面积为零/错位。本例为 deepseekv32 lightning indexer prolog quant（test_b4_s1_2_s2_64k，b=4, s1=2, s2=64k, t=8）。

## 触发与观测

- 触发：PyPTO 编译器管线上的算子精度失败（本例见适用场景）。

## 探针与操作

1. **pass 级 dump 图对比**：读取 output dump（computation_graph/Strategy_01_PVC2_OOO/ 各 Pass 的 Before/After JSON），定位 staged 改动的 Pass（本例 Pass_08 SplitRawTensor）并审查其 offset 处理逻辑。

## 机制与判别

- 源码变化与诊断：`根因 Pass：Pass_08 SplitRawTensor（split_raw.cpp 的 staged 改动）。staged 改动将 UpdateDynOffset 从条件减法改为无条件减法（旧代码 if (offset[i] >= diff[i]) result[i] = offset[i] - diff[i]，新代码 result[i] = (lhs[i] - rhs[i]).Simplify()），同时 SplitLogicalTensor 末尾从全部置零改为保留 rebased 动态 offset，导致后续 Pass（特别是 Pass_27 InferDynShape）基于错误 offset 推导。` staged 改动 diff（完整机制单元）：


```
-std::vector<int64_t> SplitRawTensor::UpdateOffset(std::vector<int64_t>& offset, const std::vector<int64_t>& diff) const
+Status SplitRawTensor::UpdateDynOffset(const std::vector<int64_t>& offset, const std::vector<SymbolicScalar>& dynOffset,
+                                       const TensorOffset& diff, std::vector<SymbolicScalar>& result) const
 {
-    std::vector<int64_t> result = offset;
-    for (size_t i = 0; i < offset.size(); i++) {
-        if (offset[i] >= diff[i]) {
-            result[i] = offset[i] - diff[i];
-        }
+    if (offset.size() != diff.GetOffset().size()) {
+        APASS_LOG_ERROR_F(Elements::Tensor, "Cannot rebase offset with different dimensions: %zu and %zu.",
+                          offset.size(), diff.GetOffset().size());
+        return FAILED;
     }
-    return result;
-}
-
-std::vector<SymbolicScalar> SplitRawTensor::UpdateDynOffset(std::vector<SymbolicScalar>& offset,
-                                                            const std::vector<SymbolicScalar>& diff) const
-{
-    std::vector<SymbolicScalar> result = offset;
-    for (size_t i = 0; i < offset.size(); i++) {
-        if (offset[i] >= diff[i]) {
-            result[i] = offset[i] - diff[i];
-        }
+    if (dynOffset.empty() && diff.GetDynOffset().empty()) {
+        result.clear();
+        return SUCCESS;
     }
-    return result;
+    auto lhs = dynOffset.empty() ? SymbolicScalar::FromConcrete(offset) : dynOffset;
+    auto rhs = diff.GetDynOffset().empty() ? SymbolicScalar::FromConcrete(diff.GetOffset()) : diff.GetDynOffset();
+    if (lhs.size() != rhs.size()) {
+        APASS_LOG_ERROR_F(Elements::Tensor, "Cannot rebase dynamic offset with different dimensions: %zu and %zu.",
+                          lhs.size(), rhs.size());
+        return FAILED;
+    }
+    result.clear();
+    result.reserve(lhs.size());
+    for (size_t i = 0; i < lhs.size(); i++) {
+        result.emplace_back((lhs[i] - rhs[i]).Simplify());
+    }
+    return SUCCESS;
 }
```


## 验证信号

- 客观信号：Pass_08 SplitRawTensor 的 staged 改动 diff。
- 修复方向（未实施）：SplitLogicalTensor 末尾处理动态 offset 的逻辑需审查——logical tensor 被拆分获得独立 raw tensor 后，其动态 offset 应正确归零或 rebase；UpdateDynOffset 的无条件减法在 offset < diff 的维度会产生负值，需恢复条件守卫或确保所有场景下 offset >= diff 成立。


**来源记录与诊断解释**

- 根因 Pass：Pass_08 SplitRawTensor（split_raw.cpp 的 staged 改动）。staged 改动将 UpdateDynOffset 从条件减法改为无条件减法（旧代码 if (offset[i] >= diff[i]) result[i] = offset[i] - diff[i]，新代码 result[i] = (lhs[i] - rhs[i]).Simplify()），同时 SplitLogicalTensor 末尾从全部置零改为保留 rebased 动态 offset，导致后续 Pass（特别是 Pass_27 InferDynShape）基于错误 offset 推导。

## 适用与失效边界

- 适用：PyPTO 图 pass 管线上数据搬运 offset 类的精度问题定位。
- 失效/边界：本轨迹只做定位不做修复（任务要求先定位）；结论基于 dump 图静态对比，未做修复后回归验证；对非 SplitRawTensor 触发的同类症状（其他 pass 改 offset）需重新走 dump 图对比流程。
