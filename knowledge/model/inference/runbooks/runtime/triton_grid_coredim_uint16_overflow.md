---
{
  "type": "Runbook",
  "title": "昇腾 Triton kernel grid 超限（CoreDim ≤ 65535）：首维溢出与三轴乘积映射、截顶与 chunk 化规避",
  "description": "Triton kernel 在昇腾 NPU 上启动时 grid 维度受 rtKernelLaunch coreDim ≤ 65535 硬上界约束：grid 首维（逐行规约 kernel 的 token 行数）或三轴乘积超限即抛 coreDim can't be greater than UINT16_MAX / EE1003。诊断先算 gridX*gridY*gridZ 是否超限；规避统一采用截顶/压缩 axis 0 + kernel 内行循环。",
  "tags": [
    "task.debugging",
    "topic.compilation",
    "topic.model_serving"
  ],
  "status": "stable",
  "sources": [
    {
      "resource": "https://github.com/vllm-project/vllm-ascend/issues/3548",
      "role": "evidence"
    }
  ],
  "created_at": "2026-07-15T00:00:00Z",
  "updated_at": "2026-11-06T09:40:40Z",
  "platforms": [
    "agnostic"
  ]
}
---

# 昇腾 Triton kernel grid 超限（CoreDim ≤ 65535）：首维超限与三轴乘积超限的诊断与规避

> 本卡合并两个来源：vllm-ascend issue #3548 的 grid 首维溢出案例（原卡内容，保留）与 2026-10 轨迹实测的 triton-ascend 3.2.1 driver 源码取证（grid 三轴乘积被映射为 coreDim）。两条证据链互补：前者给出症状与逐行截顶修法，后者给出 driver 级根因、逐字报错与 chunk 化规避模式。

## 适用场景


- **后端**：Triton kernel 跑在昇腾 NPU 上（`torch_npu` triton），grid 第一维被映射为 NPU 的 **CoreDim**。
- **grid 形状**：kernel 以 `grid = (M, ...)` 启动，`M` = 参与规约的 token 行数（batch × seq 展平），即每行 token 分配一个 program/core。
- **规模阈值**：`M > 65535`（UINT16_MAX）。大批量 + 长生成会把 `M` 推过此线——例如高并发解码使 KV cache 占用逼近 100%、同一步待规约行数冲高时。
- 昇腾侧固有：CoreDim 取值上界为 `UINT16_MAX = 65535`；此约束不随硬件型号/CANN 版本放宽，是 NPU triton launch 的硬边界。

轨迹补充（triton-ascend 3.2.1，standalone Triton kernel，无 vllm 依赖）：


- 框架/模型：vLLM 仓 qwen4_exp（`${LOCAL_PATH_1}`，Kimi K3 attn_res 的 standalone Triton 移植，无 vllm 依赖）中的 `_hc_combine` triton kernel。
- 平台/版本：Ascend NPU（Device:0，具体型号未在轨迹中记录）、torch_npu、Python 3.12.9、triton 3.2.0（`${SITE_PACKAGES}/triton/__init__.py`）+ triton-ascend backend（`triton_ascend-3.2.1.dist-info`）。
- 工作负载：rows=7680、HC=4、hidden=2560、bf16，kernel grid=(7680, 4, 5)。
- 缺失信息：NPU 具体型号、CANN 包版本未在轨迹中记录；仅单会话单版本观测。

