---
type: Runbook
title: "310P 长 T 递推 kernel 慢在搬运：msprof 判别法"
description: 长 T 串行 chunk 递推 kernel 切到 msprof kernel 级口径后远慢于参考实现；用 op_summary 逐 kernel Task Duration 占比判定搬运/同步 bound，而不是继续调数学。
tags: [task.debugging, topic.performance.analysis, topic.implementation.synchronization]
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/8746f7ced6cef47e3fd7abd64c0eb827e28e2b56/docs/zh/guide/programming_guide/advanced_programming/hardware_implementation/architecture_spec/npu_arch_2002.md
    role: constraint
  - resource: https://gitcode.com/cann/asc-devkit/blob/8746f7ced6cef47e3fd7abd64c0eb827e28e2b56/docs/zh/api/SIMD-API/basic_api/sync_control/intra_core_sync/intra_core_sync_overview.md
    role: constraint
created_at: "2026-10-28T10:00:08Z"
updated_at: "2026-10-28T10:00:08Z"
platforms: ["310p"]
---

# 310P 长 T 递推 kernel 慢在搬运：msprof 判别法

## 现象

把一个“按 T 维串行分块递推”的 AscendC 算子从 host 侧多算子拼接改成单 kernel 直调后，逐用例 e2e 计时口径显示领先参考实现（用例全过、geomean 约 1.7x）；改用标准模式的 msprof kernel 级 `--compare`（`--warm-up=3`、`--repeats=1`，两侧同机同批采集）后，同一份 `.so` 的 geomean 只有约 0.50x（10/10 有效）。

两者并不矛盾。单次 launch 的 `op_summary_*.csv` 里，自定义主 kernel 一行独大，其余 dtype/layout 转换 kernel（Cast/Transpose/ViewCopy/ZerosLike/AsStrided）都只有主 kernel 的百分之几；而主 kernel 处理一个 chunk 的实测耗时，比该 chunk 的 f16 cube 计算量按峰值算出的理论值高约 2–3 个数量级。时间不在算上，在搬和等上。

## 适用场景

- 工程形态：AscendC kernel 直调（host 侧 `aclrtlaunch_<kernel>`），T 维串行分块递推类算子，每 chunk 内有多条 GEMM 链，中间矩阵在核内算出来后还要再参与下一次 Mmad。
- API 路径：`Mmad` / `LoadData` / `DataCopy`（GM↔L1↔L0）/ `SetFlag`+`WaitFlag`（`V_MTE3`/`MTE3_MTE2`/`MTE2_MTE1`/`MTE1_M`/`MTE3_V`）/ `PipeBarrier<PIPE_ALL>`；采集侧 `msprof --ai-core=on --task-time=on` + `op_summary_*.csv`。
- 验证过的平台与 CANN 版本：310P（Ascend310P3 / dav-m200）；**CANN 版本本轨迹未记录**（该卡的版本相关结论只在“m200 取数路径”这一层成立，不依赖具体 CANN 小版本）。
- 适用粒度：单个 kernel 的性能归因（不是算子全集，也不是 e2e）。
- 路线优先级：`recommended_fastpath`（先用口径判别，再决定是否重写数据流）。
- 明确不适用：计算真正 bound 的 kernel（cube 已吃满）；操作数全部来自 host 预排 GM、核内不产出中间矩阵的简单 kernel；只有一路 GEMM 的 kernel。

## 判别方法

### 平台律（m200，决定这类 kernel 的一阶成本）

1. cube 的操作数只能经 GM → L1 → L0 以 f16 tile 形式读入；核内算出的中间矩阵（逆矩阵近似、转置块、带因子等）要参与 `Mmad`，必须走一次完整回环：UB →(MTE3)→ GM →(MTE2 Nd2Nz)→ L1 →(MTE1 LoadData)→ L0A/L0B。
2. `Mmad` 从 L0C 读出结果没有 `M_MTE3` 事件可用，代码只能挂 `PipeBarrier<PIPE_ALL>()` 全屏障，每读一次结果就把整条流水排空。
3. 因此“每 chunk 的 GM 回环次数 × chunk 数”是一阶成本项，而 chunk 数随 T（以及 batch/头数）线性增长。

