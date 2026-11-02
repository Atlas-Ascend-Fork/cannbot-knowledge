---
type: Runbook
title: "SwiGLU 行量化的 scale 通过而 INT8 差一位时保留完整舍入决策"
description: "在有界 INT8 点积、FP32 scale 和精确 INT8 合同下，补偿反量化、SiLU、整行 maxabs 与归一化并携带低位到 RNE；沿 CANN per-token 分支保留 INT32 tile 交接与严格计算钩子，区分结构迁移、精度验证和性能归因。"
aliases: ["scale PASS INT8 one LSB FAIL", "GroupedMatmulSwigluQuantV2 exact INT32 compensated FP32", "compensated rowmax RNE", "CANN per-token strict tile handoff", "INT32 Cube UB full-row paired workspace"]
tags: [task.debugging, topic.precision]
status: stable
sources:
  - resource: https://gitcode.com/cann/ops-transformer/blob/be33d95bb755cedec3108f70805c1874d1792540/gmm/grouped_matmul_swiglu_quant_v2/op_kernel/grouped_matmul_swiglu_quant_v2_apt.cpp
    role: implementation
  - resource: https://gitcode.com/cann/ops-transformer/blob/be33d95bb755cedec3108f70805c1874d1792540/gmm/grouped_matmul_swiglu_quant_v2/op_kernel/arch35/grouped_matmul_swiglu_quant_v2_pertoken_quant.h
    role: implementation
  - resource: https://gitcode.com/cann/ops-transformer/blob/be33d95bb755cedec3108f70805c1874d1792540/gmm/common/cgmct/kernel/kernel_gmm_swiglu_pertoken_quant.h
    role: implementation
  - resource: https://gitcode.com/cann/ops-transformer/blob/be33d95bb755cedec3108f70805c1874d1792540/gmm/common/cgmct/epilogue/block_epilogue_dequant_swiglu.h
    role: implementation
  - resource: https://gitcode.com/cann/ops-transformer/blob/be33d95bb755cedec3108f70805c1874d1792540/gmm/common/cgmct/epilogue/block_epilogue_pertoken_quant.h
    role: implementation
created_at: "2026-10-20T15:38:07Z"
updated_at: "2026-10-21T05:59:21Z"
platforms: ["950"]
---

# SwiGLU 行量化的 scale 通过而 INT8 差一位时保留完整舍入决策

> **来源角色说明（2026-10-31）**：上列五份固定公开源码的角色已由 `primary` 改为 **`implementation`**——它们承载的是**结构基线与迁移边界**（per-token 分支选择、raw INT32 tile 交接、完整行 workspace/同步、ABI），**不承载**本卡的严格数值主张。已核实公开 epilogue 的 `VFDoDequant` / `VFDoSwiglu` 及其 caller 走的是**单 FP32 的 cast / multiply / Exp / Div**，**没有**本卡的整数残差、成对高低位 nonlinear/max 与 RNE tie 修正。
> ⇒ 本卡的**严格补偿钩子、P/Q 计数、布局与全部数字**来自**车队私有作者记录的实测**，既不是这些公开文件的实现，也不是对它们的独立重现；本轮内容审查未重放。旧 13+37 与新 50 两个合同、全部性能失败结果、WHITE_BOX 谱系与原生失败记录**均按原样保留**。

## 适用场景

- **工程形态**：GroupedMatmulSwigluQuantV2 的返回 tuple 中浮点 scale 在容差内通过、INT8 叶却出现一单位差异时，保留从 INT32 点积到最后 RNE 的完整舍入决策，而不是放宽整数标准或用输出 dtype 归一化未定义的属性组合。
- **API 路径**：公开 quant-matmul 的单位 scale 与显式 INT32 输出；AscendC helper 以 4097 split 做 FP32 高低位反量化；SiLU/gate 继续携带高低位；整行 maxabs 选择后除以 127，低位保留到最后 RNE 再 clamp 到 INT8。
- **验证过的平台与 CANN 版本**：950；实验 SDK 为 9.2.0.B060 / arch35（Runbook 不声明 `cann_versions`，版本边界以此处与失效边界为准）。
- **适用粒度**：`exact_task`——实际 INT8 输入/权重、FP32 token/channel scales、INT64 group 边界、无可选 bias/offset、四个 mode/dtype 属性均为 0；已测 K 为 256 或 1024，保守无溢出前提为 `K*16384 < 2^31`。
- **路线优先级**：`recommended_fastpath`。
- **明确不适用或未验证场景**：FP8、非有限值和其他属性合同不在该结果内；旧链仅实测 group-list type 0，原 37 项模式合同未解决且不被新合同删除；编译融合/FMA、指数范围、零行、下溢与拆分算法的非有限值处理均须另行核验；无逐原语消融，不能把任一步骤认定为失败的唯一原因。性能侧完整 50 例 GM 未达 0.8/1.1，精度通过不蕴含性能达标。