路径约定：`${LOCAL_PATH_1}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开；`${LOCAL_PATH_2}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开；`${LOCAL_PATH_3}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开；`${SITE_PACKAGES}` 为当前 Python 解释器的 site-packages 目录。使用前在本地设置这些变量；不同编号不可假定为同一位置。代码中的变量样式字符串也须替换，不依赖 Python 自动展开。

## 触发与观测


在昇腾 NPU 上启动一个 Triton kernel（`torch_npu` triton 后端），运行到**大批量 / 长序列**规模时抛出运行时异常：

```
coreDim=xxx can't be greater than UINT16_MAX.
```

或框架层报为 `invalid CoreDim`。此前小批量 / 短序列同一 kernel 正常，症状只在把 batch_size 或输出长度推高、并发规约行数冲高后才出现。对照面：同一 kernel 的上游 CUDA/GPU 版本从不报此错。

若你正观测到上述症状，且该 kernel 的 launch grid 第一维随 batch/序列长度线性增长（典型为「一行 token 一个 program」的逐行规约 kernel，如 (RMS)Norm / LayerNorm / gated-norm），则本页适用。

2026-10 轨迹观测（triton-ascend 3.2.1，grid=(7680,4,5)）触发同一上界的另一形态——`Invalid_Argument(EE1003)`：


运行 `python test111.py`（grid=(7680,4,5)，三轴乘积 153600）后进程 Abort，逐字输出（事件 17）：

```
terminate called after throwing an instance of 'std::runtime_error'
  what():  The Inner error is reported as above. The process exits for this inner error, and the current working operator name is _hc_combine_kernel.
Since the operator is called asynchronously, the stacktrace may be inaccurate. If you want to get the accurate stacktrace, please set the environment variable ASCEND_LAUNCH_BLOCKING=1.
Note: ASCEND_LAUNCH_BLOCKING=1 will force ops to run in synchronous mode, resulting in performance degradation. Please unset ASCEND_LAUNCH_BLOCKING in time after debugging.
[ERROR] 2026-10-15-21:02:09 (PID:1522550, Device:0, RankID:-1) ERR00100 PTA call acl api failed.
[PID: 1522550] 2026-10-15-21:02:09.886.246 Invalid_Argument(EE1003): Starting the compute task of the corresponding operator failed because value 153600 for parameter coreDim is invalid. Expected value: less than or equal to 65535.
        Solution: 1. Check the input parameter range of the function. 2. Check the function invocation relationship.
TraceBack (most recent call last):
        The argument is invalid. Reason: rtKernelLaunch execution failed.
```

## 探针与操作

### 修法（原卡，grid 首维截顶 + kernel 内跨步循环）


把「grid 首维 = M」的逐行 kernel 改成 **「grid 首维截顶到 65535 + kernel 内按 stride 跨步循环覆盖剩余行」**，两处配套改动缺一不可：

1. **launch 侧截顶 grid 首维**：定义 `MAX_CORES = 65535`，`grid = (M if M < MAX_CORES else MAX_CORES, ngroups)`，并把上限作为 `constexpr`（`N_CORES = MAX_CORES`）传入 kernel。这样启动的 program 数永不超过 65535，绕过 CoreDim 上界。

   ```python
   MAX_CORES = 65535
   grid = (M if M < MAX_CORES else MAX_CORES, ngroups)
   layer_norm_fwd_kernel[grid](x, ..., N_CORES=MAX_CORES, num_warps=num_warps)
   ```

2. **kernel 内跨步循环覆盖剩余行**：截顶后 program 数 `< M`，单个 program 需处理多行。用 `BLOCK_ROWS = M if M < N_CORES else N_CORES` 求每轮跨度，`n_iters = M // BLOCK_ROWS`、`remain = M % BLOCK_ROWS`；前 `remain` 个 row 多做一轮（`if row < remain: n_iters += 1`）以吃掉余数行；循环内以 `i * BLOCK_ROWS * stride_x_row + row * stride_x_row` 为基址跨步取址，逐行完成 mean/rstd 规约、(RMS)Norm、以及可选的 gating（如 `z * sigmoid(z)`）写回。

   ```python
   row = tl.program_id(0)
   BLOCK_ROWS = M if M < N_CORES else N_CORES
   n_iters = M // BLOCK_ROWS
   remain = M % BLOCK_ROWS
   if row < remain:
       n_iters = n_iters + 1
   for i in tl.range(n_iters):
       X_base = X + (i * BLOCK_ROWS * stride_x_row) + row * stride_x_row + group * N
       # ... 逐行 (RMS)Norm + 可选 gating 写回 ...
   ```

功能上与原逐行 kernel **等价**——只是把「一 program 一行」改成「一 program 多行、每隔 65535 步取址一次」，规约与归一化语义不变。

