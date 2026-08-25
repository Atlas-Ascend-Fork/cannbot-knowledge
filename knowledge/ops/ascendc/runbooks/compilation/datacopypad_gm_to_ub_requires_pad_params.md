---
type: "Runbook"
title: "DataCopyPad 加载缺少 Pad 参数导致编译失败"
description: "dav-3510 的 GM 到 UB DataCopyPad 扩展重载需要第四个 Pad 参数，不能照搬 UB 到 GM 的三参数形式。"
tags: ["task.debugging", "topic.data_movement.data_copy", "topic.implementation.api_layer.basic_api"]
status: stable
sources: []
created_at: "2026-08-14T03:13:06Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["950"]
---

# DataCopyPad 加载缺少 Pad 参数导致编译失败

## 现象

在 Ascend950 / `dav-3510` 上构建一个使用 `TBuf` 分块搬运的 Ascend C kernel 时，`cummin.asc` 的输入搬运调用写成了三参数形式：

```text
AscendC::DataCopyPad(xLocal, xGm_[rowBase + cs], loadParams)
```

远端 CANN 9.0.1 编译器在该调用处报出原文：

```text
error: no matching function for call to 'DataCopyPad'
candidate function template not viable: requires 4 arguments, but 3 were provided
```

同一函数内的 UB 到 GM 输出搬运仍可使用三参数形式，因此不能仅凭函数名相同就把两个方向的重载签名视为对称。

## 适用场景

- 工程形态：Ascend C kernel 直调工程的构建阶段；
- API 路径：`LocalTensor<T> <- GlobalTensor<T>` 的 `AscendC::DataCopyPad` 扩展参数重载；
- 验证过的平台与版本：Ascend950PR_957c / `dav-3510`，CANN 9.0.1；与 frontmatter `platforms: [950]` 一致；
- 适用粒度：`platform_wide`，适用于同一工具包重载集合下的 GM 到 UB 搬运调用；
- 路线优先级：`recommended_fastpath`，保留字节长度的 `DataCopyExtParams`，并为加载方向显式补默认 `DataCopyPadExtParams<T>`；
- 明确不适用或未验证场景：UB 到 GM 的 store 重载、非 dav-3510 工具包版本，以及 A2/A3 均未验证，必须重新查目标版本声明。

## 根因

dav-3510 的 GM 到 UB 扩展重载签名要求 `DataCopyPadExtParams<T>`，而出错代码误用了仅含 `DataCopyExtParams` 的三参数调用形式。

## 解决配方

保留 `DataCopyExtParams` 中按字节表达的 `blockLen`，仅在加载方向补第四个默认 Pad 参数；下面代码来自轨迹中的真实写入快照，未做改写。

### before

代码证据：revision 为轨迹修复前写入快照（轨迹未记录 40 位 Git revision）；path `operators/cummin/cummin.asc`；symbol `KernelCummin<T>::Process`；lines 137–193。该函数完整展示了出错的 GM→UB 三参数调用及同函数中的 UB→GM 三参数调用，支撑“加载与存储重载不对称”的结论。

