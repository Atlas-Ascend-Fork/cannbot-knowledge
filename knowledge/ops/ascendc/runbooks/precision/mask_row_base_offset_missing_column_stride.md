---
type: Runbook
title: "掩码分块装载漏乘列宽：只有 query 梯度错"
description: 掩码按 [unit][row][tile][col] 落 GM，跨行装载基址写成 base+kt 而不是 base+kt*列宽，表现为仅 query 梯度坏、key/value 梯度逐位精确；判据是同一坏法在三种互斥编码假设下都不变。
tags: [task.debugging, topic.precision, topic.data_movement.data_copy, topic.implementation.masking]
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/8746f7ced6cef47e3fd7abd64c0eb827e28e2b56/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/data_move/DataCopy_GMAndUB_highdim_split.md
    role: primary
  - resource: https://gitcode.com/cann/asc-devkit/blob/8746f7ced6cef47e3fd7abd64c0eb827e28e2b56/docs/zh/api/SIMD-API/basic_api/data_structures/GlobalTensor/operator.md
    role: constraint
created_at: "2026-10-28T09:51:16Z"
updated_at: "2026-10-28T09:51:16Z"
platforms: ["310p"]
---

# 掩码分块装载漏乘列宽：只有 query 梯度错

## 现象

310P 注意力反向把 A 域掩码从 f32 矩阵换成 f16 通道（host 免 permute，kernel 侧跨行 strided 装载 + 硬件 `Compare` 转码）。编译绿灯后跑点验：

```
case 19  query: 1.822e+00/4.076e-04   key: 8.415e-04/8.414e-04   value: 2.169e-03/2.165e-03  FAIL
case  0  query: 1.530e+00/3.693e-04   key: 8.197e-04/8.196e-04   value: 2.874e-03/2.876e-03  FAIL
case 48  query: 5.519e+00/5.917e-04   key: 1.360e-03/1.360e-03   value: 2.344e-03/2.344e-03  FAIL
```

三个输出的分工很干净：**只有 query 梯度（A 域）坏，key/value 梯度（B 域）连最后一位都相同**。而且误差量级在多次重建之间保持同档（1.5~5.5），不像竞态。

## 适用场景

- 工程形态：Kernel 直调；掩码/元信息按 `[unit][row][tile][col]` 四维布局落 GM，kernel 侧按行跨块装载。
- API 路径：`DataCopy(dst, src[offset], DataCopyParams(blockCount, blockLen, srcStride, dstStride))` 的 **GM 基址算术**。
- 验证过的平台与 CANN 版本：Ascend310P3（dav-m200 / DAV_2002）+ CANN 9.1.0。
- 适用粒度：`operator_family`（凡“多维索引手工展平”的地址算术都适用）。
- 路线优先级：`safety_fallback`（展平索引一律写成显式乘法，并加断言）。
- fallback 声明：当多维索引需要手工展平时，回退到“每一项都写显式量纲因子 + 起止偏移断言”的写法，而不是依赖紧凑的一维下标；即使前者更啰嗦，也优先选它。
- 不适用 / 未验证：与平台无关，属 C++ 下标算术错误；其它布局（非 `[u][r][kt][c]`）未逐一验证。

## 判别方法

**根因**：掩码在 host 侧的布局是 `[u][r][kt][c]`，其中 `r` 是 64 行、`kt` 是分块、`c` 是 64 列。行的长度是 `nKT * 64` 个元素，所以“第 `kt` 个块的首元素”偏移是 `kt * 64`。

kernel 里写成了：

```cpp
// ✗ 每行只有 1 个元素间距 → kt>0 读到的是本行下一块的开头 1 个元素附近
DataCopy(maskI8, gMaskI[static_cast<int64_t>(u) * nKT * M64 * C64 + kt],
         DataCopyParams(M64, 4, (nKT - 1) * 4, 0));
```

