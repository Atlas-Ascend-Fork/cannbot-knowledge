---
type: Optimization
title: 索引驱动散读的循环不变量地址计算外提
description: 将addr(idx)拆为base+idx×stride，把不依赖idx的base和stride移到循环外只计算一次
tags:
- task.optimization
- topic.attention
- topic.tiling
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/FA-A5/01-loop-invariant-address-hoisting.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

# 性能优化策略：索引驱动散读的循环不变量地址计算外提

> **单一优化点：** 当一个按运行时索引逐行搬运的循环（gather/scatter）在**最内层**通过一个通用地址函数（形如 `GetXxxOffset(tiling, b, n, idx)`）计算每行的源/目的地址，而该函数内部**大部分项与索引无关**（layout 分支、batch/head 基址、行 stride 均由循环外的量决定）时，把不变部分**提到循环外**预计算成 `base` 与 `stride` 两个标量，内层只保留 `addr = base + idx * stride` 一次乘加。
>
> **为什么这在搬运循环里值钱（而不只是"编译器会做的常规外提"）：** 这类循环的内层是 `标量装载 → 地址计算 → 搬运指令发射` 的**串行链**，标量单元与搬运单元在同一发射窗口内竞争。地址函数通常从 `tilingData` 结构体**逐字段读**（编译器无法证明其不被别名改写，难以自动外提），且含 `if (layout == ...)` 分支——分支与多次 64 位乘法直接压在关键路径上。
>
> **已验证锚点：** A5(Ascend950DT) SparseFlashAttention，`Gather` 内层由 `GetKRowOffset(tilingData_, b, n2, idx)`（读 4 个 tiling 字段 + layout 分支 + 3 次 64 位乘法）改为外提后的 `kRowBase + idx * kRowStride`。两个大 prefill 刻度：`s256 1735.4→1715.7µs (−1.14%)`、`s1024 15510.0→15315.4µs (−1.26%)`，精度 37/37 不变。
>
> **收益量级预期（重要）：** 本策略只削减**标量算术量**，不改变标量装载次数、不改变搬运指令数。实测量级为 **−1%~−2%**。若期望更大收益，说明瓶颈不在算术而在依赖链（用策略 02）或在搬运本身。

本策略只做"循环不变量外提"。不改变搬运指令数、不改变数据值/布局、不引入批量或展开（属策略 02）、不改 tiling。

---

## 1. 优化原理

### 1.1 性能问题模式（通用）

索引驱动的搬运循环常写成：

```cpp
for (i = 0; i < rows; ++i) {
    int32_t idx = idxUb.GetValue(i);                       // 标量装载
    uint64_t off = GetRowOffset(tiling, b, n, (uint32_t)idx);  // ← 通用地址函数
    DataCopy(dstUb[i * dstStride], srcGm[off], len);       // 搬运发射
}
```

而 `GetRowOffset` 的典型实现：

```cpp
__aicore__ inline uint64_t GetRowOffset(const T *t, uint32_t b, uint32_t n, uint32_t idx)
{
    uint32_t nVal = t->n;      // ← 结构体字段读
    uint32_t sVal = t->s;      // ← 结构体字段读
    uint32_t d    = t->d;      // ← 结构体字段读
    if (t->layout == LAYOUT_A) {                       // ← 分支
        return (uint64_t)b*sVal*nVal*d + (uint64_t)idx*nVal*d + (uint64_t)n*d;
    }
    return (uint64_t)b*nVal*sVal*d + (uint64_t)n*sVal*d + (uint64_t)idx*d;
}
```

对**每一行**都要：读 3~4 个结构体字段、走一次 layout 分支、做 3 次 64 位乘加。而其中**只有 `idx` 是循环变量**——其余全是循环不变量。

三个"编译器通常不替你外提"的原因：

| 原因 | 说明 |
|---|---|
| 指针别名 | `tilingData_` 是 `const T*`（有时甚至非 `__restrict`），编译器无法证明循环体内的 `DataCopy` 不会改写它，保守起见每轮重读 |
| 跨函数 | 地址函数常在另一个头文件、以模板 inline 形式提供，内联后仍可能保留字段读 |
| 分支 | `layout` 分支在循环内，阻碍进一步的强度削减 |

### 1.2 本策略利用的机制

把地址表达式按"是否依赖 idx"做**代数拆分**：

```
addr(idx) = base + idx * stride
```

其中 `base` 与 `stride` 只依赖循环外的量（layout、b、n、各维长度），可在循环外算一次。

```text
# 基线
for i: idx=load(i); off = f(tiling,b,n,idx);   # 字段读×4 + 分支 + 乘×3
       DataCopy(dst, src[off], len)

# 改写
{ base, stride } = split_f(tiling, b, n)       # 循环外算一次（含分支）
for i: idx=load(i); off = base + idx*stride;   # 乘×1 + 加×1
       DataCopy(dst, src[off], len)
```

