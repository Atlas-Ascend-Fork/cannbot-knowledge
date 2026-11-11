# 进化失败模式（Failure Patterns）

AscendC 算子性能进化中已被证实的失败组合，用于在 partial 启动前给出 anti 提示，避免重复踩坑。机器可读元数据（phenomenon / severity / failed_combination / operator_type / occurrences）同时保存在 `ascendc-evolution-knowledge/references/okf_compat.json`，由 `generate_index_json.py` 合并进 `INDEX.json`。

- [F1: P22+A1:reduction:tail_precision](f1_p22_a1_reduction_tail_precision.md)：精度失败，ulp 误差集中在最后一个 tile（尾块未对齐 32B）。
- [F2: multi-kernel:cube_registration](f2_multikernel_cube_registration_breaks.md)：910B2C 上做多 kernel Cube 流水线（im2col AIV + wrepack AIV + GEMM AIC + epilogue AIV，5 个 `extern "C" __global__` kernel 写在一个 `o
- [F3: manual-mmad:loaddata3d-16x16-only](f3_manual_mmad_loaddata3d_16x16_trap.md)：手动 mmad kernel 用 `LoadData3D`（L1→L0A/L0B 的 tile 加载辅助函数）做分形搬运时，**只对 16x16x16 identity 输出正确**；对真实 shape（32x128、32x48、13x29
- [F4: MTE1_M+M_MTE1:L0A/L0B:event_window_conflict](f4_l0a_l0b_event_window_conflict.md)：批量/连续 launch 时随机（大 shape 0–2 次迭代内、小 shape 40 次不现）报：
- [F5: cv_split_fa:ring_iteration_cost:gm_bytes_bound](f5_cv_split_fa_ring_cost_equals_gm_bytes.md)：CV 分离（AIC 算 QK^T/P@V，AIV 算 softmax，S/P 经 GM workspace 中转）的 FA 内核，
- [F6: P4+P140+P142:attention:dc-split-doubles-gather](f6_dc_split_doubles_kv_gather.md)：P4+P140+P142:attention:dc-split-doubles-gather (performance_negative)
- [F7: P61+P125:attention:mte2-inorder-hoist-gather-blocks-c2](f7_mte2_inorder_hoist_gather_blocks_consumer.md)：P61+P125:attention:mte2-inorder-hoist-gather-blocks-c2 (performance_negative)
- [F8: HSetFlag+MemoryT::L0B:mixed_entry_sequence:507014](f8_hflag_l0b_coherent_mixed_entry_hang.md)：用硬件 L0 一致性 flag（`HSetFlag/HWaitFlag<HardEvent::M_MTE1|MTE1_M, MemoryT::L0B, false>`）替换
- [F9: eval_harness:msprof_case_loader:root_jsonl_poisoning](f9_msprof_case_loader_jsonl_poisoning.md)：进化变体的 canonical `evaluation_results.json` 里 `timing_summary.n_cases_total` 变成 10（或 6/16 等），