### Probe（单算子单例 profile）

wrapper：以参考实现为金标准，只取一个代表性用例，先热身再采（首次采集会踩到“输入仍在 CPU”而报 `NotImplementedError: Could not run '...' with arguments from the 'CPU' backend`，必须在调用前 `.npu()`）：

```python
import importlib.util
import torch
import torch_npu
torch.ops.load_library("<算子包>/build/lib<generic>_ops.so")
_REF = "<参考实现模块路径>"          # 提供 get_input_groups()
_spec = importlib.util.spec_from_file_location("ref_full", _REF)
ref = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ref)
_REPRESENTATIVE = [<代表性 case 索引>]   # 覆盖 T 跨度即可

def _inputs(case_idx):
    groups = ref.get_input_groups()
    return [groups[i] for i in _REPRESENTATIVE][case_idx]

args = [a.npu() if isinstance(a, torch.Tensor) else a for a in _inputs(0)]
for _ in range(5):
    torch.ops.npu.<算子>(*args)
torch.npu.synchronize()
```

采集（只开 task-time + ai-core，避免 ACL 级开销淹没 kernel 级）：

```bash
cd <diag-dir> && rm -rf PROF_* && \
ASCEND_RT_VISIBLE_DEVICES=0 msprof --output=<diag-dir> \
  --ai-core=on --task-time=on --ascendcl=on \
  /usr/local/python3.11.10/bin/python3 <diag-dir>/_wrapper.py
```

判读：对 `PROF_*/mindstudio_profiler_output/op_summary_*.csv` 按 `Task Type`（AI_CORE/AIV/MIX）过滤，把 `Task Duration(us)` 按 `Op Name` 求和：

```python
import csv
rows = list(csv.DictReader(open("<op_summary>.csv")))
tot = 0
for r in rows:
    tt = r.get('Task Type', '')
    if 'AI_CORE' in tt or 'AIV' in tt or 'MIX' in tt:
        d = float(r.get('Task Duration(us)', 0) or 0)
        tot += d
        print(f'{r.get("Op Name","?"):<40} {tt:<18} {d:>14.1f}')
print('TOTAL compute:', round(tot, 1), 'us')
```

### 判据（三条同时成立才判“搬运/同步 bound”）

- 主 kernel 占单次 launch 设备时间约九成以上（其余同类转换 kernel 只有它几个百分点）；
- 主 kernel 的每 chunk 实测时间比该 chunk 的 cube 理论时间高两个数量级以上；
- 源码里每 chunk 的 `pushScr/loadA/loadBScr` 调用次数与 `PipeBarrier<PIPE_ALL>` 条数，与实测时间同向增长。

## 根因

m200 的 cube 取数路径决定了：**核内自产的操作数没有“留在片上”的通路，每一次复用都要付一次完整的 GM 回环**；而 L0C 读出缺 `M_MTE3` 事件，又迫使每次读结果都全屏障排空。于是这类递推 kernel 的一阶成本 = 每 chunk 的回环次数 × chunk 数 + 每 chunk 的全屏障次数 × chunk 数，二者都随 T 线性增长；cube 本身远未吃满，数学近似也动不了这两项。

这也解释了 e2e 与 kernel 级口径为何相反：融合把 launch 数从 N 降到 1，e2e 口径里 host 开销与算子数被消掉，比值被放大；kernel 级口径只看主 kernel 的设备时间，回环与屏障一分不少。

## 解决配方

这是一个**判别配方**（不是数据流重写配方）：

