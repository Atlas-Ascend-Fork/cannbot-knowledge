---
{
  "type": "Runbook",
  "title": "torchtitan-npu deepseek_v4_flash 单卡 bring-up（8 卡改 1 卡）——四个跨层 bug 的定位与 import 期运行时绕过",
  "description": "torchtitan-npu 在新硬件/新环境（本例 Ascend950PR 回片 A5、CANN 9.0.1）上将多卡训练改单卡（1p、seq_len 2048、c4_test、5 步）时的 bring-up 排障：模型层零改动、全部修复收敛在 patches/extensions/ops 层并在 import 阶段激活。适用于区分「模型 bug」与「模型外各层（框架/上游/算子库/胶水层）bug」的分层排障范式。",
  "tags": [
    "task.debugging",
    "topic.graph_execution"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-13T02:13:38Z",
  "platforms": [
    "950"
  ]
}
---
# torchtitan-npu deepseek_v4_flash 单卡 bring-up（8 卡改 1 卡）——四个跨层 bug 的定位与 import 期运行时绕过

## 适用场景
torchtitan-npu 在新硬件/新环境（本例 Ascend950PR 回片 A5、CANN 9.0.1）上将多卡训练改单卡（1p、seq_len 2048、c4_test、5 步）时的 bring-up 排障：模型层零改动、全部修复收敛在 patches/extensions/ops 层并在 import 阶段激活。适用于区分「模型 bug」与「模型外各层（框架/上游/算子库/胶水层）bug」的分层排障范式。

## 触发与观测
- 触发：8 卡改单卡后 5 步训练连续崩挂四次，错误分别来自 CANN 算子库、torch 上游、仓库扩展、仓库 ops 四个层。
- 观测：
  - 坑1（CANN 算子层）：FSDP2 的 reduce-scatter copy-in（torch.ops.fsdp.chunk_cat，由 foreach_reduce 在 post_backward 调用，world_size=1 也触发）经 torch._chunk_cat 下沉到 aclnnChunkCat，在 CANN 9.0.1 + Ascend950PR 回片上动态 kernel 配置加载失败（errno 561108 ParseDynamicKernelConfig / 561118 ADD_TO_LAUNCHER_LIST_AICORE / 561000，最终 ERR00100 PTA call acl api failed），每次 FSDP2 post-backward 中止；绕过为 patches/torch_npu/chunk_cat.py 在 import 时把 torch._chunk_cat 替换为 torch 官方参考分解（F.pad 补零到 num_chunks 倍数 → reshape 为 (num_chunks, -1) → torch.cat(dim+1)），走常规 cat kernel。
  - 坑2（torch 上游层）：OffsetBasedRNGTracker.__init__ 对 RNG state 做 rank0 广播，单 rank 任务里该集合通信是恒等操作，但 NPU 上单 rank HCCL 广播 kernel 间歇性永不完成，卡死参数初始化（stream.cc SynchronizeExecutedTask 三分钟超时，stream_id=33）；torchtitan 的 set_determinism 仅在 world_size > pp_degree 时不做 state sync，单卡 PP=1 回退到 run_state_sync=True 命中广播；绕过为 patches/torch/distributed/tensor_random.py 在 world_size==1 时置 run_state_sync=False。
  - 坑3（仓库扩展层）：DistMuon 的 _preflight_step 要求所有配置参数都有梯度，报 RuntimeError: DistMuon requires every configured gradient before step(); missing gradients: ['layers.2.attention.indexer.compressor.ape', ...]；参考 sparse core 故意丢弃 selector 的 topk_scores 边，indexer 参数天然无梯度；冻结参数反而会卡死 FSDP2 的 stream 事件链，唯一安全缝是在 optimizer.materialize() 前 _exclude_reference_indexer_from_muon()：无 fused teacher pair 时从 muon_pattern 裁掉 indexer/compressor 条目（AdamW catch-all 原生跳过无梯度参数）。
  - 坑4（仓库 ops 层）：ops/ascendc/fused_matmul.py 的 _npu_baddbmm 无条件调用 cann_ops_nn.fused_matmul，而安装的 cann_ops_nn 没有该函数（AttributeError: module 'cann_ops_nn' has no attribute 'fused_matmul'，DistMuon Newton-Schulz 首步即崩）；修复为 _HAS_FUSED_MATMUL = cann_ops_nn is not None and hasattr(cann_ops_nn, "fused_matmul") 守卫，缺函数时走普通 baddbmm 分解（beta*self + alpha*(batch1@batch2) 分步计算）。

## 探针与操作
- 坑1 探针：plog 日志定位 aclnnChunkCat_4191 动态 kernel 配置失败链（kernel_mgr.cpp:223/479 → chunk_cat.cpp:41 → aclnn_chunk_cat.cpp:159/234 → op_plugin ChunkCatKernelOpApi.cpp:124 → ERR00100）。
- 坑2 探针：RUNTIME 日志 `SynchronizeExecutedTask: report three minutes timeout! stream_id=33, task_id=2, pendingNum=0`（通信 stream 挂死特征）。
- 坑3 探针：dist_muon.py:517 _preflight_step 的 RuntimeError（missing gradients 列表）。
- 坑4 探针：cann_ops_nn/__init__.py:37 __getattr__ 抛 AttributeError。
- 分层定位原则：bug 在哪层，修就在哪层（models/ 图纸不动，管道层修复）。

## 机制与判别
- 坑1 绕过单元（patches/torch_npu/chunk_cat.py 完整实现）：
```
"""Fallback for ``torch._chunk_cat`` when the NPU kernel is unusable.

FSDP2's reduce-scatter copy-in (``torch.ops.fsdp.chunk_cat``, called from
``foreach_reduce`` in ``post_backward`` even at world size 1) lowers to
``torch._chunk_cat`` -> ``aclnnChunkCat``. On CANN 9.0.1 the ChunkCat dynamic
kernel fails to load its config for the Ascend950PR stepping
(``ACLNN_ERR_INNER_LOAD_JSON_FAILED``, errno 561108), so every FSDP2
post-backward aborts with ``ERR00100 PTA call acl api failed``.

Route the binding through torch's own reference decomposition instead
(pad -> chunk view -> ``torch.cat``), which uses the regular cat kernel.
"""

import torch
import torch_npu

_original_torch_chunk_cat = torch._chunk_cat


def _chunk_cat_fallback(tensors, dim, num_chunks, *, out=None):
    tensors = list(tensors)
    first = tensors[0]
    ndim = first.dim()
    if dim < 0:
        dim = dim + ndim
    padded = []
    for tensor in tensors:
        size_along_dim = tensor.size(dim)
        pad_to = (size_along_dim + num_chunks - 1) // num_chunks * num_chunks
        if pad_to != size_along_dim:
            pad = [0] * 2 * (tensor.dim() - dim - 1) + [0, pad_to - size_along_dim]
            tensor = torch.nn.functional.pad(tensor, pad)
        padded.append(tensor.reshape(tensor.shape[:dim] + (num_chunks, -1)))
    result = torch.cat(padded, dim + 1)
    if out is None:
        return result
    out.copy_(result)
    return out


def apply() -> None:
    if not torch_npu.npu.is_available():
        return
    torch._chunk_cat = _chunk_cat_fallback


apply()
```
- 坑2 绕过单元（patches/torch/distributed/tensor_random.py 完整实现）：
```
"""Skip the DTensor RNG state-sync broadcast in single-rank jobs.

``OffsetBasedRNGTracker.__init__`` broadcasts the device RNG state from rank 0
to every rank.  With one rank in the job the collective is an identity
operation, and upstream PyTorch already deprecates it in favour of seeding
every rank identically (which torchtitan's ``set_determinism`` does).
On NPU the single-rank HCCL broadcast kernel is additionally unreliable:
its device task intermittently never completes, wedging parameter
initialization (``SynchronizeExecutedTask`` three-minute timeouts on the
communication stream).

torchtitan's ``set_determinism`` only pre-constructs the tracker without
state sync when ``world_size > pp_degree``, so a single-card PP=1 job falls
back to the lazy tracker with ``run_state_sync=True`` and hits the broadcast.
Skip the sync there instead.
"""

import torch
import torch_npu
from torch.distributed.tensor import _random

_ORIGINAL_TRACKER_INIT = _random.OffsetBasedRNGTracker.__init__


def _patched_tracker_init(self, device_mesh, run_state_sync: bool = True) -> None:
    if (
        run_state_sync
        and torch.distributed.is_available()
        and torch.distributed.is_initialized()
        and torch.distributed.get_world_size() == 1
    ):
        run_state_sync = False
    _ORIGINAL_TRACKER_INIT(self, device_mesh, run_state_sync)


def apply() -> None:
    if not torch_npu.npu.is_available():
        return
    _random.OffsetBasedRNGTracker.__init__ = _patched_tracker_init


apply()
```
- 坑3 修复单元（extensions/torchtitan/trainer.py 新增方法，edit newString 原文）：
```
        def _exclude_reference_indexer_from_muon(self) -> None:
            """Drop gradient-free indexer parameters from the DistMuon pattern.

            The reference sparse core discards the selector's ``topk_scores``
            edge, so every ``attention.indexer`` parameter is gradient-free by
            design; only the fused core/selector teacher pair trains them.
            DistMuon aborts its first ``step()`` over a configured parameter
            without a gradient, so without the fused pair the indexer entries
            must leave the Muon group (the AdamW catch-all skips them
            natively). Freezing the parameters instead wedges FSDP2's stream
            event chain on NPU, so the pattern is the only safe seam.
            """
            profile = getattr(self.optimizer, "_muon_profile", None)
            override = getattr(self, "override", None)
            if profile is None or "indexer" not in profile.muon_pattern:
                return
            requested = {
                entry if isinstance(entry, str) else entry[0]
                for entry in (getattr(override, "imports", None) or ())
            }
            fused_pair = requested.issuperset(_FUSED_INDEXER_TEACHER_PAIR)
            if fused_pair:
                return
            pattern = profile.muon_pattern.replace(
                r"attention\.indexer\.(?:wq_b|weights_proj)\.weight|", ""
            ).replace(
                r"attention\.(?:compressor|indexer\.compressor)\.", r"attention\.compressor\."
            )
            self.optimizer._muon_profile = replace(profile, muon_pattern=pattern)

        def _post_init_optimizer(self) -> None:
```
- 坑4 修复单元（将来源完整模块与守卫改动合成；保留普通bmm分支、返回和注册）：

```python
# Copyright (c) 2026 Huawei Technologies Co., Ltd. All Rights Reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

from __future__ import annotations

from importlib import import_module
from typing import Any

import torch
import torch.library

from torchtitan_npu.override import _IS_A5

_DISPATCH_KEY = "PrivateUse1"

cann_ops_nn: Any = None
if _IS_A5:
    cann_ops_nn = import_module("cann_ops_nn")


_HAS_FUSED_MATMUL = cann_ops_nn is not None and hasattr(cann_ops_nn, "fused_matmul")


def _maybe_contiguous(x: torch.Tensor) -> torch.Tensor:
    # 连续 tensor 直接返回，不触发 aten.contiguous
    return x if x.is_contiguous() else x.contiguous()


def _npu_baddbmm(
    self: torch.Tensor,
    batch1: torch.Tensor,
    batch2: torch.Tensor,
    *,
    beta=1,
    alpha=1,
) -> torch.Tensor:
    if self.dim() == 3 and _HAS_FUSED_MATMUL:
        batch1 = _maybe_contiguous(batch1)
        batch2 = _maybe_contiguous(batch2)
        return cann_ops_nn.fused_matmul(batch1, batch2, x3=self, alpha=alpha, beta=beta, fused_op_type="add")
    result = torch.bmm(batch1, batch2).mul_(alpha)
    if beta != 0:
        result.add_(self, alpha=beta)
    return result


def _register_impl(op_name: str, fn) -> None:
    try:
        torch.library.impl(op_name, _DISPATCH_KEY)(fn)
    except RuntimeError as exc:
        raise RuntimeError(f"Failed to register {op_name!r} for dispatch key {_DISPATCH_KEY!r}") from exc


if _IS_A5:
    _register_impl("aten::baddbmm", _npu_baddbmm)
```

本例处理的是已安装cann_ops_nn但缺少fused_matmul符号；未额外处理模块自身导入失败。

- 判别：4 个 bug 均为「跨层调用链断裂」（FSDP2→torch_npu→CANN、DTensor→HCCL、torchtitan 优化器↔模型设计、Muon→cann_ops_nn），通过错误码/堆栈定位到层，再按层选择 patches（运行时替换上游）、extensions（合法改造点）、ops（路由层守卫）三种机制。

## 验证信号
- 验证层级：修复前设备失败与源码修改。修后完整训练运行结果未进入采用证据，不能因账本中的device_functional标签宣称修后训练已通过。
- 客观信号：plog 错误链（561108/561118/561000/ERR00100）、SynchronizeExecutedTask 3 分钟超时、DistMuon RuntimeError、cann_ops_nn AttributeError 分别对应修复前的四次失败。

## 适用与失效边界
- 适用：CANN 9.0.1 + Ascend950PR 回片单卡 bring-up；上游 bug 等上游修复后按仓库规则删除已吸收补丁（patches/ 是临时机制）。
- 坑1 绕过有性能代价（chunk_cat 分解多趟 kernel）；坑4 绕过使 Newton-Schulz 从单算子变为 5 迭代 × 每次几个算子——环境修好后 hasattr 探测自动切回融合实现。
- 坑3 修复依赖 muon_pattern 的正则结构（wq_b/weights_proj/compressor 条目名），模型侧改动需同步核验。
- 分解版与融合版的等价性论证及修后训练数字未进入账本证据，不得据本卡宣称。
