---
type: Optimization
title: 恒等 V 段消除：MTE2→MTE3 直通拷贝替代整流计算段
description: conj 对实数输入逐位恒等，但 champion 每个 tile 仍走 MTE2→V→MTE3：fp16/bf16 每 repeat 5 条向量指令（unpack-load→Cast-up→Muls(1.0)→Cast-down→pack-store）、fp32 3 条，并为该段维护独立 VECOUT 队列与第二组事件往返。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.implementation.pipeline
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/identity-v-pipe-elimination-mte-passthrough.md
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
      "恒等性必须在目标 dtype 的实数全值域上逐位成立：fp32 走 x×1.0 逐位精确，fp16/bf16 走 unpack-load→Cast-up 到 fp32→Muls(1.0f)→Cast-down→pack-store 的往返也逐位精确（RINT 下转），删除后输出仍逐位等于 y=x；不得只由『测试只覆盖实数 dtype』反推",
      "必须保持 UB 进出的字节载荷与逐字节语义：conj__v4 的 ConjMtePassthrough 保持 DataCopyPad GM→UB→GM 直通，conj/003 明确『UB 进出、数据载荷与逐字节语义不变』，_conj 只删恒等向量段不改 DataCopyPad",
      "删除独立的 VECOUT 队列/缓冲后要重设队列绑定关系：_conj 用 TQueBind<VECIN,VECOUT,2> 让同一缓冲承担进出；conj__v4 用 TPipe 双 queue double-buffer（VECIN→VECOUT 直通 EnQue）",
      "移除 V 段后同步链必须重新给成最小集合：conj/003 从 2 组事件往返（MTE2_V + V_MTE3）+ LocalMemBar 收缩为 1 组最小事件对；仍有 Reg 计算的路径（conj d002 / 未删 Reg 的形态）保留 Reg::LocalMemBar<VEC_STORE,VEC_LOAD>",
      "小 case 的规模门控必须保留：conj__v4 对 totalBytes<4096 保留 SIMT 现路径，极小 case 上 MTE 固定开销可能贵于 SIMT",
      "释放出来的 UB（原 VECOUT 缓冲）不得反向用于缩小单块：conj__v4 的 round_02 把 tile 从 32KB 参数化到 8KB 时实测证伪回滚，单块大小是 MTE 效率的主导项而非核间并行不足"
    ],
    "excluded_conditions": [
      "算子在各 dtype 上不是恒等（存在真实数值变换）时不适用：机制的全部收益来自被删段对输出逐位零贡献",
      "V 段已与 MTE 搬运充分重叠、且独立队列/事件成本不随 V 段消失时不适用：_conj 的 HYPOTHESIS 即『若 VEC 段已与 MTE 双缓冲充分重叠则收益有限，由配对 ABBA 裁决』，实测收敛到小而稳定的 1.1113x",
      "V 段在某个未测 dtype/路径上承担格式转换职责（输入输出不同精度、mixed dtype）时不可删",
      "极小 case（<4KB）缺少 SIMT 回退路径时不能全量走 MTE 直通"
    ],
    "required_conditions": [
      "算子在被路由的 dtype 上数学恒等：conj 对实数输入 y=conj(x)=x（tests/common.py 注明，golden=torch.conj 实数不变）；Or 写回自身输入同样属于此类",
      "V 段是独立可删的整段而非散落在数据流里：champion 每 tile 走 GM→UB(DataCopyPad)→Reg 恒等向量段→UB→GM，并为该段维护独立 VECOUT 队列与缓冲（conj__v4 的 ConjRegImpl Load/Cast/Muls/Cast/Store；_conj 记 fp16/bf16 每 repeat 5 条向量指令、fp32 3 条）",
      "UB 进出的字节载荷不变即可保持逐位等价：删 V 段后 CopyIn 的 LocalTensor 在 DeQue 后可直接作为 CopyOut 源（_conj 形态），或把 VECIN→VECOUT 直通 EnQue（conj__v4 形态）",
      "同步结构可收缩：原为两组事件往返（MTE2_V + V_MTE3）+ LocalMemBar，删 V 段后可收缩为 1 组最小 MTE2→MTE3 事件对（conj/003 形态）"
    ]
  },
  "classification": "validated_strategy",
  "created": "2026-09-18",
  "evidence": [
    {
      "operator": "conj__v4",
      "operator_class": "elementwise",
      "precision": "10/10 PASS",
      "run_id": "<run-id>",
      "speedup": 1.2979,
      "status": "accepted"
    },
    {
      "operator": "_conj",
      "operator_class": "elementwise",
      "precision": "10/10 PASS（逐位一致）",
      "run_id": "<run-id>",
      "speedup": 1.1113,
      "status": "accepted"
    },
    {
      "operator": "conj",
      "operator_class": "elementwise",
      "precision": "10/10 PASS（MERE/MARE 全 0，两次独立全量 exit 0）",
      "run_id": "<run-id>",
      "speedup": 1.0697,
      "status": "accepted"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "vec-identity-compute",
      "v-pipe-dead-code",
      "extra-event-pair-round-trip",
      "per-repeat-mask-align-scalar-loop",
      "scalar-gm-throughput"
    ],
    "dtypes": [
      "bf16",
      "fp16",
      "fp32"
    ],
    "pattern": "identity-v-pipe-elimination-mte-passthrough",
    "reduce_mode": "",
    "structure": [
      "v-segment-deletion",
      "mte2-mte3-passthrough",
      "tquebind-vecin-vecout",
      "minimal-single-event-pair",
      "bit-exact-identity"
    ]
  },
  "generality": "op_class",
  "id": "IDENTITY-VPIPE-ELIMINATION-MTE-PASSTHROUGH",
  "implementation_steps": [
    "先证明恒等：逐 dtype 论证被删 V 段的输出与输入逐位相同（fp32 x×1.0 逐位精确；fp16/bf16 经 fp32 上转 ×1.0 后 RINT 下转逐位精确往返），并确认测试用例只覆盖实数 dtype（本 run golden=torch.conj 对实数不变）",
    "删除 V 段本体：移除 Load/Muls(1.0)/Store（fp32 3 指令/repeat）与 unpack-load→Cast-up→Muls(1.0)→Cast-down→pack-store（fp16/bf16 5 指令/repeat）循环，以及逐 repeat 的 UpdateMask/LoadAlign/Muls/Cast/StoreAlign 标量循环",
    "把 UB 直通接起来：让 CopyIn 的 LocalTensor 在 DeQue 后直接作为 CopyOut 源（_conj：TQueBind<VECIN,VECOUT,2>），或把 VECIN→VECOUT 直通 EnQue（conj__v4：TPipe 双 queue double-buffer 32KB tile，DataCopyPad GM→UB→GM 零 ALU），必要时让整个数据流从 SIMT 逐元素 GM load/store 切到 MTE2/MTE3 经 UB 中转的块拷贝",
    "重设同步为最小集合：删掉两组事件往返里多余的一对，只留 MTE2→MTE3 所需的最小事件对；仍有 Reg 计算的路径保留 Reg::LocalMemBar<VEC_STORE,VEC_LOAD>",
    "按 MTE 带宽特征重排 blockDim/tile 并保留小 case 门控（conj__v4：MTE 分支 blockDim=ceil(totalBytes/32KB) 上限 50、blockLength 32B 对齐分块并在尾块用 DataCopyPad pad 处理、totalBytes<4096 保留 SIMT），以逐位精度门 + 配对 ABBA 验收"
  ],
  "intent": "删除整流数学恒等的 V 段死代码：conj 对实数输入是逐位恒等映射，但每个 tile 仍跑一遍完整的 V-pipe（Muls(1.0)、Cast 往返、UpdateMask）并维护一个独立的 VECOUT 队列与第二组事件往返，对输出逐位零贡献；改用 MTE2→MTE3 直通后同步链、队列与逐 repeat 标量循环一并消失。",
  "mechanism": "identity-v-pipe-elimination-mte-passthrough：三个成员都建立在『conj 对实数 dtype 为恒等映射』这一可证事实上，删除形态逐级加深。_conj（muls-elimination-input-tensor-direct-copyout）：保留 TQue 框架但把 input/output 两个队列绑成 TQueBind<VECIN,VECOUT,2>，CopyIn 的 LocalTensor 在 DeQue 后直接作为 CopyOut 源，删掉 fp32 的 Load/Muls*1.0/Store 与 fp16/bf16 的 unpack-load→Cast-up→Muls*1.0→Cast-down→pack-store 循环，机制层 aiv_vec_time 清零。conj/003（vec-free-mte-passthrough-copy）：进一步把同步链从 2 组事件往返（MTE2_V + V_MTE3）+ LocalMemBar 收缩为 1 组最小事件对，并消除逐 repeat 的 UpdateMask/LoadAlign/Muls/Cast/StoreAlign 标量循环（作用对象是 1 核截距 scalar 0.74-0.79us 占 wall 55%，与多核 aiv_scalar_time(Σ) 斜率份额 64 核时占 wall 85%）。conj__v4（mte23-ub-staged-passthrough-copy）：把整个数据流从 SIMT 线程逐元素 GM load/store 换成 MTE2/MTE3 经 UB 中转的纯直通块拷贝——ConjMtePassthrough，TPipe 双 queue double-buffer 32KB tile，VECIN→VECOUT 直通 EnQue，零 ALU 计算指令，删除 ConjRegImpl 与 ConjCustomKernel 的 Load/Cast/Muls/Cast/Store 全套 ALU 路径，host 侧重排 blockDim=ceil(totalBytes/32KB)（上限 50）与 32B 对齐分块，对 totalBytes<4096 保留 SIMT 门控。数据载荷与逐字节语义在三者中均不变。",
  "name": "恒等 V 段消除：MTE2→MTE3 直通拷贝替代整流计算段",
  "operator_class": "elementwise",
  "operator_scope": "在被路由的 dtype 上数学恒等、但数据流仍走 MTE2→V→MTE3 并保留独立输出队列的算子：real-valued conj / 写回自身输入的更新类（Or）、以及任何『输出=输入』的逐元素 kernel；不适用于有真实数值变换的元素级链",
  "principle": "当被替换的整段计算数学恒等（real-valued conj 即 y=x），它在流水上就不再是计算而是纯粹的往返：占一个 V 段、一份独立 VECOUT 缓冲、一组 V 侧事件与逐 repeat 的掩码/对齐标量循环，却对输出逐位零贡献。这类死代码的代价有两层：第一层是发射——_conj 记 fp16/bf16 路径每 repeat 5 条向量指令（unpack-load→Cast<float>→Muls(1.0f)→Cast<T>→pack-store），fp32 路径 3 条；第二层是结构——独立 VECOUT 队列带来的第二组事件往返与缓冲。删掉它使数据流从 MTE2→V→MTE3 退化为 MTE2→MTE3 直通，同步链从两组事件往返收缩为一组最小事件对，UB 走向也从『进出两块缓冲』变成『同一块 UB 进出』。收益不是无条件的：如果 V 段本来就被 MTE 双缓冲完全隐藏，剩下的只是同步与队列成本，实测会收敛到小而稳定的正收益（_conj 1.1113x，其中 fp32 只有 1.032x 因为其 3 指令/repeat 的 V 段最短）。这条机制与『减少 V 段指令数』（vec-frontend-instruction-diet / vec-algebraic-strength-reduction 一类）正交：后者优化活着的 V 段，本机制删掉整段死的。",
  "related_anti_patterns": [],
  "risks": [
    "收益上界受 V 段与 MTE 的重叠程度限制：若 V 段已完全隐藏在 MTE 搬运下，删它只减少同步/队列成本——_conj 的 HYPOTHESIS 明确指出这一点，实测得 1.1113x（fp32 仅 1.032x、fp16 1.176x、bf16 1.131x）",
    "MTE 直通不是无条件更快，删 V 段后不得顺手缩小单块：conj__v4 的 round_02 把 tile 从 32KB 参数化到 8KB，实测证伪回滚——单块大小是 MTE 效率的主导项而非核间并行不足",
    "极小 case 上 MTE 固定开销可能劣于 SIMT：conj__v4 保留 totalBytes<4096 的 SIMT 门控，两个门内小 case 实测 +0.3%/+1.1%（噪声级），去掉门控会把它们变成实质回退",
    "被删的 V 段若在某个未测 dtype/路径上承担非恒等职责（mixed dtype 转换），会静默改变输出；必须以逐位精度门（MERE/MARE 全 0 或 bit-exact）验证",
    "同步链收缩后事件对不足会出现间歇性读写竞争（conj d002 记录的『VF 存储队列缺 Reg::LocalMemBar<VEC_STORE,VEC_LOAD>』即此类形态）"
  ],
  "slug": "identity-v-pipe-elimination-mte-passthrough",
  "summary": "conj 对实数输入逐位恒等，但 champion 每个 tile 仍走 MTE2→V→MTE3：fp16/bf16 每 repeat 5 条向量指令（unpack-load→Cast-up→Muls(1.0)→Cast-down→pack-store）、fp32 3 条，并为该段维护独立 VECOUT 队列与第二组事件往返。删除整段恒等 V 计算、让 CopyIn 的 UB 张量直接喂 CopyOut（TQueBind<VECIN,VECOUT,2>，或 VECIN→VECOUT 直通 EnQue）、把同步收缩为最小 MTE2→MTE3 事件对后，数据流退化为纯 MTE 直通。实测 conj__v4/mte23-ub-staged-passthrough 3.1041→2.3916us（1.2979x，fp32 262144 10.09→6.38us）、_conj 2.6256→2.3625us（1.1113x，10/10 逐位一致，aiv_vec_time 清零）、conj/vec-free-mte-passthrough 2.0786→1.9431us（1.0697x）。",
  "verification": {
    "correctness": [
      "conj__v4：10/10 PASS（repairs 0，编译门一次通过）；语义依据是 tests/common.py 注明 conj 实数输入恒等，champion 的 SIMT 路径本来就已按 uint16/uint32 carrier 纯位拷贝",
      "_conj：10/10 逐位一致（0 repair rounds）；ABBA 4 对平衡交替、同 shape、双目录独立编译、溯源干净，比值 0.9014/0.8919/0.9090/0.8970 全部同向，均值 0.8998，逐 case 全 dtype 一致改善且幅度远超 ±0.6% 噪声带，机制层 aiv_vec_time 清零",
      "conj/003：10/10（repairs 0，两次独立全量运行 exit 0）；V 级删除为逐位恒等，MERE/MARE 全 0；两次运行也排除了 d002 发现的标量参数偶发不送达（host 未改，shield H2D 屏障仍在）"
    ],
    "performance": [
      "conj__v4：ABBA 5 对 10 次测量平衡交替，pair ratio b_over_a 0.7572/0.7847/0.7557/0.7706/0.7847，两级聚合 3.1041→2.3916us = 1.2979x；fp32_c2_262144 10.0888→6.3804us、bf16_c6_131072 6.3916→3.4902us、fp16_c4_65536 4.3923→2.9525us；两个 SIMT 门控小 case +0.3%/+1.1%（噪声级），其余逐 case 无实质劣化",
      "_conj：ABBA 4 对 12 项配对，逐 case 全 dtype 一致改善，两级聚合 2.6256→2.3625us = 1.1113x（fp32 2.736→2.650、fp16 2.776→2.361、bf16 2.384→2.108）",
      "conj/003：ABBA 两块 4 对 geomean ratio 0.9299/0.9394/0.9373/0.9334（区间宽 0.0095，结论无歧义），两级聚合 2.0786→1.9431us = 1.0697x（-7.0%），超过方向设定的 5% 采纳门槛；全 10 case 逐 case 均值下降，最大 case fp32 262144 9.2688→9.1312us"
    ],
    "rollback_signals": [
      "任一 dtype case 的 MERE/MARE 不再为 0（恒等证明不成立，或被删段落实际承担了非恒等职责）",
      "删 V 段后同步事件对不足，出现间歇性读写竞争（回退到显式 LocalMemBar 或补事件对）",
      "顺手缩小 tile 导致 MTE 效率下降（conj__v4 round_02 的 8KB tile 布局已实测证伪回滚）",
      "极小 case（<4KB）失去 SIMT 门控后 MTE 固定开销反超（conj__v4 保留 SIMT 路径的边界）",
      "精度的基线签名是 test-suite 全通过而非 baseline-parity：任何一次 exit 非 0 都直接回滚"
    ]
  }
}
-->

