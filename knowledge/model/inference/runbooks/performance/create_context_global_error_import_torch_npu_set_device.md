---
{
  "type": "Runbook",
  "title": "TP1 NPU context 后台预创建：完成通知、惰性 torchair 与启动计时边界",
  "description": "Qwen3.5-9B TP1 eager 的 dummy 权重回放：还原后台完成通知与主线程等待兜底，区分整批调度和批内命令计时，不外推冷热收益。",
  "tags": [
    "task.implementation",
    "topic.performance.analysis"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:05Z",
  "updated_at": "2026-11-23T06:30:53Z",
  "platforms": []
}
---


# TP1 NPU context 后台预创建：完成通知、惰性 torchair 与启动计时边界



## 适用场景

cann-recipes-infer 类推理框架单进程 TP1/world_size=1、eager、Qwen3.5-9B dummy 权重、1 prompt×32 token。讨论把 NPU context 初始化与 CPU 模型构建重叠的控制流，以及如何区分整批调度耗时与批次内单次命令耗时；数字不作为真实权重或多卡服务的收益保证。

## 触发与观测

全进程分段计时（自建 prof 驱动 wrap 各阶段）观测到：`import torch` ~2.3s、`import InferenceConfig` ~1.0s、`ExecutionEngine.__init__`（含 `torch.npu.set_device` 串行）1.9–9.3s 随设备冷热大幅波动，而模型构建 + dummy 权重物化（`initialize_dummy_weights`）为 ~1.8–2.0s 纯 CPU 工作（source 0 seq 171/291/321 profile 日志）。两者串行是 wall 时间的最大离群源；此外 `_move_to_device`（2.9GB H2D）在设备状态差时从 0.23s 恶化到 ~12s（source 0 seq 291/321），跨设备（device 4/5/6）冷热噪声使单次计时不可比。

## 探针与操作

完成通知是机制的一部分。source 0 seq 195 的完整模块包含 `finally: _ready.set()`，seq 250 将主线程 `ensure` 改成等待后同步 `set_device` 兜底；seq 456 只打印了函数前半段，不能把该显示片段当完整函数。下面按完整模块与后续接线变更还原必要控制流：

```python
import os
import threading

_lock = threading.Lock()
_thread = None
_index = None
_error = None
_ready = threading.Event()


def _create_context(index: int) -> None:
    global _error
    try:
        import torch
        import torch_npu  # noqa: F401
        torch.npu.set_device(torch.device("npu", index))
    except BaseException as exc:
        _error = exc
    finally:
        _ready.set()


def start(index=None) -> None:
    global _thread, _index
    if index is None:
        index = int(os.getenv("LOCAL_RANK", "0"))
    with _lock:
        if _thread is not None:
            if index != _index:
                raise RuntimeError("NPU context already initializing for another device")
            return
        _index = index
        _thread = threading.Thread(target=_create_context, args=(index,), daemon=True)
        _thread.start()


def ensure(device) -> None:
    if _thread is not None:
        _ready.wait()
    import torch
    torch.npu.set_device(device)
```

`finally` 保证后台成功或失败都能唤醒主线程；`ensure` 的同步调用负责为调用线程选择设备，后台失败时也由这次调用重试。同步调用若仍失败，应让异常返回，不能仅凭完成事件宣称 context 创建成功。

接线为 `ModelWorker._load_weights` 在 CPU 构建前调用 `start(self.device.index or 0)`，`DummyModelLoader._move_to_device` 在首次 H2D 前调用 `ensure`（source 0 seq 195/250/251/302）。完整模块和接线涉及多个版本，上述控制流用于说明必要通知与等待关系，不把 seq 456 的截取输出当完整最终文件。

eager 惰性 torchair：移除模块级 import/patch，Attention 初始化仅在 `enable_gegraph` 或 `enable_npugraph_ex` 时导入并 patch；forward 默认使用 `torch.ops.npu`，GE 分支另用 `torchair.ops`（source 0 seq 200/201/349–352）。原轨迹只有 TP1 数值验证，图模式与多卡行为仍须各自回归。

## 机制与判别

- 等待的是后台尝试结束，不是“必然成功”；完成事件必须在异常路径也置位，首次设备操作前还要在主线程执行 `ensure`。
- import 期启动的早期版本中，曾观测到 `import InferenceConfig` 约25.2s，另一记录约1.0s（source 0 seq221/224）；seq224明确尚不能定因，同期golden并发运行造成CPU争用等解释未排除。后续把启动点移到 `_load_weights`（seq300），但不能由前后单次耗时认定25.2s由启动位置造成，也不能混用不同版本的收益数字。
- eager 移除无用 torchair 导入是另一项同时变化；未做单变量消融，不能把所有命令耗时差唯一归因于后台 context。多卡 HCCL 初始化与图模式未在本轨迹验证。

## 验证信号

- source 0 seq 401：device 6 的整批调度器 `wall_seconds=50.82459229999222`；批次内 shell START/END 差分别是基线 14.68/15.02s、当时 candidate 7.46/13.62s。
- source 0 seq 451：device 4 的另一整批 `wall_seconds=62.43853527700412`；批次内基线 24.07/10.46s、当时 candidate 14.08/13.81s。两批用不同设备，批次内交错运行；不能把八个值统一称作同一设备上的调度器全任务时间。
- source 0 seq 466：最终 candidate 在 device 4 单独调度，`wall_seconds=9.57524134000414`。该口径也不能与前述批内 shell 命令时间直接拼成性能对照。
- source 0 seq476读取较早的 `scratch-cmp3` 比较日志，记录 `token_gate: pass`、`logit_gate: pass`，logits max/mean relative均为0.0、samples66，tokens match_ratio 1.0；它只覆盖该日志对应版本的dummy权重回放，不能绑定到seq466的最终运行。较早运行的逐token输出另见seq381/421/436；seq466只有任务完成和文件写出，没有逐token比对或配套比较器结果。
- 上述记录来自原轨迹；本卡修订不表示重新运行真实 NPU 模型。

## 适用与失效边界

- 仅覆盖 TP1、eager、dummy 权重和上述短任务条件；真实权重、图模式、多卡与服务并发均未验证。
- seq 299 的约 0.3s 差异属于迁移启动点之前的早期 ovl 版本；seq 324 明确未在慢初始化状态测试 new3。最终方案的冷热收益差异仍是假设，不能据此声明“冷态收益最大、热态固定省0.3s”。
- H2D 的 0.2–12s 波动未被本方案消除。使用时分别记录设备、实现版本、批次计时及命令计时，先验证完成通知、主线程设备绑定与错误传播，再在目标设备测量。

## 附：断言存档

- 后台初始化必须在成功与异常路径都通知等待者；主线程首次 H2D 前同步选择设备并兜底。
- 批次调度器耗时与批内命令 START/END 差是不同指标；两批设备不同，不合并成单一加速比。
- 原轨迹较早版本的dummy权重比较器双门通过，不构成最终9.575s运行的精度验收；最终版本、真实权重及多卡仍需各自数值验证。
