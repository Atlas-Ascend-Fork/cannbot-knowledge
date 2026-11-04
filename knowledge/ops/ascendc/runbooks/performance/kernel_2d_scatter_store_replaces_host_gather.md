---
type: Runbook
title: 输出暂存 + host gather 改为核内 2D 散射直存
description: kernel 先把每块结果整块写进暂存区、再由 host 按索引重排，需要数十 MB 索引 H2D 与逐元素 gather；让 MTE3 直接按目标行主序散射写出，整条辅助链消失。
tags: [task.optimization, task.design, topic.data_movement.data_copy, topic.memory]
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/8746f7ced6cef47e3fd7abd64c0eb827e28e2b56/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/data_move/DataCopy_GMAndUB_highdim_split.md
    role: primary
  - resource: https://gitcode.com/cann/asc-devkit/blob/8746f7ced6cef47e3fd7abd64c0eb827e28e2b56/docs/zh/guide/operator_practice/simd_operator_optimization/memory_access/efficient_transfer_api.md
    role: supporting
created_at: "2026-10-28T09:46:50Z"
updated_at: "2026-10-28T09:46:50Z"
platforms: ["310p"]
---

# 输出暂存 + host gather 改为核内 2D 散射直存

## 现象

kernel 尾声把每个工作单元的 64×64 结果**整块连续**写进一块暂存区（各单元按 `(u·ND+dv)·4096` 互不重叠），host 再按“单元 → 输出行号”的映射把暂存区重排成最终布局。

功能正确、精度通过，但性能采集里：

- 小形状上 **v 的预转置 + 输出重排**两条辅助链合计占了辅助开销的 **87%**；
- 某个巨例上这两条链合计仍占 **63%**；
- 重排需要一次**数十 MB 量级索引**的 H2D，以及逐元素 gather（gather 在采集里以 `GatherV2` 出现，另有 `MaskedFill`/`Cumsum` 等 AI_CPU 派发）；
- 主 kernel 本身在同批采集里占比很小。

把 kernel 尾声改成“按目标行主序做 2D 散射直存”、删掉 host 侧整条重排链之后，上述辅助开销消失，精度通过。

## 适用场景

- 工程形态：kernel 直调；kernel 输出需要落到“行号由元数据决定、列由 head/分片决定”的最终布局。
- API 路径：`DataCopy(GlobalTensor, LocalTensor, DataCopyParams(blockCount, blockLen, srcStride, dstStride))`，从 UB 直接散布写到 GM。
- 验证过的平台与 CANN 版本：310P（DAV_2002 / dav-m200）+ CANN 9.1.0。
- 适用粒度：operator_family —— 任何“每单元一块方形结果、目标行号不连续”的算子。
- 路线优先级：recommended_fastpath（一次 MTE3 散射，省掉整个 host 重排链）。
- 明确不适用或未验证场景：不适用于“目标位置完全随机（不可用固定步长表达）”的布局；这类必须留在 host 侧做 gather。

## 根因

原实现的代价全部来自“把重排推迟到 host”：

1. **暂存区写**：本来可以直接写最终位置，却先写暂存，多了一次全量搬运；
2. **索引 H2D**：host 需要知道“暂存区的哪一块对应输出的哪几行”，这份索引随行数线性增长（本轨迹到数十 MB 量级），每次调用都要重新构造并上传；
3. **逐元素 gather**：设备上按索引搬运，退化成小拷贝洪流（与 `index_copy_` 同类问题，见同批“index_copy_ 退化为逐元素 memcpy”卡）。

而目标布局本身是**规则的**：单元 `u` 负责从 `qRow` 开始的连续若干行，列范围由 `h`、`dv` 决定，行与行之间的跨越是固定步长。也就是说，一次 2D 散射就能表达：

- 每条 burst = UB 里的一行（64 个 f32 = 256B = 8 个 32B 块）；
- `dstStride` = 目标行距与源行距之差，单位同样是 **32B 块**（见同批精度卡的 `dstStride` 单位结论）；
- `blockCount` = 本单元本 tile 的**有效行数**（末 tile 可能不足一个 tile 宽）。

只要保证“每个单元的写区间互不重叠”，就不需要任何 host 侧重排。

## 判别方法

