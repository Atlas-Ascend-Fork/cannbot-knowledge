---
type: Runbook
title: bf16 转换落 AI_CPU：改 AI core 位级 cvt
description: 310P 上 torch_npu 的 bf16 转换派发到 AI_CPU（Cast10），每次固定开销约主 kernel 单次的一成；改用 AI core 位级 cvt kernel 并批处理对齐尾部即可消除。
tags: [task.optimization, topic.compute.elementwise.type_conversion, topic.implementation.api_layer.aicpu_api]
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/8746f7ced6cef47e3fd7abd64c0eb827e28e2b56/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/type_conversion/Cast.md
    role: constraint
created_at: "2026-10-28T09:46:50Z"
updated_at: "2026-11-03T02:48:57Z"
platforms: ["310p"]
---

# bf16 转换落 AI_CPU：改 AI core 位级 cvt

## 现象

在 310P（dav-m200）上优化分块门控前向 kernel。主 kernel 已经写完后，用 msprof 单例 profile 逐算子 breakdown，主 kernel 之外冒出一个来历不明的算子：

```
 cnt  占整轮 task    vec      mac       m1       m2       m3 blk name
   5   约 78%       40.0%     0.9%     1.3%    33.3%     5.8%   8 chunk_kda_310p
   5   约 14%         0         0        0        0        0     2 Cast10
  20   约 7%        83.0%       0        0      3.8%     2.8%   8 cvt_310p
```

（占比按 5/5/20 次迭代的求和折算）

`Cast10` 的 `blk=2`、全部 pipe 列为 0——不是 AI core 的算子。把 `op_summary*.csv` 按算子名过滤，逐行形态是：

```
Cast10 | AI_CPU | <duration> | 2 | <in-shape> | DT_BF16 | <out-shape> | FLOAT | N/A
Cast10 | AI_CPU | <duration> | 2 | ...        | DT_BF16 | ...       | FLOAT | N/A
（共 5 行：同一路 bf16->f32 小张量转换，首调更慢，其后稳定在同一量级）
```

即：一个**极小的** bf16→f32 转换（门控标量 beta，按 (t,h) 每行一个数），被派发到 **AI_CPU**，单次耗时约为主 kernel 单次耗时的 **0.10x**（首调更差，约 0.37x）。同时 host 侧还有若干次 fp16/bf16 张量转换走 AI core（`cvt_310p`，blk=8）。

## 适用场景

- 工程形态：Kernel 直调（自定义 AscendC 算子 + torch 张量 staging 的混合 host）。
- API 路径：`torch::Tensor::to(torch::kFloat32)` / `.to(torch::kHalf)` 等 torch_npu dtype 转换；替代品是自研 AI core cvt kernel（本例 `cvt_310p`，裸 `aclrtlaunch` 启动）。
- 验证过的平台与 CANN 版本：310P（dav-m200 / DAV_2002）+ CANN 9.1.0。**310P 无原生 bf16 计算**，bf16 相关转换最容易落到 AI_CPU。
- 适用粒度：platform_wide（平台 dtype 矩阵性质）。
- 路线优先级：recommended_fastpath。
- 明确不适用或未验证场景：A2/A3 上是否有 AI core 的 bf16 cast 实现（未验证，推断在原生支持 bf16 的平台上该问题不成立）；未验证超大张量时 AI_CPU 版本是否被切分成多块从而摊薄固定开销。

## 根因

310P（dav-m200）的 cube 只支持 fp16、**没有原生 bf16**。torch_npu 在 310P 上把 bf16 与 f16/f32 之间的转换回退到 **AI_CPU** 执行（profile 里是 `Cast10`，`Task Type=AI_CPU`、`Block Num=2`）。

AI_CPU 的执行特征是**固定启动开销占绝对主导**：本例的张量只有 (t,h) 规模的几千个元素，转换本身的计算量可以忽略，但每次调用都要付一份跨引擎调度成本。profile 显示这份成本约为主 kernel 单次耗时的 **0.10x**，而首调高达 0.37x（首次调度路径更慢）；5 次迭代里这个 cast 总计占整轮 task 总时长的 **约 14%**。

