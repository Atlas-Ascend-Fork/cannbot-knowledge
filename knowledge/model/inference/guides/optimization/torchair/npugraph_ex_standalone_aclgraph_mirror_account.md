---
type: Guide
title: npugraph_ex独立包acl_graph与集成镜像的差异账
description: 以函数级 AST 比较对账独立包与集成 acl_graph.py 两固定版：发布近同构、主线配置键层分化与独立包独有段。
tags:
- task.optimization
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/acl_graph.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/_acl_concrete_graph/acl_graph.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_acl_concrete_graph/acl_graph.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_acl_concrete_graph/acl_graph.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/_acl_concrete_graph/static_kernel.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_acl_concrete_graph/static_kernel.py
  role: implementation
created_at: '2026-11-12T14:57:20Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# npugraph_ex独立包acl_graph与集成镜像的差异账

## 版本与范围

对账 TorchAir 两固定版（主线 `92e1e967bd35ebc37a442b4a969730bf3cf77a3c`、发布 `7c6c754bed00c86ffaaa2a45cb7ac2724f058013`）里独立包 `npugraph_ex/npugraph_ex/_acl_concrete_graph/acl_graph.py`（2062/1596 行）与集成 `python/torchair/_acl_concrete_graph/acl_graph.py`（1882/1588 行）的同名镜像，方法是函数级 AST 归一比较（ast.dump 去属性，evidence 留档脚本），不改写任何一版；集成侧行段语义已由集成卡承载，本卡只记镜像差异本身。全程只读静态，未 import/执行上游、未运行公共 checks、无设备验证；既有卡已覆盖的行为只链接不重述。

## 发布快照两侧近同构

发布两树结构完全同名（24/24 顶层定义）：51 个共有定义 AST 逐字相同，仅 2 处不同。其一，`AclGraph.capture` 的 debug_dump 段：独立包侧（1215–1240）把 dump 收进闭包 `debug_dump()`、返回结果路径并按 `config.get('deadlock_check','0')=='1'`（1231）触发 `run_deadlock_check(res)`（1237），集成发布侧（1222–1229）只有 TORCH_COMPILE_DEBUG 环境门、无 deadlock 接线——集成 acl_graph.py 两固定版 rg 全树均无 run_deadlock_check 调用点，该接线是独立包专属（与 dfx 页承诺配对，见[死锁检查工具链](torchair_gegraph_check_deadlock_toolchain.md)）。其二，`get_node_all_placeholder_inputs` 的 dict 分支：集成两固定版都带 `.valus()` 拼写笔误（主线 242、发布 219），独立包两版均已是 `.values()`——同名镜像并非逐字节同构，不能从一侧推断另一侧。

## 主线配置键层分化

主线两树共 18 个同名定义 AST 不同，多数差异是同一行为在两套配置键上的表达：独立包读平铺公开键（`force_eager`、`static_kernel_compile`、`clone_input` 真值缺省 True、`clone_output` 真值、`capture_limit`、`super_kernel_optimize`/`super_kernel_optimize_options`、`reuse_graph_pool_in_same_fx` 键存在且真值即启用），集成读翻译后的内部字符串键（`run_eagerly`=='1'、`_aclnn_static_shape_kernel`=='1'、`clone_input`=="1"、`enable_output_clone`=="1"、`static_capture_size_limit`、`_super_kernel_*`，内存池复用改为「`disable_mempool_reuse_in_same_fx`!='1'」取反极性）。同形参数在两树传不同键，跨树混用 options 会静默失效；该分化由配置序列化层解释，见[配置对象边界](torchair_compiler_config_boundaries.md)与[静态Kernel双消费者](torchair_integrated_and_standalone_static_kernel_consumers.md)。静态编译调用形态也不同：独立包 `compile_static_kernel(self.fx_forward, *args, config=self.config)`（compile 1191–1302、run_eagerly_compile 2036–2062）整体传 config，集成按 `_aclnn_*` 键逐项取值传参——此差异已在[捕获键与首调](npugraph_ex_restored_capture_keys_and_first_call.md)记录，本卡不重述。

## 主线独立包独有段

