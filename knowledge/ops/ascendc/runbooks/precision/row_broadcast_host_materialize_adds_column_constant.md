---
type: Runbook
title: 行广播别用逐行 Adds 或 srcStride=0
description: 逐行 Adds 只产出列同值矩阵；DataCopy 的 srcStride=0 语义是块间无间隔（源连续推进，与文档一致），向量 srcRepStride=0 按文档复读首个连续 8 DataBlock、但既有内核注释称顺序推进且未上板复核——两种 stride=0 都不能当广播原语；本轨迹形态下行同值矩阵用 host 物化。
tags: [task.debugging, topic.precision, topic.data_movement.data_copy, topic.implementation.masking]
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/8746f7ced6cef47e3fd7abd64c0eb827e28e2b56/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/basic_arithmetic/Adds.md
    role: primary
  - resource: https://gitcode.com/cann/asc-devkit/blob/8746f7ced6cef47e3fd7abd64c0eb827e28e2b56/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/data_move/DataCopy_GMAndUB_highdim_split.md
    role: constraint
  - resource: https://gitcode.com/cann/asc-devkit/blob/8746f7ced6cef47e3fd7abd64c0eb827e28e2b56/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/SIMD_compute/high_dim_split.md
    role: constraint
created_at: "2026-10-28T09:51:47Z"
updated_at: "2026-11-02T07:57:34Z"
platforms: ["310p"]
---

# 行广播别用逐行 Adds 或 srcStride=0

## 现象

在 310P（Ascend310P3，DAV_2002 / dav-m200）上用 raw-launch 裸 Mmad 写一个多段 GEMM 的注意力反向 kernel（选块稀疏注意力反向，A 域产出 dq、B 域产出 dk/dv），为了省掉 host 侧物化的 64×64 f32 行广播参数矩阵，把 A 域的 lse 与 δ 改成 kernel 内向量装载 + 逐行 `Adds`：

```cpp
// kernel/attn_bwd.cpp —— 被否决的写法（A 域单元头）
DataCopy(lseL, gLse[static_cast<int64_t>(u) * C64], C64);
DataCopy(dltL, gDlt[static_cast<int64_t>(u) * C64], C64);
// …随后每个 A 单元做 64 次 Adds
for (int32_t r = 0; r < C64; ++r) {
    Adds(lseMat[r * C64], lseL, 0.0f, C64);
    Adds(dltMat[r * C64], dltL, 0.0f, C64);
}
```

精度门禁立刻变成 0/3，且错误只落在 dq：

```
case   0 … dq: 3.507e+01/3.693e-04 dk: 8.197e-04/8.196e-04 dv: 2.874e-03/2.876e-03 FAIL
case  19 … dq: 5.564e+01/4.076e-04 dk: 8.415e-04/8.414e-04 dv: 2.169e-03/2.165e-03 FAIL
case  48 … dq: 1.0322e+02/5.917e-04 dk: 1.360e-03/1.360e-03 dv: 2.344e-03/2.344e-03 FAIL
==== 0/3 PASS ====
```

注意 dk/dv 的误差与参照实现逐位相同（8.197e-04 vs 8.196e-04、2.874e-03 vs 2.876e-03），即 B 域完全没被改动——这是"只有某个域的广播姿态错了"的典型指纹，而不是算错。

第二条看似等价的省 host 路线（GM 侧"广播读"，`srcStride=0`）更糟：

```cpp
// 被否决的写法二：同一 256B 源块重复读 64 次
DataCopy(lseMat, gLse[static_cast<int64_t>(u) * C64],
         DataCopyParams(C64, 8, 0, 0));
DataCopy(dltMat, gDlt[static_cast<int64_t>(u) * C64],
         DataCopyParams(C64, 8, 0, 0));
```

→ `dq: 8.130e+04/3.693e-04`，dk/dv 仍逐位正确。

