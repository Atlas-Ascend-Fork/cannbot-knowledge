---
type: Runbook
title: "L0C 读出是 16×16 分形：须按块解码"
description: "fixpipe 从 L0C 读到 UB 的内容按 16×16 块置换排列；直接 reshape 成行主序会得到 0.2 级假误差，按块解码后与模拟逐位一致，存储链本身健康。"
tags: [task.debugging, topic.programming_model, topic.precision, topic.data_movement]
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/8746f7ced6cef47e3fd7abd64c0eb827e28e2b56/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_fractal_intro/key_fractal_format_details.md
    role: primary
  - resource: https://gitcode.com/cann/asc-devkit/blob/8746f7ced6cef47e3fd7abd64c0eb827e28e2b56/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_store/DataCopy_L0CToUB.md
    role: constraint
created_at: "2026-10-28T09:52:17Z"
updated_at: "2026-10-28T09:52:17Z"
platforms: ["310p"]
---

# L0C 读出是 16×16 分形：须按块解码

## 现象

把 L0C 的累加结果读出到 UB 后，直接按行主序 `reshape`（或直接按行主序写 GM、再由 host 按行主序比对）会得到一种很"像 bug"的误差：

- 误差量级 **0.2 级**，远大于 f16 模拟噪声（1e-4 级），且是**确定性的**——同一输入每次跑都一样；
- 输出**不是全零**，行/列都非空，只是"整体对不上"，容易被读成"算错了"或"搬错了"；
- 把同一块读出数据按 16×16 块重新解码后，与高精度模拟的误差回到 **1e-5 量级**（模拟噪声内）；
- 同时，**输出区与读出的原始块逐位一致**——说明存储链是健康的，搬运没有错，错的是"如何解释这块内存"。

## 适用场景

- 工程形态：kernel 直调；手写 Cube 数据流（`Mmad` → L0C → fixpipe/DataCopy 读到 UB）。
- API 路径：`Mmad` 输出到 L0C、`DataCopy(UB, L0C, ...)` 读出（或等价的 fixpipe 读出）、随后的 UB 侧向量处理与 MTE3 落地。
- 验证过的平台与 CANN 版本：Ascend310P3（DAV_2002 / m200）+ CANN 9.1.0。
- 适用粒度：`operator_family` —— 任何手写 L0C 读出的 Cube 算子。
- 路线优先级：`recommended_fastpath`（按块解码只是一次重排；不做就是持续误判）。
- 明确不适用 / 未验证场景：不适用于使用高阶 Matmul API 自行完成读出/重排的实现（布局由 API 负责）；`BLOCK_MODE_MATRIX` 的其它模式未系统核对。

## 根因

fixpipe 把 L0C 搬到 UB 时，输出是**按 16×16 分形块排列**的：整块数据在大块序上是"列块优先、行块次之"，块内才是行主序。

在本轨迹的 64×64 f32 输出上，实测解码式是（`mi` 行块号、`nj` 列块号，均 0..3）：

```python
off = nj * 1024 + mi * 256
out[mi*16:(mi+1)*16, nj*16:(nj+1)*16] = t[off:off+256].reshape(16, 16)
```

等价的 PyTorch 一行写法：

```python
out = t.view(4, 4, 16, 16).permute(1, 2, 0, 3).reshape(64, 64)
```

`nj` 的跨距 1024 元素 = 4 个 16×16 f32 块（每块 256 元素 = 1KB），`mi` 的跨距 256 元素 = 1 块。

拿行主序去解释这种排列，等价于对输出做了一个"块级转置 + 块内保持"的置换；由于数值本身量级正常、非零、非 NaN，最终表现为一个"确定性的大误差"，而不是崩溃。

## 判别方法

1. **先算量级**：误差在 0.1~1 级、而参考与金标之间只有 1e-4 级 ⇒ 是内容错位，不是精度退化。
2. **做两路解码的差分**：同一块读出数据，一路按行主序、一路按 16×16 块解码，分别与高精度模拟比对。若按块解码后落到模拟噪声内，结论就定了。
3. **验存储链是否无辜**：把 GM 输出区与"按行主序解释的读出块"逐位比对。**逐位一致**说明存储搬的是原样，错在解释方式而不是搬运。
4. 用 `e2e == 直 reshape` 与 `按块解码 == 模拟` 两个等式同时成立来定型：这是布局问题的充分证据。

## 完整代码

**按块解码的验证脚本（实测用）**

