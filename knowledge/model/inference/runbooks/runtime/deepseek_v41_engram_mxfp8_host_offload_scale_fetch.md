---
type: Runbook
title: 量化嵌入表Host卸载：保持查表行与scale配对
description: 接口条件：查表式Host卸载须让全局行号、量化值、scale和异步完成配套；ElasticBuffer是本文Engram接口，并非普通CPU权重卸载。
tags:
- task.debugging
- topic.memory
- topic.compute.quantization
status: draft
sources: []
created_at: '2026-11-02T08:24:24Z'
updated_at: '2026-11-03T01:38:52Z'
platforms:
- '950'
aliases:
- DeepSeek V4.1：Engram Host 查表与 scale
---

# 量化嵌入表Host卸载：保持查表行与scale配对

## 适用性与框架边界

本卡沿**行号→查表→scale 配对→完成后反量化**诊断。它讨论按命中行检索的大表接口，不能作为普通 CPU 权重 offload 的配置教程。

| 层次 | 读用范围 |
|---|---|
| 通用原则 | 同一查询行必须得到匹配的量化值与 scale；消费者只能在对应查询完成后读取，值与 scale 的所有权分别核对。 |
| 成立前提 | 目标系统确实使用查表式卸载，并已确定行号命名空间、分片、scale 覆盖轴和异步完成合同。不同接口的 scale 驻留与同步方式可以不同。 |
| recipes 专属 | ElasticBuffer.engram_write/fetch、Engram TP、本地值 shard 加设备 padded 全表 scale、E8M0 门禁和 wait_callable 是文中接口。**ElasticBuffer 查表不是普通 CPU 权重 offload**，不能翻译为 vLLM 通用 offload 开关。 |
| vLLM / 其他框架入口 | 若模型实际使用此类检索，检查嵌入/查表后端、量化方法、数据传输完成与模型消费者；普通线性权重卸载应追踪自己的加载/传输/执行合同。 |

本轮未验证 ElasticBuffer 外部 ABI 或 vLLM 接入，以下引用清理也不证明物理内存已回收。

## 适用场景

Engram 用上下文 hash 得到记忆表行号，查回若干 embedding 向量，随后由投影和 Gate 将检索内容与 token 隐藏状态结合。本卡只诊断“行号→量化表值→BF16 向量”的过程。Gate 的输出异常不一定源于 Gate；查错行、取错 scale 或提前消费 fetch 都会更早改变它的输入。

本文使用查表式 Host offload：把大表本体放到主机存储，设备只取本次命中的行。它与把线性层权重搬回设备再计算的普通 CPU 权重卸载职责不同。MXFP8 把 FP8 值与每个通道块的 E8M0 scale 分开保存；offload 不意味着所有配套张量都离开 device。以下接口细节限 recipes 中 DeepSeek V4.1 enable_engram_offload=True、ElasticBuffer 与 Engram TP（张量并行）行分片，各 rank 是通信组中的计算进程，BF16 表有独立分支。路线为 recommended_fastpath 的静态合同核查，范围限当前加载/fetch 方案。

目标平台为 950；本轮仅固定源码核验，未运行 CPU/NPU、编译、查表精度、Host 内存或通信性能测试。CANN、外部 ElasticBuffer 和通信环境版本未知。

## 现象

加载时全量反量化会改变存储方式；将全局行号配到局部 scale、把 exponent 字节当数值转换，或在 fetch 完成前消费数据，都会破坏检索输入。本轮没有实际内存、时延或数值故障记录，需通过下列职责边界判断部署问题发生在哪一步。

## 根因与判别方法

先核对目标查表接口的行号、值、scale 与完成条件；下表仅描述 recipes ElasticBuffer 实例。全表 scale 留在设备是该接口的选择，不要求其他系统采用相同驻留。