# 性能优化策略：恒等 V 段消除：MTE2→MTE3 直通拷贝替代整流计算段

conj 对实数输入逐位恒等，但 champion 每个 tile 仍走 MTE2→V→MTE3：fp16/bf16 每 repeat 5 条向量指令（unpack-load→Cast-up→Muls(1.0)→Cast-down→pack-store）、fp32 3 条，并为该段维护独立 VECOUT 队列与第二组事件往返。删除整段恒等 V 计算、让 CopyIn 的 UB 张量直接喂 CopyOut（TQueBind<VECIN,VECOUT,2>，或 VECIN→VECOUT 直通 EnQue）、把同步收缩为最小 MTE2→MTE3 事件对后，数据流退化为纯 MTE 直通。实测 conj__v4/mte23-ub-staged-passthrough 3.1041→2.3916us（1.2979x，fp32 262144 10.09→6.38us）、_conj 2.6256→2.3625us（1.1113x，10/10 逐位一致，aiv_vec_time 清零）、conj/vec-free-mte-passthrough 2.0786→1.9431us（1.0697x）。

## 1. 原理

当被替换的整段计算数学恒等（real-valued conj 即 y=x），它在流水上就不再是计算而是纯粹的往返：占一个 V 段、一份独立 VECOUT 缓冲、一组 V 侧事件与逐 repeat 的掩码/对齐标量循环，却对输出逐位零贡献。这类死代码的代价有两层：第一层是发射——_conj 记 fp16/bf16 路径每 repeat 5 条向量指令（unpack-load→Cast<float>→Muls(1.0f)→Cast<T>→pack-store），fp32 路径 3 条；第二层是结构——独立 VECOUT 队列带来的第二组事件往返与缓冲。删掉它使数据流从 MTE2→V→MTE3 退化为 MTE2→MTE3 直通，同步链从两组事件往返收缩为一组最小事件对，UB 走向也从『进出两块缓冲』变成『同一块 UB 进出』。收益不是无条件的：如果 V 段本来就被 MTE 双缓冲完全隐藏，剩下的只是同步与队列成本，实测会收敛到小而稳定的正收益（_conj 1.1113x，其中 fp32 只有 1.032x 因为其 3 指令/repeat 的 V 段最短）。这条机制与『减少 V 段指令数』（vec-frontend-instruction-diet / vec-algebraic-strength-reduction 一类）正交：后者优化活着的 V 段，本机制删掉整段死的。

