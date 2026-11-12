# 索引与缓存搬运

- [AllocExtend A2/A3 ACLNN 算子知识](sgl_alloc_extend.md)：闭合 aclnnSglAllocExtend 在A2/A3上的分页槽位、四字段Tiling、单AIV节点和生命周期；记录3A字节UB分配被A/2A元素偏移越界的静态缺陷，不代表可安全复用或真机复现。
- [AllocExtend 950 ACLNN 算子知识](sgl_alloc_extend_950.md)：闭合 aclnnSglAllocExtend 在950上的分页槽位、四字段Tiling、单AIV节点和生命周期；记录3A字节UB分配被A/2A元素偏移越界的静态缺陷，不代表可安全复用或真机复现。
- [ApplyTokenBitMask A2/A3 ACLNN 算子知识](sgl_apply_token_bitmask.md)：闭合 aclnnSglApplyTokenBitMask 在 A2/A3 上的原地词表掩码、九字段POD、三dtype与UB双缓冲；区分严格raw工作张量和外部Torch选行补齐，待上机验收。
- [ApplyTokenBitMask 950 ACLNN 算子知识](sgl_apply_token_bitmask_950.md)：闭合 aclnnSglApplyTokenBitMask 在 950 上的原地词表掩码、九字段POD、三dtype与UB双缓冲；区分严格raw工作张量和外部Torch选行补齐，待上机验收。
- [AssignCache A2/A3 ACLNN 算子知识](sgl_assign_cache.md)：闭合 aclnnSglAssignCache 在A2/A3上的四carrier模板、20字节Tiling、UB分块、32字节尾块读改写和IB同步；记录未校验的范围、sync跨度单位及取整重叠风险，不宣称安全复用或运行复现。
- [AssignCache 950 ACLNN 算子知识](sgl_assign_cache_950.md)：闭合 aclnnSglAssignCache 在950上的四carrier模板、20字节Tiling、UB分块、32字节尾块读改写和IB同步；记录未校验的范围、sync跨度单位及取整重叠风险，不宣称安全复用或运行复现。
- [CacheLocAssign A2/A3 ACLNN 算子知识](sgl_cache_loc_assign.md)：闭合 aclnnSglCacheLocAssign 在A2/A3上从打包源scatter写pool的两条行号路线、128字节Tiling、固定SDK减法与UB/同步；记录guard计费不足、padding及16元素窗口边界，不代表运行正确或安全复用。
- [CacheLocAssign 950 ACLNN 算子知识](sgl_cache_loc_assign_950.md)：闭合 aclnnSglCacheLocAssign 在950上从打包源scatter写pool的两条行号路线、128字节Tiling、固定SDK减法与UB/同步；记录guard计费不足、padding及16元素窗口边界，不代表运行正确或安全复用。
- [CacheLocUpdate A2/A3 ACLNN 算子知识](sgl_cache_loc_update.md)：闭合 aclnnSglCacheLocUpdate 在A2/A3上单核从pool打包读出到packed_ref的两路线、128字节POD与固定SDK Sub；记录UB guard、对齐预读、空段16项读取及整S输出边界，不代表运行正确。
- [CacheLocUpdate 950 ACLNN 算子知识](sgl_cache_loc_update_950.md)：闭合 aclnnSglCacheLocUpdate 在950上单核从pool打包读出到packed_ref的两路线、128字节POD与固定SDK Sub；记录UB guard、对齐预读、空段16项读取及整S输出边界，不代表运行正确。
- [KvCompressEpilogFP8 950 ACLNN 算子知识](sgl_kv_compress_epilog_fp8_950.md)：aclnnSglKvCompressEpilog 的quant_mode为1时FP8/RoPE/FP32scale打包与176字节POD；索引预算和窄化、D对齐/奇数RoPE偏移及UnAlign读取256字节Reg可能跨当前槽的限制，draft未运行验证。
- [KvCompressEpilogMXFP8 950 ACLNN 算子知识](sgl_kv_compress_epilog_mxfp8_950.md)：蒸馏aclnnSglKvCompressEpilog模式2的E8分组量化、两种缓存布局和48个VF实例，记录索引预算、槽位窄化、RoPE步长与未掩码读取、scale填充等静态限制。
