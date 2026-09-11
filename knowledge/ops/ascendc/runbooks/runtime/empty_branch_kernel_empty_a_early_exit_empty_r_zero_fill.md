---
type: "Runbook"
title: 空batch归约kernel：bias零填充+全核早退配方
description: reduction 算子 B==0 且 has_bias 时两路 bias 输出需零填充 6H 的完整 AscendC kernel 配方：Duplicate(0) 常量驻留 + 6 段 strided DataCopyPad + V_MTE3 单 crossing 同步；H==0 或 B==0 且无 bias 时全核早退。
tags: [task.implementation, topic.compute.reduction, topic.data_movement.data_copy, topic.implementation.synchronization, topic.tiling, topic.implementation.pipeline]
status: stable
sources: []
created_at: '2026-09-09T11:49:41Z'
updated_at: '2026-09-09T11:49:41Z'
platforms: ["950"]
cann_versions: ["9.0.0-beta.2"]
---
# 空batch归约kernel：bias零填充+全核早退配方


## 现象

在按 ACLNN 算子仓流程开发 GRU Cell 反向融合算子（对标 torch 的 thnn fused gru cell backward，多分支 tiling 模板架构：base 逐元素主链 / group 跨核规约 / empty 空张量短路）时，空张量分支（tilingKey=2）的 kernel 文件起先只是一个可编译的桩：`Init` 把全部 8 个参数 `(void)` 转换、`Process` 直接 `return`。对"输出全为空张量"的退化（EMPTY_A：H==0，或 B==0 且 has_bias=false）这个桩恰好就是最终语义；但对 **EMPTY_R（B==0 且 has_bias=true）** 它是错的——此时两路 bias 输出 `grad_input_bias`/`grad_hidden_bias` 形状为 `(3H,)` 并非空张量，语义上等于"对空 batch 求和"，每元素必须写 **0**，而桩完全不写，ST 用例以 poison 初化输出后与期望零比对失败（该红基线由测试先行阶段刻意保留，测试驱动注释原文载明："Branch-2 红基线阶段（本分支数值用例 EMPTY_R 部分失败、EMPTY_A 空张量短路通过属桩即最终语义……）退出码 0 属预期"）。

本卡记录这个"没有输入数据、没有浮点计算"的 kernel 怎么写：输入 `grad_hy (0,H)`、`storage (0,5H)` 均为 0 元素，无任何 GM→UB 搬入；输出里门梯度 `(0,3H)`、`grad_hx (0,H)` 为空张量不写，只有两路 bias 共 6H 个 0 要写。实现后该分支 12 条 ST（含 fp16/bf16、H=1/2048/3000 切分边界）全部转绿。

## 适用场景（必填 — 检索前的第一道滤网）

- **工程形态**：ops-registry-invoke 算子仓开发（op_kernel/op_host 分离、tilingKey 多模板分发、aclnn ST 验证）；空张量/退化 shape 合法输入的 reduction 类算子。
- **API 路径**：`AscendC::TBuf<TPosition::VECOUT>` + `TPipe::InitBuffer`；`GetTPipePtr()->FetchEventID(AscendC::HardEvent::V_MTE3)` + `SetFlag/WaitFlag`；`AscendC::DataCopyPad`（UB→GM 三参重载，不带 `DataCopyPadExtParams`）；`__simd_vf__` + `asc_vf_call` 寄存器级 VF（`AscendC::Reg::Duplicate/UpdateMask/StoreAlign`）。
- **验证过的平台与 CANN 版本**：Ascend 950 系列（arch35，AIV）+ CANN 9.0.0-beta.2（与 frontmatter `platforms` 一致；真机具体型号 PR/DT 未在本轨迹区分）。
- **适用粒度（transfer_scope）**：`operator_family`——reduction 语义算子（输出含沿 batch 维求和的 bias 分量）的空张量退化分支。
- **路线优先级**：`recommended_fastpath`（对"空 batch 求和 = 0"语义的退化分支，这是最小正确实现：一条 VF + 单 buffer + 一对事件同步）。
- **明确不适用 / 未验证场景**：B>0 的主计算链（需要 CopyIn/五链计算）；跨核规约分支（group，需 SyncAll + workspace 中转）；reducer 不是 sum 的空集语义（min/max 等空集值不同）；H > 3000 尤其 H > 6×16384 的多 chunk 大 H 未实测；非 950 平台的寄存器宽度（kVlBytes）未验证。

