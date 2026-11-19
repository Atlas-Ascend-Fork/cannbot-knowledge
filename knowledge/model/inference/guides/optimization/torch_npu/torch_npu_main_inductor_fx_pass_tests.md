---
type: Guide
title: 主线 Inductor fx_passes 测试族：算子契约、动态形状开关、stack-sum/add-chain 数学事实与 pass 组装顺序
description: 固定提交下 test/_inductor 八个 FX pass 测试文件中实现面卡未记录的测试侧契约：multi_slice_concat 算子/模板配置契约、NPU_INDUCTOR_DYNAMIC_FX_PASS 硬开关、stack_sum FP32 累加、remove_cast 与 multi_slice 的注册顺序断言、filter_masks 尺寸符号守卫。
tags:
- task.testing
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_multi_slice_concat_pass.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_dynamic_shape_fx_passes.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_stack_sum_pass.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_remove_cast_after_slice_by_add_cat.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_grouped_matmul_pass.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_sink_pointwise_cat_pass.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_slice_cat_pass_composition.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_dynamic_cat_mask.py
  role: primary
created_at: '2026-11-12T17:02:00Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 主线 Inductor fx_passes 测试族：算子契约、动态形状开关、stack-sum/add-chain 数学事实与 pass 组装顺序

## 固定版本与范围

主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的 `test/_inductor` 八个 FX pass 测试文件静态阅读。pass 匹配规则本体（min_groups=8/copy_cost≥2/段上限/行 cat 无 aclnn 门/mask [rows,1] 溯源/placeholder 源/step None-1/dtype 白名单/多用户 cat 拒绝/bucket 语义/`_gmm_plan_batch_size` 均衡分摊）在 [FX 改写条件卡](torch_npu_inductor_fx_rewrite_conditions.md) 已逐条持有，测试为镜像，本卡不重述。未运行任何测试。

## multi_slice_concat 的算子级契约（test_multi_slice_concat_pass.py）

- **eager 走参考实现**（:245-247 注释原义）：`npu_ext::multi_slice_concat` 在 eager 是 CompositeExplicitAutograd 参考实现（逐段 copy + cat），融合 kernel 只存在于 lowering 之后；纯数据搬移要求 bitwise 相等（atol=0/rtol=0）。计划非法一律 RuntimeError 而非错算：plan 长度不齐、src_idx 越界、mask_idx 非 -1/合法、非 [rows,1] 掩码、段偏移+宽度越界（:308-335）；行向拼接要求等宽，混合宽度报 "needs one width"（:937-941）。
- **测试捕获契约**（:161-181 注释）：静态捕获必须 `tracing_mode="fake"`——`"real"` 为每个输入建独立 FakeTensorMode，多源段元数据推断触发 "Mixing fake modes" 而**静默跳过**改写；动态捕获用 `torch.export` 只把 dim 0 设为符号（生产形态），最后一维必须静态才有常量偏移，`tracing_mode="symbolic"` 或 `torch.compile(dynamic=True)` 会把列数也符号化、pass 静默回落 aten.cat。动态 batch 从不为 1：dim 0/1 硬特化，符号值域 [2, inf)，batch=1 触发重编译（:406-410, :1130-1158）。
- **mask 链边界**：广播剥离到最深合格 [rows,1] 即停——生产形态中 [1,1] 的图输入不是行掩码、不得登记，中间的 [rows,1] 才是（:518-551）；`squeeze` 不算可剥离广播，`logical_not(f).squeeze().reshape(-1,1)` 两次得到两个 mask 节点，端到端回归钉住"两个 mask 视图落在同一 ComputedBuffer 上时 def_kernel 按 buffer 名注册参数会互相覆盖、首个参数未定义、渲染 kernel 抛 NameError"的历史故障形态（生产 `is_live_type` 即此形态，:1201-1231 注释）；lowering 侧由 `_dedup_inputs` 同名合并闭合（[矩阵乘族卡](torch_npu_inductor_triton_matmul_kernel_family.md) 已持去重/回退表）。
- **kernel 模板配置契约**（multi_slice_concat.py 助手的直接单元锚，实现面卡片未记录）：`_pad_width` 输出为 2 的幂且 32 字节整数块（:824-836）；`_get_configs` 的 `BLOCK_ROWS` 为 2 的幂、并行度约束 `programs*2 >= min(rows, num_vector_core)`、56 核/378 行/64-128 段得 `BLOCK_ROWS=8`（:838-869）；tile 预算 `_ub_bytes() // _ASSUMED_LIVE_TILES // esize`，段数少于假定并发 tile 数时按实际段数放大，超出后不再收缩（:871-887）；padding 用前缀掩码 `cols1[None,:] < width` 掩蔽（非 `<= cols`，:905-912）；全部索引项携带 `INDEX_DTYPE`，禁止隐式 `tl.int32`，行基址经 `seg_rows = tl.full([], ROWS, INDEX_DTYPE)` 再乘 32 而非裸 `ROWS * 16`（:966-980）。
- **端到端方法论**：pass 未命中时数值检查 vacuously 通过（回退 aten.cat 仍 bitwise 正确），测试以注册表包裹 spy 计数 op 节点数证明 pass 真的触发（:100-132）；超预算段（`_pad_width > _max_tile_elems`）在 lowering 回退逐 slice 拷贝而 pass 层仍触发，模板不可达（:1160-1183）；`_pass_spy` 之外 `ASCEND_CUSTOME_PASS_REGISTER` 直接以函数名定位替换（无 dict 层锁，测试自身负责还原）。

