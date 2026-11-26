---
type: "Runbook"
title: "310P im2col：V2Pro/多块 V1 的 s>1+f>1 全零"
description: "310P 硬件 im2col 在 V2Pro（mode 0）与 V1 多块（mode 3）下，stride>1+filter>1 静默全零；V1 单块（mode 1）在 M=16 prepad 用例上曾 PASS，最终探针未复跑，不能把 V1 整体判死。当前落地用 4 相位/软件 im2col。"
tags: [task.debugging, topic.performance.analysis, topic.data_movement, topic.programming_model.execution_unit.cube]
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/a6a99bcf65cdf43202e0e270ea1f9cdc79cf1c23/impl/basic_api/dav_m200/kernel_operator_mm_impl.h
    role: implementation
  - resource: https://gitcode.com/cann/asc-devkit/blob/a6a99bcf65cdf43202e0e270ea1f9cdc79cf1c23/include/basic_api/kernel_struct_mm.h
    role: header
created_at: '2026-11-05T07:33:56Z'
updated_at: '2026-11-11T09:46:56Z'
platforms: ["310p"]
---

# 310P im2col：V2Pro/多块 V1 的 s>1+f>1 全零

## 现象

在 7 号 conv2d 的 V2Pro（mode 0）与 V1 多块（mode 3）路径上给 stride=2 支持时，s=2、k=3×3 的用例输出全零。现象非常“干净”：

- 不是错值，是**全零**：探针把 fmap 填成 1,2,3,… 的斜坡、B 放单位阵，理论上 C 应逐元素复现窗口内容；实际 A 面板每个 m、每个 tap 都是 0。
- 换 `l1W=10/12/14/16` 四个宽度、V1 多块（mode 3）与 V2Pro（mode 0）两种模式，全部零；不是某个宽度没对齐。
- **反例（同一轨迹）**：prepad + `P=0` 的 M=16 探针里，V1 单块（mode 1）在 s=2、k=3×3 上曾 PASS（max|diff|=0、bad=0/2304）；最终探针没有再跑 mode 1，所以本卡只否定 mode 0/3，**不否定 V1 单块**。
- 同一套代码把 filter 换成 1×1、stride 仍为 2，立刻正常，且能解码出 `m→(h·S, w·S)` 的栅格映射（`R=(l1W-1)/S+1`）。

也就是说，失败不是“stride 参数没生效”，而是 **在 mode 0/3 上，stride>1 与 filter>1 同时出现时硬件 im2col 返回全零**；mode 1 的单块反例仍未解释。

## 适用场景

- **工程形态**：AscendC kernel 直调；310P 上用 `LoadData3DParamsV2Pro`（或 V1 `LoadData3DParamsV1`）做卷积/滑窗的硬件 im2col 展开。
- **API 路径**：`LoadData3DParamsV2Pro` + `SetFmatrix` + `Mmad`；参数编码里的 `filterConfig` 同时带 `filterH/filterW/strideH/strideW`。
- **验证过的平台与 CANN 版本**：Ascend310P3（DAV_2002 / dav-m200）+ CANN 9.0.0。
- **适用粒度**：`operator_family` —— 310P 上 V2Pro（mode 0）/V1 多块（mode 3）“stride>1 + filter>1 走硬件 im2col”的 7 号 conv2d 探针/同族 kernel；证据来自单一探针、固定 C1=1 与有限 filter 矩阵，不能直接外推到所有算子/所有形状，也不覆盖 V1 单块（mode 1）。
- **路线优先级**：**`banned`（仅 mode 0/3）** —— V2Pro 与 V1 多块“stride>1 且 filter>1 直接用硬件 im2col”实测不可用；s=2 的落地路线是“4 相位堆叠成 stride-1 图，再用 filter 不变、stride=1 的硬件 im2col”，或软件 im2col。V1 单块（mode 1）是**未复核**的候选，不作为 banned 依据。
- **明确不适用 / 未验证场景**：filter=1×1、任意 stride 的组合（已验证 s=2 正常）；**V1 单块（mode 1）的 s=2+filter>1 只在 M=16 prepad 探针上 PASS 过，最终探针未复跑**；stride>1 + filter=1×N/N×1 的组合未逐一验证；dilation>1 的交互未验证；其它代际未验证。

