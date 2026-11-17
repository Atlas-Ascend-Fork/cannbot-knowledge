---
{
  "type": "Runbook",
  "title": "覆写式 stage marker 的候选簇：保留 tick 和成员，先确认 launch 归属",
  "description": "按原始 tick 阈值返回全部 role/worker 候选簇；成员数不能证明本次 launch，频率换算和归属确认分别取证。",
  "tags": [
    "task.implementation",
    "topic.performance.analysis"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-14T18:00:00Z",
  "updated_at": "2026-11-17T01:57:52Z",
  "platforms": []
}
---
# 覆写式 stage marker 的候选簇：保留 tick 和成员，先确认 launch 归属

## 适用场景

back-to-back 连发、设备 marker 缓冲区被覆写后的 stage-timing 快照分析。输入为同一设备、同一计数器域的 `[role, marker, worker]` 原始整数 tick；role/marker 的实际含义须与采集端表一致。

## 触发与观测

朴素 max-min 跨度过大，排序后出现多个大间隙。旧 launch 残留可能比本次 marker 更多，按成员数或按“最新簇”选择都不能独自证明本次归属。

## 探针与操作

以下是本次修订的诊断示例，返回每个 role/worker 的所有候选簇与每条 `(role, worker, marker, tick)` 身份，不选择本次 launch。保存为 `marker_probe.py` 后传入采集文件和原始 tick 阈值；只有从同版本计数器说明或独立校准确认频率后，才提供 `--tick-hz`。`--unwritten-tick` 仅在采集协议已确认某值代表未写入时指定，默认保留零值。

```python
import math
from numbers import Integral, Real


def marker_candidates(stage_ticks, *, gap_ticks, tick_hz=None, unwritten_tick=None):
    """Return all clusters in [role][marker][worker] raw integer ticks.

    Clusters are candidates only. This function never assigns a launch ID.
    """
    if isinstance(gap_ticks, bool) or not isinstance(gap_ticks, Integral) or gap_ticks <= 0:
        raise ValueError('gap_ticks must be a positive integer number of ticks')
    if tick_hz is not None:
        if isinstance(tick_hz, bool) or not isinstance(tick_hz, Real):
            raise ValueError('tick_hz must be a verified positive finite rate')
        tick_hz = float(tick_hz)
        if not math.isfinite(tick_hz) or tick_hz <= 0:
            raise ValueError('tick_hz must be a verified positive finite rate')
    if unwritten_tick is not None and (
        isinstance(unwritten_tick, bool) or not isinstance(unwritten_tick, Integral) or unwritten_tick < 0
    ):
        raise ValueError('unwritten_tick must be a nonnegative integer or None')
    if not len(stage_ticks):
        return []
    marker_count = len(stage_ticks[0])
    if not marker_count:
        if any(len(role) for role in stage_ticks):
            raise ValueError('ragged marker dimension')
        return []
    worker_count = len(stage_ticks[0][0])
    candidates = []
    for role_id, role in enumerate(stage_ticks):
        if len(role) != marker_count or any(len(row) != worker_count for row in role):
            raise ValueError('expected rectangular [role][marker][worker] ticks')
        for worker_id in range(worker_count):
            members = []
            for marker_id, row in enumerate(role):
                tick = row[worker_id]
                if isinstance(tick, bool) or not isinstance(tick, Integral) or tick < 0:
                    raise ValueError('each raw tick must be a nonnegative integer')
                if unwritten_tick is not None and tick == unwritten_tick:
                    continue
                members.append({'role': role_id, 'worker': worker_id,
                                'marker': marker_id, 'tick': int(tick)})
            members.sort(key=lambda item: (item['tick'], item['marker']))
            clusters = []
            for member in members:
                if not clusters or member['tick'] - clusters[-1][-1]['tick'] >= gap_ticks:
                    clusters.append([])
                clusters[-1].append(member)
            for cluster in clusters:
                span = cluster[-1]['tick'] - cluster[0]['tick']
                candidate = {'candidate_id': len(candidates), 'role': role_id,
                             'worker': worker_id, 'members': cluster,
                             'numeric_span_ticks': span, 'gap_ticks': int(gap_ticks),
                             'launch_id': None, 'ownership': 'unconfirmed'}
                if tick_hz is not None:
                    candidate.update(tick_hz=tick_hz, numeric_span_seconds=span / tick_hz)
                candidates.append(candidate)
    return candidates


if __name__ == '__main__':
    import argparse
    import json
    import numpy as np

    parser = argparse.ArgumentParser()
    parser.add_argument('npy')
    parser.add_argument('--gap-ticks', required=True, type=int)
    parser.add_argument('--tick-hz', type=float)
    parser.add_argument('--unwritten-tick', type=int)
    args = parser.parse_args()
    ticks = np.load(args.npy, allow_pickle=False)
    if ticks.ndim == 4 and ticks.shape[-1] == 1:
        ticks = ticks[..., 0]
    if ticks.ndim != 3:
        parser.error('expected [role, marker, worker] or a trailing singleton axis')
    print(json.dumps(marker_candidates(ticks.tolist(), gap_ticks=args.gap_ticks,
        tick_hz=args.tick_hz, unwritten_tick=args.unwritten_tick), ensure_ascii=False))
```

`STAGE_TIMING_NPY` 是实际采集文件，`GAP_TICKS` 是本次分析明确选定的 tick 间隙阈值，均由调用方提供：

```bash
python3 marker_probe.py "${STAGE_TIMING_NPY}" --gap-ticks "${GAP_TICKS}"
```

## 机制与判别

函数只在相邻 tick 差达到 `gap_ticks` 时分段，保留所有簇和成员，统一标记 `ownership=unconfirmed`、`launch_id=null`。时间分隔既不保证簇内属于同一 launch，也不保证成员最多或位置最新的簇属于本次。归属必须由与这些记录绑定的独立 launch ID、可核验采样窗口或哨兵确认；缺少该信号就只报告候选。可选频率仅做数值单位换算，不能把数值跨度升级为本次 launch 时延。

## 验证信号

历史工具输出清点过两个专家数档候选中的 13 与 70 个 label，但没有独立归属信号；这不是本次 launch 的覆盖率。修订的 CPU 合成反例使用原始 tick `[100,200,300,400]` 与 `[2000,2050,2100]`、`gap_ticks=1000`，返回 4 成员和 3 成员两个候选且均未认定归属，避免直接选择旧的大簇。历史换算未闭合的微秒值不再作为结论；本次没有新设备采样。

## 适用与失效边界

阈值依赖本次数据，不能复用为通用常量。不同 rank 的计数器不视为同步；回绕、跨计数器域、时间接近的多次 launch 或仍在写入的缓冲区都会影响聚类解释。先核对位宽、采样边界和独立归属，再解释 `numeric_span_ticks/seconds`；它们不是端到端延迟。缺失阶段需另采，也不能为清理旧 marker 而无条件清零有守卫依赖的缓冲区。
