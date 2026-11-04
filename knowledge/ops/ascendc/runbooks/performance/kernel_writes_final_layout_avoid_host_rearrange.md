---
type: Runbook
title: kernel 直写最终布局出口，免 host 逆排与 cast
description: 出口若按 [B,HV,tile,*] 出中间布局再由 host 逆排、contiguous、按 dtype cast，会付大量 GM 往返；把最终布局下推到 kernel 行基址直写，host 只留窄片视图。
tags: [task.optimization, topic.data_movement.layout_transform, topic.performance.analysis, topic.implementation.pipeline]
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/8746f7ced6cef47e3fd7abd64c0eb827e28e2b56/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/data_move/DataCopy_GMAndUB_highdim_split.md
    role: constraint
  - resource: https://gitcode.com/cann/asc-devkit/blob/8746f7ced6cef47e3fd7abd64c0eb827e28e2b56/docs/zh/api/SIMD-API/basic_api/sync_control/intra_core_sync/SetFlag_WaitFlag_ISASI.md
    role: constraint
created_at: "2026-10-28T09:46:50Z"
updated_at: "2026-10-28T09:46:50Z"
platforms: ["310p"]
---

# kernel 直写最终布局出口，免 host 逆排与 cast

## 现象

一个 chunk 内链式小矩阵算子（ChunkIntra 形态）的 kernel 路径在做完结构重写后，e2e 口径仍有一批用例明显落后，且**集中在 fp32 输出**的用例上（相对参照路线可低到 0.3~0.7x 量级）。

host 出口的代码形态（v2 时期，verbatim）：

```cpp
    // ---- 出口: 视图逆排后再按需 cast（bf16 走窄片, 免整 tileTp 白转）----
    const auto dt = v.scalar_type();
    auto w = wW.view({B, HV, MT, 64, 128})
                 .narrow(3, 0, C)
                 .reshape({B, HV, MT * C, 128})
                 .narrow(2, 0, T)
                 .narrow(3, 0, K)
                 .transpose(1, 2)
                 .contiguous();
    auto u = uW.view({B, HV, MT, 64, 64})
                 .narrow(3, 0, C)
                 .reshape({B, HV, MT * C, 64})
                 .narrow(2, 0, T)
                 .narrow(3, 0, V)
                 .transpose(1, 2)
                 .contiguous();
    auto inv = invW.view({B, HV, MT, 64, 64})
                    .narrow(3, 0, C)
                    .reshape({B, HV, MT * C, 64})
                    .narrow(2, 0, T)
                    .narrow(3, 0, C)
                    .transpose(1, 2)
                    .contiguous();
    if (dt == torch::kFloat32) {
        w = w.to(torch::kFloat32);
        u = u.to(torch::kFloat32);
        inv = inv.to(torch::kFloat32);
    } else {
        if (w.scalar_type() != k.scalar_type()) {
            w = w.to(k.options());
            u = u.to(v.options());
            inv = inv.to(k.options());
        }
    }
```

即：kernel 先写 `[B, HV, tileTp, *]` 的中间布局，host 再用 `view/narrow/reshape/transpose/contiguous` 逆排成 `[B,T,HV,*]`，最后按输入 dtype 整体 cast。对 fp32 输出，这一步会读一遍 f16、写一遍 f32 的整张量；三个输出加起来是**数百 MB 级的额外 GM 往返**，且在计时区间内。

## 适用场景

- 工程形态：AscendC kernel + torch extension 直调；kernel 能拿到最终布局的步长参数（HV、T、chunk 宽度）。
- API 路径：host `torch::empty` 直接按最终布局分配；kernel 侧 `DataCopy` 2D 写 + 行基址 lambda；`aclrtlaunch_*` 参数增加 `HVX`、`outF32`。
- 验证过的平台与 CANN 版本：310P（dav-m200 / DAV_2002）+ CANN 9.1.0（实测）。
- 适用粒度：函数级（出口段 + host 出口段）。
- 路线优先级：recommended_fastpath。
- 明确不适用或未验证场景：输出尾维的 padding 列不能保证恒零时不适用（直写会把 pad 列也写出去，只能靠视图窄片遮蔽）；需要非连续/别名校验语义的输出未验证；其他 dtype（f64/int）未验证。

