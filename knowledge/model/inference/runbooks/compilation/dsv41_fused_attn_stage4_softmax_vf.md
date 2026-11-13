---
{
  "type": "Runbook",
  "title": "dsv41_fused_attn Stage 4 device softmax（_softmax_w）修复：测试 valid 传参",
  "description": "在 Ascend950DT 上排查 dsv41_fused_attn Stage 4（STAGE_SMW device softmax）与宿主 _h_softmax 对拍的剩余失败：真因是测试把 [1,1] dummy 当作 kernel 第 3 参（valid 标志）传入，修正是传真实 flags（valid_dev = vflag_h.to(dev).contiguous()）。验证层级 device_functional。",
  "tags": [
    "task.implementation",
    "topic.attention"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": [
    "950"
  ]
}
---
# dsv41_fused_attn Stage 4 device softmax（_softmax_w）修复：测试 valid 传参

- knowledge_form: repair_recipe | route: inference | area: compilation

## 适用场景

适用于在 Ascend NPU（Ascend950DT 等 A5 类卡）上用 PyPTO Pro（pypto_pro VF API）开发/修复 dsv41_fused_attn 类融合注意力 kernel 的工程师：涉及 device softmax（STAGE_SMW Stage 4）使能、以及“kernel 已对而测试 harness 传错参”的排查场景。

## 触发与观测

触发与初始状态：任务书要求把未启用的 Stage 4（device softmax，STAGE_SMW，约 350 行）修到与宿主 _h_softmax 逐元素对拍。

失败信号：第一轮修复后 stage4 对拍仍失败——AssertionError [topk_prefix_37_64] max|d_w|=1.000e+00 at (0,31)，#>atol=744；[lpad64_t2h8] max|d_w|=1.000e+00 at (0,27)，#>atol=896。

## 探针与操作

探针与操作（本轨迹实际执行的排查链）：

1. 在 kernel 内把 den 计算替换为哨兵常量（den = 12345.0 + 0.0 * pl.getval(...)，）→ 探针输出 den dev 全 12345.0、nonzero elems 0→ 说明 den 哨兵已写出，而 p_w 权重仍全零；应优先检查 valid 输入。
2. 写独立 probe（probe_vf_min/probe_vf_replica/probe_real_smw）在 kernel 外复现 VF 调用；把 probe 传给 kernel 的第 3 个张量从 dd 换成 va（真实 valid flags）后立即 nonzero 208、max diff 5.96e-08→ 该 probe 下对拍通过，调用侧 valid 传参是已核实的失败因素；不外推全部形状正确。
3. 定位测试 harness：cube 入口因自身 stage 不读 valid 槽而传 [1,1] dummy，测试沿用了 dummy——Stage 4 读该槽导致所有 lane 判无效；修正测试传 valid_dev = vflag_h.to(dev).contiguous()。

来源结论（真因与修正）：
修复 kernel 后测试仍 max|d_w|=1.000e+00（#>atol=744/896）且边界用例（全无效行/topk_zero）0.000e+00 通过；用 12345.0 哨兵替换 den 计算的探针显示 den 输出全为哨兵 12345.0，p_w 的 nonzero elems 为 0；不能据此称全部输出均未写出。真因在测试/探针侧：kernel 第 3 参是 vf 路径的 valid 标志，cube 入口因自身 stage 不读该槽而传 [1,1] dummy，测试沿用了 dummy——Stage 4 读该槽导致所有 lane 判无效。修正是测试传真实 flags：valid_dev = vflag_h.to(dev).contiguous()（探针同步把第 3 参换成 va 后 kernel 立即对拍通过：nonzero 208、max diff 5.96e-08）。


## 机制与判别

机制与判别（真因与修正在 来源结论，见探针与操作节）：

测试 harness 修正（来源修改片段）：

```
        dq = torch.zeros((1, 1, HEAD_DIM), dtype=torch.float32, device=dev)
        dsc = torch.zeros((1, 1, 1), dtype=torch.float32, device=dev)
        dd = torch.zeros((1, 1), dtype=torch.float32, device=dev)
        # Stage 4 reads the *vf-path* ``valid`` parameter, so it must hold the
        # real flags (the cube entry leaves this slot as a [1, 1] dummy because
        # its own stages never read it).
        valid_dev = vflag_h.to(dev).contiguous()
        dpay = torch.zeros((1, 1), dtype=torch.uint8, device=dev)
        dsca = torch.full((1, 1, 2), 127, dtype=torch.uint8, device=dev) \
            .view(torch.float8_e8m0fnu)
        out_dequant = torch.zeros((t_total, h_total, HEAD_DIM),
                                  dtype=torch.float32, device=dev)

        sc_c = torch.zeros((t_total * 64, lpad), dtype=torch.float32, device=dev)
        p_w = torch.zeros((t_total * 64, lpad), dtype=torch.float32, device=dev)
        attn_c = torch.zeros((t_total * 64, HEAD_DIM), dtype=torch.float32,
                             device=dev)
        den_c = torch.zeros((t_total * 64,), dtype=torch.float32, device=dev)

        tensors = (
            dq, dq, valid_dev, dsc, dq, dd,   # vf tensors (valid is real)
            q_pay, q_sc, kt_pay, kt_sc, v_pay, v_sc,
            dpay, dsca, p_w, sc_c, attn_c, den_c,
            qcos, qsin, sink_t, topk_t, out_dequant,
        )
```

## 验证信号

验证信号（device_functional 级）：

- 探针对拍：把传给 kernel 的第 3 个张量换成 va（真实 valid flags）后立即 nonzero 208、max diff 5.96e-08。
- 修正后测试传 valid_dev = vflag_h.to(dev).contiguous()。

## 适用与失效边界

适用边界：PyPTO Pro VF API kernel 的测试与调用方传参约定。失效/不适用：测试/调用方必须给 vf 路径第 3 参传真实 valid 标志（cube 入口的 dummy 约定不能沿用）。