实现机制：identity-v-pipe-elimination-mte-passthrough：三个成员都建立在『conj 对实数 dtype 为恒等映射』这一可证事实上，删除形态逐级加深。_conj（muls-elimination-input-tensor-direct-copyout）：保留 TQue 框架但把 input/output 两个队列绑成 TQueBind<VECIN,VECOUT,2>，CopyIn 的 LocalTensor 在 DeQue 后直接作为 CopyOut 源，删掉 fp32 的 Load/Muls*1.0/Store 与 fp16/bf16 的 unpack-load→Cast-up→Muls*1.0→Cast-down→pack-store 循环，机制层 aiv_vec_time 清零。conj/003（vec-free-mte-passthrough-copy）：进一步把同步链从 2 组事件往返（MTE2_V + V_MTE3）+ LocalMemBar 收缩为 1 组最小事件对，并消除逐 repeat 的 UpdateMask/LoadAlign/Muls/Cast/StoreAlign 标量循环（作用对象是 1 核截距 scalar 0.74-0.79us 占 wall 55%，与多核 aiv_scalar_time(Σ) 斜率份额 64 核时占 wall 85%）。conj__v4（mte23-ub-staged-passthrough-copy）：把整个数据流从 SIMT 线程逐元素 GM load/store 换成 MTE2/MTE3 经 UB 中转的纯直通块拷贝——ConjMtePassthrough，TPipe 双 queue double-buffer 32KB tile，VECIN→VECOUT 直通 EnQue，零 ALU 计算指令，删除 ConjRegImpl 与 ConjCustomKernel 的 Load/Cast/Muls/Cast/Store 全套 ALU 路径，host 侧重排 blockDim=ceil(totalBytes/32KB)（上限 50）与 32B 对齐分块，对 totalBytes<4096 保留 SIMT 门控。数据载荷与逐字节语义在三者中均不变。

