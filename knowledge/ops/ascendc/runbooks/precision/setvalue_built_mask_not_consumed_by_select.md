---
type: Runbook
title: SetValue 写的掩码是字节粒度，Select 按 bit 消费
description: SetValue 逐元素写 int8 掩码时每元素占 1 字节，而 Select 的 selMask 每元素只取 1 bit；行内 Select 只读行首 count/8 字节，于是每 8 个元素共用同一字节的位，表现为块级零化对、元素级漏掩。改用 Compare 产出位打包掩码。
tags: [task.debugging, topic.implementation.masking, topic.precision, topic.compute.elementwise.comparison_logic]
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/8746f7ced6cef47e3fd7abd64c0eb827e28e2b56/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/compare_and_select/overview.md
    role: primary
  - resource: https://gitcode.com/cann/asc-devkit/blob/8746f7ced6cef47e3fd7abd64c0eb827e28e2b56/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/compare_and_select/Compare.md
    role: constraint
  - resource: https://gitcode.com/cann/asc-devkit/blob/8746f7ced6cef47e3fd7abd64c0eb827e28e2b56/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/compare_and_select/Select.md
    role: constraint
created_at: "2026-10-28T09:51:16Z"
updated_at: "2026-10-31T09:21:53Z"
platforms: ["310p"]
---

# SetValue 写的掩码是字节粒度，Select 按 bit 消费

## 现象

为了让“两个半 tile chunk 打包进一个整 tile”的方案精确（块对角下三角：保留两块各自的严格下三角，掩掉跨块两个子块），kernel 里用嵌套循环 `SetValue` 构造了一张 int8 掩码 `m2`：

```cpp
        // m2 = tril(-1) AND 同半块（pair: 块对角下三角, 掩掉跨 chunk 块 (b,a)）
        for (int32_t i = 0; i < T64; ++i) {
            for (int32_t j = 0; j < T64; ++j) {
                const bool same = (j < T64 / 2) == (i < T64 / 2);
                m2.SetValue(i * T64 + j,
                            (j < i && same)
                                ? static_cast<int8_t>(-1)
                                : static_cast<int8_t>(0));
            }
        }
```

然后按行 `Select`：

```cpp
        const LocalTensor<int8_t>& msk = pairMode ? m2 : m1;
        for (int32_t i = 0; i < T64; ++i) {
            Select(lf[i * T64], msk[i * T64], t2[i * T64], zeros2,
                   SELMODE::VSEL_TENSOR_TENSOR_MODE, T64);
        }
```

结果：整 tile（单 chunk）形态的用例全部通过，**半 tile（pair）形态全红**——gate=off 用例误差达到 1.5e3 量级（垃圾值），gate=on 用例 0.35~3.0e3；同一批 8 例只有 2 例 PASS。

dump 后的指纹非常特定（把 kernel 的 `lf` 与“按 staging 张量重建的块对角下三角”逐元素比）：

```
lf vs block-tril(stagedL): 0.828125
lf[1,:4]: [0.1055, 0.6094, 0.0374, 0.015]
exp[1,:4]: [0.1054, 0.0, 0.0, 0.0]
```

即：块外（列 32-63）已被零掉（块掩码的“宏观”效果部分生效），但块内行 1 的对角线与上三角**没有被掩掉**，而代码里 `m2[1][1..3]` 明确应为 0。掩码逐元素逻辑正确、行内 Select 也已是“逐行”形态——问题不在逻辑。

另一条独立轨迹（310P，CANN 9.1.0）给出同一根源的另一面：host 侧把 torch bool 掩码直接喂 `Select`，A 域输出出现半错（dq 误差 ~0.5 档），而 B 域用 kernel 内 `Compare` 产生的掩码却正确。把 bool 取反成 `0xFF` 再传，误差反而涨到 4.5/14.8/22.9 三档；两种手工编码都不对，说明问题在“编码格式本身”——`Select` 只按 bit 消费 `selMask`，host 的字节掩码不是它要的位打包格式。

