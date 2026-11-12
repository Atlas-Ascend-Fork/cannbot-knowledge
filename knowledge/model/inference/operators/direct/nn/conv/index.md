# 卷积计算

- [原生因果卷积 Prefill A3 Direct Invoke 算子知识](sgl_causal_conv1d_prefill.md)：闭合原生causal_conv1d的A3因果prefill、12条AIV路线、初态快照、滚动partial及状态写回；记录dtype缓存与selector窄化等静态风险，保持draft。
- [原生因果卷积 Prefill 950 Direct Invoke 算子知识](sgl_causal_conv1d_prefill_950.md)：闭合原生causal_conv1d的950因果prefill、12条AIV路线、初态快照、滚动partial及状态写回；记录dtype缓存与selector窄化等静态风险，保持draft。
- [原生统一因果卷积 Update A3 Direct Invoke 算子知识](sgl_causal_conv1d_unified_update.md)：闭合run_mode1统一因果卷积在A3的dense/packed与K4投机状态路线、27字段POD、188416B UB及同步；保留dtype缓存和状态容量等静态风险，保持draft。
- [原生统一因果卷积 Update 950 Direct Invoke 算子知识](sgl_causal_conv1d_unified_update_950.md)：闭合run_mode1统一因果卷积在950的dense/packed与K4投机状态路线、27字段POD、188416B UB及同步；保留dtype缓存和状态容量等静态风险，保持draft。
- [旧原生因果卷积 Update A3 Direct Invoke 算子知识](sgl_causal_conv1d_update.md)：闭合旧torch.ops.npu.causal_conv1d_update的Host预移、8条单/多launch路线、14字段POD、对齐UB与状态提交；明确短序列、pad偏移及accepted边界，保持draft。
- [SGL 因果状态卷积 v2 A3 Direct Invoke 算子知识](sgl_causal_conv1d_update_v2.md)：闭合 causal_conv1d_update_v2 的39参数、八实现族及原地状态与workingX生命周期；限定FP16中间精度、APC/packed弱guard与小通道arange48编译前提。
