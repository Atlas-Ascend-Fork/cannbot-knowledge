---
{
  "type": "Runbook",
  "title": "pypto.assemble 在 l_max>32 且 tile_bt>1 时写回错误——block_attn_res 前后向 kernel 改用条件 unroll_list",
  "description": "PyPTO（tile 编译框架，Ascend NPU 后端，TILE_FWK_DEVICE_ID + PTO_TILE_LIB_CODE_PATH 环境）上开发 block_attn_res 类融合算子（RMSNorm + attention scores matmul + softmax + weighted summation matmul + assemble 写回）时，出现「forward 输出在 assemble 之前全部正确、写回后错误」的精度问题。适用于 l_max 分档（32/64/96+）与 loop_unroll tile_bt 组合的精度排障，以及 PyPTO 框架 assemble/valid_shape 语义缺陷的定位。",
  "tags": [
    "task.debugging",
    "topic.attention"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": []
}
---
# pypto.assemble 在 l_max>32 且 tile_bt>1 时写回错误——block_attn_res 前后向 kernel 改用条件 unroll_list

## 适用场景

PyPTO（tile 编译框架，Ascend NPU 后端，TILE_FWK_DEVICE_ID + PTO_TILE_LIB_CODE_PATH 环境）上开发 block_attn_res 类融合算子（RMSNorm + attention scores matmul + softmax + weighted summation matmul + assemble 写回）时，出现「forward 输出在 assemble 之前全部正确、写回后错误」的精度问题。适用于 l_max 分档（32/64/96+）与 loop_unroll tile_bt 组合的精度排障，以及 PyPTO 框架 assemble/valid_shape 语义缺陷的定位。

## 触发与观测

触发：`python3 build_ci.py -f=python3 -c -s="models/kimi/test_block_attn_res.py::test_block_attn_res"` 两个用例精度失败。

## 探针与操作

- PyPTO FAQ 检索：view-valid-shape-precision.md（view 未传 valid_shape 导致精度问题）、view-assemble-cycle.md、loop-principle.md。

## 机制与判别

修复：

```python
    bt, l, d = v_flat.shape  # noqa: E741
    dtype = v_flat.dtype
    if l_max == 32:
        unroll_list = [1, 64, 128]
    else:
        unroll_list = [1]
    norm_m_tile = 64 * 1024 // (4 * d)
    norm_m_tile = max(norm_m_tile, 1)

    if d == 512:
        pypto.set_pass_options(
            vec_nbuffer_setting={"DEFAULT": 8},
            cube_nbuffer_setting={"DEFAULT": 8, "func8_0": 16},
            cube_l1_reuse_setting={"DEFAULT": 2},
        )
    elif d == 1536:
        pypto.set_pass_options(
            vec_nbuffer_setting={"DEFAULT": 8, "func8_2": 48},
            cube_nbuffer_setting={"DEFAULT": 16},
            cube_l1_reuse_setting={"DEFAULT": 2},
        )

    pypto.experimental.set_operation_options(combine_axis=True)

    for bt_idx, unroll_length in pypto.loop_unroll(
        0,
        bt,
        1,
        name="Block_attn_Res_T_Loop",
        idx_name="bt_idx",
        unroll_list=unroll_list,
    ):
```

（反向 kernel 同型修改：l_max==32 时 [1,64]、否则 [1]。）

- 修复：block_attn_res_impl.py 前向 kernel l_max==32 时 unroll_list=[1,64,128]、否则 [1]；反向 kernel l_max==32 时 [1,64]、否则 [1]。修复后 b1_t1023_n32_d512_bf16 与 b2_t4096_n25_d512_bf16 均 PASSED（全文件 2 passed），l_max=32 快路径不受影响。

## 验证信号

- b1_t1023_n32_d512_bf16 单测 PASSED（1 passed）；b2_t4096_n25_d512_bf16（l_max=32 路径）PASSED；全文件 `2 passed`。
- 最终 diff 复核确认修改仅含条件 unroll_list 与 loop 名调整；临时诊断脚本清理。
- 验证层级：device_functional（Ascend910 NPU 实测 pytest）。

## 适用与失效边界

- 该 workaround 以「l_max>32 时牺牲 unroll 吞吐」换取正确性；框架侧根治需修 pypto.assemble/loop_unroll 对 l_max>32 多行写回的处理。
- l_max=32 档保持 [1,64,128] 快路径；新 l_max 档（96/128+）默认全部 [1]，待框架修复后可恢复。
- 案例来自 bf16/D=512/bt 大（t=1023/4096）形态；其他 dtype/维度未逐一回归。
- glm_v4_5 attention_fusion 的精度问题（同会话后半段）与本案不同源，本候选不覆盖其结论。