## 适用场景

- 工程形态：AscendC kernel 内 `Select` + 手工构造的 int8 掩码（`LocalTensor<int8_t>`）用于三角/块结构裁剪；或 host 侧准备掩码、kernel 侧 `Select`/`Compare`。
- API 路径：`LocalTensor::SetValue`（逐元素写标量）→ `Select(dst, selMask, src0, src1, VSEL_TENSOR_TENSOR_MODE, n)`；`Compare(dst, src0, src1, CMPMODE, n)` 产出的**位打包**掩码（每个元素 1 bit）；`Compare(dst, src0, src1, CMPMODE::NE, n)` 转码 host bool。
- 验证过的平台与 CANN 版本：Ascend310P3（dav-m200 / DAV_2002）+ CANN 9.1.0（实测）。
- 适用粒度：`operator_family`（掩码生成 + 选择这一函数形态，同一算子的其它阶段不适用）。
- 路线优先级：**recommended_fastpath**——掩码一律 `Compare` 生成；需要复合掩码时做多遍 Select。
- 明确不适用 / 未验证场景：其他代际未验证；其他掩码 dtype（f16/bool tensor）与 `SELMODE` 未验证；`SetValue` 写入 f32 数据张量本身是正常的（本卡只针对“把 SetValue 张量当掩码用”）。

## 判别方法

**根因**：`Select` 的 `selMask` 是**位打包**的（每元素 1 bit），而 `SetValue` 逐元素写入的是**一字节一元素**。本卡的 `m2` 是 `[64,64]` int8 张量，SetValue 写了 4096 字节；行内 `Select(..., T64)` 却只从该行起始读 `64/8=8` 字节，按 LSB-first 解释为 64 个 bit。于是输出元素 `e` 的掩码取自行内第 `e/8` 列的字节的第 `e%8` 位：**每 8 个连续元素共用同一列的布尔值**。

这精确解释了 dump 指纹：行 1 只有列 0 应为 `-1`（0xFF），行内 Select 读到的前 8 字节里 bit 0..7 全部来自列 0 的 0xFF，所以列 0..7 全被保留（`lf[1,:4]` 非零）；列 8/16/… 为 0x00，所以行 1 的上三角与后段被正确清零。即“块级零化对、元素级漏掩”不是 Select 不认 SetValue 张量，而是字节/位粒度不匹配。

同理，host 侧把 torch bool 掩码直接喂 `Select`（每元素 1 字节 0x01）也是字节/位不匹配：Select 只读前 `count/8` 字节并逐位解释，等价于只用到前 1/8 的数据且每字节首位生效；取反成 0xFF 只是换了一种错法。`Compare` 产出的掩码之所以正确，是因为它的 dst 就是按 bit 展开的位打包缓冲（同批 A/B 已实测确认这一位打包语义）。

判别方法：

1. 先把失败范围二分：整 tile 形态通过、只有引入新掩码的形态失败 → 锁定掩码来源，而不是 GEMM/装载。
2. dump Select 之后的矩阵，与“按同一份 staging 张量在 torch 里重建的期望掩码结果”逐元素比。若**块级零化对、元素级漏掩**，且掩码由 SetValue 构造 → 本根因。可进一步对指纹：按位打包解释，每 8 个连续元素的掩码应相同（取自行内第 `e/8` 列的字节位）；例如行 1 只有列 0 为 0xFF，则列 0..7 应全部保留。
3. 把同一张掩码改成 Compare 生成（或直接删掉该掩码、用两遍 Compare+Select 等价替代），误差应立即回到 1e-4 量级。
4. 对 host 掩码：分别试 0x01 与 0xFF，若两者都不对且 B 域（kernel 内 Compare 生成）正确 → 编码来源问题，而非极性。

## 解决配方

