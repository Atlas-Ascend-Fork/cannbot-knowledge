---
type: Runbook
title: "TBuf 切片越界 2KB 污染相邻 S 镜像行块"
description: '多个逻辑张量用切片共用一个大 TBuf 时，容量按元素总数手算写错 4×128 元素，尾切片越界 2KB 写进相邻 TBuf 的首 8 行，表现为该区出现 1.25~1.45 的伪浮点。'
tags: [task.debugging, topic.implementation.memory_management, topic.memory]
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/8746f7ced6cef47e3fd7abd64c0eb827e28e2b56/docs/zh/api/SIMD-API/basic_api/resource_management/TBuf/TBuf_intro.md
    role: constraint
created_at: "2026-10-28T09:51:47Z"
updated_at: "2026-10-28T09:51:47Z"
platforms: ["310p"]
---

# TBuf 切片越界 2KB 污染相邻 S 镜像行块

## 现象

在 310P（dav-m200）上重写一个分块扫描（chunk-scan）kernel 时，向量暂存全部挤在一个 `VECCALC` TBuf 里，用 `Get<float>()` 之后按固定偏移切出多个逻辑张量（`rho`、`gl`、`betaF`、`eV`、`e2V`、`rV`、`zerosF`）。其中"每个 chunk 载入的 beta 块"直接拿了 `zerosF` 的尾切片当落点：

```cpp
    pipe.InitBuffer(msBuf, 13 * 128 * sizeof(float));         // 6.5KB 向量暂存
    ...
    LocalTensor<float> betaBlk = zerosF[T64];                 // [64,16] f32
```

现象是**部分 chunk 的输出在行 0~7 出错**，且每次错的行集合会随改动漂移；把 kernel 内 S 镜像槽（`B_ST`）在 chunk 0 处 dump 出来：

```
B_ST row0[:8]: ['0.0000', '1.2500', '0.0000', '1.3906', '0.0000', '1.4531', '0.0000', '1.3125']
B_ST row32[:8]: ['0.0000', '0.0000', '0.0000', '0.0000', '0.0000', '0.0000', '0.0000', '0.0000']
nonzero rows: [0, 1, 2, 3, 4, 5, 6, 7] count 8
```

即"**该槽首 8 行非零、后 56 行全零**"，非零值只落在**奇数** f16 下标上、量级 1.25~1.45。kernel 结束后在 host 侧回读 GM scratch 确认这是真实写入（不是探针伪影）：每个核的 `B_ST` 区都有 240 个奇数偏移非零元素、最大 1.449。

因为该槽是 `S_T`（递推状态）的 B 源镜像，`v_new = u - w@S` 就带上了这部分垃圾，输出错在对应的 8 行上。

**另一条独立轨迹（310P，CANN 9.1.0）**观察到同类"单 buffer 手算偏移少算容量"的另一种表现：标量区按 `14 * 128` 声明为 7KB，而最后一个 `[64,8]` f32 子视图需要到 8KB，**越界 1KB** 覆盖紧随其后的状态缓冲；该轨迹先尝试扩容到 16×128，症状未消失。症状是"末行前缀和差约 6%"（`gk[63]` 内核值 −159.0 vs 参考 −169.06），前几行完全正确；强门控用例显现，弱门控用例因末行累积值小而被门限淹没。同一处越界同时造成"末行读到邻居数据"与"状态缓冲被写坏"两个看似无关的现象。

## 适用场景

- 工程形态：Kernel 直调（AscendC，`TPosition::VECCALC` TBuf 手工布局）。
- API 路径：`TPipe::InitBuffer` + `TBuf::Get<T>()` 的"多逻辑张量共用一 TBuf + 偏移切片"布局；`DataCopy` 把 GM 块搬进切片。
- 验证过的平台与 CANN 版本：Ascend310P3（DAV_2002 / m200）+ CANN 9.1.0，UB 240KB。
- 适用粒度：`operator_family`（任何手工算 UB 偏移布局的 AscendC kernel 都适用）。
- 路线优先级：`recommended_fastpath`（给"块载入缓冲"单独开 TBuf，不共用）。
- 不适用 / 未验证场景：未在 A2/A3 验证同一 UB 布局约束下的邻居顺序（未验证，推断可迁移）；TBuf 由 `TPipe` 分配，越界写**不会**触发任何硬件报错或断言，只能靠现象定位。

## 根因

`InitBuffer(msBuf, 13 * 128 * sizeof(float))` 只分配了 **13×128 = 1664** 个 f32（6.5KB），而切片布局实际需要：

```
rho   4×128 = 512
gl      128 = 128
betaF    64 =  64
eV      128 = 128
e2V     128 = 128
rV      128 = 128
zerosF   64 =  64
----------------------
小计         = 1152              ← 其余张量恰好在 [0,1152)
betaBlk = zerosF[T64] 起于 1152、长 T64*H = 64×16 = 1024
----------------------
布局总需求   = 2176 个 f32 = 8.5KB
```