1. 先用单例 `op_summary` 拆账，确认“主 kernel 占比 ≥ 九成”，把优化对象锁定在主 kernel 内；
2. 数一遍源码里每 chunk 的 GM 回环调用点与 `PipeBarrier<PIPE_ALL>` 条数，与 profile 里的每 chunk 时间对照（判据第三条）；
3. 判据成立后，优化方向是**减少每 chunk 的回环次数与屏障条数**，而不是让 cube 算得更满或换数学近似；
4. 每一步改动都用同一 kernel 级口径复测（相对参考实现的成对 geomean），不要用 e2e 结论验收；
5. 若一时无法减少回环，就先别在该 kernel 上继续投数学优化——收益是一阶不动的。

优化后的实现不在本轨迹的复核范围内（见「失效边界」），本卡只给出“判别 → 定向”的闭环。

## 设计决策

- **为什么把“平台律”放在判据之前**：回环次数与屏障条数是 m200 取数路径的必然产物，不是实现者的疏忽；先认清“这类 kernel 的一阶成本在哪”，就不会把时间浪费在 tile 尺寸与数学近似上。
- **为什么只用 `--task-time` + `--ai-core`**：ACL 级采集的 host 开销会把 kernel 级时间淹没，单例探针要的是“主 kernel 一行独大”的干净画像。
- **为什么要 e2e 与 kernel 级两条口径都采**：两者可以完全相反，只采其中一条必然误判方向；e2e 用于确认“用户可见收益”，kernel 级用于确认“设备侧真实归因”。
- **为什么判据要求三条同时成立**：单看“主 kernel 占比高”会漏掉“占比高但 cube 本来就算得慢”的情形；单看“比理论值高”又可能被理论值本身的假设误差误导。

## 系统信息

- SoC：Ascend310P3（dav-m200），8 个 AI core；UB 约 240KB、L1 1MB、L0C 256KB；cube 只支持 fp16。
- 工具链：**CANN 版本未记录**；采集用 `msprof`（`--ai-core --task-time --ascendcl`），分析用 `op_summary_*.csv`。
- 目录布局：`kernel/<op>_*.cpp` 单文件 kernel；`host/<op>_host.cpp` 裸 `aclrtlaunch_` 直调；`perf/<op>/...` 放采集产物。
- 相关文件：kernel 源（下节代码出处）；测试侧 `tests/perf_<op>.py`（e2e 口径）与 `msprof_profile_run.sh --compare`（kernel 级口径）。

## 完整代码

v0 反模式（verbatim 摘录，供对照“每个 Mmad 后一次全屏障 + 相邻事件对”的形态）：

源文件头部注释（m200 适配要点）：

```cpp
// m200 适配要点（装载律沿用同批实证模板）:
//   · 2^(gk_i-gk_j) 跨度 ~2^75, f16 立方数不可分离表示 → 行带分解:
//     每 16 行带用带中点参照 ρ_r, 因子 q·2^(gk-ρ), k·2^(ρ-gk) ∈ 2^±9.3;
//     指数 clamp [−30,15]（越界仅命中被 tril 掩掉或数值可忽略的对，
//     ...（此处省略该算子自身的容差常量））
//   · β 行权折入 Akk 列（Akk·diag(β)）→ u/w 共享 A 操作数, vT 免 β 处理
//   · S 以转置布局 S_T[v,k] 常驻 UB（f16）, GM 行块镜像 = w@S/qg@S 的
//     B 源（B 装载律: 自然 [n,k] → B=srcᵀ）
//   · kgᵀ/v_newᵀ/kqᵀ 经单位阵 Mmad 转置（B 侧自带转置: eye@Xᵀ=Xᵀ）
//   · 核内算得的立方操作数经 GM scratch 往返:
//     UB→(MTE3)→GM→(MTE2 Nd2Nz)→L1→(MTE1 LoadData)→L0A/L0B
//     （相邻 set/wait 事件对 + 每 Mmad 后全屏障）
```

搬运/Mmad 辅助（每个 `Mmad` 之后一次全屏障）：

