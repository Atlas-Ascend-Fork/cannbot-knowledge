---
{
  "type": "Runbook",
  "title": "ds41 融合算子替换移植进 vllm-ascend rfc 的 A3/A5 设备门控模式",
  "description": "把 dsnext 的 ds41 wheel 融合算子（indexer_prologue_k、compressor_v2、npu_hc_pre_v2/mhc_post、kv_compress_epilog_v2、npu_rms_norm、QLI/QSLI/MQSMLA 经 packaged_attention 换源）替换进 vllm-ascend rfc 分支的 DeepSeek V4.1 A5 路径后，A3 环境因无 custom_ops wheel 在 vLLM 子进程模型注册表检查即失败。门控模式：模块级 wheel 导入 try/except + _DS41_WHEEL_OPS 标志；层内 self._ds41_wheel_ops = _DS41_WHEEL_OPS and uses_a5_packed_cache()（compressor 侧 _fused）运行时分流；调用方按 packed_cache_ops 分流并恢复 A3 eager 回退路径（in-tree npu_hc_pre_v3/npu_hc_post、Triton pool_projected_eager）。A5 门控分支与已通过逐层探针精度对比（索引 100% exact、greedy 文本一致）的替换版本逐字相同；A3/A5 双平台验证完成后作为 replace dsv4.1 op 系列提交。",
  "tags": [
    "task.implementation",
    "topic.graph_execution",
    "topic.parallelism"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-03T12:00:00Z",
  "updated_at": "2026-11-06T09:40:40Z",
  "platforms": [
    "a3"
  ]
}
---

# ds41 融合算子替换移植进 vllm-ascend rfc 的 A3/A5 设备门控模式

## 适用场景

- 框架：vllm-ascend `rfc/vllm_cann` 分支（基线 vLLM v0.30.0），模型 deepseek_v41（DeepSeek V4.1 Flash，A5 走 MRV2 + packed cache）。
- 移植来源：vllm-ascend-dsnext `wzc_indexer` 分支的 ds41 wheel 算子族（`cann_ops_transformer.ops.ds41` + `custom_ops`，CANN 9.2 时代封装）：`indexer_prologue_k`（wk 投影+RMSNorm+部分 RoPE+MXFP4 量化+分离/折叠双平面写入一体）、`compressor_v2`（投影+门控池化一体）、`npu_hc_pre_v2`/`mhc_post`、`kv_compress_epilog_v2`（wheel 版）、`npu_rms_norm`，以及经 `packaged_attention.py` dispatcher 契约换源的 QLI/QSLI/MQSMLA。
- 目标：A5 上启用 ds41 融合算子栈，A3（无 custom_ops wheel、`cann_ops_transformer` 可能无 ds41 子模块）完整回退 rfc 原有 in-tree/Triton 实现；DSpark draft 层经 `DeepseekV41DecoderLayer` 继承自动被同一门控覆盖。
- 工作负载：A5 真权重 DP8/EP8 服务请求 + FULL_DECODE_ONLY 图捕获 + DSpark；A3 W8A8 启动验证。

路径约定：`${LOCAL_PATH_1}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开。使用前在本地设置这些变量；不同编号不可假定为同一位置。代码中的变量样式字符串也须替换，不依赖 Python 自动展开。

## 触发与观测

触发：算子替换初版在 model.py 顶部直接 `import custom_ops` / `import cann_ops_transformer`，A3 环境启动时 vLLM 在子进程里做模型架构检查（`registry.inspect_model_cls → _run_in_subprocess`，只 import 模块不跑 forward），立刻 ImportError：

```
File "${LOCAL_PATH_1}", line 15, in <module>
    import custom_ops  # noqa: F401  # Registers torch.ops.custom.* from the wheel.
ModuleNotFoundError: No module named 'custom_ops'
```

（用户从 A3 服务器转贴，事件 1086；A5 服务器装有两 wheel 故全程无此错误。）

门控修复后，A3 的错误从"启动检查阶段"推进到"worker 模型构建阶段"（HCCL 通信组创建，事件 1145/1147）——注册表检查错误消失是门控生效的观测信号；再经 HCCL_IF_IP 网络修复后 A3 启动并通过验证（事件 1160 用户确认）。

## 探针与操作

门控实现分三层（均已用 reader 逐字复核）。

第 1 层：模块级导入保护（model.py，事件 1098）：

```python
try:
    import cann_ops_transformer  # noqa: F401  # Registers torch.ops.cann_ops_transformer.* from the wheel.
    import custom_ops  # noqa: F401  # Registers torch.ops.custom.* from the wheel.

    _DS41_WHEEL_OPS = True
except ImportError:
    # A3 environments do not ship the ds41 operator wheels; the decoder layer
    # falls back to the in-tree mHC operators there.
    _DS41_WHEEL_OPS = False
```

indexer.py 同型保护 + None 兜底（事件 1110）：

```python
try:
    from cann_ops_transformer.ops.ds41 import indexer_prologue_k
except ImportError:
    # A3 environments may not ship the ds41 operator package; the packed
    # cache path below requires it and raises a clear error when missing.
    indexer_prologue_k = None
```

第 2 层：层内运行时门控（model.py DecoderLayer `__init__`，事件 1104）：

```python
        # The ds41 wheel operators (mHC v2, fused compressor, indexer prologue)
        # exist only in the A5 operator-package environment; every other
        # device keeps this repository's in-tree operators.
        self._ds41_wheel_ops = _DS41_WHEEL_OPS and uses_a5_packed_cache()
```

`uses_a5_packed_cache()` 读 `HardwareCapability.DSV41_PACKED_CACHE` 硬件能力位（A5 profile 有、基类 `get_dsv41_packed_cache_ops()` 返回 None、A5 适配器返回 `MixedQuantPackedCacheOps`，device_op.py:66-68/1065-1068）。compressor 侧同型（事件 1116）：

```python
        # The fused ds41 compressor op exists only in the A5 wheel
        # environment; other devices keep the eager Triton pooling path.
        self._fused = uses_a5_packed_cache()
        self._ring_num_cores = None
```

hc_pre/hc_post 的双路径分流（model.py，事件 1107）：

```python
    def hc_pre(self, x, hc_fn, hc_scale, hc_base, pre_mix=None):
        plog("HC_PRE_IN", self.layer_idx, x, hc_fn, hc_scale, hc_base, pre_mix)
        if self._ds41_wheel_ops:
            out = torch.ops.custom.npu_hc_pre_v2(
                x=x,
                hc_fn=hc_fn,
                hc_scale=hc_scale,
                hc_base=hc_base,
                pre_mix=pre_mix,
                hc_mult=self.hc_mult,
                hc_sinkhorn_iters=self.hc_sinkhorn_iters,
                norm_eps=self.norm_eps,
                hc_eps=self.hc_eps,
            )
        else:
            out = torch.ops._C_ascend.npu_hc_pre_v3(
                x,
                hc_fn,
                hc_scale,
                hc_base,
                pre_mix,
                hc_mult=self.hc_mult,
                hc_sinkhorn_iters=self.hc_sinkhorn_iters,
                norm_eps=self.norm_eps,
                hc_eps=self.hc_eps,
            )
        plog("HC_PRE_OUT", self.layer_idx, *out)
        return out
```

`hc_post`（A5 → `torch.ops.cann_ops_transformer.mhc_post(residual, comb, x, post)`，A3 → `torch.ops._C_ascend.npu_hc_post` 的 4×unsqueeze 原形式）与 `rms_norm_cast`（A5 → `torch_npu.npu_rms_norm` + `.float()` 双输出，A3 → 原 `DeviceOperator.rms_norm_cast` 链含 vLLM RMSNorm 回退）同法门控（同一 edit，事件 1107）。

第 3 层：调用方按 `packed_cache_ops` 分流并恢复 A3 eager 路径（dsa_v41.py `_write_compressed_source`，事件 1129）：

```python
            if getattr(attn, "packed_cache_ops", None) is not None:
                # The fused ds41 compressor op takes the raw hidden_states; the
                # wkv/wgate projection and gated pooling happen inside the op.
                self._quantize_indexer_query(attn, prepared_indexer, metadata)
                latent = compressor.pool_projected(hidden_states, state_metadata)
            else:
                hidden_states_fp32 = hidden_states.float()
                # Finish the input cast before query quantization starts on the
                # auxiliary stream, so the WKV matmul can overlap that quantization.
                self._quantize_indexer_query(attn, prepared_indexer, metadata)
                kv = compressor.wkv(hidden_states_fp32)
                score = compressor.wgate(hidden_states_fp32)
                latent = compressor.pool_projected_eager(kv, score, state_metadata)
```

配套守卫：indexer packed 分支入口的明确报错（事件 1113）：

```python
            if indexer_prologue_k is None:
                raise RuntimeError(
                    "cann_ops_transformer.ops.ds41.indexer_prologue_k is required "
                    "on the A5 packed-cache path; install the ds41 operator wheels"
                )
```

compressor 融合路径的内部自洽守卫（事件 1139）：

```python
        from cann_ops_transformer.ops.ds41 import compressor as compressor_v2

        if not self._fused:
            raise RuntimeError("The fused ds41 compressor path requires the A5 wheel environment")
        if not hasattr(self, "_ring_pooled"):
```

命名取舍（判别依据）：两条路径签名不同（融合 `pool_projected(hidden_states, metadata)` 2 参 vs eager `pool_projected(kv, scores, metadata)` 3 参），Python 不支持按签名重载必须异名——`pool_projected` 让给 dsnext 融合路径（与 dsnext 逐字对齐），`pool_projected_eager` 函数体与 rfc 原版逐行相同（同一 Triton `compressor_from_projected` + norm）；附带安全收益是残留旧签名调用会立刻 TypeError 暴露而非静默走错路径。

## 机制与判别

结论 1（导入层）：

模块级 wheel 导入以 try/except 包裹并置 _DS41_WHEEL_OPS 标志（indexer 侧为 indexer_prologue_k=None 兜底），使没有 custom_ops/ds41 wheel 的 A3 环境也能通过 vLLM 启动时只做 import 的子进程模型注册表检查。

判别依据：vLLM 0.30.0 的模型注册表检查跑在干净子进程里，只执行 import 链（事件 752/866/1086 的三次同型失败）；静态审计工具结果（事件 1136）确认 `model.py 导入保护(try/except): YES / indexer.py 导入保护(try/except): YES`。

结论 2（运行时层）：

层内运行时门控 self._ds41_wheel_ops = _DS41_WHEEL_OPS and uses_a5_packed_cache()（compressor 侧为 self._fused = uses_a5_packed_cache()，调用方按 packed_cache_ops 分流）使 A5 走 ds41 wheel 融合算子、A3 完整回退 in-tree/Triton 实现。

判别依据：`_DS41_WHEEL_OPS and uses_a5_packed_cache()` 同时约束"wheel 在"与"设备是 A5"两个条件，双保险；A3 回退路径为 in-tree `npu_hc_pre_v3`/`npu_hc_post`、`DeviceOperator.rms_norm_cast` 原链、Triton `pool_projected_eager` + fp32 权重 + `_ring_num_cores`、indexer 的 `k_norm + wk + rotary + npu_dynamic_quant + scatter_cache_sk` eager 链（事件 1143 审计清单、1156/1157 最终代码复读）。indexer.py:166 的 `indexer_prologue_k is None` 守卫在 A3 永不触达——外层 `packed_cache_ops is None` 已挡住（基类返回 None，仅 A5 适配器返回实现），该守卫真正针对的是"A5 且 wheel 运行时缺失"场景（事件 1159）。

结论 3（A5 等价性）：

门控后的 A5 分支执行的代码与已通过逐层探针精度对比的替换版本逐字相同——QLI_OUT 304/304、QSLI_OUT 1024/1024、IDX_SELECT_POST 1328/1328 全部 exact，两次 greedy 生成文本一致——因此 A5 侧无需重新验证。

判别依据：门控 edit 只是在已验证代码外包裹 if/else，`_ds41_wheel_ops=True` 分支即原替换版本（事件 1144 论证）；替换版本的精度对比在先前的逐层探针实验中闭合：`QLI_OUT`/`QSLI_OUT`/`IDX_SELECT_POST` 100% exact、`SMLA_META_CONSUME` 100% exact（metadata blob 逐位相同，证实 ds41 与 packaged 为同代 kernel）、dummy 阶段 `SMLA_OUT` 94% exact、两次 greedy 生成文本完全一致（事件 982/1011 对比表 + 事件 1013 判定报告）；mHC v2/v3 是唯一算法级差异源（元素级漂移最高 ~10%，被 cache 量化与 greedy 裕度吸收）。混杂条件说明：两轮探针运行的 KV cache 池块数不同（71035 vs 71111，融合栈显存足迹略小所致），cache 类张量的逐字节对比被池尺寸差异屏蔽，判读以索引/输出探针为准。

结论 4（交付状态）：

A3 与 A5 双平台验证完成（用户确认），替换与门控已作为 replace dsv4.1 op 系列提交入库。

## 验证信号

- 静态检查（会话内工具结果）：门控修复后 4 文件 py_compile + ruff 全部通过（事件 1133，`All checks passed! ... === ALL OK ===`）。
- 门控审计（会话内工具结果）：AST 审计输出 `model.py:893 [torch.ops.custom.npu_hc_pre_v2] -> GATED`、`model.py:922 [torch.ops.cann_ops_transformer.mhc_post] -> GATED`、`indexer.py:173 -> GATED`，导入保护双 YES（事件 1136）；最终人工审计清单确认 A3 路径全部 in-tree/Triton（事件 1143）。审计曾报 3 处 UNGATED，其中 2 处为检查窗口误报、compressor 1 处以内部守卫补齐（事件 1139-1140）。
- A5 精度（NPU 服务器侧、用户转贴的 compare_probe_logs.py 输出，事件 982/1011）：索引类输出 100% exact、greedy 文本一致（单次对比，1 条固定 prompt、EAGER 模式、greedy 采样、探针含 .item() 同步）。证据等级：原始对比表转贴。
- A3 进展信号（服务器侧日志转贴）：门控前注册表检查 ImportError（事件 1086）→ 门控后该错误消失、失败推进到 worker 模型构建阶段（事件 1145/1147）→ HCCL_IF_IP 网络修复后 A3 验证完成（事件 1160 用户陈述）。
- 提交状态（会话内工具结果）：`git log --oneline -4` 显示 4 个 `replace dsv4.1 op` 提交、工作区干净（事件 1164）。
- 双平台"验证完成"（事件 1160）为用户确认性陈述，会话内无法对 A3/A5 机器直接复核；A5 侧有此前完整的探针对比链支撑，A3 侧有启动阶段推进链支撑，但 A3 修复后的服务日志未回报。
- 替换后首 token ~30s 为 wheel 算子 JIT 绑定编译的一次性开销（QLI/QSLI/MQSMLA 绑定在首个真实 prefill 才触发）；开启 DSpark + FULL_DECODE_ONLY 后图捕获充当全量预热、速度恢复正常（事件 1068-1078，用户陈述，无量化基线，不构成性能结论）。

## 适用与失效边界

- 适用：向 vllm-ascend（有 DeviceOperator/HardwareProfile 分发体系的版本线）移植依赖外部 wheel 的融合算子、且需保留无 wheel 设备回退路径的场景；门控粒度建议：模块级 try/except 标志 + 设备能力位（`uses_a5_packed_cache()`）的合取 + 调用方 `packed_cache_ops` 分流三层叠加。
- 失效边界：若目标设备也装了 wheel（`_DS41_WHEEL_OPS=True`）但硬件能力位不含 `DSV41_PACKED_CACHE`，仍走 in-tree 路径——即门控按"wheel 与设备同时满足"取交集；若未来 A3 也需要 ds41 算子，需重开 wheel 分发而非仅改门控。
- 部署前提：A5 运行环境需安装配套的 `custom_ops` + 新版 `cann_ops_transformer`（含 ds41 算子族与 `indexer_prologue_k`）wheel 及其 OPP 二进制（`aclnnCompressorV2` 等符号）；wheel Python wrapper 与二进制包不配套时会以 `aclnnXxx not found` 报错（事件 896-908 的排查链：从 csrc 提取 aclnn 符号清单 → nm -D 全盘扫描 → 对照 MISSING）。
- 权重格式边界：`indexer_prologue_k` 强制 wk 为 NZ 格式，本模式采用 `process_weights_after_loading` 内对 wk 单权重 `npu_format_cast` 本地强转，而不是全局 `weight_nz_mode: 2`——全局开关会把 MoE gate 的 BF16 权重也转 NZ，撞 rfc 特有的 A5 `npu_fused_matmul("16cast32")` 不支持 NZ 权重而崩溃（事件 873-895，两特性从未在同一仓库存过的组合冲突）。
- 钩子边界：vLLM 加载器只调用量化方法/顶层模型的 `process_weights_after_loading`；普通子模块（compressor/indexer）的权重适配钩子需在 ForCausalLM 顶层显式遍历 `named_modules()` 触发（镜像 dsnext，事件 912-930），否则 compressor 权重停留 FP32 触发 EZ1009 dtype 错误、indexer wk 停留 ND。
- 已知未闭合项：替换遗留的三个过期测试（test_dsa_v41.py:194 的 `quantize_mxfp4_indexer`→`quantize_query_mxfp4`、test_deepseek_v41_cache.py 的 `pool_projected`→`pool_projected_eager`、CP 测试的 fake prologue + 实例级 pool mock 适配）已修复（事件 1173-1234），但轨迹在发出清理后全量检查命令处截断（C 1236），该检查结果未记录；DSpark 接受率与 mHC v2 的对照、GSM8K/GPQA 类评测均未执行。