## 根因

**机制层未公开**：V2Pro 走 `img2colv2_cbuf_to_ca`，V1 走 `img2col_cbuf_to_ca`（不是同一个 intrinsic 家族）；头文件只给参数编码，不给“哪些参数组合合法”的约束表。可判定的事实是：

- 在本探针的 mode 0/3 上，`filterH/filterW > 1` 且 `strideH/strideW > 1` 时，指令不报错，A 面板返回全零；mode 1 的同一组合有 PASS 反例。
- 在本次探针（`mStart=0`）下，mode 0/3 的全零与 `l1W` 无关；只要 filter 是 1×1，stride=2 就能正常解码。`mStart≠0` 没有扫描，不能据此说“与 mStart 无关”（失效边界已列）。**mode 1 的反例说明不能把 mode 0/3 的结论推广到整个 V1。**
- 因此这不是“窗口越界读到了 pad 零”，也不是“栅格宽度算错”——换宽度不会改变全零；在 mode 0/3 上它表现为参数组合被硬件判为不可用，且没有错误码。mode 1 为什么能 PASS 仍未定论。

也可以从“窗口覆盖”角度理解为什么它像非法组合：stride=2、filter=3 时，栅格宽度 `R=(l1W-1)/S+1`，最后一个窗口要求 `l1W ≥ (R-1)·S + kH`；当 `l1W` 不满足时硬件可能直接按无效处理。但实测把 `l1W` 加到 16 仍然全零，所以“覆盖不足”只能解释部分宽度，不能解释全部；机制层仍未定论。

## 尝试与观测

探针把 fmap 填成斜坡、B 放单位阵，直接解码 A 面板的每个 `(m, tap)`。完整探针脚本：

```python
import numpy as np, torch, torch_npu
SO = ("<op_build>/conv_standard2d_ext.cpython-311-aarch64-linux-gnu.so")
torch.ops.load_library(SO)
def panel(H,W,kH,kW,S,D,P,M,mode):
    C1=1; K=C1*kH*kW*16
    fmap = (1 + (np.arange(C1*H*W*16).reshape(-1) % 100000)).astype(np.float32)
    ft = torch.from_numpy(fmap).half().npu()
    bt = torch.from_numpy(np.eye(K, dtype=np.float16).reshape(-1)).npu()
    c = torch.ops.npu.conv_std2d_im2col_probe(ft, bt, 1,H,W,kH,kW,S,D,P,M,K,K,0,0,mode)
    cn = c.cpu().numpy(); mfr = M//16
    A = np.zeros((M,K), dtype=np.float32)
    for m in range(M):
        for n in range(K):
            A[m,n] = cn[(n//16)*mfr*256 + (m//16)*256 + (m%16)*16 + (n%16)]
    return A
def dec(v,H,W):
    if abs(v) < 1e-6: return "0"
    f = int(round(v))-1
    return f"{((f//(W*16))%H)},{(f//16)%W}"
for mode in (3,0):
    print(f"=== mode {mode} (V1)" if mode==3 else "=== mode 0 (V2Pro)")
    for W in (10,12,14,16):
        A = panel(W,W,3,3,2,1,0,16,mode)
        r = " ".join(dec(A[m,4*16],W,W) for m in range(16))
        print(f"  l1W={W}: m0..15 tap(kh1,kw1): {r}")
```

观测（逐字）：

```text
=== mode 3 (V1)
  l1W=10: m0..15 tap(kh1,kw1): 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
  l1W=12: m0..15 tap(kh1,kw1): 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
  l1W=14: m0..15 tap(kh1,kw1): 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
  l1W=16: m0..15 tap(kh1,kw1): 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
=== mode 0 (V2Pro)
  l1W=10: m0..15 tap(kh1,kw1): 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
  l1W=12: m0..15 tap(kh1,kw1): 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
  l1W=14: m0..15 tap(kh1,kw1): 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
  l1W=16: m0..15 tap(kh1,kw1): 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
```

对照（同探针、k=1×1、s=2）：能正常解码出 `m→(h·S, w·S)` 与 `R=(l1W-1)/S+1`，不是全零。