## 触发与合同

浮点 scale 在容差内，不代表 INT8 量化结果满足逐元素相等。已测 GroupedMatmulSwigluQuantV2 原始合同中，13 个有定义的 INT8 案例有 2 个通过、11 个出现一单位 INT8 差异，另外 37 个案例的模式合同未解决。不能根据实际输出 dtype 把未定义的属性组合归一化为 INT8，也不能把 scale 的 PASS 转为整个返回 tuple 的 PASS。

本方法使用实际 INT8 输入/权重、FP32 token/channel scales、INT64 group 边界、无可选 bias/offset，且四个 mode/dtype 属性均为 0。精度参考对实际 postcast 值做独立 CPU FP64 点积、缩放、SiLU/gate、整行 maxabs/127 和 RNE；INT8 必须精确相等，FP32 scale 沿冻结的浮点判据核验。FP8、非有限值和其他属性合同不在该结果中。

## 处置方法及实现边界

1. 先取得有界 INT32 点积，并验证输出 dtype、shape、device。实现采用公开 quant-matmul 的单位 scale 和显式 INT32 输出；保守无溢出前提为 K*16384<2^31。已测 K 为 256 或 1024；这不证明任意满足该不等式的后续转换均正确。
2. 反量化使用 FP32 高低位对，保留乘法与加法残差。已测自定义 helper 用 4097 split、明确的向量依赖和当前流，顺序为 channel scale 后 token scale；CPU 参考的缩放结合顺序不同。实际结果验证了所测输入，不是任意数值下关联律的证明。
3. SiLU/gate 继续携带高低位；被测实现以 ln(2) 做范围约简、十八阶多项式和独立整数指数，保留参考 sigmoid 的有限溢出截断。不得把该有限域近似称为通用 FP64 模拟。
4. 在完整输出行上选择 maxabs，保留最大值和归一化商的低位到最后 RNE。若值保存为 `(high, low, exponent)`，先仅在非零高低位对中取最大的共同 rowExponent，全零行取0；将每对按 `elementExponent-rowExponent` 对齐后，才按绝对值的高位、再低位选择最大值并归一化。返回 scale 时，先将该对齐域中的最大值除以127，再乘回 `2^rowExponent` 并按冻结规则合并高低位。全零行沿冻结 helper 的量化/scale 分支，不能擅自把 scale 设成0。依据完整小数残差与 floor 奇偶性决定 tie，再 clamp 到 INT8。已测 helper 的指数差截断到[-149,0]；这与其有限指数域、零行和下溢处理一起固定，不是全域等价或 FTZ/非有限值证明。提前把 nonlinear result、maxabs 或商压成一个 FP32 值可能改变整数边界。
5. 对两个返回叶逐一验证。保留实际输入/属性哈希和零输出坏控制；不加 epsilon、不读取正确答案、不缓存输入值对应输出、不降低整数标准。编译融合/FMA、指数范围、零行、下溢和拆分算法的非有限值处理均须另行核验。

这是公开 INT32 primitive、已有 AscendC helper 和补偿 FP32 NPU 尾处理的组合修复；没有逐原语消融证明哪个步骤是 11 个失败的唯一原因。已测点积范围并不支持“INT32 转 FP32 丢低位导致本次所有失败”的说法。

## 两个独立的实测合同

旧合同候选 SHA-256 为 2a36630eeb53c0fc9b1b23b895f8472d7da05609599995506e48d93e2c8bfc2e，实际加载 helper DSO 为 2e6654e0e6e4452c815c709811ef13d770c91a0edb5473d1e2c5e06a204aa42e。在原 13 个有定义案例中，13 个完整 tuple、168,312,832 个 INT8 元素精确相等，663,680 个 FP32 scale 元素通过；原有 2 通过、11 失败及 37 未解决记录保留。旧链仅实测 group-list type 0。

