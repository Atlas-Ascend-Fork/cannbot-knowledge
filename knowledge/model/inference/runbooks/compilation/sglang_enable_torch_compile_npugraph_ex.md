---
{
  "type": "Runbook",
  "title": "sglang 路径 B（--enable-torch-compile / npugraph_ex）在 910B3 单卡 decode 图捕获阶段必崩：错误签名按 batch size 区间分裂，四层阻塞逐层定位后仅以 4 处临时补丁跑通",
  "description": "在 Ascend 910B3 + CANN 9.1.0 容器内跑 sglang（fork c54ba66cd）+ Qwen2.5-0.5B：默认路径 A（eager + 裸 NPUGraph 捕获）端到端可用；开 --enable-torch-compile（backend=npugraph_ex）后 decode graph 捕获必崩，且两种错误签名由 torch_compile_max_bs（默认 32）分桶决定：bs>32 的 eager 区间报 ATB PagedAttentionOperation setup failed，bs≤32 的编译区间报 Dynamo non-Tensor。逐层定位出四层独立阻塞（A Dynamo non-Tensor / C msgspec 进 fullgraph / B ATB PagedAttention / D 捕获期 skip_guard_eval_unsafe guard），在一次性测试克隆上叠加 4 处补丁后首次端到端跑通（12 shape 捕获 513.55 s），但补丁已 git checkout 还原，上游 stock 配置路径 B 仍不可用。",
  "tags": [
    "task.debugging",
    "topic.compilation",
    "topic.graph_execution"
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

# sglang 路径 B（--enable-torch-compile / npugraph_ex）在 910B3 单卡 decode 图捕获阶段必崩：错误签名按 batch size 区间分裂，四层阻塞逐层定位后仅以 4 处临时补丁跑通

## 适用场景

- 模型/框架：sglang（fork `guanam/sglang`，HEAD `c54ba66cd4`，源码 editable 安装，`sglang 0.0.0.dev20048+gc54ba66cd`），torch `2.10.0+cpu` / torch_npu `2.10.0.post4`（内置 torchair/npugraph_ex），triton_ascend 3.2.2、sgl_kernel_npu 2026.6.1；模型 Qwen/Qwen2.5-0.5B-Instruct（bf16，page_size 128）。
- 平台：Ascend 910B3 单卡（NPU Id 7，`/dev/davinci7`，64GB HBM），npu-smi 25.5.0 驱动，CANN 9.1.0 容器（`quay.io/ascend/vllm-ascend:v0.23.0.post1`，容器名 `sglang-npu-verify`）。
- 目标与工作负载：`--attention-backend ascend` 单卡推理服务，decode 阶段 NPU graph 捕获（backend=full，capture bs=[1,2,4,8,12,16,24,32,40,48,56,64]），对比路径 A（默认，eager forward + 裸 `torch.npu.NPUGraph` 捕获）与路径 B（`--enable-torch-compile`，`torch.compile(fullgraph=True, backend=npugraph_ex)`）。
- 缺失信息：多卡、大模型（仅 0.5B 实测）、bf16 以外精度未验证。

路径约定：`${SGLANG_ROOT}` 为SGLang 源码根。使用前在本地设置这些变量；不同编号不可假定为同一位置。代码中的变量样式字符串也须替换，不依赖 Python 自动展开。

路径补充：`${MODEL_ROOT}` 为本地模型权重存储根。按本地环境设置变量，保留文中的相对路径关系。

## 触发与观测

触发：给 `python3 -m sglang.launch_server --model-path ${MODEL_ROOT}/Qwen2.5-0.5B-Instruct --attention-backend ascend --mem-fraction-static 0.5 --enable-torch-compile` 加 `--enable-torch-compile` 后，decode NPU graph 捕获阶段（`Capturing batches (bs=64 avail_mem=29.61 GB)`）进程崩溃退出，服务无法启动。路径 A（默认）同机同模型端到端可用（`/health` 200，`/generate` 输出 `" Paris. It is the largest city in Europe..."`，decode 捕获 12 shape 耗时 5.82 s）。

观测到的两种错误签名（均为客观日志）：

- 签名 1（默认配置，首个捕获 shape `bs=64`，eager 区间）：

```
82: Capturing batches (bs=64 avail_mem=29.61 GB):   0%|          | 0/12 [00:00<?, ?it/s][rank0]:[E1015 01:31:02.378289168 OpParamMaker.cpp:453] PagedAttentionOperation setup failed!
83: Exception raised from OperationSetup at ../third_party/op-plugin/op_plugin/utils/custom_functions/atb/AtbCommon.cpp:203 (most recent call first):
106:RuntimeError: The Inner error is reported as above. The process exits for this inner error, and the current working operator name is PagedAttentionOperation.
142:Exception: Capture cuda graph failed: The Inner error is reported as above. The process exits for this inner error, and the current working operator name is PagedAttentionOperation.
```

- 签名 2（`--cuda-graph-max-bs-decode 8` 使首个捕获 shape 为 `bs=8`，编译区间）：

```
101:torch._dynamo.exc.Unsupported: torch.* op returned non-Tensor
102:  Explanation: torch.* ops that return a non-Tensor cannot be traced into the Dynamo FX graph output
182:Exception: Capture cuda graph failed: torch.* op returned non-Tensor
```

判别实验：把 `--torch-compile-max-bs` 从默认 32 提到 64，强制首个 shape `bs=64` 进入编译区间后，错误立即从签名 1 切换为签名 2（`logs/repro_tc3.log`）。

## 探针与操作

探针 1（分桶判定）：读 `base_cuda_graph_runner.py` 的 compile_bs 构造（锚点事件 165 原文）：

```
    compile_bs = (
        [bs for bs in capture_bs if bs <= get_exec().graph.torch_compile_max_bs]
        if get_flags().capture.enable_torch_compile
        else []
    )
    return capture_bs, compile_bs
```

配合 `decode_cuda_graph_runner.py:1221` 的 `patch_model(model, bs in self.compile_bs, ...)`：`enable_compile = bs ∈ compile_bs`。对照实验（C 168 `--torch-compile-max-bs 64`）证实签名按 bs 区间分裂。

探针 2（逐层补丁前推，全部施加于一次性测试克隆 `${SGLANG_ROOT}`，验证后 `git checkout` 还原）：

- 层 A：NPU 版 `patch_model_npu` 缺少 CUDA 版 `patch_model` 的 `_to_torch(...enter_torch_compile...)` 预解析。原始代码（锚点事件 284 原文，`npu_graph_runner.py:78-94`）：

```
78: @contextmanager
79: def patch_model_npu(
80:     model: torch.nn.Module,
81:     enable_compile: bool,
82:     num_tokens: int,
83:     tp_group: GroupCoordinator,
84: ):
85:     if enable_compile:
86:         backend = get_compiler_backend("npugraph_ex")
87:         yield torch.compile(
88:             torch.no_grad()(model.forward),
89:             fullgraph=True,
90:             dynamic=False,
91:             backend=backend,
92:         )
93:     else:
94:         yield model.forward
```

  补上 `_to_torch` 预解析后 Dynamo `non-Tensor` 错误消失，暴露下一层（`InternalTorchDynamoError: TypeError: object.__new__(Contribution) is not safe, use Contribution.__new__()`，来自 `layer_boundary/residual/stream.py:155` 在 forward 里构造 `msgspec.Struct`）。
- 层 C：改 `fullgraph=True` 为 `fullgraph=False` 绕过 msgspec 构造，越过后暴露层 B（ATB `PagedAttentionOperation setup failed` 在编译 shape 上复现，栈经 `torch_npu/dynamo/torchair/_acl_concrete_graph/acl_graph.py:901 fx_run_eagerly` 落到 `torch_npu._npu_paged_attention`）。
- 层 B：env `ASCEND_USE_FIA=true` 让 decode attention 走 `npu_fused_infer_attention_score`（`ascend_backend.py:3118` 分支）而不是 ATB `_npu_paged_attention`（`ascend_backend.py:3193`），ATB 错误消失，暴露层 D。
- 层 D：`@torch._dynamo.disable` 加在 `layer_boundary/stage.py:85 Stage._prepare`，致命 guard 消失，12 个 shape 全部捕获成功。

失败路线（不可采用）：`torch._dynamo.config.allow_unspec_int_on_nn_module = True` 单独无效——`memory_pool_npu.py:263` 的 `k_buffer_layer = self.k_buffer[layer_id - self.start_layer]` 是用 int 索引 Python list，Dynamo 仍逐层特化，累计 191 次重编译导致 12 shape 捕获耗时 513.55 s（路径 A 仅 5.82 s，非同口径，仅作量级对照）。

## 机制与判别

结论 c1（分桶）：sglang 开启 --enable-torch-compile 后，decode NPU graph 捕获按 batch size 区间分裂为两种失败：bs > torch_compile_max_bs（默认 32）的捕获区间走 eager forward，报 ATB PagedAttentionOperation setup failed；bs ≤ torch_compile_max_bs 的区间走 torch.compile（backend=npugraph_ex），报 torch._dynamo.exc.Unsupported: torch.* op returned non-Tensor。把 --torch-compile-max-bs 提到 64 强制首个 shape bs=64 进入编译后，错误立即从签名 1 切换为签名 2。两个签名不是随机，而是由 `compile_bs` 分桶决定；ATB 路径失败的直接原因还与 `--enable-torch-compile` 使 `ascend_backend.py` 的 `not self.enable_torch_compile` 为假、绕过 NPU 图友好的 `forward_decode_graph` 落到普通 `forward_decode`（ATB `_npu_paged_attention`）有关。

结论 c2（最小可跑通补丁集）：在一次性测试克隆上叠加 4 处补丁后路径 B 首次端到端跑通：patch_model_npu 补 _to_torch 预解析（消 Dynamo non-Tensor）、fullgraph=False（绕过 msgspec.Struct 进整图）、ASCEND_USE_FIA=true（绕开 ATB _npu_paged_attention）、Stage._prepare 加 @torch._dynamo.disable（消捕获期 guard 重编译）；12 个 shape 捕获完成 elapsed=513.55 s，/health 200，/generate 输出正确。注意：该补丁集是验证性绕过而非上游修复——`@torch._dynamo.disable` 把整个 attention-prep 宿主路径踢出图（graph break），`enter_torch_compile` 会把 op 切到 `forward_native` 纯 torch 参考实现、在 NPU 上可能改变行为/性能，均未定稿。

结论 c3（D 层根因）：捕获期 skip_guard_eval_unsafe stance 下 D 层失败的根因是编译区内每次调用都新建的宿主对象：暖机两轮 48 次调用的状态序列（去掉对象 id）逐字节相同，而 id(stream.pending) 在 98 次调用中去重后 80 个不同、id(stream.residual) 84 个不同；把 warmup 从 2 次加到 6 次后同样的 guard 原样复现，证明不是 warmup 不足。致命 guard（`TORCH_LOGS=recompiles` 抓到）为 `layer_boundary/stage.py:85 _prepare` 的两支：`call["update"] = stream.pending.update`（stage.py:106）与 `steps.entry.prepare.keywords['step'].keywords['enters_stack']`（stage.py:111→:329 `plan.enters_stack`）；次要非致命项为 `memory_pool_npu.py:263` 的 `self._modules['attn'].layer_id == N` 每层一次特化。捕获轮 fatal 日志（锚点事件 418 原文）：

```
3437:[2026-10-15 02:15:06] NPUGraph: ERROR — capture failed: RuntimeError: Recompilation triggered with skip_guard_eval_unsafe stance. This usually means that you have not warmed up your model with enough inputs such that you can guarantee no more recompilations., graph_id=281469401636528, stream=<torch_npu.npu.Stream device=npu:0 npu_stream=0xaaab0ba2dad8>, pool=((0, 1),), device=0
```

插桩结论（`logs/dbg_stream.log`，98 次 `_prepare` 调用 = 暖机 2 轮×48 + 捕获轮×2；锚点事件 637 原文）：

```
pass1(warm1) calls: 48
pass2(warm2) calls: 48
pass3(capture) calls: 2
pass1==pass2 (除 id 外): True
distinct pending ids: 80 / 98
distinct residual ids: 84 / 98
```

机理：宿主状态确定稳定（两轮逐字节相同），变的只有对象身份；Dynamo 的 guard 依附对象身份（`stream.pending.update` 绑定方法），`Contribution`（msgspec.Struct）每次 forward 重建 → guard 每轮失配 → 每轮都要求重编译；暖机期允许重编译把问题掩盖，捕获期 `skip_guard_eval_unsafe`（`npu_cudagraph_backend.py:110` / `npu_graph_runner.py:172` 的 `torch.compiler.set_stance`）禁止重编译 → 直接抛错。未验证推断：guard 的确切类型（ID_MATCH / call guard）是从"状态相同、仅 id 变、guard 仍失配"反推的，未逐字核对 Dynamo C++ 源码。

## 验证信号

（平台：Ascend 910B3 单卡 + CANN 9.1.0 容器 + Qwen2.5-0.5B-Instruct；证据等级：真机容器内实测，单次）

- 事件 43/510：路径 A（默认）`/health` 200、`/generate` 返回 `" Paris. It is the largest city in Europe..."`、`Capture target decode NPU graph end. bs=[1,2,4,8,12,16,24,32,40,48,56,64], elapsed=5.82 s`。
- 事件 106：路径 B 默认配置（`--enable-torch-compile`）捕获 bs=64 报签名 1（ATB PagedAttentionOperation setup failed）。
- 事件 169：`--torch-compile-max-bs 64` 后同一 bs=64 报签名 2（torch.* op returned non-Tensor）——分桶判别实验成立。
- 事件 291：补层 A 后 Dynamo 错误消失、暴露 `object.__new__(Contribution) is not safe`（msgspec 层 C）。
- 事件 322：补层 A+C 后 ATB 错误在编译 shape 上复现（层 B）。
- 事件 342：加 `ASCEND_USE_FIA=true` 后 ATB 错误消失、暴露 `Recompilation triggered with skip_guard_eval_unsafe stance`（层 D）。
- 事件 418/422：warmup 2→6 次后 D 原样复现，重编译计数不变（`forward` 23 次、`_prepare`/`prepare` 各 2 次）——证否"warmup 不足"。
- 事件 637：插桩分析输出（上文原文）——状态序列相同、对象身份每次新建。
- 事件 475：4 处补丁叠加后 `Capture target decode NPU graph end. bs=[1,2,4,8,12,16,24,32,40,48,56,64], elapsed=513.55 s` + `The server is fired up and ready to roll!` + `health == 200`（单次观测）。
- 事件 479：补丁态 `/generate` 输出 `" Paris. It is the largest city in Europe and the third largest city in the"`（与路径 A 同 prompt 同结果，单次）。
- 事件 483：全部补丁 `git checkout` 还原、服务停止——所有验证均为临时可逆改动，未污染上游源码仓（事件 495 确认 `${SGLANG_ROOT}` git status 干净）。

## 适用与失效边界

- 失败条件（stock 配置路径 B 不可用）：sglang `c54ba66cd` + torch_npu 2.10.0.post4（CANN 9.1.0）+ `--attention-backend ascend` + `--enable-torch-compile`，decode 捕获阶段必崩，签名由首个捕获 shape 是否 ≤ `torch_compile_max_bs` 决定（默认 32）。
- 4 处补丁仅为定位用的最小可跑通集，不是修复：`fullgraph=False` 牺牲整图性；`@torch._dynamo.disable(_prepare)` 造成 graph break；`ASCEND_USE_FIA=true` 仅适用 FIA 支持的布局（page size 128）；`_to_torch` 照搬 CUDA 版会把部分 op 切到 `forward_native`。验证后补丁已全部还原，上游未修。
- 遗留未修（边界）：`layer_id` 索引 Python list 触发的 191 次重编译使捕获从 5.82 s（路径 A）膨胀到 513.55 s（补丁态路径 B，单次观测）；路径 B 修通后的稳态性能（replay guard 开销）与精度对比未做；修复 A 的最小正确形态（只预解析 dispatch_forward）未验证。
- 可能不成立的情况：sglang/torch_npu 版本升级（layer_boundary 机制重构、torch_npu 2.8+ 多图冲突修复、msgspec compile-safe 改造）后任一阻塞层可能消失；结论仅对本次实测版本组合负责。
- 停止/回退条件：适配 npugraph_ex 时按 A→C→B→D 顺序逐层打补丁验证；若某层补丁后无新阻塞则止于此；任一层不可绕过（如必须 fullgraph=True）则路径 B 整体不可用，回退路径 A。