## 根因

空 batch 求和是数学恒等而非浮点运算：Σ_{b=0}^{B-1} x_b 在 B==0 时 ≡ 0（sum 单位元），因此 EMPTY_R 的全部计算就是"把常量 0 写满两路 bias 输出"。

由此推出整条实现链（每步给算式）：

1. **无精度损失路径**：0 在 fp32/fp16/bf16 中均精确可表示（编码分别为 0x00000000/0x0000/0x0000，无尾数舍入），故 golden 语义"fp32 空和 0 → 收窄 CAST → D_T"与"直接 D_T 域 Duplicate(0)"位级一致 → 不需要 fp32 中间 buffer、不需要 Cast、不需要 tmpBuf（设计口径 has_post_elewise=false、has_post_reduce_input=false，编译期常量折叠）。
2. **无 CopyIn**：B==0 ⇒ grad_hy/storage 均 0 元素，零值来自 Duplicate 常量而非 GM 读入。
3. **写量**：2 路 bias × 3 段 [r|z|n] × H = 6H 个 0；GM 写字节数 = 6H × sizeof(D_T)。常量与段偏移 aOff 无关 → **Duplicate 一次**填 aUbFactor 个 0 驻留 postBuf，之后每 chunk 6 段 CopyOut 共读同一 buffer（写一次读多次）。
4. **同步只需一对 V_MTE3**：持有法则 trace——唯一跨 pipe 访问是 V 写 postBuf → MTE3 读 postBuf（RAW crossing）；循环内 postBuf 无任何 V 重写 → 无跨迭代 WAR；MTE3 读与读同 pipe 硬件有序 → 循环内无需再同步。所以全 kernel 只需一对 `SetFlag/WaitFlag(V_MTE3)`，位于 Duplicate 之后、首次 CopyOut 之前；无 MTE2_V（无 CopyIn）、无 SyncAll（无跨核）。
5. **buffer 容量按最大 dtype 预留**：postBufSize = CeilAlign(Max(aUbFactor × maxDtypeSize, blockSize), blockSize)，maxDtypeSize = Max(sizeof(D_T), 4) = 4 → b16 时容量按 4B/元素分配、Duplicate 实写 2B/元素（例：fp16 aUbFactor=8 → 容量 32B、实写 16B），CopyOut 只读 aLen × sizeof(D_T) 字节，容量冗余无害。
6. **尾块字节精确**：aUbFactor 经 4 约束钳到 ≤ aTotal=H，尾 chunk aLen = aEnd − aOff < aUbFactor；`DataCopyPad` UB→GM 方向 `blockLen = aLen × sizeof(D_T)` 为有效字节、不要求 32B 对齐（实测 H=1 fp32 → blockLen=4B、fp16 H=8 → 16B 均正确）；`blockCount=1` 时 srcStride/dstStride 是块间 gap、不参与，置 0 即可。
7. **EMPTY_A 全核早退**：host 侧对"全空"退化置 `usedCoreNum=0` 但 `SetBlockDim(1)`（**严禁 SetBlockDim(0)**，blockDim 必须 ≥1），kernel 入口 `blockIdx >= usedCoreNum_`（0）恒真 → 全核 return，零计算零 IO；5 路输出 numel 全为 0（H==0 时 3H=0，bias 输出也是 (0,) 空张量，判定顺序 H==0 优先于 B==0）。

## 解决配方

按"根因"第 1–7 条落成三个函数（完整代码见下）：

- `Init`：载入 Empty TilingData；**只绑定**实际要写的两路 bias 输出 GM；`postBufSize > 0`（仅 EMPTY_R）时分配 VECOUT postBuf、经 `GetPhyAddr()` 取 `__ubuf__` 裸指针、`FetchEventID(V_MTE3)` 取事件号（禁止硬编码）；空输入/空输出参数 `(void)` 转换不绑定。
- `Process`：`blockIdx >= usedCoreNum_` 早退（EMPTY_A）；大小核映射出 `[aStart, aEnd)`（大核 aStart = blockIdx × aBigCoreLoopCnt × aUbFactor，小核再加大核总量偏移）；`aEnd = min(aEnd, aTotal_)` 防越界；`DuplicateEmptyROutputVf` 一次；`SetFlag/WaitFlag(V_MTE3)` 一对；chunk 循环调 `CopyOut`。
- `CopyOut`：单 `DataCopyExtParams`（`{}` 零初始化 + 显式置 `blockCount=1 / blockLen=aLen×sizeof(D_T) / srcStride=0 / dstStride=0 / rsv=0`），段枚举 s ∈ [0,6)：s<3 写 `gmGradInputBias_[s×hiddenSize + aOff]`，s≥3 写 `gmGradHiddenBias_[(s−3)×hiddenSize + aOff]`（两张独立 (3H,) 张量，段内偏移 = 段序×H + aOff）。

