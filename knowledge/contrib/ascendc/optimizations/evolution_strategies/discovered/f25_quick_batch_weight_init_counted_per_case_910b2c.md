---
type: Optimization
title: "F25: quick-batch 口径把「模型首次 forward 的权重初始化」计入每个 case 的被测时间——加速比存在人造天花板"
description: "某些算子在 forward() 内惰性构造权重；quick-batch 口径的计时窗口内每个 case 只跑一次 forward，权重构造 kernel 被按 stream 求和计入该 case，于是小 shape 的加速比被压向 1.0，存在与内核无关的人造天花板。卡片给出识别、双口径判定与合法的包装层摊薄方法。"
tags:
  - task.debugging
  - topic.attention
  - topic.programming_model.execution_unit.vector
  - topic.compute.reduction
  - topic.compute.normalization
  - topic.compute.quantization
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/guide/operator_practice/performance_analysis/collect_performance_data.md
    role: supporting
  - resource: https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/f25_quick_batch_weight_init_counted_per_case_910b2c.json
    role: evidence
created_at: "2026-10-28T00:00:00Z"
updated_at: "2026-10-28T00:00:00Z"
platforms:
  - a2
---
> 证据：基线/变体与逐 case 数据见 [证据包 cases/f25_quick_batch_weight_init_counted_per_case_910b2c.json](https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/f25_quick_batch_weight_init_counted_per_case_910b2c.json)。

> 平台说明：`a2` 对应 Ascend 910B 系列（本卡实测型号见正文）；`a3` 对应 Ascend 910C 系列。

# F25: quick-batch 口径把「模型首次 forward 的权重初始化」计入每个 case 的被测时间——加速比存在人造天花板

## 现象

某些算子的 `model.py` / `model_new_ascendc.py` 在 `forward()` 里**惰性构造权重**
（`torch.empty(...)` + `nn.init.kaiming_uniform_`，或 `torch.randn`），并用 `self._cache` 缓存。
这类算子在 `ops-profiling` 的 `--quick --quick-batch` 口径下会得到**与形状几乎无关的恒定耗时**，
小 shape 的加速比永远贴在 1.0 附近，无论内核优化多少。

判据：T 从很小变到很大而被测时间几乎不变 ⇒ 存在固定地板；一个 T=1 的算子不应跑出毫秒级时间。

## 根因（两层，都在 harness 侧，被测实现无法直接优化）

1. `msprof_perf_summary.py::_generate_batch_wrapper_script` 把 **`model = cls(...)` 与整个 forward
 都放在 `with torch.npu.stream(_s):` 内**，且 quick-batch 的 `loop_iters = repeats`（通常 1），
 即**计时窗口内每个 case 恰好一次 forward**。
2. 于是这一次 forward 触发的**权重构造 kernel**（`aclnnInplaceUniform_DSARandomUniform` /
 `DSARandomNormal` / `Cast` / `OnesLike`）落在该 case 的 stream 上，被
 `_parse_msprof_duration_quick_batch` **按 stream 求和**计入该 case。
3. 而同一条 stream 上的**真实算子 kernel 数量远少于权重构造 kernel**，两者混在一起。

PyTorch 参考侧（`model.py`）用同样的构造代码，**ref 与 asc 各付一次**，所以比率被压向 1.0。

## 量化模型（不含实测数值）

- 设 `F` 为权重构造的固定成本（与 T 无关），`ref_kernel` / `asc_kernel` 为两侧真实内核时间。
- 被测时间 ≈ `F + kernel`；加速比 = `(F + ref_kernel) / (F + asc_kernel)`。
- 取 `asc_kernel → 0` 得天花板 `1 + ref_kernel/F`。对全部 case 求几何平均即得该算子的口径上限；
 大 T case 的上限较高，小 T case 可能只有接近 1.0。
- 反向验证：把 asc 拆成 `F + kernel` 后，应与 msprof 单点分段逐段对得上。

## 二次陷阱：跨运行漂移与 warm-up 不一致

同一份**未改动**的基线内核，在不同时间点、不同 `--warm-up` 下用同一 ref 缓存测量，结果会有
可观差异（同一份代码可差几个百分点以上）。⇒ 绝对数值不可跨时间点、跨 warm-up 比较；
DVFS/预取状态会随 warm-up 次数变化。

## Resolution

1. **先判断有没有被这个地板污染**：在 `task_time.csv` 里找该 case 的 stream 是否含
 `*DSARandomUniform*` / `*DSARandomNormal*` / `*OnesLike*` 行；若有，则被测时间 = 权重构造 + 内核。
 也可以用「时间是否随形状缩放」快速判断。
 把基线内核与候选内核在同一时段、同一 `--warm-up`、同一 ref 缓存下各测一次，
3. **目标设定**：对这类「权重构造占主导」的算子，进 Init 时就要算出天花板，写进世界模型
 `open_questions`；不要把一个物理不可达的 target 当作失败判据。
4. 若确实需要评估真实内核算力，用 msprof 单点（`--per-case` 或自建 `msprof --application` 脚本）
 拿到无地板的 kernel 时间，但**性能分数仍必须来自官方 quick-batch**，两者不可混用。

## 来源

来自内部进化运行；运行标识、设备、用例与逐 case 数据见证据包。

## Resolution 补充：包装层可以合法摊薄 F

上文「都在 harness 侧，被测实现无法优化」需要修正：harness 确实改不了，但
`model_new_ascendc.py` 这一层可以合法地「跨实例复用已初始化权重」，因为
(1) wrapper 对每个 case 都 `cls(...)` 新建实例（`_cache` 是实例属性，必 miss）；
(2) golden 在构造前用 `torch.manual_seed(hash(key_biz) & 0xFFFFFFFF)` **确定性重播种**并在返回前
恢复 RNG 状态 ⇒ 权重内容只是 `(key_biz, dtype)` 的纯函数，复用与重建**逐位等价**。

改法（类级缓存）：
```python
class ModelNew(nn.Module):
 _shared_cache: dict = {} # 类级，跨实例共享
 def __init__(self):
 super().__init__()
 self._cache = ModelNew._shared_cache
```

效果方向：harness 口径（含 F）显著抬升，而纯内核口径基本不变（内核二进制未改）。
注意 quick-batch 会把 case 切成多个独立进程，模块级缓存不跨进程 ⇒ 仍有一部分 case 实付 F。

**边界（不要越线）**：在 `model_new_ascendc.py` 里读 `*_perf_cases.jsonl` / `<op>.json` 预生成全部配置的
权重（把剩余 F 也移出计时窗）属于利用测试文件预热 = hardcode test shapes，**禁止**。只允许与用例无关的
「同配置复用」。

**结论**：这类算子的「达标判定」必须双口径并列 —— harness 口径（含 F，可被包装层摊薄）与纯内核口径。

## 验证状态

本卡为 `status: stable`：定量结果与运行标识见证据包 `cases/f25_quick_batch_weight_init_counted_per_case_910b2c.json`；引用时请结合上文适用条件与失效边界判断适用范围。

