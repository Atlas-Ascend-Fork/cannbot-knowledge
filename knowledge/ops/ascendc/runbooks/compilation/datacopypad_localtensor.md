---
type: "Runbook"
title: "DataCopyPad 无匹配重载 LocalTensor 实参不一致"
description: "Ascend950（dav-3510）上 scatter kernel 把 reduce/CopyOut 缓冲声明为 LocalTensor<int8_t>、而 updates 队列产出 LocalTensor<T>，bisheng 编译报 no matching function for call to DataCopyPad/ApplyScatterReduce 并附 candidate not viable: no known conversion from LocalTensor<float> to const LocalTensor<int8_t>。判别方法：LocalTensor<E> 模板实参为强类型、E 不一致无隐式转换，DMA 重载全部 not viable。"
tags: ["task.debugging", "topic.data_movement.data_copy", "topic.implementation"]
status: stable
sources: []
created_at: "2026-08-18T15:44:52Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["950"]
---

# DataCopyPad 无匹配重载 LocalTensor 实参不一致

## 现象

在用 ops-direct-invoke-flash 工作流为 Ascend950（dav-3510）实现 scatter 算子时，agent 写完第一版 kernel（含 reduce 与非 reduce 两条分支）后执行 `bash build.sh --install`。bisheng 编译 `scatter_kernel.cpp.o` 时对 `scatter_kernel<float>`、`scatter_kernel<half>`、`scatter_kernel<__bf16>`、`scatter_kernel<int32_t>`、`scatter_kernel<int64_t>` 五个模板实例化均报编译错误，整轮构建以 `gmake: *** [Makefile:91: all] Error 2` / `CalledProcessError: returned non-zero exit status 2` 失败。报错集中在 reduce 分支的 `DataCopyPad` 读回（行 196）、`ApplyScatterReduce` 调用（行 201）、`DataCopyPad` 写出（行 207）三处，以及 `ApplyScatterReduce` 形参声明（行 46）。

## 适用场景

- 工程形态：kernel 直调（ops-direct-invoke-flash，`AscendC::Reg` API 路线，单文件 `.cpp` 经 bisheng `--npu-arch=dav-3510` 编译）。
- API 路径：`AscendC::DataCopyPad` / `AscendC::DataCopyExtParams` / `AscendC::DataCopyPadExtParams<E>` / `AscendC::LocalTensor<E>` / `AscendC::GlobalTensor<E>::operator[]` / `AscendC::TQue::AllocTensor<E>`。
- 验证过的平台与 CANN 版本：Ascend950（NpuArch=dav-3510），trace 内 bisheng 编译目标为 dav-3510，CANN 工具链见 `/home/developer/Ascend/cann-9.0.0-beta.2` 与 `cann-9.1.0`。a3/a2 未在 trace 内上机验证，不得据推断写入 `platforms`。
- 适用粒度：`operator_family`——`LocalTensor<E>` 模板实参强类型约束与 `DataCopyPad` 重载解析规则跨算子通用，非 scatter 专属。
- 不适用或未验证场景：本卡仅诊断构建期 `no matching function` 报错的根因与判别方法；该 kernel 改写后的精度正确性在本 trace 内未验证通过，不能据本卡判断 scatter 实现精度正确。

## 判别方法

