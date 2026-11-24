---
type: Optimization
title: 启动参数按值直传：删除设备侧 tiling GM 读与每调用 H2D
description: kernel 真正消费的 tiling 字段只有几个标量，却每次 launch 都付一遍设备侧 GM 结构体读（_nestedgetmaxseqlen 44 次串行标量 GM load；conj 4×u32 依赖加载 + 拷贝循环）与一遍 host 每调用 H2D。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/launch-arg-by-value-tiling-fetch-elimination.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

<!-- strategy-metadata
{
  "applicability": {
    "constraints": [
      "标量参数的首次使用有 arg 布局初始化竞态：CANN 9.1.0/ascend950 上内联 kernel 的参数首次使用可能以零值 args 早退（基线全指针 args 无此问题），且当标量参数 launch 紧邻一个 NPU cast kernel 时参数不送达；必须用一个可信的『发射屏障』把首次标量参数 launch 与其它 kernel 隔开",
      "屏障必须是常态路径而不是一次性握手：conj d002 的修复记录显示『入口切换预热协议（无害 1 元素恒等 launch 占领描述符）』无效，最终生效的是每次调用一个静态 12B staging H2D copy_；conj__v3 的生效形态是每 dtype 首次调用一次 dummy launch + stream synchronize 的惰性 warmup",
      "blockDim 必须改为从 GetBlockNum() 取（_nestedgetmaxseqlen 形态），不得再从 tiling 字段读，否则等于把刚删掉的依赖又加回来",
      "数据面逐字节不变：DataCopyPad 载荷、Reg Muls/Cast、逐字节语义必须与 champion 完全一致；若同时删除 TQue 框架（conj d002 形态），必须换成单 TBuf<VECCALC>（一次 InitBuffer，in=前半 / out=后半 32B 对齐）+ 显式最小 SetFlag/WaitFlag（MTE2_V/V_MTE3，多 tile 回路 MTE3_MTE2/MTE3_V），并为 VF 存储队列补 Reg::LocalMemBar<VEC_STORE,VEC_LOAD>（对齐 FlipAddcmul 模式）",
      "删除 host 每调用 H2D 的收益不计入 device Task Duration 决策口径（属 host 侧时延），不得用它支撑性能结论；微内核（1-2us 量级）必须用配对 ABBA msprof 裁决，不能用单次运行"
    ],
    "excluded_conditions": [
      "kernel 需要 tiling 结构体整体（大数组、尺寸随 shape 变化）时不适用：按值传参只适合可枚举的少数标量（本 run 只传 seqLen 或 3-4 个 u32 / 一个 12B 结构体）",
      "tiling 读已经不存在或已被别的机制摊销掉时没有可消除对象；把逐字节读换成更大粒度的读（MTE2 批量搬运）不等于本机制——本 run conj 主线的 index-scalar-bulk-mte2-tbuf 已证伪那条路（9.117→9.2092 回滚），本机制消除的是读路径本身",
      "blockDim 语义依赖 host 传入的 tiling 字段、无法用 GetBlockNum() 等价替代时不适用"
    ],
    "required_conditions": [
      "kernel 真正消费的 tiling 字段只有少数几个标量，其余是纯搬运开销：_nestedgetmaxseqlen 的 NestedGetMaxSeqlenCopyTiling（sizeof=44B）逐字节循环拷贝，kernel 只消费 ndim/dimSize[0..1]/blockDim；conj 的 ConjCopyTiling 只有 4 个 u32（12B）；conj__v3 只需 totalLength/blockLength/tileLength/mode",
      "构建/工具链支持 __global__ 签名中的非 GM_ADDR 值参数：本 run conj 走 <<<>>> 结构体按值传参、conj__v3 传 4×u32 标量、_nestedgetmaxseqlen 传 by-value seqLen；先例为 CANN 9.1.0 的 Pto_prefetch.hpp:90（指针 + by-value uint64 total_elems，设备侧 get_block_num() 读核数）",
      "设备侧 tiling 读是每 launch 固定成本的可测分量：conj__v3 的 1-block 小 case（84B-32KB）scalar 0.96-1.08us 占 wall 65-70% 且与数据量无关；_nestedgetmaxseqlen 的 aiv_scalar_time 1.177/1.468/1.188us 占 aiv_total 1.340/2.000/1.305us 的 74-90%",
      "host 侧每调用都存在 tiling tensor 构造 + H2D：conj pybind11.cpp 的 tiling_cpu.to(device)（16B）、_nestedgetmaxseqlen pybind11.cpp:49-56 的 torch::empty + 阻塞 H2D —— 删除它对 device Task Duration 中性偏正，对 e2e 是额外收益"
    ]
  },
  "classification": "validated_strategy",
  "created": "2026-09-18",
  "evidence": [
    {
      "operator": "conj",
      "operator_class": "elementwise",
      "precision": "10/10 PASS（连续 3 次全量 exit 0，MERE/MARE 全 0）",
      "run_id": "<run-id>",
      "speedup": 1.2186,
      "status": "accepted"
    },
    {
      "operator": "_nestedgetmaxseqlen",
      "operator_class": "elementwise",
      "precision": "20/20 PASS bit-exact int64 scalar",
      "run_id": "<run-id>",
      "speedup": 1.2106,
      "status": "accepted"
    },
    {
      "operator": "conj__v3",
      "operator_class": "elementwise",
      "precision": "10/10 PASS（MERE/MARE 全 0）",
      "run_id": "<run-id>",
      "speedup": 1.1558,
      "status": "accepted"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "aiv-scalar-fixed-overhead",
      "per-launch-gm-tiling-fetch",
      "host-per-call-tiling-h2d",
      "tque-handshake-fixed-cost",
      "scalar-arg-first-use-layout-race"
    ],
    "dtypes": [
      "bf16",
      "fp16",
      "fp32"
    ],
    "pattern": "launch-arg-by-value-tiling-fetch-elimination",
    "reduce_mode": "",
    "structure": [
      "by-value-launch-scalar-args",
      "gm-tiling-read-deleted",
      "host-per-call-h2d-deleted",
      "getblocknum-instead-of-tiling-blockdim",
      "queueless-single-tbuf-direct-path",
      "emission-barrier-workaround"
    ]
  },
  "generality": "op_class",
  "id": "LAUNCH-ARG-BY-VALUE-TILING-FETCH-ELIMINATION",
  "implementation_steps": [
    "枚举 kernel 真正消费的 tiling 字段，把它们从 GM 结构体提升为 __global__ 的 by-value 标量参数：_nestedgetmaxseqlen 传 seqLen（先例为 CANN Pto_prefetch.hpp:90 的混合指针 + by-value uint64 参数）、conj d002 传 (GM_ADDR x, GM_ADDR y, uint32_t totalLength, uint32_t blockLength, uint32_t tileLength)、conj__v3 把 ConjTiling 结构体整体按值传入",
    "kernel 内删除 tiling GM 读与 tiling_ 成员：_nestedgetmaxseqlen 删 NestedGetMaxSeqlenCopyTiling 的 44 字节逐字节拷贝（44 次串行标量 GM load）与 GM tiling 入参；conj d002 删 ConjCopyTiling 的 12B GM 逐字节标量读；conj__v3 删 ConjCopyTiling 的 4×u32 GM 依赖加载与结构体拷贝循环；守卫改读 GetBlockNum()",
    "host 侧删除每次调用的 tiling tensor 构造与 H2D：_nestedgetmaxseqlen 删 pybind11.cpp:49-56 的 torch::empty + 阻塞 H2D；conj 删 pybind11.cpp 的 tiling tensor 构造与 H2D、改为构造栈结构/标量直接进 launch；conj__v3 删 tiling_cpu/tiling_npu 张量与每次调用 16B H2D",
    "为标量参数首用竞态加发射屏障，二选一：每 dtype 首次调用一次 dummy launch + stream synchronize（conj__v3 的惰性 warmup），或每次调用一个小的静态 H2D staging copy_（conj d002 的每调用 12B staging，历史上 champion 的 tiling H2D 恰好充当同一屏障）",
    "若同时删除 TQue 框架（conj d002 形态）：换成单 TBuf<VECCALC> + 显式最小 SetFlag/WaitFlag 事件对，并补 Reg::LocalMemBar<VEC_STORE,VEC_LOAD>；最后以 20/20 或 10/10 精度门 + 配对 ABBA msprof 验收，微内核需按噪声地板门禁用配对裁决"
  ],
  "intent": "消除每次 launch 都要付的 tiling 获取成本：kernel 只消费少数几个标量，却仍要付一遍设备侧 GM 结构体读（_nestedgetmaxseqlen 44 次串行标量 GM load；conj 4×u32 依赖加载 + 拷贝循环）与一遍 host 侧每调用 H2D；把这些标量改成 launch 按值参数后，读路径与 H2D 一起消失，blockDim 可直接从 GetBlockNum() 取。",
  "mechanism": "launch-arg-by-value-tiling-fetch-elimination：把 tiling 通道从『host 建张量 → H2D → 设备读 GM 结构体』整条换成 launch 值参数。_nestedgetmaxseqlen 把唯一的形状标量 seqLen 放进 __global__ 签名（可行性先例：CANN Pto_prefetch.hpp:90 传指针 + by-value uint64 total_elems，设备侧 get_block_num() 读核数），删掉 NestedGetMaxSeqlenCopyTiling（kernel/nestedgetmaxseqlen_kernel.h:12-20）的 44 字节逐字节 GM 拷贝循环与 GM tiling 入参，blockDim 守卫改读 GetBlockNum()，host 侧 pybind11.cpp:49-56 的每调用 tiling tensor + 阻塞 H2D 一并消失。conj 的两个变体走同一条路但覆盖面更大：d002 在删 tiling GM 读的同时把 TQue/TPipe 框架也剥掉——单 TBuf<VECCALC> 一次 InitBuffer（in=前半 / out=后半 32B 对齐），显式 SetFlag/WaitFlag(MTE2_V/V_MTE3，多 tile 回路 MTE3_MTE2/MTE3_V)，尾部 Reg::LocalMemBar<VEC_STORE,VEC_LOAD> 对齐 FlipAddcmul 模式，入口签名变为 (GM_ADDR x, GM_ADDR y, uint32_t totalLength, uint32_t blockLength, uint32_t tileLength)；conj__v3 把整个 ConjTiling 结构体按值传入并删除 ConjCopyTiling 的 4×u32 GM 依赖加载与 host 每次调用 16B H2D。三者的共同陷阱是标量参数的首次使用竞态：CANN 9.1.0/ascend950 上内联 kernel 参数首次使用会以零值 args 早退（全指针 args 的基线没有该问题），且当标量参数 launch 紧邻一个 NPU cast kernel 时参数不送达（失败输出 = 未写入的回收 cast-temp 字节，100% 匹配）。生效的屏障形态有两类：conj d002 的每调用 12B 静态 staging H2D copy_，conj__v3 的每 dtype 首用惰性 warmup。数据面（DataCopyPad 载荷、Reg Muls/Cast、逐字节语义）在三者中均与 champion 完全一致。",
  "name": "启动参数按值直传：删除设备侧 tiling GM 读与每调用 H2D",
  "operator_class": "elementwise",
  "operator_scope": "形状/切分信息已全部在 host 侧算完、设备侧只需少数标量即可执行的一次性（非流式）kernel；典型如逐元素恒等/映射算子（conj）、只输出少量元数据的 microkernel（_nestedgetmaxseqlen 是纯 metadata 微内核：1 block、不读输入、写 2 个掩码寄存器与一次 8B DataCopyPad）、以及单 tile 直通路径的元素级 kernel（conj 的 queueless 形态）",
  "principle": "tiling 的存在意义是把 host 算出的形状/切分信息交给 kernel；当 kernel 只需要少数几个标量时，GM 结构体 + host H2D 这条通道本身就是固定成本。设备侧要为一次暴露延迟的 GM 读构造地址并串行拷贝（_nestedgetmaxseqlen 是 44 字节逐字节循环 = 44 次串行标量 GM load，而 kernel 只消费 ndim/dimSize[0..1]/blockDim），host 侧每次调用都要建张量并做一次 H2D。launch 参数通道本来就能传值，把标量放进 __global__ 签名即可让运行时在 launch 时随描述符下发，设备侧不再有『读』这个动作——省掉的不只是字节数，整条『地址构造 → GM 读等待 → 拷贝循环』的依赖链都不存在了。这条机制与『换更有吞吐的读法』方向正交且更彻底：后者（把逐字节读换成 MTE2 批量搬运，本 run 的 index-scalar-bulk-mte2-tbuf）已被证伪回滚（9.117→9.2092us），因为问题不是读得慢，而是根本不需要读。conj 的 queueless 变体进一步说明同一杠杆可以延伸到每核的框架固定链：TQue/TPipe 的 Alloc/EnQue/DeQue/Free 与 2×InitBuffer 也是每个 launch 都要付一次的固定标量成本，删掉它把单 tile 路径的多 tile 队列编排退化成单 TBuf + 最小事件对。",
  "related_anti_patterns": [
    "microkernel-noise-floor-measurement-gate"
  ],
  "risks": [
    "scalar-arg 首用竞态是主要修复来源：conj d002 消耗 3 次精度修复（LocalMemBar + FetchEventID 事件 id→无效；入口切换预热协议→无效，且 tileLength=1 恒等 warmup 触发 device error 507035 后改用正式 tile；最终定位到『标量参数 launch 紧邻 NPU cast kernel 时参数不送达，失败输出=未写入的回收 cast-temp 字节 100% 匹配』，改用静态 12B 每调用 H2D 发射屏障后连续 3 次全量通过）；conj__v3 同样消耗 3 次精度修复（结构体按值→无效、参数前置重排→无效、首用惰性 warmup→生效）",
    "该竞态会被相邻 kernel 的类型放大会掩盖：屏障的必要性依赖 launch 与相邻 cast kernel 的相对顺序，只有把屏障放在每次真实 launch 之前（或每 dtype 首次调用之前）才是稳定的；失败形态是零值 args 早退或写入未初始化的 cast-temp 字节，而非编译错误",
    "删除 TQue 后同步责任转移到手写事件：漏掉 VF 存储队列的 Reg::LocalMemBar<VEC_STORE,VEC_LOAD> 或事件 id 复用会造成间歇性精度失败而非编译错误（conj d002 的对齐对象是 FlipAddcmul 模式）",
    "blockDim 从 tiling 字段改读 GetBlockNum() 后需确认所有入口都改到；漏改的入口会以默认/零值核数静默跑错（blockDim=1 的 _nestedgetmaxseqlen 本来就是 host 侧设定，改动面小但仍需逐入口核对）",
    "删除每调用 H2D 的收益不计入 device Task Duration：可以记录为附带收益，但不得用于支撑性能结论；微内核（1.5-2.3us）落在 <50us 噪声地板内，必须按 microkernel-noise-floor-measurement-gate 先验卡用配对 ABBA 裁决",
    "TQue 直通路径的收益上界受先验卡约束：single-tile-tque-direct-path-limited-gain 给出的上界是 0.1-0.6us，若本次收益主要来自标记读删除而非框架剥离，删框架部分可能低于预期"
  ],
  "slug": "launch-arg-by-value-tiling-fetch-elimination",
  "summary": "kernel 真正消费的 tiling 字段只有几个标量，却每次 launch 都付一遍设备侧 GM 结构体读（_nestedgetmaxseqlen 44 次串行标量 GM load；conj 4×u32 依赖加载 + 拷贝循环）与一遍 host 每调用 H2D。把这些标量改为 __global__ 按值 launch 参数、blockDim 改读 GetBlockNum()、删除 GM tiling 入参后，读路径与 H2D 一起消失；conj 的 queueless 变体还顺带剥掉 TQue/TPipe 框架改成单 TBuf + 显式最小事件对。实测 _nestedgetmaxseqlen 1.3786→1.1388us（1.2106x，20/20 bit-exact）、conj/queueless-launcharg-direct-path 2.5171→2.0655us（1.2186x，10/10 PASS）、conj__v3/kernel-arg-pass-by-value 2.1436→1.8547us（1.1558x，10/10 PASS）。主要代价是标量参数首用竞态，需配发射屏障。",
  "verification": {
    "correctness": [
      "_nestedgetmaxseqlen：20/20 bit-exact（criterion = bit-exact int64 scalar），build 一次通过、零修复预算；数据流为纯 metadata 微内核，从未读输入 x",
      "conj d002：10/10 PASS（连续 3 次全量运行 exit 0）；消耗 3 次精度修复后收敛——Reg::LocalMemBar<VEC_STORE,VEC_LOAD> + FetchEventID→无效，入口切换预热协议→无效（期间 tileLength=1 恒等 warmup 触发 device error 507035，改用正式 tile），最终静态 12B 每调用 H2D 发射屏障 + queueless kernel 复位后 3/3 全通过",
      "conj__v3：10/10 PASS（repairs 3：结构体按值→无效、参数前置重排→无效、每 dtype 首用惰性 warmup→生效）；数据面（DataCopyPad 载荷、Reg Muls/Cast、逐字节语义）与 champion 完全一致，identity 拷贝语义逐位不变",
      "conj d002 的数据面与 champion 完全一致（DataCopyPad 载荷、Reg Muls/Cast、逐字节语义都不变），改动只在参数传递方式与队列框架"
    ],
    "performance": [
      "_nestedgetmaxseqlen：形式化配对 ABBA 4 对（序列 B C C B B C C B，双目录重建 sealed snapshot，3 warmup + 10 measured × 20 shape = 260 launches/run，device 5）池化两级聚合 1.3786→1.1388us = 1.2106x（-17.39%），12 个 pair×case 单元全部候选更快，效应约为基线侧 run spread（0.9%）的 19 倍；B 侧 1.3786us 复现 champion 正式值 1.3771us（差 0.11%）；逐 dtype bf16 1.3626→1.1233、fp16 1.4073→1.1686、fp32 1.3663→1.1251",
      "conj d002：ABBA 两块（p1=A,B,B,A；p2=B,A,A,B，8 次独立 msprof 进程）4 对 ratio 0.821/0.818/0.8181/0.8254（区间宽 0.0074），两级聚合 2.5171→2.0655us = 1.2186x（-17.94%）；1 核 case 截距显著下降（case_01_fp32_512 1.564→1.1934、case_03_fp32_21 1.6529→1.2498、case_07_bf16_217 1.6594→1.197），fp32 262144@64 核 9.7354→9.2705us（-4.8%），中大 case -7~11%",
      "conj__v3：ABBA 平衡交替 x4 对（B A A B B A A B，双目录子进程交替加载）pair speedup 1.1473/1.1592/1.1555/1.1609，12 项 case 级配对全部 >1.0（1.0378-1.3575）无 shape 回退，dtype 组 geomean 2.1436→1.8547us = 1.1558x（-15.58%，超出保守预测区间 -5%~-10%）；fp32 2.3176→1.9974、fp16 2.1612→1.8561、bf16 1.9664→1.7209；case2（fp32 1MB）收益最小（1.0378），与其 MTE 带宽墙表象一致"
    ],
    "rollback_signals": [
      "标量参数首用竞态未被屏障覆盖：出现随相邻 kernel 变化的间歇性精度失败（零值 args 早退，或写入未初始化的回收 cast-temp 字节）",
      "删除 TQue 后手写事件/内存屏障不完备，VF 存储队列未落盘（需要 Reg::LocalMemBar<VEC_STORE,VEC_LOAD>）",
      "精度门未过而性能有收益：按契约整体回滚，不保留一半改动",
      "微内核（1-2us 量级）未做配对 ABBA 就下结论：落在 <50us 噪声地板内，必须按 microkernel-noise-floor-measurement-gate 用配对 msprof 裁决",
      "ABBA 配对 geomean 无显著下降（<5%）或任一精度用例失败且无性能收益，即整体回滚恢复 champion"
    ]
  }
}
-->