也就是说：**开销与数据量无关、纯粹是“派发到 AI_CPU”这件事本身的代价**（该机制为推断，见“误诊”）。这解释了为什么“这么小的张量”能进主 caliber 前十的算子榜——主 caliber 统计的是全部 task 的 duration 之和，AI_CPU task 同样计入。

## 解决配方

方向：把 bf16 转换从 torch_npu 的 cast 换成**自己在 AI core 上做的位级转换**，并顺手消掉原来“非对齐尾段回退到 torch cast”的实现——那个回退本身又引入一次 AI_CPU cast。

`before`（host 里的通用 cvt 启动函数：2B 元素按 32 元素对齐，尾段用 torch 的 `copy_` 精确补）：

```cpp
    const int64_t n32 = n & ~static_cast<int64_t>(31);
    if (n32 > 0) {
        const uint32_t ret = aclrtlaunch_<generic>_cvt(
            8, stream, src.data_ptr(), dst.data_ptr(), offTab.data_ptr(),
            static_cast<int32_t>(n32), mode);
        TORCH_CHECK(ret == 0, "<generic>_cvt launch failed, error=", ret);
    }
    if (n32 < n) {   // 非对齐尾段 torch 精确补
        dst.view(-1).narrow(0, n32, n - n32)
            .copy_(src.view(-1).narrow(0, n32, n - n32));
    }
    return true;
}
```

`after`（源码逐字：2B 模式按 16 元素（32B 整块）对齐，尾段走第二次裸 launch——**该尾段机制实测证伪**，保留源码原貌仅为记录实际形态，可用性结论以“失效边界”的对照矩阵为准）：

```cpp
    // 2B 元素模式对齐 16 元素（32B 整块）; 尾段 16 元素 = 恰一 32B 块,
    // 第二次裸调用精确补（torch bf16 cast 走 aicpu 固定开销显著, 禁用其尾段回退）
    const bool twoByte = (mode == 0 || mode == 1 || mode == 5);
    const int64_t aln = twoByte ? 16 : 8;
    const int64_t n32 = n & ~(aln - 1);
    if (n32 > 0) {
        const uint32_t ret = aclrtlaunch_<generic>_cvt(
            8, stream, src.data_ptr(), dst.data_ptr(), offTab.data_ptr(),
            static_cast<int32_t>(n32), mode);
        TORCH_CHECK(ret == 0, "<generic>_cvt launch failed, error=", ret);
    }
    if (n32 < n) {   // 非对齐尾段（2B 模式恰 16 元素 = 1×32B 块）
        const int64_t srcEs = (mode == 2) ? 4 : 2;   // 源元素字节
        const int64_t dstEs = (mode == 5) ? 4 : 2;   // 目的元素字节
        const uint32_t ret = aclrtlaunch_<generic>_cvt(
            8, stream, static_cast<char*>(src.data_ptr()) + n32 * srcEs,
            static_cast<char*>(dst.data_ptr()) + n32 * dstEs,
            offTab.data_ptr(), static_cast<int32_t>(n - n32), mode);
        TORCH_CHECK(ret == 0, "<generic>_cvt tail launch failed, error=", ret);
    }
    return true;
}
```

**尾段偏移必须按源/目的各自的元素字节数分侧计算**（上方 after 代码为源码逐字）：该 kernel 支持的 mode 里输入、输出元素宽度并不总相等——

| mode | 转换 | 源元素 | 目的元素 | 尾段源偏移 | 尾段目的偏移 |
| --- | --- | --- | --- | --- | --- |
| 0 | bf16→f16 | 2B | 2B | `n32 * 2` | `n32 * 2` |
| 1 | f16→bf16 | 2B | 2B | `n32 * 2` | `n32 * 2` |
| 2 | f32→bf16 | 4B | 2B | `n32 * 4` | `n32 * 2` |
| 5 | bf16→f32 | 2B | 4B | `n32 * 2` | `n32 * 4` |