## 动态形状 FX pass 的硬开关（test_dynamic_shape_fx_passes.py）

`NPU_INDUCTOR_DYNAMIC_FX_PASS` 是设备无关单测断言的全局硬开关（canonical 全树零命中）：置 `"0"` 时 symbolic_shape_util 的符号比较全部退化为不可判定（`s0 == s0` 也 False），`resolve_size_arg` 对 SymInt 返回 None，`materialize_shape` 拒绝符号维、纯静态形状仍原样通过（:294-303, :459-482）。开关按调用时环境读取（测试内直接设 env 再调 pass），不是导入期冻结。三值判定语义：不同符号不可证等（False、不加 guard）、`s0+1 > s0` 可证、`resolve_size_arg(True/1.5) -> None`、`materialize_shape` 只接受锚维长度（`s0*s0` 不可具体化返回 None）。逐 pass 动态行为：fold_expand/view_fold/fold_slice 恒等折叠、fold_reduce 仅静态 1 维、repeat_to_expand 仅纯广播、cat_to_view 全维覆盖才折叠，开关关闭时上述全部退化为静态判定。

## stack_sum 的算术与视图事实（test_stack_sum_pass.py）

`stack_sum_to_add_chain_pass` 同时匹配 cat(dim=0)→reshape→sum(dim=0) 与 unsqueeze→cat→sum 两种形态；FP16/BF16 输入把 add 链升 FP32 累加再一次性降回——n 输入产生 n 次 upcast + 1 次 downcast（3 输入 = 4 个 convert 节点），输出 dtype 不变（:106-115）；输入是列 slice 时保留为视图（4 个 slice 不删，:149-167）；cat 有其它用户、sum 在非 stack 轴、整数输入（int sum 会升 int64 而 add 链不会）三种形态拒绝（:326-363）。插入节点必须携带 `meta['val']`（走 propagate_fake_tensor 路径，ShapeProp 不可达，:269-291）；符号 batch 匹配且复用一次编译。数值验收用图级 A/B：改写后对 FP32 golden 的误差不得超过未改写基线 + 一个 FP16 ulp（两条路径都 FP32 累加、单次舍入，正常 bitwise 相等，:182-196）。

## remove_cast 与 pass 组装顺序（test_remove_cast_after_slice_by_add_cat.py、test_slice_cat_pass_composition.py）