# 性能优化策略：启动参数按值直传：删除设备侧 tiling GM 读与每调用 H2D

kernel 真正消费的 tiling 字段只有几个标量，却每次 launch 都付一遍设备侧 GM 结构体读（_nestedgetmaxseqlen 44 次串行标量 GM load；conj 4×u32 依赖加载 + 拷贝循环）与一遍 host 每调用 H2D。把这些标量改为 __global__ 按值 launch 参数、blockDim 改读 GetBlockNum()、删除 GM tiling 入参后，读路径与 H2D 一起消失；conj 的 queueless 变体还顺带剥掉 TQue/TPipe 框架改成单 TBuf + 显式最小事件对。实测 _nestedgetmaxseqlen 1.3786→1.1388us（1.2106x，20/20 bit-exact）、conj/queueless-launcharg-direct-path 2.5171→2.0655us（1.2186x，10/10 PASS）、conj__v3/kernel-arg-pass-by-value 2.1436→1.8547us（1.1558x，10/10 PASS）。主要代价是标量参数首用竞态，需配发射屏障。

## 1. 原理

tiling 的存在意义是把 host 算出的形状/切分信息交给 kernel；当 kernel 只需要少数几个标量时，GM 结构体 + host H2D 这条通道本身就是固定成本。设备侧要为一次暴露延迟的 GM 读构造地址并串行拷贝（_nestedgetmaxseqlen 是 44 字节逐字节循环 = 44 次串行标量 GM load，而 kernel 只消费 ndim/dimSize[0..1]/blockDim），host 侧每次调用都要建张量并做一次 H2D。launch 参数通道本来就能传值，把标量放进 __global__ 签名即可让运行时在 launch 时随描述符下发，设备侧不再有『读』这个动作——省掉的不只是字节数，整条『地址构造 → GM 读等待 → 拷贝循环』的依赖链都不存在了。这条机制与『换更有吞吐的读法』方向正交且更彻底：后者（把逐字节读换成 MTE2 批量搬运，本 run 的 index-scalar-bulk-mte2-tbuf）已被证伪回滚（9.117→9.2092us），因为问题不是读得慢，而是根本不需要读。conj 的 queueless 变体进一步说明同一杠杆可以延伸到每核的框架固定链：TQue/TPipe 的 Alloc/EnQue/DeQue/Free 与 2×InitBuffer 也是每个 launch 都要付一次的固定标量成本，删掉它把单 tile 路径的多 tile 队列编排退化成单 TBuf + 最小事件对。