| 张量或符号 | 轴、单位与来源 | 消费者 |
|---|---|---|
| quant_weight | [R,C]；全表 FP8 值，R 为行数、C 为 embedding 通道 | loader → 各 rank Host shard |
| scale | [R,S]；每行 S 个通道块 scale | loader → padded 全表设备 scale |
| block_size | C/S；每个 scale 覆盖的通道数 | fetch 后 unflatten 与广播 |
| shard_rows / shard_start | ceil(R/P) / rank×shard_rows；单位为表行，P 为 Engram TP 数 | 本地表分片 |
| _mxfp8_shard | [shard_rows,C]；末 rank 有零补齐行 | ElasticBuffer.engram_write |
| _mxfp8_sf | [shard_rows×P,S]；全局 padded 行域 | engram_write 的 sf 参数 |
| flat_input_ids | [token行数,hash列数]，内容为全局表行号 | 展平为 int32 → fetch |
| fetched / fetched_sf | [命中行数,C] / [命中行数,S] 的值与 scale 编码 | wait 完成后的反量化 |
| output | [token行数,hash列数,C]，BF16 | 后续 Engram 投影与 Gate |

在本文 recipes 接口中，engram_write 的 scale 在 offload 准备时转到 NPU；表值与全表 scale 的所有权不同，不能按同一行分片公式一起截成局部表后仍用全局 hash 查询。

教学推演（非实测）：假设 R=5、P=2，则每 rank 分配 3 行，rank 0 对应全局 [0,3)，rank 1 对应 [3,5) 加一行 padding。scale 的 padded 全表行域为 6 行。若查询全局行 4，却只保存 rank 1 的两行 scale 并直接以 4 索引，行号命名空间已经错了。再令 C=8、S=2，则前四通道乘第一个 scale、后四通道乘第二个，不能把两个 scale 当作整行的两个任选值。

本实现 fetch 后将 scale 原始字节 e 左移 23 位再以 FP32 查看；对 e∈[1,254] 可解释为 2^(e-127)。例如正常编码 e=127 对应 1，e=128 对应 2。view(uint8) 读取编码；to(float32) 将低精度值变成可做乘法的数值，两者职责不同。e=0、255 和非有限值处理未验证，不能由正常例子外推完整 E8M0 ABI。

## 诊断路径

1. 确认目标系统使用按行查表式卸载后，找到自己的 hash 行号生产者、表分片 loader、Host 写入接口、异步 fetch 与反量化器。记录全局 R/C、TP rank/组、每 rank 行区间及 padding，确认返回行对应原查询顺序。
2. 记录 weight/scale dtype、原始 scale 编码、scale 行域与 S，检查 C 能整除 S。若同一行只在部分通道错误，先按块轴核对 scale；若跨 rank 或尾行才错，先查全局行号与本地所有权。
3. 记录 write 的 storage 与 sf 所属设备/对象，以及 fetch 请求、wait 返回和第一次消费的时点。预期只有完成合同满足后才能读取值和 scale；本文 ElasticBuffer 返回 callable 时，只有句柄不表示数据已取回，必须履行其 wait 合同。
4. 分别保存“模块引用、外部 buffer 所有权、allocator 已分配/保留内存、进程/Host 存储”信息。引用置空或 del 只能说明可见所有权变化；判断内存收益须测实际峰值和生命周期。
5. 修正后以同一表和行号对比 non-offload 与 offload 路径的首尾有效行、多块 scale 和不同 rank，先比较 BF16 向量再比较后续 Gate/模型输出。特殊指数编码应按实际外部包合同单独验收。

<details>
<summary>recipes / CANN Executor 完整实现对照（可选阅读）</summary>

## 快速检查

已有 recipes 源码时可选搜索；其他框架直接按上述角色记录元数据。

```bash
rg -n '_mxfp8_block_size|scale.dtype|sf_full|engram_write|engram_fetch|wait_callable|fetched_sf' models/deepseek_v4_1/models/modules/engram.py
```

## 系统信息

