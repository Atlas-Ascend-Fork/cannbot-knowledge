# 硬件参考

Ascend 910B/910_95/950PR/910C 硬件规格与强制约束速查。生成任何 Triton Ascend kernel 之前必须过一遍约束检查清单。

- [ascend_910b](ascend_910b.md)：910B2/910B3 核心架构、Grid 语义、内存层次、编译选项
- [ascend_910_95](ascend_910_95.md)：910_95/950PR/950DT（dav-c310，Reg-based A5 架构）核数、UB/L1/L0C 容量、专有数据通路与 910B 差异
- [NPU 内存层次与数据通路模型](npu_memory_model.md)：Ascend NPU 的 GM/L1/UB/L0A/L0B/L0C 存储层次、容量与对齐约束、MTE/FIX 数据通路及 tl.load/tl.store/tl.dot 的硬件映射。
- [constraints_cheatsheet](constraints_cheatsheet.md)：强制约束速查（UB/Gird/对齐） + 性能约束 + autotune 搜索空间
- [ascend_patterns](ascend_patterns.md)：Ascend 特有的编程模式与 GPU→Ascend 迁移差异
- [Ascend950PR (David V100) -- Target Platform](target_ascend950pr.md)：950PR（DAV_3510/arch35）完整平台规格：核数、UB/L1/L0 容量、6 管线与 Scalar 单元、SIMT+SIMD 模型、原子操作、跨核同步、Cube 数值行为与已知缺陷（手册+白皮书+实测）。
- [Ascend950DT_9582 -- Target Platform](target_ascend950dt.md)：950DT 主卡——与 950PR 共架构、内存/SKU 级差异；三级证据标注约定；子卡索引见卡内。
- [Ascend910C (DaVinci V220, dual-die) — Target Platform](target_ascend910c.md)：910C（A3）平台规格：SIMD-only、80~96 AIV、UB 192KB/AIV、L0C 128KB、SOC 字符串与构建参数、与 A5 移植差异及待实测项。
- [Ascend910B (DaVinci V220) — Target Platform](target_ascend910b.md)：910B（A2）平台规格：SIMD-only、B1–B4 SOC 型号、UB 192KB/AIV、L0C 128KB、构建参数与待上机验证项。

- [Ascend950 微架构（Cube/Vector/CV 通道/NDDMA/BufferID）](ascend950_microarchitecture.md)：950 系列共架构微架构：芯片组成（2 AI Die + 2 IO Die）、Cube Core 脉动阵列与数值行为、Vector Core 双发射 SIMD、SIMD/SIMT 混合编程、Cube↔Vector 直通通道、NDDMA 五维重排、BufferID 同步原语、L2 特性。
- [Ascend950 每核存储层次与 UB 双口径](ascend950_per_core_memory.md)：950 系列（PR/DT 共架构）每 AI Core 的 L1/L0A/L0B/L0C/UB 容量；UB 512KB 物理（白皮书口径）vs 248KB 可用（CANN 平台配置口径）的双口径澄清——kernel authoring 和 tiling 预算以 248KB 为安全天花板，代码必须 GetCoreMemSize(UB) 不得硬编码。
- [Ascend950 调度器 / 互连 / DVPP](ascend950_scheduler_interconnect.md)：950 系列共架构：STARS2.0 硬件调度器（任务流/资源池/同步标志）；UB 2.0 互连（HiLink SerDes、UBoE、URMA、CCU 集合通信、片上交换）；PCIe 5.0；DVPP 编解码配置。
- [Ascend950DT 实测观测与方法学警告](ascend950dt_measured_observations.md)：一台 950DT 主机的实测值（CANN 9.1.0, 2026-09-05）：matmul fp16/bf16 430.4 TFLOP/s、HBM 大缓冲平台期 2.7–3.1 TB/s、conv fp16 353–364、conv fp32 HF32 开 176–183/关 26.9；测量陷阱：小缓冲带宽假象、matmul 不能当 conv 上限、SKU 未定。
- [Ascend950DT vs 950PR 差异与 SKU 表](ascend950dt_vs_pr_overrides.md)：950DT 相对 950PR 的全部差异字段：片上高速内存容量/带宽（headline）、AI 子系统 SKU 核数、分格式算力（MXFP4/FP8/BF16/TF32/INT）、L2、AI CPU；SKU 必须按设备实证不可按型号推。
- [Ascend310P (dav-m200 / 200x) -- Target Platform](target_ascend310p.md)：Ascend310P（dav-m200/200x）目标平台参考：交叉编译限定的证据契约，含 SoC 身份、能力清单与证据 JSON 说明

- [AscendC 芯片别名与 NpuArch 映射表](ascendc_chip_alias_and_npu_arch_map.md)：AscendC 统一芯片调用名、产品系列别名（A2/A3/A5）、SocVersion 与 __NPU_ARCH__ 数值的对应关系，以及为什么产品名不能直接推断接口支持面、映射漂移时从哪里发现。
- [API 文档产品标签到 platforms 枚举的映射](ascendc_product_label_to_platform_values.md)：把 API 内容页产品支持章节的 npu 标签（950/A3/910b/310b/310p/910/x90/9030）翻译成知识卡 platforms 枚举（950/a3/a2/310p/910/kirin_x90/kirin_9030），点出两个易错点——910b 对应的是 a2 而不是 910、310b 在本仓没有对应取值，并说明标签的 HTML 注释形态与"文档口径优先"的边界。