## 2. 性能问题模式

- 优化目标：删除整流数学恒等的 V 段死代码：conj 对实数输入是逐位恒等映射，但每个 tile 仍跑一遍完整的 V-pipe（Muls(1.0)、Cast 往返、UpdateMask）并维护一个独立的 VECOUT 队列与第二组事件往返，对输出逐位零贡献；改用 MTE2→MTE3 直通后同步链、队列与逐 repeat 标量循环一并消失。
- 适用数据流：在被路由的 dtype 上数学恒等、但数据流仍走 MTE2→V→MTE3 并保留独立输出队列的算子：real-valued conj / 写回自身输入的更新类（Or）、以及任何『输出=输入』的逐元素 kernel；不适用于有真实数值变换的元素级链
- Feature signature：`{"bottleneck": ["vec-identity-compute", "v-pipe-dead-code", "extra-event-pair-round-trip", "per-repeat-mask-align-scalar-loop", "scalar-gm-throughput"], "dtypes": ["bf16", "fp16", "fp32"], "pattern": "identity-v-pipe-elimination-mte-passthrough", "reduce_mode": "", "structure": ["v-segment-deletion", "mte2-mte3-passthrough", "tquebind-vecin-vecout", "minimal-single-event-pair", "bit-exact-identity"]}`

