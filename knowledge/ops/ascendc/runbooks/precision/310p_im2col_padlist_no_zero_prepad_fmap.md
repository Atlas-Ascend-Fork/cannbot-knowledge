---
type: "Runbook"
title: "310P im2col padList 契约未定论：先预 pad + P=0"
description: "官方契约里 padList 是 [left,right,top,bottom] 填充列表、padValue 是填充值；早期探针用非零 padList + leftTop=-P、未预 pad 时 p=1 失败，终版改为零 padList + 预 pad 后 PASS。非零 padList 的成功形态未找到，prepad + P=0 是已验证配方。"
tags: [task.debugging, topic.precision, topic.data_movement, topic.programming_model.execution_unit.cube]
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/a6a99bcf65cdf43202e0e270ea1f9cdc79cf1c23/impl/basic_api/dav_m200/kernel_operator_mm_impl.h
    role: implementation
  - resource: https://gitcode.com/cann/asc-devkit/blob/a6a99bcf65cdf43202e0e270ea1f9cdc79cf1c23/include/basic_api/kernel_struct_mm.h
    role: header
  - resource: https://gitcode.com/cann/asc-devkit/blob/a6a99bcf65cdf43202e0e270ea1f9cdc79cf1c23/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_load/LoadData_3D.md
    role: constraint
created_at: '2026-11-05T07:33:56Z'
updated_at: '2026-11-09T00:00:00Z'
platforms: ["310p"]
---

# 310P im2col padList 契约未定论：先预 pad + P=0

## 现象

在 7 号 conv2d 的硬件 im2col 探针上做参数矩阵：`filter=3×3/3×1/1×3/2×1`、`stride=1`、`dilation=1`，以单位阵 B 让 C 直接复现 A 面板。结果非常规整：

- `p=0` 的所有 filter 组合**全部精确 PASS**（max|diff|=0）；
- 唯一失败的是 `p=1`：输出不是零，而是“源 flat 步长 = filterW”的错值——看起来像窗口在 L1 里按行主序滑动，而不是按 `l1H/l1W` 的二维栅格。

这不是数据没搬进来，也不是 pad 值不对；但**注意这是两个版本的探针**：最早失败的 run 用的是**非零** `padList={1,1,1,1}` + `leftTopW/H=-1`、fmap 未预 pad（V1/V2Pro 结果一致，见开发轨迹的 stride-3 指纹）；后来的终版探针改成**零 padList + prepad** 才 PASS。不要把叙述读成“零 padList 导致失败”——正好相反，零 padList 是终版通过的那一版；非零 padList 的**成功**形态没有找到。

## 适用场景

- **工程形态**：AscendC kernel 直调；310P 上用 `LoadData3DParamsV2Pro`（或 V1）做卷积/滑窗的硬件 im2col。
- **API 路径**：`SetFmatrix(l1H, l1W, padList, FMATRIX_LEFT)` + `LoadData3DParamsV2Pro`（`channelSize`/`extConfig`/`filterConfig`）；`Nd2Nz`/`DataCopy` 把 fmap 放进 L1。
- **验证过的平台与 CANN 版本**：Ascend310P3（DAV_2002 / dav-m200）+ CANN 9.0.0。
- **适用粒度**：`operator_family` —— 310P conv/im2col 族；本卡证据来自 7 号 conv2d 的单探针（C1=1、固定 filter 矩阵），不等于全平台结论。
- **路线优先级**：`recommended_fastpath` —— **预 pad 的 fmap + `P=0`** 是已验证配方；非零 `padList` 的成功形态未找到，不能据此否定。
- **明确不适用 / 未验证场景**：`stride>1` 且 `filter>1` 的组合另有负结果（见 `310P im2col stride>1 且 filter>1 静默全零`）；**非零 `padList` + `leftTop=-P` 的成功形态未找到**；dilation>1 的 pad 交互未逐一验证；其它代际未验证。

## 根因

**官方契约**（`LoadData_3D.md` 表 3/表 4/表 5）：`padList = [padding_left, padding_right, padding_top, padding_bottom]` 是 padding 列表，`padValue` 是填充值；“若不想开启 padding，可将 `padList` 设为全 0”。同一条开发轨迹里官方 conv3d_v2 也把 H 向 `padTop/padBottom` 折进 `padList` 交给 fmatrix，**一个 pad 元素都不物化**。因此“`padList` 不合成零边”与官方 API 契约冲突，不能作为本卡的机制结论。