以下为 MultiHeadEmbedding 的加载、写入和查询完整调用链，依赖 PyTorch、torch_npu、通信组与 cann_ops_transformer.ops.ElasticBuffer。外部实现的内部完成、驻留与销毁策略没有随源码取得。

## 机制代码

### reset_parameters

这里跳过随机初始化，因为加载器随后零填并覆盖有效行；不能在未加载权重时直接运行。

```python
    def reset_parameters(self):
        # The loader fully overwrites this shared (zero_ + copy),
        # so skip nn.Embedding's normal_ init.
        pass
```

### 构造与分片元数据：MultiHeadEmbedding.__init__

输入总表行数、C、布局和通信配置；计算 padded_total_N、TP rank 及本地行数，保存 MXFP8 暂存引用。engram_dp_size 与 attn_dp_size 用于另一个 non-offload 查询分支，不应误套到 Host fetch。

```python
    def __init__(
        self,
        num_embeddings: int,
        dim: int,
        infer_config,
        layer_id: int,
        engram_layout: EngramLayout,
        comm_manager=None,
    ):
        self.layout = engram_layout
        self.num_heads = self.layout.n_heads
        self.embedding_dim = dim
        self.layer_id = layer_id
        self.infer_config = infer_config
        self.comm_manager = comm_manager
        custom_params = self.infer_config.model_config.custom_params
        self.engram_offload = bool(custom_params.get("enable_engram_offload", False))
        self.engram_tp_size = int(custom_params.get("engram_tp_size", 1))
        parallel_config = self.infer_config.parallel_config
        self.world_size = int(parallel_config.world_size)
        self.attn_dp_size = int(parallel_config.attn_dp_size)
        self.engram_dp_size = self.world_size // self.engram_tp_size
        self.engram_tp_group = None
        if self.engram_tp_size > 1 and self.comm_manager is not None:
            self.engram_tp_group = self.comm_manager.get_group(
                f"engram_tp_group_{self.layer_id}"
            )
        # Keep the rank-local vocabulary information for the non-offloaded
        # TP lookup path. VocabParallelEmbedding only performs the local
        # embedding lookup; this module must reduce the masked results.
        self.engram_tp_rank = (
            dist.get_rank(self.engram_tp_group)
            if self.engram_tp_group is not None
            else 0
        )
        self._engram_offloaded = False
        self._mxfp8_shard = None
        self._mxfp8_sf = None
        self._mxfp8_block_size = 0
        padded_total_N = (
            (num_embeddings + self.engram_tp_size - 1) // self.engram_tp_size
        ) * self.engram_tp_size

        super().__init__(
            vocab_size=padded_total_N,
            hidden_size=dim,
            padding_idx=None,
            params_dtype=(
                torch.bfloat16 if self.engram_offload else torch.get_default_dtype()
            ),
            tp_size=self.engram_tp_size,
            tp_rank=self.engram_tp_rank,
        )
        self.engram_vocab_size_per_rank = self.input_size_per_partition
        set_weight_attrs(
            self.weight, {"engram_fp8_weight_loader": self.fp8_weight_loader}
        )
```

### 加载：fp8_weight_loader

输入二维 FP8 表与二维 scale；输出模块内暂存或已反量化的本地参数。按三个阶段阅读：

| 阶段 | 关键变量 | 不变量 |
|---|---|---|
| 布局检查 | rows、cols、scale_rows、scale_cols | 每表行有同一行 scale，块宽为整数 |
| offload 准备 | mxfp8_shard、sf_full | 值只保存本 rank；scale 保留 padded 全表，尾行用正常单位 scale 编码 |
| non-offload | local_scale、dequant_weight | 局部有效行按块反量化成 BF16，padding 仍为零 |