1. 看辅助链的构成：如果 host 侧出现“大索引张量 + gather/scatter”，先问“目标位置能否用固定步长表达”。
2. 算一算索引规模：索引元素数随行数线性增长时就高度可疑。
3. 在采集里确认主 kernel 的占比：若主 kernel 占比很低而 `GatherV2`/AI_CPU/`N/A` 任务占比很高，优化点在 host 链而不是 kernel。
4. 改完后用“逐单元写区间是否重叠”做正确性自检（行区间按单元划分、列区间按 head/分片划分，二者不交叠）。

## 完整代码

**kernel：改前（整块连续写暂存区）**

```cpp
            // 整块存 GM 尾部 scratch: (u·ND+dv)·4096 —— 每 unit 半片互不
            // 重叠（行区直接落会在 H>1 时跨 h 互踩）; host 按同一公式 gather。
            // 出口沉降: 对前写会被出口截断 → 对后幂等重存整块
            DataCopy(gmScr[metaPad + (static_cast<int64_t>(u) * ND + dv) *
                                    T64 * T64],
                     t2, DataCopyParams(512, 1, 0, 0));
            SetFlag<HardEvent::MTE3_V>(ev3V);
            WaitFlag<HardEvent::MTE3_V>(ev3V);
            DataCopy(gmScr[metaPad + (static_cast<int64_t>(u) * ND + dv) *
                                    T64 * T64],
                     t2, DataCopyParams(512, 1, 0, 0));   // 幂等重存整块
```

**kernel：改后（2D 散射直存行主序）**

```cpp
            // 2D 散射直存 gmOut 行主序（替代整块存 scratch + host gather）。
            // 目标: 行 (qRow+i) 列 h·D+dv·64+j → 每 burst = t2 一行
            // 64 f32(256B=8×32B), dst 行距 H·D f32 → dstStride=(H·D−64)/8
            // （H·D∈{128,256,512} → 8/24/56, 整数）。unit/tile/h/dv 写区
            // 互不重叠（行区间各归各 unit, 列区间各归各 h·dv）。仅存有效行
            // nValid = min(64, lenB − t·64) ≥ 1（末 tile 越界行不落）。
            // 出口沉降: ev3V 对可 early-fire, 对前写会被出口截断 → 对后
            // 幂等重存（对后写实证可靠）
            const int32_t nValid =
                (lenB - tEff * T64 < T64) ? (lenB - tEff * T64) : T64;
            const uint8_t oGap =
                static_cast<uint8_t>((H * D - T64) / 8);
            const int64_t oBase =
                (static_cast<int64_t>(qRow) * H + h) * D + dv * T64;
            DataCopy(gmOut[oBase], t2,
                     DataCopyParams(static_cast<uint16_t>(nValid), 8, 0, oGap));
            SetFlag<HardEvent::MTE3_V>(ev3V);
            WaitFlag<HardEvent::MTE3_V>(ev3V);
            DataCopy(gmOut[oBase], t2,
                     DataCopyParams(static_cast<uint16_t>(nValid), 8, 0, oGap));
            PipeBarrier<PIPE_ALL>();
```

**host：改前（staging 里保留 vT 预转置 + 出口 gather）**

```cpp
//   vT:      逐 b 紧拼 [ΣnJt_b, H, ND, 64d, 64j]（行=d 列=j 列连续, 行距 64;
//            Nd2Nz+ift=false 的 B=(vT)ᵀ=V 要求）。
//   out32:   [sumL, H, D] f32; 出口按暂存区索引 gather 重排后 .to()
```

**host：改后（两条链删除，只剩垫尾拷贝）**

```cpp
// staging（大瘦身: vT 预转置与输出 gather 全删——两项合计曾占
// 小形状 87%/某巨例 63% 辅助开销（GatherV2×2 + MaskedFill/Cumsum AI_CPU +
// 数十 MB 级索引 H2D）; 现仅剩三份垫尾拷贝）:
//   q16/k16/v16: [sumL+64, H, D] f16 —— empty+copy_+尾 64 行 zero_
//   meta:    [max(units·64,8192)+8] i32 —— unit 段 + 尾 8 个信标
//   out32:   [sumL, H, D] f32, kernel 尾声 2D 散射直存行主序
```

## 设计决策

