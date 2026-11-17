---
type: Runbook
title: 墙钟比 kernel 慢 10 倍：按算子拆账，别猜 host 物化
description: 端到端墙钟约为自研 kernel 的 10 倍时，把这 9 成差额归因于 host 侧标量物化只是猜测；逐算子拆账显示大头是 host 预处理链引入的元级小算子。
tags: [task.debugging, topic.performance.analysis, topic.implementation.api_layer.utils_api]
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/8746f7ced6cef47e3fd7abd64c0eb827e28e2b56/docs/zh/guide/operator_practice/performance_analysis/analyze_performance_data.md
    role: supporting
created_at: "2026-10-28T09:46:50Z"
updated_at: "2026-11-05T03:51:50Z"
platforms: ["310p"]
---

# 墙钟比 kernel 慢 10 倍：按算子拆账，别猜 host 物化

## 现象

310P attention-backward 移植版在最大用例上端到端每调用墙钟约为**自研 Ascend C kernel 自身耗时的 10 倍**（同一调用、同一平台），而 ref 路线（torch 小算子拼接，同平台）只有该移植版的约 **0.21x**（即成对比较下移植版慢约 5 倍）。

同一调用的 `torch_npu` profiler 却显示：自研 kernel 每调用只占墙钟的约十分之一（`kernel_details.csv` 里按 Name 聚合后，单个 attention-bwd 类 kernel 的均值远小于墙钟），其余差额全在别处。首调用还有一次显著更长的冷启动（编译/分配器），warm 后稳定，必须 warm-up 后再取数。

**必须先说明：最初的归因是错的。** 拆账前的推理是：“host C++ 掩码循环 数百万次标量写 + 十余 MB H2D ≈ 每调用数十毫秒”，与墙钟“完全吻合”，看起来就此结案。这是**推断（非实测）**，不是测量结论。

实测把这个循环向量化搬到 NPU 后：墙钟只降了约 15%，相对参照路线由 0.21x 升至约 0.25x（按 0.21/0.85 换算，两档数字取整口径见失效边界）。**这批标量写只值墙钟的十分之一强，不是全部。** 归因“数值上吻合”不等于因果成立——这一步是本卡最值钱的部分：如果就此收兵，会认为“已经优化到位”，而实际大头一点没动。

真正的做法是逐算子拆账（`kernel_details.csv` 按 Name 聚合 Duration 的 **sum**，3 个活跃 iter 求均值；实例数 n= 与 avg 由脚本同时打印，倍数一律取 sum 口径），把这些算子按相对自研 kernel 的倍数排开：

| 算子（Name 前缀） | 相对自研 kernel 的耗时倍数（同一次调用，按 Name 聚合 sum） |
|---|---|
| `GatherElements` | 约 4.9x |
| `ScatterElements` | 约 1.4x |
| `Add` | 约 0.47x |
| `LessEqual` | 约 0.31x |
| 自研 attention-bwd kernel | 1.00（基准） |

即：两条元级索引算子（`GatherElements` + `ScatterElements`）合计约为自研 kernel 的 6 倍 ≈ **墙钟的六成**；表内全部条目（含 `Add`/`LessEqual`）约 7 倍 ≈ 七成——全是 host 侧预处理链引入的**元级小算子**（详见同批 gather/scatter 卡）。早期版本写“占墙钟约 80%、两个 ScatterElements”，该占比无法由上表（按 Name 聚合 sum）复算，已弃用；需精确占比时重导 CSV 按 sum 与实例数 n= 复核。

**判断“哪一段慢”的唯一可靠手段是 op 级拆账**，尤其是当 host 侧有 `torch::zeros/accessor` 循环、`permute/contiguous`、`cast` 这类“看起来免费”的调用时。

## 适用场景