**另一条独立轨迹（310P，CANN 9.1.0）**进一步实测：向量 repeat 形的 `BinaryRepeatParams` / `UnaryRepeatParams` 用 `srcRepStride=0` 造广播，同样**编译通过、运行不报错、数值全错**（dk/dv 误差跳到 1e5~1e6 量级）。该轨迹用三步单变量二分定位：只回退广播 `Sub` 后 dq/dk/dv 全部 PASS，而保留广播 `Sub` 时误差逐位相同——坏的是广播原语，不是全矩阵 `Compare/Select`。注意 `srcRepStride=0` 的机制表述存在未决冲突：固定版本官方文档（`SIMD_compute/high_dim_split.md`）写明 repeatStride=0 时"对首个连续的 8 个 DataBlock 反复读取和计算"，而既有内核实证注释（op46）称其"顺序推进源"；后者未在本轨迹上板单独复核，本卡不裁决哪种机制成立，只主张实测结论——**无论哪种语义，`srcRepStride=0` 都不能当"逐 repeat 推进的广播原语"用**。它与 `DataCopy` 的 `srcStride=0`（块间无间隔、源连续推进，实测与文档一致）是两种不同语义，不能合并成一条"stride=0 行为律"。

## 适用场景

- **工程形态**：kernel 直调（torch 扩展 raw-launch：AscendC kernel + host 侧 torch 物化 + `TORCH_LIBRARY` 注册），非 aclnn / 非 spec 生成。
- **API 路径**：AscendC `DataCopy`（UB→UB 与 GM→UB，`DataCopyParams`/`DataCopyExtParams`）、`Adds`（UnaryRepeatParams/BinaryRepeatParams）、`LocalTensor`/`GlobalTensor`；host 侧 `torch::Tensor::expand().contiguous()`。
- **验证过的平台与 CANN 版本**：Ascend310P3（DAV_2002 / dav-m200）+ CANN 9.1.0，device 4（单卡独占，msprof/dev 锁串行）。
- **适用粒度**：`same_operator` —— 同一 kernel 内 A 域（行 = query、列 = key）与 B 域（tile = 键×查询、列 = query）两种朝向都实测过；同族"多段 GEMM + 逐行参数矩阵"的 kernel 可迁移。
- **路线优先级**：`recommended_fastpath` —— 本轨迹形态下（逐行 `Adds` 只能产列同值矩阵）需要行同值矩阵时 host 物化后 kernel 直装；需要列同值时逐行 `Adds` 即可。这是 tile 朝向论证 + 实测对照的结论，不是"行广播在任何实现下都必须 host 物化"的普适律。
- **明确不适用 / 未验证**：A2/A3/950 等平台未验证（不得据此外推）；`srcStride=0` 的语义是工具链实现细节，不能当作跨平台的"广播原语"使用；本卡不覆盖 16×16 分形布局下的转置类广播。

## 判别方法（根因）

1. **先确认是系统性布局错误还是竞态**：同一输入连跑三次输出逐位相同、错误只集中在单输出、全 head 全行命中 → 系统性（详见同族卡"单输出巨误差定位"）。
2. **算清该域 tile 的朝向**：A 域 tile 行 = query、列 = key，需要的矩阵是 `lseMat[r][c] = lse[r]`（行同值）；B 域 tile 行 = key、列 = query，需要的是 `lseMat[r][c] = lse[c]`（列同值）。
3. **认清 `Adds` 的行切片语义**：`Adds(dst[r*C64], src64, 0.0f, C64)` 是把整条 64 元素向量写进 dst 的第 r 行，因此得到 `lseMat[r][c] = lse[c]` —— 这是**列同值**。它无论怎么摆放都不可能产出**行同值**。
4. **分清两类 stride=0 的语义，不要合并**：`DataCopy` 的 `srcStride=0`（srcGap）= 相邻块之间无额外间隔、源连续推进——本会话实测 GM→UB `DataCopyParams(C64, 8, 0, 0)` 与 UB→UB `srcStride=0` 两条均如此，与固定版本文档一致；向量 repeat 形的 `srcRepStride=0` 按官方文档是"复读首个连续 8 个 DataBlock"，但既有内核注释称"顺序推进源"且未上板复核（机制未决，见"现象"补充段）。无论未决项倒向哪边，实测用它造广播都是 1e5 级错值——判别与修复都不依赖对该机制的裁决。
5. **做最小判别实验**：把行广播换成 host 物化后重跑同一用例——dq 从 3.507e+01 变回 3.693e-04/3.693e-04（与参照实现逐位相同），即根因确认。另外把 Adds 循环挪到三个不同位置（单元头 / loadA 之后 / 每 visit 重建），误差恒为 3.507e+01，证明与放置和 WAR 顺序无关。

### 310P/CANN 9.1.0 补充（另一条独立轨迹）