另一个显式修订合同使用 Model 4199393aaefe9893581dab9ca7cd7b4d36ed052b822b67c349920cd4325c7592、cases fee2d5114b75bc0c1df4b85df7b1982be6f88b509d5fdcb6f57c71c476842646，同一候选/helper 获得独立 50 例完整通过，覆盖两种 group-list type 各 25 例；900,218,880 个 INT8 元素精确相等、2,146,432 个 scale 元素通过。该合同明确修改了冲突属性并使用新 seed，不能删除旧 37 项未决、声称旧数组相同或认证 FP8。

## 从 CANN per-token 结构开始，保留严格计算钩子

当“完整 INT32 点积先写 GM，再启动严格尾处理”的实现精度通过但速度不足时，可复用 CANN 的调度和 tile 交接结构，而不是整体替换成其快速 epilogue。以下是 `cann/ops-transformer@be33d95bb755cedec3108f70805c1874d1792540` 的源码分析及由此得到的迁移方法，平台限 arch35；**尚未建立该提交与已测 B060 原生二进制及选中 tiling 的对应关系**，不是对原生内部耗时的解释。

**先确认任务的源码权限。** 独立 cookbook 中的“灰盒/冷验证不得窥看 arch35 参考实现”属于该验证 recipe 的隔离约束，仍须保留。当前具名 WHITE_BOX 源码研究按调用方授权执行，并记录所读提交、分支与复用来源；这不把已曝光源码的实现追认为灰盒或冷黑盒结果，也不将上述隔离要求扩展成对所有 WHITE_BOX 研究的禁止。

1. **先选对分支和部署方式。** `grouped_matmul_swiglu_quant_v2_apt.cpp` 按 `ORIG_DTYPE_X_SCALE` 选择分支：FP32 token scale 进入 per-token，E8M0 scale 进入另一组 MX/weight-quant 路径。INT8 X/W、FP32 scales 的本合同不能借用 MX 的布局或流水结论。per-token 入口将 INT8 的 Cube 结果类型设为 INT32，从 Host tiling 取得 baseM/baseN/baseK，并使用 tail-split group scheduler。先核对 transpose、group-list 解释、行列偏移、尾块和当前 SDK 的 tiling/launch/workspace 契约；不要把独立 pybind11 cookbook 的固定 tile、手填结构体或禁用某 API 的部署约束当成这个分支的通用规则。
2. **把 raw INT32 tile 交给严格钩子。** `ProcessSingleGroup` 为左右半矩阵分别计算完整 K 的 INT32 tile，经 L0C→UB 交给两个目的区域；AIC 等待上次 AIV 消费，再通知 AIV，AIV 处理后返还复用信号。保留 group 顺序、空 group 跳过、左右列偏移、M/N 尾块、对齐 stride 和完整 K 语义，替换 `epilogueDequantAndSwigluOp_` 的算术。不能把部分 K 和当成最终点积，也不能只因有两个 buffer 就断言已实现计算/搬运重叠。
3. **明确不能照搬的精度步骤。** 源码快速路径把 INT32 转为一个 FP32，再做 channel/token 缩放、Exp/Div、单 FP32 SwiGLU 值及普通 maxabs/量化。它没有本卡的整数残差、成对 nonlinear/max 低位和 RNE tie 修正。严格钩子继续使用上文验证过的 high/low 运算顺序、指数与截断规则；不得以代数等价改变关联顺序。CPU 数学参考的 token→weight 缩放顺序与 CANN 此路径及已测候选的 weight→token 顺序不同，现有实测只支持各自冻结输入上的结果。
4. **完整行约束决定 workspace。** CANN 在第一阶段把 SwiGLU 值写 workspace，`End(); SyncAll();` 后再按完整输出行量化。若一个 tile 只覆盖 H 的一部分，严格替换必须按原始行列坐标保存 `(high, low, exponent)`，完整行到齐后先按上文非零值规则选择共同行指数、对齐每对，再做低位感知的 max、归一化和 RNE，最后恢复行指数形成 scale；全零行和有限指数/截断规则沿冻结 helper，不能逐 N tile 独立计算 scale，也不能直接比较不同指数的原始 high/low。以两个 FP32 加一个 INT32 指数计，逻辑载荷为每值12B、尚未含对齐，不能复用原单 FP32 workspace 的尺寸和偏移。该结构可去掉单独的完整 INT32-dot GM 边界，但新增成对 workspace 流量，净收益未知。只有另行证明 tile 覆盖完整 H、容量和生命周期均成立时，才考虑取消这条全局边界。
5. **先证明新接线，再做流水选择。** 每个新 DSO 对冻结的完整50例核对实际输入/属性、左右半矩阵布局、group/tail、两个返回叶和当前加载库；INT8 保持逐元素相等，scale 保持原判据。精度失败先定位首个不同的 tile/返回叶，不能靠放宽标准换速度。精度通过后，才用同一完整消费者做交替计时并保留原生精度失败。接着可单独选择 K 分块、双槽事件或 epilogue 融合这一类改动；若一起改变，只能评价整个方案，不能归功于某条流水或某次 copy 的删除。