`DataCopyParams(M64, 4, (nKT-1)*4, 0)` 的**块间步长**本身是对的（每行跳过 `(nKT-1)*4` 个 32B 块 = 该行其余 `nKT-1` 个块），但**基址**只前进了 `kt` 个元素。于是：

- `kt = 0`：基址正确 → 该块掩码是对的；
- `kt > 0`：基址错位 `kt*64 - kt` 个元素 → 每行读到的是别人的数据。

由于掩码只影响“该不该算”，错位后表现为“该掩的没掩 / 不该掩的掩了”，query 梯度行级偏差到 1.5~5.5 档；B 域用另一份按块位打包的元信息，完全不受影响。

**为什么这个 bug 极难从数值上认出**：它在 `nKT = 1` 时完全不可见；在 `nKT > 1` 时只污染 A 域；而且错位量随 `kt` 变，误差不是固定 stride 结构，容易被当成“装载/转码语义不对”。

**判据**：当“坏的是哪几个输出 / 哪些行”这个结构在 N 个互斥假设下完全不变时，去找所有假设共有的那段代码。

本会话里“只有 query 梯度坏”这个坏法跨三种彼此矛盾的掩码编码假设都成立：

| 编码方案 | query 梯度误差 | key/value 梯度 |
|---|---|---|
| host bool 0x01 直传 | ~0.47~0.55 | 逐位相同 |
| 取反成 0xFF | 4.5 / 14.8 / 22.9 | 逐位相同 |
| f16 + 内核 `Compare` 转码 | 1.822 / 1.530 / 5.519 | 逐位相同 |

三种方案的**数值幅度**差一个数量级，但“只有 query 梯度坏、key/value 梯度逐位相同”的结构一字不差。三种方案共同的部分不是编码，而是同一段地址算术——bug 就在那里。

这条判据的价值在于**省掉一整轮无效二分**：若只看“误差还是 0.5 档，说明编码还没对”，会继续在编码上打转（本会话确实先打转了两轮）。

## 解决配方

**before（verbatim，错误）**：

```cpp
DataCopy(maskI8, gMaskI[static_cast<int64_t>(u) * nKT * M64 * C64 + kt],
         DataCopyParams(M64, 4, (nKT - 1) * 4, 0));
```

**after（verbatim，正确）**：

```cpp
// ✓ 块内偏移按"每行 nKT 个 64 元素块"展平
DataCopy(maskI8,
         gMaskI[static_cast<int64_t>(u) * nKT * M64 * C64 +
                static_cast<int64_t>(kt) * C64],
         DataCopyParams(M64, 4, (nKT - 1) * 4, 0));
```

同轮结果（同一 build，只改这一行）：

```
case 19  query: 4.076e-04/4.076e-04  PASS
case  0  query: 3.693e-04/3.693e-04  PASS
case 48  query: 5.917e-04/5.917e-04  PASS      # 三个输出的 ours 与 ref 误差逐位相同
```

随后 9 例回归全 PASS 且逐位相同。

要点：`DataCopyParams` 的 stride 单位是 32B 块、基址单位是元素，两套量纲同时出现在一行里；基址这一项必须显式乘列宽 `C64`，不能沿用“块数”的直觉。

## 设计决策

- 展平索引一律写成显式乘法（`kt * C64`），不用凑巧等价的紧凑写法：这类 bug 在 `kt = 0` 与 `nKT = 1` 时全部隐身，靠用例覆盖不可靠。
- 把判据放在“坏法结构是否跨假设不变”，而不是“误差档位是否下降”：误差档位随编码方案变，结构才是稳定的信号。
- 路线优先级：safety_fallback。

## 系统信息

- 平台：Ascend310P3（dav-m200 / DAV_2002），CANN 9.1.0。
- 相关文件：`kernel/kernel_entry.cpp`（A 域 visit-load 掩码段）。
- 布局：host 侧掩码 `[u][r][kt][c]`（`r = M64` 行，`c = C64` 列）；每行 `nKT` 个块。
- 量纲对照：`DataCopyParams` 的 `srcStride`/`dstStride` 以 32B 块计；`GlobalTensor` 下标以元素计。