- 三步单变量二分：bisect-A（只留全矩阵掩码、lse/dlt 回落逐行 Adds）误差与两处都开时逐位相同；bisect-B（matE 改用逐行 Adds、保留全矩阵 Compare/Select）仍错；bisect-C（**只去掉广播 `Sub`**）三个输出全部 PASS。判决点在 bisect-C。
- `BinaryRepeatParams`/`UnaryRepeatParams` 的 `srcRepStride=0` 形需先解决编译问题（`Sub`/`Adds` 无 mask 重载、字面量 `0` 与指针形参重载歧义需 `(uint64_t)0`），修到能编译后 dk/dv 仍为 1e5 档错误。
- 条件分支：逐行 `Adds` 产出的是**列同值**矩阵，只有当所需广播维恰为列（B 域，列 = query）时才正确；A 域需要行同值，在本轨迹的实现形态下用 host 物化。另一条独立轨迹在 B 域使用逐行 `Adds` 正常工作，与本卡结论一致。

## 解决配方（before / after）

**before（错误：kernel 内逐行 Adds 造行广播）**

```cpp
// kernel/attn_bwd.cpp —— A 域单元头：装载 64 元素向量
DataCopy(lseL, gLse[static_cast<int64_t>(u) * C64], C64);
DataCopy(dltL, gDlt[static_cast<int64_t>(u) * C64], C64);
// …然后（每单元一次）
for (int32_t r = 0; r < C64; ++r) {
    Adds(lseMat[r * C64], lseL, 0.0f, C64);     // 实际得到列同值
    Adds(dltMat[r * C64], dltL, 0.0f, C64);
}
```

**after（正确：host 物化行广播矩阵，kernel 直装）**

```cpp
// host/attn_bwd_host.cpp
// [实证律·广播形态] A 域 lse/δ 必须是"行同值"矩阵 lseMat[r][c]=lse[r]
// (r=query 行)。kernel 侧两条省物化路线实测均不可行:
//   · 逐行 Adds 行切片 ← 64 元素向量 → 得"列同值"(每行是整条向量), 是 B 域
//     形态, A 域用 dq 误差 35.07(确定性)
//   · GM→UB DataCopy srcStride=0 伪广播 → 源顺序推进不复读, dq 8.13e4
// → 行广播由 host 物化(expand+contiguous, 单核); 列广播(B 域)kernel Adds 即可
auto lse2 = lseT.view({unitsA, 64, 1}).expand({unitsA, 64, 64}).contiguous();
auto dlt2 = dltT.view({unitsA, 64, 1}).expand({unitsA, 64, 64}).contiguous();
```

```cpp
// kernel/attn_bwd.cpp —— A 域单元头：直装 host 物化矩阵，不做任何 Adds
// [实证律·广播形态] A 域要的是"行同值"矩阵: lseMat[r][c] = lse[r]
// (r=query 行, c=key 列)。两条看似等价的省 host 路线实测都不成立:
//  · 逐行 Adds(Adds(lseMat[r*64], lseL, 0, 64)) 产出的是"列同值"
//    —— 每行都是整条 64 向量(即 lseMat[r][c]=lse[c]), 那是 B 域
//    形态(B 域 tile 是键×查询, 列=查询, 正确); A 域用它 dq 误差
//    35.07(确定性, 与放置位置无关: unit 头/loadA 后/每 visit 实测同值)
//  · GM→UB DataCopy srcStride=0 伪广播: 实测源顺序推进不复读
//    (dq 8.13e4), 与 UB→UB srcStride=0 同律
// → 行广播矩阵只能 host 物化(lse2/dlt2), kernel 直装。列广播(B 域)
//   仍可用 Adds, host 侧零物化。
DataCopy(lseMat, gLse2[static_cast<int64_t>(u) * M64 * C64],
         M64 * C64);
DataCopy(dltMat, gDlt2[static_cast<int64_t>(u) * M64 * C64],
         M64 * C64);
```

B 域（列参数）保持不动，仍是逐行 `Adds`（那里是对的）：

```cpp
// kernel/attn_bwd.cpp —— B 域 visit：lse/δ（列参数）→ 列同值矩阵
DataCopy(lseL, gLse[uA * C64], C64);
DataCopy(dltL, gDlt[uA * C64], C64);
for (int32_t r = 0; r < C64; ++r) {
    Adds(lseMat[r * C64], lseL, 0.0f, C64);
    Adds(dltMat[r * C64], dltL, 0.0f, C64);
}
```