实现机制：launch-arg-by-value-tiling-fetch-elimination：把 tiling 通道从『host 建张量 → H2D → 设备读 GM 结构体』整条换成 launch 值参数。_nestedgetmaxseqlen 把唯一的形状标量 seqLen 放进 __global__ 签名（可行性先例：CANN Pto_prefetch.hpp:90 传指针 + by-value uint64 total_elems，设备侧 get_block_num() 读核数），删掉 NestedGetMaxSeqlenCopyTiling（kernel/nestedgetmaxseqlen_kernel.h:12-20）的 44 字节逐字节 GM 拷贝循环与 GM tiling 入参，blockDim 守卫改读 GetBlockNum()，host 侧 pybind11.cpp:49-56 的每调用 tiling tensor + 阻塞 H2D 一并消失。conj 的两个变体走同一条路但覆盖面更大：d002 在删 tiling GM 读的同时把 TQue/TPipe 框架也剥掉——单 TBuf<VECCALC> 一次 InitBuffer（in=前半 / out=后半 32B 对齐），显式 SetFlag/WaitFlag(MTE2_V/V_MTE3，多 tile 回路 MTE3_MTE2/MTE3_V)，尾部 Reg::LocalMemBar<VEC_STORE,VEC_LOAD> 对齐 FlipAddcmul 模式，入口签名变为 (GM_ADDR x, GM_ADDR y, uint32_t totalLength, uint32_t blockLength, uint32_t tileLength)；conj__v3 把整个 ConjTiling 结构体按值传入并删除 ConjCopyTiling 的 4×u32 GM 依赖加载与 host 每次调用 16B H2D。三者的共同陷阱是标量参数的首次使用竞态：CANN 9.1.0/ascend950 上内联 kernel 参数首次使用会以零值 args 早退（全指针 args 的基线没有该问题），且当标量参数 launch 紧邻一个 NPU cast kernel 时参数不送达（失败输出 = 未写入的回收 cast-temp 字节，100% 匹配）。生效的屏障形态有两类：conj d002 的每调用 12B 静态 staging H2D copy_，conj__v3 的每 dtype 首用惰性 warmup。数据面（DataCopyPad 载荷、Reg Muls/Cast、逐字节语义）在三者中均与 champion 完全一致。

