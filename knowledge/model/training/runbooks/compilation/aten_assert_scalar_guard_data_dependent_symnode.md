---
{
  "type": "Runbook",
  "title": "torch.compile 图追踪下符号尺寸校验用 aten::_assert_scalar 替代 Python if 分支（修复 GuardOnDataDependentSymNode）",
  "description": "torchtitan-npu DeepSeek V4 compressor 的 if length % ratio: Python 分支在 make_fx 符号化追踪下需对无来源 SymInt（u0）求值 Ne(Mod(u0,4),0)，Dynamo 建不出 guard 抛 GuardOnDataDependentSymNode。修复：length 为 torch.SymInt 时改发 torch.ops.aten._assert_scalar.default 断言（避免Python分支求值的源码方案；尚未核对目标编译产物中的运行时行为），eager 路径保留 raise ValueError。",
  "tags": [
    "task.implementation",
    "topic.compilation"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-13T02:13:38Z",
  "platforms": []
}
---
# torch.compile 图追踪下符号尺寸校验用 aten::_assert_scalar 替代 Python if 分支（修复 GuardOnDataDependentSymNode）


## 适用场景

torchtitan-npu DeepSeek V4 compressor 的 if length % ratio: Python 分支在 make_fx 符号化追踪下需对无来源 SymInt（u0）求值 Ne(Mod(u0,4),0)，Dynamo 建不出 guard 抛 GuardOnDataDependentSymNode。修复：length 为 torch.SymInt 时改发 torch.ops.aten._assert_scalar.default 断言（设计上避免Python分支求值；目标编译产物是否保留运行时校验尚未核对），eager 路径保留 raise ValueError。

## 触发与观测


来源结论：

torchtitan_npu/models/deepseek_v4/compressor.py 的 Compressor._forward 中 if length % ratio: Python 分支在 graph trainer 的 make_fx 符号化追踪下需对无来源 SymInt（u0）求值 Ne(Mod(u0, 4), 0)，Dynamo 建不出 guard 抛 GuardOnDataDependentSymNode: Could not guard on data-dependent expression；修复为 length 是 torch.SymInt 时改发 torch.ops.aten._assert_scalar.default(length % ratio == 0, <原 ValueError 消息文案>) 断言节点，eager 路径保留原 raise ValueError 行为逐字不变。

## 探针与操作


来源改动节选：代码注释中的运行时保证已改为待验证意图；这是diff上下文，不是完整函数。

```
@@ -177,7 +177,17 @@ class Compressor(Module):
         if x.dim() != 3 or x.size(0) != 1:
             raise ValueError(f"the compressor addresses one packed row, got shape {tuple(x.shape)}.")
         length = x.size(1)
-        if length % ratio:
+        # A Python branch on a symbolic size would force a data-dependent guard that cannot be
+        # evaluated for an unbacked symbol. Emit a scalar assertion instead; this change
+        # intends to preserve the check; target compiled runtime behavior is unverified.
+        if isinstance(length, torch.SymInt):
+            torch.ops.aten._assert_scalar.default(
+                length % ratio == 0,
+                f"the local stream is not a whole number of compression blocks of ratio {ratio}: "
+                "documents are aligned by `dataloader.per_doc_alignment`, and the CP wrapper's "
+                "augmented stream adds whole blocks.",
+            )
+        elif length % ratio:
             raise ValueError(
                 f"the local stream ({length} tokens) is not a whole number of compression blocks "
                 f"of ratio {ratio}: documents are aligned by `dataloader.per_doc_alignment`, and "
```

## 机制与判别

本卡机制与判别并入『触发与观测』来源结论：与『探针与操作』登记机制片段：（修复 diff 补丁）。

## 验证信号


来源核对了 SymInt 分支生成 `_assert_scalar`、eager 分支保留 ValueError 的实现与 CPU 参考检查。8 卡 20 步端到端训练没有进入采用证据，不能声称该范围已通过。编译器是否将断言保留为预期运行时行为仍需目标编译产物与设备执行核对。

## 适用与失效边界

适用：torch.compile/make_fx 符号化追踪下对动态尺寸做合法性校验的代码（torchtitan/torchair 类 repo）。失效边界：仅验证 SymInt 路径发断言、eager 保留 ValueError 的分支形态；完全合并（去掉 elif）会把用户可见异常从 ValueError 变为 RuntimeError，与该仓 CLAUDE.md 约定冲突（用户未拍板）；8 卡 20 步端到端训练验证未进入账本证据，不得据本卡宣称。validation_scope: 源码修改与 CPU 参考检查；未验证端到端训练。