- **不在 host 侧“优化 gather”，而是删掉它**：只要布局规则，就应该在写出的那一刻直接写对位置；host 侧无论怎么优化都还要付索引构造与上传。
- **`dstStride` 用“f32 行距减本行宽度，再除以 8”**：单位是 32B 块，与 `blockLen` 一致；写成表达式而不是字面量，便于换 `D`/`H` 时自动成立。
- **只存有效行**：末 tile 的有效行数可能小于 tile 宽，越界行若不裁剪会写到下一个单元的行区间（多核并行时就是静默写坏别人的数据）。
- **保留“对后幂等重存”**：早期观测到“对前写会被出口截断”，重存一次的成本是每条一次 MTE3，比出错代价低。
- 该配方属 recommended_fastpath。

## 系统信息

- 目标平台 310P（DAV_2002 / dav-m200），CANN 9.1.0；tile 宽 64，`H·D` 与 tile 宽是“整数倍减去 64 后能被 8 整除”的关系（`(H·D−64)/8` 必须整除）。
- 相关文件：`kernel/<generic>.cpp`（尾声落地）、`host/<generic>_host.cpp`（staging 与出口）。
- 采集：同批 task_time/api_statistic，按算子名与 AI_CPU 派发分项。

## 性能影响

参照路线 = **同一算子的“整块暂存 + host gather”版本**（同平台 310P，同一采集口径成对观测）：

- 两条辅助链（v 预转置 + 输出重排）合计占小形状辅助开销 **87%**、占某巨例 **63%**；直存后这两项归零。
- 大索引 H2D 与 `GatherV2`×2、`MaskedFill`/`Cumsum` 派发随之消失。
- 绝对时延与倍数只留在中间产物，不进本卡；方向性结论是“辅助链占比从主项降到 0”。

## 预防

- 设计阶段先问一句：**“最终布局能不能在写出的那一刻就写对？”** 能就不要引入暂存 + 重排。
- 若必须暂存，至少在 host 侧把索引构造降到“一次 H2D + 一次整块 gather”，并检查索引规模。
- 散射写的 `blockCount` 一律用“有效行数”而不是“tile 宽”。

## 验证信号

来源：本会话内一次开发轨迹（单条轨迹）。

- 改前采集：辅助链两项合计占小形状辅助开销 87%、占某巨例 63%，主 kernel 占比很低；同批出现 `GatherV2` 与 AI_CPU 派发（来源平台：310P；证据等级：tool_observed）。
- 改动分批验证：先只回退同批的另一个实验性改动（装载方向），保留直存 → 精度恢复；随后全量 50 例精度 50/50 PASS（来源平台：310P；证据等级：tool_observed）。
- 改后同一采集口径下辅助链消失，最终一轮性能采集正常完成并落盘（来源平台：310P；证据等级：tool_observed）。

## 失效边界

- **`(H·D − T64)` 必须能被 8 整除**（即目标行距是 32B 的整数倍）；否则 `dstStride` 不能这样算，需要另设对齐策略。
- **写区间不重叠是硬前提**：当多个核并行处理同一输出行区间的不同列分片时，必须保证列分片不交叠；若布局上做不到，就要退回暂存 + 重排。
- **末 tile 必须裁剪 `blockCount`**：不做裁剪会静默写坏相邻单元（多核时更难查）。
- 不适用于“目标位置不可用固定步长表达”的随机散射。
- 未验证平台：其它代际未验证；`dstStride` 上限（本轨迹用到 `(H·D−64)/8` 的小值）在大行距下的可用范围未系统核对。
- **未决项**：本轨迹里“直存 + UB 内重排”两者仍然共存（重排保留用于把分形读出转成行主序），也就是说直存并没有消掉 UB 内重排本身；若要把重排也消掉，需要让 MTE3 直接从分形块按块写出（每块 16 行 × 16 列），该形态未尝试。

## 坏实践

- **用暂存 + host 重排承载“规则布局”**：把一次可表达的散射，换成一次全量搬运 + 索引上传 + 逐元素 gather。
- **`blockCount` 用 tile 宽而不是有效行数**：末 tile 越界写，多核下静默污染邻居。
- **只盯主 kernel 优化**：辅助链占比高时，kernel 再怎么优化都到不了目标（本轨迹先做了三轮 kernel 侧归因才发现主项在 host）。

## 误诊

- **误诊**：首轮性能归因曾把巨例的慢归给 kernel 本身，实际采集显示主 kernel 占比很低、辅助链才是主项。
- **误诊**：也曾试图在 host 侧“优化 gather 的写法”（减少中间算子），收益有限；真正的解法是把重排取消掉。
