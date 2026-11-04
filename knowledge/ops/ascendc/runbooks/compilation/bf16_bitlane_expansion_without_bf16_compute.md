---
type: Runbook
title: "310P 无 bf16 硬件 — int16 Scatter 位展开"
description: "310P 没有 bf16 运算/转换通路时，把 bf16 输入按『高 16 位即 fp32 位型』整块展开：Duplicate 清零低半字 + 按字节偏移表 Scatter 写入高半字，全程无 bf16 运算，bf16 用例对参考与 golden 双逐位一致。"
tags: [task.migration, topic.compute.elementwise.type_conversion, topic.data_movement.layout_transform]
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/8746f7ced6cef47e3fd7abd64c0eb827e28e2b56/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/type_conversion/Cast.md
    role: constraint
  - resource: https://gitcode.com/cann/asc-devkit/blob/8746f7ced6cef47e3fd7abd64c0eb827e28e2b56/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/scatter_gather/Scatter_ISASI.md
    role: constraint
  - resource: https://gitcode.com/cann/asc-devkit/blob/8746f7ced6cef47e3fd7abd64c0eb827e28e2b56/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/data_padding/Duplicate.md
    role: constraint
created_at: "2026-10-28T09:52:17Z"
updated_at: "2026-10-28T09:52:17Z"
platforms: ["310p"]
---

# 310P 无 bf16 硬件 — int16 Scatter 位展开

## 现象

迁移一个分块门控累加算子到 310P（dav-m200 / DAV_2002）。算子的语义要求"输入 dtype 由调用方给出、输出恒 fp32"，而代表用例里**接近一半是 bf16 输入**——bf16 不是可裁剪的可选项，不能像某些迁移那样"把 bf16 例剔掉"。

310P 上没有可用的 bf16 运算通路：bf16 不能直接参与向量 `Add`，也没有可靠的 bf16↔fp32 转换指令可用（同路线里 fp32→fp16 的 `Cast` 本身也只剩 `CAST_NONE` 一种合法 round mode）。但张量本身必须原样从 GM 读进来——读进 UB 时把 GM 指针按 `int16_t` 视图整块 `DataCopy` 是可以的，只是 UB 里躺着的仍然是 16 位 bf16 位型。

也就是说，问题是：**手里有一块 16 位 bf16 位型、需要在不做任何 bf16 运算的前提下变成 fp32 数值**。

实现走的是"位级展开"：整块 `Duplicate` 先把目标 fp32 缓冲清零（低半字全 0），再用一次 `Scatter` 把每个 bf16 的 16 位写到对应 fp32 元素的高半字位置。最终实测 bf16 用例对 NPU eager 参考与 CPU golden **双逐位一致**（`max abs = 0`），包括一例含 bf16 最小次正规数（9.18e-41 量级）的边界输入。代价是这条路径比同元素量的 fp16 路径慢约 2.46 倍（见「性能影响」）。

## 适用场景

- 工程形态：Kernel 直调 / torch-extension raw-launch，host 侧 `TORCH_LIBRARY` 绑定，kernel 用 `__global__ __aicore__` + `aclrtlaunch_*` 裸启动；也适用于任何"kernel 内需要接收 bf16 输入但设备无 bf16 运算"的 AscendC 算子。
- API 路径：`GlobalTensor<int16_t>` 整块 `DataCopy`（MTE2）→ `LocalTensor::ReinterpretCast<int16_t>` → `Duplicate<int16_t>` → `Scatter<int16_t>`（offsets 为偏移表）；host 侧用 `torch::arange(...)` 生成偏移表并 `npuSynchronizeDevice()` 后传入。
- 验证过的平台与 CANN 版本：Ascend310P3（DAV_2002 / dav_m200）+ CANN 9.1.0，tikcpp `ascendc.cmake` 构建。
- 适用粒度：`platform_wide`（310P 缺 bf16 硬件导致的通用规避手法，不限本算子）。
- 路线优先级：`recommended_fastpath`（在 310P 上这是唯一"无损且不引入额外 kernel"的 bf16 入口路线；性能上不是最优，见「性能影响」）。
- 明确不适用 / 未验证场景：不适用于有原生 bf16 通路的平台（A2/A3/A5 直接用 `Cast`/原生 bf16 运算即可，位展开只会变慢）；未验证在"块元素数超过偏移表长度"的形态下的可扩展性（见「失效边界」）；未验证 `Scatter` 偏移单位在其他 CANN 版本是否仍按字节语义（本卡按字节实测有效）。

## 根因

bf16 的位布局是 fp32 的**前 16 位**：1 位符号 + 8 位指数 + 7 位尾数，正好等于 fp32 的 `[31:16]`；fp32 余下的低 16 位是尾数低位。因此

```
fp32_bits = (uint32)bf16_bits << 16
```

