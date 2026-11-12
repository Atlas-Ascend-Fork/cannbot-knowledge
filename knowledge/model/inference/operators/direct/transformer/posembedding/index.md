# 位置编码计算

- [FusedRopeQkMqa A2/A3 Direct Invoke 算子知识](sgl_fused_rope_qk_mqa.md)：闭合MQA纯Q/K RoPE的四配对尾部特化、14stride字段和预选cache共享，保留原值尾复制、类型提升及physical资源边界。
- [FusedRopeQkMqa 950 Direct Invoke 算子知识](sgl_fused_rope_qk_mqa_950.md)：闭合MQA纯Q/K RoPE的四配对尾部特化、14stride字段和预选cache共享，保留原值尾复制、类型提升及physical资源边界。
- [SplitQkvRmsnormRope A2/A3 Direct Invoke 算子知识](sgl_split_qkv_rmsnorm_rope.md)：闭合QKV拆分的16种norm/bias/partial/配对特化与KVhead网格，记录FP32连续计算、bias源码读集合、表读取及arange准入边界。
- [SplitQkvRmsnormRope 950 Direct Invoke 算子知识](sgl_split_qkv_rmsnorm_rope_950.md)：闭合QKV拆分的16种norm/bias/partial/配对特化与KVhead网格，记录FP32连续计算、bias源码读集合、表读取及arange准入边界。
- [SplitQkvRmsnormRopePosCacheHalf A2/A3 Direct Invoke 算子知识](sgl_split_qkv_rmsnorm_rope_pos_cache_half_npu.md)：闭合位置cache QKV融合的16网格与舍入特化、自有RNE helper和int32后clamp，计入共享频率读取与连续化，保留物理编译边界。
- [SplitQkvRmsnormRopePosCacheHalf 950 Direct Invoke 算子知识](sgl_split_qkv_rmsnorm_rope_pos_cache_half_npu_950.md)：闭合位置cache QKV融合的16网格与舍入特化、自有RNE helper和int32后clamp，计入共享频率读取与连续化，保留物理编译边界。
- [SplitQkvTpRmsnormRopeTp1 A2/A3 Direct Invoke 算子知识](sgl_split_qkv_tp_rmsnorm_rope_tp1.md)：闭合tp_world1的QKV拆分本地均方与RMS/RoPE双Kernel图，记录补偿式累加、8B统计GM与低dtype写回重读精度边。
- [SplitQkvTpRmsnormRopeTp1 950 Direct Invoke 算子知识](sgl_split_qkv_tp_rmsnorm_rope_tp1_950.md)：闭合tp_world1的QKV拆分本地均方与RMS/RoPE双Kernel图，记录补偿式累加、8B统计GM与低dtype写回重读精度边。
- [SplitQkvgateGemmaRmsnormRope A2/A3 Direct Invoke 算子知识](sgl_split_qkvgate_gemma_rmsnorm_rope.md)：闭合逐head Q/gate解交错、Gemma1+weight的FP32 RMSNorm与NeoX、gate/V输出，保留完整Host及PASS_DIM0和arange编译准入。
- [SplitQkvgateGemmaRmsnormRope 950 Direct Invoke 算子知识](sgl_split_qkvgate_gemma_rmsnorm_rope_950.md)：闭合逐head Q/gate解交错、Gemma1+weight的FP32 RMSNorm与NeoX、gate/V输出，保留完整Host及PASS_DIM0和arange编译准入。