不改掩码表，改为**两遍 Select**：第一遍用已有的 Compare 掩码做全局严格下三角；第二遍只对下半块行做“列 ≥ 半 tile”的 Compare 掩码，再就地 Select（把跨块 (b,a) 子块清掉）。

**before（SetValue 掩码）**：见“现象”中的两段代码。

**after（verbatim，含第一遍与第二遍）**：

```cpp
        for (int32_t i = 0; i < T64; ++i) {
            Select(lf[i * T64], m1[i * T64], t2[i * T64], zeros2,
                   SELMODE::VSEL_TENSOR_TENSOR_MODE, T64);   // tril(-1)
        }
        if (pairMode) {
            // 第二遍: 掩掉块 (b,a) —— 行 32-63 保留列 32-63（j >= 32）
            LocalTensor<float> thr = tD;
            LocalTensor<float> cj = t2;
            for (int32_t j = 0; j < T64; ++j) {
                cj.SetValue(j, static_cast<float>(j));
            }
            for (int32_t i = T64 / 2; i < T64; ++i) {
                Duplicate(thr, 32.0f, T64);
                Compare(m2[i * T64], cj, thr, CMPMODE::GE, T64);
                Select(lf[i * T64], m2[i * T64], lf[i * T64], zeros2,
                       SELMODE::VSEL_TENSOR_TENSOR_MODE, T64);
            }
            PipeBarrier<PIPE_ALL>();
        }
```

要点：

- 第二遍的掩码 `m2` 现在由 `Compare` 就地生成（列索引 `cj` 对阈值 32 做 `GE`），只占用原来的 `m2` 缓冲，语义和旧表一致但字节形态可用；
- `cj`/`thr` 复用 `t2`/`tD` 两个随后不再承载有效数据的缓冲（第一遍已消费 `t2` 的原始 L；`tD` 是 readout 的中间缓冲），用后 `PipeBarrier<PIPE_ALL>()` 排空；
- 列索引向量虽然也用 `SetValue` 写，但它作为 **Compare 的 f32 输入数据**，不是掩码——这条路径正常。

**合并轨迹的解法（kernel 内 `Compare` 转码 host bool，verbatim）**：

```cpp
// ✓ kernel：原始 bool/半精度掩码 → 硬件 Compare 生成 sel → Select
if (lean) {
    // 实证: sel 编码须为硬件 Compare 输出——现场转码
    Compare(keepM, maskI8, zeroH, CMPMODE::NE, M64 * C64);
    Select(z, keepM, z, negOneM,
           SELMODE::VSEL_TENSOR_TENSOR_MODE, M64 * C64);
    Exp(z, z, M64 * C64);                 // 被掩位置 Exp(NEG_BIG)→0
} else {
    Exp(z, z, M64 * C64);                 // p
    Mul(z, z, maskMat, M64 * C64);        // ×keep(host 0/1 物化)
}
```

```cpp
// ✗ 两种错误尝试
// (a) host 直接把 torch bool 字节交给 Select
Select(z, maskI8, z, negOneM, SELMODE::VSEL_TENSOR_TENSOR_MODE, M64 * C64);
// (b) 把 bool 取反成 0xFF 再传
auto maskA = (-keepT.to(torch::kChar));      // 0xFF
```

附带约束：`Compare` 的输入数据在 dav-m200 上只接受 half/float（`SupportType<T, half, float>()`，不支持 int8 源），所以 host 的 bool/整型掩码需先转成 half（0.0/1.0）再参与 `Compare`；`Compare` 的 **dst 输出**是位打包的 `int8_t`/`uint8_t` 字节缓冲（每元素 1 bit，`count` 个元素占 `count/8` 字节），不是 half——掩码落盘类型不要按 half 理解。见同批 dtype 白名单卡与“整块 Select 的掩码必须连续位打包”卡。

## 设计决策