### 已测边界与下一次生成的决策

在修订 Model `4199393a…` / cases `fee2d511…` 的严格合同上，一个采用 CANN tile-handoff 结构并保留严格钩子的后续版本，实际 DSO 为 `00b350d0761e6933b06334083efd760a8ff2232e649e760a04ecfb75be5a41f4`：P50通过、候选计时返回250通过，原生25通过/225失败；完整50例500个 Event legs 的等例权重 median-of-five-paired-ratios GM为 **0.21411681559959814**，仍未达到0.8/1.1。该版本还包括有界分母 helper 专化，不能把结果解释成仅 tile-handoff 的消融。它证明这套严格计算可接入一个实测结构，也反驳“用了 CANN 交接/减少中间边界就已经达到性能目标”；不证明全输入域等价、精确指令成本或硬件极限。该版本的封存证据（内部归档，社区不可访问）保留源码、构建、完整消费者和失败边界。

另一算子 WeightQuantBatchmatmul 的残差保留流水提供范围更窄的反例（两个 DSO 分别为 `dc5dcf5630b92a53c48d17c5c99f68d54298a53517d60c3c9e0a4ab339bb5fc8`、`e072fece0028e8f65af35d63c5f41a0b23057320cbdb9b837747b9009e8ca101`）：两个完整50例版本均获得 P100/Q400 候选返回通过，GM分别为0.33672314663113234和0.3956104514108981，均未达到0.8/1.1。后者将“两次 MMAD/K128”改为“一次宽 MMAD/K64”，在17个实际分组形状上逻辑 MMAD 调用数相等、FIX copy 调用数减半。该旁证不能验证本算子的数学或源码分支，只说明静态少 copy、更多槽位及精度通过不能替代整体验速；两个窗口也不是隔离流水收益的对照；两者本轮新负控制未运行，历史控制也不视为本轮控制。前一版本的封存证据（内部归档，社区不可访问）与后一版本终件 SHA-256 `0d63bbd7444eb20c8f32ddda9076e88a1e867db8f905e058dbb8d38c2747a7d2`分别绑定，不拼接结果。

下一次生成应先依据输入 dtype/scale/layout 选择 per-token 分支，明确保留的调度与 raw INT32 边界、被替换的严格钩子、完整行 workspace/同步和部署契约，再列出要验证的首个布局/数值判据。可采用这条范围明确的组装方法，不需要先声称它是唯一实现或普适最优；但新源码/DSO仍须自己的完整精度和性能结果。现有 WHITE_BOX 证据不构成冷黑盒再生成验证，旧黑盒的检索或决策遗漏仍为 UNKNOWN。

## 性能负结果与知识验证边界

后续同一修订合同的另一个融合实现，kernel SHA-256 为 852b97d2665b5ab7a0f3af06bc69f294dae9f2f0171ce772dd292e9941758c5b、DSO 为 4eeabd7e841d656d4273b4cb3126c5cb777390604c8afcb6b1b92c7d9e337923，完整 P50 和 250 个候选计时返回通过；50 例、500 个 Event legs 的等例权重 paired-ratio GM 为 0.05681986528329742，低于该轮 0.8/1.1 门槛。一次窗口，spread 未测；原生参考返回的 25 通过、225 INT8 失败分列保留。这是该具体融合版本的失败结果，不给旧候选转移速度，也不是硬件极限或某条 Div 指令成本的证明。

