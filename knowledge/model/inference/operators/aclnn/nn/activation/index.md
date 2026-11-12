# 激活计算

- [SiTU MXFP8 量化 950 ACLNN 算子知识](sgl_situ_mxfp8_quant_950.md)：闭合950上aclnnSglSituMxfp8Quant的两计数路线、24B POD、58848B UB及SDK9.2量化同步；警示计数窄化、分核溢出与CTRL60初始化顺序风险，未运行验证。
- [SwigluGroupQuantBlockFP8 950 ACLNN 算子知识](sgl_swiglu_group_quant_block_fp8_950.md)：aclnnSglSwigluGroupQuant 的quant_mode为3时128值FP8量化及128个VF属性组合、212字节POD；E8非round写入类型/范围与group加origin加weight的bufID条件，draft未运行验证。
- [SwigluGroupQuantFP8 950 ACLNN 算子知识](sgl_swiglu_group_quant_fp8_950.md)：aclnnSglSwigluGroupQuant 的quant_mode为1时128值FP8量化、16个VF实例、212字节POD及专家前缀/UB池复用；CTRL60单指令模式与未写origin边界，draft未运行验证。
- [SwigluGroupQuantMXFP8 950 ACLNN 算子知识](sgl_swiglu_group_quant_mxfp8_950.md)：aclnnSglSwigluGroupQuant 的quant_mode为2时32值MXFP8指数位量化、16个VF实例与212字节POD；尾块四mask写出队列槽及无mask局部读跨度风险，draft未运行验证。
