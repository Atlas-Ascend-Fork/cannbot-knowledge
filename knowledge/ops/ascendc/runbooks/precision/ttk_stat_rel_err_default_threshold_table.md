---
type: "Runbook"
title: TTK stat_rel_err 默认阈值 fp32 2^-13
description: golden 不写 threshold 时 TTK 按 dtype 默认表取阈值（fp32=2^-13≈1.22e-4）并以 mere<th AND mare<10×th 判定，spec numerical_tolerance 不直接生效。
tags: [task.testing, topic.precision]
status: stable
sources: []
created_at: '2026-09-09T11:49:41Z'
updated_at: '2026-09-09T11:49:41Z'
platforms: ["950"]
---
# TTK stat_rel_err 默认阈值 fp32 2^-13


## 现象

在用 TTK kernel 模式对 AscendC 算子（本例为 GRU Cell 反向融合算子的开发分支成品 kernel）跑白盒精度套件、判读失败用例时，发现 `result.csv` 的 `precision_metrics` 里实际生效的比对阈值是 `0.0001220703125`（即 2^-13），而算子 spec.yaml 的 `numerical_tolerance` 声明 fp32 rtol/atol=1e-5、用例 CSV 的 `precision_tolerances` 列也写 1e-5——两者都与实测阈值对不上。当时 golden（TestSpec 格式 `golden.py`）的容差声明只写了判据名、没写数值：

```python
    # 计算类算子（Elementwise/Reduction/FusedComposite 数值计算范式）浮点输出 → stat_rel_err
    tolerance = {
        "float32": {"standard": "stat_rel_err"},
        "float16": {"standard": "stat_rel_err"},
        "bfloat16": {"standard": "stat_rel_err"},
    }
```

同一套件里还能观测到：某路输出 mare=7.33e-4，超过了单阈值 th=1.22e-4，但 TTK 判 `pass=true`——因为实际判据是 `mere < th AND mare < 10×th` 的双指标结构，不是单阈值。若按 spec 的 1e-5 去推"mare 预算 = 10×1e-5 = 1e-4"，与 TTK 实际预算 10×2^-13≈1.22e-3 会差 12 倍，判读结论直接错。

## 适用场景

- 工程形态：TTK kernel / GEIR 模式白盒精度评测（`ttk kernel --plugin <golden.py>`），判读 `result.csv` / `result_oom.csv` 的精度列。
- API 路径：TTK 比对框架 `ttk/core_modules/comparison/resolve.py`（阈值解析）+ `ttk/core_modules/comparison/stat_rel_err.py`（判据实现）；golden TestSpec 的 `tolerance` 字段。
- 验证过的平台与 CANN 版本：Ascend950PR_9579 + CANN cann-9.0.0-beta.2（TTK 检出于 /tmp/ops-test-kit；与 frontmatter `platforms` 一致）。
- 适用粒度：`platform_wide`（TTK 工具行为，跨算子适用）。
- 路线优先级：recommended_fastpath（判读规则，无替代路线）。
- 明确不适用 / 未验证场景：CLI `--compare` 显式传阈值、或 golden `tolerance` 显式声明 `threshold` 字段的场景（两者优先级高于默认表，本卡未验证其具体覆盖行为）；`close`/`cosine`/`binary` 等其他比对 standard。

## 判别方法

机制：TTK 的浮点比对阈值按三级优先级解析——CLI > golden TestSpec `tolerance` 声明 > `stat_rel_err` 默认表。golden 只声明 `{"standard": "stat_rel_err"}` 而不给 `threshold` 时，落到默认表，与 spec.yaml 的 `numerical_tolerance`、用例 CSV 的 `precision_tolerances` 列均无关（后两者不参与该判定链）。

默认表源码（`ttk/core_modules/comparison/resolve.py`，verbatim）：

```python
# 2.1 stat_rel_err 阈值表（resolve_tolerance 是唯一解析点——比对类不查表）
THRESHOLDS = {
    "float16": 2**-10,
    "bfloat16": 2**-7,
    "float32": 2**-13,
    "float8_e4m3fn": 2**-3,
    "float8_e5m2": 2**-2,
}
DEFAULT_THRESHOLD = 2**-13
```

判据实现源码（`ttk/core_modules/comparison/stat_rel_err.py` 的 `compare_impl` 核心，verbatim）：

```python
    def compare_impl(self) -> EachCompareResult:
        # 空数组已在 compare() 入口 _check_empty 统一短路，这里只处理非空
        # threshold 是 resolve_tolerance 解析好的最终值（经 params → options 传入），不查表
        actual, golden = self.output, self.golden
        T = np.promote_types(np.dtype(np.float32), np.promote_types(actual.dtype, golden.dtype))
        a = actual.astype(T)
        g = golden.astype(T)
        th = self.tol_options["threshold"]

        with np.errstate(invalid="ignore", divide="ignore"):
            rel_err = np.abs(a - g) / (np.abs(g) + FLOOR)
            # ……（NaN/Inf 一致性短路，略）……
            mere = float(np.mean(rel_err[mask]))
            mare = float(np.max(rel_err[mask]))
            passed = mere < th and mare < MARE_RATIO * th
```