**等价性是逐位的**：只要拆分在同一整数域（如全程 `uint64`）内展开，与原式项项对应，无溢出差异。

---

## 2. 适用条件与泛化边界

必须**同时**满足：

| 条件 | 要求 |
|---|---|
| 循环形态 | 内层按运行时索引计算地址并发搬运指令（gather/scatter/散读散写） |
| 可拆分性 | 地址表达式对索引是**仿射**的：`addr = base + idx*stride`（一次项） |
| 不变性 | `base`/`stride` 只依赖循环外量（layout、batch/head 索引、各维长度） |
| 循环长度 | 内层迭代数足够大（实例 128~512 行/批），否则外提开销占比过高 |
| 瓶颈定位 | profiling 显示该循环所在核的 `scalar` 管线占比高 |
| 基线稳定 | 修改前 build/精度/性能可重复 |

优先适用：

- `aiv_scalar_ratio` / `aic_scalar_ratio` 明显高于 `vec_ratio`，且热点循环含逐行地址函数调用。
- 地址函数从 `TilingData` 逐字段读、含 layout/format 分支。
- 单行搬运字节小（如 256B），行开销由发射侧而非带宽决定。

不适用或收益极小：

- 地址对索引**非仿射**（如 PagedAttention 的两级索引 `blockTable[idx>>k]*B + (idx&(B-1))*s`）——需先做**两级拆分**（外层块表查表仍在内层，只能外提其中的常量部分），收益结构不同。
- 内层迭代数很小（<16）——外提的固定开销占比过高。
- 该循环不是热点（scalar 占比低）。
- 期望 >5% 的收益——本策略量级是 1%~2%，见 §7 AP-005。

---

## 3. 实施步骤

### 3.1 定位并展开地址函数

1. 找到内层的地址计算调用点。
2. 把被调函数**手工展开**在纸上，逐项标注每一项依赖哪些变量。
3. 分成两组：依赖 `idx` 的（保留在内层）、不依赖 `idx` 的（外提）。

### 3.2 代数拆分

以 BSND / BNSD 两种 layout 为例：

```text
BSND: addr = b*S*N*D + idx*N*D + n*D
      → base   = b*S*N*D + n*D
        stride = N*D

BNSD: addr = b*N*S*D + n*S*D + idx*D
      → base   = b*N*S*D + n*S*D
        stride = D
```

### 3.3 外提落地

```cpp
// —— 循环外：算一次（分支也在这里，内层无分支）——
uint64_t rowBase, rowStride;
{
    const uint32_t nVal = tiling->n;
    const uint32_t sVal = tiling->s;
    const uint32_t dVal = tiling->d;
    if (tiling->layout == LAYOUT_A) {          // [B,S,N,D]
        rowBase   = (uint64_t)b * sVal * nVal * dVal + (uint64_t)n * dVal;
        rowStride = (uint64_t)nVal * dVal;
    } else {                                    // [B,N,S,D]
        rowBase   = (uint64_t)b * nVal * sVal * dVal + (uint64_t)n * sVal * dVal;
        rowStride = (uint64_t)dVal;
    }
}

// —— 内层：只剩一次乘加 ——
for (uint32_t i = 0; i < rows; ++i) {
    int32_t idx = idxUb.GetValue(i);
    DataCopy(dstUb[(uint64_t)i * dstRowStride],
             srcGm[rowBase + (uint64_t)(uint32_t)idx * rowStride], len);
}
```

### 3.4 保留原函数

- **不要删除**原地址函数：它仍被非热点路径（如 causal mask 读索引、边界处理）使用。
- 在外提处加注释，标明"与 `GetXxxOffset` 逐项等价"，便于后续同步修改。

---

## 4. 正确性红线

### 4.1 整数域一致

- 拆分前后必须在**同一整数域**内展开。原式若在 `uint64` 域内做全部乘加，拆分式也必须逐项 `(uint64_t)` 提升。
- 特别注意 `idx` 是 `int32_t`：转换须与原式一致（原式若写 `(uint64_t)static_cast<uint32_t>(idx)`，拆分式照抄，**不要**简化为 `(uint64_t)idx`——负索引语义会不同）。

### 4.2 分支必须一起外提

- layout 分支要整体搬到循环外；**不能**只外提部分项而把分支留在内层（那样既没省分支，又增加了寄存器压力）。

### 4.3 不变性证明

- 逐一确认 `base`/`stride` 依赖的每个量在内层循环中**不被修改**。
- 若循环体内可能改写 `tilingData` 指向的内存（几乎不会，但需确认），则外提不合法。

### 4.4 与其它调用点保持同步

- 若原地址函数在别处也被调用，本次外提**不改变**其语义；后续若修改该函数（如新增 layout），**必须同步修改外提处**——这是本策略引入的唯一维护成本。

---

## 5. 已知陷阱

### AP-001：类型转换不一致导致越界