## 3. 正确性红线

- 收益上界受 V 段与 MTE 的重叠程度限制：若 V 段已完全隐藏在 MTE 搬运下，删它只减少同步/队列成本——_conj 的 HYPOTHESIS 明确指出这一点，实测得 1.1113x（fp32 仅 1.032x、fp16 1.176x、bf16 1.131x）
- MTE 直通不是无条件更快，删 V 段后不得顺手缩小单块：conj__v4 的 round_02 把 tile 从 32KB 参数化到 8KB，实测证伪回滚——单块大小是 MTE 效率的主导项而非核间并行不足
- 极小 case 上 MTE 固定开销可能劣于 SIMT：conj__v4 保留 totalBytes<4096 的 SIMT 门控，两个门内小 case 实测 +0.3%/+1.1%（噪声级），去掉门控会把它们变成实质回退
- 被删的 V 段若在某个未测 dtype/路径上承担非恒等职责（mixed dtype 转换），会静默改变输出；必须以逐位精度门（MERE/MARE 全 0 或 bit-exact）验证
- 同步链收缩后事件对不足会出现间歇性读写竞争（conj d002 记录的『VF 存储队列缺 Reg::LocalMemBar<VEC_STORE,VEC_LOAD>』即此类形态）

资源与硬件约束：

