---
{
  "type": "Runbook",
  "title": "inductor_npu_ext 放开 sigmoid_backward decompose 白名单并双环境同步验证",
  "description": "在 inductor_npu_ext 的 decomposition.py `_whitelist_decompositions()` 无条件追加 sigmoid_backward 与 conj_physical 两个 keep 行，使 aten.sigmoid_backward 经 torch.compile(ascendc) 分解为 sub+mul×2 并与前后 elementwise 算子融合为单 kernel；前置核对分解链子算子已在 lowering 白名单且 AF v1 Sub/Mul 支持 fp16/fp32。实测于 Ascend910（A3）：2 个新增 smoke 用例在 torch 2.9 与 torch 2.12（同步 site-packages 副本：备份+编辑+py_compile+重跑）双环境通过，LowerSummary 全 Lowered 无 Fallback。",
  "tags": [
    "task.implementation",
    "topic.compilation"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-03T12:00:00Z",
  "updated_at": "2026-11-06T09:40:40Z",
  "platforms": [
    "910"
  ]
}
---

# inductor_npu_ext 放开 sigmoid_backward decompose 白名单并同步双 torch 环境（Ascend910 实测）

> 来源轨迹：来源记录（事件号见文中 event N）

## 适用场景

- 框架/组件：torchair `experimental/_inductor_npu_ext`（inductor 的 AscendC lowering 后端，`torch.compile(options={"npu_backend": "ascendc"})`），decompose 白名单文件 `python/inductor_npu_ext/decomposition.py` 的 `_whitelist_decompositions()`。
- 平台/版本：Ascend910_9362（SoC A3，`current_soc=2`），npu-smi 25.5.5，CANN 9.2.0（${LOCAL_PATH_1}）。双环境实测：环境 1 `yrk_torch29_py312`（torch 2.9.0+cpu / torch_npu 2.9.0.post9.dev20261009）；环境 2 `yrk_torch_212_py313`（torch 2.12.0+cpu / torch_npu 2.12.0.post3.dev20261009）。
- 目标/工作负载：编译后的含 `aten.sigmoid_backward`（sigmoid 梯度算子）的图——不放开 decompose 时该算子整算子 fallback 切图（eager 单独调用），子算子无法与前后 elementwise 融合。
- 证据等级：单台 Ascend910 机器、单次运行；无性能基线对比。

路径约定：`${LOCAL_PATH_1}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开；`${LOCAL_PATH_2}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开；`${LOCAL_PATH_3}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开；`${LOCAL_PATH_4}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开；`${LOCAL_PATH_5}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开；`${LOCAL_PATH_6}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开。使用前在本地设置这些变量；不同编号不可假定为同一位置。代码中的变量样式字符串也须替换，不依赖 Python 自动展开。

## 触发与观测

- 现状（before）：源仓库 decomposition.py 中 grep `sigmoid_backward|conj_physical` 无匹配（event 21/23）；而 torch 原生 decomposition 表同时含 `aten.sigmoid_backward.default/.grad_input` 与 `aten.conj_physical.default/.out`（event 33/35）。上游分解定义（torch/_decomp/decompositions.py，event 29 逐字，已经 reader 复核）：

```
132: @register_decomposition(aten.sigmoid_backward)
133: @out_wrapper("grad_input")
134: @pw_cast_for_opmath
135: def sigmoid_backward(out_grad: Tensor, y: Tensor):
136:     return out_grad * (y * (1 - y)).conj_physical()
```

- make_fx 实测分解链（event 164/165、172/173）：fp32 → `prims.sub + prims.mul×2`（过滤后的 inductor 表下为 `aten.sub.Tensor + aten.mul.Tensor×2`）；fp16/bf16 → 首尾各多一个 `prims.convert_element_type`（`pw_cast_for_opmath` 进出 fp32 计算 dtype）；`conj_physical` 对实数 dtype 是 no-op（`_refs.conj_physical` 非复数直接返回输入，event 66/67），在链中消除——因此 keep 必须同时保留 `aten.conj_physical`，否则分解在表内被拦。
- 中途探针错误（不可采用）：直接 `getattr(torch.ops.aten.rsub, 'default')` 触发 `AttributeError: The underlying op of 'aten.rsub' has no overload name 'default'`（event 168/169）；须用 `_packet_overloads(packet)` 按 `packet.overloads()` 展开后再过滤。

## 探针与操作

1. 源仓库修改：`_whitelist_decompositions()` 中在 `isfinite` 之后、`cat` 之前插入（最终文件 decomposition.py:235-243，event 184/185 编辑、event 226 修后读取，均已经 reader 复核）：

```
    keep |= _packet_overloads(aten.isfinite)
    # sigmoid_backward --> sub+mul+mul（pw_cast_for_opmath 下 fp16/bf16 附带
    # convert_element_type 进出 fp32），子算子在 A2/A3 白名单且 AF v1 Sub/Mul
    # 支持 fp16/fp32（bf16 经自动 cast），全 SoC 可融合；conj_physical 的原生
    # decomp 对实数 dtype 为 no-op（分解链中消除），需一并保留
    keep |= _packet_overloads(aten.sigmoid_backward)
    keep |= _packet_overloads(aten.conj_physical)
    # 1)过滤空tensor 2)单tensor输入场景优化 3) 重复tensor场景转化为unsqueeze+expand
    keep |= _packet_overloads(aten.cat)
```

2. 前置确认（放开前必须核对，均可复用）：
   - 分解链子算子 `aten.sub`/`aten.mul` 已在 `_LoweringGuard.support` 白名单（aten_lowering.py L13-19，event 50/52），无需新增 `aten_lowering.py`/`asc_ops.py`/`asc_overrides.py`。
   - AF v1（A2/A3）Sub/Mul 的 TensorType 支持 fp16/fp32（event 181 逐字，已经 reader 复核）：

```
${LOCAL_PATH_2})
${LOCAL_PATH_3}                            {{"T", TensorType{DT_INT16, DT_INT32, DT_FLOAT16, DT_FLOAT}}}});
${LOCAL_PATH_4})
${LOCAL_PATH_5}                            {{"T", TensorType{DT_INT16, DT_INT32, DT_FLOAT16, DT_FLOAT}}}});
```

3. 新增 smoke 用例 2 个：`tests/smoke/test_sigmoid_backward_decompose.py`（event 206/207）。`test_sigmoid_backward_basic_all_dtypes`（fp32/fp16/bf16 精度 + Lowered 无 Fallback + asc_graph 含 Sub/Mul）核心断言（event 206 写入内容，已经 reader 复核）：

```
        def fn(g, y):
            return torch.ops.aten.sigmoid_backward(g, y)

        for dtype, tol in [(torch.float32, 1e-5), (torch.float16, 1e-2), (torch.bfloat16, 1e-2)]:
            with self.subTest(dtype=dtype):
                y = torch.sigmoid(torch.randn(64, 128, dtype=dtype).npu())
                g = torch.randn(64, 128, dtype=dtype).npu()
                logs, graphs = self._run_and_collect(fn, g, y, atol=tol, rtol=tol)

                self.assertIn("Lowered", logs, "应有 Lowered 日志")
                self.assertIn("aten.sub", logs, "sigmoid_backward 应分解且 sub 被 lowering")
                self.assertIn("aten.mul", logs, "sigmoid_backward 应分解且 mul 被 lowering")
                self.assertNotIn("Fallback", logs, "不应有 Fallback")
                self.assertTrue(
                    any("ascir.ops.Sub" in gr and "ascir.ops.Mul" in gr for gr in graphs),
                    "asc_graph 应包含 Sub 和 Mul 操作",
                )
```

   `test_sigmoid_backward_fused_downstream`（mul → sigmoid_backward → add）断言全图无 Fallback 且 asc_graph 含 Sub/Mul/Add。
4. 双环境同步（确认运行时实际加载的 torch_npu 安装包副本）：torch 2.9 环境副本已含该 hunk（event 128/130 diff 的 `<` 侧）；torch 2.12 环境 `grep -c sigmoid_backward .../torch_npu/_inductor/ascendc/decomposition.py` 计数 0（event 234/235）→ 先备份 `cp ... ${LOCAL_PATH_6}`（event 249/250），以相同 hunk 编辑 site-packages 副本（event 252/253），`py_compile` 后在同一 smoke 文件上重跑（event 255/256）。

## 机制与判别

- 结论 c1：在 inductor_npu_ext 的 `_whitelist_decompositions()` 中无条件追加 `keep |= _packet_overloads(aten.sigmoid_backward)` 与 `keep |= _packet_overloads(aten.conj_physical)` 后，Ascend910（A3，current_soc=2）上 torch.compile(ascendc 后端) 将 aten.sigmoid_backward 分解为 aten.sub.Tensor + aten.mul.Tensor×2（fp16/bf16 经 pw_cast_for_opmath 附带 prims.convert_element_type 进出 fp32，conj_physical 对实数 dtype 为 no-op 在链中消除），LowerSummary 全部 Lowered、无 Fallback，并与前后 elementwise 算子融合为单 kernel（kernel 名 autofused_sigmoid_backward_* / autofused_add_mul_sigmoid_backward_*）
  - 证据链：make_fx 链路（event 165/173）→ 原型运行 LowerSummary（event 192：`Lowered 4x aten.sub.Tensor`、`Lowered 8x aten.mul.Tensor`、`Lowered 4x/2x/2x/1x prims.convert_element_type.default`、`Lowered 1x aten.add.Tensor`，无任何 Fallback 行；kernel 名 `autofused_add_mul_sigmoid_backward_e935...`）→ 重跑复核（event 196，`== basic torch.float32/float16: PASS precision`）→ smoke 2 用例 OK（event 215）。
- 结论 c2：该 hunk 必须同步到运行时实际加载的 torch_npu 安装包副本：torch 2.12 环境（yrk_torch_212_py313/torch_npu 2.12.0.post3）同步前 grep sigmoid_backward 计数为 0，经备份（${LOCAL_PATH_6}）、编辑、py_compile 后重跑 2 个 smoke 用例通过（Ran 2 tests ... OK），与 torch 2.9 环境（yrk_torch29_py312/torch_npu 2.9.0.post9）形成双版本一致看护
  - 证据链：event 235（计数 0 + current_soc: 2）→ event 250（backup created）→ event 253（Edit applied）→ event 256（py_compile OK + `Ran 2 tests in 3.242s / OK`）。
- 可区分解释与未验证推断：
  - torch 2.9 安装包副本已含相同 hunk（event 130/135），说明该改动此前已以安装包先行存在；本轨迹将其落回源仓库并补齐 2.12 环境。哪个是权威首提交无法追溯（该目录 `git log` 报 fatal: not a git repository，event 39/41）。
  - "融合为单 kernel"的判据是 LowerSummary 无 Fallback + kernel 名 `autofused_*`（event 192/196）与 asc_graph.py 标记统计（event 203：`8 ascir.ops.Sub`、`18 ascir.ops.Mul`、`42 ascir.ops.Cast`、`2 ascir.ops.Add`），未做逐 kernel 计数核对，也未做性能对比。
  - 未验证：A2/A5 SoC 实机行为（仅静态依据 AF v1/v2 TensorType 推断）；fp64 等其他 dtype；动态 shape 场景；与 GE 后端路径的差异。

## 验证信号

（单台 Ascend910_9362、CANN 9.2.0，单次运行）
- event 192/196：原型脚本 fp32/fp16/bf16 精度 PASS；LowerSummary 全 Lowered、无 Fallback；融合 kernel 名含 sigmoid_backward。
- event 215：torch 2.9 环境 smoke `Ran 2 tests in 4.719s / OK`（含精度对比 assert_close）。
- event 220：`py_compile OK`（源仓库 decomposition.py + 新 smoke 文件），无残留 debug 目录。
- event 235/256：torch 2.12 环境同步前 grep 计数 0 → 同步后 `py_compile OK` + `Ran 2 tests in 3.242s / OK`。
- 无任何同名同单位性能指标基线，融合收益（避免整算子 fallback 切图、backward 链入同一融合 kernel）为机制性描述，不是性能结论。

## 适用与失效边界

- 版本：实测 torch 2.9.0+cpu/torch_npu 2.9.0.post9 与 torch 2.12.0+cpu/torch_npu 2.12.0.post3；上游分解定义引用 torch 2.12 源码树（torch/_decomp/decompositions.py:132-136）。torch 升级若改变 sigmoid_backward 分解链（如不再调用 conj_physical 或新增子算子），keep 行需重新核对。
- SoC：keep 为无条件（全 SoC）；依据是 AF v1 Sub/Mul 支持 fp16/fp32、bf16 经自动 cast，但仅 A3 实测，A2/A5 未验证。
- dtype：fp32/fp16/bf16 实测；其他 dtype 未验证（fp64 下 eager aclnn 路径与分解链优劣未评估）。
- 失效/回退条件：若分解链子算子（sub/mul/cast）未来被移出 lowering 白名单或 AF dtype 收紧，会退化为子算子独立 eager fallback、切图劣化；此时应先恢复子算子融合（注册 `_LoweringGuard.support`），仍不可融合再从 keep 移除、整算子回退 fallback。
- 同步边界：site-packages 副本同步会随 torch_npu 重装/升级被覆盖，需重复"确认加载来源 → 备份 → 编辑 → py_compile → 重跑 smoke"流程；备份位于 /tmp（重启即失）。