## 2. 性能问题模式

- 优化目标：消除每次 launch 都要付的 tiling 获取成本：kernel 只消费少数几个标量，却仍要付一遍设备侧 GM 结构体读（_nestedgetmaxseqlen 44 次串行标量 GM load；conj 4×u32 依赖加载 + 拷贝循环）与一遍 host 侧每调用 H2D；把这些标量改成 launch 按值参数后，读路径与 H2D 一起消失，blockDim 可直接从 GetBlockNum() 取。
- 适用数据流：形状/切分信息已全部在 host 侧算完、设备侧只需少数标量即可执行的一次性（非流式）kernel；典型如逐元素恒等/映射算子（conj）、只输出少量元数据的 microkernel（_nestedgetmaxseqlen 是纯 metadata 微内核：1 block、不读输入、写 2 个掩码寄存器与一次 8B DataCopyPad）、以及单 tile 直通路径的元素级 kernel（conj 的 queueless 形态）
- Feature signature：`{"bottleneck": ["aiv-scalar-fixed-overhead", "per-launch-gm-tiling-fetch", "host-per-call-tiling-h2d", "tque-handshake-fixed-cost", "scalar-arg-first-use-layout-race"], "dtypes": ["bf16", "fp16", "fp32"], "pattern": "launch-arg-by-value-tiling-fetch-elimination", "reduce_mode": "", "structure": ["by-value-launch-scalar-args", "gm-tiling-read-deleted", "host-per-call-h2d-deleted", "getblocknum-instead-of-tiling-blockdim", "queueless-single-tbuf-direct-path", "emission-barrier-workaround"]}`