- **触发（trigger，tool_observed）**：kernel 构建失败，bisheng 报 `error: no matching function for call to 'DataCopyPad'` 与 `error: no matching function for call to 'ApplyScatterReduce'`，且紧随 `note: candidate function not viable: no known conversion from 'LocalTensor<float>' to 'const LocalTensor<int8_t>' for 2nd argument`。报错在 reduce 分支的 DMA 读回/写出与累加调用三处同时出现，对全部五个 dtype 实例化复现。
- **探针（probe，executable check）**：在构建日志中 grep `no matching function for call to 'DataCopyPad'\|'ApplyScatterReduce'`，再 grep 其后的 `note: candidate.*not viable.*LocalTensor<.*>.*LocalTensor<.*>`，定位每条 not-viable 候选里源 `LocalTensor<Ea>` 与目标 `LocalTensor<Eb>` 的模板实参对；随后回到源码逐个 `DataCopyPad` / `ApplyScatterReduce` 调用点，比对两侧 `LocalTensor<E>` 与对端 `GlobalTensor<E>::operator[]` 的元素类型 `E` 是否一致。判别结论：只要在同一个 DMA 调用里出现 `LocalTensor<int8_t>`（字节模式缓冲）与 `LocalTensor<T>` / `GlobalTensor<T>`（typed 队列/输出）混用，即命中本判别。
- **观测（observation，tool_observed）**：构建日志给出 `candidate function not viable: no known conversion from 'LocalTensor<float>' to 'const LocalTensor<int8_t>' for 2nd argument`——编译器明确拒绝从 `LocalTensor<float>` 到 `LocalTensor<int8_t>` 的实参传递，且所有重载候选均 not viable，最终落到 `no matching function`。
- **解释（interpretation，agent 根因分析）**：`AscendC::LocalTensor<E>` 的模板实参 `E` 是强类型，`E` 不同的 `LocalTensor` 之间不存在隐式转换；当 scatter kernel 把 reduce 累加缓冲与 CopyOut 缓冲按内置 scatter 的字节模式声明为 `LocalTensor<int8_t>`（`tempQueue.AllocTensor<int8_t>()`、`ApplyScatterReduce(const LocalTensor<int8_t>&, ...)`），而 updates 队列产出 `LocalTensor<T>`（`inQueueUpd.AllocTensor<T>()`，T=float/half/__bf16/int32_t/int64_t）时：(1) `ApplyScatterReduce` 的 `LocalTensor<int8_t>` 形参拒绝 `LocalTensor<T>` 实参；(2) `DataCopyPad` 在 `(LocalTensor<int8_t>, GlobalTensor<T>::operator[])` 读回与 `(GlobalTensor<T>::operator[], LocalTensor<T>)` 写出处，源/目标 `E` 与 typed 对端均不一致，重载候选全部 not viable。机制链：模板实参强类型 → 形参/实参 `E` 不一致 → 无隐式转换 → 重载候选全部 not viable → `no matching function`。这是解释（interpretation），由 agent 在 trace 内基于报错文本与 `LocalTensor<E>` 模板语义给出，非独立上板实测。

## 验证信号

本卡验证信号取自本 trace 内构建工具的实际输出（bisheng 编译 `bash build.sh --install`），从原始 trace 记录 drill-down 恢复。

- 首次构建失败：`scatter_kernel.cpp:196:17: error: no matching function for call to 'DataCopyPad'`、`:201:17: error: no matching function for call to 'ApplyScatterReduce'`、`:207:17: error: no matching function for call to 'DataCopyPad'`、`:46:24: note: candidate function not viable: no known conversion from 'LocalTensor<float>' to 'const LocalTensor<int8_t>' for 2nd argument`，对 float/half/__bf16/int32_t/int64_t 五个实例化均复现，`gmake: *** [Makefile:91: all] Error 2` / `CalledProcessError: returned non-zero exit status 2`（来源平台: Ascend950；证据等级: tool_observed）。

## 预防

- 在一个 kernel 内，对同一物理 UB 缓冲的 `LocalTensor<E>` 模板实参 `E` 必须与经 DMA 交互的对端 `GlobalTensor<E>::operator[]` 元素类型一致；不要把内置算子（如 `scatter/arch35`）的 `LocalTensor<int8_t>` 字节模式与 typed `LocalTensor<T>` 队列混用——`LocalTensor<E>` 是强模板类型，`E` 不同即不可隐式转换，`DataCopyPad` 重载会直接 not viable。
- `DataCopyPad` 的目标 `GlobalTensor<T>` 一律按元素偏移 `outputGm[dst_elem]` 索引（`operator[]` 返回 `T&`），不要按字节偏移 `outputGm[dst_elem * sizeof(T)]` 索引；后者在 `GlobalTensor<T>` 上会把 `T&` 起点错移，且与 `LocalTensor<T>` 源类型不一致。
- 当 Reg API 入口必须以 `(__ubuf__ float*)` 强转 `LocalTensor<T>` 物理地址时，把强转收敛在 `asc_vf_call` 包装函数内部一处，缓冲侧保持 typed `LocalTensor<T>`，避免 DMA 链路也卷入 reinterpret。