若像等宽直觉那样两侧都写 `n32 * 2`：mode 5（bf16→f32）n=17 时 n32=16，目的指针只偏 32B，尾段会从第 8 个输出元素起写，覆盖前段结果；mode 2（f32→bf16）则是源侧读错位。host 侧也未校验 mode 与 src/dst dtype 的对应关系，mode 传错无护栏，复用时须自行保证。

代码注释 `尾段 16 元素 = 恰一 32B 块`、`第二次裸调用精确补` **表述有误**：前者说的其实是 2B 模式的对齐粒度是 16 元素（1×32B 块），尾段实际长度是 `n - n32`（2B 模式 1~15 元素、4B 模式 1~7 元素），并非恒 16 元素；后者与实测相悖（尾段 launch 触发即异常，见“失效边界”）。源码下次修订时应删除/改写这两处注释，本文按原貌保留并以此处更正为准。

调用侧把 beta 的 `beta.to(torch::kFloat32)` 换成 mode 5（bf16 → f32 的**位型精确展开**：bf16 的 16 位就是 f32 的高 16 位，低位补零，无舍入）：

```cpp
        auto dst = torch::empty({Tp * 16}, f32);
        auto dstN = dst.narrow(0, 0, T * 16);
        cvt_launch(beta.reshape({-1}), dstN, 5, cvtStream);
```

三条要点：

1. **2B 元素（bf16/f16）的搬运粒度是 16 元素 = 32B**，对齐算错就会落到“尾段 torch 补”，等于把 AI_CPU cast 又请回来；
2. 尾段的“第二次裸 launch”机制**实测不可用**（见“失效边界”的对照矩阵：尾段一旦触发，读侧 MTE 命令 burst num 非法直接 aicore 异常）——正确姿势是调用方把规模凑整到对齐粒度（本算子 H=16 天然对齐），不要依赖尾段分支；
3. 同一 host 里其余 bf16/f16 widen 也统一走这个 cvt kernel，才能把 `Cast10` 从 profile 里彻底消掉。

## 设计决策

- 为什么自己做位级 cvt 而不是等 torch_npu 修？310P 无原生 bf16 是硬件事实，AI_CPU 回退是工具链的既定路径；自己做成 AI core kernel 是唯一可控解。
- 为什么 mode 5 能做到“精确”？bf16 的尾数只有 8 位，恰好是 f32 的高 16 位；`bf16→f32` 只需把 16 位搬到高半字、低 16 位补 0，**零舍入**。反过来 f32→bf16 才需要 RNE，所以该 kernel 的不同 mode 精度性质不同，mode 5 可以放心当“无损加宽”用。
- 为什么顺带批处理多次 cvt？每次裸 launch 有固定 launch 开销，host 侧本来就有 q/k/v/o/beta 五路转换，合并成一轮 + 一次 device sync 比逐路 sync 便宜。
- 被放弃的候选：把 beta 留在 bf16 由主 kernel 原位加宽（可省掉这一路 cvt）。轨迹后段实现为“in-kernel raw ingest”，**未构建未验证**。

## 系统信息

- 平台：310P（dav-m200 / DAV_2002），CANN 9.1.0，8 核；UB 240KB。
- 相关文件：`kernel/<generic>_cvt.cpp`（`cvt_310p`，mode 0=bf16→f16、1=f16→bf16、2=f32→bf16、5=bf16→f32）；`host/<generic>_host.cpp`（`cvt_launch` 与 staging）；`kernel/<generic>_chunk_kda.cpp`（消费 f32 平铺 beta 的主 kernel）。
- 测量：单例诊断用 `msprof --output=... --ai-core=on --task-time=on --ascendcl=on python3 _wrapper.py`，再解析 `mindstudio_profiler_output/op_summary*.csv`；主 caliber 用 `bash msprof_profile_run.sh --compare --warm-up=3 --device=<id>`。

## 性能影响

参照路线：**同一 host 里被替换掉的 torch_npu bf16↔f16/f32 cast（AI_CPU `Cast10`）**，来源平台 310p。