**探针实际发生的事（按版本分开）**：早期探针把 `padList` 设为 `{P,P,P,P}`（`uint8_t padList[4] = {P_,P_,P_,P_}`），配合 `leftTopW/H=-P`、fmap 未预 pad；p=1 时得到“源 flat 步长 = filterW”的 stride-3 错值（max|diff|=3.84e2、bad=2017/2304）。V1 与 V2Pro 在这个参数化下结果一致，说明不是某一条指令的问题。后来终版探针把 `padList` 改成 `{0,0,0,0}` 并预 pad fmap，p=1 才 PASS。因此正确结论是：**“非零 padList + 负起点 + 未预 pad”的成功形态没有找到**；不能反过来说“非零 padList 没跑过”，也不能说“零 padList 导致失败”。

**已验证的替代配方**：把 fmap 预先 pad 成 `[C1][Hp][Wp][16]`，窗口用 `P=0`，L1 的行带/宽度按实际装载范围设置。这样窗口永远在合法范围内，不依赖 `padList/padValue` 的填充行为；prepad 探针与 v5a/v6 精度都验证了这条路线。

## 解决配方

### Before：未 pad 的 fmap + P>0

早期/受控探针用的是**非零** `padList={P,P,P,P}`（终版 prepad 才改成全零 `pad0`）：

```cpp
        uint8_t padList[4] = {static_cast<uint8_t>(P_), static_cast<uint8_t>(P_),
                              static_cast<uint8_t>(P_), static_cast<uint8_t>(P_)};
        // ...
        } else if (mode_ != 0) {
            LoadData3DParamsV1<half> p1;
            for (int32_t i = 0; i < PAD_SIZE_; ++i) { p1.padList[i] = padList[i]; }
            p1.l1H = static_cast<uint16_t>(H_);
            p1.l1W = static_cast<uint16_t>(W_);
            p1.c1Index = 0;
            p1.fetchFilterW = 0;
            p1.fetchFilterH = 0;
            p1.leftTopW = static_cast<int16_t>(-P_);
            p1.leftTopH = static_cast<int16_t>(-P_);
            p1.strideW = static_cast<uint8_t>(S_);
            p1.strideH = static_cast<uint8_t>(S_);
            p1.filterW = static_cast<uint8_t>(kW_);
            p1.filterH = static_cast<uint8_t>(kH_);
            p1.dilationFilterW = static_cast<uint8_t>(D_);
            p1.dilationFilterH = static_cast<uint8_t>(D_);
            p1.jumpStride = 1;
            p1.repeatMode = 0;
            p1.repeatTime = static_cast<uint8_t>(K_ / 16);
            p1.cSize = 0;
            p1.padValue = static_cast<half>(0);
            LoadData(a2, f1v[0], p1);
        } else {
            SetFmatrix(static_cast<uint16_t>(H_), static_cast<uint16_t>(W_),
                       padList, FmatrixMode::FMATRIX_LEFT);
            LoadData3DParamsV2Pro pa = WindowParams();
            pa.channelSize = static_cast<uint16_t>(C1_ * 16);
            pa.extConfig = (static_cast<uint64_t>(mStart_) << 48) |
                           (static_cast<uint64_t>(kStart_) << 32) |
                           (static_cast<uint64_t>(M_) << 16) |
                           static_cast<uint64_t>(K_);
            LoadData(a2, f1v[0], pa);
        }
```

### After：预 pad 的 fmap + P=0

探针侧的预 pad（把 fmap 放进 `[C1][Hp][Wp][16]`）：

```python
def run_case(fmap, C1, H, W, kH, kW, S, D, P, M, mode=0, prepad=False,
             kslice=None, mstart=0, kstart=0):
    K = C1 * kH * kW * 16
    fmap = (1 + (np.arange(C1 * H * W * 16).reshape(C1, H, W, 16)
                 % 1024)).astype(np.float32)
    if prepad and P > 0:
        # hardware does not synthesise the pad: stage the padded fmap in L1
        # (l1H/l1W = padded dims) and run the window with P=0.
        fp = np.zeros((C1, H + 2 * P, W + 2 * P, 16), dtype=np.float32)
        fp[:, P:P + H, P:P + W, :] = fmap
        fmap = fp
        H, W, P = H + 2 * P, W + 2 * P, 0
```

终版 kernel 侧用 `P=0`、`padList={0,0,0,0}`（这个 `pad0` 只在 prepad 版本出现）。注意 `l1H` 不是整图高 `Hp`：主 kernel 每次只把一行带装进 L1，`l1H=tileRows`（`rowsOut+(kH-1)*D_`），`l1W=Wp_`；探针整图装载时才用 `l1H=Hp`：