```python
    def fp8_weight_loader(self, param, quant_weight, scale):
        """Load an Engram FP8 shard or prepare it for offload."""
        if quant_weight.ndim != 2 or scale.ndim != 2:
            raise ValueError(
                "Engram FP8 weight and scale must both be two-dimensional, "
                f"got weight={tuple(quant_weight.shape)}, scale={tuple(scale.shape)}"
            )

        rows, cols = quant_weight.shape
        scale_rows, scale_cols = scale.shape
        if scale_rows != rows or scale_cols <= 0 or cols % scale_cols != 0:
            raise ValueError(
                "Engram FP8 scale shape does not match the weight: "
                f"weight={tuple(quant_weight.shape)}, scale={tuple(scale.shape)}, "
                "expected one scale row per embedding row and an integral "
                "number of values per scale"
            )
        block_size = cols // scale_cols

        shard_rows = self.input_size_per_partition
        shard_start = self.engram_tp_rank * shard_rows
        shard_end = min(shard_start + shard_rows, rows)
        if tuple(param.shape) != (shard_rows, cols):
            raise RuntimeError(
                "Engram local embedding shape mismatch: "
                f"parameter={tuple(param.shape)}, expected={(shard_rows, cols)}"
            )

        if self.engram_offload:
            if scale.dtype != torch.float8_e8m0fnu:
                raise TypeError(
                    "Engram MXFP8 offload requires an E8M0 scale table, "
                    f"got dtype={scale.dtype}"
                )
            mxfp8_shard = torch.zeros(
                self.input_size_per_partition, cols, dtype=quant_weight.dtype
            )
            if shard_start < shard_end:
                mxfp8_shard[:shard_end - shard_start].copy_(
                    quant_weight[shard_start:shard_end]
                )
            self._mxfp8_shard = mxfp8_shard
            padded_rows = self.input_size_per_partition * self.engram_tp_size
            sf_full = torch.full((padded_rows, scale_cols), 127, dtype=torch.uint8)
            sf_full[:scale_rows].copy_(scale.view(torch.uint8))
            self._mxfp8_sf = sf_full.view(torch.float8_e8m0fnu)
            self._mxfp8_block_size = block_size
            return

        param.data.zero_()
        if shard_start < shard_end:
            local_scale = scale[shard_start:shard_end].to(
                device=quant_weight.device, dtype=torch.float32
            )
            dequant_weight = (
                quant_weight[shard_start:shard_end].to(torch.float32)
                .unflatten(-1, (-1, block_size))
                * local_scale.unsqueeze(-1)
            ).flatten(-2).to(torch.bfloat16)
            param.data[:shard_end - shard_start].copy_(dequant_weight)
```

### Host 写入：offload_weights

选择 MXFP8 暂存或 BF16 参数，按实际 storage dtype 查询容量并创建 ElasticBuffer，调用 engram_write。MXFP8 的 sf 在 NPU 上；写入后清除暂存成员并删除原 weight。该函数只表明调用和引用变化，不证明外部存储与 allocator 在某时刻完成物理回收。

```python
    def offload_weights(self):
        """Move the loaded local embedding shard into host storage."""
        from cann_ops_transformer.ops import ElasticBuffer

        if not self.engram_offload:
            raise RuntimeError("offload_weight_loader is only valid in offload mode")
        if self._engram_offloaded:
            return
        if self._mxfp8_shard is not None:
            storage = self._mxfp8_shard
            sf = (
                self._mxfp8_sf.view(torch.uint8)
                .to(torch.device("npu", torch.npu.current_device()))
                .view(torch.float8_e8m0fnu)
            )
        elif self.weight.dtype == torch.bfloat16:
            storage, sf = self.weight, None
        else:
            raise TypeError(
                "ElasticBuffer only accepts BF16 or MXFP8 Engram embeddings, "
                f"but the loaded shard has dtype={self.weight.dtype}"
            )
        num_cpu_bytes = ElasticBuffer.get_engram_storage_size_hint(
            self.input_size_per_partition, self.embedding_dim, storage.dtype
        )
        self.engram_buffer = ElasticBuffer(
            self.engram_tp_group,
            num_cpu_bytes=num_cpu_bytes,
            explicitly_destroy=True,
        )
        # Safetensors are yielded from CPU. ElasticBuffer's device-side write
        # API consumes an NPU tensor, so keep this transfer temporary and do
        # not retain a second copy as a module member.
        self.engram_buffer.engram_write(storage, sf=sf)
        if self._mxfp8_shard is not None:
            self._mxfp8_shard = None
            self._mxfp8_sf = None
        del self.weight
        self._engram_offloaded = True
```