- 单次 AI_CPU cast 的耗时 ≈ 该算子主 kernel 单次耗时的 **0.10x**（首调 ≈ 0.37x）；
- 换成 AI core cvt 后，每次转换的耗时降到**同一个 cvt kernel 在 AI core 上的常规量级**（profile 中该 kernel 每次约为主 kernel 的 0.02x）；
- 5 次迭代合计，被替换掉的 cast 占整轮 task 总时长的 **13.8%**，替换后该算子在 op_summary 中消失；
- 精度未退化：位级展开（mode 5）无舍入；本算子最终全量精度 40/40 通过（见验证信号）。
- 该优化属 recommended_fastpath，不存在“精度换性能”的取舍。

## 完整代码

mode 5 的位级展开在 kernel 侧的实现约定（供复用时的语义对照）：

```cpp
// cvt 的 mode 5 分支：bf16 → f32 位型精确展开（<<16, 零舍入）
//   bf16 位型 b15..b0  →  f32 位型 b15..b0 0000...0
//   与 mode 0/1/2 共用同一 offset 表（按 dtype 决定搬运粒度与符号扩展）
```

（该 kernel 的完整源码不在本轨迹的读取范围内，卡内只保留 host 侧的完整调用/对齐逻辑，即上文 `after`。）

## 预防

- 在 310P 上看到 profile 里出现 `Task Type=AI_CPU` 的算子（尤其 `Cast`/`Cast10`），先当作“固定开销税”处理：它计入主 caliber，且与张量大小无关（该因果为推断）。
- host 侧逐路检查是否还有 `.to(kFloat32)` / `.to(kHalf)` / `.float()` / `.half()` 落在 bf16 张量上——这些都会回退。
- 自研 cvt 的**对齐粒度按元素字节数分别处理**（2B→16 元素、4B→8 元素），尾段偏移按源/目的元素字节数分侧计算（`n32 * srcEs` / `n32 * dstEs`）。
- **入口护栏**：在校验 mode↔dtype 对应（见上文 mode 表）之后，**保守地要求输入与输出的总字节数都能被 32 整除**（`(n*srcEs)%32==0 && (n*dstEs)%32==0`；对本 kernel 四个 mode 等价于 `n % 16 == 0`）。只按读侧对齐（如 mode 2 的 `n%8==0`）会放行反例：n=24 读侧 96B 对齐通过、写侧 48B 非 32B 倍丢尾 8 元素（见"失效边界"矩阵）。不满足的长度应在启动自研 kernel 前拒绝或转入已验证的回退路径（CPU/torch 补）；本例 host 未做这些校验，复用必须补上。
- 尾段处理只推荐两条路：**凑整**（pad 到对齐粒度）或 **CPU/torch 补尾段**（接受引回一次 AI_CPU cast）；既不要用第二次裸 launch（实测必异常），也不要用 before 版本的 `copy_` 兜底（同样是把 AI_CPU cast 请回来）。

## 验证信号

来源：分块门控前向 kernel（310P）优化会话中，单例 msprof profile 的算子级 breakdown。以下均为本轨迹内的工具输出。

- 替换前：op_summary 中 `Cast10` 出现 5 次、`Task Type=AI_CPU`、`Block Num=2`，5 次迭代合计占整轮 task 总时长的约 14%；单次与主 kernel 单次耗时之比 0.10x（首调 0.37x）（来源平台：310P；证据等级：tool_observed）。
- 替换后同一 case 的 op_summary：`Cast10` **消失**，`cvt_310p` 由 20 次升到 25 次（每迭代 5 路），整轮 task 总时长降到替换前的约 0.44x（来源平台：310P；证据等级：tool_observed）。
- 该 case 的主 kernel 同期另有一次架构级重写（另有卡片记录），因此“约 0.44x”是**两者叠加**的结果，不能单独归给本卡；本卡可单独归因的是“`Cast10` 从其 profile 中消失 + 该路转换改为 AI core 执行”（来源平台：310P；证据等级：tool_observed）。
- 精度未退化：终版 `.so` 全量精度 40/40 通过（来源平台：310P；证据等级：tool_observed）。
- 尾段对照矩阵（310P chip 3，逐 case 独立进程）：56 个 (mode, n) 组合中，mode 0/1/5 仅 16 倍 n PASS、其余 aicore 异常（burst num 非法）；mode 2 的 PASS 集为 {8,16,32,48}——其中 n=8 属"单次不足 32B 的写反而完整落盘"的边界形态，不作为放行依据（放行条件见"预防"的双侧 32B 整除护栏）；非 8 倍 n 异常，n=24 写侧丢尾 8 元素（来源平台：310P；证据等级：tool_observed）。