另一条独立轨迹（310P，CANN 9.1.0）给出的**列广播** kernel 内配方（不属于行广播场景，仅作为列方向的可用路线记录）：`Brcb` 先做行内 16 份复制 → 4 次 16×16 `Transpose` 排段 → 4 次 strided `DataCopy` 抠列 → 3 次行块拷贝拼成 `[64,64]`。其 `srcStride=3` 是"列选择"而非广播，与"读同一块 64 次"是两种语义。

## 设计决策

- **为什么接受 host 物化的成本**：被否决的两条 kernel 路线省掉的是每单元 2 张 64×64 f32 矩阵的 GM 写+读，但都改变语义；行广播在该工具链上没有可靠的 kernel 内原语，因此正确性优先。
- **为什么不是"再换个位置试试"**：三处放置实测同值，说明不是同步/WAR 问题，继续调顺序属于无效搜索。
- **为什么不用 `Brcb`/索引搬运做行广播**：会话内未验证行方向的 Brcb 配方，留作未决项（见失效边界），不作为推荐路线；另一条独立轨迹只在列方向验证了 Brcb 配方。
- **路线分级**：本配方是 `recommended_fastpath`（正确且已验证）；两条 kernel 内行广播路线（逐行 Adds 造行同值、`srcStride=0` 伪广播）是 `banned`（见坏实践）。

## 系统信息

- 工具链：CANN 9.1.0（`/usr/local/Ascend/ascend-toolkit/set_env.sh`），torch + `torch_npu`，Python `/usr/local/python3.11.10/bin/python3`，单 device 4。
- 工程布局（工作副本）：`/home/<user>/<workdir>/{kernel/attn_bwd.cpp, host/attn_bwd_host.cpp, tests/test_attn_bwd.py, perf/}`。
- 构建：`cd /home/<user>/<workdir> && bash build.sh` → 末行 `BUILD_OK: build/lib<generic>_ops.so`。
- 精度命令：`ASCEND_RT_VISIBLE_DEVICES=4 /usr/local/python3.11.10/bin/python3 tests/test_attn_bwd.py --cases 0,19,48`（全量时去掉 `--cases`）。
- kernel 常量：`M64=64`（tile 行）、`C64=64`（tile 列）；A 单元 = (b, kh, t)，B 单元 = (b, kh, kt)。

## 完整代码

见 `## 解决配方` 的 before/after（host 物化 + kernel 直装）与 B 域对照代码。

## 性能影响

- **相对代价（成对，来源平台 310P）**：相对被否决的"kernel 内逐行 Adds"路线，host 物化路线每调用额外做 2×(A 单元数) 张 64×64 f32 的 GM 写 + kernel 侧同尺寸 GM→UB 直装（参照路线：kernel 内 `Adds` 逐行写；本卡不给绝对时延）。这两条参照路线本身是错的，代价比较只用于说明"正确性修复不是免费的"。
- 该修复与同会话的批装载/掩码链优化一起构成整轮改动，整轮相对同一官方口径的参照实现比值由略低于 1 提升到略高于 1（参照路线：官方 harness 的参照实现，同一 `Task_Duration` 口径，平台 310P）——本条修复对性能是负贡献，对正确性是必要条件。

## 预防

- 写广播前先画出 (行, 列) 语义表：哪一维是 query、哪一维是 key，参数沿哪一维变化。
- 任何"逐行 `Adds` 造行广播"的代码都当作 bug 审查；`Adds` 只能造列同值。
- 任何 `srcStride=0` / `srcRepStride=0` 都当作"顺序推进"处理，不当广播用。
- 改广播路径后必须同时跑 A/B 两个输出域：本次 dk/dv 逐位不变、只有 dq 崩，正是"只有 A 域广播错"的判别信号。
- 精度回归若只错一个输出，先查该输出域的 tile 朝向与参数矩阵布局，别先怀疑同步。

## 验证信号

来源说明：以下信号取自本算子在 310P 上的精度回归实测——全量精度门禁脚本的输出、单例探针输出与诊断分支（`ATTN_BWD_STAGE`）对照；均为本轨迹内的工具输出，无外部转述。

