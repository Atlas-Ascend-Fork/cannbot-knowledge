---
{
  "type": "Runbook",
  "title": "跨分支移植 PR#3824 的 3-way patch 冲突解决与轴分裂静默失效修复（torchair 26.2.0）",
  "description": "把 PR#3824（inductor 符号索引折叠引发非线性 load 报错的轴分裂修复）移植到与 master 差异巨大的 26.2.0 分支：git diff merge-base..PR head 生成 patch 后 git apply --3way，npu.py 两处 _tracing_asc_impl 冲突按保留 26.2.0 逐节点对齐结构、仅合入 did_split 分支解决。移植后静态检查发现试对齐调用 master 独有的 _align_nodes_to_canonical，AttributeError 被 broad except 吞掉导致轴分裂静默失效（did_split 恒 False）；新增 _trial_align_nodes_var_to_expr 适配方法修复，E2E mock 验证 [2358,128]→[2358,4,32] 恢复仿射、test_index_expr 19/19，git stash 对照确认其余单测失败为 torch_npu 残缺包环境问题。",
  "tags": [
    "task.debugging",
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

# torchair 26.2.0 移植 PR#3824（非线性 load 轴分裂）：3-way patch 冲突解决与静默失效修复

> 来源轨迹：来源记录（事件号见文中 event N）

## 适用场景

- 框架/组件：torchair `experimental/_inductor_npu_ext`（inductor NPU 扩展），目标分支 `26.2.0_1014`（基于 upstream/26.2.0）；被移植内容为 GitCode PR#3824「修复inductor 符号索引折叠引发非线性load报错的问题」（head `053687a9`，base master，merge-base `5a52eeaf`，净改动 3 文件 +303/-7）。
- 问题域：reshape/transpose 坐标反解产生非仿射 load 地址（attention：`32*s + 75456*(c//32) + c%32`；window：`32*s + 512*(c//32) + c%32`），普通 Load 无法表达，`_index_to_loop` 抛 `RuntimeError: index expression ... cannot be represented as a standard strided offset` 整图编译失败；PR#3824 用 canonical 轴分裂（`[S] -> [S//k, k]`）+ 值域化简恢复仿射。
- 验证环境（本轨迹）：本机无真实 NPU（torch_npu 为残缺包），torch 2.10.0+cpu / Python 3.11；验证手段为 CPU 数学检查 + 端到端 mock + 仓库单测 + git stash 对照。
- 缺失信息：真机 NPU 关闭/开启轴分裂 A/B 对照（文档 TC003/TC004）与整网回归（TC006）未执行；PR 原 diff（event 62）中段未逐行复核。

路径约定：`${LOCAL_PATH_1}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开；`${LOCAL_PATH_2}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开。使用前在本地设置这些变量；不同编号不可假定为同一位置。代码中的变量样式字符串也须替换，不依赖 Python 自动展开。

## 触发与观测

- 触发：当前分支与 PR 基点在 `__init__.py`/`npu.py` 差异巨大（`2 files changed, 174 insertions(+), 514 deletions(-)`，event 68/69），不能直接 checkout 文件覆盖。
- 移植后关键观测（对照问题文档验收标准检查时发现）：
  - 探针命令（event 178，已经 reader 复核）：

```
grep -n "def _align_nodes_to_canonical\|def _align_node_to_canonical\|def _canonical_axes_for_kernel" experimental/_inductor_npu_ext/python/inductor_npu_ext/npu.py
```

  - 输出（event 180，已经 reader 复核）：

```
358:    def _canonical_axes_for_kernel(self):
953:    def _align_node_to_canonical(
```

  即移植代码调用的 bulk 预对齐方法 `def _align_nodes_to_canonical` 在 26.2.0 中不存在；master `053687a9` 上位于 npu.py:959（event 188/190）。检查循环还在 npu.py:487 使用 `aligned.var_to_expr`（event 198/199），同样依赖 master 的 `_AlignedNodeAxes`。

## 探针与操作

1. 3-way patch 移植（event 72/73）：

```
git diff 5a52eeafe461240a6f589a74d3d45843d552b372 053687a9 > ${LOCAL_PATH_1} && git apply --3way ${LOCAL_PATH_1}
```

   结果：`__init__.py`、`common/utils.py` 干净应用；`npu.py` 两处冲突（event 76/77：npu.py:1033-1055、1142-1155），均为 26.2.0 重构 `_tracing_asc_impl`（对齐从 master 的 bulk 预对齐改为逐节点进行）所致。解决原则：保留 26.2.0 结构、仅合入 PR 的 `did_split` 分支。冲突 1 解决（event 93/94，已经 reader 复核）：

```
            # 仅在真发生轴分裂时构造 canonical 域（用于 node.run 外层 SimplifyIndexing），
            # 未分裂 kernel 的 node.run 路径与现状逐字节一致。
            canonical_axis_ranges = dict(zip(canonical_axes, canonical_ranges)) if did_split else None
            canonical_loop = DenseLoop(axis=canonical_axes, size=canonical_ranges)
```

   冲突 2 解决——`node.run` 参数从 PR 的 `aligned.axis_indexings` 改为 26.2.0 逐节点对齐的局部变量 `axis_indexings`（event 96/97，已经 reader 复核）：

```
                        with self.set_current_node(node):
                            if did_split:
                                # 外层注入 canonical 轴域的值域化简，把 flatten 替换产生
                                # 的 FloorDiv/ModularIndexing（如 FloorDiv(32*a1+a2, 32) → a1）
                                # 在到达 load/store 前消除。core 在 SchedulerNode.codegen 内
                                # 装载的节点域 SimplifyIndexing 位于链内层、先执行，但其
                                # 值域键为 flatten 复合式（信息弱），div/mod 由本层消除。
                                with V.set_ops_handler(SimplifyIndexing(V.get_ops_handler(), canonical_axis_ranges)):
                                    node.run(*axis_indexings)
                            else:
                                node.run(*axis_indexings)
```

2. 静默失效定位（before 代码，npu.py:453-462 一带，event 185 读取，已经 reader 复核）：

```
        for round_index in range(3):
            canonical_axes = [sympy.Symbol(n) for n in names]
            try:
                # 注意必须传 {} 而非 None：_concat_input_shape_for_node 会对每个
                # 有 outputs 的节点调用 concat_input_shapes.get(...)，None 直接
                # AttributeError（曾被下方 except 吞掉，导致分裂静默失效）。
                aligned_nodes = self._align_nodes_to_canonical(canonical_axes, ranges, {})
            except Exception as e:  # pylint: disable=broad-except
                # 对齐失败说明轴空间本身不合法——回退，不引入新失败模式。
                logger.warning("canonical axis split trial alignment failed, fallback: %s", e)
                return canonical_names, canonical_ranges, False
```

3. 修复（event 222-229，npu.py:426 新增适配方法，已经 reader 复核）：

```
    def _trial_align_nodes_var_to_expr(self, canonical_axes, canonical_ranges):
        """轴分裂试对齐（26.2.0 适配）：逐节点复用 _align_node_to_canonical，从返回的
        axis_indexings（按 body.var_ranges 顺序）重建 var→canonical 表达式映射，语义
        等价于上游 bulk 预对齐产出的 _AlignedNodeAxes.var_to_expr（该方法由 master 侧
        轴对齐重构引入，26.2.0 未含）。空 concat 语义一致：_resolve_pre_concat_ranges
        对空表直接返回 canonical_ranges，故无需 concat 形参。

        无 body 的节点（模板类，正常已在入口禁区检查排除）返回 None，检查循环跳过。
        """
        aligned_nodes = []
        for node in self._nodes:
            body = getattr(node, "_body", None)
            if body is None:
                aligned_nodes.append(None)
                continue
            axis_indexings, _, _ = self._align_node_to_canonical(node, canonical_axes, canonical_ranges)
            aligned_nodes.append(
                {var: indexing[0] for var, indexing in zip(body.var_ranges.keys(), axis_indexings)}
            )
        return aligned_nodes
```

   试对齐改调 `aligned_nodes = self._trial_align_nodes_var_to_expr(canonical_axes, ranges)`（event 225/226），检查循环改 `aligned_expr = expr.xreplace(aligned)`（event 228/229）。
4. 端到端 mock 验证（`${LOCAL_PATH_2}`，event 254/255/257/258）：mock `FakeBody` 以 window 场景索引 `32*s0 + 512*FloorDiv(c0,32) + ModularIndexing(c0,1,32)`、`fake_align` 模拟未分裂（1:1）与分裂后（flatten `c0 -> 32*a1+a2`）两种对齐，`FakeGraph.sizevars = SizeVarAllocator()` 绕开 V.graph，驱动 `_refine_canonical_axes_by_affinity(["a0","a1"], [2358,128])`，断言 `(names, ranges, did_split) == (["a0","a1","a2"], [2358, 4, 32], True)`。
5. 环境失败判别（git stash 对照，event 281，已经 reader 复核）：

```
git stash && timeout 120 python3 -m unittest discover -s experimental/_inductor_npu_ext/tests -p "test_decomposition.py" 2>&1 | grep -E "^(OK|FAILED|Ran)"; git stash pop && git status --short
```

## 机制与判别

- 结论 c1：目标分支与 PR 基点差异巨大（__init__.py/npu.py +174/-514）时，用 `git diff <merge-base> <PR head>` 生成 patch 后 `git apply --3way` 只应用 PR 增量：__init__.py 与 common/utils.py 干净应用，npu.py 在 _tracing_asc_impl 两处冲突按「保留 26.2.0 结构、仅合入 did_split 分支」解决（node.run 改用 26.2.0 逐节点对齐的局部变量 axis_indexings，而非 master 预对齐的 aligned.axis_indexings）
  - 证据链：event 69（差异统计）→ 73（3-way 应用结果）→ 77（冲突行号）→ 94/97（冲突解决）→ 117（`diff pr.patch applied.patch`：实质差异仅 _tracing_asc_impl 适配与行号/base 哈希）。
- 结论 c2：PR#3824 的 _refine_canonical_axes_by_affinity 试对齐调用 `self._align_nodes_to_canonical(canonical_axes, ranges, {})`（npu.py:460）及检查循环的 `aligned.var_to_expr`（npu.py:487）均依赖 master 重构 ad836f73（PR !3796，wudii，2026-09-30）引入的 bulk 预对齐 API；26.2.0 仅有逐节点 `_align_node_to_canonical`（npu.py:953）且无该 def——运行时 AttributeError 被 broad except 吞掉并 return (…, False)，轴分裂静默失效（did_split 恒为 False），不产生任何报错
  - 证据链：event 180（def 缺失 grep）→ 185（调用点 + 吞异常 except + fallback return False）→ 190（master 053687a9 有 def，npu.py:959）→ 191（26.2.0 逐节点 API）→ 199（`487: aligned_expr = expr.xreplace(aligned.var_to_expr)`）→ 124/127/131（ad836f7309973e777a17c76c488a736edcef50aa，author wudii，PR !3796 fix/score-aligned-canonical-axes-20260929，含于 upstream/master 不在 26.2.0）。
  - 判别：该失效不抛错、不改变现有 kernel 行为（未分裂路径逐字节一致），只有轴分裂永不触发；表现为文档验收标准 `AXIS_SPLIT ranges=['2358','4','32']` 永远观察不到，而非新增报错。
- 结论 c3：新增 `NPUKernel._trial_align_nodes_var_to_expr`（npu.py:426）逐节点调用 26.2.0 的 `_align_node_to_canonical` 并从返回的 axis_indexings（按 body.var_ranges 顺序）重建 var→canonical 映射，试对齐与 `expr.xreplace(aligned)` 改走该适配方法后，静默失效消除
  - 证据链：event 223/226/229（三处 edit）→ 232（`syntax OK` + grep 确认 `426: def _trial_align_nodes_var_to_expr`、`480: aligned_nodes = self._trial_align_nodes_var_to_expr(canonical_axes, ranges)`）。
  - 语义等价依据（静态）：`_resolve_pre_concat_ranges` 对空 concat 形参直接返回 canonical_ranges（event 205/209，npu.py:736-737）；`_current_var_to_expr` 副作用与 master 行为一致（真实 codegen 会重设，event 212/213/216）。
- 结论 c4：端到端 mock（window 场景 32*s + 512*(c//32) + c%32）输出 did_split: True、ranges: [2358, 4, 32]，[2358,128] → [2358,4,32] 地址恢复仿射，满足文档 AXIS_SPLIT 验收标准；test_index_expr.py 19/19 通过；ut.py/test_decomposition/test_reshape_split_fusion_guard 的失败经 git stash 对照（无改动时同样 FAILED errors=1/16）确认为本机 torch_npu 残缺包的环境问题而非移植回归
  - 证据链：event 258（mock 输出，已经 reader 复核）→ 265（`Ran 19 tests in 2.124s / OK`）→ 277（stash 掉改动后 test_reshape_split_fusion_guard 同样 `FAILED (errors=1)`）→ 282（stash 后 test_decomposition 同样 `Ran 16 tests ... FAILED (errors=16)`，与带改动运行 event 278 一致）。
- 可区分解释与未验证推断：
  - 静默失效的诊断是静态代码检查结论（def 缺失 + broad except 回退路径），未在修复前实际运行 mock 复现 AttributeError；修复后 mock 的 `did_split: True` 间接证实机制。真机上预期可查到 `logger.warning("canonical axis split trial alignment failed, fallback: ...")` 日志（未验证）。
  - 数学前置检查（event 238/239）：case1 `32*s + 75456*FloorDiv(32*a1+a2,32) + ModularIndexing(32*a1+a2,1,32)` 非仿射判定 True；case2 分裂后 `32*s + 75456*a1 + a2` 仿射 True；case3 `FloorDiv(a1,1)` 剥离后等于 a1 True。
  - torch 2.10 中 `simplify_with_ranges` 不能从 `torch._inductor.sizevars` 模块级导入（event 250/251 ImportError），但 `SizeVarAllocator().simplify_with_ranges`（make_simplify_with_ranges_cache 工厂产物）可用——mock 据此构造 FakeGraph。
  - 同轴双除数（如 //32 与 %8）两轮分裂后余项为复合式、复检不收敛 → 干净回退（event 185 代码注释），本轨迹未单独验证。
  - 模板 kernel（NPUConcatBuffer/NPUMatmulBuffer 等）在 `_refine_canonical_axes_by_affinity` 入口禁区检查直接返回 False，不参与分裂。

## 验证信号

（本机无 NPU；torch 2.10.0+cpu；除注明外均为单次运行）
- event 106/232：py_compile `syntax OK`；event 232 grep 确认新方法与调用落位（npu.py:426 def / 480 call）。
- event 239：仿射判定/剥 //1 数学检查全 True（case1 nonaffine True / case2 affine True / case3 strip True / trial align 与 refine 均可调用）。
- event 258（单次）输出原文（已经 reader 复核）：

```
names: ['a0', 'a1', 'a2']
ranges: [2358, 4, 32]
did_split: True
E2E_MOCK_PASS: [2358,128] -> [2358,4,32], window 地址恢复仿射
```
- event 265（单次）：test_index_expr.py `Ran 19 tests in 2.124s / OK`。
- event 277/282（单次）：git stash 对照——无改动时 test_reshape_split_fusion_guard 同样 `FAILED (errors=1)`、test_decomposition 同样 `Ran 16 tests ... FAILED (errors=16)`，与带改动运行一致 → 判为 torch_npu 残缺包环境问题（`No module named 'torch_npu._inductor'; 'torch_npu' is not a package`，event 264/265）。
- event 289/293/297：修复以 `e8169a6a`（npu.py +26/-5）提交，与移植提交 `04ed24a4` 一并推送 `04ed24a4..e8169a6a` 至 origin/26.2.0_1014（远程提示 MR 3840）。
- 交付边界：以上信号只证明 CPU 语义与单测无回归；不构成真机 NPU 修复成功（TC003/TC004/TC006 未执行），也无任何性能结论。

## 适用与失效边界

- 版本：`_AlignedNodeAxes`/`_align_nodes_to_canonical`/`_adjust_canonical_axes_by_access` 由 master `ad836f73`（PR !3796，2026-09-30）引入；任何不含该重构的分支（26.2.0 及更早）移植 PR#3824 的 npu.py 都需要 `_trial_align_nodes_var_to_expr` 这类适配，或先合入 !3796。torch 侧依赖 `torch._inductor.sizevars.SimplifyIndexing` 与 `SizeVarAllocator` 缓存方法（torch 2.10 验证；模块级 `simplify_with_ranges` 不可导入）。
- 验证边界：仅 CPU mock + 单测 + stash 对照；真机关闭/开启轴分裂 A/B、整网 attention 回归、动态待拆轴、模板 kernel 场景均未执行，不能宣称真机修复成功。
- 失效场景：同轴双除数两轮分裂仍不收敛 → 回退保持原报错路径（非线性地址由 gather 路径兜底）；待拆轴不能整除、动态 shape、融合模板 kernel 不适用；连续布局/单 head 等可化简项走既有路径不受影响。
- 通用警示（移植模式）：broad except + 静默回退返回值的代码，跨分支移植后可能整体失效而无任何报错——py_compile/导入通过不等于功能生效；移植后必须用「关键 API def 存在性 grep + 端到端 mock 检查关键开关变量（如 did_split）」复核，并用 git stash 对照区分环境失败与回归。
- 回退条件：若 `_trial_align_nodes_var_to_expr` 在后续分支合入 !3796 后与 bulk 预对齐产生行为分歧（如同名方法恢复存在），应优先回到上游实现，删除适配层。
