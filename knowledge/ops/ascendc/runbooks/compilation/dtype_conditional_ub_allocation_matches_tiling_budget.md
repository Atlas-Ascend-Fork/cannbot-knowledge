---
type: "Runbook"
title: "按 dtype 分配 UB 必须匹配 tiling 预算"
description: "SPLIT_D 的 fp32 路径直接使用输入张量，却仍分配仅低精度转换需要的 xFp32Buf，使实际 UB 占用超过 tiling 预算；按 dtype 守护该缓冲后恢复大 D 路径。"
tags: ["task.debugging", "topic.implementation.tiling", "topic.memory"]
status: stable
sources: []
created_at: "2026-08-14T03:54:37Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["a3"]
---

# 按 dtype 分配 UB 必须匹配 tiling 预算

## 现象

RmsNorm 的 NORMAL 路径和小 D 用例已通过，但较长归约维进入 SPLIT_D 后，设备同步报 ACL `507035`，并明确给出 “VEC instruction read/write UB is out of bounds”。故障发生在 fp32 大 D 路径；这与一般的数值 mismatch 或 GM 索引错误不同。

## 适用场景

- 工程形态：classic Ascend C 直调 kernel 的编译、链接或运行工程。
- API 路径：`KernelRmsNormSplitD`、`xFp32Buf_`、`ACL 507035`、`ubFactor` 所在的 kernel、host 或构建接口链。
- 验证平台与版本：平台 a3；CANN：unknown。
- 适用粒度：`same_operator`，迁移前须重算同算子各 dtype/template 的 live-buffer 预算。
- 路线优先级：`recommended_fastpath`。
- 不适用/停止边界：错误信号、API 契约或数据路径与本卡不一致时停止套用；修复后未闭合原信号则回到根因诊断。

## 根因

SPLIT_D 的 fp32 计算直接对 `xLocal` 做平方，不使用 `xFp32Buf_`；但 `Init` 仍无条件为它分配 `ubFactor * sizeof(float)`。令 `B_tiling(dtype, tile)` 为 host 预算、`B_live(dtype, tile)` 为 kernel 所有 live queue/TBuf 与固定 scratch 之和，则该分支出现 `B_live = B_tiling + tile * sizeof(float)`，并在 `B_live > UB_available` 时触发 VEC UB 越界。

根因只有一个：kernel 的 dtype 条件分配与 tiling 的逐元素预算不一致。修复不是减小测试规模或改异常处理，而是让 fp32 的实际 live-buffer 集合与 host 预算使用同一公式。

## 解决配方

### before

```cpp
    __aicore__ inline void Init(GM_ADDR x, GM_ADDR gamma, GM_ADDR y,
                                int64_t numRow, int64_t numCol, int64_t numColAlign,
                                int64_t blockLength, uint32_t ubFactor, float epsilon)
    {
        numCol_ = numCol;
        numColAlign_ = numColAlign;
        ubFactor_ = static_cast<int64_t>(ubFactor);
        epsilon_ = epsilon;
        blockElems_ = 32 / sizeof(T);

        xGm_.SetGlobalBuffer((__gm__ T *)x);
        gammaGm_.SetGlobalBuffer((__gm__ T *)gamma);
        yGm_.SetGlobalBuffer((__gm__ T *)y);

        int64_t blk = AscendC::GetBlockIdx();
        coreStart_ = blockLength * blk;
        coreEnd_ = coreStart_ + blockLength;
        if (coreEnd_ > numRow) coreEnd_ = numRow;
        if (coreStart_ > numRow) coreStart_ = numRow;

        pipe_.InitBuffer(xQueue_, DEPTH, ubFactor_ * sizeof(T));
        pipe_.InitBuffer(gammaQueue_, DEPTH, ubFactor_ * sizeof(T));
        pipe_.InitBuffer(yQueue_, DEPTH, ubFactor_ * sizeof(T));
        pipe_.InitBuffer(xFp32Buf_, ubFactor_ * sizeof(float));
        pipe_.InitBuffer(sqxBuf_, ubFactor_ * sizeof(float));
        pipe_.InitBuffer(reduceBuf_, 256);
        pipe_.InitBuffer(tmpBuf_, 256);
        pipe_.InitBuffer(scalarBuf_, 256);
        if constexpr (!std::is_same<T, float>::value) {
            pipe_.InitBuffer(gammaFp32Buf_, ubFactor_ * sizeof(float));
        }
    }
```

### after