**通用抓手**：任何在 NPU 上以「行数当 grid 首维」启动、且行数可能随 batch/序列长度超过 65535 的 Triton 逐行 kernel，都要用「grid 首维 clamp 到 65535 + kernel 内 stride 循环」这一范式；不要假设 GPU 上不会溢出就照搬 grid。fork/vendored kernel 若直接从上游 CUDA 实现 import，须复核其 launch grid 维度上界是否踩 CoreDim 线。

### driver 源码取证（2026-10 轨迹）


1. 定位实际生效的 triton 安装与版本（事件 20/22）：
   `python -c "import triton; print(triton.__file__, triton.__version__)"`
   → `${SITE_PACKAGES}/triton/__init__.py 3.2.0`
2. 确认 ascend backend 存在（事件 26/27）：`ls ${SITE_PACKAGES}/triton/backends/` 输出含 `ascend` 与 `triton_ascend-3.2.1.dist-info`。
3. 在 backend 源码中 grep `blockDim|coreDim|gridX|grid_x`（事件 29），关键命中逐字如下（事件 30）：

```
${SITE_PACKAGES}/triton/backends/ascend/cpu_driver.py:
  Line 162:     def launch(gridX, gridY, gridZ, stream, cu_function,

  Line 191:         return mod.launch(gridX, gridY, gridZ, launch_enter_hook, launch_exit_hook, packed_metadata, *args)


${SITE_PACKAGES}/triton/backends/ascend/driver.py:
  Line 496:         int gridX, gridY, gridZ;

  Line 662:       nodeBasicInfo.data.nodeBasicInfo.blockDim = nodeBasicBlockDim;

  Line 764: static void _launch(const char* kernelName, const void* func, rtStream_t stream, int gridX, int gridY, int gridZ, std::vector<std::vector<int64_t>> &tensorShapes, std::vector<int> &tensorKinds{', ' + arg_decls if len(signature) > 0 else ''}) {{

  Line 771:   uint32_t blockNum4Workspace = gridX * gridY * gridZ;

  Line 779:     uint32_t blockNum = gridX * gridY * gridZ;
```

4. 读取 `driver.py` 760-799 行确认 `_launch` 源码（事件 32/33，逐字）：

```
764: static void _launch(const char* kernelName, const void* func, rtStream_t stream, int gridX, int gridY, int gridZ, std::vector<std::vector<int64_t>> &tensorShapes, std::vector<int> &tensorKinds{', ' + arg_decls if len(signature) > 0 else ''}) {{
765:   // only 1D parallelization is supported for NPU
766:   // Pointer type becomes flattend 1-D Memref tuple: base_ptr, data_ptr, offset, shape, stride
767:   // base_ptr offset shape and stride are not used, arbitrarily set for now
768:   std::string name = "";
769:   name.append(kernelName);
770:   void *workspace_addr_ptr = NULL;
771:   uint32_t blockNum4Workspace = gridX * gridY * gridZ;
772:   {get_backend_func("pre_launch", True)}
773:   {f'''
774:   uint64_t totalWorkSpaceSize = {workspace_size} * blockNum4Workspace;
775:   {get_backend_func("allocate_memory", "totalWorkSpaceSize", "stream")}
776:   ''' if workspace_size > 0 else ''}
777:   {'auto launch_call = [=]() -> rtError_t' if enable_taskqueue else ''} {{
778:     {get_backend_func("pre_launch", False)}
779:     uint32_t blockNum = gridX * gridY * gridZ;
```

### 规避改造：program 内行循环 + `_NPU_MAX_BLOCKS` 反算 chunk（2026-10 轨迹）


一次 edit 完成完整修改单元（事件 40，对 `attn_res_triton.py`）。新 kernel（逐字）：