## 根因

出口把“布局重排 + 类型转换”放在 host 侧做，而这两件事都可以在 kernel 写的时候就完成：

1. kernel 本来就知道每个 chunk 的 (b, hv, chunk) 坐标 → 可以直接算出 `[B,T,HV,*]` 的行基址；写中间布局只是为了让 host 逆排更容易。
2. dtype 转换可以“不转换”——按输出契约直接以 f32 写 GM（cube/vector 侧本来就是 f32 累加），省掉 f16→f32 的整张量 cast。

判别方法：

1. 把出口的 `transpose+contiguous+cast` 逐项计时/按流量估算，与 e2e 差距同量级 → 本根因。
2. 看落后用例是否与输出 dtype 强相关（fp32 明显更差、f16 持平）→ cast 流量主导。
3. 改成直写后，若 f16 用例基本不变、fp32 用例明显改善 → 确认。

## 解决配方

host 侧改为“按最终布局分配 + 直写 + 出口只做窄片视图（bf16 一次 cast）”。

before：见“现象”中的出口段。

after（verbatim）：

```cpp
    c10_npu::npuSynchronizeDevice();
    // ---- 出口直写缓冲: 最终 [B,T,HV,*] 布局（免 transpose+contiguous+cast）。
    //      f32 契约 kernel 直写 f32（t2 直拷）; f16 直写 f16;
    //      bf16 写 f16 后仅一次窄 cast（与输入 cast 对称, ref 同样支付）。
    const auto dt = v.scalar_type();
    const bool outF32 = (dt == torch::kFloat32);
    auto outOpt = outF32 ? f32 : f16;
    auto wBuf = torch::empty({B, T, HV, 128}, outOpt);
    auto uBuf = torch::empty({B, T, HV, 64}, outOpt);
    auto invBuf = torch::empty({B, T, HV, C}, outOpt);
    auto scratch = torch::empty({8LL * 524288}, f16);
    const int64_t units = B * HV * MT;
    const uint32_t blockDim = static_cast<uint32_t>(std::min<int64_t>(units, 8));
    uint32_t ret = aclrtlaunch_<generic>_chunk_intra(
        blockDim, stream,
        kkg16b.data_ptr(), kgq16b.data_ptr(), kqT.data_ptr(), vtB.data_ptr(),
        wBuf.data_ptr(), uBuf.data_ptr(), invBuf.data_ptr(),
        scratch.data_ptr(),
        static_cast<int32_t>(units), static_cast<int32_t>(MT),
        static_cast<int32_t>(HV), static_cast<int32_t>(C),
        static_cast<int32_t>(T), outF32 ? 1 : 0,
        static_cast<int32_t>(getenv("<GENERIC>_DBG") ? atoi(getenv("<GENERIC>_DBG")) : 0),
        0);
    TORCH_CHECK(ret == 0, "<generic>_chunk_intra launch failed, error=", ret);
    c10_npu::npuSynchronizeDevice();   // 输出侧同理: torch 读前必须排空 kernel
    // K/V 尾维窄片视图（kernel 写满 128/64,  pad 列 GEMM 恒零）; bf16 一次 cast
    auto w = wBuf.narrow(3, 0, K);
    auto u = uBuf.narrow(3, 0, V);
    auto inv = invBuf;
    if (!outF32 && dt == torch::kBFloat16) {
        w = w.to(k.options());
        u = u.to(v.options());
        inv = inv.to(k.options());
    }
    return std::make_tuple(w, u, inv);
```

kernel 侧：新增 `HVX`、`outF32` 参数，按 dtype 选 `GlobalTensor<half>`/`<float>` 两套出口，并用行基址 lambda 定位（verbatim）：