问题：原式 `(uint64_t)static_cast<uint32_t>(idx) * stride`，外提时简写成 `idx * stride`（`int32` 乘法）。
症状：大 shape 下地址溢出/为负，读到非法地址或错值。
修复：逐字符照抄原式的类型转换链。

### AP-002：只外提乘法、分支留在内层

问题：把 `base` 算出来了，但 `if (layout==...)` 还在内层。
症状：收益几乎为 0（分支预测失败与字段读仍在）。
修复：§4.2，分支整体外提。

### AP-003：误以为编译器已经做了

问题：认为"这是常规循环不变量外提，编译器会自动做"，跳过本策略。
澄清：因指针别名 + 跨函数 + 分支三重障碍，实测编译器**未做**（外提后仍有 −1.2% 的实测收益）。判据：改完实测，而非假设。

### AP-004：在非热点循环上做

问题：对迭代数很小或非瓶颈的循环外提。
症状：无收益，且代码可读性下降。
修复：先 profiling 确认 scalar 占比与该循环的热度。

### AP-005：期望收益量级错配

问题：期望本策略带来 >5% 收益。
澄清：本策略**只削减标量算术量**，不减少标量装载次数、不减少搬运指令数。实测量级 **1%~2%**。
若瓶颈是"标量装载→发射"的**串行依赖链**，请用策略 02（展开+预取，实测 −20%）；
若瓶颈是搬运指令数本身，本策略无能为力。

### AP-006：把两级索引当仿射式硬拆

问题：PagedAttention 类的 `addr = blockTable[idx>>k]*blockBytes + (idx&mask)*rowBytes` 不是仿射式，强行套用。
症状：拆不出与 idx 无关的 `stride`（查表项本身依赖 idx）。
修复：这类应评估"预先批量换算物理地址存 workspace"的另一类做法；本策略只适用于仿射式。

---

## 6. LLM 实施前必须回答的问题

| 问题 | 必填内容 |
|---|---|
| 热点定位 | 哪个循环；profiling 的 `*_scalar_ratio` 值；该循环的迭代数 |
| 地址函数 | 函数名、完整展开式、每一项依赖的变量清单 |
| 仿射性 | 能否写成 `base + idx*stride`；若不能，为什么 |
| 拆分式 | 每种 layout/format 分支下的 `base`、`stride` 表达式 |
| 类型链 | 原式的类型转换链；拆分式是否逐字符一致 |
| 不变性 | `base`/`stride` 依赖量在内层是否恒定 |
| 其它调用点 | 原函数还被谁调用；本次是否保留 |
| 收益预期 | 是否理解量级为 1%~2%（而非 >5%） |
| 基线 | 修改前 build/精度/性能基线值，及重复次数 |

任一项无法回答，不实施本策略。

---

## 7. 禁止事项与回退条件

禁止：

- 改变类型转换链（AP-001）。
- 只外提算术、把分支留在内层（AP-002）。
- 删除原地址函数（其它调用点仍需）。
- 在非仿射地址上强行拆分（AP-006）。
- 用本策略替代策略 02（两者削减的是不同东西，可叠加）。

回退或缩小策略的条件：

- 精度不一致 → 优先查类型转换链（AP-001）。
- 实测无收益 → 检查分支是否也外提（AP-002）；再检查该循环是否真是热点（AP-004）。
- 地址非仿射 → 放弃本策略。

---

## 8. 验收标准

最小验证：

```bash
bash <build> --soc=<soc> --op=<op> --wheel 2>&1 | grep -cE "error:"   # 须为 0
source <set_env> && pytest <op>/test/test_<op>.py -q                   # 精度须与基线一致
```

精度：**必须逐位一致**（本策略是等价变换，任何精度变化都说明拆分错了）。

性能（profiling 归因）：

- 该核的 `*_scalar_time` 下降；
- 端到端下降 1%~2%（大 shape 更明显，因内层迭代数更多）；
- 搬运指令数、`mte2/mte3` 时间**不应**有明显变化（若变了，说明改动越界了）。

边界：不同 layout 分支各测一次；小 shape（迭代数少）应无明显收益也无劣化。

性能结论须写清：

```text
本策略只削减标量算术量，实测量级 1%~2%。
不减少标量装载次数与搬运指令数——那是策略 02 与搬运类策略的范围。
精度必须逐位一致；有差异即为拆分错误（首查类型转换链）。
```

## 检索卡（短卡）

动作：将addr(idx)拆为base+idx×stride，把不依赖idx的base和stride移到循环外只计算一次
适用：最内层按运行时索引计算地址并发出gather、scatter或散读散写搬运
限制：地址表达式拆分前后必须在同一整数域内展开
范围：索引驱动的散读散写内层循环
检索词：gather、scatter、addr(idx)、base、stride、循环不变量外提
机会：索引驱动搬运在最内层反复调用通用地址函数