```
@triton.jit
def _hc_combine_kernel(
    residual_ptr,
    block_output_ptr,
    injection_ptr,
    output_ptr,
    num_rows,
    stride_residual_row,
    stride_block_row,
    stride_injection_row,
    stride_output_row,
    GROUP_DIM: tl.constexpr,
    HC_COUNT: tl.constexpr,
    HAS_INJECTION: tl.constexpr,
    BLOCK_SIZE: tl.constexpr,
    ROWS_PER_PROG: tl.constexpr,
) -> None:
    # NPU rtKernelLaunch limits total blocks (gridX * gridY * gridZ) to
    # 65535, so axis 0 is chunked and each program loops over ROWS_PER_PROG
    # rows to keep the launch grid within the limit.
    chunk = tl.program_id(0)
    stream = tl.program_id(1)
    tile = tl.program_id(2)
    inner_offsets = tile * BLOCK_SIZE + tl.arange(0, BLOCK_SIZE)
    mask = inner_offsets < GROUP_DIM
    offsets = stream * GROUP_DIM + inner_offsets
    for i in tl.static_range(ROWS_PER_PROG):
        row = chunk * ROWS_PER_PROG + i
        if row < num_rows:
            residual = tl.load(
                residual_ptr + row * stride_residual_row + offsets,
                mask=mask,
                other=0.0,
            ).to(tl.float32)
            block_output = tl.load(
                block_output_ptr + row * stride_block_row + inner_offsets,
                mask=mask,
                other=0.0,
            ).to(tl.float32)
            if HAS_INJECTION:
                injection = tl.load(
                    injection_ptr + row * stride_injection_row + stream
                ).to(tl.float32)
                block_output *= 2.0 * tl.sigmoid(injection / HC_COUNT)
            tl.store(
                output_ptr + row * stride_output_row + offsets,
                residual + block_output,
                mask=mask,
            )
```

新增常量（逐字）：

```
# rtKernelLaunch rejects coreDim (total blocks) > 65535
_NPU_MAX_BLOCKS = 65535
```

launcher 反算 grid（逐字）：

```
    if rows:
        tiles = triton.cdiv(group_dim, block_size)
        max_row_chunks = max(1, _NPU_MAX_BLOCKS // (hc_count * tiles))
        rows_per_prog = triton.cdiv(rows, max_row_chunks)
        row_chunks = triton.cdiv(rows, rows_per_prog)
        injection_ptr = residual if injection_logits is None else injection_logits
        injection_stride = 0 if injection_logits is None else injection_logits.stride(0)
        _hc_combine_kernel[(row_chunks, hc_count, tiles)](
```

