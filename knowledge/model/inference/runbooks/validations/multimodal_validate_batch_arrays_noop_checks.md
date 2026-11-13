---
{
  "type": "Runbook",
  "title": "多模态 index 校验的 no-op 与范围遗漏：反例、局部补丁及边界",
  "description": "来源反例显示仅统计 used 数量与组起点对齐，会放行超出 vision 行数的 128..191，或重复映射两个图像到同一段。连续序检查是局部补丁，还需独立范围与唯一映射验证；既有 39/200 测试通过不证明这些条件已完整覆盖。",
  "tags": [
    "task.testing",
    "topic.data_pipeline"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": []
}
---
# 多模态 index 校验的 no-op 与范围遗漏：反例、局部补丁及边界

## 适用场景


适用于多模态输入桥接层（multimodal.py validate_batch_arrays/build_multimodal_batch）存在校验放行漏洞的修复：index 越界（128..191 超 vision 128 行）、双图映射同一 slot 区间、非官方 row-major 唯一顺序等。

## 触发与观测
主 agent code review 指出漏洞；行为测试 test_batch_slot_pool_overflow_rejected（断言 ValueError）以 AssertionError: ValueError not raised 失败、test_valid_row_builds 断言 image_feature_index 映射错误失败，实证旧校验未拦截非法输入。

### 结论与证据边界

multimodal.validate_batch_arrays 的越界/映射漏洞（主 agent review 指出、行为测试证实）：旧实现含 no-op 占位检查 `if (index[:, lengths[0] * 0:][0:0]).size:  # placeholder no-op; real checks below\n        pass` 与 `if len(values) and (values == values[0]).all() is False:\n            pass`，index 填 128..191 时 used=64<=128 且组起点 128%64=0/连续检查均通过，但 vision 只有 128 行、index_select 会越界，双图都映射 0..63 也通过、违反官方 row-major 唯一顺序——test_batch_slot_pool_overflow_rejected 断言 ValueError not raised 失败、test_valid_row_builds 断言 image_feature_index 映射错误失败。

### 结论与证据边界

修复（models/startlux-decision-v1.1-0.8b-instant/multimodal.py）：删除两个 no-op 占位分支，改为真实校验——每个 image 组 values[0] 必须 % merged_per_image==0（slot 边界对齐）且 np.array_equal(values, np.arange(int(values[0]), int(values[0])+merged_per_image))（官方 masked_scatter 连续 run 顺序），配合同轮补充的 int 校验/严格 marker 校验与修正后的行为测试，tests.test_startlux_multimodal 39 tests OK、全量 test_startlux* 200 tests OK（此前 38 tests 2 failures）。

## 探针与操作
写真实反例行为测试（构造 index 填 128..191、双图 0..63 映射等非法 batch），python3 -m unittest tests.test_startlux_multimodal 全量跑，grep FAIL 定位；读 multimodal.py 的校验分支确认 no-op 占位检查。

## 机制与判别
见上方结论原文与下方机制片段；判别性证据与边界适用讨论见“适用与失效边界”节。

### 补充机制片段

```
    if (index[:, lengths[0] * 0:][0:0]).size:  # placeholder no-op; real checks below
        pass
    used = int((index >= 0).sum())
```

### 补充机制片段

```
            groups = _row_groups(valid_tokens.tolist(), image_token, vision_start,
                                 vision_end, merged_per_image)
            for k, (s, e) in enumerate(groups):
                values = index[b, s:e]
                if int(values[0]) % merged_per_image != 0:
                    raise ValueError(f"row {b} image group {k} does not start at a "
                                     f"slot boundary")
                if not np.array_equal(values, np.arange(int(values[0]),
                                                        int(values[0]) + merged_per_image)):
                    raise ValueError(f"row {b} image group {k} is not a contiguous "
                                     f"feature run in official masked_scatter order")
```

## 验证信号

来源报告局部补丁后 39 项以及更大集合 200 项测试通过，但所展示条件自身不拒绝 128..191 这个已知越界例，也不独立保证不同图像映射不重复。应保留并重新运行这些反例，绑定实际运行的 validator 与测试版本；不能从总 PASS 数推导已知漏洞均已修复。

## 适用与失效边界
适用：numpy index 数组校验场景——空切片（[:, 0:0]）的 .size 恒为 0，该 if 条件为假、(values==values[0]).all() is False 的短路写法都是无效检查的模式化识别。局部补丁要求每组连续且对齐，但这仍允许 start=128、长度64的越界段；还需核对每个 index 的实际范围，以及按契约应唯一的 slot 映射。局限：本候选只覆盖 validator 修复与 200 项测试回归；同轨迹的统一多模态 AIR 导出（CPU oracle/eager/export/realGE 全链）在轨迹结束时仍有未解决错误（OfficialBackendBridge.lane、KeyError 'ab' 等），不属本条范围。