其中 `MARE_RATIO = 10`、`FLOOR = 1e-7`（文件顶部算法常量）。即：
- `mere` = 全部元素相对误差的均值，`mare` = 最大值；
- 相对误差分母带 1e-7 的下限保护：`rel_err = |a − g| / (|g| + 1e-7)`；
- 通过条件是双指标：`mere < th` **且** `mare < 10 × th`。

判读操作：拿到失败用例后直接看 `result.csv` 该行的 `precision_metrics`（dict 形式含 `standard/mere/mare/threshold/pass/reason`），用其中的 `threshold` 字段作为实际生效阈值，不要用 spec/CSV 里的容差列推算。可用一小段脚本跨 dtype 抽查 threshold 字段验证默认表生效（fp32 用例 0.0001220703125、bf16 用例 0.0078125、fp16 用例 0.0009765625）。

## 设计决策

本卡为评测判读规则，无代码设计取舍，无证据。需要提醒的取舍点是：若希望 TTK 判定与 spec 数值容差严格一致，应在 golden 的 `tolerance` 里显式写 threshold（走第二优先级），而不是依赖默认表——但显式覆盖行为本 trace 未验证，属未验证场景。

## 验证信号

来源说明：以下信号来自一次 AscendC 算子开发分支的白盒精度套件执行（TTK kernel 模式、上板 Ascend950PR_9579、CANN 9.0.0-beta.2），判读失败用例时从 result.csv 与 TTK 源码双侧核对得出。

- 同一套件三个 dtype 用例的 `precision_metrics.threshold` 实测：fp32 用例 0.0001220703125 = 2^-13、bfloat16 用例 0.0078125 = 2^-7、float16 用例 0.0009765625 = 2^-10，与 `resolve.py` 的 THRESHOLDS 默认表逐一吻合（来源平台：950；证据等级：tool_observed）。
- 判据结构实测：某 fp32 用例一路输出 mare=7.33e-4 > th=1.22e-4 但 `pass=true`，与其并列的另一路输出 mare=1.24e-3 ≥ 10×th=1.22e-3 时 `pass=false` 且 reason 为 `threshold exceeded: mare(1.24e-03>=0.001220703125)`——证实预算是 10×th 而非 th（来源平台：950；证据等级：tool_observed）。
- golden `tolerance` 无 threshold 声明的源码事实（上卡内联代码块），与实测阈值来自默认表的推断互洽（来源平台：950；证据等级：tool_observed）。

## 失效边界

- 默认表数值属于 TTK 检出版本的行为，TTK 升级后可能变化；本卡锚定实测版本（CANN cann-9.0.0-beta.2 环境下的 /tmp/ops-test-kit 检出，无精确版本号事件）。
- `resolve.py` 源码注释提示存在 dtype 字符串解析的鲁棒性处理（`_dtype_str` 优先 `numpy.dtype(...).name`，异常时回退字符串切分；回退路径可能令 bfloat16 查表 miss 而回落 DEFAULT=2^-13 使阈值过严）——该坑在本 trace 中**未实际发生**（bf16 用例正确切到 2^-7），仅作边界提示，未验证。
- spec `numerical_tolerance` 与 TTK 默认阈值的口径差（fp32: 1e-5 vs 1.22e-4）是"哪边该改"的验收口径问题，本卡只记录实际生效行为，不裁决口径。

## 坏实践

- 拿 spec.yaml 的 `numerical_tolerance`（如 fp32 1e-5）推算 TTK 的 mare 预算（10×1e-5=1e-4），再拿它判读 TTK 的 FAIL/PASS——与实际预算 1.22e-3 差 12 倍，会把边缘超差误判为大幅超差（或反向）。
- 只看 mare 是否超 th 就断言 FAIL，忽略 `mere < th AND mare < 10×th` 的双指标结构（mare 在 th 与 10×th 之间时 TTK 判 PASS）。
- 以为用例 CSV 的 `precision_tolerances` 列会传给比对器——实测不参与 stat_rel_err 判定链。

## 误诊

- 把"threshold=1.22e-4 与 spec 1e-5 不一致"误诊为 TTK bug 或 golden 配置错误：实际是设计好的三级优先级 + dtype 默认表机制，golden 不写 threshold 就该落到默认表。
- 把 mare 超出 th（但小于 10×th）的输出当成失败逐个排查：TTK 此时判 pass，失败清单应以 `pass`/`reason` 字段为准。

## 未决事项

- 用例 CSV `precision_tolerances` 列在 TTK kernel 模式下是否完全不进判定链，只做了"实测未生效"的观测，未逐行验证其消费路径。
- golden `tolerance` 显式声明 `threshold` 时的覆盖行为未验证；如需让判定与 spec 对齐，可作后续实验。