## 3. 正确性红线

- scalar-arg 首用竞态是主要修复来源：conj d002 消耗 3 次精度修复（LocalMemBar + FetchEventID 事件 id→无效；入口切换预热协议→无效，且 tileLength=1 恒等 warmup 触发 device error 507035 后改用正式 tile；最终定位到『标量参数 launch 紧邻 NPU cast kernel 时参数不送达，失败输出=未写入的回收 cast-temp 字节 100% 匹配』，改用静态 12B 每调用 H2D 发射屏障后连续 3 次全量通过）；conj__v3 同样消耗 3 次精度修复（结构体按值→无效、参数前置重排→无效、首用惰性 warmup→生效）
- 该竞态会被相邻 kernel 的类型放大会掩盖：屏障的必要性依赖 launch 与相邻 cast kernel 的相对顺序，只有把屏障放在每次真实 launch 之前（或每 dtype 首次调用之前）才是稳定的；失败形态是零值 args 早退或写入未初始化的 cast-temp 字节，而非编译错误
- 删除 TQue 后同步责任转移到手写事件：漏掉 VF 存储队列的 Reg::LocalMemBar<VEC_STORE,VEC_LOAD> 或事件 id 复用会造成间歇性精度失败而非编译错误（conj d002 的对齐对象是 FlipAddcmul 模式）
- blockDim 从 tiling 字段改读 GetBlockNum() 后需确认所有入口都改到；漏改的入口会以默认/零值核数静默跑错（blockDim=1 的 _nestedgetmaxseqlen 本来就是 host 侧设定，改动面小但仍需逐入口核对）
- 删除每调用 H2D 的收益不计入 device Task Duration：可以记录为附带收益，但不得用于支撑性能结论；微内核（1.5-2.3us）落在 <50us 噪声地板内，必须按 microkernel-noise-floor-measurement-gate 先验卡用配对 ABBA 裁决
- TQue 直通路径的收益上界受先验卡约束：single-tile-tque-direct-path-limited-gain 给出的上界是 0.1-0.6us，若本次收益主要来自标记读删除而非框架剥离，删框架部分可能低于预期