```cpp
    __aicore__ inline void Process()
    {
        for (int64_t r = 0; r < rowsThisBlock_; ++r) {
            CT cur = Traits::sentinel();
            int64_t curIdx = 0;
            int64_t rowBase = r * rowLength_;

            for (int64_t cs = 0; cs < rowLength_; cs += chunkElems_) {
                uint32_t thisChunk = static_cast<uint32_t>(rowLength_ - cs);
                if (thisChunk > chunkElems_) thisChunk = chunkElems_;
                if (thisChunk == 0) break;

                // --- CopyIn: MTE2 GM -> UB ---
                auto xLocal = xBuf_.Get<T>();
                AscendC::DataCopyExtParams loadParams{
                    /*blockCount=*/1,
                    /*blockLen=*/static_cast<uint32_t>(thisChunk * sizeof(T)),
                    /*srcStride=*/0, /*dstStride=*/0, /*rsv=*/0};
                AscendC::DataCopyPad(xLocal, xGm_[rowBase + cs], loadParams);
                // sync MTE2 (load done) -> S (scalar read)
                SyncMte2ToS();

                // --- Compute: scalar sequential prefix-min scan on UB ---
                auto valLocal = valBuf_.Get<T>();
                auto idxLocal = idxBuf_.Get<int64_t>();
                __ubuf__ T *xAddr = reinterpret_cast<__ubuf__ T *>(xLocal.GetPhyAddr());
                __ubuf__ T *vAddr = reinterpret_cast<__ubuf__ T *>(valLocal.GetPhyAddr());
                __ubuf__ int64_t *iAddr = reinterpret_cast<__ubuf__ int64_t *>(idxLocal.GetPhyAddr());
                for (uint32_t j = 0; j < thisChunk; ++j) {
                    CT a = Traits::to_ct(xAddr[j]);
                    // lte(a, cur): NaN is global min; on tie (a<=cur) keep LAST.
                    bool aNan = (a != a);
                    bool curNan = (cur != cur);
                    bool upd = aNan ? true : (curNan ? false : (a <= cur));
                    if (upd) {
                        cur = a;
                        curIdx = cs + static_cast<int64_t>(j);
                    }
                    vAddr[j] = Traits::from_ct(cur);
                    iAddr[j] = curIdx;
                }

                // --- CopyOut: S (write done) -> MTE3 (store) ---
                SyncSToMte3();
                auto valLocalOut = valBuf_.Get<T>();
                auto idxLocalOut = idxBuf_.Get<int64_t>();
                AscendC::DataCopyExtParams valParams{
                    1, static_cast<uint32_t>(thisChunk * sizeof(T)), 0, 0, 0};
                AscendC::DataCopyPad(valGm_[rowBase + cs], valLocalOut, valParams);
                AscendC::DataCopyExtParams idxParams{
                    1, static_cast<uint32_t>(thisChunk * sizeof(int64_t)), 0, 0, 0};
                AscendC::DataCopyPad(idxGm_[rowBase + cs], idxLocalOut, idxParams);
                // sync MTE3 (store done) -> S (buffer reusable next iter)
                SyncMte3ToS();
            }
        }
    }
```

### after

代码证据：revision 为轨迹修复后写入快照（轨迹未记录 40 位 Git revision）；path `operators/cummin/cummin.asc`；symbol `KernelCummin<T>::Process`；lines 137–194。该函数完整展示加载方向新增默认 Pad 参数，同时输出方向保持三参数形式。

```cpp
    __aicore__ inline void Process()
    {
        for (int64_t r = 0; r < rowsThisBlock_; ++r) {
            CT cur = Traits::sentinel();
            int64_t curIdx = 0;
            int64_t rowBase = r * rowLength_;

            for (int64_t cs = 0; cs < rowLength_; cs += chunkElems_) {
                uint32_t thisChunk = static_cast<uint32_t>(rowLength_ - cs);
                if (thisChunk > chunkElems_) thisChunk = chunkElems_;
                if (thisChunk == 0) break;

                // --- CopyIn: MTE2 GM -> UB ---
                auto xLocal = xBuf_.Get<T>();
                AscendC::DataCopyExtParams loadParams{
                    /*blockCount=*/1,
                    /*blockLen=*/static_cast<uint32_t>(thisChunk * sizeof(T)),
                    /*srcStride=*/0, /*dstStride=*/0, /*rsv=*/0};
                AscendC::DataCopyPad(xLocal, xGm_[rowBase + cs], loadParams,
                                      AscendC::DataCopyPadExtParams<T>());
                // sync MTE2 (load done) -> S (scalar read)
                SyncMte2ToS();

                // --- Compute: scalar sequential prefix-min scan on UB ---
                auto valLocal = valBuf_.Get<T>();
                auto idxLocal = idxBuf_.Get<int64_t>();
                __ubuf__ T *xAddr = reinterpret_cast<__ubuf__ T *>(xLocal.GetPhyAddr());
                __ubuf__ T *vAddr = reinterpret_cast<__ubuf__ T *>(valLocal.GetPhyAddr());
                __ubuf__ int64_t *iAddr = reinterpret_cast<__ubuf__ int64_t *>(idxLocal.GetPhyAddr());
                for (uint32_t j = 0; j < thisChunk; ++j) {
                    CT a = Traits::to_ct(xAddr[j]);
                    // lte(a, cur): NaN is global min; on tie (a<=cur) keep LAST.
                    bool aNan = (a != a);
                    bool curNan = (cur != cur);
                    bool upd = aNan ? true : (curNan ? false : (a <= cur));
                    if (upd) {
                        cur = a;
                        curIdx = cs + static_cast<int64_t>(j);
                    }
                    vAddr[j] = Traits::from_ct(cur);
                    iAddr[j] = curIdx;
                }

                // --- CopyOut: S (write done) -> MTE3 (store) ---
                SyncSToMte3();
                auto valLocalOut = valBuf_.Get<T>();
                auto idxLocalOut = idxBuf_.Get<int64_t>();
                AscendC::DataCopyExtParams valParams{
                    1, static_cast<uint32_t>(thisChunk * sizeof(T)), 0, 0, 0};
                AscendC::DataCopyPad(valGm_[rowBase + cs], valLocalOut, valParams);
                AscendC::DataCopyExtParams idxParams{
                    1, static_cast<uint32_t>(thisChunk * sizeof(int64_t)), 0, 0, 0};
                AscendC::DataCopyPad(idxGm_[rowBase + cs], idxLocalOut, idxParams);
                // sync MTE3 (store done) -> S (buffer reusable next iter)
                SyncMte3ToS();
            }
        }
    }
```

