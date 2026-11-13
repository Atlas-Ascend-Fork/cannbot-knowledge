---
{
  "type": "Runbook",
  "title": "Deepseek v2 lite inductor+af 融合 kernel retCode=0x31 vector core 异常定位：expand 广播维在 concat 输入 layout 中 stride 未置 0 导致越界读",
  "description": "torchair 的 inductor NPU 扩展（inductor_npu_ext，auto fusion/autofuser）把 aten.cat+aten.expand+convert_element_type 融合成单 kernel（DeepSeek v2 lite 开箱即用时触发）。",
  "tags": [
    "task.debugging",
    "topic.compilation"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": []
}
---
# Deepseek v2 lite inductor+af 融合 kernel retCode=0x31 vector core 异常定位：expand 广播维在 concat 输入 layout 中 stride 未置 0 导致越界读

## 适用场景

torchair 的 inductor NPU 扩展（inductor_npu_ext，auto fusion/autofuser）把 aten.cat+aten.expand+convert_element_type 融合成单 kernel（DeepSeek v2 lite 开箱即用时触发）。

> 验证层级：source_read + static_check（修复 edit 落盘；用户中间态复跑确认，全量回归未在轨迹内完成）

## 触发与观测

融合 kernel autofused_to_copy_cat_expand 执行报 Vector Core kernel execution failed retCode=0x31（[vector core exception]），IDEDD dump MTE_ERROR_T0_0=0x80000000、多 core 故障 PC 固定 +0x34c——典型的越界读地址错。

## 探针与操作

1) 读报错 kernel 的 asc_graph.py：对比 op 输出 buffer 的物理 layout（buf95_layout size=[1,1,21,64] stride=[1344,1,64,1]）与 ascir 构造（load1.y.size=[1,16,21,64]）——物理与逻辑 size 失配且 stride 非零。2) 读 error.log 确认 aicore dump。3) 读 fusion codegen 的 _concat_input_layout：物理 size≠逻辑（展开）size 时直接 return fallback_layout。4) 修复后用用户提供的复现（DeepSeek v2 lite）+ 既有 cat 相关测试（test_cat_with_slice_input）回归。

## 机制与判别

修复单元（_concat_input_layout 广播维 stride=0 构造）：


```
    def _concat_input_layout(self, name: str, fallback_layout):
        try:
            layout = V.graph.get_buffer(name).layout
        except Exception:
            return fallback_layout
        if len(layout.size) != len(fallback_layout.size):
            return fallback_layout
        if all(
            self._same_size(
                V.graph.sizevars.simplify(actual),
                V.graph.sizevars.simplify(expect),
            )
            for actual, expect in zip(layout.size, fallback_layout.size)
        ):
            return layout
        # Physical size != logical (expanded) size: some dims are broadcast
        # (e.g. aten.expand). Use the expanded size but zero out stride for
        # broadcast dims so the Load reads the physical buffer correctly and
        # a Broadcast op is generated to expand the dimension.
        stride = []
        for phys_s, exp_s, phys_st in zip(layout.size, fallback_layout.size, layout.stride):
            if self._same_size(
                V.graph.sizevars.simplify(phys_s),
                V.graph.sizevars.simplify(exp_s),
            ):
                stride.append(phys_st)
            else:
                stride.append(sympy.Integer(0))
        return FixedLayout(
            device=layout.device,
            dtype=layout.dtype,
            size=list(fallback_layout.size),
            stride=stride,
            offset=layout.offset,
        )
```

## 验证信号

验证信号（error.log/asc_graph 客观记录 + 修复 edit 落盘）：

  - 客观信号：
- 判别：_concat_input_layout 在物理 size 与逻辑（展开）size 不一致时（aten.expand 广播输入）直接返回带错误连续 stride 的 fallback，广播语义丢失；正确做法是逐维判断——phys==exp 的维用物理 stride、广播维（phys≠exp）置 stride=0，size 用展开后 size、offset 保留物理 offset，Load 按物理 buffer 安全读取、Broadcast op 负责展开。
  - 客观信号：
## 适用与失效边界

适用：inductor+af 下 concat 输入含 aten.expand 广播维的融合 kernel 越界（retCode=0x31/MTE 异常）定位与修复。失效/边界：本轨迹内修复已应用并经用户中间态复跑确认 Load/Broadcast 行为正确，但最终全量回归的运行结果未在轨迹内捕获。