## 设计决策

1. **TPosition 选 VECOUT 而非 VECCALC**：设计表指定 postBuf 用 VECOUT（输出型 buffer：V 写、MTE3 读），但既有 base.h 全用 VECCALC、代码库中无 VECOUT 先例，实现时一度倾向"求稳改 VECCALC"。先用 grep 探测 CANN 头文件 `${ASCEND_HOME_PATH}/x86_64-linux/ascendc/include/basic_api/impl/common_types.h`，确认 `enum class TPosition : uint8_t { …, VECIN, VECOUT, VECCALC, LCM = VECCALC, … }` 中 VECOUT 是合法成员 → 按设计用 VECOUT（编译 + ST 证实）。注：rg 直接搜 CANN 安装目录多次空结果，改 `find … -name "*.h" | xargs grep` 才命中。
2. **InitBuffer 而非设计伪码的 AllocTBuf**：设计文档 §5.1 写 `pipe_->AllocTBuf<TPosition::VECOUT>(size)`，但该 API 在本环境未验证存在；改用代码库既有且被 base.h 验证过的模式——成员声明 `TBuf<TPosition::VECOUT> postBuf_;` + `pipe_->InitBuffer(postBuf_, size)`。TPosition 语义不受分配 API 影响。
3. **Duplicate 走 `__ubuf__` 裸指针**：VF 接口要 `__ubuf__ T*` 而非 LocalTensor，Init 里 `postPtr_ = reinterpret_cast<__ubuf__ D_T*>(postBuf_.Get<D_T>().GetPhyAddr())` 一次取好（base.h 同款），CopyOut 内则用 `postBuf_.Get<D_T>()` 的 LocalTensor 传 DataCopyPad。
4. **DataCopyExtParams 显式全字段置值**：设计伪码未置 `rsv`；实现对齐 base.h 模式用 `{}` 值初始化 + 显式 `rsv = 0`，避免依赖默认值。
5. **Duplicate 填满 aUbFactor、CopyOut 只读 aLen**：尾 chunk 常量 buffer 多填无害（buffer 容量本按 aUbFactor 分配），写 GM 侧按 aLen 字节精确，两件事解耦。
6. **不开 double buffer、不用 TQue、无 SyncAll**：常量 buffer 写一次读多次，ping-pong 无收益；Empty 模板范式统一 TBuf 深度 1；无跨核交互。
7. **测试门禁同步收紧**：kernel 转绿的同时把 ST 驱动退出码从"仅 stTotal2>0"收紧为 `stFailed2 == 0 && stErrors2 == 0`，消除"红基线豁免留在门禁里"的隐患（这是防作弊方向的收紧，不是放松）。

## 系统信息

- **toolchain/环境**：CANN 9.0.0-beta.2（ASCEND_HOME_PATH 实测）；x86_64 Linux 构建宿主；算子包构建脚本 `operators/build.sh <pkg>` 产出 custom_opp .run 并安装到 `${ASCEND_OPP_PATH}/vendors/`。
- **目标平台**：Ascend 950 系列（arch35；OpDef 注册 Ascend950PR/Ascend950DT，真机编译 `__NPU_ARCH__` 恒为 3510）；AIV 向量寄存器宽度 256B（`kVlBytes = 256U`，既有 kernel.h 常量）；单核 UB 256KB、blockSize 32B（设计口径）。
- **目录布局（算子包内）**：`op_kernel/arch35/`（empty.h、kernel.h 共享 VF 链、base.h、group.h、tiling_struct.h）、`op_host/arch35/`（tiling 实现，空张量分类 HandleEmptyTensor 已在前置任务落地）、`tests/aclnn/`（test_aclnn.cpp 驱动 + run.sh + st_cases_branch2.json 12 条）、`tests/tiling/`（TilingUT 73 条）。
- **本卡相关文件**（与本轨迹实际读写一一对应）：写——`op_kernel/arch35/thnn_fused_gru_cell_grad_empty.h`（桩 → 终版全量重写）、`op_kernel/arch35/thnn_fused_gru_cell_grad_kernel.h`（追加 §9.8 DuplicateEmptyROutputVf）、`tests/aclnn/test_aclnn.cpp`（退出码收紧）、`tests/aclnn/run.sh`（注释同步）；读（设计依据）——`docs/.../design/branches/DESIGN-BRANCH-2.md`、`docs/.../design/Kernel.md` §9.8、`docs/.../design/Validation.md`、`op_host/arch35/*tiling*.cpp`（确认 host 契约）。
- **host↔device 契约**：Empty TilingData 独立结构体（usedCoreNum/aTotal/aUbFactor/aBigCoreCnt/aBigCoreLoopCnt/aSmallCoreLoopCnt/postBufSize/hiddenSize/isBias，仅定宽标量、trivially copyable）；EMPTY_A 时除 usedCoreNum=0 与 isBias 外全 0。