### 查询：MultiHeadEmbedding.forward

输入 hash 行号，返回 embedding。长函数先包含 non-offload 的跨 DP gather，再进入 offload 分支；阅读时先找 self.engram_offload：

| 分支 | 中间量 | 输出及完成边界 |
|---|---|---|
| Host fetch | wait_callable、fetched、fetched_sf | 调 wait 后重建 scale、按块相乘、转 BF16 并恢复形状 |
| 单 rank non-offload | super().forward | 直接局部查表 |
| 多 rank non-offload | local_input_ids、owned、output | 屏蔽非本地行，再 all_reduce 或 reduce_scatter |

后两个分支为原样上下文，不代表 Host 路径也通过这些 collective 完成。

```python
    def forward(
        self, input_ids: torch.Tensor, is_prefill: bool = False
    ) -> torch.Tensor:
        input_shape = input_ids.shape
        num_heads = input_shape[-1]
        flat_input_ids = input_ids.reshape(-1, num_heads)

        # In DSV4, attention workers may hold different request batches. When
        # the Engram TP group spans more DP replicas than the attention group,
        # gather their hash IDs first, just like calc_input_embeddings().
        allgather_ratio = 1
        local_tokens = flat_input_ids.shape[0]
        if (
            not self.engram_offload
            and self.engram_tp_group is not None
            and self.attn_dp_size > self.engram_dp_size
        ):
            allgather_ratio = self.engram_tp_size
            if is_prefill:
                max_tokens = torch.tensor(
                    [local_tokens], dtype=torch.long, device=flat_input_ids.device
                )
                dist.all_reduce(
                    max_tokens, op=dist.ReduceOp.MAX, group=self.engram_tp_group
                )
                max_tokens = int(max_tokens.item())
                gather_input = F.pad(
                    flat_input_ids, (0, 0, 0, max_tokens - local_tokens), value=0
                )
            else:
                max_tokens = local_tokens
                gather_input = flat_input_ids
            gathered = flat_input_ids.new_empty(max_tokens * allgather_ratio, num_heads)
            dist.all_gather_into_tensor(
                gathered, gather_input, group=self.engram_tp_group
            )
            flat_input_ids = gathered

        if self.engram_offload:
            shape = flat_input_ids.shape
            wait_callable = self.engram_buffer.engram_fetch(
                flat_input_ids.reshape(-1).to(torch.int32)
            )
            output = wait_callable()
            if isinstance(output, tuple):
                fetched, fetched_sf = output
                sf = (
                    (fetched_sf.view(torch.uint8).to(torch.int32) << 23)
                    .view(torch.float32)
                )
                output = (
                    fetched.to(torch.float32)
                    .unflatten(-1, (-1, self._mxfp8_block_size))
                    * sf.unsqueeze(-1)
                ).flatten(-2).to(torch.bfloat16)
            return output.view(*shape, self.embedding_dim)
        if self.engram_tp_group is None or self.engram_tp_size == 1:
            return (
                super()
                .forward(flat_input_ids)
                .view(*flat_input_ids.shape, self.embedding_dim)
            )

        # engram_tp_size > 1 and enable_engram_offload = False
        shard_start = self.engram_tp_rank * self.engram_vocab_size_per_rank
        local_input_ids = flat_input_ids - shard_start
        owned = (local_input_ids >= 0) & (
            local_input_ids < self.engram_vocab_size_per_rank
        )
        local_input_ids = local_input_ids.masked_fill(~owned, 0)
        output = super().forward(local_input_ids)
        output = output * owned.unsqueeze(-1).to(output.dtype)
        if self.attn_dp_size <= self.engram_dp_size:
            dist.all_reduce(output, group=self.engram_tp_group)
        else:
            reduced = output.new_empty(max_tokens, output.shape[-2], output.shape[-1])
            dist.reduce_scatter_tensor(reduced, output, group=self.engram_tp_group)
            output = reduced[:local_tokens] if is_prefill else reduced
        return output.view(*output.shape[:-1], self.embedding_dim)
```