- 恒等性必须在目标 dtype 的实数全值域上逐位成立：fp32 走 x×1.0 逐位精确，fp16/bf16 走 unpack-load→Cast-up 到 fp32→Muls(1.0f)→Cast-down→pack-store 的往返也逐位精确（RINT 下转），删除后输出仍逐位等于 y=x；不得只由『测试只覆盖实数 dtype』反推
- 必须保持 UB 进出的字节载荷与逐字节语义：conj__v4 的 ConjMtePassthrough 保持 DataCopyPad GM→UB→GM 直通，conj/003 明确『UB 进出、数据载荷与逐字节语义不变』，_conj 只删恒等向量段不改 DataCopyPad
- 删除独立的 VECOUT 队列/缓冲后要重设队列绑定关系：_conj 用 TQueBind<VECIN,VECOUT,2> 让同一缓冲承担进出；conj__v4 用 TPipe 双 queue double-buffer（VECIN→VECOUT 直通 EnQue）
- 移除 V 段后同步链必须重新给成最小集合：conj/003 从 2 组事件往返（MTE2_V + V_MTE3）+ LocalMemBar 收缩为 1 组最小事件对；仍有 Reg 计算的路径（conj d002 / 未删 Reg 的形态）保留 Reg::LocalMemBar<VEC_STORE,VEC_LOAD>
- 小 case 的规模门控必须保留：conj__v4 对 totalBytes<4096 保留 SIMT 现路径，极小 case 上 MTE 固定开销可能贵于 SIMT
- 释放出来的 UB（原 VECOUT 缓冲）不得反向用于缩小单块：conj__v4 的 round_02 把 tile 从 32KB 参数化到 8KB 时实测证伪回滚，单块大小是 MTE 效率的主导项而非核间并行不足

## 4. 泛化条件

- 策略作用域：op_class：elementwise

适用：

- 算子在被路由的 dtype 上数学恒等：conj 对实数输入 y=conj(x)=x（tests/common.py 注明，golden=torch.conj 实数不变）；Or 写回自身输入同样属于此类
- V 段是独立可删的整段而非散落在数据流里：champion 每 tile 走 GM→UB(DataCopyPad)→Reg 恒等向量段→UB→GM，并为该段维护独立 VECOUT 队列与缓冲（conj__v4 的 ConjRegImpl Load/Cast/Muls/Cast/Store；_conj 记 fp16/bf16 每 repeat 5 条向量指令、fp32 3 条）
- UB 进出的字节载荷不变即可保持逐位等价：删 V 段后 CopyIn 的 LocalTensor 在 DeQue 后可直接作为 CopyOut 源（_conj 形态），或把 VECIN→VECOUT 直通 EnQue（conj__v4 形态）
- 同步结构可收缩：原为两组事件往返（MTE2_V + V_MTE3）+ LocalMemBar，删 V 段后可收缩为 1 组最小 MTE2→MTE3 事件对（conj/003 形态）

