---
type: Runbook
title: NPU 推理脚本 os._exit 快退残留 CANN TBE 孙进程的 shutdown 噪声（RouteServer.finalize 消除）
description: NPU 推理脚本 os._exit 快退残留 CANN TBE 孙进程的 shutdown 噪声（RouteServer.finalize 消除）。昇腾 NPU 推理脚本在所有输出已落盘、用 os._exit(0) 快速退出后，关闭阶段仍打印 "main process disappeared" 噪声。输出其实完整、退出行为正常，但这类冗余打屏纯属干扰、影响对最终结果的判断。
tags:
- task.debugging
- topic.multimodal
- topic.model_serving
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/401
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# NPU 推理脚本 os._exit 快退残留 CANN TBE 孙进程的 shutdown 噪声（RouteServer.finalize 消除）

## 信号（现象）

昇腾 NPU 推理脚本在所有输出已落盘、用 `os._exit(0)` 快速退出后，关闭阶段仍打印 `"main process disappeared"` 噪声。输出其实完整、退出行为正常，但这类冗余打屏纯属干扰、影响对最终结果的判断。

## 触发条件

- 推理脚本走「快速退出路径」：用 `os._exit(0)` 跳过 Python 解释器正常 shutdown（规避 torch_npu C 扩展在解释器析构时触发的 double-free SIGABRT），并对**直接子进程**逐个 SIGKILL（防 DataLoader worker / multiprocessing resource_tracker 打 leaked-semaphore 警告）。
- 该进程此前触发过 CANN TBE 算子编译 / 知识库（经 `RouteServer` 派生 `task_distribute` 子进程）。观测于走仓内多模态统一拉起（[mm-inference-launch](../../concepts/frameworks/mm_inference_launch.md)）的文/图生视频 DiT 推理脚本。

## 根因

CANN TBE 的 `RouteServer` 派生的 `task_distribute` 是 Python 进程的**孙进程**——对直接子进程的 SIGKILL 扫描（`pgrep -P <pid>`）够不到它们。父进程快退、未清理这些孙进程时，孙进程发现父进程已消失，在关闭阶段打印 `"main process disappeared"`。此前的兜底是靠 shell 脚本级 grep 收拾这些够不到的孙进程。

## 修法

在 `os._exit(0)` 之前显式调用 TBE `RouteServer` 的 finalize 清理这层孙进程，`try/except` 包裹（清理失败只 `warning`、不阻塞退出）：

```python
# Clean up CANN TBE knowledge-bank subprocesses before the fast exit below.
try:
    from tbe.common.repository_manager.route import RouteServer
    RouteServer.finalize()
except Exception as exc:  # pylint: disable=broad-except
    logger.warning("TBE RouteServer finalize failed during shutdown: %s", exc)
```

紧随其后仍是原快退序列：`pgrep -P <pid>` 找直接子进程 → 逐个 `os.kill(pid, SIGKILL)` → `os._exit(0)`。finalize 只补齐「孙进程」这一层此前够不到的清理，退出行为不变。可迁移到任何用 `os._exit` 快退、且触发过 TBE 编译的昇腾推理脚本。

## 相关

- 同属 DiT 视频生成模型昇腾 bringup 的后端适配经验：[cuda-native-dit-video-attention-sp-npu-adaptation](../../optimizations/experience/rules/cuda_native_dit_video_attention_sp_npu_adaptation.md)。

## Evidence

- diff 事实（clone `@160c8d0b`，`models/sana-video/inference_video_scripts/inference_sana_video.py` 的 `__main__` 收尾块）：`RouteServer.finalize()` 新增块 + `os._exit`/SIGKILL 上下文；旧注释「shell-level grep 收拾孙进程」被替换为 Python 侧 finalize。属行为/噪声消除修复，源未给量化 metric。
  - 溯源下探：[cann-recipes-infer-pr-401-fix-some-modifications-to-multimodal-network-log-printing-and-readme-doc](https://gitcode.com/cann/cann-recipes-infer/merge_requests/401)