这些都是披露源码复用的 WHITE_BOX 结果。旧黑盒的实际检索、全文阅读、决策遗漏及原因为 UNKNOWN；独立 CPU 或保存输出 replay 不构成冷黑盒生成验证。后续消费者必须独立绑定知识快照、源码暴露模式和新候选完整实测结果。

[现有 GMM SwiGLU cookbook](../../examples/gmm_swiglu_quant_a8w8_class_template.md) 的 Step 5 提供 dequant/SwiGLU/quant 骨架和特定 reciprocal 经验，不提供本合同的成对 nonlinear/maxabs/RNE 决策闭环。不要把其特定替换规则当成此处精确整数合同的证明。

## 迁移候选：联合 gate/up 权重布局与严格 strip 生命周期

### 触发、合同和取舍

当同一 X tile 对 gate/up 两半分别做 INT8→INT32 contraction，而后续仍必须保留成对非线性和完整 H 行量化时，可评估把同一逻辑 N tile 的两半权重预先放成相邻的物理 2N 列，再调用一次更宽 Matmul。它是固定实验源码与终件（内部归档，社区不可访问）的自定义组合，不是 CANN 原生新增分支或商业二进制实现的证明，也不保证减少一次高层调用就更快。实验 SDK 为9.2.0.B060/arch35；不能把其资源包当成9.1.0或其他 SDK 的 ABI。

该组合只覆盖显式修订的 mode0 合同：INT8 X/W、FP32 token/channel scales、INT64累计/计数 group、无可选 bias/offset；H 为64倍数且不超过1280，保守点积界为 `K*16384<2^31`。严格 values、full-H normalizer 和 LUT 字节保持继承版本；整套布局需要新 core 与新 host-tiler 各自实际绑定。它不覆盖 MX/NZ/FP8，也不提供全域 NaN、FTZ、signed-zero 或任意新 shape 的精度证明。

### 生成时必须同时闭合的布局和 ABI

1. **按逻辑 tile 打包，不能沿用原全行 stride。** 输入权重为 `[E,K,2H]`。对专家 `e`、逻辑列起点 `col`、K 行 `k` 和 `j<N`，两半源地址分别为 `e*K*2H+k*2H+col+j` 与该地址加H；目的地址为 `e*K*2H+col*2K+k*2N+side*N+j`。每个逻辑 tile 形成连续 `[K,2N]`，右半在行内 `+N`。这既不是原始 `[K,2H]` 行距，也不是 FRACTAL_NZ。
2. **把 E 纳入 workspace 与元数据缓存合同。** 三个 full-H high/low/exponent 平面仍占 `M*H*12` bytes，其后增加 `E*K*2H` 个 INT8 bytes；SDK system reservation 单独计入。host-tiler 参数和 shape/device-packet cache key 都包括 `(M,K,H,E)`，避免相同 M/K/H、不同 E 复用过小 workspace。缓存只存 shape/SDK 元数据，不缓存输入值对应的答案。
3. **预打包先完成，才复用 UB。** 当前实现由 MIX 内 AIV 每次处理最多32个 K 行、逻辑N≤128，临时 INT8 UB 为8192B。GM→UB的源 stride 单位是byte、目的 stride 是32B；UB→GM相反，必须按所选重载核对。两半读完后 `MTE2_MTE3`，连续写 packed GM 后 `MTE3_MTE2` 再复用 scratch，所有参与者 `SyncAll` 后才开始 packed Cube 读取。此 scratch 在严格 epilogue 初始化前结束，不能与后阶段峰值简单相加。
4. **SDK 支持、逻辑宽和物理宽一起传递。** 实测50个 SDK shape 包均为 baseM128、baseN256、baseK128；每个 P/Q 进程48个不同MKHE包，共96个实际包与静态包逐字节关联。运行时逻辑N64尾块的联合宽度是128，这是同一baseN256包下的尾宽处理，不是另一个已测baseN128包。逻辑 scheduler、scale 与输出列坐标仍按N，Matmul原始B行距和输出按2N。支持这组包不等于任意 tile 或另一配置可用。