是**精确**的数值映射：指数域完全一致、尾数高位一致、尾数低位补 0，没有任何舍入。bf16 的次正规数（指数域全 0、尾数 7 位）映射到 fp32 后同样是次正规数且精确（bf16 次正规数的步长是 2^-133，fp32 次正规数最小步长 2^-149，前者是后者的 2^16 倍，必然可精确表示）。所以"位展开"与"转换"等价，误差恰好为 0——这是本方案能做到双逐位一致的算术根据。

小端内存下，fp32 元素 i 的字节区间是 `[4i, 4i+3]`，其中 `[4i, 4i+1]` 是低半字、`[4i+2, 4i+3]` 是高半字。把 bf16 的 16 位写到**高半字**，等价于把 bf16 位型左移 16 位：

- 先 `Duplicate(f16v, 0, 2*blk)`：把 `2*blk` 个 int16（= `blk` 个 fp32）全清零，保证低半字为 0；
- 再 `Scatter<int16_t>(f16v, src16, off, 0, blk)`：把第 i 个 bf16 写到字节偏移 `4i+2` 处，正好覆盖元素 i 的高半字。

偏移表由 host 一次生成并缓存：`(torch::arange(N).to(int32) * 4 + 2)`，其中 `N` 覆盖最大块元素数。之所以必须**由 host 生成并通过 GM 传入**、而不是在核内算出来，是因为在这条 310P 路线上"设备内生成偏移表"会挂死（同仓既有经验），只能按"常量表 H2D 落盘 + 整机同步一次"的纪律处理——裸 `aclrtlaunch_*` 启动不受 torch 流事件约束，若不同步，`Scatter` 可能读到还没落盘的常量表。

## 解决配方

kernel 侧（`dtype == bf16` 分支）：整块按 `int16_t` 视图载入 → 整块清零目标 fp32 缓冲 → 按偏移表散射写入高半字 → 之后所有计算都在 fp32 上做。

```cpp
        // ---- dtype 归一 fp32（V 管道）----
        LocalTensor<float> srcF;
        if (dt == GK_DT_F32) {
            srcF = inF;  // 直读，零拷贝
        } else if (dt == GK_DT_F16) {
            Cast<float, half>(fF, inBuf.Get<half>(), RoundMode::CAST_NONE, blk);
            srcF = fF;
        } else {
            // bf16 位型 <<16 == fp32 位型：整块 int16 奇槽散射展开（精确）
            LocalTensor<int16_t> f16v = fF.ReinterpretCast<int16_t>();
            Duplicate(f16v, static_cast<int16_t>(0), 2 * blk);
            Scatter<int16_t>(f16v, inBuf.Get<int16_t>(), off, 0, blk);
            srcF = fF;
        }
```

host 侧（偏移表的生成、缓存与整机同步）：

```cpp
    // bf16 奇槽偏移表（4i+2，字节单位 u32，项数覆盖最大块）：
    // host 常量一次生成缓存复用；H2D 落盘后整机同步一次
    // （裸 kernel 启动不受 torch 流事件约束，竞输时 Scatter 读到未初始化表）
    static torch::Tensor offTab;
    void* offPtr = nullptr;
    if (dt == 2) {
        if (!offTab.defined()) {
            auto idx = torch::arange(64 * 64, torch::kInt32);
            offTab = (idx * 4 + 2).to(gc.device());
            c10_npu::npuSynchronizeDevice();
        }
        offPtr = offTab.data_ptr();
    }
```

kernel 侧读表（懒加载，只在 bf16 分支执行一次，随后 `MTE2_V` 同步）：

```cpp
    // bf16: 偏移表一次性 MTE2 载入并同步（host 常量表；blk·4B 恒 32B 倍数）
    if (dt == GK_DT_BF16) {
        GlobalTensor<uint32_t> gmOff;
        gmOff.SetGlobalBuffer(reinterpret_cast<__gm__ uint32_t*>(offTab), blk);
        DataCopy(off, gmOff, blk);
        SetFlag<HardEvent::MTE2_V>(evA);
        WaitFlag<HardEvent::MTE2_V>(evA);
    }
```

端口条件（缺一不可）：目标 fp32 缓冲的容量 ≥ `blk` 个 float；偏移表项数 ≥ `blk`；`blk` 个 fp32 的字节数（`4·blk`）是 32B 的整数倍时才能整块 `DataCopy`（否则要么扩表分片，要么改走 `DataCopyPad` 并自行处理尾部）。

## 设计决策