## 完整代码

终版 `op_kernel/arch35/thnn_fused_gru_cell_grad_empty.h`（verbatim，含 EMPTY_A 早退与 EMPTY_R 编排）：

```c++
template <typename D_T>
class ThnnFusedGruCellGradEmptyKernel {
public:
    __aicore__ inline ThnnFusedGruCellGradEmptyKernel() {}

    // ── Init（§5.1）：TilingData 读取 + 两路 bias GM 绑定 +（仅 EMPTY_R）
    //    postBuf 分配 + V_MTE3 eventID 获取 ──
    __aicore__ inline void Init(GM_ADDR gradHy, GM_ADDR storage, GM_ADDR gradInputGates,
                                GM_ADDR gradHiddenGates, GM_ADDR gradHx, GM_ADDR gradInputBias,
                                GM_ADDR gradHiddenBias, const ThnnFusedGruCellGradEmptyTilingData* td,
                                AscendC::TPipe* pipe)
    {
        td_ = td;
        pipe_ = pipe;
        usedCoreNum_       = td->usedCoreNum;        // EMPTY_A=0（全核早退）/ EMPTY_R=填充分块核数
        aTotal_            = td->aTotal;             // = H（EMPTY_A 不读）
        aUbFactor_         = td->aUbFactor;          // §2.2 4 约束取 min
        aBigCoreCnt_       = td->aBigCoreCnt;        // §2.2 大小核均衡
        aBigCoreLoopCnt_   = td->aBigCoreLoopCnt;
        aSmallCoreLoopCnt_ = td->aSmallCoreLoopCnt;
        hiddenSize_        = td->hiddenSize;         // 段基：GM 段偏移 = 段序 × hiddenSize + aOff
        isBias_            = td->isBias;             // attr has_bias（§6）

        // 输入 grad_hy/storage（0 元素）与三路空输出不绑定不读/写（§5.1）
        (void)gradHy;
        (void)storage;
        (void)gradInputGates;
        (void)gradHiddenGates;
        (void)gradHx;

        // GM 绑定：仅两路 bias 输出（EMPTY_R 写；EMPTY_A 绑定后不触达，无害）
        gmGradInputBias_.SetGlobalBuffer(reinterpret_cast<__gm__ D_T*>(gradInputBias));
        gmGradHiddenBias_.SetGlobalBuffer(reinterpret_cast<__gm__ D_T*>(gradHiddenBias));

        if (td->postBufSize > 0) {                   // 仅 EMPTY_R（isBias==1 且 B==0）：§4 单 postBuf
            pipe_->InitBuffer(postBuf_, static_cast<uint32_t>(td->postBufSize));
            postPtr_ = reinterpret_cast<__ubuf__ D_T*>(postBuf_.Get<D_T>().GetPhyAddr());
            evVtoMTE3_ = static_cast<int32_t>(GetTPipePtr()->FetchEventID(AscendC::HardEvent::V_MTE3));
        }
    }

    // ── Process（§5.3）：EMPTY_A 早退 + EMPTY_R 编排 ──
    __aicore__ inline void Process()
    {
        const int64_t blockIdx = static_cast<int64_t>(AscendC::GetBlockIdx());
        if (blockIdx >= usedCoreNum_) {
            return;   // ★ EMPTY_A：usedCoreNum=0 → 全核早退（零计算零 IO）
        }

        // blockIdx → [aStart, aEnd)：按 a 元素数切（§2.2 大小核公式）
        int64_t aStart, aEnd;
        if (blockIdx < aBigCoreCnt_) {
            aStart = blockIdx * aBigCoreLoopCnt_ * aUbFactor_;
            aEnd   = aStart + aBigCoreLoopCnt_ * aUbFactor_;
        } else {
            aStart = aBigCoreCnt_ * aBigCoreLoopCnt_ * aUbFactor_
                   + (blockIdx - aBigCoreCnt_) * aSmallCoreLoopCnt_ * aUbFactor_;
            aEnd   = aStart + aSmallCoreLoopCnt_ * aUbFactor_;
        }
        aEnd = (aEnd < aTotal_) ? aEnd : aTotal_;   // 防越界（aTotal = H）
        if (aStart >= aEnd) {
            return;
        }

        // Compute：Duplicate 一次（常量与 aOff 无关，范式 §1.2 实现要点）——唯一 VF
        DuplicateEmptyROutputVf<D_T>(postPtr_, static_cast<D_T>(kEmptyROutputValue),
                                     static_cast<uint32_t>(aUbFactor_));

        // V→MTE3 同步：postBuf V 写完成前禁止 MTE3 读（§5.5 唯一 crossing）
        AscendC::SetFlag<AscendC::HardEvent::V_MTE3>(evVtoMTE3_);
        AscendC::WaitFlag<AscendC::HardEvent::V_MTE3>(evVtoMTE3_);

        for (int64_t aOff = aStart; aOff < aEnd; aOff += aUbFactor_) {
            const int64_t aLen = (aEnd - aOff < aUbFactor_) ? (aEnd - aOff) : aUbFactor_;
            CopyOut(aOff, aLen);   // §5.4：每 chunk 6 段 strided 零写
        }
    }

private:
    // ── CopyOut（§5.4）：EMPTY_R 每 chunk 6 段 strided 零写出 ──
    //   段枚举 s = 输出序×3 + 段序 ∈ [0, BIAS_SEG_CNT=6)（s-major
    //   [in_r|in_z|in_n|hid_r|hid_z|hid_n]）；s<3 → grad_input_bias[段序]，
    //   s≥3 → grad_hidden_bias[段序−3]（两张独立 (3H,) 张量，段内偏移 = 段序×H + aOff）
    __aicore__ inline void CopyOut(int64_t aOff, int64_t aLen)
    {
        AscendC::DataCopyExtParams params{};
        params.blockCount = 1;
        params.blockLen   = static_cast<uint32_t>(aLen * sizeof(D_T));   // 有效字节（尾块亦精确）
        params.srcStride  = 0;
        params.dstStride  = 0;
        params.rsv        = 0;
        auto outLocal = postBuf_.Get<D_T>();      // 常量零驻留（§5.3），6 段共读
        for (int32_t s = 0; s < BIAS_SEG_CNT; ++s) {
            if (s < 3) {
                AscendC::DataCopyPad(gmGradInputBias_[s * hiddenSize_ + aOff], outLocal, params);
            } else {
                AscendC::DataCopyPad(gmGradHiddenBias_[(s - 3) * hiddenSize_ + aOff], outLocal, params);
            }
        }
    }

    const ThnnFusedGruCellGradEmptyTilingData* td_ = nullptr;
    AscendC::TPipe* pipe_ = nullptr;

    // ─── GM 绑定（仅两路 bias 输出；输入与三路空输出不绑）───
    AscendC::GlobalTensor<D_T> gmGradInputBias_;   // (3H,)：EMPTY_R 零填充目标
    AscendC::GlobalTensor<D_T> gmGradHiddenBias_;  // (3H,)：EMPTY_R 零填充目标

    // ─── UB（TBuf，深度 1，不开启 double buffer；§4 仅 1 路 postBuf）───
    AscendC::TBuf<AscendC::TPosition::VECOUT> postBuf_;   // Duplicate 写一次、6 段 CopyOut 共读
    __ubuf__ D_T* postPtr_ = nullptr;                      // postBuf 基址（D_T 视图）

    // ─── 调度参数（从 TilingData 载入）───
    int32_t usedCoreNum_ = 0;          // EMPTY_A=0（全核早退）/ EMPTY_R=填充分块核数
    int64_t aTotal_ = 0;              // = H（EMPTY_A 不读）
    int64_t aUbFactor_ = 0;           // §2.2 4 约束取 min
    int32_t aBigCoreCnt_ = 0;         // §2.2 大小核均衡
    int64_t aBigCoreLoopCnt_ = 0;
    int64_t aSmallCoreLoopCnt_ = 0;
    int64_t hiddenSize_ = 0;          // H：段基 = 段序 × hiddenSize + aOff
    int32_t isBias_ = 0;             // attr has_bias（§6）

    // ─── eventID（FetchEventID 获取、禁止硬编码，§5.5）───
    int32_t evVtoMTE3_ = 0;          // V_MTE3：Duplicate → CopyOut RAW
};
```