- remove_cast_after_slice_by_add_cat 把 slice-cat 的逐段 cast 收拢为 cat 后单次 cast：NaN/Inf/-0.0 逐位保留且 signbit 相等、幂等、支持显式/嵌套/零 batch、浮点全 dtype 对（FP16/BF16/FP32/FP64 互转）、rank 1-4 与全部拼接轴、不同源 dtype 切分 run（两源两 cast）；拒绝：CPU 张量、单 slice 无 dense、纯 slice 无 dense、零宽段、cat meta 缺失、图内有 add_ 变异、非浮点 dtype、`_to_copy(non_blocking=...)`。两个 compile 用例 `@unittest.skip("currently not passing")`（动态 batch+反向、rank3 fp16 提升）——跳过状态是固定提交的静态意图。
- **注册顺序断言**（fx pass 安装顺序）：`remove_cast_after_slice_by_add_cat → sink_pointwise_cat_pass → multi_slice_concat_pass` 在 `ASCEND_CUSTOME_PASS_REGISTER[POST]` 中必须按此序排列；cast 收拢不先做，multi_slice 无法折叠掩码段（:135-151, composition :32-42）。DEFAULT_SHUT_DOWN_PASSES 把 sink 与 MSC 一起开关，cast 收拢独立默认开启；三个 pass 全部 `ignore_inference_check=True`（训练生效）。pass 集变化参与 FX 缓存身份（[编译资源卡](torch_npu_inductor_compile_resources_and_passes.md) 的 uuid 机制），spy 注入即改变 `AscendCustomPostPass().uuid()`。
- `max_pointwise_cat_inputs` 只控制 MSC 的原生 cat 路由，sink 无 cat 输入数上限（sink 测试 :79-81 注释）；混合 cast+clamp 分支下 cast 收拢与 sinking 各留一个完整三输入 cat，copy-free 预算保原生。端到端回归声明"外部 custom-op 的 eager 回退不能验证融合"——生成代码不得含 `torch.ops.npu_ext.multi_slice_concat.default(` 直调（composition :167-169）。
- `sink_pointwise_cat` 测试新增事实：**ReLU 不下沉**——注释原义 "NPU compiled ReLU currently differs from eager for signed zero"（:141-144），与零阈值 clamp 同属符号零保护；其余形态（同链相邻/公共外层运算不合并/中间舍入 cast 不重排/逐列 bias 拒绝/行 cat 拒绝/共享用户不删）均为 [FX 改写条件卡](torch_npu_inductor_fx_rewrite_conditions.md) 已有规则的镜像。

## filter_masks 的尺寸符号守卫（test_dynamic_cat_mask.py）

回归钉住 `NPUIndexTritonKernel.filter_masks`（codegen/triton.py）对动态维 cat 的负载掩码语义：尺寸符号（s0/ps0/i0）出现在 `current_subblock_axis` 时，守护该次 load 的 tmp 掩码必须保留（历史 bug：符号既不贡献掩码又使子集测试失败，tmp 掩码被丢、动态维 cat 首段越界，:1-9 docstring）；旁边有真循环轴时冗余轴掩码仍被清（`{y1, s0}` → 保留 tmp3 + x0_mask）；非本 load 索引的循环轴的守护掩码被丢弃；无 subblock 时全部掩码不动。端到端：`mark_dynamic(head, 1)` 编译后第二组更宽的 extent 复用同一 kernel，守护必须跟随符号而非 trace 时的尺寸。与[归约/Welford 测试契约卡](torch_npu_main_inductor_reduction_welford_tests.md)的 "filter_masks 只清字符串名掩码" 结论互补，本文件补尺寸符号轴这一类。

## 已覆盖镜像与边界

- test_grouped_matmul_pass.py（352 行）整文件为 [FX 改写条件卡](torch_npu_inductor_fx_rewrite_conditions.md) 分组 GEMM 节的逐条测试镜像（`_gmm_plan_batch_size(33)→17`、80 组 27/27/26、min_groups=8/max_rows 静态门/行 cat/不等宽 bucket/beta 拒绝、split_item=0/group_type=-1、多用户分支单独剔除其余 15 支仍融合），唯一新增数字是注释中的分组相对 RMS 误差 6.6e-06（matmul 自身噪声级，fp16 累加序差）与"81 次下发降为 4 次"的计数表述。
- 实现面归属：multi_slice 的 lowering 回退表/no-fuse 输出/`_ub_bytes()` 读取归 [矩阵乘族卡](torch_npu_inductor_triton_matmul_kernel_family.md)；pass 注册/关闭集合/缓存身份归 [编译资源卡](torch_npu_inductor_compile_resources_and_passes.md)。本卡只记测试侧契约，不重述实现。
- 静态口径：全部未运行；bitwise/signbit 断言、`_pad_width` 表、BLOCK_ROWS 并行度、INDEX_DTYPE 渲染、`_pass_spy` 计数均为源码级阅读；两处 `currently not passing` 跳过不证明当前套件执行其余用例。