```cpp
    // 出口直写: w [B,T,HV,128] / u [B,T,HV,64] / inv [B,T,HV,C]（同 dtype,
    // outF32=1 时为 f32 —— 免 host 侧 transpose+contiguous+cast 三座大山）
    GlobalTensor<half> gmOutH, gmUH, gmInvH;
    GlobalTensor<float> gmOutF, gmUF, gmInvF;
    const int64_t bhCnt = units / MT;
    if (outF32) {
        gmOutF.SetGlobalBuffer(reinterpret_cast<__gm__ float*>(wW),
                               bhCnt * T * HVX * K128);
        gmUF.SetGlobalBuffer(reinterpret_cast<__gm__ float*>(uW),
                             bhCnt * T * HVX * T64);
        gmInvF.SetGlobalBuffer(reinterpret_cast<__gm__ float*>(invW),
                               bhCnt * T * HVX * Ceff);
    } else {
        gmOutH.SetGlobalBuffer(reinterpret_cast<__gm__ half*>(wW),
                               bhCnt * T * HVX * K128);
        gmUH.SetGlobalBuffer(reinterpret_cast<__gm__ half*>(uW),
                             bhCnt * T * HVX * T64);
        gmInvH.SetGlobalBuffer(reinterpret_cast<__gm__ half*>(invW),
                               bhCnt * T * HVX * Ceff);
    }
    const int64_t hvStride = HVX;   // 每 token 的头步长（元素）
    auto wRowBase = [&](int64_t bh, int32_t m) __aicore__ -> int64_t {
        const int64_t b = bh / HVX;
        const int64_t hv = bh % HVX;
        return (b * T + static_cast<int64_t>(m) * Ceff) * HVX * K128
               + hv * K128;
    };
    auto uRowBase = [&](int64_t bh, int32_t m) __aicore__ -> int64_t {
        const int64_t b = bh / HVX;
        const int64_t hv = bh % HVX;
        return (b * T + static_cast<int64_t>(m) * Ceff) * HVX * T64
               + hv * T64;
    };
    auto invRowBase = [&](int64_t bh, int32_t m) __aicore__ -> int64_t {
        const int64_t b = bh / HVX;
        const int64_t hv = bh % HVX;
        return (b * T + static_cast<int64_t>(m) * Ceff) * HVX * Ceff
               + hv * Ceff;
    };
```

**必须同时做的配套**：f32 直写的源要经 V 物化 + `V_MTE3` 握手（否则半 tile 形态会读到陈旧内容），见同批“MTE3 直写 GM 前源须经 V 物化并 V_MTE3 握手”卡；以及“只搬每行前 C 列”的出口要补 `srcGap`（见精度类卡）。直写本身与这两条是三个独立根因。

## 设计决策

- **为什么 kernel 写满尾维、host 只做窄片视图**：kernel 的 GEMM 输出宽度就是 tile 宽度（pad 列恒零），直接写满可避免 kernel 里再做变宽写；host 侧 `narrow(3, 0, K/V/C)` 是零拷贝视图，免费。
- **bf16 保留一次 cast**：kernel 恒以 f16 操作数计算，bf16 输出需要一次转换；这与输入侧 bf16→f16 的转换对称，参照路线同样支付，故不强行在 kernel 内做 bf16。
- **f32 直写而不是“Host 端 cast”**：cube 累加本来就是 f32，直写 f32 精度更好（免一次 f16 量化）且省一遍整张量读写。
- 被放弃的候选：让 kernel 直接输出非 padded 的紧凑宽度（`[B,T,HV,K]` 且 K 非 2 的幂）——会破坏 `Nd2Nz`/`DataCopy` 的块宽对齐，收益不抵风险。

## 系统信息

- 平台：Ascend310P3 / dav-m200（8 vector core），CANN 9.1.0。
- 工程形态：CMake + `build.sh` → `lib<generic>_ops.so`；host `host/<generic>_host.cpp`，kernel `kernel/<generic>.cpp`；精度套件 `tests/test_<generic>.py`，e2e 性能脚本 `tests/perf_<generic>.py`。
- 出口三元组：w（K 维）、u（V 维）、inv（chunk 宽度维）；host 对前两者做窄片、inv 原样返回。
- launch 侧：`aclrtlaunch_*` 的 extern 声明与 kernel 签名必须同步加参数（`HVX`、`outF32`），漏改一处会编译失败。