独立包主线树相对集成主线独有四组。第一组 cond 支撑：`_cond_branch_gms_and_operands`（302）、`_cond_operand_fully_updated`（331）、`_remap_branch_update_rulers`（566）三个顶层函数，`AclGraph.__init__` 的 `contains_cond` 形参，capture/compile 里的 `NPUGraphCaptureCtx`/`ControlFlowOpWarmupCtx` 包装，以及 `get_updated_ops_rulers_param` 的 `placeholder_index_map`/`name_prefix` 扩展签名——语义由[cond 编译门控](npugraph_ex_cond_compile_validation_and_unwrap.md)、[cond 分派与输出缓冲](npugraph_ex_cond_dispatch_and_output_buffers.md)、[任务更新规则](npugraph_ex_task_update_rules_and_graph_keys.md)承载。第二组 `_static_kernel_dump_ctx`（1178–1191）：静态编译的 dump 运行本身是图捕获，密集分派会把 cond 展开成 host 读 pred、捕获中拒绝读回导致 dump 整体失败且不产算子 json、静态编译静默覆盖为空，故经 ControlFlowOpWarmupCtx 以分派模式记录条件节点。第三组捕获控制：`is_need_to_recapture` 开头的 `unsafe_skip_npugraph_capture_validation` 直接 False 与 `force_recapture` 计数+True 早退（1723–1730）、`reset_captured_graph` 的 force_recapture 计数器清理——集成 python/torchair 两固定版 rg 对 `force_recapture|unsafe_skip` 全树零命中，这两个功能页只对独立包成立，见[捕获控制](npugraph_ex_capture_controls.md)。第四组零散防护：`_set_stream_limit` 在设置前先读当前限核、与目标一致即跳过并注释说明 torch.npu 侧 set_stream_limit 会永久置位全局 enable_core_control、令 eager 每 aclnn 算子多两次设备查询且把 aic/aiv 计入 cache hash key（1481–1489），集成主线同方法（1318–1333）无此短路；`run()` 在 replay_func 为 None 时抛「前次 capture 失败」的专门 RuntimeError 而非裸 NoneType 调用错误（1709–1721，该守卫的独立包两版差异已由[捕获键与首调](npugraph_ex_restored_capture_keys_and_first_call.md)记录）。此外 `__init__` 1014–1025 对 contains_cond 且 `super_kernel_optimize` 真值而未开 `static_kernel_compile` 的组合告警「super kernel fusion is applied by op_compiler during static kernel compilation」——该告警只对 cond 图触发，不证明非 cond 图会得到同样提示。

## 边界

本账是两固定提交的静态镜像事实：AST 归一相等不代表字节相同，diff 涵盖全部顶层与类级定义但不含模块级语句与导入顺序的逐行核对；「集成无此分支/方法」限指 python/torchair 树 rg 全树零命中的名字，不排除集成侧以其他名字实现类似行为。固定 release 组合中 `_set_stream_limit` 整方法在两侧都不存在（发布树无流限核重设），主线独立包的短路守卫不能回推发布。全部结论未运行验证，捕获/重放/告警的实际时序属运行时证据。

## Evidence

- [固定主实现](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/acl_graph.py)（primary）：全文函数级 AST 比对窗口；302–373、566–602、689、1001–1025、1145–1210、1303–1350、1467–1492、1723–1751、2036–2062 定向实读。
- [固定发布实现](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/_acl_concrete_graph/acl_graph.py)（implementation）：全文 AST 比对；1215–1240（debug_dump 闭包与 run_deadlock_check 接线）、valus/values 分支定向实读。
- [固定集成主线](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_acl_concrete_graph/acl_graph.py)（implementation）：全文函数级 AST 比对；1318–1333、1545–1566、242 定向实读。
- [固定集成发布](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_acl_concrete_graph/acl_graph.py)（implementation）：全文函数级 AST 比对；219、1222–1229 定向实读。
## 发布独立包static_kernel镜像的接线分化

此前本卡只对账acl_graph.py；已补齐发布`7c6c754bed00c86ffaaa2a45cb7ac2724f058013`独立包`_acl_concrete_graph/static_kernel.py`（711行）与集成发布同文件的全文件`diff -w`（79行差异）。32个顶层定义同名同构，分化集中在五处接线：

- SoC名来源：独立包调`torch_npu.npu.get_device_name()`，集成走`_torchair.GetSocName()`。
- dump启停：独立包直接`torch_npu._C._aclop_start_dump/stop_dump`，集成经`_torchair.AclopStartDumpArgs/AclopStopDumpArgs`包装。
- 产物目录名：独立包`static_kernel_compile_outputs`，集成`aclnn_static_shape_kernel_outputs`——按集成目录名检索的工具找不到独立包产物。
- 异常面：集成`safe_resolve_output_dir`捕获`(PermissionError, OSError)`，独立包只捕获`OSError`。
- 提示文案：cache_compile场景的API名一为`torch.npu.npugraph_ex.inference.cache_compile`、一为`torchair.inference.cache_compile`。

其余为命名空间导入与排版。主线独立包static_kernel（1347行）相对两发布版的 cond/捕获控制独有段已由[静态Kernel双消费者](torchair_integrated_and_standalone_static_kernel_consumers.md)与其他卡承载，本节不重复；发布侧Gloo、run包安装与reselect流程两树同构，行为按[run包生命周期](npugraph_ex_static_kernel_run_package_lifecycle.md)核对。

## 来源与复核范围

- [新增来源 1](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/_acl_concrete_graph/static_kernel.py)（implementation）：1–711全文件与集成发布`diff -w`；分化点定位291–303、351–381、603–623。
- [新增来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_acl_concrete_graph/static_kernel.py)（implementation）：作为diff基线全文件比对（该文件既有审阅范围见[静态Kernel双消费者](torchair_integrated_and_standalone_static_kernel_consumers.md)固定实现来源2）。