- **为什么不用 `Cast`**：310P 没有 bf16↔fp32 的可用转换通路，强行写 `Cast<float, bfloat16_t>` 在该平台不会得到可用的硬件指令；位展开用的是纯整数/向量指令，与 bf16 支持无关。
- **为什么选 `Scatter` 而不是逐元素写**：`Scatter` 一次处理整块（`blk` 个元素），保持"热路径零标量逐元素"的纪律；`Duplicate` + `Scatter` 正好与同仓既有的 bf16↔fp16/fp32 平铺转换 kernel 用的"奇槽展开"同构，属于对既有实证模式的复用而不是新发明。
- **为什么偏移表放 host**：核内生成偏移表在本平台会挂死；且常量表只需一次 H2D，缓存成 `static torch::Tensor` 可在多次调用间复用，代价是一次 `npuSynchronizeDevice()`。
- **为什么必须整机同步而不是只靠流序**：kernel 是 `aclrtlaunch_*` 裸启动，不进入 torch 的流事件依赖链；H2D 拷贝完成后若只做流内同步，裸 kernel 仍可能先于拷贝读到表。这是"裸启动不受流序约束"在本方案里的直接落点。
- **被放弃的写法（有 diff 证据）**：最初对 fp16 分支写成了"手算基址 + 统一用 int16 目的类型"——

  ```cpp
        } else {
            DataCopy(inBuf.Get<int16_t>(), (dt == DT_F16)
                    ? reinterpret_cast<__gm__ int16_t*>(gmH.GetPhyAddr() + base)
                    : gm16[base], blk);
        }
  ```

  （该片段是当时源码的原样形态；dtype 常量此时尚未加前缀，故写作 `DT_F16`，终版为 `GK_DT_F16`。）

  问题是 `GlobalTensor` 本身已经携带基址，`GetPhyAddr() + base` 是重复加偏移，且把一个 `half` 视图强转成 `int16_t*` 绕过了类型检查；自我复核后改成按 dtype 各自用 typed 视图（见「完整代码」中的载入段落）。这条"混合类型 + 手算地址"的捷径没有进入编译，属于被自查拦下的坏实践。
- 路线档次：`recommended_fastpath`（正确性优先、零额外 kernel；性能上比 fp16 路径慢，若追求吞吐可按「失效边界」的未决项另做优化）。

## 系统信息

- 平台：Ascend310P3（dav-m200，`__NPU_ARCH__` 2002），CANN 9.1.0（`/usr/local/Ascend/cann-9.1.0/set_env.sh`）。
- 构建：`bash build.sh` → `cmake -DSOC_VERSION=Ascend310P3 -DASCEND_CANN_PACKAGE_PATH=<cann>`（tikcpp `ascendc_kernel_cmake`），产物 `build/lib<generic>_ops.so`，`nm -D` 可见 `aclrtlaunch_<generic>_310p`。
- 目录布局（算子专属目录形态）：`<op>/kernel/<generic>.cpp`、`<op>/host/<generic>.cpp`、`<op>/tests/test_<generic>.py`、`<op>/perf/`；根级 `build.sh`/`CMakeLists.txt` 注册源文件。
- 本次实际读写的相关文件：`kernel/<generic>.cpp`（kernel）、`host/<generic>.cpp`（host，含偏移表）、`CMakeLists.txt`（注册）、`build.sh`（touch 范围）、`tests/test_<generic>.py`、`tests/_preval_<generic>.py`、`perf/msprof/model.py`、`perf/profiler_supplement.py`。
- UB 预算：输入块 / 归一 fp32 块 / 输出块 / 偏移表各一份，均为块元素数 × 4B（uint32 表同宽），工程内实际占用约 64KB，远低于 240KB。

## 完整代码

### kernel（终版，完整函数）

终版由"首次完整写入 + 两处修订"合成：①fp16 载入分支由"手算地址 + int16 目的"改为按 dtype 的 typed 视图；②dtype 常量加 `GK_` 前缀以避开 tikcpp 宏撞名。其余部分与首次写入逐字一致。