- 工程形态：Kernel 直调 + 大量 host 侧张量预处理（reshape/permute/cast/掩码物化）。
- API 路径：`torch_npu.profiler` 的 `kernel_details.csv` 逐算子粒度拆账（`Name` + `Accelerator Core` + `Duration(us)` 列）。
- 验证过的平台与 CANN 版本：310P（dav-m200 / DAV_2002）+ CANN 9.1.0 + torch_npu。
- 适用粒度：operator_family（“自定义 kernel + host 预处理链”的性能排查）。
- 路线优先级：recommended_fastpath（先拆账再优化）。
- 明确不适用或未验证场景：纯单 kernel 算子（wall ≈ kernel，无需拆）；没有 profiler 权限/无法采集的环境；其他代际未验证。

## 判别方法

拆账流程本身即为判别方法：

1. 取 op 级明细（`kernel_details.csv` 在 `ASCEND_PROFILER_OUTPUT` 下）。
2. 按 `(Name, Accelerator Core)` 聚合 `Duration`，把“自定义 kernel”与“框架小算子”分账，按总时长降序取前 14 名。
3. 同时用 wall 计时确认迭代稳定（排除首调用冷启动污染）。

判读规则（记 `Σkernel` = `kernel_details.csv` **全部条目** `Duration` 之和，同次调用、单流串行假设——本 trace 单流；纯 CPU 循环不出现在该 CSV 里）：

- `wall >> Σkernel` → 差额在 **kernel 之外**：Python 派发 / 同步 / CPU 循环 / H2D——此时才该怀疑 host 标量物化（CPU 循环不产生 kernel 条目，榜单上看不到它）。
- `wall ≈ Σkernel` → 差额**就在榜单里**：看前几名；若前几名是框架小算子（`Gather`/`Scatter` 等），瓶颈是 host 预处理链物化出的 NPU 小算子，不是“调度开销”，也不是纯 CPU 循环——本卡案例即此形态（自研 kernel 只占墙钟约十分之一，榜首是 `GatherElements` 4.9x）。
- 首 iter 异常大 → 冷启动，必须 warm-up 后再取数。

## 完整代码

```bash
# 1) 取 op 级明细（kernel_details.csv 在 ASCEND_PROFILER_OUTPUT 下）
D=$(ls -d <diag-dir>/prof/*_ascend_pt | head -1)/ASCEND_PROFILER_OUTPUT
```

```python
# 2) 按 (Name, Accelerator Core) 聚合 Duration，把"自定义 kernel"与"框架小算子"分账
import csv, collections
rows = list(csv.DictReader(open(f"{D}/kernel_details.csv")))
agg = collections.defaultdict(lambda: [0, 0.0])
for r in rows:
    d = float(r["Duration(us)"])
    k = (r["Name"], r["Accelerator Core"])
    agg[k][0] += 1; agg[k][1] += d
for (n, ac), (c, d) in sorted(agg.items(), key=lambda x: -x[1][1])[:14]:
    print(f"{n[:44]:44s} {ac:6s} n={c:4d} sum={d:9.1f}us avg={d/c:9.1f}us")
```

```python
# 3) 同时用 wall 计时确认迭代稳定（排除首调用冷启动污染）
for i in range(3):
    t0 = time.time(); op(*args); torch.npu.synchronize(); print(i, (time.time()-t0)*1e3, "ms")
```

## 设计决策

- 优化顺序由拆账决定，而不是由代码“看起来重”决定：本例先做的是 gather/scatter 消除（占墙钟约六成、含关联小算子约七成的那部分），不是 kernel 内部调优（只占墙钟十分之一强）。
- 保留 ref 路线的同机对比作为分母：只报“我们 xx ms”没有意义，必须成对给出参照路线与平台。
- 拆账表只报**相对自研 kernel 的倍数**，不把单次绝对耗时当结论——绝对口径随用例几何与机器状态浮动。

## 系统信息

- 平台 310P（dav-m200 / DAV_2002），CANN 9.1.0，torch_npu profiler（`ASCEND_PROFILER_OUTPUT/kernel_details.csv`）。
- 工具口径：所引官方文档对应 msprof 的 `op_summary_*.csv`（按算子看耗时占比/流水信息）；本卡实测用 torch_npu profiler 的 `kernel_details.csv`，列名（`Name`/`Accelerator Core`/`Duration(us)`）为该工具口径，两者是不同工具的同类粒度输出，不能混列。
- 相关文件：`host/<generic>_host.cpp`（预处理链）、`kernel/<generic>_bwd.cpp`（自定义 kernel）。
- 采集：`torch_npu.profiler` 取 3 个活跃 iter 的均值；wall 用 `torch.npu.synchronize()` 包围的 3 次取中位。

