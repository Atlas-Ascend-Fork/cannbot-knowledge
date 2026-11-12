# 融合 Kernel

- [Compressor (C4A / C128A KV 压缩融合算子)](compressor.md)：V4 C4A/C128A 压缩算法、当前独立 RMSNorm/RoPE 与缓存写回；区分 HiF8、FP8 和离线/在线 CP 状态生命周期。
- [Deepseek Indexer Attention Kernel](deepseek_indexer_attention.md)：`Deepseek Indexer Attention` (DIA) 是 cann-recipes-infer 用 **PyPTO** 实现的**大融合算子** —— 把 DSA 的 4 个相对独立子算子 MLAProlog + IndexerProlog + Lightning Indexer + Sparse Flash Attention 融合成单一 kernel，在整网范围内挖掘更大并行度、提升内存利用率。这是 PyPTO "MegaKernel" 能力在 DeepSeek-V3.2-Exp 上的典型实例。 PyPTO 源码：`ops/pypto/src/deepseek_indexer_attention/op_kernel/deepseek_indexer_attention.cpp`。
- [FIA v1/v2：参数名、TND/Paged NZ 布局与分路径 mask](fused_infer_attention_score.md)：TND Prefill 不等长请求的 KV 长度：Qwen Dense 分页路径传普通原值，Qwen3-MoE 直读路径传累加长度；区分 v1/v2、Paged NZ、float8 Decode mask，以及 6.0 v1 全遮蔽行和 BSH 单 Query 边界。
- [GatherSelectionKvCache](gather_selection_kv_cache.md)：说明TopK选择缓存复用、当前packed TND调用和workspace来源，区分Host卸载场景与算子可接受的device输入。
- [Indexer Prolog Kernel](indexer_prolog.md)：区分 V3.2 的 PyPTO 三流融合与 V4 压缩 K、HiF8/FP8/Int8 Q 前处理，并修正 GLM-5 模型身份和当前 FP8 支持。
- [Lightning Indexer Kernel](lightning_indexer.md)：LI 的精确 TopK、当前 V4 压缩长度/余数与 Int8、FP8、HiF8 模式，以及 CP 临时缓存和 metadata 配对。
- [mambav2_rmsnormgated](mambav2_rmsnormgated.md)：AscendC 实现的 Mamba v2 风格 RMSNorm + SiLU(z) + Mul 融合算子，Qwen3-Next gated-deltanet 输出段使用。BF16 输入输出（`x`, `z`, `w`），FP32 内部计算，单 AIV kernel 完成归一化、门控激活、权重缩放和逐元素相乘，消除三次独立 kernel launch 和两次中间 BF16 转存。
- [HcPre / HcPost (mHC 融合算子)](mhc_hcpre_hcpost.md)：`HcPre` 与 `HcPost` 是 DeepSeek-V4 mHC 残差结构的成对融合算子，完成 Attention/MoE 子层前后的多路↔单路变换。HcPre 融合 RMSNorm、hc_fn 线性变换、Sinkhorn-Knopp 和 pre 加权求和，输出 y、post、comb；HcPost 用 post 扩展子层输出并与 comb 残差合并，目标是让中间数据留在 UBuffer。A3 AscendC 采用 Cube:Vector=1:2 流水，Decode 切 K、Prefill 切 token；PyPTO 以 MPMD 并行 Vector RMSNorm 与 Cube MatMul，并用 split-K 和静态展开。VF 的历史测量另见来源观测。Native 与 PyPTO 的首轮 Sinkhorn 均先行归一再列归一，数值实现细节以各自代码为准。
- [npu_mla_prolog (v2 / v3)](mla_prolog.md)：R1 packed MLAProlog v3 与量化模式、当前 V4 Partial RoPE/HiF8 helper、A3 PyPTO 和 CP/Decode 分派边界。
- [recurrent_gated_delta_rule](recurrent_gated_delta_rule.md)：Next自研GDN递推kernel与当前Qwen3.5原生API的输入/状态边界，后者只支持非投机Decode。
- [SparseAttnSharedKV (SAS) Kernel](sparse_attn_sharedkv.md)：V4 Shared-KV Attention 的 SWA/CSA/HCA 算法与当前 SparseFlashMLA 三种入口、PA_BBND、压缩长度余数和 metadata 配对。
- [Sparse Flash Attention Kernel](sparse_flash_attention.md)：保留 SFA 的 A3 离散访存与 TileLang 算法，更新当前 packed、C8 返回值及 Offload 有效 token 缓存契约。

- [SGLang 公共算子注册、架构检测与显式后端分发](sgl_operator_registry.md)：解释 register_operator/register_impl 的进程级架构缓存、互斥支持集、auto别名、惰性加载和无回退错误分类。