```cpp
// ============================================================================
// 分块门控局部累加（310P, dav-m200, __NPU_ARCH__ 2002）
//
// 语义（参考实现 chunk_size=64 恒定）:
//   g [B,T,H]（log 空间门控）按 64 行块做块内前缀和（reverse=False）或块内
//   后缀和（reverse=True），可选整体 scale；跨块不累加；输出恒 fp32。
//   golden 在 fp32 buf 上：
//     out = blocks.cumsum(dim=2)                        （reverse=False）
//     out = blocks.sum(dim=2,keepdim) - out + blocks    （reverse=True）
//
// 迁移设计（纯向量算子，无 cube，无 GEMM 结构）:
//   工作单元 = (b, chunk)。[B,T,H] 行主序下块内 64 行 × H 列在 GM 天然连续；
//   T%64==0 时块起点恒为 64·H 元素（≥1KB）对齐 → 32B 对齐满足整块搬运。
//   每单元：整块 DataCopy 入 UB → dtype 归一 fp32 → 行进向量扫描
//   （64 步 H 宽 Add，加法结合序与 golden 逐元素一致，前缀路径与 CPU golden
//   逐位一致）→ 可选整块 Muls → 整块 DataCopy 出。
//   reverse 走反向行进链（suffix_i = Σ_{j>=i} g_j），与 golden 的
//   total-prefix+current 代数等价、仅结合序不同（误差 ~ulp 级，量级 ≤44，
//   远低于 1e-3 eager-parity 门）。
//
// dtype 处理（310P 无 bf16 硬件 —— 位级展开规避，全程无 bf16 运算）:
//   fp32: 直读 UB;
//   fp16: Cast<float,half> CAST_NONE（精确升 f32：half→fp32 CAST_NONE 位级精确）;
//   bf16: bf16 位型<<16 == fp32 位型（精确）—— 整块 int16 Scatter 到奇槽
//         展开：Duplicate 偶槽清零 + Scatter 奇槽 4i+2（字节偏移表 host 常量
//         MTE2 载入；设备内生成偏移表会挂死）。
//
// 事件与对齐纪律:
//   无 DataCopyPad —— 全部整块 DataCopy，字节数 64·H·{2,4}B 恒为 32B 倍数
//   （H%8==0 为 host 快路径门），GM 块地址 64·H·elsize 对齐
//   fp16→fp32 只用 RoundMode::CAST_NONE
//   MTE2→V→MTE3 事件对纪律：单缓冲三通道排空（MTE3_MTE2 / MTE3_V / V_MTE2），
//   尾部 WaitFlag 排空悬挂事件 + PipeBarrier<PIPE_ALL> 收尾
//   核数: units = B·(T/64)，用例实证 32..262144，blockDim=min(units,8)；
//   分片为连续段（同批 chunk 相邻 → GM 局部性，段边界天然 64·H 元素对齐）
//   向量化: 热路径零标量逐元素（每单元 64 向量 Add + ≤2 个整块向量 op）
//   UB 预算: inBuf 16KB + fBuf 16KB + outBuf 16KB + offBuf 16KB = 64KB ≪ 240KB
//
// 覆盖 shape 包络（host 门，包络外回退 golden 同款 torch 组合）:
//   chunk_size==64 && T%64==0 && 0<H≤64 && H%8==0 && dtype∈{f32,f16,bf16}
//   && B·(T/64) ≤ INT32_MAX（块偏移核内 int64 计算，无 32 位溢出）
// ============================================================================
#include "kernel_operator.h"

using namespace AscendC;

namespace {

constexpr int32_t ROWS = 64;  // chunk_size（实证恒 64）
constexpr int32_t GK_DT_F32 = 0;
constexpr int32_t GK_DT_F16 = 1;
constexpr int32_t GK_DT_BF16 = 2;

}  // namespace

extern "C" __global__ __aicore__ void generic_scan_310p(
    GM_ADDR gIn, GM_ADDR out, GM_ADDR offTab,
    int32_t B, int32_t T, int32_t H, int32_t chunks, int32_t units,
    int32_t dt, int32_t reverse, int32_t hasScale, float scaleF) {
    const int32_t core = GetBlockIdx();
    const int32_t nCores = GetBlockNum();
    if (core >= nCores) {
        return;
    }
    const int32_t blk = ROWS * H;  // 每单元元素数（f32 计）

    // 分片: 连续段（u → b=u/chunks, c=u%chunks；块内元素偏移 int64 计算）
    const int32_t uPer = (units + nCores - 1) / nCores;
    const int32_t u0 = core * uPer;
    const int32_t u1 = (u0 + uPer < units) ? (u0 + uPer) : units;
    if (u0 >= u1) {
        return;
    }

    TPipe pipe;
    TBuf<TPosition::VECCALC> inBuf, fBuf, outBuf, offBuf;
    pipe.InitBuffer(inBuf, blk * sizeof(float));      // 输入块（16bit 只用前半）
    pipe.InitBuffer(fBuf, blk * sizeof(float));       // 归一 f32 块（f32 直读时不用）
    pipe.InitBuffer(outBuf, blk * sizeof(float));     // 扫描结果（MTE3 源）
    pipe.InitBuffer(offBuf, blk * sizeof(uint32_t));  // bf16 奇槽偏移表（懒用）

    LocalTensor<float> inF = inBuf.Get<float>();
    LocalTensor<float> fF = fBuf.Get<float>();
    LocalTensor<float> oF = outBuf.Get<float>();
    LocalTensor<uint32_t> off = offBuf.Get<uint32_t>();

    const int64_t total = static_cast<int64_t>(B) * T * H;
    GlobalTensor<float> gmF;
    GlobalTensor<half> gmH;
    GlobalTensor<int16_t> gm16;
    GlobalTensor<float> gmOut;
    if (dt == GK_DT_F32) {
        gmF.SetGlobalBuffer(reinterpret_cast<__gm__ float*>(gIn), total);
    } else if (dt == GK_DT_F16) {
        gmH.SetGlobalBuffer(reinterpret_cast<__gm__ half*>(gIn), total);
    } else {
        gm16.SetGlobalBuffer(reinterpret_cast<__gm__ int16_t*>(gIn), total);
    }
    gmOut.SetGlobalBuffer(reinterpret_cast<__gm__ float*>(out), total);

    event_t evA = static_cast<event_t>(0);  // MTE2_V
    event_t evB = static_cast<event_t>(0);  // V_MTE3
    event_t evC = static_cast<event_t>(0);  // MTE3_MTE2
    event_t evD = static_cast<event_t>(0);  // MTE3_V
    event_t evE = static_cast<event_t>(0);  // V_MTE2

    // bf16: 偏移表一次性 MTE2 载入并同步（host 常量表；blk·4B 恒 32B 倍数）
    if (dt == GK_DT_BF16) {
        GlobalTensor<uint32_t> gmOff;
        gmOff.SetGlobalBuffer(reinterpret_cast<__gm__ uint32_t*>(offTab), blk);
        DataCopy(off, gmOff, blk);
        SetFlag<HardEvent::MTE2_V>(evA);
        WaitFlag<HardEvent::MTE2_V>(evA);
    }

    for (int32_t u = u0; u < u1; ++u) {
        const int32_t b = u / chunks;
        const int32_t c = u - b * chunks;
        const int64_t base =
            (static_cast<int64_t>(b) * T + static_cast<int64_t>(c) * ROWS) * H;
        if (u > u0) {
            // 上单元 MTE3 排空后才能覆写 UB（三通道纪律：
            // MTE2 写 inBuf / V 写 fBuf·outBuf / V 读 inBuf·fBuf 三类复用
            // 各需一个等待，缺任一曾致跨块竞态）
            WaitFlag<HardEvent::MTE3_MTE2>(evC);
            WaitFlag<HardEvent::MTE3_V>(evD);
            WaitFlag<HardEvent::V_MTE2>(evE);
        }

        // ---- 载入整块 [64,H]（GM 连续 64·H 元素，字节数 32B 倍数）----
        if (dt == GK_DT_F32) {
            DataCopy(inF, gmF[base], blk);
        } else if (dt == GK_DT_F16) {
            DataCopy(inBuf.Get<half>(), gmH[base], blk);
        } else {
            DataCopy(inBuf.Get<int16_t>(), gm16[base], blk);
        }
        SetFlag<HardEvent::MTE2_V>(evA);
        WaitFlag<HardEvent::MTE2_V>(evA);

        // ---- dtype 归一 fp32（V 管道）----
        LocalTensor<float> srcF;
        if (dt == GK_DT_F32) {
            srcF = inF;  // 直读，零拷贝
        } else if (dt == GK_DT_F16) {
            Cast<float, half>(fF, inBuf.Get<half>(), RoundMode::CAST_NONE, blk);
            srcF = fF;
        } else {
            // bf16 位型 <<16 == fp32 位型：整块 int16 奇槽散射展开（精确）
            LocalTensor<int16_t> f16v = fF.ReinterpretCast<int16_t>();
            Duplicate(f16v, static_cast<int16_t>(0), 2 * blk);
            Scatter<int16_t>(f16v, inBuf.Get<int16_t>(), off, 0, blk);
            srcF = fF;
        }

        // ---- 行进向量扫描（每行一个 H 宽向量 op，依赖链 64 深与 golden
        //      逐元素同序；reverse 反向行进 = 块内后缀和）----
        if (reverse == 0) {
            Adds(oF, srcF, 0.0f, H);  // out[0] = g[0]
            for (int32_t i = 1; i < ROWS; ++i) {
                Add(oF[i * H], oF[(i - 1) * H], srcF[i * H], H);
            }
        } else {
            Adds(oF[(ROWS - 1) * H], srcF[(ROWS - 1) * H], 0.0f, H);
            for (int32_t i = ROWS - 2; i >= 0; --i) {
                Add(oF[i * H], oF[(i + 1) * H], srcF[i * H], H);
            }
        }

        if (hasScale != 0) {
            Muls(oF, oF, scaleF, blk);  // 整块缩放（golden 同为逐元素 fp32 乘）
        }

        SetFlag<HardEvent::V_MTE3>(evB);
        WaitFlag<HardEvent::V_MTE3>(evB);

        // ---- 整块写出 fp32（64·H·4B 恒 32B 倍数，32B 对齐写）----
        DataCopy(gmOut[base], oF, blk);

        SetFlag<HardEvent::MTE3_MTE2>(evC);
        SetFlag<HardEvent::MTE3_V>(evD);
        SetFlag<HardEvent::V_MTE2>(evE);
    }

    // 排空尾部事件（末单元 SetFlag 无后续 WaitFlag，悬挂退出会污染设备事件态）
    WaitFlag<HardEvent::MTE3_MTE2>(evC);
    WaitFlag<HardEvent::MTE3_V>(evD);
    WaitFlag<HardEvent::V_MTE2>(evE);
    PipeBarrier<PIPE_ALL>();
}
```

