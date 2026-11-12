# 激活计算

- [SGL逐元素sigmoid门控 A2/A3 Direct Invoke 算子知识](sgl_fused_sigmoid_mul.md)：还原fused_sigmoid_mul在A2/A3的FP32门控融合、连续化、grid与尾块掩码，并区分独立实现的前提和公共wrapper校验。
- [SGL逐元素sigmoid门控 950 Direct Invoke 算子知识](sgl_fused_sigmoid_mul_950.md)：还原fused_sigmoid_mul在950的FP32门控融合、连续化、grid与尾块掩码，并区分独立实现的前提和公共wrapper校验。
- [SGL逐行广播sigmoid门控 A2/A3 Direct Invoke 算子知识](sgl_fused_sigmoid_mul_broadcast.md)：还原fused_sigmoid_mul_broadcast在A2/A3的FP32门控融合、连续化、grid与尾块掩码，并区分独立实现的前提和公共wrapper校验。
- [SGL逐行广播sigmoid门控 950 Direct Invoke 算子知识](sgl_fused_sigmoid_mul_broadcast_950.md)：还原fused_sigmoid_mul_broadcast在950的FP32门控融合、连续化、grid与尾块掩码，并区分独立实现的前提和公共wrapper校验。
- [GateMultiplyLargeContiguous A2/A3 Direct Invoke 算子知识](sgl_gate_multiply_large_contiguous.md)：闭合N不少于16777216且双连续的BF16×FP32 gate乘法自有Kernel域，保留全入口Torch缺源、设备缓存与950未验证边界。
- [GateMultiplyLargeContiguous 950 Direct Invoke 算子知识](sgl_gate_multiply_large_contiguous_950.md)：闭合N不少于16777216且双连续的BF16×FP32 gate乘法自有Kernel域，保留全入口Torch缺源、设备缓存与950未验证边界。
- [旧SwiGLU逐行INT8 A3 Direct Invoke 算子知识](sgl_legacy_swiglu_int8.md)：闭合旧SwiGLU在A3的SiLU后可选限幅与逐行INT8、四条分组路线、完整Triton参数/资源/同步；警示cumulative越视图、1536尾slice和零scale，保持draft。
- [旧SwiGLU逐行INT8 950 Direct Invoke 算子知识](sgl_legacy_swiglu_int8_950.md)：闭合旧SwiGLU在950的SiLU后可选限幅与逐行INT8、四条分组路线、完整Triton参数/资源/同步；警示cumulative越视图、1536尾slice和零scale，保持draft。
- [SituAndMul A2/A3 Direct Invoke 算子知识](sgl_situ_and_mul.md)：闭合浮点SiTU四列块与24特化、设备端group有效前缀、FP32饱和及int64行地址，区分Direct未调公共check和int32调度容量。
- [SituAndMul 950 Direct Invoke 算子知识](sgl_situ_and_mul_950.md)：闭合浮点SiTU四列块与24特化、设备端group有效前缀、FP32饱和及int64行地址，区分Direct未调公共check和int32调度容量。
- [SwigluOaiFloat A2/A3 Direct Invoke 算子知识](sgl_swiglu_oai_float.md)：闭合need_quantFalse的浮点OAI激活与三group有效前缀，明确所有scale未定义、无1536量化slice及整行/整数/编译资源边界。
- [SwigluOaiFloat 950 Direct Invoke 算子知识](sgl_swiglu_oai_float_950.md)：闭合need_quantFalse的浮点OAI激活与三group有效前缀，明确所有scale未定义、无1536量化slice及整行/整数/编译资源边界。
- [SwigluOaiQuant A2/A3 Direct Invoke 算子知识](sgl_swiglu_oai_quant.md)：闭合need_quantTrue的OAI激活与逐行INT8量化、三group有效前缀和1536切片，保留输入dtype舍入、零scale与整行资源准入。
- [SwigluOaiQuant 950 Direct Invoke 算子知识](sgl_swiglu_oai_quant_950.md)：闭合need_quantTrue的OAI激活与逐行INT8量化、三group有效前缀和1536切片，保留输入dtype舍入、零scale与整行资源准入。