## 边界与处置

- **s=2 + filter>1（仅 V2Pro mode 0 / V1 多块 mode 3）**：不要走硬件 im2col；V1 单块 mode 1 仍有 PASS 反例，待复核，不在这条禁用范围内。可行路线：
  1. **4 相位堆叠**：host 把输入按 `(h%2, w%2)` 拆成 4 个相位平面，拼成一张 stride-1 的图，filter/权重按相位重排；之后 `S=1` 的硬件 im2col 可正常工作。这条路线在 7 号 conv2d 的 s=2 用例上已落地（v4 phase path）。
  2. **软件 im2col / 窗口直读**：把 stride 吸收进地址计算，不依赖硬件 im2col。
  3. **filter=1×1 特例**：仍可走硬件 im2col（已验证）。
- **不要把全零读成“数据没搬进来”**：全零的指纹是“所有 m、所有 tap 都零，且换 l1W 无效”；数据/布局问题通常会随宽度或 m 变化。

## 设计决策

- **为什么先做宽度扫描**：如果全零只出现在某些 `l1W`，那是覆盖/栅格问题；在 mode 0/3 下四个宽度全零，才把它归为该模式下的“参数组合非法”。
- **为什么同时测 V1 和 V2Pro**：V1 走 `img2col_cbuf_to_ca`、V2Pro 走 `img2colv2_cbuf_to_ca`，两者不是同一个 intrinsic；mode 3 与 mode 0 都零只能说明这两条路径都不可用，不能外推到 V1 单块（mode 1），后者有同轨迹的 PASS 反例。
- **为什么选 4 相位而不是继续调 stride 参数**：在 mode 0/3 上，硬件对 `stride>1 + filter>1` 没有可用路径；继续试 `l1W`/`mStart` 只是在无效组合里打转。mode 1 仍有 PASS 反例，先按 4 相位走稳妥路线，同时把 mode 1 列为待复核，不把整条 V1 判死。
- **当前方案路线档位**：`banned`（仅 V2Pro mode 0 / V1 多块 mode 3 的 `stride>1+filter>1`）；V1 单块 mode 1 为 `unverified/待复核`；替代路线是 `recommended_fastpath` 的 4 相位堆叠。

## 系统信息

- 目标平台：Ascend310P3（DAV_2002 / dav-m200），CANN 9.0.0；kernel 直调（`EXEC_KERNEL_CMD`/raw launch）。
- 探针：`op_kernel/conv_std2d_im2col_probe.cpp` + `precision/test_im2col_probe.py`；探针 op 通过 `torch.ops.npu.conv_std2d_im2col_probe(fmap, b, C1,H,W,kH,kW,S,D,P,M,N,K,mStart,kStart,mode)` 调用。
- 实现证据：`asc-devkit/impl/basic_api/dav_m200/kernel_operator_mm_impl.h:199-217`（V1 `img2col_cbuf_to_ca`）、`:265-282`（V2 非 Pro `img2colv2_cbuf_to_ca`）、`:328-355`（V2Pro A1→L0A `img2colv2_cbuf_to_ca`）；`include/basic_api/kernel_struct_mm.h:356`（`LoadData3DParamsV2Pro`）。

## 性能影响

本卡是路线可行性负结果，不主张性能收益。相对的路线代价：

- 硬件 im2col + stride=1（s=1 或 4 相位堆叠）：可用；
- 硬件 im2col + stride>1 + filter>1（mode 0/3）：实测全零；V1 单块 mode 1 有 PASS 反例，未定论；
- 软件 im2col / 窗口直读：可用，但搬运量随 filter 的 tap 数放大（同算子内部相对代价，来源平台 310P）。

## 预防

- 在 310P 上优先 `stride==1` 或 filter=1×1；若必须 stride>1+filter>1，先确认是 V2Pro（mode 0）/V1 多块（mode 3）（banned）还是 V1 单块（mode 1，未定论），不要用 mode 3 的负结果直接判死 V1 单块。
- 探针必须同时扫“filter=1×1 + stride>1”和“filter>1 + stride>1”两组；只测前者会得到“stride 支持”的假结论。
- 看到全零先做“宽度扫描”：如果换 l1W 仍然全零，优先怀疑参数组合非法，而不是数据没到。

