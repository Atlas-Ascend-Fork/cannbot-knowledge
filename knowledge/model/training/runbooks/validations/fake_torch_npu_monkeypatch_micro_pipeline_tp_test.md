---
{
  "type": "Runbook",
  "title": "无 NPU 环境下 monkeypatch 假 torch_npu 验证 micro_pipeline_tp 融合算子入参的单元测试模式",
  "description": "torchtitan-npu micro_pipeline_tp 融合算子 PR 的无 NPU 回归验证模式，让 CPU 开发机也能锁定 NPU 融合算子的入参转发与 fail-fast 行为契约。",
  "tags": [
    "task.implementation",
    "topic.graph_execution"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T12:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": []
}
---
# 无 NPU 环境下 monkeypatch 假 torch_npu 验证 micro_pipeline_tp 融合算子入参的单元测试模式

无 NPU 环境下可用 monkeypatch 伪造 torch_npu 模块，在 CPU 上验证 micro_pipeline_tp 融合算子的入参转发与 fail-fast 契约。本卡记录测试实现与运行方式。

## 适用场景

torchtitan-npu patch/融合算子行为契约的无 NPU 回归验证场景：开发机无 NPU 卡时为 PR（如 #405/issue#63）补单测并跑通 pytest；适用于 micro_pipeline_tp 类融合算子的入参传递与 fail-fast 行为验证。route=training，area=validations。

## 触发与观测

触发：PR#405 需要填写『如何测试』并以可复现命令/截图佐证；开发机（Windows、仅 CPU torch）无法直连 NPU。

## 探针与操作

测试实现：

```
from types import SimpleNamespace

import pytest
import torch

from torchtitan_npu.patches.torch import micro_pipeline_tp


def _install_fakes(monkeypatch):
    captured: dict = {}

    def fake_npu_mm_reduce_scatter_base(A_flat, B, hcom, world_size, *, reduce_op):
        captured["reduce_op"] = reduce_op
        captured["world_size"] = world_size
        return torch.randn(3, 5)

    monkeypatch.setattr(
        micro_pipeline_tp,
        "c10d",
        SimpleNamespace(_resolve_process_group=lambda group_name: SimpleNamespace(size=lambda: 2)),
    )
    monkeypatch.setattr(micro_pipeline_tp, "_get_hccl_comm_name", lambda group_name: "fake_hcom")
    monkeypatch.setattr(
        micro_pipeline_tp,
        "torch_npu",
        SimpleNamespace(npu_mm_reduce_scatter_base=fake_npu_mm_reduce_scatter_base),
    )
    return captured


def test_fused_matmul_reduce_scatter_forwards_sum_reduce_op(monkeypatch):
    captured = _install_fakes(monkeypatch)
    A = torch.randn(6, 4)
    B = torch.randn(4, 5)

    micro_pipeline_tp._npu_kernel_fused_matmul_reduce_scatter(
        A, B, "sum", scatter_dim=0, group_name="fake_group"
    )

    assert captured["reduce_op"] == "sum"
    assert captured["world_size"] == 2


def test_fused_matmul_reduce_scatter_rejects_non_sum_reduce_op(monkeypatch):
    captured = _install_fakes(monkeypatch)
    A = torch.randn(6, 4)
    B = torch.randn(4, 5)

    with pytest.raises(NotImplementedError, match="reduce_op='sum'"):
        micro_pipeline_tp._npu_kernel_fused_matmul_reduce_scatter(
            A, B, "avg", scatter_dim=0, group_name="fake_group"
        )

    assert captured == {}
```


运行命令：pytest tests/unit_tests/patches/test_micro_pipeline_tp.py -v；为让 torchtitan_npu.patches 可导入，本机临时伪造 torch_npu 模块（fake __init__.py），测试后清理。

## 机制与判别

无 NPU 环境下可用 monkeypatch + SimpleNamespace 伪造 torch_npu 模块在 CPU 上验证 micro_pipeline_tp 融合算子的入参传递契约：fake npu_mm_reduce_scatter_base 捕获 reduce_op/world_size，test_fused_matmul_reduce_scatter_forwards_sum_reduce_op 断言 reduce_op == 'sum' 与 world_size == 2 被正确转发，test_fused_matmul_reduce_scatter_rejects_non_sum_reduce_op 断言非 sum 触发 NotImplementedError 且 captured 为空（底层算子未被调用）；在本机伪造 torch_npu 模块后 pytest 2 passed（0.01s）。


机制：monkeypatch.setattr 把模块内引用（c10d、_get_hccl_comm_name、torch_npu）替换为 SimpleNamespace 假件，使 _npu_kernel_fused_matmul_reduce_scatter 在纯 CPU 环境执行到『组 NPU 算子入参拼装』这一层，从而断言 reduce_op/world_size 的转发与非 sum 的 fail-fast。

## 验证信号

验证信号：pytest 2 passed（test_fused_matmul_reduce_scatter_forwards_sum_reduce_op PASSED / test_fused_matmul_reduce_scatter_rejects_non_sum_reduce_op PASSED，0.01s）。

## 适用与失效边界

边界：伪造 torch_npu 只覆盖被 patch 模块的符号解析，不验证真实 NPU 算子语义/数值（不等于设备级验证）；契约范围是入参转发与 fail-fast，不含反向/多卡一致性；若 micro_pipeline_tp 后续新增对 torch_npu 其他符号的引用需同步扩展 fake；测试可在 CI（有 NPU）与本地（无 NPU）双跑，本地结果即 2 passed。