```cpp
    __aicore__ inline void Init(GM_ADDR x, GM_ADDR gamma, GM_ADDR y,
                                int64_t numRow, int64_t numCol, int64_t numColAlign,
                                int64_t blockLength, uint32_t ubFactor, float epsilon)
    {
        numCol_ = numCol;
        numColAlign_ = numColAlign;
        ubFactor_ = static_cast<int64_t>(ubFactor);
        epsilon_ = epsilon;
        blockElems_ = 32 / sizeof(T);

        xGm_.SetGlobalBuffer((__gm__ T *)x);
        gammaGm_.SetGlobalBuffer((__gm__ T *)gamma);
        yGm_.SetGlobalBuffer((__gm__ T *)y);

        int64_t blk = AscendC::GetBlockIdx();
        coreStart_ = blockLength * blk;
        coreEnd_ = coreStart_ + blockLength;
        if (coreEnd_ > numRow) coreEnd_ = numRow;
        if (coreStart_ > numRow) coreStart_ = numRow;

        pipe_.InitBuffer(xQueue_, DEPTH, ubFactor_ * sizeof(T));
        pipe_.InitBuffer(gammaQueue_, DEPTH, ubFactor_ * sizeof(T));
        pipe_.InitBuffer(yQueue_, DEPTH, ubFactor_ * sizeof(T));
        pipe_.InitBuffer(sqxBuf_, ubFactor_ * sizeof(float));
        pipe_.InitBuffer(reduceBuf_, 256);
        pipe_.InitBuffer(tmpBuf_, 256);
        pipe_.InitBuffer(scalarBuf_, 256);
        if constexpr (!std::is_same<T, float>::value) {
            pipe_.InitBuffer(xFp32Buf_, ubFactor_ * sizeof(float));
            pipe_.InitBuffer(gammaFp32Buf_, ubFactor_ * sizeof(float));
        }
    }
```

## 设计决策

优先移除 fp32 不使用的缓冲，而不是把无用项补进 `perElem`。前者使 kernel 的实际资源需求与已有计算路径一致，也保留更大的 `ubFactor`；后者会为从不读取的存储付费并缩小切片。

## 性能影响

修复减少 fp32 SPLIT_D 的 UB 占用，理论上允许保持既有切片宽度；轨迹没有提供同平台、同负载的配对性能数据，因此只证明功能与资源闭环，不宣称加速。

## 预防

- 为每个模板、每个 dtype 列出所有存活的 `TQue/TBuf`，逐项核对 `depth * bytes`；
- host 的 `perElem` 公式必须与 kernel 的 `if constexpr` 分配条件同源核算；
- 在模板切换点两侧使用参数化归约维 probe，至少覆盖 fp32 与低精度分支；
- 资源估算除逐元素缓冲外，还要预留 reduce、tmp、scalar 等固定开销。

## 验证信号

以下信号均来自本次开发会话修复前后的实际构建、运行或评测输出。

- 修复前：大 SPLIT_D 路径触发 UB 越界后的 ACL 507035 vector core exception。（来源平台：a3；证据等级: tool_observed）。
- 修复后：大 SPLIT_D 定向矩阵全部输出 OK。（来源平台：a3；证据等级: tool_observed）。
- 修复后：干净构建 exit=0，随后 32 passed。（来源平台：a3；证据等级: tool_observed）。

## 失效边界

本卡只覆盖 `KernelRmsNormSplitD` 的这组缓冲及 tiling 预算。若 `DEPTH`、队列集合、dtype 转换路线、UB 容量或固定 scratch 发生变化，必须重新计算 `B_live(dtype, tile) <= UB_available`，不得复用源任务的逐元素常数。其他平台未在本闭环验证。

## 坏实践

- 看到大 D 越界就只把 `ubFactor` 乘固定折扣；这会掩盖 host/kernel 资源模型不一致；
- 为所有 dtype 无条件分配转换缓冲，期待编译器消除；`InitBuffer` 已经占用 UB，不因后续未读而自动安全；
- 只跑 NORMAL 或小 D 用例后宣布全部模板通过。

## 误诊

如果缩小 `ubFactor` 后故障位置不变，或错误日志指向 GM 地址、尾块 DMA、队列同步，应检查地址和生命周期，不要把所有 ACL 507035 都归为容量溢出。只有“模板切换相关 + 实际分配可算出超过 UB + 移除无用缓冲后闭环”才支持本根因。

<!-- cannbot:related:start -->
## 相关

- [507035 — Host 按逻辑行宽预算导致 UB 溢出](ub_budget_uses_aligned_physical_width_507035.md)（`related`）：“kernel 的 dtype 条件分配与 tiling 的逐元素预算不一致”定位多分配的转换 TBuf，“Host 与 Device 共用同一对齐公式”处理物理 stride 低估，二者共同要求 Host 预算精确复刻 Device live-buffer。
- [FP16 double-buffer UB 预算漏乘 2 致 VEC_ERROR](fp16_double_buffer_ub_budget_queue_vs_tbuf_multiplier.md)（`related`）：“kernel 的 dtype 条件分配与 tiling 的逐元素预算不一致”要求按 dtype 枚举 live-buffer，“Queue 部分受 double buffer 翻倍、Cast(TBuf) 部分不翻倍”进一步给出混合 Queue/TBuf 时各自倍数的核算法。
<!-- cannbot:related:end -->