### Host 非冗余配置门禁

这是配置检查片段，约束 Engram TP 与 world/device 数的关系，以符合当前 Host 存储部署选择；它不证明外部通信链已可用，也不是其他框架普遍采用的分组规则。

```python
        engram_tp_size = int(custom_params.get("engram_tp_size", 1))
        enable_engram_offload = custom_params.get("enable_engram_offload", False)
        world_size = parallel_config.world_size
        if engram_tp_size <= 0 or world_size % engram_tp_size != 0:
            raise ValueError(
                f"engram_tp_size={engram_tp_size} must be positive and divide world_size={world_size}"
            )
        if engram_tp_size > world_size:
            raise ValueError(
                f"engram_tp_size={engram_tp_size} can not be greater than world_size={world_size}"
            )
        if enable_engram_offload and world_size > 1:
            device_count = torch.npu.device_count()
            if world_size <= device_count and engram_tp_size < world_size:
                raise ValueError(
                    f"Got engram_tp_size={engram_tp_size}, "
                    f"world_size={world_size}, device_count={device_count}; "
                    "set engram_tp_size=world_size to keep host storage "
                    "non-redundant."
                )
            if world_size > device_count and engram_tp_size < device_count:
                raise ValueError(
                    f"Got engram_tp_size={engram_tp_size}, "
                    f"world_size={world_size}, device_count={device_count}; "
                    "set engram_tp_size to at least device_count so host "
                    "storage remains non-redundant."
                )
```

</details>

## 设计决策

可迁移决策是保持查询行、量化值、scale 与完成条件一致。本文 recipes 接口把量化值留在 Host、全表 scale 保留在 device，使 fetch 可按全局行号返回对应值与 scale。保持字节编码和数值计算两种视图各司其职，并在本文接口中以 wait_callable 为消费前的完成边界；其他后端按自己的完成合同等待。外部框架可采用不同驻留或分片方式，但必须维持行号、scale 与完成条件的一致性。

## 验证信号

- [来源平台：950（仅源码目标，未上板）；证据等级：artifact_verified，静态源码] MXFP8 offload loader 要求 E8M0 scale，暂存本地量化 shard 与 padded 全表 scale。
- [来源平台：950（仅源码目标，未上板）；证据等级：artifact_verified，静态源码] forward 调用 wait_callable 后才重建 scale，按块反量化到 BF16；模块删除原 weight 并清空暂存成员。

没有实际 write/fetch 精度、内存峰值或通信通过结果。保持 draft，未生成 verified 事件。

## 部署验收

待执行：对照 BF16 与 MXFP8 的 write/fetch、首尾有效行、多块 scale 和跨 rank 查询；保存 wait 的实际完成关系；测 Host/device 与临时转换峰值，并另验重入和销毁流程。

## 坏实践

用局部 scale 配全局 hash、把原始 exponent 编码做数值 cast 后当同一编码、在 wait 前读输出，或凭引用删除/empty_cache 判断实际内存下降，均不足以满足本合同。

## 失效边界

ElasticBuffer、URMA/UB 环境与确切版本未知。E8M0 特殊编码和非有限值未测；padding 行不能作为真实 hash 返回。本加载约定假定来源为 CPU 量化表，其他设备来源需另验。