xNC1 的 plane/gap 装载属于“Nd2Nz 单条 DMA”卡，不在此重复；本卡只看窗口参数：

```cpp
                    SetFmatrix(static_cast<uint16_t>(tileRows),
                               static_cast<uint16_t>(Wp_), pad0,
                               FmatrixMode::FMATRIX_LEFT);
                    LoadData3DParamsV2Pro pa;
                    pa.enTranspose = false;
                    pa.enSmallK = false;
                    pa.filterSizeW = false;
                    pa.filterSizeH = false;
                    pa.fMatrixCtrl = false;
                    pa.channelSize = static_cast<uint16_t>(ciG1_ * 16);
                    pa.extConfig = (static_cast<uint64_t>(kc) << 32) |
                                   (static_cast<uint64_t>(M) << 16) |
                                   static_cast<uint64_t>(kl);
                    pa.filterConfig = (static_cast<uint64_t>(D_) << 40) |
                                      (static_cast<uint64_t>(D_) << 32) |
                                      (static_cast<uint64_t>(kH_) << 24) |
                                      (static_cast<uint64_t>(kW_) << 16) |
                                      0x0101ULL;
                    LoadData(a2, fmapV[0], pa);
```

注意 `filterConfig` 的低 16 位是 `strideH<<8 | strideW`，这里 `0x0101` 即 stride=1；`extConfig` 的 `mStart/kStart` 与 `M/kl` 是窗口的扁平输出位置与 K 宽度。

## 设计决策

- **为什么在 fmap 侧预 pad，而不是在 kernel 内逐 tap 补零**：硬件 im2col 的优势就是一次装载展开整个窗口；逐 tap 补零会把窗口展开退回软件路径，失去硬件 im2col 的意义。预 pad 的一次物化成本远小于逐 tap 地址计算。
- **为什么 `l1W` 用 pad 后宽度、`l1H` 用实际装载行数**：窗口的二维栅格按 `l1W` 回绕；如果用未 pad 的 `W`，窗口越界后会按 `W` 回绕到下一行。主 kernel 的行带装载用 `l1H=tileRows`，不是整图 `Hp`。
- **为什么 `padList` 置零**：预 pad 后窗口永远在合法范围内，`padList` 只是恒等元数据；**这不是因为硬件不支持填充**——非零 `padList` 的成功形态未找到。
- **当前方案路线档位**：`recommended_fastpath`。

## 系统信息

- 目标平台：Ascend310P3（DAV_2002 / dav-m200），CANN 9.0.0；kernel 直调。
- 探针：`op_kernel/conv_std2d_im2col_probe.cpp` + `precision/test_im2col_probe.py`；主 kernel：`op_kernel/conv_standard2d_v5_gemm.cpp`。
- 实现证据：`asc-devkit/impl/basic_api/dav_m200/kernel_operator_mm_impl.h:328-355`（V2Pro A1→L0A）；`include/basic_api/kernel_struct_mm.h:356`（`LoadData3DParamsV2Pro`）；`include/basic_api/kernel_operator_mm_intf.h:426`（`SetFmatrix`）。

## 完整代码

Before/After 的 causal unit 已在上文内联；核心是“fmap 预 pad + `P=0` + `l1W=pad 后宽度`（`l1H` 按实际装载行数）”。探针的期望值函数也按同一约定计算：

```python
def expected_panel(fmap, C1, H, W, kH, kW, S, D, P, M):
    """fmap: [C1][H][W][16] float32 -> A[M][K] float32."""
    Hp, Wp = H + 2 * P, W + 2 * P
    padded = np.zeros((C1, Hp, Wp, 16), dtype=np.float32)
    padded[:, P:P + H, P:P + W, :] = fmap
    kd_h = (kH - 1) * D + 1
    kd_w = (kW - 1) * D + 1
    Hout = (Hp - kd_h) // S + 1
    Wout = (Wp - kd_w) // S + 1
    assert M <= Hout * Wout, (M, Hout * Wout)
    K = C1 * kH * kW * 16
    out = np.zeros((M, K), dtype=np.float32)
    for m in range(M):
        hs = (m // Wout) * S
        ws = (m % Wout) * S
        for c1 in range(C1):
            for kh in range(kH):
                for kw in range(kW):
                    tap = kh * kW + kw
                    base = (c1 * kH * kW + tap) * 16
                    for c0 in range(16):
                        out[m, base + c0] = padded[c1, hs + kh * D,
                                                   ws + kw * D, c0]
    return out
```

## 性能影响

本卡是正确性修复，未单独测量 prepad 的性能代价。定性的同算子内部对比：