- 修前：dq 单输出 3.507e+01 / 5.564e+01 / 1.0322e+02，同时 dk 与 dv 的误差与参照实现逐位相同（`8.197e-04 vs 8.196e-04`、`2.874e-03 vs 2.876e-03`），门禁 0/3（来源平台：310P；证据等级：tool_observed）。
- Adds 行广播放在三处不同位置（单元头 / loadA 之后 / 每 visit 重建）实测误差恒为 3.507e+01，与放置无关（来源平台：310P；证据等级：tool_observed）。
- GM→UB `DataCopyParams(C64, 8, 0, 0)` 伪广播变体：dq 8.130e+04，dk/dv 仍逐位正确（来源平台：310P；证据等级：tool_observed）。
- 改回 host 物化后：dq 3.693e-04/3.693e-04，与参照实现逐位相同，单例 PASS（来源平台：310P；证据等级：tool_observed）。
- 全量 50/50 PASS：最大 `|ours-gold|` dq 9.533e-04、dk 4.410e-03、dv 8.152e-03；最差 `ours/ref` 误差比 dq 1.0000、dk 1.0007、dv 1.0047；最差门限占用 0.5023（来源平台：310P；证据等级：tool_observed）。
- 重新构建后 8 例复验 8/8 PASS（来源平台：310P；证据等级：tool_observed）。
- 另一条独立轨迹（310P，CANN 9.1.0）：`srcStride=0` 的 `DataCopy` 后 dq 精确、dk/dv 误差跳到 1e5~1e6 量级；`BinaryRepeatParams`/`UnaryRepeatParams` 的 `srcRepStride=0` 修到编译通过后 dk/dv 仍为 1e5 档；bisect-C（去掉广播 `Sub`）后 dq/dk/dv 全 PASS（来源平台：310P；证据等级：tool_observed）。

## 失效边界

- 只在 Ascend310P3（DAV_2002 / dav-m200, CANN 9.1.0）实测；A2/A3/950 未验证，推断可迁移但不得据此写入平台范围。
- 依赖 tile 常量 64×64：`M64/C64` 变化时行广播矩阵尺寸与 `DataCopy` 参数都要重算。
- 未决项：同骨架内单独把 B 操作数装载回退为"逐操作数"（stage-4 对照）会同时打崩 dk/dv（dk 1.024e+02、dv 2.572e+02，dq 也错到 8.986e+00），根因未定位——说明批装载与其它改动存在未建模的耦合，回退时不要以为只影响性能。
- 未决项：kernel 内用 `Brcb`/索引搬运直接构造**行同值**矩阵未验证。
- 未决项：`srcRepStride=0` 的机制——固定版本文档称"复读首个连续 8 DataBlock"，既有内核注释称"顺序推进源"，两者矛盾且本轨迹未上板单独复核；下个 agent 若要复用"以 srcRepStride=0 做源广播"，必须先做只含该原语的对照实验再下结论。
- 另一条独立轨迹（310P，CANN 9.1.0）的补充边界：其结论是"在这条链路上 `srcStride=0`/`srcRepStride=0` 形不可用"，不等于"stride=0 在所有上下文都错"；未做最小复现，机制细节未定；`Brcb` 列广播配方要求目标 `[64,64]` 连续且 16 对齐，行数非 64 需重推。

## 坏实践

- **把逐行 `Adds` 当行广播**：得到的是列同值矩阵，只对"列 = query"的 B 域成立；在 A 域会造成 dq 确定性大错而 dk/dv 全对，极易被误判为"只差一点精度"。
- **用 `srcStride=0` 当广播原语**：GM→UB 与 UB→UB 都顺序推进源，结果是读错数据（dq 8.130e+04），不是重复读。
- **靠"编译通过 + 不报错"判断广播原语可用**：本例的 `srcStride=0` 与 repeat 形 stride=0 都是静默错数据。
- **看到单输出错就先去调同步/加屏障**：本例三处放置同值，同步假设直接排除。
- **放宽容差或只跑单用例就宣布修好**：本例必须全量 50 例 + 重新构建后复验。
- **同时改两处（广播 + 掩码）再看结果**：误差指纹会互相掩盖，二分必须单变量。

## 误诊

- 曾怀疑 host 掩码链的 `unsqueeze(3) & causalValid.view(...)` 顺序、`lseT` 的 permute 索引布局、跨单元 V_MTE2 WAR、删掉的 `V_MTE3` 事件对——逐项排除后确认与它们无关（这些假设为会话内推理，未逐一做隔离实验，标注 agent_reported）。
- 另一条独立轨迹曾以为 `gk` 广播错是"前缀和算错"，实际是广播矩阵本身错位，前缀和的错误只是下游表现（agent_reported）。