### host（终版，完整文件）

```cpp
// ============================================================================
// host 绑定 —— torch.ops.npu.block_gated_scan
//
// 与参考实现数学对齐:
//   g [B,T,H] → 按 chunk_size=64 块内前缀/后缀和（fp32 累加）→ 可选 scale
//   → 输出 [B,T,H] 恒 fp32（golden buf 即 fp32，无回铸）
//
// 双路径（fail-loud 门 + golden 同款回退）:
//   快路径（kernel）: 连续 NPU 张量 && chunk_size==64 && T%64==0
//     && 0<H≤64 && H%8==0 && dtype∈{f32,f16,bf16} && units≤INT32_MAX
//     —— 覆盖全部 benchmark 用例（实证: T 恒 64 倍数、H∈{8,16,32,64}）
//   回退路径（torch 组合，与参考逐步同式 → 数值恒等）: 尾块（T%64≠0）、
//     异 chunk_size、H 越界、CPU 张量等包络外 shape —— 保正确性优先
//
// bf16 处理（310P 无 bf16 硬件，业务必须场景）:
//   输入是调用方交付的 bf16 张量，不可裁剪 —— kernel 内位级 <<16 精确展开
//   为 fp32（无任何 bf16 运算），偏移表 host 常量缓存
//   （常量表 H2D 落盘后整机同步一次）
// ============================================================================
#include <torch/extension.h>
#include <torch_npu/csrc/core/npu/NPUStream.h>
#include "acl/acl_base.h"
#include "acl/acl_rt.h"
#include <algorithm>
#include <cstdint>

extern "C" uint32_t aclrtlaunch_generic_scan_310p(
    uint32_t blockDim, void* stream, void* gIn, void* out, void* offTab,
    int32_t B, int32_t T, int32_t H, int32_t chunks, int32_t units,
    int32_t dt, int32_t reverse, int32_t hasScale, float scaleF);

namespace {

// golden 同款组合回退（包络外 shape）—— 与参考 forward 逐步同式，
// 数值恒等；纯 torch 路径（无裸 launch，无额外流序要求）
torch::Tensor block_gated_scan_fallback(const torch::Tensor& g,
                                        int64_t chunk_size, bool reverse,
                                        c10::optional<double> scale) {
    const int64_t B = g.size(0);
    const int64_t T = g.size(1);
    const int64_t H = g.size(2);
    const int64_t chunks = (chunk_size > 0) ? (T + chunk_size - 1) / chunk_size
                                            : 0;
    const int64_t padded = chunks * chunk_size;
    auto buf = torch::zeros({B, padded, H}, g.options().dtype(torch::kFloat32));
    if (T > 0) {
        buf.narrow(1, 0, T).copy_(g.to(torch::kFloat32));
    }
    auto blocks = buf.view({B, chunks, chunk_size, H});
    auto out = blocks.cumsum(2);
    if (reverse) {
        // 块内后缀和：总和 - 前缀和 + 当前元素（golden 同式）
        out = blocks.sum(2, /*keepdim=*/true) - out + blocks;
    }
    if (scale.has_value()) {
        out = out * (*scale);
    }
    return out.reshape({B, padded, H}).narrow(1, 0, T);
}

}  // namespace

torch::Tensor block_gated_scan_npu(const torch::Tensor& g,
                                   int64_t chunk_size, bool reverse,
                                   c10::optional<double> scale) {
    TORCH_CHECK(g.dim() == 3, "g must be [B, T, H], got ", g.dim(), "D");

    // 非连续输入先归一（NPU 上 strided 拷贝无流序 —— 复制发生后、裸 launch
    // 前须整机同步；benchmark 输入本就连续，此路径罕见）
    torch::Tensor gc = g;
    bool copied = false;
    if (!gc.is_contiguous()) {
        gc = gc.contiguous();
        copied = true;
    }
    if (gc.device().type() != c10::DeviceType::PrivateUse1) {
        return block_gated_scan_fallback(gc, chunk_size, reverse, scale);
    }

    const int64_t B = gc.size(0);
    const int64_t T = gc.size(1);
    const int64_t H = gc.size(2);
    const int64_t chunks = (T > 0 && chunk_size > 0) ? T / chunk_size : 0;
    const bool fast =
        gc.numel() > 0 && chunk_size == 64 && T % 64 == 0 && H > 0 &&
        H <= 64 && H % 8 == 0 && B <= INT32_MAX && T <= INT32_MAX &&
        B * chunks <= INT32_MAX &&
        (gc.scalar_type() == torch::kFloat32 ||
         gc.scalar_type() == torch::kFloat16 ||
         gc.scalar_type() == torch::kBFloat16);
    if (!fast) {
        return block_gated_scan_fallback(gc, chunk_size, reverse, scale);
    }
    if (copied) {
        c10_npu::npuSynchronizeDevice();
    }

    int32_t dt = 0;
    if (gc.scalar_type() == torch::kFloat16) {
        dt = 1;
    } else if (gc.scalar_type() == torch::kBFloat16) {
        dt = 2;
    }

    // bf16 奇槽偏移表（4i+2，字节单位 u32，项数覆盖最大块）：
    // host 常量一次生成缓存复用；H2D 落盘后整机同步一次
    // （裸 kernel 启动不受 torch 流事件约束，竞输时 Scatter 读到未初始化表）
    static torch::Tensor offTab;
    void* offPtr = nullptr;
    if (dt == 2) {
        if (!offTab.defined()) {
            auto idx = torch::arange(64 * 64, torch::kInt32);
            offTab = (idx * 4 + 2).to(gc.device());
            c10_npu::npuSynchronizeDevice();
        }
        offPtr = offTab.data_ptr();
    }

    auto out = torch::empty({B, T, H}, gc.options().dtype(torch::kFloat32));
    const int64_t units = B * chunks;
    const uint32_t blockDim =
        static_cast<uint32_t>(std::min<int64_t>(units, 8));
    const float scaleF =
        scale.has_value() ? static_cast<float>(*scale) : 0.0f;
    const uint32_t ret = aclrtlaunch_generic_scan_310p(
        blockDim, c10_npu::getCurrentNPUStream().stream(), gc.data_ptr(),
        out.data_ptr(), offPtr, static_cast<int32_t>(B), static_cast<int32_t>(T),
        static_cast<int32_t>(H), static_cast<int32_t>(chunks),
        static_cast<int32_t>(units), dt, reverse ? 1 : 0,
        scale.has_value() ? 1 : 0, scaleF);
    TORCH_CHECK(ret == 0, "generic_scan_310p launch failed, error=", ret);
    return out;
}

TORCH_LIBRARY_FRAGMENT(npu, m) {
    m.def("block_gated_scan(Tensor g, int chunk_size, bool reverse, "
          "float? scale) -> Tensor");
}

TORCH_LIBRARY_IMPL(npu, PrivateUse1, m) {
    m.impl("block_gated_scan", &block_gated_scan_npu);
}
```