跨分支共享的常量填充 VF（追加进 `op_kernel/arch35/thnn_fused_gru_cell_grad_kernel.h` §9.8，verbatim；`kVlBytes = 256U` 为该文件既有常量）：

```c++
// kEmptyROutputValue：sum 归约的空 batch 退化值（空和 = 0）
constexpr float kEmptyROutputValue = 0.0f;

// DuplicateEmptyROutputVf（逐字取自 Kernel.md §9.8 / reduction-empty-kernel-template.md §5.1）
template <typename T>
__simd_vf__ inline void DuplicateEmptyROutputVfImpl(
    __ubuf__ T* dst, T value, uint32_t count, uint16_t repU16)
{
    constexpr uint32_t VL = kVlBytes / sizeof(T);   // 寄存器 VL（元素数）：fp32=64，b16=128
    AscendC::Reg::RegTensor<T> vReg;
    AscendC::Reg::Duplicate(vReg, value);
    AscendC::Reg::MaskReg mask;
    uint32_t remaining = count;
    for (uint16_t i = 0; i < repU16; ++i) {
        int32_t off = static_cast<int32_t>(i) * static_cast<int32_t>(VL);
        mask = AscendC::Reg::UpdateMask<T>(remaining);
        AscendC::Reg::StoreAlign(dst + off, vReg, mask);
    }
}

// 调用侧：value = 0（kEmptyROutputValue, sum）；count = aUbFactor（单 chunk 元素数）
template <typename T>
__aicore__ inline void DuplicateEmptyROutputVf(__ubuf__ T* dst, T value, uint32_t count)
{
    constexpr uint32_t VL = kVlBytes / sizeof(T);
    const uint16_t repU16 = static_cast<uint16_t>((count + VL - 1) / VL);
    asc_vf_call<DuplicateEmptyROutputVfImpl<T>>(dst, value, count, repU16);
}
```