## 验证信号

来源：7 号 conv2d v6/v7 战役的同一条开发轨迹（单条轨迹、单次上板；证据等级 `tool_observed`）。实现机制由 asc-devkit 固定提交 `a6a99bcf` 的 impl 源码独立核对。

- k=3×3、s=2、P=0、prepad 后 `H=W=10`：V1 多块（mode 3）与 V2Pro（mode 0）在 `l1W=10/12/14/16` 下 A 面板所有 `(m, tap)` 全零；max|diff|=1.024e+03、bad=1936/2304。（来源平台：310P；证据等级：tool_observed）
- k=1×1、s=2：同探针能正常解码出 `m→(h·S, w·S)` 与 `R=(l1W-1)/S+1`，不是全零。（来源平台：310P；证据等级：tool_observed）
- s=1、k=3×3（预 pad、P=0）在 **M=16 单块**探针上走 V2Pro 可 PASS；说明不是 im2col 整体坏了，而是 stride>1 + filter>1 的特定组合。注意多块 M=48、mode=3 的 s=1 k=3×3 用例仍 FAIL（同轨迹的 M=48 mode=3 输出：max|diff|≈8.96e2、bad=5984/6912），本条的 PASS 结论只适用于 M=16 单块。（来源平台：310P；证据等级：tool_observed）
- **反例**：V1 单块（mode 1）、s=2、k=3×3、M=16、prepad + `P=0` 的同探针曾 PASS（max|diff|=0、bad=0/2304）；最终探针没有复跑 mode 1，因此这条 PASS 目前只是未决候选，不能据此推翻 mode 0/3 的负结果，也不能把 V1 整体判死。（来源平台：310P；证据等级：tool_observed）

## 失效边界

- **未定论**：硬件指令为什么在 mode 0/3 下对 `stride>1 + filter>1` 返回全零、是否有“覆盖不足才非法”的精确条件，机制层未验证；**V1 单块（mode 1）的 s=2+filter>1 反例（同轨迹的 M=16 prepad 探针 PASS）没有再复跑**，是最高优先的未决项。**未决项（优先）**：用更细的探针扫 `mode 1 × filterH/filterW × strideH/strideW × l1W × dilation`，把“非法组合”的边界画出来，并尝试从 ISA 文档/二进制行为定位根因。
- **未覆盖**：stride>1 + filter=1×N/N×1、dilation>1 与 stride 的交互、`mStart≠0` 的组合、其它 `l1H/l1W`；不能从本卡外推。
- **平台**：只验证 310P；其它代际的 im2col 约束不同（未验证，推断不可迁移）。
- **替代路线的代价**：4 相位堆叠需要 host 侧拆相位/重排权重，且 s=2 时 K 维含零 tap；这些代价未在本卡量化。

## 坏实践

- 看到全零就继续调 `l1W`/`mStart`/`l1H`，把无效参数组合当成“还没对齐”。
- 只测 `filter=1×1 + stride=2` 就宣布“310P 硬件 im2col 支持 stride>1”，然后在真实 filter 上踩全零。
- 把 V2Pro 当成 V1 的“修复版”，以为换成 V2Pro 就能支持 stride>1 + filter>1；mode 0/3 都零，但 V1 单块 mode 1 有 PASS 反例。
- 把 mode 3 的全零推广成“V1 整体全零”；mode 1 的单块反例说明这个推广不成立，V1 单块要单独复核。

## 误诊

- 早期 v2-gate 的参数矩阵里同时列了 “s2” 和 “k1×1”，但 s2 那一格实际用的是 1×1 filter；后来被读成“s2 支持任意 filter”，这是本卡最值得记录的一次误诊。
- 第一轮把全零解释成“左/上偏移越界读到了 pad 零”，于是加 `l1W`；四个宽度全零后否定了这个假设。
- 也曾把 mode 3 的负结果写成“V1/V2Pro 全部全零”；后来发现同轨迹的 mode 1 s=2 k=3×3 曾 PASS，说明负结果只覆盖 mode 0/3，不能外推到 V1 单块。