资源与硬件约束：

- 标量参数的首次使用有 arg 布局初始化竞态：CANN 9.1.0/ascend950 上内联 kernel 的参数首次使用可能以零值 args 早退（基线全指针 args 无此问题），且当标量参数 launch 紧邻一个 NPU cast kernel 时参数不送达；必须用一个可信的『发射屏障』把首次标量参数 launch 与其它 kernel 隔开
- 屏障必须是常态路径而不是一次性握手：conj d002 的修复记录显示『入口切换预热协议（无害 1 元素恒等 launch 占领描述符）』无效，最终生效的是每次调用一个静态 12B staging H2D copy_；conj__v3 的生效形态是每 dtype 首次调用一次 dummy launch + stream synchronize 的惰性 warmup
- blockDim 必须改为从 GetBlockNum() 取（_nestedgetmaxseqlen 形态），不得再从 tiling 字段读，否则等于把刚删掉的依赖又加回来
- 数据面逐字节不变：DataCopyPad 载荷、Reg Muls/Cast、逐字节语义必须与 champion 完全一致；若同时删除 TQue 框架（conj d002 形态），必须换成单 TBuf<VECCALC>（一次 InitBuffer，in=前半 / out=后半 32B 对齐）+ 显式最小 SetFlag/WaitFlag（MTE2_V/V_MTE3，多 tile 回路 MTE3_MTE2/MTE3_V），并为 VF 存储队列补 Reg::LocalMemBar<VEC_STORE,VEC_LOAD>（对齐 FlipAddcmul 模式）
- 删除 host 每调用 H2D 的收益不计入 device Task Duration 决策口径（属 host 侧时延），不得用它支撑性能结论；微内核（1-2us 量级）必须用配对 ABBA msprof 裁决，不能用单次运行

## 4. 泛化条件

- 策略作用域：op_class：elementwise

适用：

- kernel 真正消费的 tiling 字段只有少数几个标量，其余是纯搬运开销：_nestedgetmaxseqlen 的 NestedGetMaxSeqlenCopyTiling（sizeof=44B）逐字节循环拷贝，kernel 只消费 ndim/dimSize[0..1]/blockDim；conj 的 ConjCopyTiling 只有 4 个 u32（12B）；conj__v3 只需 totalLength/blockLength/tileLength/mode
- 构建/工具链支持 __global__ 签名中的非 GM_ADDR 值参数：本 run conj 走 <<<>>> 结构体按值传参、conj__v3 传 4×u32 标量、_nestedgetmaxseqlen 传 by-value seqLen；先例为 CANN 9.1.0 的 Pto_prefetch.hpp:90（指针 + by-value uint64 total_elems，设备侧 get_block_num() 读核数）
- 设备侧 tiling 读是每 launch 固定成本的可测分量：conj__v3 的 1-block 小 case（84B-32KB）scalar 0.96-1.08us 占 wall 65-70% 且与数据量无关；_nestedgetmaxseqlen 的 aiv_scalar_time 1.177/1.468/1.188us 占 aiv_total 1.340/2.000/1.305us 的 74-90%
- host 侧每调用都存在 tiling tensor 构造 + H2D：conj pybind11.cpp 的 tiling_cpu.to(device)（16B）、_nestedgetmaxseqlen pybind11.cpp:49-56 的 torch::empty + 阻塞 H2D —— 删除它对 device Task Duration 中性偏正，对 e2e 是额外收益