```cpp
    // ---- 通用搬运/Mmad 辅助（顺序流水, 相邻事件对）----
    auto pushScr = [&](int32_t off, int32_t nBlk) {
        SetFlag<HardEvent::V_MTE3>(evV3);
        WaitFlag<HardEvent::V_MTE3>(evV3);
        DataCopy(gmScr[scr + off], staging, DataCopyParams(static_cast<uint16_t>(nBlk), 1, 0, 0));
        SetFlag<HardEvent::MTE3_MTE2>(ev32);
        WaitFlag<HardEvent::MTE3_MTE2>(ev32);
    };
    auto pushScrHalf = [&](int32_t off) {   // staging 前 64 列 → [64,64] 槽
        SetFlag<HardEvent::V_MTE3>(evV3);
        WaitFlag<HardEvent::V_MTE3>(evV3);
        DataCopy(gmScr[scr + off], staging, DataCopyParams(T64, 2, 2, 0));
        SetFlag<HardEvent::MTE3_MTE2>(ev32);
        WaitFlag<HardEvent::MTE3_MTE2>(ev32);
    };
    auto loadA = [&](int32_t off, bool wide) {
        DataCopy(l1a, gmScr[scr + off], wide ? nd128 : nd64);
        SetFlag<HardEvent::MTE2_MTE1>(ev21);
        WaitFlag<HardEvent::MTE2_MTE1>(ev21);
        LoadData(l0a, l1a, wide ? pA128 : pA64);
        SetFlag<HardEvent::MTE1_M>(ev1M);
        WaitFlag<HardEvent::MTE1_M>(ev1M);
    };
    auto loadBScr = [&](int32_t off, bool wide) {
        DataCopy(l1b, gmScr[scr + off], wide ? nd128 : nd64);
        SetFlag<HardEvent::MTE2_MTE1>(ev21);
        WaitFlag<HardEvent::MTE2_MTE1>(ev21);
        LoadData(l0b, l1b, wide ? pB128 : pB64);
        SetFlag<HardEvent::MTE1_M>(ev1M);
        WaitFlag<HardEvent::MTE1_M>(ev1M);
    };
    auto doMmad = [&](const LocalTensor<half>& aT, const MmadParams& mp) {
        Mmad(l0c, aT, l0b, mp);
        PipeBarrier<PIPE_ALL>();            // M→MTE3 读出（无 M_MTE3 事件）
        DataCopy(tD, l0c, DataCopyParams(4, 8, 0, 0), epM);
        SetFlag<HardEvent::MTE3_V>(ev3V);
        WaitFlag<HardEvent::MTE3_V>(ev3V);
        for (int32_t nb = 0; nb < T64 / 16; ++nb) {   // D 布局 → 行主序
            DataCopy(t2[nb * 16], tD[1024 * nb], DataCopyParams(T64, 2, 0, 6));
        }
        SetFlag<HardEvent::MTE3_V>(ev3V);
        WaitFlag<HardEvent::MTE3_V>(ev3V);
    };
```

调用侧每 chunk 反复 `pushScr(...)` / `loadA(...)` / `loadBScr(...)` / `doMmad(...)`（同一 chunk 内十余次），串行 chunk 数随 T 线性增长——这是“实测时间 ∝ 往返次数”的直接来源。

## 性能影响

同一算子、同一参考实现、同一台 310P、同一标准 `--compare` 口径：

- v0 数据流（每 chunk 数十次 GM scratch 回环 + 每次 Mmad 后 `PIPE_ALL`）：geomean 约 0.50x（相对参考实现），10/10 有效；
- 按“减少每 chunk 回环与屏障”的方向重写后：geomean 约 1.02x（相对参考实现），10/10 有效。
- 中间的具体改写手法来自开发会话的 agent 报告，非本轨迹工具输出；优化后的源码也不在本轨迹内（见「失效边界」），故本卡只保留“机制 + 成对相对代价”，不提供重写配方。

## 预防

