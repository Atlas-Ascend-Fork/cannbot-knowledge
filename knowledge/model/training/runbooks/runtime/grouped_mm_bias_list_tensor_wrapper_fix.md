---
{
  "type": "Runbook",
  "title": "aten::_grouped_mm 的 NPU 实现中 npu_grouped_matmul 的 bias 必须包装为 List（Tensor）（PR#419）",
  "description": "torchtitan-npu 的 MoE grouped matmul 路径（torchtitan_npu/ops/_grouped_mm.py 把 torch_npu.npu_grouped_matmul 注册为 aten::_grouped_mm 的 PrivateUse1 实现）需要传入 bias 的场景。适用于「Ascend 接口按 List[Tensor] 约定、包装层传裸 Tensor」的潜伏类型 bug 修复。",
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
# aten::_grouped_mm 的 NPU 实现中 npu_grouped_matmul 的 bias 必须包装为 List（Tensor）（PR#419）

## 适用场景
torchtitan-npu 的 MoE grouped matmul 路径（torchtitan_npu/ops/_grouped_mm.py 把 torch_npu.npu_grouped_matmul 注册为 aten::_grouped_mm 的 PrivateUse1 实现）需要传入 bias 的场景。适用于「Ascend 接口按 List[Tensor] 约定、包装层传裸 Tensor」的潜伏类型 bug 修复。

## 触发与观测
- 触发：任务单指出位置 torchtitan_npu/ops/_grouped_mm.py:40、问题为 bias 应为 List[Tensor] 而当前传裸 Tensor；现有调用方多数传 None 所以是潜伏 bug。
- 观测：
  - torchtitan_npu/ops/_grouped_mm.py 的 aten::_grouped_mm PrivateUse1 实现把裸 Tensor 直接传给 torch_npu.npu_grouped_matmul 的 bias 参数，而按 Ascend 接口约定 bias 应为 List[Tensor]；现有调用方（MoE forward/grad 场景）多数传 None，所以是潜伏 bug，一旦真的传 bias 就会因类型不符出错。

## 探针与操作
- 修复前代码核对（_grouped_mm.py 原文，self/mat2 已是 List、bias 为裸 Tensor）。
- 修复后建议的 NPU 复现路径（任务单给出、本轨迹未执行）：bias=None 路径输出与修复前一致；bias 非 None 时执行成功，结果与参考 x @ w + bias 在容差内一致。
- PR 流程：fork + fix/grouped-mm-bias-list-type 分支 + 提交 + MR 描述模板。

## 机制与判别
- 修复前调用（完整机制单元，保留读取事件的行号前缀；注意 40 行 bias=bias 为裸 Tensor 而 [self]/[mat2] 为 List）：
```
33:     return torch_npu.npu_grouped_matmul(
34:         [self],
35:         [mat2],
36:         group_list=offs.to(dtype=torch.int64),
37:         group_list_type=0,
38:         split_item=2,
39:         group_type=(2 if split_along_k else 0),
40:         bias=bias,
41:         output_dtype=out_dtype,
42:     )[0]
```
- 判别：Ascend npu_grouped_matmul 的 x/w/bias 均按 per-group List 传参（文档约定）；包装层漏包 bias 属于签名不一致，None 路径不受影响。修复实施细节（bias 包装 edit）未进入本卡账本证据，登记机制片段：仅为修复前调用代码。

## 验证信号
- validation_scope: static_check + source_read（对照 Ascend 文档约定与源码结构核对；未做设备级验证）。

## 适用与失效边界
- 适用于所有走 aten::_grouped_mm PrivateUse1 且需 bias 的调用方；bias=None 主路径行为不变。
- 失效边界：修复实施与 NPU 实测未进入本卡账本证据，不得据本卡宣称；bias List 长度是否与 group 数另有约束需按 Ascend 文档逐项核对。
- 后续真实验证建议（由 1300dbe5 给出）：在 NPU 服务器以 --debug.seed=42 --debug.deterministic 跑 baseline(master) vs candidate(fix 分支) 90 步训练并 tee 日志后用 premerge-accuracy-check 对比。