不适用：

- kernel 需要 tiling 结构体整体（大数组、尺寸随 shape 变化）时不适用：按值传参只适合可枚举的少数标量（本 run 只传 seqLen 或 3-4 个 u32 / 一个 12B 结构体）
- tiling 读已经不存在或已被别的机制摊销掉时没有可消除对象；把逐字节读换成更大粒度的读（MTE2 批量搬运）不等于本机制——本 run conj 主线的 index-scalar-bulk-mte2-tbuf 已证伪那条路（9.117→9.2092 回滚），本机制消除的是读路径本身
- blockDim 语义依赖 host 传入的 tiling 字段、无法用 GetBlockNum() 等价替代时不适用

## 5. 实施步骤

1. 枚举 kernel 真正消费的 tiling 字段，把它们从 GM 结构体提升为 __global__ 的 by-value 标量参数：_nestedgetmaxseqlen 传 seqLen（先例为 CANN Pto_prefetch.hpp:90 的混合指针 + by-value uint64 参数）、conj d002 传 (GM_ADDR x, GM_ADDR y, uint32_t totalLength, uint32_t blockLength, uint32_t tileLength)、conj__v3 把 ConjTiling 结构体整体按值传入
2. kernel 内删除 tiling GM 读与 tiling_ 成员：_nestedgetmaxseqlen 删 NestedGetMaxSeqlenCopyTiling 的 44 字节逐字节拷贝（44 次串行标量 GM load）与 GM tiling 入参；conj d002 删 ConjCopyTiling 的 12B GM 逐字节标量读；conj__v3 删 ConjCopyTiling 的 4×u32 GM 依赖加载与结构体拷贝循环；守卫改读 GetBlockNum()
3. host 侧删除每次调用的 tiling tensor 构造与 H2D：_nestedgetmaxseqlen 删 pybind11.cpp:49-56 的 torch::empty + 阻塞 H2D；conj 删 pybind11.cpp 的 tiling tensor 构造与 H2D、改为构造栈结构/标量直接进 launch；conj__v3 删 tiling_cpu/tiling_npu 张量与每次调用 16B H2D
4. 为标量参数首用竞态加发射屏障，二选一：每 dtype 首次调用一次 dummy launch + stream synchronize（conj__v3 的惰性 warmup），或每次调用一个小的静态 H2D staging copy_（conj d002 的每调用 12B staging，历史上 champion 的 tiling H2D 恰好充当同一屏障）
5. 若同时删除 TQue 框架（conj d002 形态）：换成单 TBuf<VECCALC> + 显式最小 SetFlag/WaitFlag 事件对，并补 Reg::LocalMemBar<VEC_STORE,VEC_LOAD>；最后以 20/20 或 10/10 精度门 + 配对 ABBA msprof 验收，微内核需按噪声地板门禁用配对裁决

## 6. LLM 前置问题

- 目标实现是否满足：kernel 真正消费的 tiling 字段只有少数几个标量，其余是纯搬运开销：_nestedgetmaxseqlen 的 NestedGetMaxSeqlenCopyTiling（sizeof=44B）逐字节循环拷贝，kernel 只消费 ndim/dimSize[0..1]/blockDim；conj 的 ConjCopyTiling 只有 4 个 u32（12B）；conj__v3 只需 totalLength/blockLength/tileLength/mode？
- 目标实现是否满足：构建/工具链支持 __global__ 签名中的非 GM_ADDR 值参数：本 run conj 走 <<<>>> 结构体按值传参、conj__v3 传 4×u32 标量、_nestedgetmaxseqlen 传 by-value seqLen；先例为 CANN 9.1.0 的 Pto_prefetch.hpp:90（指针 + by-value uint64 total_elems，设备侧 get_block_num() 读核数）？
- 目标实现是否满足：设备侧 tiling 读是每 launch 固定成本的可测分量：conj__v3 的 1-block 小 case（84B-32KB）scalar 0.96-1.08us 占 wall 65-70% 且与数据量无关；_nestedgetmaxseqlen 的 aiv_scalar_time 1.177/1.468/1.188us 占 aiv_total 1.340/2.000/1.305us 的 74-90%？
- 目标实现是否满足：host 侧每调用都存在 tiling tensor 构造 + H2D：conj pybind11.cpp 的 tiling_cpu.to(device)（16B）、_nestedgetmaxseqlen pybind11.cpp:49-56 的 torch::empty + 阻塞 H2D —— 删除它对 device Task Duration 中性偏正，对 e2e 是额外收益？
- 是否命中排除条件：kernel 需要 tiling 结构体整体（大数组、尺寸随 shape 变化）时不适用：按值传参只适合可枚举的少数标量（本 run 只传 seqLen 或 3-4 个 u32 / 一个 12B 结构体）？
- 是否命中排除条件：tiling 读已经不存在或已被别的机制摊销掉时没有可消除对象；把逐字节读换成更大粒度的读（MTE2 批量搬运）不等于本机制——本 run conj 主线的 index-scalar-bulk-mte2-tbuf 已证伪那条路（9.117→9.2092 回滚），本机制消除的是读路径本身？
- 是否命中排除条件：blockDim 语义依赖 host 传入的 tiling 字段、无法用 GetBlockNum() 等价替代时不适用？