host 侧契约（前序任务已落地、本卡 kernel 消费，摘录自 tiling 实现的 grep 确认）：`ClassifyEmptyTensor` 判定顺序 H==0 → EMPTY_A；否则 B==0 → isBias==1 ? EMPTY_R : EMPTY_A；EMPTY_A 置 `usedCoreNum=0` + `SetBlockDim(1)`（严禁 0）；EMPTY_R 按 4 约束填 aUbFactor 等字段。

## 预防

- 写 reduction 算子的空张量分支前，先确认 reducer 的空集值：sum → 0；min/max 等空集语义不同，不能套用"零填充"。
- host 侧空退化 `SetBlockDim` 严禁 0——必须 `SetBlockDim(1)` + `usedCoreNum=0`，kernel 用 `blockIdx >= usedCoreNum` 表达全核早退。
- V 写、MTE3 读同一 TBuf：必须 `FetchEventID(V_MTE3)` + 一对 `SetFlag/WaitFlag`，事件号禁止硬编码。
- 每个 `__simd_vf__` 定义必须有 `asc_vf_call<>` 调用点（仓库门禁 vf_reachability_check 把"只为过 grep 保留的死 VF 符号"判 FAIL）。
- 桩阶段为红基线放宽的 ST 退出码，分支转绿后必须同步收紧（把本分支 `stFailed==0 && stErrors==0` 纳入返回条件），否则退出码 0 ≠ 全过。
- b16 dtype 下 buffer 容量按 maxDtypeSize=4B/元素预留，实写/实读按 sizeof(D_T)——不要按 2B 反推 buffer 大小。

## 验证信号

以下为该空张量分支 kernel 实现（常量填充 VF + empty 模板三个函数）当次开发会话的实测结果，验证命令为算子包标准链路：`build.sh <pkg>` 编译安装 → `tests/aclnn/run.sh`（build+oracle 生成+ST 执行）→ `tests/tiling/run.sh` → 四项 ops-impl-review 脚本。