1664 < 2176，**短 512 个 f32 = 2048 B**。`betaBlk` 的 MTE2 块载入（`DataCopyParams(T64*H*4/32, 1, 0, 0)` = 128 个 32B 块 = 4096B）只把前 512 个元素落进本 buffer，**尾部 512 个 f32 顺着地址写进下一个分配的 TBuf**（这里是 `sTBuf`，即 `S_T` 的行块镜像）。

字节数对得上现象：2048B ÷ (128 × 2B/行) = **正好 8 行** `[64,128]` f16 tile——与观测到的"首 8 行非零、其余全零"一致。

值的量级也对得上：被写进去的是 f32 小值（beta 量级 0.05 左右，位型 `0x3D4x`~`0x3D9x`）。这段内存的**后一半字节**（f16 下标为奇数的位置）恰好是这些 f32 的**高半字**；小 f32 的高半字 `0x3D4C` 按 f16 解读 = 符号 0、指数域 15（2^0）、尾数 `0x34C/1024≈0.297`，即 **≈1.30**——正是观测到的 1.25~1.45 区间、且只落在奇数下标。

根因一句话：**共用 TBuf 的容量按"以为的元素总数"手写成 13×128，而切片链实际要 2176 个元素，尾切片越界 512 元素写坏了相邻 TBuf。**

原代码的注释本身甚至写着"`+ betaBlk[64,16]=1024 el —— 溢出会踩相邻 sTt2, 勿缩`"，说明作者知道"总需求 2176 el"，却把 `InitBuffer` 的 13×128 当成了 2176——`13×128=1664` 与 `17×128=2176` 混淆，少了 4×128。

## 解决配方

`before`（`kernel/chunk_scan.cpp`）：

```cpp
    pipe.InitBuffer(msBuf, 13 * 128 * sizeof(float));         // 6.5KB 向量暂存
    ...
    LocalTensor<float> betaBlk = zerosF[T64];                 // [64,16] f32
    ...
    // （rho[4,128]+gl[128]+betaF[64]+eV+e2V+rV[128]+zerosF[64] = 1152 el
    //   + betaBlk[64,16]=1024 el —— 溢出会踩相邻 sTt2, 勿缩）
```

`after`（把块载入缓冲拆成独立 TBuf，并把合并 buffer 缩到它真正需要的 1152 元素）：

```cpp
    pipe.InitBuffer(msBuf, 9 * 128 * sizeof(float));          // 4.5KB 向量暂存
    pipe.InitBuffer(betaBuf, T64 * H * sizeof(float));         // 4KB beta 块专用
    ...
    LocalTensor<float> betaBlk = betaBuf.Get<float>();        // [64,16] 独立 TBuf
    ...
    // （rho/gl/betaF/eV/e2V/rV/zerosF = 1152 el; beta 块独立 TBuf——曾以 msBuf
    //   尾切片承载 4KB 载入, 值渗入相邻 sTt2 首 240 奇槽（beta 位型）, 勿回退）
```

同时把 `betaBuf` 加进 TBuf 声明列表：

```cpp
    TBuf<TPosition::VECCALC> gkBuf, qkBuf, stBuf, aqBuf, lfBuf, tDBuf,
        t2Buf, vnBuf, eyeBuf, mskBuf, msBuf, betaBuf, sTBuf, warmBuf;
```

要点：
1. `msBuf` 缩到 9×128 = 1152 个 f32，**等于**剩余逻辑张量的精确总和（不多不少，便于日后加一项就立刻越界可见）；
2. 块载入缓冲单独开 TBuf，靠 `TPipe` 的分配器保证不重叠；
3. 改完必须重新 dump 受害区确认清零，而不是只看精度用例——本例受害区只在部分 chunk 显现。

## 设计决策

- 为什么不全用一个大 buffer 加上限校验？`TPipe`/`TBuf` 没有"切片越界断言"，把多个逻辑张量塞进一个 buffer 时越界完全静默；块载入（4KB）与逐元素暂存（128 元素级）生命周期不同，拆开更符合"生命周期分组"。
- 代价：多一个 TBuf 占用 4KB UB。为腾出这 4KB，作者把原本的双缓冲 staging 降成单缓冲（`stBuf` 只留一份 16KB），总 UB 仍在 240KB 预算内。
- 被放弃的方案：`msBuf` 直接按 2176 元素分配（17×128）。可行但会把"块载入"和"逐元素暂存"继续耦合，且该 TBuf 之后还要被别的相位复用，容量语义会越来越难核对。选中 `recommended_fastpath`（独立 TBuf）。

## 系统信息

- 平台：Ascend310P3（DAV_2002 / m200），CANN 9.1.0，UB 240KB / 8 核。
- 相关文件：`kernel/chunk_scan.cpp`（TBuf 布局、beta 块载入与标量列抽取、`S_T` 行块 push）；`host/chunk_scan_host.cpp`（beta 平铺 f32 的产出方）；诊断脚本 `<diag-dir>/chunk_scan/scr.py`（kernel 内 dump + host 回读 GM scratch）。
- 构建：`bash build.sh` → `build/lib<generic>_ops.so`。

## 完整代码

见 `## 解决配方` 的 before/after 与 TBuf 声明；改动为"拆独立 `betaBuf` + 合并 buffer 缩容"，其余切片偏移不变。