- **预 pad + 硬件 im2col**：一次 `Hp*Wp*16` 的物化（host 或 prep kernel），热路径仍是单条硬件 im2col；
- **逐 tap 软件补零**：每个 tap 都要做地址计算/边界判断，窗口展开退回软件路径；
- 参照路线：7 号 conv2d v5/v6 的硬件 im2col；来源平台 310P。

## 预防

- 在 310P 上先用单值探针确认 `padList` 的非零形态是否按官方契约工作；如果走预 pad 配方，就把 fmap 显式 pad 好再进 L1。
- `l1W` 用 pad 后宽度、`l1H` 用本次装载行数（整图 `Hp` 或行带 `tileRows`）；写成原始 `H/W` 会得到“源 flat 步长=filterW”的错值。
- 探针矩阵必须同时测 `p=0` 与 `p=1`；只测 `p=0` 会漏掉这条陷阱。
- 预 pad 的零区要一次分配、一次清零；不要依赖 `AllocTensor` 的初始内容。

## 验证信号

来源：7 号 conv2d v6/v7 战役的同一条开发轨迹（单条轨迹、单次上板；证据等级 `tool_observed`/`artifact_verified`）。实现机制由 asc-devkit 固定提交 `a6a99bcf` 的 impl 源码独立核对。

- 探针矩阵：`filter=3×3/3×1/1×3/2×1`、`p=0` 全部精确 PASS；`p=1` 唯一失败（max|diff|=3.84e2、bad=2017/2304，stride-3 指纹）。该组 p=1 用例使用的是**非零** `padList={1,1,1,1}` + `leftTop=-1`、未预 pad；不能据此断言 `padList` 不具备填充语义，只能说明“非零 padList 的成功形态未找到”。（来源平台：310P；证据等级：tool_observed）
- 改为“预 pad fmap + `P=0` + `l1W=pad 后宽度`（行带 `l1H=tileRows`）”后，prepad 探针全部 PASS；v5a/v6 精度 56/56。（来源平台：310P；证据等级：artifact_verified）
- 主 kernel 的 `SetFmatrix` 与 `LoadData3DParamsV2Pro` 参数在终版代码中逐字使用 `pad0={0,0,0,0}` 与 `filterConfig` 的 `0x0101`（stride=1）。（来源平台：310P；证据等级：tool_observed）

## 失效边界

- **`stride>1` + `filter>1`**：即使预 pad + `P=0`，硬件 im2col 仍全零；本卡只覆盖 `stride=1`（或 filter=1×1）。见 `performance/310p_im2col_stride_gt1_filter_gt1_silent_zero`（负结果卡）。
- **`l1H/l1W` 用错**：`l1W` 用原始 `W` 会回到 flat 回绕的错值；`l1H` 要按本次装载行数（整图 `Hp` 或行带 `tileRows`）设置。
- **非零 `padList` 的成功形态未找到**：官方契约支持 `padList` 填充，但早期探针用非零 `padList={P,P,P,P}` + `leftTop=-P`、未预 pad 时 p=1 失败；终版零 padList + prepad 才 PASS。不要把“非零 padList 失败”推广成“padList 不填充”。
- **预 pad 的零区**：必须由 host/前一个 kernel 显式清零；`AllocTensor` 的初始内容不可信。
- **跨代际**：只验证 310P；其它代际的 im2col pad 语义不同（未验证，推断不可迁移）。
- **未决项**：`dilation>1` 与 pad 的交互未逐一验证；`mStart≠0` 的预 pad 窗口未做独立探针。

## 坏实践

- 用非零 `padList` + 负 `leftTop` 跑未预 pad 的 fmap，失败后归因为“padList 不填充”；实际是非零 `padList` 的成功形态未找到，先用 prepad 配方。
- 只测 `p=0` 就宣布 pad 路径可用。
- 预 pad 时只 pad 行不 pad 列，或 `l1W` 用原始 `W`；两者都会让窗口越界回绕。

## 误诊

- 第一轮看到 `p=1` 的错值，先怀疑 `Nd2Nz` 的源行距/`srcDValue` 错了；实际是窗口越界后在 L1 里按行主序读到了下一行。
- 也曾怀疑 `SetFmatrix` 的 `padList` 顺序（左/上/右/下）写反；控制变量显示 `p=0` 全对、`p=1` 全错。早期失败 run 用的是非零 `padList={P,P,P,P}` + `leftTop=-P`；后来把探针改成零 `padList` + prepad 才 PASS。对照官方文档后确认：不能把失败归因为“硬件不合成零边”，正确结论是“非零 padList 的成功形态未找到”。