不适用：

- 算子在各 dtype 上不是恒等（存在真实数值变换）时不适用：机制的全部收益来自被删段对输出逐位零贡献
- V 段已与 MTE 搬运充分重叠、且独立队列/事件成本不随 V 段消失时不适用：_conj 的 HYPOTHESIS 即『若 VEC 段已与 MTE 双缓冲充分重叠则收益有限，由配对 ABBA 裁决』，实测收敛到小而稳定的 1.1113x
- V 段在某个未测 dtype/路径上承担格式转换职责（输入输出不同精度、mixed dtype）时不可删
- 极小 case（<4KB）缺少 SIMT 回退路径时不能全量走 MTE 直通

## 5. 实施步骤

1. 先证明恒等：逐 dtype 论证被删 V 段的输出与输入逐位相同（fp32 x×1.0 逐位精确；fp16/bf16 经 fp32 上转 ×1.0 后 RINT 下转逐位精确往返），并确认测试用例只覆盖实数 dtype（本 run golden=torch.conj 对实数不变）
2. 删除 V 段本体：移除 Load/Muls(1.0)/Store（fp32 3 指令/repeat）与 unpack-load→Cast-up→Muls(1.0)→Cast-down→pack-store（fp16/bf16 5 指令/repeat）循环，以及逐 repeat 的 UpdateMask/LoadAlign/Muls/Cast/StoreAlign 标量循环
3. 把 UB 直通接起来：让 CopyIn 的 LocalTensor 在 DeQue 后直接作为 CopyOut 源（_conj：TQueBind<VECIN,VECOUT,2>），或把 VECIN→VECOUT 直通 EnQue（conj__v4：TPipe 双 queue double-buffer 32KB tile，DataCopyPad GM→UB→GM 零 ALU），必要时让整个数据流从 SIMT 逐元素 GM load/store 切到 MTE2/MTE3 经 UB 中转的块拷贝
4. 重设同步为最小集合：删掉两组事件往返里多余的一对，只留 MTE2→MTE3 所需的最小事件对；仍有 Reg 计算的路径保留 Reg::LocalMemBar<VEC_STORE,VEC_LOAD>
5. 按 MTE 带宽特征重排 blockDim/tile 并保留小 case 门控（conj__v4：MTE 分支 blockDim=ceil(totalBytes/32KB) 上限 50、blockLength 32B 对齐分块并在尾块用 DataCopyPad pad 处理、totalBytes<4096 保留 SIMT），以逐位精度门 + 配对 ABBA 验收

## 6. LLM 前置问题

- 目标实现是否满足：算子在被路由的 dtype 上数学恒等：conj 对实数输入 y=conj(x)=x（tests/common.py 注明，golden=torch.conj 实数不变）；Or 写回自身输入同样属于此类？
- 目标实现是否满足：V 段是独立可删的整段而非散落在数据流里：champion 每 tile 走 GM→UB(DataCopyPad)→Reg 恒等向量段→UB→GM，并为该段维护独立 VECOUT 队列与缓冲（conj__v4 的 ConjRegImpl Load/Cast/Muls/Cast/Store；_conj 记 fp16/bf16 每 repeat 5 条向量指令、fp32 3 条）？
- 目标实现是否满足：UB 进出的字节载荷不变即可保持逐位等价：删 V 段后 CopyIn 的 LocalTensor 在 DeQue 后可直接作为 CopyOut 源（_conj 形态），或把 VECIN→VECOUT 直通 EnQue（conj__v4 形态）？
- 目标实现是否满足：同步结构可收缩：原为两组事件往返（MTE2_V + V_MTE3）+ LocalMemBar，删 V 段后可收缩为 1 组最小 MTE2→MTE3 事件对（conj/003 形态）？
- 是否命中排除条件：算子在各 dtype 上不是恒等（存在真实数值变换）时不适用：机制的全部收益来自被删段对输出逐位零贡献？
- 是否命中排除条件：V 段已与 MTE 搬运充分重叠、且独立队列/事件成本不随 V 段消失时不适用：_conj 的 HYPOTHESIS 即『若 VEC 段已与 MTE 双缓冲充分重叠则收益有限，由配对 ABBA 裁决』，实测收敛到小而稳定的 1.1113x？
- 是否命中排除条件：V 段在某个未测 dtype/路径上承担格式转换职责（输入输出不同精度、mixed dtype）时不可删？
- 是否命中排除条件：极小 case（<4KB）缺少 SIMT 回退路径时不能全量走 MTE 直通？