### 完整 producer、strip 和复用信用

| 对象/边 | 当前有界实现 | 生成时的判据 |
|---|---|---|
| Matmul/GetTensorC→raw UB | 一个物理2N结果；目的声明32768个INT32元素，即131072B，覆盖完整M128×256 producer范围 | 不能仅按一个AIV半M或一个strip来分配完整目的view；核对所选Copy policy实际写入范围 |
| 两AIV分M消费 | 每个消费者最多64行，物理行距 `stride=2N`，gate/up在同一行 | raw/scales/group/tail的逻辑坐标保持一致，左右列不能误读成两块紧邻的全矩阵 |
| 严格 scratch 索引 | 继承钩子的物理索引域小于4096，故 `stripRows<=4096/(2N)` | 逻辑N128时最多16行、N64时最多32行；64行消费者可能需要4或2个strip，不能固定“两条32行” |
| strip→三平面GM | high/low和exponent保留物理stride中的空隙，copy仅写逻辑N列；UB源stride以32B计，GM目的stride以byte计 | 每个源地址、行距和extent都以真实布局核对；不能将带孔UB源当成紧密N列 |
| exponent源复用 | 同一个4096元素指数区逐strip重用；每个strip写GM后等 `MTE3_V`，才允许下一次Vector覆盖 | 增加strip数量时必须重新枚举所有异步源生命周期；仅做末尾一次drain不足以保护中间复用 |
| AIV→Cube、最终量化 | 本地最终drain后各AIV归还free；AIC取回两份信用再覆盖raw；最终full-H量化保持全局完成边界 | 初始/每tile/最后信用逐个配平，不能把某个strip完成当成整tile或整行完成 |

当前严格区显式 UB 最高地址为236608B，低于实际目标253952B；这是这组资源和布局的界，不是任意N可用的上限证明。预打包、更多GM写读、更宽Matmul、变小strip和更多等待均有成本。源码中的event和更少高层调用不能单独证明生成指令重叠、A-load降低或性能收益。

strict values继续按原顺序生成 `(high,low,exponent)`。完整 H 到齐后，normalizer只从非零对选择共同rowExponent（全零行取0），先按 `elementExponent-rowExponent` 对齐，再比较绝对值的高低位、归一化和RNE；scale先由对齐域max/127产生，再恢复行指数。零行、有限指数差截断及下溢规则沿冻结 helper，不能把不同指数的原始high/low直接比较，也不能从代数恒等式推出全域位等价。

### 固定验证、反例和下一次决策

终件（内部归档，社区不可访问）绑定新 core `c576708ce5435485fba64a8938161c14569a52e71cb1d0c9f295f8e86ee4fe6d` 与新aux `a7fdabf9debb061dea2cdb5b62dc7c4ca5a4e01d59a75c93ceb2a19fbbfaaa52`：自己的P50与候选Q250返回通过，原生参考25通过/225失败；100份保存的CPU64/input/gold回执、两个返回叶和500条Event分列。完整50例等例权重 median-of-five-paired-ratios GM为0.25333956905290494，仍未达到0.8/1.1。它支持该冻结集合内的整套接线，反驳“把两次Matmul合一次就已达标”；不证明单独的packing、宽N、helper或搬运成本。CPU-only坏输出控制不等于新鲜NPU负对照或冷生成；当前版本无profile，不能借用旧版本或后续独立profile的成本解释。

归档还保留初次错误CMake路径configure rc1/compiler0与随后唯一实际aux/core编译链rc0；辅助FUSION字段仍有旧entryCPP摘要，另附勘误，实际新CPP由两个157文件freeze及构建源码绑定。不要将旧描述或恢复脚本位置当作当前执行身份。原性能失败、历史花费和输入合同不改写。

下一次生成先绑定源码权限、合同与精度钩子，再逐项闭合专家/tile地址、含E的workspace、真实SDK包、完整producer目的区、每个strip物理索引和异步源drain、两消费者信用及full-H同步；任一项未闭合就拒绝该组合。闭合后每个新core/aux组合仍须自己的完整P和条件全分母Q。已曝光源码的具名WHITE_BOX研究按caller授权记录谱系；灰盒/冷验证recipe的访问隔离继续保留，原黑盒失败原因与冷黑盒应用验证仍UNKNOWN。