- 不尝试“先 SetValue 再用某种 Cast/And 把它变成合法掩码”：没有证据表明存在稳定的转换路径；用 Compare 现算更廉价（每个下半块行一次 Compare）。
- 两遍 Select 的成本是“下半块行数”次额外 Compare+Select；相对重新设计 GEMM 让上三角天然为零的方案，改动面小得多，且保持既有数值路径不变。
- 复合掩码（A AND B）优先拆成“多遍 Select”而不是“构造一张复合掩码表”——复合表要么 SetValue（本坑），要么需要额外的 int8 向量 And（未验证）。
- 合并轨迹选“host 传原始 bool（零拷贝、免 permute）+ kernel 内 Compare 转码”，而不是“host 侧预先转成 Select 可消费的字节”：`Select` 要的是位打包 bit 流，host 的逐元素字节（0x01/0xFF 都试错）不是这个格式；在 host 侧手工打包位流既无公开约定也不可移植，由 `Compare` 产生最稳。
- 路线优先级：recommended_fastpath。

## 系统信息

- 平台：Ascend310P3 / dav-m200（8 vector core），CANN 9.1.0。
- 工程形态：CMake + `build.sh` → `lib<generic>_ops.so`；kernel `kernel/kernel_entry.cpp`，精度套件 `tests/precision_suite.py`。
- 相关缓冲：`mBuf` 扩成 2 张 tile 大小的 int8（`m1` 严格下三角、`m2` 块掩码/第二遍掩码）；`tD` 为 readout 中间缓冲，`t2` 为当前 GEMM 结果的 f32 行主序副本。
- 合并轨迹相关文件：`host/host_stage.cpp`（掩码物化）、`kernel/kernel_entry.cpp`（A 域 Compare/Select 段）。
- 第一遍的全局掩码生成（verbatim，与第二遍同构）：

```cpp
        for (int32_t i = 0; i < T64; ++i) {
            Duplicate(ifRow, static_cast<float>(i), T64);
            Compare(m1[i * T64], colIdx, ifRow, CMPMODE::LT, T64);   // j<i
        }
```

## 完整代码

“解决配方”中的 before/after 两段为完整因果单元；掩码生成（第一遍 Compare 段、第二遍 Compare+Select 段）与缓冲声明（`LocalTensor<int8_t> m1 = mBuf.Get<int8_t>(); LocalTensor<int8_t> m2 = m1[T64 * T64];`）均已内联。合并轨迹的 Compare 转码段亦已内联。

## 性能影响

相对“一张复合掩码 + 一遍 Select”，本方案多出“下半块行数”次 Compare 与 Select；相对需要正确性的替代方案（重设计 GEMM），这是很小的代价。具体倍率本会话未单独测量（未验证）。

## 预防

- 掩码只来自 `Compare`；在 kernel 头注释里写明“SetValue/Scalar 写的是字节粒度，`Select` 按 bit 消费，不能直接当掩码用”。
- 复合掩码用多遍 Select 实现，不要合成掩码表。
- 掩码/索引缓冲要声明在 kernel 外层作用域：本会话第一版把 `ifRow`/`colIdx` 写在 init 常量块里，第二遍 Select 段直接编译失败（`use of undeclared identifier 'ifRow'` / `'colIdx'`，3 errors）——这不是语义问题，而是作用域问题。
- 对 host 掩码：把“编码不对”和“极性反了”分开排查，不要用取反去试。

## 验证信号

来源说明：主轨迹与合并轨迹均来自 Ascend310P3 单卡、CANN 9.1.0 会话内的实测。