## 预防

- 共用 TBuf 时把**每个切片的 (起点, 长度) 列表写成算式并求和**，直接与 `InitBuffer` 的容量比较；不要用"13×128"这种压缩写法，写成一串显式加总更不容易错。
- 新增/调整任何切片后，立刻 dump 相邻 TBuf 的首尾各 8 行（本例受害区就是"首 8 行"）——受害区多半从邻居的**头部**开始。
- 现象侧自检：邻居区出现"**部分行非零、其余全零**"或"**只有奇数下标非零**"，几乎必然是"某块 f32 数据错位落进 f16 区"。

## 验证信号

来源：分块扫描 kernel（310P）kernel 重写期间的精度排查。以下均为本轨迹内的工具输出。

- 失败签名：`B_ST` 槽首 8 行非零（行 0~7，值 1.25~1.45，只落奇数 f16 下标），行 32 起全零（来源平台：310P；证据等级：tool_observed）。
- kernel 结束后 host 回读 GM scratch：每个核 `B_ST` 区 240 个奇数偏移非零、最大 1.449，确认是真实写入而非探针伪影（来源平台：310P；证据等级：tool_observed）。
- 修复后同一 dump：`core0 B_ST region max abs: 0.0 / nonzero count: 0 of 16384`，`core1/core2 B_ST max: 0.0`（来源平台：310P；证据等级：tool_observed）。
- 该修复（独立 `betaBuf`）保留进终版 kernel，最终全量精度 40/40 PASS（来源平台：310P；证据等级：tool_observed）。
- 另一条同族轨迹（310P，CANN 9.1.0）：修复前 `gk[63]` 内核值 −159.0 vs 参考 −169.06（约 6% 偏差），前几行精确，且同期状态输出饱和/乱序；把标量区从 14×128 扩到 16×128 后，该轨迹用例仍 `0/1 PASS`、末行误差仍在——说明单纯扩容不是充分修复（来源平台：310P；证据等级：tool_observed）。
- 该轨迹后来的全量 50/50 出现在另一套 gk 打包（packed gkp）重写之后，与本卡的 msBuf 容量修复无因果关系，**不能**作为本卡第二条独立闭环（来源平台：310P；证据等级：tool_observed）。

## 失效边界

- 依赖"邻居 TBuf 紧随其后且其头部先被使用"这一布局事实；若 `TPipe` 分配顺序或 TBuf 声明顺序变化，受害区会换位置——**症状漂移不是修复有效的证据**，必须回到"切片需求总量 vs InitBuffer 容量"这条不变量。
- 只适用于手工算偏移的 TBuf 切片；用 `LocalTensor` 的子视图 API（带越界检查的实现）时表现不同。
- 未验证场景：UB 240KB 打满（>95%）时 `TPipe` 是否改变分配顺序（未验证）。
- 另一条独立轨迹（310P，CANN 9.1.0）的补充边界：该轨迹的"扩到 8KB"结论绑定其当时的子视图布局（后续随 gk 段回退，占用又重新变小）；应读作"**声明必须覆盖当前布局的总占用**"，而不是"8KB 是常数"。`InitBuffer` 的实际分配粒度（是否按 32B/512B 对齐向上取整）未查证。
- 未决项：为这类"共用 TBuf 偏移布局"补一个编译期/启动期断言（切片末端 ≤ buffer 长度），需要在 kernel 里能拿到 buffer 长度常量；本轨迹未做。
- 未决项（另一条独立轨迹）：越界读为何恰好让末行差约 6%（而非更随机）未逐字节验证，推测与越界区同状态缓冲的特定行对齐有关。

## 坏实践

- 把多个逻辑张量压进一个 TBuf 后，用注释记"总需求 2176 el"却在 `InitBuffer` 写 `13 * 128`（1664）——注释与实际容量脱钩，且越界完全静默。
- 见到"某几行错、改动后错的行会漂移"先去怀疑算术/掩码；这类"漂移"恰恰是 UB 邻居被写坏的典型特征。
- 依赖 dump 结果下结论而不做 host 侧回读二次确认——本例 dump 与回读一致才排除了探针伪影。
- 手算 `N*128` 偏移却不核总字节数；只跑弱参数用例验收，会把越界影响压到门限以下。

## 误诊

- 曾怀疑是 Nd2Nz 读新推 GM 槽命中旧线（`agent_reported`，另一条真实存在的 m200 装载律），并为此加暖读；暖读对该现象无改善。
- 曾怀疑探针本身有 MTE2→MTE3 抢序（`agent_reported`）而把结论撤回一轮；后续补全屏障后该区仍非零，才确认是真写入。
- 另一条独立轨迹曾沿"hi/lo f16 拆位精度不够""cumsum 累加误差""Mmad 链式累加"三个方向逐个估算，都把理论误差算到 `1e-5` 量级，与实测 6% 差三个数量级——这个数量级不匹配正是转向"内存越界"的线索（agent_reported）。
- **推断（非实测）**："越界 2KB = 8 行"与"1.25~1.45 是 f32 高半字"两条是算术推导：与观测的行数、值区间、奇偶性三重吻合，但没有单独的对照实验。