## 性能影响

- 同一算子、同一平台、同一元素量级的两个用例对比：**bf16（位展开）路径的 kernel 时长约为 fp16 路径的 2.46 倍**（参照路线：同算子的 fp16 直 `Cast` 路线，来源平台：310P）。差异来自 `Duplicate`（`2·blk` 个 int16）+ `Scatter`（`blk` 个元素）这一对整块操作，以及 `Scatter` 的散射寻址效率。
- pipe 画像也印证了这一点：bf16 例 `vec_ratio≈0.90`、`scalar_ratio≈0.16`，属于纯 vector-bound；而 fp16/fp32 大例是 `vec≈0.48`、`scalar≈0.80`（串行链延迟主导）。也就是说 bf16 路径把时间花在展开本身，不是花在扫描上。
- 对参考实现（同算子的 torch eager 组合）的加速幅度也体现出这条开销：与**同元素量级的 fp16 例**配对比较时，bf16 例相对参考实现的加速幅度约为 fp16 例的 0.2 倍；而最小的 bf16 例因为参考侧本身极轻（参考耗时被 host 开销主导），相对加速幅度反而更高。以上为同算子内部两条 dtype 路线的成对对比（来源平台：310P；单次采集，不构成通用预期收益）。
- 未验证精度影响：本卡路径与 fp32 路径共用后续扫描逻辑，bf16 例的精度已实测为双逐位一致（见「验证信号」），因此性能取舍不涉及精度退化。