```python
import numpy as np
raw = np.fromfile("<diag-dir>/probe_out32.bin", dtype=np.float32)
b = 4096
tD = raw[b + 8192: b + 12288]          # 尾声读出块（16KB = 4096 f32）

def dec(t):
    out = np.zeros((64, 64), dtype=np.float32)
    for mi in range(4):
        for nj in range(4):
            off = nj * 1024 + mi * 256
            out[mi*16:(mi+1)*16, nj*16:(nj+1)*16] = t[off:off+256].reshape(16, 16)
    return out

print("O(tD) 按块解码 vs 模拟 :", np.abs(dec(tD) - O_sim).max())
print("O(tD) 直 reshape vs 模拟:", np.abs(tD.reshape(64, 64) - O_sim).max())

# 存储链是否健康: GM 输出区 == 读出块直 reshape（逐位）?
out_area = raw[0:4096].reshape(64, 64)
print("输出区 == tD 直 reshape 逐位一致:", np.array_equal(out_area, tD.reshape(64, 64)))
```

实测输出（同一份探针文件）：

```
O(tD) 按块解码 vs 模拟 :  3.11e-05      <-- 模拟噪声内
O(tD) 直 reshape vs 模拟: 0.201265      <-- 假误差
输出区 == tD 直 reshape 逐位一致: True  <-- 存储链健康
```

**PyTorch 侧一行重排**（若选择在 host 侧解码，而非在 kernel 内重排）

```python
out = t.view(4, 4, 16, 16).permute(1, 2, 0, 3).reshape(64, 64)
```

## 设计决策

- **优先在 kernel 内用"2D 散射直存"绕开重排**：最终路线不是"存完再解码"，而是让 MTE3 直接按目标行主序写出，从根上不需要重排。
- **不采用 UB→UB 散射重排**：该形态在本轨迹里反复出现部分块丢失，不可靠。
- **探针一律按块解码后再比对**：否则每一个后续实验都会被同一个假误差污染（本轨迹确实被污染了多轮）。

## 系统信息

- 目标平台 Ascend310P3（DAV_2002 / m200），CANN 9.1.0；读出面为 64×64 f32（16KB）。
- 文件：`kernel/<generic>.cpp`（尾声读出与落地）、调试脚本（探针解码与比对）。

## 预防

- 迁移检查表新增：**任何来自 L0C 的读出，先确认布局再比对**；不要假设行主序。
- 探针/调试脚本里把"解码函数"做成唯一入口，禁止各处自行 `reshape`。
- 误差量级出现"0.1~1 且确定性"时，先怀疑布局，再怀疑计算。

## 验证信号

- 同一份探针数据：按块解码与高精度模拟的误差 `3.11e-05`，而直 reshape 的误差 `0.201265` —— 相差四个数量级（来源平台：310P；证据等级：tool_observed）。
- 存储链清白：GM 输出区与读出块直 reshape **逐位一致**（`array_equal` 为真）（来源平台：310P；证据等级：tool_observed）。
- 分数链同样按该解码式核对后落到噪声内（早期几次探针里 S 与 W 的读数在解码前后出现"全对/全错"的翻转，均由解码方式决定）（来源平台：310P；证据等级：tool_observed）。

## 失效边界

- **解码式只在本轨迹的 64×64 f32 tile 上逐位验证过**；其它 tile 尺寸（尤其是 16 的整数倍但块数不同）需要重新推导 `nj`/`mi` 跨距（本卡给出的跨距是对 64 宽的实测值，不是通用公式）。
- **未决项（优先）**：同一 kernel 里两条 Mmad 链（分数链与输出链）的读出布局曾被认为不同（一条分形、一条行主序），后续证据表明**两条都是分形布局**，此前的"行主序"判断是探针 dump 位置互相覆盖造成的解析错位。这个"dump 位置覆盖"的具体机制（哪个探针写到哪个偏移）没有系统梳理。下一个 agent 若要复用读出逻辑，需先固定"一块缓冲只给一个探针用"。
- 未验证平台：其它代际未验证，未验证其 fixpipe 读出布局是否同构。
- 不覆盖 `BLOCK_MODE_MATRIX` 下其它模式的单位/布局差异。

## 坏实践

- **把 L0C 读出直接 `reshape` 当行主序**：本卡最核心要禁的一条。
- **多路探针共用同一块 GM 偏移**：后写的探针覆盖前一个，导致"同一段代码在不同轮次得到不同结论"。
- **用直 reshape 的误差去判断"哪个修法有效"**：所有 A/B 实验都会被同一个假误差淹没。

## 误诊

- 误诊（agent_reported）：曾据"输出区与读出块逐位一致"判定存储链健康、但把读出块当行主序解释，于是把 0.2 级误差归给计算段，反复改向量指令；也曾在另一轮把同一误差归给"存储实现丢块"。
- 误诊（agent_reported）：一度得出"输出链读出是行主序、分数链读出是分形"的结论（两条链布局不同），后经同一解码式同时验证两条链而推翻；根因是探针 dump 位置互相覆盖。