## 完整代码

after 的完整因果单元（即上面“解决配方”中的 `DataCopy` 调用）：基址 = `u * nKT * M64 * C64 + kt * C64`，块间步长 = `(nKT - 1) * 4`（每行其余 `nKT-1` 个 32B 块），`blockCount = M64`（每行一次 4 块 = 64 个 f16 元素）。

```cpp
DataCopy(maskI8,
         gMaskI[static_cast<int64_t>(u) * nKT * M64 * C64 +
                static_cast<int64_t>(kt) * C64],
         DataCopyParams(M64, 4, (nKT - 1) * 4, 0));
```

## 性能影响

不改变任何 GM 流量或指令数：修复只是把基址算术补上一个量纲因子，装载次数、stride 与搬运字节数完全不变。本卡无受控性能 A/B，只记录“无方向性影响”。

## 预防

- 手工展平索引时逐项写出量纲因子（`* C64`），并在括号里注明单位（元素 / 32B 块）。
- 回归集必须含 `nKT ≥ 2` 的用例：`nKT = 1` 的几何对本 bug 完全无感。
- 把“坏法结构”与“误差档位”分开记录：前者是判据，后者只是当前编码方案的副产物。
- 换掩码编码方案后，先确认坏法结构是否变化；结构不变就回头查所有方案共用的地址算术。

## 验证信号

来源说明：一次 Ascend310P3 注意力反向迁移会话，逐输出误差对拍 + 9 例回归。

- 修复前：三个点验例 query 梯度误差 1.5~5.5 档，key/value 梯度与 ref 逐位相同；跨多次重建误差保持同档（来源平台：310P；证据等级：tool_observed）。
- 同一坏法在 bool 0x01（query 梯度 ~0.5）、0xFF（query 梯度 4.5~23）、f16+Compare（query 梯度 1.5~5.5）三种编码下结构不变（来源平台：310P；证据等级：tool_observed）。
- 只改这一处偏移后 3/3 点验 PASS 且 ours 与 ref 误差逐位相同；9 例回归全 PASS 逐位相同（来源平台：310P；证据等级：tool_observed）。

## 失效边界

- 该判据要求“结构”可比（同一批用例、同一组输出、同样的行集合）。若不同假设下坏行集合也变了，那更可能是竞态或多因叠加，不能套用。
- `nKT = 1` 的用例对本 bug 完全无感；只用单块几何做回归会漏掉它（本会话的点验集里刻意含 `nKT ≥ 2` 的例）。
- 地址算术错误与平台无关，不要把“换平台/换 dtype 也许就好了”当修复。
- 未验证 `C64` 取其它 tile 宽度（非 64 列）时的等价写法；量纲因子应随列宽同步替换。
- 未决项：是否需要在装载后加“首元素/末元素值 == 预期”的断言，本会话未实施。

## 坏实践

- 把“误差还是同一档”当成“上一次改动没生效”的证据——本例里误差档位会随编码变，唯一不变的是坏法结构。
- 只跑“能过的那几个用例”验收（前缀掩码 / 单块几何的例恰好不触发）。
- 展平索引手写 `base + a*b + c` 而不写显式 `* C64` 之类的量纲因子：单位不一致（元素 vs 32B 块）是这类 bug 的温床，且 `DataCopyParams` 的 stride 单位是 32B、基址单位是元素，两者混用极易漏乘。

## 误诊

- **误诊 1**：因为 query 梯度误差停在 0.5 档，判定“掩码编码还没对”，继续在 bool/0xFF/f16 三种编码间打转——两轮无效二分。真实原因是三种编码共用的地址算术。
- **误诊 2**：把误差随 `kt` 变化读成“装载/转码语义不确定”，从而怀疑 `Compare` 的输入布局；`kt = 0` 块始终正确这一事实本应直接把怀疑指向基址。