## 设计决策

- 选择 `DataCopyPadExtParams<T>()` 作为第四参，是为了匹配已经使用字节级 `DataCopyExtParams` 的 GM→UB 扩展重载，并保持默认“不额外 padding”的语义；
- 没有把整个调用改写成另一组 `DataCopyParams`/`DataCopyPadParams`，避免同时改变长度和 stride 的单位契约；
- 没有给 UB→GM 调用机械补第四参，因为目标工具包中该方向的扩展重载本来就是三参数；
- 当前方案属于 `recommended_fastpath`。

## 预防

- 根据参数方向同时核对重载：`LocalTensor <- GlobalTensor` 与 `GlobalTensor <- LocalTensor` 分开查；
- 看到 “requires 4 arguments, but 3 were provided” 时，先核对第三参属于 `DataCopyExtParams` 还是 `DataCopyParams`；
- 尾块使用字节长度时，第四参的模板类型必须与 `LocalTensor<T>` 一致；
- 修复后至少重新编译覆盖所有模板实例，不要只检查单一 dtype。

## 验证信号

这条知识来自一次 Ascend950 kernel 构建联调：编译器先在输入搬运处拒绝三参数调用，随后远端查询了 CANN 9.0.1 头文件中的加载/存储重载，补参后编译继续越过该错误，最终完整目标构建成功。

- CANN 9.0.1 头文件探针显示 GM→UB 扩展重载为四参数，而 UB→GM 扩展重载为三参数（来源平台: 950；证据等级: tool_observed）；
- 修复后 `libop_cummin.so` 链接成功并显示 `Built target op_cummin`（来源平台: 950；证据等级: tool_observed）；
- 干净重建后测试套件全部通过，证明加载调用在实际模板分发和上板执行中可用（来源平台: 950；证据等级: tool_observed）。

## 失效边界

- 结论绑定 CANN 9.0.1 / dav-3510 的已观测重载集合；其他工具包版本必须重新查声明；
- 这不是“所有 DataCopyPad 都要四参”的规则，UB→GM 方向在本版本仍是三参；
- A2/A3 未验证，不写入 `platforms`，也不推断其签名相同。

## 坏实践

- 看到同名 API 就假设 load/store 参数完全对称；
- 为消除编译错误而随意增加 Pad 参数，却不核对第三参的参数族和长度单位；
- 一次性改动 load/store 两个方向，掩盖真正缺参的调用点。

## 误诊

无证据表明此错误与 DMA 32B 对齐或尾块长度有关；编译器在重载解析阶段已经明确指出参数个数不匹配。

<!-- cannbot:related:start -->
## 相关

