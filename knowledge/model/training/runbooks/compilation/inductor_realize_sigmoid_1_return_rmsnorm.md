---
{
  "type": "Runbook",
  "title": "inductor 图输出身份决定 realize 时机：`sigmoid_1` 不在 return 里时 RMSNorm 链算两份（--check 结构性假阴性根因）",
  "description": "torchair benchmark.py --check 重编片段与整网 kernel 不同构的根因：`sigmoid_1` 在 return 里时命中 GraphLowering.run_node 的 `user.op == \"output\"`（graph.py:2209）触发 result.realize()，lowering 当场物化，下游只能读 buffer；不在 return 里时保持 lazy Pointwise，被 mul 链 inner_fn 闭包内联一份，再被 extern sigmoid_backward 经 realize_input 物化出第二份。A/B 变体只差 return 一个 token：${PRIVATE_CREDENTIAL_1} PASSED，B 的 mul_783 FAILED（NaN positions differ at 33,357,372）；四份 asc_graph 的 ops.sigmoid 计数 1/1/2/2 可区分观测；重复诞生于 GraphLowering 而非 Scheduler（pre/post fusion diff 显示融合循环只分组）。",
  "tags": [
    "task.debugging",
    "topic.compilation",
    "topic.precision",
    "task.testing"
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

# inductor 图输出身份决定 realize 时机：`sigmoid_1` 不在 return 里时 RMSNorm 链算两份（--check 结构性假阴性根因）

## 适用场景

- 框架/平台：torch 2.14.0+cpu（git 08187d9e）inductor（`torch/_inductor/graph.py` GraphLowering.run_node）+ torch_npu 2.14.0+gita916959 ascendc 后端；CANN 9.3.0~weekly.20260923.01（0923）；Ascend910_9362。
- 工作负载/问题：torchair `benchmark.py --check`（把烘焙的 eager_fn 片段重交 torch.compile 做精度校验）报 PASSED，而整网同 kernel 在 CANN 0923 上产出 23%~33% NaN 导致训练 `grad_norm=nan`——结构性假阴性的根因定位。也适用于任何"片段重编 kernel 与整网 kernel 不同构"的精度校验问题。
- 缺失信息：A/B 变体实验产物（asc_graph_variantA/B、check_log_variantA/B、benchmark_A/B.py）由并行会话生成，本轨迹只读取与交叉核验，未重跑；`--check` 输出为单次运行。

## 触发与观测

- 触发：`--check` PASSED 与整网 NaN 并存；A/B eager_fn 变体单变量复现。
- 客观输出（A/B 两次独立运行，各自用其中一个 return）：
  - variantA：`output:mul_783 precision PASSED: CosineSim=0.99999934 RelEuclid=1.19112630e-03 ...`
  - variantB：`output:mul_783 precision FAILED: NaN positions differ at 33357372 element(s).`（`sum_30`/`sigmoid_1` 两侧均 PASSED）

两个 eager_fn 变体只差 return 里一个 `sigmoid_1`（diff 只报 `29c29`），variantA 的 `mul_783` PASSED，variantB 的 `mul_783` FAILED: NaN positions differ at 33,357,372 element(s)。

重复诞生于 GraphLowering 而非 Scheduler：两个 variant 的 `ir_pre_fusion.txt` 与 `ir_post_fusion.txt` 之间融合循环只做分组（非空删除行 0，`class opN_loop_body` 4→4，`ops.*` 总数 A 36→36 / B 52→52），16 个 `ops.*` 之差在 pre-fusion 就已存在。

根因开关是 `graph.py:2209` 的 `if user.op == "output":` → `result.realize()`：sigmoid_1 是图输出时第 23 行 lowering 当场物化成 buf1（下游 op2 只能 `ops.load('buf1')`）；不是图输出时保持 lazy Pointwise、被 mul 链内联（第一份，buf1），第 28 行 extern `sigmoid_backward` 经 `realize_input` 才物化出 buf3（第二份）。

四份 asc_graph 的 `ops.sigmoid(` 计数是 1/1/2/2（recompile_4e0f9ef3 与 variantA_37677113 各 1、variantB_75b64bfd 与 network_d2a3593a 各 2），variantB 与整网逐项相同。

另外两条候选路径验证为空转：`aten.sigmoid_backward` 未注册进 `needs_realized_inputs`（lowering.py:135 的 OrderedSet）；`realize_hint()` 不物化——只在 ir.py:885 基类（函数体即 `pass`）与 3560/10587/10769 转发处定义，Pointwise/Reduction 未重写。

## 探针与操作

A/B 构造（`eager_fn_network.py` 是整网 benchmark.py 烘焙的原始片段，return `(sum_30, mul_783, sigmoid_1)`；variantA/B 第 1-26 行与它逐字相同，末尾补回被抽取边界切掉的 extern 消费者，唯一差异在 return 是否含 `sigmoid_1`）。variantB 关键行：

```
23:     sigmoid_1 = torch.ops.aten.sigmoid.default(add_1329)
24:     add_1330 = torch.ops.aten.add.Tensor(sigmoid_1, 1e-06)
25:     unsqueeze_56 = torch.ops.aten.unsqueeze.default(add_1330, -1)
26:     mul_783 = torch.ops.aten.mul.Tensor(expand_7, unsqueeze_56)
27:     squeeze_76 = torch.ops.aten.squeeze.dim(sum_30, -1)
28:     sigmoid_backward = torch.ops.aten.sigmoid_backward.default(squeeze_76, sigmoid_1)
29:     return (sum_30, mul_783, sigmoid_backward)
```

variantA 第 29 行为 `return (sum_30, mul_783, sigmoid_1, sigmoid_backward)`；真实编译源 `benchmark_A.py`/`benchmark_B.py` 的对应行在 20208-20214，两文件仅 20214 行差 `", sigmoid_1"`（文件大小差 11 字节）。

逐层排除（先 diff 产物再读源码）：先比 `ir_pre_fusion.txt`（`scheduler.py:4334`，融合循环之前 dump）与 `ir_post_fusion.txt`（`scheduler.py:4495`，之后），确认要归咎的那一层（Scheduler 融合循环）到底改了什么——post 只比 pre 多 `op1_op2_op3: FusedSchedulerNode` 分组头和两个 `snodes[i] =` 标签，diff hunk 为 `30a31,63` + 两个 c hunk（空行换标签），非空删除行 0。

loop body 原文（融合循环之前就定型）：variantA 写 `mul_3` 的节点**读**物化好的 sigmoid：

```
class op2_loop_body:
    var_ranges = {p0: 4096, p1: 4, p2: 4096}
    index0 = 4096*p0 + p2
    index1 = 4*p0 + p1
    index2 = 16384*p0 + 4096*p1 + p2
    def body(self, ops):
        load = ops.load('arg0_1', get_index)
        to_dtype = ops.to_dtype(load, torch.float32, src_dtype = torch.bfloat16, use_compute_types = True)
        load_1 = ops.load('buf1', get_index_1)
        constant = ops.constant(1e-06, torch.float32)
        add = ops.add(load_1, constant)
        mul = ops.mul(to_dtype, add)
        store = ops.store('buf2', get_index_2, mul, None)
```

variantB 写 `mul_3` 的 67M 节点**内联**整条链（第一份）：

```
class op1_loop_body:
    var_ranges = {p0: 4096, p1: 4, p2: 4096}
        load = ops.load('arg0_1', get_index)
        to_dtype = ops.to_dtype(load, torch.float32, src_dtype = torch.bfloat16, use_compute_types = True)
        load_1 = ops.load('arg2_1', get_index_1)
        load_2 = ops.load('buf0', get_index_2)
        constant = ops.constant(16384.0, torch.float32)
        truediv = ops.truediv(load_2, constant)
        constant_1 = ops.constant(1e-06, torch.float32)
        add = ops.add(truediv, constant_1)
        rsqrt = ops.rsqrt(add)
        mul = ops.mul(load_1, rsqrt)
        load_3 = ops.load('arg3_1', get_index_3)
        to_dtype_1 = ops.to_dtype(load_3, torch.bfloat16, src_dtype = torch.float32, use_compute_types = True)
        to_dtype_2 = ops.to_dtype(to_dtype_1, torch.float32, src_dtype = torch.bfloat16, use_compute_types = True)
        mul_1 = ops.mul(mul, to_dtype_2)
        load_4 = ops.load('arg4_1', get_index_4)
        to_dtype_3 = ops.to_dtype(load_4, torch.bfloat16, src_dtype = torch.float32, use_compute_types = True)
        to_dtype_4 = ops.to_dtype(to_dtype_3, torch.float32, src_dtype = torch.bfloat16, use_compute_types = True)
        add_1 = ops.add(mul_1, to_dtype_4)
        sigmoid = ops.sigmoid(add_1)
        constant_2 = ops.constant(1e-06, torch.float32)
        add_2 = ops.add(sigmoid, constant_2)
        mul_2 = ops.mul(to_dtype, add_2)
        store = ops.store('buf1', get_index_5, mul_2, None)
```

variantB 另有一个节点把同一条链**逐字再算一遍**（第二份，给 extern 用）：

```
class op3_loop_body:
    var_ranges = {p0: 4096, p1: 4}
        load = ops.load('arg2_1', get_index)
        load_1 = ops.load('buf0', get_index_1)
        constant = ops.constant(16384.0, torch.float32)
        truediv = ops.truediv(load_1, constant)
        constant_1 = ops.constant(1e-06, torch.float32)
        add = ops.add(truediv, constant_1)
        rsqrt = ops.rsqrt(add)
        mul = ops.mul(load, rsqrt)
        load_2 = ops.load('arg3_1', get_index_2)
        to_dtype = ops.to_dtype(load_2, torch.bfloat16, src_dtype = torch.float32, use_compute_types = True)
        to_dtype_1 = ops.to_dtype(to_dtype, torch.float32, src_dtype = torch.bfloat16, use_compute_types = True)
        mul_1 = ops.mul(mul, to_dtype_1)
        load_3 = ops.load('arg4_1', get_index_3)
        to_dtype_2 = ops.to_dtype(load_3, torch.bfloat16, src_dtype = torch.float32, use_compute_types = True)
        to_dtype_3 = ops.to_dtype(to_dtype_2, torch.float32, src_dtype = torch.bfloat16, use_compute_types = True)
        add_1 = ops.add(mul_1, to_dtype_3)
        sigmoid = ops.sigmoid(add_1)
        store = ops.store('buf3', get_index_4, sigmoid, None)
```

根因源码（`torch/_inductor/graph.py` GraphLowering.run_node，sed 原文；`realize()` 的语义见 ir.py:809-816 docstring："realize the IRNode into physical memory, ending the possibility of fusing into it, but allowing, e.g., multiple users to access the data without having to recompute"）：

```
            # Realize if (1) any user need inputs realized, or (2) there is
            # already too many reads and rematerializing can be bad.
            num_users = len(OrderedSet(n.users))
            if num_users > 1 and isinstance(result, TensorBox):
                for user in n.users:
                    if user.target in needs_realized_inputs:
                        result.realize_hint()
```

```
                    if user.op == "output":
                        # pyrefly: ignore [missing-attribute]
                        if isinstance(result.data.data, (Pointwise, Reduction)):
                            # Cheap-to-recompute nodes (0 buffer reads, e.g.
                            # index arithmetic or constant fills) can be
                            # deferred to realize_input at output processing.
                            # This prevents cascade materialization where
                            # shared constants inflate downstream read counts.
                            if (
                                config.delay_realize_cheap_outputs
                                # pyrefly: ignore [missing-attribute]
                                and result.data.num_reads() == 0
                                # pyrefly: ignore [missing-attribute]
                                and not result.data.has_large_inner_fn()
                            ):
                                continue
                            result.realize()
```

## 机制与判别

- 两条时间线（行号指 eager_fn 摘录文件；`graph.py`/`ir.py`/`config.py`/`lowering.py` 均在 torch/_inductor/ 下）：
  - variantA（sigmoid_1 在 return 里，≡ recompile 片段）：第 23 行 lowering `sigmoid_1` 时 `n.users`={add_1330, sigmoid_backward, output}、`num_users=3>1`，命中 `graph.py:2209`；逃逸条件不成立（`delay_realize_cheap_outputs` 默认 True 但 `num_reads()==0` 不满足，链读 4 个输入）→ `graph.py:2225` `result.realize()` 当场物化成 `buf1`；第 24-26 行的 `add_1330`/`mul_783` 只能 `ops.load('buf1')`；第 28 行 extern `sigmoid_backward` 的 `realize_input`（ir.py:7429 → StorageBox 分支 `x.realize()`）幂等，不产生第二份。链算一份。
  - variantB（sigmoid_1 不在 return 里，≡ 整网）：第 23 行 lowering 时 `n.users`={add_1330, sigmoid_backward}，2209 永不命中、2153 也不命中 → 保持 lazy Pointwise；第 24-26 行顺着 `inner_fn` 闭包组合进去（内联，第一份 buf1）；第 28 行 extern 经 `process_kernel`/`realize_input` 才物化（第二份 buf3）。链算两份。
- 缓冲编号是 realize 时序的化石记录（与 `ir_pre_fusion.txt` 节点表对上）：variantA `buf0(op0)→buf1=sigmoid(op1)→buf2=mul_3(op2, 读 buf1)→buf3=sum_30(op3)`；variantB `buf0(op0)→buf1=mul_3(op1, 内联整条链)→buf2=sum_30(op2)→buf3=sigmoid(op3, 最后才出生)`。
- Scheduler 救不回来：B 里 `op1.unmet_dependencies=[buf0]`、`op3.unmet_dependencies=[buf0]`，两节点间没有依赖边（兄弟而非生产者-消费者），`can_fuse_vertical`（scheduler.py:8491-8512）无边可匹配；27 条 WhyNoFuse 拒绝理由无一以图输出为条件，`score_fusion`（choices.py:730）组成项亦无图输出项——重复在 lowering 阶段就不可逆。
- 可区分观测汇总（四个独立观测同向）：`ops.sigmoid` 计数 1/1/2/2；`unmet_dependencies` 是否读 sigmoid buffer；extern kernel 是否在片段内；A PASSED vs B FAILED。
- 证据分级：A/B 差一个 token → 因果成立（实测事实）；loop body/节点表/graph.py 行号 → 源码与 IR 产物依据；"realize 时机差异"是由前两者推出的机制解释。本轨迹未测"只去掉 `sigmoid_1` 返回、不加 `sigmoid_backward`"的第三变体（按此机制应不复现——未验证推断）。
- NaN 最终成因（重复链里 `truediv` 两路输入各来自一条 broadcast 链 → CANN 0923 图融合 pass 守卫拒绝后移且不回滚 → tiling 错配 → 读未初始化片上内存）是另一层缺陷（CANN 侧，1009 已修），不在本卡范围。

## 验证信号

（A/B 两次独立运行 + 产物 diff；CANN 0923 / Ascend910_9362；证据等级：check log 与 debug dump 原始产物）
- A/B 结果：variantA 三输出全 PASSED；variantB `mul_783` FAILED: NaN positions differ at 33357372 element(s)。
- 单变量核验：摘录文件 diff 只报 `29c29`；真实编译源 benchmark_A/B.py 仅 20214 行差 `", sigmoid_1"`（大小差 11 字节）。
- pre/post fusion diff：两 variant 均 3 个 hunk（`30a31,63` / `33a34,62` 追加 FusedSchedulerNode 分组头 + 两个把空行换成 `snodes[i] =` 标签的 c hunk），非空删除行 0，`class opN_loop_body` 4→4，`ops.*` A 36→36、B 52→52。
- `ops.sigmoid(`/`call_function`/`PlaceHolder` 计数：recompile 1/1/1、variantA 1/1/1、variantB 2/2/0、network 2/2/0。
- 节点表：variantA `op2.unmet_dependencies=[buf1]`（读 sigmoid）vs variantB `op1=[buf0]`、`op3=[buf0]`（不读任何 sigmoid buffer）。
- `realize_hint` 定义位置仅 ir.py:885/3560/10587/10769（基类为 `pass`，其余转发）；`needs_realized_inputs`（lowering.py:135）grep `sigmoid_backward` 无命中。

## 适用与失效边界

- 适用：torchair/torch_npu `benchmark.py --check` 类片段重编校验的可信度评估；eager_fn 片段抽取边界的固有局限分析（--check 报 PASSED 只说明"这段 aten 语义在 ascendc 后端下正确"，不说明"整网那个 kernel 正确"）。
- 复现配方（两条一起改才成立）：补一个不在 lowering 白名单里的下游 extern 消费者 + 不把它消费的中间值 return 出去。只补 extern 消费者（variantA）不复现；推断只去掉 return 而不加 extern 消费者也不复现（未验证）。
- 失效/边界：
  - `delay_realize_cheap_outputs` 逃逸条件（`num_reads()==0`）本例不成立（链读 4 个输入）；读数为 0 的常量填充/index 算术类图输出走 `continue` 延迟物化，本机制不适用。
  - torch/inductor 版本敏感：graph.py 行号（2148-2225、2209、2225）对应 08187d9e；版本变更后应按 `user.op == "output"` 语义定位而非行号。
  - 判别 `--check` 是否已复现整网缺陷的停止条件：重编结果与整网逐项对齐（主 kernel `ops.*` 合计 47、`ops.rsqrt`/`ops.sigmoid`/`ops.truediv` 各 2）且能复现 NaN，即停止，无需继续归因 kernel 内部。
  - 本机制解释的是"结构为什么重建不出来"，不构成对 CANN 侧 NaN 缺陷的修复建议。