复跑命令（事件 43，workdir `${LOCAL_PATH_2}`）：`python test111.py 2>&1`。
数值校验：写 `${LOCAL_PATH_3}`（事件 47），对 (7680,2560,4)、(1,2560,4)、(3,128,2)、(65535//20+7,512,4)、(7,4096,8) 五组形状及无 injection 路径用 `torch.allclose(atol=2e-2, rtol=2e-2)` 对比参考实现（事件 50 运行）——首跑失败，失败点在参考实现自身（见下文边界）。

## 机制与判别

### 根因（原卡）


Triton kernel 的 **grid 第一维在昇腾上被映射为 NPU 的 CoreDim，其取值上界是 `UINT16_MAX = 65535`**。当 kernel 采用「一 program 处理一行」的逐行规约模式（`grid = (M, ngroups)`，`M` 为 token 行数）时，一旦 `M` 超过 65535，请求的 CoreDim 超界，NPU 直接拒绝并抛 `coreDim=... can't be greater than UINT16_MAX`。

这是 **backend_incompatibility**：同款 kernel 在 GPU 上 grid 首维上限约 `2^31-1`，几乎不可能溢出，因此直接从上游移植的 CUDA 版 kernel 未针对 NPU 的 CoreDim 上界做适配。根因不在模型逻辑、也不在数值精度，而在 launch 维度与后端物理核数编址位宽的错配。

### 参考实现及其约束（原卡）

### 参考实现及其约束

- **参考实现**：vllm-ascend `vllm_ascend/ops/fla.py` 的 `layer_norm_fwd_kernel`（FLA = flash linear attention），服务 [qwen3-next](../../concepts/models/qwen3_next.md) 的 [gated-deltanet](../../concepts/modules/gated_deltanet.md) 线性注意力路径中的 gated (RMS)Norm；对应线性递归核见 [recurrent-gated-delta-rule](../../concepts/kernels/recurrent_gated_delta_rule.md)。该 kernel 原本从上游 vLLM `vllm.model_executor.layers.fla.ops.layernorm_guard` 直接 import，`_layer_norm_fwd` 用 `grid = (M, ngroups)` 启动，未适配 NPU；vllm-ascend 在本仓 fork 了它并加上截顶 + 跨步循环。
- **约束（属该参考实现、非技术本身）**：`MAX_CORES = 65535` 是该 fork 的硬编码常量；复现规模为 Qwen3-Next-80B-A3B-Instruct、`--tensor-parallel-size 4 --max-model-len 32000 --enforce-eager`，用大批量 + 长输出（aisbench `batch_size=512`、`max_out_len=30000`）把 `M` 推过 65535。`z * sigmoid(z)` gating 是该 gated-norm 特有的写回步骤，其他逐行 kernel 按各自算子替换即可。
- **验证 / 回退**：修后在同一大批量、长输出、KV cache 占用达 100% 的场景下不再抛 CoreDim 异常，全部请求正常完成（吞吐为仓自报，无独立前后定量复测）。若怀疑跨步循环引入数值偏差，可在 `M < 65535`（不触发截顶、退化为逐行）与 `M > 65535` 两档下对拍归一化输出确认等价。

### 轨迹结论一：driver 将 gridX*gridY*gridZ 乘积映射为 coreDim


结论 1：triton-ascend 3.2.1 的 driver 在 `_launch` 中计算 `uint32_t blockNum = gridX * gridY * gridZ;`（driver.py:779）并作为 NPU 启动的 blockDim/coreDim，rtKernelLaunch 要求该值 ≤ 65535；kernel grid 三轴乘积超限即报 EE1003 Invalid_Argument 并使进程 Abort。
（锚点：事件 30/33 源码；信号：事件 30/33 源码命中 + 事件 17 运行时报错。`_launch` 注释 `// only 1D parallelization is supported for NPU` 表明 NPU 侧只接受单一扁平化 block 数。）

结论 2：报错数值 153600 恰等于 grid=(7680,4,5) 的三轴乘积，且三个轴单独取值（7680、4、5）均小于 65535，据此可以把『grid 乘积超限』与『单轴维度超限』两类根因区分开。
（锚点/信号：事件 17。判别分支：若为单轴超限类限制，报错值应对应某个单轴取值；实测报错值为乘积，排除该分支。）

结论 3：该错误以异步 C++ 异常终止（`terminate called after throwing an instance of 'std::runtime_error'`）出现，报错提示设置 ASCEND_LAUNCH_BLOCKING=1 可获得同步调用栈；asc 文档中『逻辑 blockDim 大于实际 AI 核数会插入异常同步导致 Kernel 卡死』是另一类相邻失效（挂死），与本例启动即失败不同。
（锚点/信号：事件 17 报错原文、事件 23 中 `asc/language/basic/utils.py` 的 blockDim 相关文档。）

未验证推断：
- driver.py 第 788 行存在 `enable_auto_map_parallel_blocks` 开启时的钳制路径（`blockNum = std::min(blockNum, (uint32_t){num_physical_blocks});`），本次 EE1003 发生说明该钳制在本环境未启用/未生效；该开关的实际行为未在轨迹中验证。
- `ENABLE_GRID_WARN_PRINT` 路径表明 blockNum 超过 `num_physical_blocks`（物理核数）时仅打印性能警告（`performance maybe reduced`），说明『超物理核数』与『超 65535 硬限制』是两个不同层次的约束；前者行为未实测。

### 轨迹结论二：chunk 化改造模式的机制


结论 1：把行维度（axis 0）压缩为 chunk、program 内用 `tl.static_range(ROWS_PER_PROG)` 循环处理多行并以 `if row < num_rows` 守卫边界，launcher 侧按 `_NPU_MAX_BLOCKS = 65535` 反算 `max_row_chunks = max(1, _NPU_MAX_BLOCKS // (hc_count * tiles))`、`rows_per_prog = triton.cdiv(rows, max_row_chunks)`、`row_chunks = triton.cdiv(rows, rows_per_prog)` 后以 `_hc_combine_kernel[(row_chunks, hc_count, tiles)]` 启动，可把 grid 乘积压入 65535 上限，且 program_id(0/1/2) 解码方式不变（grid 三维仍由 driver 传给 device）。
（锚点：事件 40 修改单元；支撑：事件 37 读到 driver.py grid_info 段把 grid 三维作为参数传给 device，故只重排 axis 0 不影响 `tl.program_id(1)/tl.program_id(2)` 语义；信号：事件 44 复跑通过。）

结论 2：修复后 test111.py（rows=7680、HC=4、hidden=2560、bf16）单次复跑输出 `test passed`，属功能级单次验证；按修复代码推导 grid 由 (7680,4,5)=153600 变为 (2560,4,5)=51200。
（锚点：事件 40/43/44；信号：事件 44。数值 `(2560,4,5)` 为按修复代码的确定性推导（65535//(4*5)=3276 → rows_per_prog=ceil(7680/3276)=3 → row_chunks=ceil(7680/3)=2560），非运行时打印。）

结论 3：数值校验未在轨迹内完成：对比参考实现的首跑因参考实现自身广播 bug 抛 `RuntimeError: The size of tensor a (4) must match the size of tensor b (7680) at non-singleton dimension 1`，轨迹最后一个事件将参考实现改为 `out = r + block_output.float().unsqueeze(1)`，修复后的复跑结果未出现在轨迹中。
（锚点：事件 47/51/54；信号：事件 51。）

判别说明：`test passed` 只能证明启动限制解除、脚本运行完成，不能证明数值正确。参考实现 bug 的机理：`r = residual.float().view(rows, hc_count, group_dim)` 形状为 (rows, hc, group_dim)，与 (rows, group_dim) 的 `block_output.float()` 直接相加时右对齐广播在第 1 维冲突（4 vs 7680），需 `unsqueeze(1)` 变为 (rows, 1, group_dim)；该失败发生在 host 侧参考实现，与 NPU kernel 无关。

未验证推断：`ROWS_PER_PROG` 为 `tl.constexpr`，rows 规模变化会改变该常量取值并触发重新 JIT 编译（按代码推导，编译行为未实测）。

## 验证信号

### 原卡 Evidence


- [vllm-ascend-issue-3548-bug-qwen3-next-has-a-runtime-bug-in-layer-norm-fwd-kernel-which-has-inva](https://github.com/vllm-project/vllm-ascend/issues/3548) — issue（closed，作者收尾确认已由对应修复 PR 解决）+ 修复 PR（state=MERGED，merge sha `534f32d27c0cc48731fbdae3701fbb6c3bb4332a`，2025-10-21，`vllm_ascend/ops/fla.py`）。
- 核心断言（`grid = (M, ngroups)` 溢出 CoreDim / 修法为截顶 + 循环）为合并态 diff 内容；根因（CoreDim = UINT16_MAX 上界）由 issue 标题 `invalid CoreDim`、PR 测试日志异常文本 `coreDim=xxx can't be greater than UINT16_MAX`、常量 `MAX_CORES=65535` 三点互证。

### 轨迹验证信号（单会话、单次观测）


以下均为本轨迹内客观观测（平台：Ascend NPU + triton-ascend 3.2.1；单会话、单次）：

- 事件 17：`Invalid_Argument(EE1003): ... value 153600 for parameter coreDim is invalid. Expected value: less than or equal to 65535.` + `rtKernelLaunch execution failed`（运行时报错，单次）。
- 事件 22：triton 版本与路径 `3.2.0`（`${SITE_PACKAGES}/triton/__init__.py`）。
- 事件 27：`triton/backends/` 下存在 `ascend` 目录与 `triton_ascend-3.2.1.dist-info`。
- 事件 30：grep 命中 `driver.py` Line 771/779 的 `uint32_t blockNum... = gridX * gridY * gridZ;`。
- 事件 33：`driver.py` 760-799 行源码逐字读取确认乘积计算与 `// only 1D parallelization is supported for NPU` 注释。
- 事件 37：`driver.py` 800-864 行显示 grid 三维通过 `grid_info` 作为参数传入 device，佐证 `program_id(0/1/2)` 解码与 grid 重构解耦（对修复模式的关键支撑）。
- 事件 23：asc `language/basic/utils.py` 中『逻辑 blockDim 不大于实际 AI 处理器核数，否则多轮调度插入异常同步导致 Kernel 卡死』的文档描述（用于区分相邻失效模式）。

证据等级：源码静态读取（事件 30/33/37）+ 运行时报错（事件 17）；无多版本/多硬件对比，结论限于 triton-ascend 3.2.1。


本轨迹内客观观测（平台：Ascend NPU + triton-ascend 3.2.1；均为单次）：

- 事件 41：edit 成功应用（`Edit applied successfully.`）。
- 事件 44：`python test111.py` 复跑输出 `test passed`（功能级、单一 shape 7680×10240 bf16，单次观测）。
- 事件 51：数值校验首跑抛 `RuntimeError: The size of tensor a (4) must match the size of tensor b (7680) at non-singleton dimension 1`（参考实现广播 bug，客观信号表明数值验证未闭合）。
- 事件 54：参考实现修复 edit（`out = r + block_output.float().unsqueeze(1)`）为轨迹最后一个事件，无后续复跑结果。
- 无性能测量：改造前后耗时/吞吐均未测，本卡不含任何性能结论。

## 适用与失效边界


- 已验证版本：triton 3.2.0 + triton-ascend 3.2.1（Ascend NPU）。其他版本未验证：若后续 triton-ascend 改为分轴映射、或默认启用 `enable_auto_map_parallel_blocks` 钳制，本规则失效。
- 触发条件是三轴乘积而非单轴：即使每个轴单独看都不大（本例 7680/4/5），乘积也可能超限；排查时应先算 `gridX*gridY*gridZ` 是否 > 65535。
- 报错为异步（栈可能不准）：需要准确调用栈时设置 `ASCEND_LAUNCH_BLOCKING=1`（同步模式，性能下降，调试后须取消）；本轨迹未执行该设置。
- 与两类相邻限制区分：（1）asc Python API 层面『逻辑 blockDim 大于实际 AI 核数 → 多轮调度插入异常同步、Kernel 卡死』是挂死类失效，不是本例的启动即失败；（2）driver 的 `ENABLE_GRID_WARN_PRINT` 路径针对 blockNum 超物理核数，仅性能警告。65535 是 rtKernelLaunch 对 coreDim 的启动硬上限。
- 根因的修复/规避模式见本卡「探针与操作」的 chunk 化改造小节。


- 已验证范围：triton-ascend 3.2.1、rows=7680/HC=4/hidden=2560/bf16 的单次功能运行通过（`test passed`）。数值正确性未在轨迹内闭合，引用本模式前应独立完成与参考实现的数值校验。
- 模式前提（按代码推导，未实测）：`hc_count * tiles ≤ 65535`。若其余两轴乘积本身超限，`max_row_chunks = max(1, _NPU_MAX_BLOCKS // (hc_count * tiles))` 退化为 1，grid 乘积仍可能超限；此时需把 tile 轴也纳入循环或压缩 BLOCK_SIZE。
- 行间需要跨 program 通信/同步的 kernel 不适用：本模式把多行折叠进同一 program 串行处理，仅适合行独立的 elementwise/按行计算。
- `tl.static_range(ROWS_PER_PROG)` + `if row < num_rows` 的写法保证非整块行（rows 不能被 rows_per_prog 整除）不越界；轨迹中的边界形状校验（如 rows=7、65535//20+7）因参考实现 bug 未跑完，边界行为未实测。
- 改造减少并行 program 数量（本例 153600→51200），对吞吐的影响未测量；不要据此写通用性能结论。
- 若 triton-ascend 后续版本改变 grid→blockDim 映射或启用自动钳制，本模式的必要性随之变化（见 本卡「适用与失效边界」 的边界）。

原卡约束（保留）：`MAX_CORES = 65535` 为该 fork 硬编码常量；复现规模 Qwen3-Next-80B-A3B-Instruct、`--tensor-parallel-size 4 --max-model-len 32000 --enforce-eager`。若怀疑跨步循环引入数值偏差，可在 `M < 65535`（不触发截顶、退化为逐行）与 `M > 65535` 两档下对拍归一化输出确认等价。