## 完整代码

host 出口段（before/after）与 kernel 的 dtype 双套 GlobalTensor + 三个行基址 lambda 均已 verbatim 内联于“现象”与“解决配方”，构成可复用的直写出口骨架。

## 性能影响

- 同一算子、同一 50 例 e2e 脚本成对比较（310P）：直写出口相对“kernel 写中间布局 + host 逆排/cast”的 v2 路线约 **+4.5%**（同一参照路线，geomean 由 1.69 级升到 1.766 级）。收益集中在 fp32 输出用例；f16 用例基本持平。
- 精度副作用为正：fp32 用例免一次 f16 量化，误差由 ~2.5e-4 量级降到 ~1.8e-4 量级。
- 以上相对值只对“v2 → v2+直写”这一对路线成立，不是通用预期收益。

## 预防

- 出口先问：布局逆排与 dtype 转换能不能在写的时候顺手做掉？若 kernel 已知最终坐标，答案通常是可以。
- 直写落地时必须同时检查三件事：源是否已 V 物化（f32）、2D 写的 `srcGap` 是否等于“源行宽 - 出货宽度”、pad 尾列是否恒零。
- host 侧保留一个“直写关闭”的对照开关（本会话用的是环境变量回退复合路径），便于单变量回归。

## 验证信号

本卡信号来自同一开发会话内的实测（310P 单卡、CANN 9.1.0）。

- 直写版本首轮 smoke 只有 3/7 PASS（半 tile f32 全红），说明直写不是“改完就对”；随后由 V 物化与 `srcGap` 两处独立修复补齐（来源平台：310P；证据等级：tool_observed）。
- 三处修复齐备后：7/7 smoke PASS，f32 用例误差 1.788e-4 / 2.232e-4 / 2.440e-4 量级（各例 gate 为 1e-3）（来源平台：310P；证据等级：tool_observed）。
- 全量精度套件 50/50 PASS（默认分派、无环境变量）（来源平台：310P；证据等级：tool_observed）。
- e2e 报告由脚本直出：直写后相对直写前的同一 50 例口径约 +4.5%（geomean 1.69 → 1.766），且仍高于同脚本的 host-composite 参照路线（1.675 级）（来源平台：310P；证据等级：tool_observed）。
- 直写后 f32 用例误差较旧出口更低（~1.8e-4 vs ~2.5e-4 量级）（来源平台：310P；证据等级：tool_observed）。

## 失效边界

- 尾维 padding 列必须业务恒零；若某项输出在 pad 列上有非零值，`narrow` 视图会把它藏起来（视图层正确）但底层数据“脏”，若调用方自行按更大宽度读取会出错。
- 直写把 `HVX`、`outF32` 等布局参数下推到 kernel：多一个参数就多一个不一致点（host 声明、kernel 签名、launch 实参三处必须同步）。
- 未验证非连续输出需求（如 stride 定制、通道子集）与 f64/int 输出。
- 未验证其他代际平台；按同代 m200 的推断可迁移，未验证。
- 未决项：bf16 输出仍有一次整张量 cast（未尝试 kernel 内直出 bf16）。

## 坏实践

- 把“逆排 + cast”留在 host 当成“反正是视图操作”——`transpose` 后的 `contiguous()` 是真实物化，`to(f32)` 是真实读写。
- 只改 kernel 出口、不改 host 分配布局（会写越界或错位）。
- 以为直写只是“省一次拷贝”，忽略它会引入“源物化”与“源行距”两个新的正确性约束。

## 误诊

- **误诊 1**：把直写后半 tile f32 的失败归因为“直写布局算错”（行基址公式逐项验算后正确）。
- **误诊 2**：把出口残留误差归因为“GEMM 半 tile 零行”——dump 证明 GEMM 结果正确。