## 性能影响

- 方向性结论（成对，同调用同平台 310P）：自研 kernel 只占墙钟约十分之一；元级 `gather`/`scatter` 类算子合计约为自研 kernel 的 6 倍（≈墙钟六成；含 `Add`/`LessEqual` 等表内全部条目约 7 倍 ≈ 七成）。因此“优化 kernel 内部”在该形态下的上限约为墙钟的十分之一。
- 把 host 标量循环搬到 NPU：墙钟只降约 15%（相对参照路线由 0.21x 升至约 0.25x，按 0.21/0.85 换算），说明该改动的收益远小于“看起来的大头”。未做受控 A/B 的分项归因（同一会话内只有“改前/改后”两档）。

## 预防

- 先拆账，再决定改哪里；不要在“数值看起来吻合”的假设上投入几天。
- 任何 host 侧逐元素 `accessor` 写、`permute().contiguous()`、整张量 `cast` 都要在拆账表里核对是否变成框架小算子。
- 报性能时永远附参照路线与平台，禁止单边绝对数。

## 验证信号

来源：一次 310P attention-backward 迁移会话，torch_npu profiler op 级拆账 + 本地挂钟。

- 同一最大用例：本地墙钟约为自研 kernel 均值的 10 倍量级（来源平台：310P；证据等级：tool_observed）。
- 同一用例：ref 路线（torch 小算子拼接）墙钟相对移植版约 0.21x（来源平台：310P；证据等级：tool_observed）。
- 把 host 侧数百万次标量写的掩码循环搬到 NPU 后，墙钟仅降约 15%，相对参照路线由 0.21x 升至约 0.25x（0.21/0.85 换算；两档数字取整口径见失效边界）（来源平台：310P；证据等级：tool_observed）——**证伪了“标量循环≈全部墙钟差额”的归因**。
- 同一份 CSV 中 `GatherElements` 约为自研 kernel 的 4.9x、`ScatterElements` 约 1.4x，两条元级索引算子合计约 6 倍（来源平台：310P；证据等级：tool_observed）。

## 失效边界

- 本地挂钟**包含 Python 派发**，相对 msprof 的 `Task_Duration` 有系统性膨胀（本 trace 中同一实现的本地挂钟与 msprof 数字相差约 1.5x）。用挂钟只能做**同机成对比较**，不能直接当 gate 指标。
- 结论依赖用例几何：小用例上墙钟与 kernel 的比值同样由固定开销的框架小算子主导（实测小例的 wall/kernel 比值约 26x 量级），但各项占比不同，不能把最大用例的比例外推。
- profiler 会把 `scatter_add_` 之类映射成 `ScatterElements` 名字，按名字推断“是哪一行代码”会错——必须回到代码点定位（本例一度误以为已删除的 scatter 又出现了）。
- 0.21x 与约 0.25x 的取整口径：0.21x 是改前实测；0.25x 按“改后墙钟 −15%、ref 不变”由 0.21/0.85 换算得出，**非同一 run 的成对实测**，只作方向性表述。
- 未验证其他代际平台与其他 profiler 版本的列名。

## 坏实践

- 用“数值正好对得上”结案（墙钟 ≈ 推算出的 host 标量写时间）。
- 只看自定义 kernel 的耗时并据此宣布“kernel 已足够快/太慢”。
- 在没有 warm-up 的数字上做优化决策（首调用冷启动会彻底扭曲均值）。
- 把“尚未实测的 host 物化推测”写成测量结论再据此排期。

## 误诊

- **误诊 1（推断，非实测）**：认为 host 侧数百万次标量写 + H2D 就是墙钟差额的全部；向量化后只省约 15%，证伪。
- **误诊 2**：以为 profiler 里没看到 `scatter_add_` 就等于它不存在——它被映射成 `ScatterElements`，必须回代码点核对。
