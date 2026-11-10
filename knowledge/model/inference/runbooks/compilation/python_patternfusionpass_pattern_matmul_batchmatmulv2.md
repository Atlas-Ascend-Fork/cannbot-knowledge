---
{
  "type": "Runbook",
  "title": "Python PatternFusionPass 双 pattern 实现 MatMul/BatchMatMulV2+Add→GEMM 及 ONNX/torchair 双前端验证",
  "description": "用 ge.passes.PatternFusionPass 注册两个 @pattern（MatMul(a,b)+c 与 BatchMatMulV2(a,b)+c）加 GEMM(a,b,c,1.0,1.0) replacement，经 ASCEND_GE_PY_PASS_PATH 加载，同时覆盖 ONNX 导入（ge:BatchMatMulV2+ge:Add）与 torchair 在线（ge:MatMul+ge:Add）两条前端；NPU 上 baseline/optimized 输出逐位一致（max abs diff 0.0），负例不命中且图不变。",
  "tags": [
    "task.implementation",
    "topic.compilation"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-03T12:00:00Z",
  "updated_at": "2026-11-09T09:37:53Z",
  "platforms": [
    "a3"
  ]
}
---

# Python PatternFusionPass 双 pattern 实现 MatMul/BatchMatMulV2+Add→GEMM 及 ONNX/torchair 双前端验证

## 适用场景

- 平台/版本：Ascend910_9362（ACL 逻辑卡 0 = `ASCEND_RT_VISIBLE_DEVICES=1` 重映射的物理卡 1）、CANN 9.3.0、Python 3.11.4。
- 框架：GE Python pass（`ge.passes` + `ge.es`，es_all wheel 来自公共 es-api-runtime）；双前端触发——pyatc CLI 离线编译 ONNX（torch 2.7.1 导出 opset 17、`do_constant_folding=False`）与 torchair 在线（torch_npu 2.7.1.post4 内置 torchair）。
- 目标：把 `x,y → MatMul/BatchMatMulV2 → Add(mm_out, z) → Output` 两算子子图替换为直接消费 x/y/z 的单个 `GEMM`（本例负载 x(2,3)、y(3,2)、z(2,2) float32 的小模型）。
- 缺失信息：仅单次会话、单小模型、静态 2D shape、float32；其他 dtype/动态 shape/大模型未验证。

## 触发与观测

- ONNX 导入后的真实 op type（dump-first，事件 322/323）：`PreRunBegin` 为 `ge:BatchMatMulV2 + ge:Add`（torch opset 17 导出为分离的 MatMul→Add 两节点，事件 150）。
- torchair 在线路径（事件 555/556）：`ge:MatMul + ge:Add`。
- pass 加载后日志（事件 357，ONNX 路径）：

```
[PythonFuseMatMulAndAddPass] module loaded from ASCEND_GE_PY_PASS_PATH, registering for stage BEFORE_INFER_SHAPE
[PythonFuseMatMulAndAddPass] pattern defined: MatMul(a, b) + c
[PythonFuseMatMulAndAddPass] pattern defined: BatchMatMulV2(a, b) + c
[PythonFuseMatMulAndAddPass] meet_requirements: matched [BatchMatMulV2,Add] -> guard PASSED (no dtype/shape restriction)
[PythonFuseMatMulAndAddPass] replacement called, matched nodes [BatchMatMulV2,Add]
[PythonFuseMatMulAndAddPass] replacement built: GEMM(a, b, c, alpha=1.0, beta=1.0)
```

## 探针与操作

实现源码（事件 103 落盘 `src/python_fuse_matmul_add_pass.py`；事件 111 语法/注册自检 OK）。ES API 导入带回退（内置 ge.es.math 优先、ge.es.all 兜底、缺失置 None 由 `_require_es_apis` 显式报错）：

```
try:
    from ge.es.math import GEMM, Add, MatMul
except ImportError:
    try:
        from ge.es.all import GEMM, Add, MatMul
    except ImportError:
        MatMul = None
        Add = None
        GEMM = None

try:
    from ge.es.nn import BatchMatMulV2
except ImportError:
    try:
        from ge.es.all import BatchMatMulV2
    except ImportError:
        BatchMatMulV2 = None
```

核心类（两个 `@pattern` + `meet_requirements` + 带 fallback 的 `replacement`）：

```python
@register_fusion_pass(name=_PASS_NAME, stage=PassStage.BEFORE_INFER_SHAPE)
class PythonFuseMatMulAndAddPass(PatternFusionPass):
    """Fuse MatMul+Add / BatchMatMulV2+Add into GEMM at BEFORE_INFER_SHAPE."""

    @pattern
    def matmul_add(self, inputs):
        print("[{}] pattern defined: MatMul(a, b) + c".format(_PASS_NAME))
        _require_es_apis()
        a, b, c = inputs[:3]
        return MatMul(a, b) + c

    @pattern
    def batch_matmul_add(self, inputs):
        print("[{}] pattern defined: BatchMatMulV2(a, b) + c".format(_PASS_NAME))
        _require_es_apis()
        a, b, c = inputs[:3]
        return BatchMatMulV2(a, b) + c

    def meet_requirements(self, match_result):
        matched = _matched_types(match_result)
        print("[{}] meet_requirements: matched {} -> guard PASSED (no dtype/shape restriction)".format(
            _PASS_NAME, matched))
        return True

    def replacement(self, inputs, match_result):
        matched = _matched_types(match_result)
        print("[{}] replacement called, matched nodes {}".format(_PASS_NAME, matched))
        _require_es_apis()
        r_a, r_b, r_c = inputs[:3]
        try:
            out = GEMM(r_a, r_b, r_c, 1.0, 1.0)
            print("[{}] replacement built: GEMM(a, b, c, alpha=1.0, beta=1.0)".format(_PASS_NAME))
            return out
        except Exception as exc:
            print("[{}] GEMM replacement FAILED: {!r}; "
                  "fallback to rebuilding original structure, graph stays intact".format(_PASS_NAME, exc))
            try:
                if "BatchMatMulV2" in matched:
                    out = BatchMatMulV2(r_a, r_b) + r_c
                else:
                    out = MatMul(r_a, r_b) + r_c
                print("[{}] fallback replacement built: original MatMul/BatchMatMulV2+Add structure".format(_PASS_NAME))
                return out
            except Exception as fallback_exc:
                print("[{}] fallback replacement also FAILED: {!r}; re-raising to abort this rewrite".format(
                    _PASS_NAME, fallback_exc))
                raise
```

编译/运行前置条件（本轨迹实测必需，详见[私有 OPP 树 built-in 符号链接导致 pyatc ONNX 插件不加载（E13010）的定位与修复](opp_built_pyatc_onnx_e13010.md)）：

1. 私有 OPP 树 `built-in` 必须是真实目录（符号链接会致 E13010，事件 307/308）。
2. `PYTHONPATH=$GE_ES_API_PYTHONPATH`、`LD_LIBRARY_PATH=$GE_ES_API_LIB_DIR`、`ASCEND_GE_PY_PASS_PATH` 必须与 pyatc 同一条命令内联（事件 356）。
3. torchair 在线路径：`import torch_npu` 后 torchair 可用（torch_npu 2.7.1.post4 内置，事件 134/135/139）。

负例模型构造（事件 559，onnx.helper 生成仅含 MatMul 的图）：节点 `['MatMul']`，输入 x(2,3)/y(3,2)，输出 out(2,2)。

## 机制与判别

- 接口语义依据（GE 仓文档行号，事件 97）：`register_fusion_pass(*, name, stage, kind=None)`（Passes.md:398）；`PatternFusionPass` 引擎调 `patterns()/meet_requirements()/replacement()` 而非 `run()`（Passes.md:120-125）；`@pattern` 自动 capture 已访问外部输入与 return 输出（开发指南 §3.3，事件 59/63）；`BEFORE_INFER_SHAPE` 后仍进入 GE 统一 shape 推导。
- 双 pattern 的必要性由前端差异驱动：同一 `torch.matmul(x, y)+z` 在 ONNX 导入后是 `ge:BatchMatMulV2`，在 torchair 在线图中是 `ge:MatMul`（事件 361 vs 556）——两个 `@pattern` 各覆盖一条。
- GEMM 语义等价：`GEMM(a, b, c, alpha=1.0, beta=1.0) ≡ Add(MatMul(a, b), c)`；本轨迹 NPU 输出逐位一致（事件 490）为该等价提供单模型支持，不构成普适证明。
- 精度差异来源判别：baseline/optimized 与 CPU 参考的偏差完全相同（0.0013647079467773438），说明偏差来自 NPU float 计算路径而非融合（事件 490）。
- 结构收益（L0）：计算算子 2→1、中间 Tensor（2×2 mm 输出）消除（事件 361 节点对比）；时延未见差异（事件 599：baseline mean 0.0294 ms vs optimized 0.0297 ms，各 30 runs 单次观测，模型过小，不构成性能结论）。

ge.passes.PatternFusionPass 用 @register_fusion_pass(stage=PassStage.BEFORE_INFER_SHAPE) 注册、两个 @pattern 方法分别描述 MatMul(a, b) + c 与 BatchMatMulV2(a, b) + c、replacement 返回 GEMM(r_a, r_b, r_c, 1.0, 1.0)，经 ASCEND_GE_PY_PASS_PATH 加载后可同时覆盖 ONNX 导入路径（真实 op type 为 ge:BatchMatMulV2 + ge:Add）与 torchair 在线路径（ge:MatMul + ge:Add），替换后的 ge:GEMM 直接消费 x/y/z（另带 2 个标量 Const 输入），GEMM 节点带 pass_name 属性标记。

官方与在线证据：pyatc 生成的 fusion_result.json 记录 PythonFuseMatMulAndAddPass match_times=1 effect_times=1（baseline 编译无此条目）；torchair 在线路径 pass 日志显示 meet_requirements: matched [MatMul,Add] 与 replacement built: GEMM(a, b, c, alpha=1.0, beta=1.0)。

## 验证信号

全部为单次会话内单次观测，Ascend910_9362 / CANN 9.3.0：

- 结构（事件 361/365）：ONNX 路径 `PreRunBegin` 6 节点（3×ge:Data + ge:BatchMatMulV2 + ge:Add + ge:NetOutput）→ `RunCustomPassBeforeInfershape` 7 节点（3×ge:Data + 2×ge:Const + ge:GEMM + ge:NetOutput）；GEMM `inputs=['onnx::MatMul_0:0', 'onnx::MatMul_1:0', 'onnx::Add_2:0', 'Const_0_/Add_/MatMul_0:0', 'Const_1_/Add_/MatMul_1:0']`。baseline 同阶段 dump 不变（事件 369）。
- pass 归属（事件 376）：GEMM 节点属性 `name: "pass_name" / strings: "PythonFuseMatMulAndAddPass"`。
- 官方计数（事件 543/544）：fusion_result.json `PythonFuseMatMulAndAddPass {'effect_times': '1', 'match_times': '1'}`；baseline 编译无该条目。
- events 校验（事件 547/548）：`validate_evidence.py events --require-applied` 状态 PASSED。
- 在线路径（事件 551/552/556）：`torch_forward.py` exit=0、输出 tensor 正常；matched [MatMul,Add]；在线 dump `ge:MatMul+ge:Add → ge:GEMM`（PreRunBegin: Add+Data×3+MatMul+NetOutput → RunCustomPassBeforeInfershape: Const×2+Data×3+GEMM+NetOutput）。
- 精度（事件 486/487/489/490）：自研 ACL Python runner（logical device 0，warmup 5 + runs 30）推理两个 OM，`status: PASSED`；NPU 输出逐位一致；baseline/optimized 与 CPU 参考偏差同为 0.0013647079467773438。

精度（单次会话、单模型、Ascend910_9362 ACL 逻辑卡）：自研 ACL Python runner 推理 baseline/optimized 两个 OM，NPU 输出逐位一致（max abs diff = 0.0）；两者与 CPU 参考的最大绝对偏差同为 0.0013647079467773438（NPU float 计算路径固有偏差，非融合引入）。

- 负例（事件 562/563）：见下。

负例（不命中保持原状）：仅含 MatMul（无后接 Add）的 ONNX 图上 pass 正常加载、两个 pattern 正常定义，但 PreRunBegin 与 RunCustomPassBeforeInfershape 两张 dump 图完全不变（ge:Data×2 + ge:BatchMatMulV2 + ge:NetOutput），pyatc 编译成功，无断边。

- 图 diff 工具（事件 493/525/536/537）：声明预期变换规则（removed /MatMul,/Add；added GEMM+2 Const；`data_edge_changes: true`）后，`graph_integrity: PASSED`、节点/边变更全部在白名单内；`outputs` 签名检查因 pbtxt 缺可靠 outputs 签名保持 `NOT_RUN`（工具限制）。

## 适用与失效边界

- 已验证边界：float32、2D 静态 shape、x(2,3)·y(3,2)·z(2,2) 小模型、单卡；`meet_requirements` 恒 True（无 dtype/shape 守卫），生产复用需按需补守卫。
- ES API 依赖：es_all wheel 必须提供 GEMM/Add/MatMul/BatchMatMulV2 wrapper，并将 `PYTHONPATH`/`LD_LIBRARY_PATH` 与 pyatc 触发命令同条内联；定位探针和修复见 [es_all 环境变量不跨命令保留导致 pattern 静默构建失败](es_all_python_pass_pattern_pyatc.md)。
- OPP 依赖：私有 OPP 树的 `built-in` 必须为真实目录，内部子项可用符号链接；受控实验及修复见 [私有 OPP 树 built-in 结构导致 ONNX 插件不加载](opp_built_pyatc_onnx_e13010.md)。
- torchair 在线须先 `import torch_npu`（torchair 内置于 torch_npu/dynamo/torchair，单独 import 报 ModuleNotFoundError，事件 134/135/139）。
- 未验证分支：replacement 中 GEMM 构建失败回退重建原图的 fallback 路径未在轨迹内触发；`ge.es.all` 导入路径未在本环境实际生效（不存在该模块）。
- 性能：无 msprof L1 profiling；时延无差异（模型过小），只有 L0 结构收益（算子 2→1、中间 Tensor 消除）。
- 停止条件：负例图被改写、输出不一致、或 fusion_result 无 match/effect 记录时停止采用。