## 失效边界

- 若平台原生支持 bf16（A2/A3 等），torch 的 cast 可能已经落 AI core，本卡结论不适用（未验证，推断）。
- 若转换的张量足够大，AI_CPU 版本可能被分块摊薄固定开销，收益比例会下降（未验证）。
- 自研 cvt kernel 需要额外的 offset 表与一次额外 launch；当 host 侧只有**一路**极小的转换时，用它替换 torch cast 的净收益未必为正（本例有 5 路，摊薄后才划算）。
- **尾段 launch 路径实测不可用（310P chip 3 逐 case 独立进程对照矩阵）**：本例 40 个精度用例各路规模均为 16 元素对齐（H=16，逐例核对 q/beta numel），尾段分支从未触发，40/40 通过不构成对它的证据。对照矩阵实测 n ∈ {1,2,7,8,9,15,16,17,24,31,32,33,47,48} × mode ∈ {0,1,2,5}（参考值 torch `.to()` 位级比较）：
  - **mode 0/1/5（2B 元素）**：n 为 16 的倍数（16/32/48）全部 PASS；其余全部 n 触发 `aicore exception 0x26, "The burst num of the mte command is incorrect"`（尾段读侧 2B×m < 32B，MTE 命令 burst num 非法，进程级失败，不是静默错值）。
  - **mode 2（4B 元素）**：n 为 8 的倍数（8/16/32/48）PASS；n 非 8 倍数同上异常；**n=24 出现第三种形态**——无尾段 launch（24%8==0）但写侧 24×2B=48B 非 32B 整倍，尾 8 个元素丢失（bad=8/24，与 [DataCopy count 按 32B 截断](../compilation/ol_167_datacopy_count_form_silently_truncates_non_32b_ali.md) 的写侧语义一致）；而单次不足 32B 的写（n=8，16B）反而完整落盘。
  - 结论：尾段 < 1 个完整 32B 块时该机制必然异常（尾段上限 2B 模式 15 元素 / 4B 模式 7 元素，恒 < 32B），**尾段分支等于死路**；放行条件按"预防"的双侧 32B 整除护栏（等价 `n % 16 == 0`，mode 2 的 n=24 即读侧对齐但写侧丢尾的反例），凑不整的长度拒绝启动或走 CPU/torch 补（代价是引回一次 AI_CPU cast）。（来源平台：310P；证据等级：tool_observed）
- 未决项：把 beta 转换彻底省掉（改为主 kernel 原位摄取）——代码已写但未构建未验证，收益方向明确、量级未测。

## 坏实践

- 用 `dst.view(-1).narrow(...).copy_()` 给“AI core cvt kernel”兜非对齐尾段——这正是 AI_CPU cast 的入口，等于优化白做。
- 只按 32 元素对齐处理所有 dtype（2B 元素实际是 16 元素一块），导致每次都走尾段回退。
- 在 host 侧对 bf16 张量随手 `.to(kFloat32)`（包括为“保险”而加的临时转换），把 AI_CPU 开销带进主 caliber。
- 指望“尾段再裸 launch 一次”兜住非对齐规模：尾段恒小于 1 个 32B 块，实测触发即 aicore 异常，不是慢、是崩。

## 误诊

- 起初看到 `Cast10` 以为是主 kernel 内部的 Cast 指令统计口径问题；op_summary 的 `Task Type=AI_CPU` 与全零 pipe 列立刻否定了这一点。
- 曾怀疑是 `beta` 张量不连续导致 torch 走了慢路径；`.reshape({-1})` 已保证连续，且 AI_CPU 派发与连续性无关。
- 推断（非实测）：“AI_CPU 的开销与数据量无关、纯固定派发成本”——依据是同一算子在同一轮里首调 0.37x、其后稳定 0.10x，且张量极小；未做“放大张量看耗时是否变化”的对照。