## 预防

1. 迁移前先确认目标平台有没有 bf16 运算通路；没有就用"位展开"，不要在 kernel 里写 bf16 算术（会退化成不可用或极慢的模拟）。
2. 偏移表这类常量表一律 host 生成 + 缓存 + `npuSynchronizeDevice()`，并且**放在裸 kernel 启动之前**；不要"每次调用都重新算表"或"在核内生成"。
3. 偏移表的元素数要按"最大块元素数"给足（本例按 `64×64` 给），并在 host 侧把"块元素数 ≤ 表长"作为快路径门之一，否则 `Scatter` 会越界读表。
4. 用 `Duplicate` 清零时**长度要按目标缓冲的 int16 元素数（`2·blk`）给**，不是 `blk`——写成 `blk` 只会清掉前半块的低/高半字，后半块留下脏数据（这类错误在小用例上常常仍然"看起来对"，务必用非零初值的缓冲验证）。
5. 混合 dtype 分支时，`DataCopy` 的目的/源都要用与该 dtype 匹配的 typed 视图（`Get<half>()` / `Get<int16_t>()` / `GlobalTensor<T>[offset]`），不要用手算 `GetPhyAddr() + offset` 再强转指针。

## 验证信号

来源说明：本卡来自一次 310P 迁移会话中对"bf16 输入不可裁剪"场景的实现与验证。精度值取自该会话的正式精度测试脚本与其落盘的精度报告；pipe 画像取自同会话的 `torch_npu.profiler` 补充采集（`kernel_details.csv`）；性能倍数为同一会话内两 dtype 用例的成对相对比较。