- 编译 + 安装成功：custom_opp .run 包生成、SHA256 校验 OK、安装 SUCCESS（来源平台：950；证据等级：tool_observed）。
- 本分支 ST 12/12 PASSED（E08–E10 + dtype/切分边界补充用例），全部输出 mere=0.000e+00、mare=0.000e+00、nan_inf_mismatch=0（来源平台：950；证据等级：tool_observed）。
- 切分边界实测：H=1（aUbFactor 钳到 1、postBufSize=32B、bias 输出 (3,)）、H=2048（aUbFactor=1024、aLoopCntTotal=2、双核无尾块）、H=3000（尾 chunk valid=952，尾块 DataCopyPad 字节精确写 + aEnd=min(aEnd,aTotal) 防越界）均 PASS（来源平台：950；证据等级：tool_observed）。
- fp16/bf16 EMPTY_R 零填充位级正确：fp16（B=0,H=8,bias=1）与 bf16（B=0,H=8,bias=1）两用例 mere=0.000e+00、mare=0.000e+00、determinism OK(bitwise,2runs)（来源平台：950；证据等级：tool_observed）。
- 确定性：全部 12 条用例同输入 2 次执行位级一致（无数据依赖、无浮点舍入）（来源平台：950；证据等级：tool_observed）。
- 同批回归不退化（同一次 ST 运行输出内）：smoke 1/1、Branch-0 20/20、Branch-1 11/11、TilingUT 73/73，run.sh 退出码 0（来源平台：950；证据等级：tool_observed）。
- 四项代码↔方案一致性脚本退出码全 0：scalar_mainchain（GetValue/SetValue 0 处）、vf_reachability（12 个 __simd_vf__ 全被 asc_vf_call 引用、13 调用点）、workspace_consistency（3 个分支 §8 needs ↔ host 分配 yes）、non3510_scaffold（无调试脚手架残留）（来源平台：950；证据等级：tool_observed）。

## 失效边界

- 语义边界：仅适用"空 batch 求和 = 0"（sum 类 reducer）的退化；reducer 为 min/max 等空集值不同者不适用。
- 结构边界：B>0 主链、跨核规约（group 需 SyncAll + workspace fp32 中转）不适用；本卡无 SyncAll、无 user workspace。
- 规模边界：aUbFactor 受单 buf 64KB 上限钳制（maxUbFactor = 65536/4 = 16384 元素）；H ≤ 3000 实测覆盖，H > 6×16384 = 98304（aLoopCntTotal > 6）的多 chunk 大 H 未实测。
- 平台边界：寄存器宽度 kVlBytes=256B、UB 256KB、blockSize 32B 按 950 系列口径；其他 AIV 平台（VECOUT/VECIN 枚举与 V_MTE3 事件为 AscendC 通用机制）推断可迁移——**未验证，推断可迁移**；950PR 与 950DT 未在本轨迹区分实测。
- EMPTY_A 判定顺序：H==0 优先于 B==0（H==0 时 3H=0，bias 输出亦为空张量，走早退而非零填充）——复用本配方时须保持该顺序。

## 坏实践

- 桩阶段 EMPTY_R 不写 bias 输出：poison 初化的输出与期望零比对失败（红基线，测试驱动注释与开发日志均载明；具体 6/12 失败数字为前序会话 LOG 记载、本轨迹未复现，不作验证信号）。空张量输出"不写"只对 numel=0 的输出合法。
- 每次循环迭代重复 Duplicate：常量与 aOff 无关，一次驻留、多段共读即可；重复写只增加 V 指令。
- 给常量 buffer 包 TQue/开 double buffer：写一次读多次的 buffer 无 ping-pong 收益（范式明确 Empty 模板用 TBuf 深度 1）。
- host 对全核早退写 `SetBlockDim(0)`：非法（blockDim 必须 ≥1），正确表达是 `SetBlockDim(1)` + `usedCoreNum=0`。

## 误诊

- 实现前一度怀疑 `TPosition::VECOUT` 不是合法枚举、打算偏离设计改用 base.h 的 VECCALC"求稳"——grep CANN 头文件后确认 VECOUT 合法，按设计实现并实测通过；"代码库没有先例 = API 不存在"是误判，应先探测头文件。
- 曾担心 b16 下 `Reg::Duplicate` + 不带 StoreDist 的 `StoreAlign` 会写出交错数据（该疑虑已被实证否定：常量 0 填充路径 plain StoreAlign 实测位级正确）。