## 7. 验收标准

正确性：

- _nestedgetmaxseqlen：20/20 bit-exact（criterion = bit-exact int64 scalar），build 一次通过、零修复预算；数据流为纯 metadata 微内核，从未读输入 x
- conj d002：10/10 PASS（连续 3 次全量运行 exit 0）；消耗 3 次精度修复后收敛——Reg::LocalMemBar<VEC_STORE,VEC_LOAD> + FetchEventID→无效，入口切换预热协议→无效（期间 tileLength=1 恒等 warmup 触发 device error 507035，改用正式 tile），最终静态 12B 每调用 H2D 发射屏障 + queueless kernel 复位后 3/3 全通过
- conj__v3：10/10 PASS（repairs 3：结构体按值→无效、参数前置重排→无效、每 dtype 首用惰性 warmup→生效）；数据面（DataCopyPad 载荷、Reg Muls/Cast、逐字节语义）与 champion 完全一致，identity 拷贝语义逐位不变
- conj d002 的数据面与 champion 完全一致（DataCopyPad 载荷、Reg Muls/Cast、逐字节语义都不变），改动只在参数传递方式与队列框架

性能：

- _nestedgetmaxseqlen：形式化配对 ABBA 4 对（序列 B C C B B C C B，双目录重建 sealed snapshot，3 warmup + 10 measured × 20 shape = 260 launches/run，device 5）池化两级聚合 1.3786→1.1388us = 1.2106x（-17.39%），12 个 pair×case 单元全部候选更快，效应约为基线侧 run spread（0.9%）的 19 倍；B 侧 1.3786us 复现 champion 正式值 1.3771us（差 0.11%）；逐 dtype bf16 1.3626→1.1233、fp16 1.4073→1.1686、fp32 1.3663→1.1251
- conj d002：ABBA 两块（p1=A,B,B,A；p2=B,A,A,B，8 次独立 msprof 进程）4 对 ratio 0.821/0.818/0.8181/0.8254（区间宽 0.0074），两级聚合 2.5171→2.0655us = 1.2186x（-17.94%）；1 核 case 截距显著下降（case_01_fp32_512 1.564→1.1934、case_03_fp32_21 1.6529→1.2498、case_07_bf16_217 1.6594→1.197），fp32 262144@64 核 9.7354→9.2705us（-4.8%），中大 case -7~11%
- conj__v3：ABBA 平衡交替 x4 对（B A A B B A A B，双目录子进程交替加载）pair speedup 1.1473/1.1592/1.1555/1.1609，12 项 case 级配对全部 >1.0（1.0378-1.3575）无 shape 回退，dtype 组 geomean 2.1436→1.8547us = 1.1558x（-15.58%，超出保守预测区间 -5%~-10%）；fp32 2.3176→1.9974、fp16 2.1612→1.8561、bf16 1.9664→1.7209；case2（fp32 1MB）收益最小（1.0378），与其 MTE 带宽墙表象一致

回滚信号：

- 标量参数首用竞态未被屏障覆盖：出现随相邻 kernel 变化的间歇性精度失败（零值 args 早退，或写入未初始化的回收 cast-temp 字节）
- 删除 TQue 后手写事件/内存屏障不完备，VF 存储队列未落盘（需要 Reg::LocalMemBar<VEC_STORE,VEC_LOAD>）
- 精度门未过而性能有收益：按契约整体回滚，不保留一半改动
- 微内核（1-2us 量级）未做配对 ABBA 就下结论：落在 <50us 噪声地板内，必须按 microkernel-noise-floor-measurement-gate 用配对 msprof 裁决
- ABBA 配对 geomean 无显著下降（<5%）或任一精度用例失败且无性能收益，即整体回滚恢复 champion

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：microkernel-noise-floor-measurement-gate

- loop_20260916_165309 status=accepted, speedup=1.2186, precision=10/10 PASS（连续 3 次全量 exit 0，MERE/MARE 全 0））
- loop_20260915_161957 status=accepted, speedup=1.2106, precision=20/20 PASS bit-exact int64 scalar）
- loop_20260916_165309 status=accepted, speedup=1.1558, precision=10/10 PASS（MERE/MARE 全 0））

## 检索卡（短卡）

动作：把 tiling 改为 launch 按值传参，删设备侧 GM 结构体读与 host 每调用 H2D，blockDim 取 GetBlockNum()。
适用：kernel 只消费少数 tiling 标量；工具链支持 __global__ 非 GM_ADDR 值参数。
限制：标量参数首用竞态须配常态发射屏障；删 TQue 后须手写最小事件对与 LocalMemBar。
范围：elementwise 的逐元素恒等/映射与 metadata 微内核。
检索词：by-value 参数、__global__ 签名、GetBlockNum、发射屏障、TQue、LocalMemBar
机会：每次 launch 都付设备侧 GM 结构体读（44 次串行标量 load、4×u32 依赖加载）与 host 每调用 H2D。
代价：收益落在 <50us 噪声地板内须配 ABBA 裁决；删 H2D 收益不计入 device 口径。