- SetValue 掩码版本：8 例 smoke 只有 2 例 PASS，半 tile 用例误差 3.5e-1 ~ 3.0e3；整 tile 用例全部 PASS（来源平台：310P；证据等级：tool_observed）。
- dump 指纹：`lf[1,:4] = [0.1055, 0.6094, 0.0374, 0.015]` 而期望 `[0.1054, 0, 0, 0]`，逐元素 max 差 0.828；块外列已零化（来源平台：310P；证据等级：tool_observed）。
- 改两遍 Compare+Select 后同一 8 例全部 PASS（误差量级回到 1e-4 ~ 1e-3，与各用例 gate 一致）（来源平台：310P；证据等级：tool_observed）。
- 随后全量精度套件 `50/50 PASS`（来源平台：310P；证据等级：tool_observed）。
- 第一版改造曾因 `ifRow`/`colIdx` 作用域编译失败 3 处，补上局部声明后 `BUILD_OK`（来源平台：310P；证据等级：tool_observed）。
- 合并轨迹：传 torch bool（0x01）时 dq 误差约 0.5 档、dk/dv 逐位相同；传 0xFF 后 dq 误差升到 4.5/14.8/22.9 三档，恶化（来源平台：310P；证据等级：tool_observed）。
- 合并轨迹改为 kernel 内 `Compare` 转码 + half 掩码后，配合另一处 tile 偏移修正，dq/dk/dv 与参考逐位相同，9 例回归全 PASS（来源平台：310P；证据等级：tool_observed）。

## 失效边界

- 只在 `VSEL_TENSOR_TENSOR_MODE` + int8 掩码 + f32 数据上验证；`SetValue` 掩码在**行内小 count**（本卡第二遍的 count=行宽）同样失效过（第一版 `m2` 就是行内调用）——这与“字节/位粒度不匹配”一致：行内 Select 同样按 bit 消费，与 count 大小无关。
- 根因已明确为字节/位粒度不匹配（`selMask` 位打包语义由同批 A/B 在 310P 上实测确认），不是“编译器把 SetValue 优化掉”的假设，也不是 Select 独占 Compare 输出的黑盒行为。
- 未验证 f16 数据、bf16 掩码、其他 SELMODE。
- 合并轨迹只在 Ascend310P3 + CANN 9.1.0 实测；`Compare` 的 dtype 白名单在其它代际可能更宽（int8 可用），届时可用更省带宽的掩码。用 `Select` 做“置大负数”依赖后续 `Exp` 下溢；若后续是加法而不是 `Exp`，大负数会污染求和，需换成真正的乘法掩码。
- 未决项（优先）：如果将来需要“A OR B”这类复合掩码，多遍 Select 的等价写法未在本会话验证；合并轨迹的“逐位相同”验证与 tile 偏移修正同一轮完成（该轮同时含两处改动），编码修正没有单独回归一轮，其必要性由 0x01/0xFF 两次失败与 B 域对照支撑。

## 坏实践

- 手工构造掩码表（`SetValue`、标量循环、`Duplicate` 后局部改）——即使逻辑逐元素正确，运行时也可能不被识别。
- 把掩码缓冲的声明塞进常量初始化块，导致后续代码段无法引用（编译期暴露，但会浪费一轮构建）。
- host 侧手工构造“硬件编码”（0x01/0xFF/其它魔数）：没有稳定约定，跨版本必炸。
- 把“编码不对”当成“极性反了”，用取反去试（本 trace 中使误差恶化一个数量级）。

## 误诊

- **误诊 1**：先怀疑 `m2` 的逐元素逻辑写错（`same` 判定、`j<i` 边界）——逐行验算后逻辑正确。
- **误诊 2**：怀疑 `m2` 缓冲被后续写入覆写、或 slice 的 `SetValue` 偏移基准不对（`m1[T64*T64]` 之后的 slice 偏移按相对计）——排除。
- **误诊 3**：怀疑 `Select` 的 `src1` 应为行向量（早期版本的 `zerosF`）而非 `[64,64]` 基址——等价，非根因。
- **误诊 4**（外部转述，未采信为实测）：把失败归因为“pair staging 的 g/relC 指数路径错”；后续 dump 证明 staging 的 pk/衰减因子正确，真正卡住的是掩码。
- 合并轨迹一度怀疑是“`Select` 放在 `Exp` 前还是后”的数学差异——两次实验证明两者等价，真实的差异在 `selMask` 的位打包格式。