- 在 310P 上写“核内自产操作数”的 kernel 之前，先数一遍每个 chunk 的 GM 回环次数；超过个位数就先设计减少回环的数据流（多结果合批、常量常驻、按 K 分块复用），不要先调数学。
- 每个 `Mmad` 后不要无脑 `PipeBarrier<PIPE_ALL>`；能换成 `M_MTE3` 之外的细粒度事件就用细粒度（本代 L0C→UB 读出路径缺 `M_MTE3`，这是全屏障的由来，属硬件/工具链边界，不能靠写法规避）。
- 性能结论一律用 kernel 级口径复测；e2e 结论只作参考（见同批“墙钟 vs kernel 拆账”卡）。

## 验证信号

来源：一次 310P 开发会话内，对同一算子的 e2e 报告与 `msprof` kernel 级采集（单例探针 + 标准 `--compare` 全量）的实测对照。

- 标准 `--compare`（`--warm-up=3`、`--repeats=1`，10 代表例）基线 geomean ≈ 0.50x（相对参考实现），10/10 有效（来源平台：310P；证据等级：tool_observed）。
- 同一轮 `op_summary_*.csv`（110 行）中，自定义主 kernel 一行独大，转换/拷贝/转置 kernel 均为主 kernel 的百分之几（来源平台：310P；证据等级：tool_observed）。
- 同批 e2e 口径 40 例全过、geomean ≈ 1.7x，与 kernel 级结论相反（来源平台：310P；证据等级：tool_observed）。
- 按减少回环方向重写后，同口径 geomean ≈ 1.02x、10/10 有效（来源平台：310P；证据等级：tool_observed）。
- 探针首次采集因输入未搬 NPU 报 `NotImplementedError: Could not run ... with arguments from the 'CPU' backend`，`.npu()` 后 exit=0（来源平台：310P；证据等级：tool_observed）。

## 失效边界

- 前提是“每 chunk 有核内算出的中间矩阵要再进 L0”；操作数全部来自 host 预排 GM 的 kernel，回环次数本就少，本判据不适用。
- 主 kernel 占比不到九成时先查 host 侧与转换 kernel，不要套本条。
- 该判据依赖 `msprof --task-time` 的 `op_summary` 输出；其它代际（A2/A3）的 cube 取数路径不同，未验证，推断可迁移。
- **优化后的 kernel 源码不在本轨迹内**（开发会话的独立工作区），只能复核其测量产物与提交文本，不能复核实现细节；因此本卡不提供重写配方，也不应据本卡复述具体重写手法。
- CANN 版本未记录：涉及版本行为的结论（如某事件在特定版本的行为）不适用本卡。
- 未决项：v0 的绝对 Task Duration、逐 chunk 的 MTE/MMAD 细分未采集，“回环次数 ↔ 耗时”仍是比例级证据，未做逐项删减的消融实验。
- 未决项：本例重写态存在 ≤1 bf16-ulp 的跑间翻转（远小于 1e-3 门），根因未闭合（候选：出口裸 cvt）。

## 坏实践

- 用 e2e 计时（`torch.npu.Event` / 墙钟）给融合 kernel 下性能结论：融合把 launch 数从 N 降到 1，e2e 比值会被 host 开销与算子数放大，和 kernel 级结论可以完全相反。
- 看到 kernel 慢就先换数学近似（降阶、丢项、放宽指数范围）：本例近似的收益是 0 阶，收益全在回环次数与屏障数上。
- 把“附属转换 kernel 是大头”当结论：本次捕获里转换 kernel 合计不到主 kernel 的十分之一，且可下沉进 kernel；按这个误判优化会改错对象。

## 误诊

- 误诊一：“tile 太小，cube 没吃满”→ 去调 tile 尺寸/提高 Mn 利用率。实际闲置原因是每个结果都要经 GM 回环才能再进 L0，调 tile 无用。
- 误诊二：“host 侧 staging 是瓶颈”→ 只优化 host。host 只占单次调用的一小部分；主 kernel 本身占了九成。