- bf16 精度：全部 bf16 用例对 NPU eager 参考与 CPU golden **双逐位一致**（`max abs(ours-ref)=0`、`max abs(ours-gold)=0`）（来源平台：310P；证据等级：artifact_verified——取自精度报告 JSON/MD）。
- 边界值：含 bf16 最小次正规数量级（9.18e-41）与 0 混合的合成用例通过，`abs(o-r)=0.000e+00`、无 NaN/Inf（来源平台：310P；证据等级：tool_observed）。
- 窄行反序：行宽 8 的 bf16 反序用例（H8 合成例）通过，`abs(o-r)=0.000e+00`、双逐位一致（来源平台：310P；证据等级：tool_observed）。
- 全量回归：含 bf16 在内的 66/66 精度用例 PASS、0 FAIL，报告 JSON `total=66 pass=66`（来源平台：310P；证据等级：tool_observed）。
- 设备侧取证：bf16 大例在 `kernel_details.csv` 中 `vec_ratio≈0.90`、`scalar_ratio≈0.16`、`Block Num=8`，说明展开走的是 vector 单元且多核正常铺开（来源平台：310P；证据等级：tool_observed）。
- 相对开销：同元素量级的 bf16 例 kernel 时长约为 fp16 例的 2.46 倍（来源平台：310P；证据等级：tool_observed）。

## 失效边界

- **块元素数上限 = 偏移表项数**：偏移表只有固定项（本例 `64×64`），块元素数超过它就必须扩表或把块再切小，否则 `Scatter` 越界读表。
- `ROWS=64`、`chunk_size==64`、`H∈{8,16,32,64}` 这些常量与快路径门是**本源算子的用例包络（示例）**，不是通用约束；移植时按"块字节数 + 偏移表长度"重新推导。
- 只在"整块连续、字节数是 32B 倍数"时成立（本例块字节数恒为 32B 的倍数）。若块尾不满，必须自己处理尾部（`DataCopyPad` 或分块），本卡未覆盖。
- `Scatter` 的 offsets 单位按**字节**使用：本工程实测按字节寻址有效（bf16 用例逐位一致可反向佐证）。换 CANN 版本/换 API 家族时，**先做一次单块小案例验证偏移单位**（若实际按元素寻址，`4i+2` 就会错位一倍）。
- 未验证：A2/A3/A5 等有 bf16 原生通路的平台不需要本方案（推断可迁移但无收益，未验证）；也未验证 bf16 输入为非连续（strided）时的正确性——host 会把非连续输入先 `contiguous()` 并整机同步，但这条路径本身在本次会话中没有专门用例。
- 未验证：偏移表用 `uint32` 承载"字节偏移"在表长更大时（> 2^16 项）是否需要换类型；本例表长 4096 未触及。
- 未决项：
  1. bf16 展开路径比 fp16 慢 2.46 倍，优化方向（用 `Gather` 对偶展开、对齐搬运 + 整数位操作、或先 `Cast` 到 fp16 再补位）**均未尝试**；下一步应先做单算子 profiling 确认 `Scatter` 与 `Duplicate` 各自占比，再决定是否值得换。
  2. 偏移表长度与块长的耦合关系没有做成 host 侧自动校验（当前靠快路径门 `H ≤ 64` 隐式保证），换个块长参数时容易踩边界。

## 坏实践

- 在 310P 上直接写 bf16 算术或 `Cast<float, bfloat16_t>`，期望编译器"自动降级"——不会，且报错/表现不直观。
- 偏移表在核内生成（会挂死）或每次调用重新 `arange` 一遍（多一次 H2D + 同步）。
- `Duplicate` 长度只给 `blk`（少了一半），或用"未清零的缓冲"验证——残留脏数据在数值分布恰好为 0 的用例上不会暴露。
- 用"手算基址 + 统一 int16 目的类型"处理混合 dtype 载入（本会话中被自查拦下的写法），可读性差、绕过类型检查，且 `GlobalTensor` 已带偏移时必错。
- 认为"fp16 与 bf16 都是 16 位，所以展开方式可以互换"——fp16 是 1+5+10 的独立编码，**不能**用移位展开，必须走 `Cast`（`CAST_NONE` 在 310P 上对 half→fp32 是位级精确的）。

## 误诊

- 误诊一："310P 不支持 bf16，所以这个算子的 bf16 用例只能跳过"——bf16 位型可以原样搬运和展开，精度完全是 0 误差。
- 误诊二："bf16 例比 fp16 例慢是因为 bf16 精度低/计算慢"——慢的是 `Duplicate`+`Scatter` 这对展开操作（vec-bound），不是后续扫描。
- 误诊三："`Scatter` 的 offsets 是元素下标，所以要写 `2i+1`"——本工程按字节偏移 `4i+2` 实测有效；这类"单位假设"必须用小案例实测，不能靠猜。