## 坏实践

- 首版 kernel 同时声明 `tempQueue`（`VECIN`）作 reduce 累加缓冲与 CopyOut 缓冲，且用 `AllocTensor<int8_t>()`——这是把内置 scatter 的字节模式机械搬到 typed kernel 的坏实践，直接造成 `LocalTensor<int8_t>` 与 `LocalTensor<T>` 在同一 DMA 调用里对撞，触发 `no matching function`。

## 误诊

- agent 在定位修复时一度考虑"把所有 `GlobalTensor` 改为 `GlobalTensor<uint8_t>`、全链按字节寻址"（reasoning 讨论了 `outputGm[elem_offset]` 需匹配 `LocalTensor` 元素类型，并设想用 `GlobalTensor<uint8_t>` + 字节偏移统一）。该方案虽能消除重载报错，但会把整条 offset/tiling 算术退化为字节级、并在 `LocalTensor<int8_t>` 与 typed updates 之间留下隐患；真正最小修复是让类型在 typed 侧自洽（`LocalTensor<T>` + 元素偏移），而非把全链强转为字节。此为 agent 推理过程，非实测信号，仅作误诊素材记录。

## 失效边界

- 本卡仅诊断构建期 `no matching function` 报错的触发条件与根因解释；不证明该 scatter kernel 的精度正确性——本 trace 在构建通过后随即结束，float32、dim=0、无 reduce 用例与 torch 参考不匹配（精度失败的具体数值与根因未追查，记入 reconstruction unknowns，不写入本卡验证信号）。
- reduce 分支以 `(__ubuf__ float*)` 强转 `LocalTensor<T>` 物理地址、用 float Reg API 处理 half/__bf16/int32_t/int64_t 数据的写法，在本 trace 内未跑任何 reduce 上板用例，其正确性未验证；按 B16 打包布局与 float 寄存器语义推断，存在 B16/float 布局错配风险（未验证，推断可迁移结论为：该 reduce 写法对 B16/int 类型大概率不正确，但本 trace 未证实）。
- a2、a3 同样使用 `AscendC::LocalTensor<E>` 强模板类型与 `DataCopyPad` 重载解析，本卡所述类型一致性约束应同样适用（未验证，推断可迁移）。

<!-- cannbot:related:start -->
## 相关