- [DataCopy](../../apis/simd_api/basic_api/memory_vector_compute/data_move/data_copy_gm_to_ub_nddma.md)（`exemplifies`）：DataCopy 与《DataCopyPad 加载缺少 Pad 参数导致编译失败》的实质衔接是：该 DataCopy 是 GM→UB NDDMA，多维 shape/stride、NdDmaDci 与非对齐 padding 是直接契约；所选故障卡覆盖漏维、stride=0 和 cache 刷新边界。
- [DataCopyPad](../../apis/simd_api/basic_api/memory_vector_compute/data_move/data_copy_pad_gm_to_ub.md)（`exemplifies`）：《DataCopyPad》说明将数据从GM非对齐搬运至UB，可根据需要自行填充数据。；《DataCopyPad 加载缺少 Pad 参数导致编译失败》说明dav-3510 的 GM 到 UB DataCopyPad 扩展重载需要第四个 Pad 参数，不能照搬 UB 到 GM 的三参数形式。。二者在GM到UB非对齐搬入依赖Pad参数、32B最小DMA和LocalTensor/offset/rightPad合同，UB到GM方向的重载不同上存在可执行的直接衔接。
- [DataCopy 非32字节对齐尾块丢字节](../precision/datacopy_32.md)（`related`）：本卡从 DataCopy 切换到 DataCopyPad 后，GM→UB 方向必须使用带 PadExtParams 的四参数重载；目标卡给出该编译期接口约束。
- [DataCopyPad 无匹配重载 LocalTensor 实参不一致](datacopypad_localtensor.md)（`related`）：GM→UB 卡给出必须携带 PadExtParams 的方向签名，本卡补充签名匹配后 LocalTensor<T> 与 GlobalTensor<T> 的 T 仍须一致。
- [DataCopyPad 未填满强制对齐缓冲 — 小维规约读入脏尾部](../precision/datacopypad_tail_must_initialize_full_reduction_extent.md)（`related`）：GM→UB DataCopyPad 的 pad 参数决定尾部写入值；缺失时无法依赖搬运自动初始化 reduction tail。
- [DataCopy GM→UB 需 32B 对齐，非对齐 C 统计输出全零](../precision/datacopy_gm_to_ub_non_32b_aligned_silent_zero.md)（`same_topic`）：DataCopy GM→UB 需 32B 对齐，非对齐 C 统计输出全零：本卡以C字节数非32B倍数复现GM→UB DataCopy静默全零；DataCopyPad是直接修复，32B最小粒度卡解释硬件根因，其余所选卡覆盖Pad参数、尾块初始化/逐行搬运及对向DataCopy尾丢失验证。 目标卡《DataCopyPad 加载缺少 Pad 参数导致编译失败》补充：dav-3510 的 GM 到 UB DataCopyPad 扩展重载需要第四个 Pad 参数，不能照搬 UB 到 GM 的三参数形式。
- [DataCopyExtParams blockLen 窄化编译失败](datacopyextparams_block_len_requires_uint32.md)（`same_topic`）：焦点处理DataCopyPad GM→UB 扩展重载的 Pad 参数签名；DataCopyExtParams blockLen 窄化编译失败正文界定“DataCopyExtParams 的 blockLen 接收 uint32_t，模板表达式 D* sizeof(T) 须显式窄化后再做 DataCopyPad”。候选是 DataCopyPad API、相反方向重载、参数窄化与 rightPad 类型的同一签名决策。
- [DataCopyExtParams 运行时块数窄化编译失败](datacopyextparams_block_count_requires_uint16.md)（`same_topic`）：焦点处理DataCopyPad GM→UB 扩展重载的 Pad 参数签名；DataCopyExtParams 运行时块数窄化编译失败正文界定“DataCopyExtParams 的 blockCount 接收运行时 uint32_t 时触发列表初始化窄化错误，须在确认范围后显式转为 uint16_t”。候选是 DataCopyPad API、相反方向重载、参数窄化与 rightPad 类型的同一签名决策。
- [DataCopyPad UB→GM 四参调用导致编译失败](datacopypad_ub_to_gm_has_no_pad_params.md)（`same_topic`）：焦点处理DataCopyPad GM→UB 扩展重载的 Pad 参数签名；DataCopyPad UB→GM 四参调用导致编译失败正文界定“DataCopyPad 搬出方向只接受 GlobalTensor、LocalTensor 与 DataCopyExtParams 三参；误带 PadExtParams 会令模板匹配失败”。候选是 DataCopyPad API、相反方向重载、参数窄化与 rightPad 类型的同一签名决策。
- [DataCopyPad rightPad 字段为 uint8_t](datacopypad_rightpad_uint8_t.md)（`same_topic`）：焦点处理DataCopyPad GM→UB 扩展重载的 Pad 参数签名；DataCopyPad rightPad 字段为 uint8_t正文界定“AscendC DataCopyPadExtParams 的 rightPad 量字段类型是 uint8_t，用 static_cast<uint16_t> 填充会触发 C++11 narrowing 编译错误；编译器建议改 static_”。候选是 DataCopyPad API、相反方向重载、参数窄化与 rightPad 类型的同一签名决策。
- [DataCopyPad 五参编译失败—LocalTensor 子视图替代偏移](datacopypad_offset_via_tensor_subview.md)（`same_topic`）：两卡处理同一个 GM→UB overload 契约：缺少 Pad 参数是三参错误，多传目标 offset 是五参错误；合法调用固定为四参，offset 由 tensor 视图承担。
<!-- cannbot:related:end -->