## 7. 验收标准

正确性：

- conj__v4：10/10 PASS（repairs 0，编译门一次通过）；语义依据是 tests/common.py 注明 conj 实数输入恒等，champion 的 SIMT 路径本来就已按 uint16/uint32 carrier 纯位拷贝
- _conj：10/10 逐位一致（0 repair rounds）；ABBA 4 对平衡交替、同 shape、双目录独立编译、溯源干净，比值 0.9014/0.8919/0.9090/0.8970 全部同向，均值 0.8998，逐 case 全 dtype 一致改善且幅度远超 ±0.6% 噪声带，机制层 aiv_vec_time 清零
- conj/003：10/10（repairs 0，两次独立全量运行 exit 0）；V 级删除为逐位恒等，MERE/MARE 全 0；两次运行也排除了 d002 发现的标量参数偶发不送达（host 未改，shield H2D 屏障仍在）

性能：

- conj__v4：ABBA 5 对 10 次测量平衡交替，pair ratio b_over_a 0.7572/0.7847/0.7557/0.7706/0.7847，两级聚合 3.1041→2.3916us = 1.2979x；fp32_c2_262144 10.0888→6.3804us、bf16_c6_131072 6.3916→3.4902us、fp16_c4_65536 4.3923→2.9525us；两个 SIMT 门控小 case +0.3%/+1.1%（噪声级），其余逐 case 无实质劣化
- _conj：ABBA 4 对 12 项配对，逐 case 全 dtype 一致改善，两级聚合 2.6256→2.3625us = 1.1113x（fp32 2.736→2.650、fp16 2.776→2.361、bf16 2.384→2.108）
- conj/003：ABBA 两块 4 对 geomean ratio 0.9299/0.9394/0.9373/0.9334（区间宽 0.0095，结论无歧义），两级聚合 2.0786→1.9431us = 1.0697x（-7.0%），超过方向设定的 5% 采纳门槛；全 10 case 逐 case 均值下降，最大 case fp32 262144 9.2688→9.1312us

回滚信号：

- 任一 dtype case 的 MERE/MARE 不再为 0（恒等证明不成立，或被删段落实际承担了非恒等职责）
- 删 V 段后同步事件对不足，出现间歇性读写竞争（回退到显式 LocalMemBar 或补事件对）
- 顺手缩小 tile 导致 MTE 效率下降（conj__v4 round_02 的 8KB tile 布局已实测证伪回滚）
- 极小 case（<4KB）失去 SIMT 门控后 MTE 固定开销反超（conj__v4 保留 SIMT 路径的边界）
- 精度的基线签名是 test-suite 全通过而非 baseline-parity：任何一次 exit 非 0 都直接回滚

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：无

- loop_20260916_165309 status=accepted, speedup=1.2979, precision=10/10 PASS）
- loop_20260915_161957 status=accepted, speedup=1.1113, precision=10/10 PASS（逐位一致））
- loop_20260916_165309 status=accepted, speedup=1.0697, precision=10/10 PASS（MERE/MARE 全 0，两次独立全量 exit 0））

## 检索卡（短卡）

动作：把数学恒等的 V 段整段删除，DataCopyPad 搬入的 UB 张量直通搬出，同步收缩为最小 MTE2→MTE3 事件对。
适用：被路由 dtype 上数学恒等（实数 conj、写回自身输入）；V 段为独立可删的整段。
限制：恒等须在目标 dtype 实数全值域逐位成立；载荷与逐字节语义不变；同步不足会引入间歇性竞争；删 V 段后不得缩小单块。
范围：elementwise 恒等/输出=输入 kernel 的搬入-计算-搬出数据流。
检索词：TQueBind、MTE2→MTE3 直通、VECOUT 队列、LocalMemBar、DataCopyPad
机会：每 tile 仍跑完整恒等 V-pipe（Muls(1.0)、Cast 往返）并维护独立 VECOUT 队列。
代价：若 V 段已被 MTE 双缓冲完全隐藏，收益只剩同步与队列成本；极小 case 需保留 SIMT 门控。