- [DataCopyPad](../../apis/simd_api/basic_api/memory_vector_compute/data_move/data_copy_pad_gm_to_ub.md)（`exemplifies`）：《DataCopyPad》说明将数据从GM非对齐搬运至UB，可根据需要自行填充数据。；《DataCopyPad 无匹配重载 LocalTensor 实参不一致》说明Ascend950（dav-3510）上 scatter kernel 把 reduce/CopyOut 缓冲声明为 LocalTensor<int8_t>、而 updates 队列产出 LocalTensor<T>，bisheng 编译报 no matching function for call to DataCopyPad/ApplyScatterReduce 并附 candidate not viable: no known conversion from LocalTensor<float> to const LocalTensor<int8_t>。判别方法：LocalTensor<E> 模板实参为强类型、E 不一致无隐式转换，DMA 重载全部 not viable。。二者在GM到UB非对齐搬入依赖Pad参数、32B最小DMA和LocalTensor/offset/rightPad合同，UB到GM方向的重载不同上存在可执行的直接衔接。
- [LocalTensor](../../apis/simd_api/basic_api/data_structures/local_tensor/local_tensor.md)（`exemplifies`）：该构建故障证明 LocalTensor<T> 的模板元素类型是强契约，float 与 int8_t 不能在 DataCopyPad/helper 重载间隐式转换；可用于定位 LocalTensor 类型不匹配。
- [LocalTensor构造函数](../../apis/simd_api/basic_api/data_structures/local_tensor/local_tensor_constructor.md)（`exemplifies`）：《LocalTensor构造函数》处理“LocalTensor构造函数。”。《DataCopyPad 无匹配重载 LocalTensor 实参不一致》明确“Ascend950（dav-3510）上 scatter kernel 把 reduce/CopyOut 缓冲声明为 LocalTensor<int8_t>、而 updates 队列产出 LocalTensor<T>，bisheng 编译报 no matching function for call to DataCopyPad/ApplyScatterReduce 并附 candidate not viable: no known conversion from LocalTensor<float> to const LocalTensor<int8_t>。判别方法：LocalTensor<E> 模板实参为强类型、E 不一致无隐式转换，DMA 重载全部 not viable。”，可直接用于核对LocalTensor 的默认/静态地址构造、LocalMemAllocator 构造路径及错误实参诊断。
- [DataCopyPad UB→GM 四参调用导致编译失败](datacopypad_ub_to_gm_has_no_pad_params.md)（`related`）：UB→GM 卡明确该方向没有 PadExtParams；结合本卡的元素类型一致性，可同时核对 DataCopyPad 的方向重载和 LocalTensor<T> 实参。
- [DataCopyPad 五参编译失败—LocalTensor 子视图替代偏移](datacopypad_offset_via_tensor_subview.md)（`related`）：两卡共同给出 DataCopyPad `no matching function` 的分诊边界：一个由第五个偏移实参造成，另一个由 LocalTensor/GlobalTensor 元素类型不一致造成。
- [DataCopyPad 加载缺少 Pad 参数导致编译失败](datacopypad_gm_to_ub_requires_pad_params.md)（`related`）：GM→UB 卡给出必须携带 PadExtParams 的方向签名，本卡补充签名匹配后 LocalTensor<T> 与 GlobalTensor<T> 的 T 仍须一致。
- [DataCopy尾chunk非32B对齐触发ERR99999](datacopy_chunk_32b_err99999.md)（`related`）：《DataCopy尾chunk非32B对齐触发ERR99999》说明Ascend C DataCopy 在 UB↔GM 方向要求 count*sizeof(T) 为 32 字节对齐，否则搬运量对 32B 向下取整。当纯搬运算子尾 chunk 的实际元素数不满足 32B 对齐时，UB→GM 写方向触发 ERR99999、GM→UB 读方向静默丢尾部数据。判别方法：尾部元素数*sizeof(T)%32!=0 即命中。；《DataCopyPad 无匹配重载 LocalTensor 实参不一致》说明Ascend950（dav-3510）上 scatter kernel 把 reduce/CopyOut 缓冲声明为 LocalTensor<int8_t>、而 updates 队列产出 LocalTensor<T>，bisheng 编译报 no matching function for call to DataCopyPad/ApplyScatterReduce 并附 candidate not viable: no known conversion from LocalTensor<float> to const LocalTensor<int8_t>。判别方法：LocalTensor<E> 模板实参为强类型、E 不一致无隐式转换，DMA 重载全部 not viable。。二者在DataCopy尾chunk错误由有效字节数非32B倍数触发，DataCopyPad的逐行、stride、padding和最小DMA卡给出修复边界上存在可执行的直接衔接。
- [TBuf 不能直接传给 LocalTensor 形参](tbuf_gets_typed_localtensor_before_helper_call.md)（`related`）：两卡的编译器诊断都已完成模板推导，真正失败在对象类型契约：TBuf 必须先 Get<T>() 成 LocalTensor，而不同 LocalTensor<E> 之间也没有隐式转换。
<!-- cannbot:related:end -->
