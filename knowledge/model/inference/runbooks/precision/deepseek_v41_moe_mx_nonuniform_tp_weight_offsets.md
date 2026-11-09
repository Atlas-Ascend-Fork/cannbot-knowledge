---
type: Runbook
title: 非均匀TP权重加载：用累计偏移对应逻辑通道
description: 可迁移机制：非均匀分片用前缀和确定逻辑区间，再按权重与scale的实际存储轴换算；128对齐仅为本文MX实现条件。
tags:
- task.debugging
- topic.mixture_of_experts
- topic.compute.quantization
status: draft
sources: []
created_at: '2026-11-02T08:24:24Z'
updated_at: '2026-11-03T01:38:52Z'
platforms:
- '950'
aliases:
- DeepSeek V4.1 MX 非均匀 TP 按累计偏移加载权重
---

# 非均匀TP权重加载：用累计偏移对应逻辑通道

## 适用性与框架边界

本卡以**非均匀分片的逻辑覆盖与物理坐标**为主线。只要每 rank 的宽度不同，就不能用 rank×本 rank 宽度推导起点；checkpoint 名字和 loader 类名不影响这个结论。

| 层次 | 读用范围 |
|---|---|
| 通用原则 | 先用各分片宽度的前缀和确定逻辑通道区间，再分别换算权重、打包值和 scale 的存储坐标。 |
| 成立前提 | 分片宽度、参数轴及编码已知；文中 O_r×S//I 换算还要求物理轴按该逻辑轴线性缩放且分界可表示，不能把向下取整当作自动对齐。 |
| recipes 专属 | 128 通道对齐、MX/SwiGLU 条件、low_latency_tp 门禁、内部 tp_size=1 与 shard_offset/shard_full_size 是本文加载方案；其他后端未必使用它们。 |
| vLLM / 其他框架入口 | 从模型权重加载、专家 TP 分片规划、量化参数创建与 post-load 格式转换追踪同一逻辑区间；检查自己的参数轴和打包信息。 |

vLLM/其他引擎的非均匀 TP 支持与运行均未在本轮验证；本文不提供同名配置或 loader 字段映射。

## 适用场景

一个 MoE routed expert 接收分给自己的 token，通过 Gate/Up 投影得到两组中间通道，经 SwiGLU 相乘合成激活，再用 Down 投影回隐藏维度。shared expert 对所有 token 做同类前馈计算。TP（张量并行）把每个专家的中间通道分给多个 rank，各 rank（通信组中的计算进程）的输出部分和最后相加；EP（专家并行）则把不同专家分给不同 rank。本卡讨论 TP 的通道切片及其加载坐标，不能用 EP 的专家编号代替通道偏移。

可迁移任务是审查非均匀 TP 的区间覆盖及权重/scale 对应，不要求目标引擎使用本文加载器。以下成立条件专属于 DeepSeek V4.1 的 recipes MX routed/shared 专家加载：当前分配以 128 个逻辑通道为一个对齐单元：TP>1、量化模式含 mxfloat、总中间维度按此单元对齐而均分后的局部宽度不对齐时，启用非均匀分片。整模型 low_latency_tp 仍要求总中间维度能整除 TP，并要求各 rank 的输入和路由一致；分片函数能给出列表，不代表任意配置都能启动。路线为 recommended_fastpath 的实现契约核查；128 对齐与整模型限制仅适用于这一加载方案。

目标平台 950 来自模型支持说明。本轮仅核验固定源码与历史 before/after，未运行 CPU/NPU、编译、精度或性能测试；CANN 与外部包版本未知。

## 现象

平均切分可能让局部中间宽度不满足 MX 与 SwiGLU 对齐。改为非均匀宽度后，如果 loader 仍用“rank×本 rank 宽度”找 checkpoint 起点，就可能加载到相邻 rank 的区间。目标张量 shape 仍可能完全匹配，所以单独检查 copy 成功不能排除错误。本轮没有实际加载错误或修后通过的运行日志。

## 根因与判别方法

先检查逻辑覆盖，再给每个参数标注“当前阶段、分片轴、单位”。下表是 recipes 实例：权重与 scale 的 shape 仅描述 create_weights 分配阶段，不是 post-load 转置/NZ 后视图或 kernel 实参。MX 权重包含低精度值与按通道块存储的 scale；同一段逻辑通道在权重、打包字节和 scale 上未必占同样长度。先确定逻辑区间，再依据该参数实际存储轴换算，才能让 Gate、Up、Down 和 scale 对齐。

| 符号或张量 | 轴、单位与来源 | 消费者 |
|---|---|---|
| I、H、P、r | 全局中间通道数、隐藏通道数、TP 数与 rank 编号 | 初始化和 loader |
| I_r、O_r | 本 rank 通道数、之前所有 rank 通道数之和；单位均为逻辑通道 | 参数分配、物理切片换算 |
| E_local | 本 rank 存储的专家数；EP 决定专家归属 | routed 参数第一轴 |
| w13_weight | 本卡 FP4 分配为 [E_local,2I_r,H/2] 的 uint8 存储；最后一轴每字节两权重值 | GMM1 |
| w2_weight | [E_local,H,I_r/2] 的 uint8 存储 | GMM2 |
| w13_weight_scale | [E_local,2I_r,ceil(H/BLOCK_K)]；最后轴按输入通道块 | GMM1 反量化 |
| w2_weight_scale | [E_local,H,ceil(I_r/BLOCK_K)]；最后轴按中间通道块 | GMM2 反量化 |
| loaded_weight、S | 从 checkpoint 读出的某参数及其实际分片轴长度；单位为该存储轴元素 | 各 loader 的 narrow |
| shard_offset / shard_full_size | O_r / I；通用 Linear 的显式逻辑坐标元数据 | shared loader |

本文实例按整对齐单元分配；其他后端可采用自己的合法宽度列表，前缀和原则相同。令 I=A×U，A 为对齐单元。先把 U 个单元分给 P 个 rank：base=floor(U/P)，rem=U mod P，前 rem 个 rank 多一个单元。O_r=sum(I_j, j<r)，不是 r×I_r。沿实际存储长度 S 的起点是 O_r×S//I；分片大小来自目标参数在同一物理轴的长度。Gate 和 Up 各取同一逻辑区间并放入 w13 的对应半区，Down 沿输入轴取该区间。

教学推演（非上板观测）：取 U=10、P=4，宽度为 3A、3A、2A、2A，正确起点为 0、3A、6A、8A。rank 2 若使用 2×2A，会从 4A 开始，与 rank 1 的区间重叠。若所有 rank 都使用 r×I_r，最后一个 rank 也会错从 6A 开始，全局尾部 [8A,10A) 因而遗漏。若某参数的物理轴每两个逻辑值占一项，正确 rank 2 起点为 3A；scale 若每 B 个通道占一项，则起点为 6A/B（在该轴确实整除且采用此编码时）。数值不同但必须指向同一段逻辑通道。只把同一个整数偏移复制给权重和 scale 会错。

## 诊断路径

1. 找到自己的专家分片规划器、参数创建器、checkpoint loader 与最终 TP 求和。记录每 rank 的全局 I、本地 I_r、逻辑 O_r、TP/EP 组和专家编号映射。宽度和必须为 I，逻辑区间应连续且互不重叠。
2. 为 Gate、Up、Down、对应 scale 分别记录源/目标 shape、分片轴、转置标志、pack_factor、scale 分组大小及物理 start/length。把每段物理区间反推为逻辑通道，确认四类数据对应同一个 [O_r,O_r+I_r)。
3. 若 shape 相同但内容不对应，优先追查旧的 rank×local_size 公式；若只在 shared 出错，核对是否既传本地宽度又让通用 Linear 再按 TP 均分；若只在 scale 出错，追查它实际分片的是通道轴还是块轴。
4. 修正分片规划与 loader 元数据后，先逐参数核对 checkpoint 切片内容或重建后的通道覆盖，再用相同输入比较各阶段和最终求和输出。保存不同宽度分界 rank 的记录；尚未完成此验证前可退回已验收的均匀对齐配置，不能把补 padding 当作通用替代。

<details>
<summary>recipes / CANN Executor 完整实现对照（可选阅读）</summary>

## 快速检查

有 recipes 源码时，可选搜索下列符号；其他框架按上述职责定位，不要求类名相同。

```bash
rg -n 'TP_INTERMEDIATE_ALIGN|intermediate_offset|shard_offset|shard_full_size|_intermediate_shard_offset' module/fuse_moe_gmm.py module/linear.py models/deepseek_v4_1/models/modeling_deepseek.py
```

## 系统信息

以下函数依赖各量化方法为参数设置的分片轴、转置和打包属性，以及模型初始化和通信组。历史 before 仅用于比较机制；未与运行失败/恢复形成实测修复链。代码依赖 PyTorch、torch_npu 与所属模块，不能单独视为完整模型程序。

## 机制代码

### 历史 before：FusedMoEGMM.__init__

输入全局专家数、H、I 和 TP/EP 配置；原实现只给每 rank 分配 I//P。experts_per_rank 切专家轴，intermediate_size_per_partition 切通道轴，两者是不同并行维度。量化方法用局部宽度创建后续 loader 的目标参数。

```python
    def __init__(
        self,
        num_experts: int,
        hidden_size: int,
        intermediate_size: int,
        bias: bool = True,
        tp_size: int = 1,
        tp_rank: int = 0,
        ep_size: int = 1,
        ep_rank: int = 0,
        gather_output: bool = False,
        skip_bias_add: bool = False,
        params_dtype: Optional[torch.dtype] = None,
        quant_config: Optional = None,
        prefix: str = "",
    ):
        super().__init__()
        self.tp_size = tp_size
        self.tp_rank = tp_rank
        self.ep_size = ep_size
        self.ep_rank = ep_rank
        self.experts_per_rank = num_experts // ep_size
        self.intermediate_size_per_partition = intermediate_size // self.tp_size
        if quant_config is None:
            self.quant_method: Optional[QuantizeMethodBase] = (
                UnquantizedFusedMoEGMMMethod())
        else:
            self.quant_method = quant_config.get_quant_method(self, prefix)

        self.quant_method.create_weights(
            layer=self,
            num_experts=self.experts_per_rank,
            hidden_size=hidden_size,
            intermediate_size_per_partition=self.intermediate_size_per_partition,
            params_dtype=params_dtype,
            weight_loader=self.weight_loader)
        self.gmm1_events = None
```

### 当前 after：FusedMoEGMM.__init__

输入接口不变；新增全局 intermediate_size、非均匀开关和 intermediate_offset。split_sizes 决定每 rank 的真实宽度；create_weights 消费该宽度。min(split_sizes)==0 仅发 warning，不能据此判定下游支持空 shard。

```python
    def __init__(
        self,
        num_experts: int,
        hidden_size: int,
        intermediate_size: int,
        bias: bool = True,
        tp_size: int = 1,
        tp_rank: int = 0,
        ep_size: int = 1,
        ep_rank: int = 0,
        gather_output: bool = False,
        skip_bias_add: bool = False,
        params_dtype: Optional[torch.dtype] = None,
        quant_config: Optional = None,
        prefix: str = "",
    ):
        super().__init__()
        self.tp_size = tp_size
        self.tp_rank = tp_rank
        self.ep_size = ep_size
        self.ep_rank = ep_rank
        self.experts_per_rank = num_experts // ep_size
        self.intermediate_size = intermediate_size
        gmm_quant_mode = getattr(quant_config, "gmm_quant_mode", None) if quant_config is not None else None
        self.enable_nonuniform_tp_split = (
            tp_size > 1
            and gmm_quant_mode is not None
            and "mxfloat" in gmm_quant_mode
            and intermediate_size % self.TP_INTERMEDIATE_ALIGN == 0
            and (intermediate_size // tp_size) % self.TP_INTERMEDIATE_ALIGN != 0)
        if self.enable_nonuniform_tp_split:
            split_sizes = self.split_intermediate_aligned(
                intermediate_size, tp_size, self.TP_INTERMEDIATE_ALIGN)
            if min(split_sizes) == 0:
                import warnings
                warnings.warn(
                    f"intermediate_size={intermediate_size} cannot fill tp_size={tp_size} "
                    f"ranks at {self.TP_INTERMEDIATE_ALIGN}-alignment: "
                    f"{intermediate_size // self.TP_INTERMEDIATE_ALIGN} ranks get a non-empty "
                    f"shard and the rest an empty one; reduce tp_size.")
            self.intermediate_size_per_partition = split_sizes[tp_rank]
            self.intermediate_offset = sum(split_sizes[:tp_rank])
        else:
            self.intermediate_size_per_partition = intermediate_size // self.tp_size
            self.intermediate_offset = (intermediate_size // self.tp_size) * tp_rank
        if quant_config is None:
            self.quant_method: Optional[QuantizeMethodBase] = (
                UnquantizedFusedMoEGMMMethod())
        else:
            self.quant_method = quant_config.get_quant_method(self, prefix)

        self.quant_method.create_weights(
            layer=self,
            num_experts=self.experts_per_rank,
            hidden_size=hidden_size,
            intermediate_size_per_partition=self.intermediate_size_per_partition,
            params_dtype=params_dtype,
            weight_loader=self.weight_loader)
        self.gmm1_events = None
```

### 分配单元：split_intermediate_aligned

输入总宽度、rank 数和对齐单位；输出按 rank 排列的逻辑宽度列表。分配的是整单元，不修改模型总宽度。

```python
    @staticmethod
    def split_intermediate_aligned(total: int, parts: int, align: int) -> list[int]:
        units = total // align
        base, rem = divmod(units, parts)
        return [(base + 1) * align if r < rem else base * align for r in range(parts)]
```

### 坐标换算：_intermediate_shard_offset

输入某一个 checkpoint 张量及其分片轴；输出该张量存储坐标中的起点。loaded_weight.shape[shard_dim] 是每个参数自己的 S，所以权重与 scale 可以得到不同物理起点。

```python
    def _intermediate_shard_offset(self, loaded_weight: torch.Tensor, shard_dim: int) -> int:
        return self.intermediate_offset * loaded_weight.shape[shard_dim] // self.intermediate_size
```

### routed Gate/Up：_load_w13

expert_data 是一个专家的融合目标参数；shard_size 是其中一个半区的物理长度。loaded_weight 是尚未 TP 切片的 Gate 或 Up，先按逻辑前缀和截取，再按 shard_id 写入 w13 前/后半区。两次调用应使用同一逻辑起点。

```python
    def _load_w13(self, expert_data: torch.Tensor, shard_dim: int,
                  shard_id: str, loaded_weight: torch.Tensor, tp_rank: int):

        # Index the loaded weight for tp sharding.
        # gate_up_proj: "MergedColumnParallel", so tp sharding on output_dim
        shard_size = expert_data.shape[shard_dim] // 2
        if self.enable_nonuniform_tp_split:
            shard_offset = self._intermediate_shard_offset(loaded_weight, shard_dim)
        else:
            shard_offset = shard_size * tp_rank
        loaded_weight = loaded_weight.narrow(shard_dim, shard_offset,
                                             shard_size)
        # Narrow parameter and load.
        # w1, gate_proj: Load into first logical weight of w13.
        if shard_id == "w1":
            expert_data = expert_data.narrow(shard_dim, 0, shard_size)
        # w3, up_proj: Load into second logical weight of w13.
        else:
            if shard_id != "w3":
                raise ValueError("only support shard_id in [\"w1\", \"w3\"] when load w13")
            expert_data = expert_data.narrow(shard_dim, shard_size, shard_size)
        expert_data.copy_(loaded_weight)
```

### routed Down：_load_w2

与上段使用相同逻辑通道区间，但沿 Down 输入轴切片。load_full 是已有特殊加载路径的开关，不等于非均匀分片已验证可省略；最终 copy 要求源/目标一致。

```python
    def _load_w2(self,
                 expert_data: torch.Tensor,
                 shard_dim: int,
                 loaded_weight: torch.Tensor,
                 tp_rank: int,
                 load_full: bool = False):

        # Index the loaded weight for tp sharding.
        # down_proj: "RowParallel" so tp sharding on input_dim
        # Narrow parameter and load.
        shard_size = expert_data.shape[shard_dim]
        if not load_full:
            if self.enable_nonuniform_tp_split:
                shard_offset = self._intermediate_shard_offset(loaded_weight, shard_dim)
            else:
                shard_offset = shard_size * tp_rank
            loaded_weight = loaded_weight.narrow(shard_dim,
                                                 shard_offset,
                                                 shard_size)
        # w2, down_proj: Load into only logical weight of w2.
        expert_data.copy_(loaded_weight)
```

### shared 的入口：DeepseekV41SharedExpert.__init__

shared 计算与 routed 共用对齐规划，但通过通用 Linear 加载。非均匀时本函数先算真实局部宽度，令两个 Linear 的内部 tp_size=1，并传 O_r/I 元数据，避免通用层再次切分。

| 中间变量 | 含义及去向 |
|---|---|
| gu_output_sizes | Gate 与 Up 的两段输出通道数 → MergedColumnParallelLinear |
| dp_input_size | Down 的输入通道数 → RowParallelLinear |
| gu_tp_size / dp_tp_size | 非均匀时为 1，仅表示通用层不再自行均分 |
| shard_kwargs | 全局逻辑宽度和前缀和 → 两种 loader |

```python
    def __init__(
        self,
        config,
        infer_config: InferenceConfig,
        comm_manager: CommManager = None,
        is_moe_layer=False,
        prefix="",
        **kwargs,
    ):
        super().__init__()
        self.infer_config = infer_config
        self.comm_manager = comm_manager
        self.mm_quant_mode = (
            config.quant_config.mm_quant_mode
            if config.quant_config is not None
            else "w16a16")
        self.swiglu_limit = config.swiglu_limit if hasattr(config, "swiglu_limit") else None
        self.moe_tp_size = self.infer_config.parallel_config.moe_tp_size
        self.moe_ep_size = self.infer_config.parallel_config.moe_ep_size
        self.low_latency_tp = bool(
            self.infer_config.model_config.custom_params.get("low_latency_tp", False)
        )
        self.config = config
        self.hidden_size = config.hidden_size
        self.is_moe_layer = is_moe_layer
        self.tp_rank = self.comm_manager.get_rank("moe_tp_group") if self.moe_tp_size > 1 else 0
        from module.fuse_moe_gmm import FusedMoEGMM
        self.intermediate_size = config.moe_intermediate_size * config.n_shared_experts
        self.enable_nonuniform_tp_split = (
            self.moe_tp_size > 1
            and "mxfloat" in self.mm_quant_mode
            and self.intermediate_size % FusedMoEGMM.TP_INTERMEDIATE_ALIGN == 0
            and (self.intermediate_size // self.moe_tp_size) % FusedMoEGMM.TP_INTERMEDIATE_ALIGN != 0)
        if self.enable_nonuniform_tp_split:
            split_sizes = FusedMoEGMM.split_intermediate_aligned(
                self.intermediate_size, self.moe_tp_size, FusedMoEGMM.TP_INTERMEDIATE_ALIGN)
            self.intermediate_size_per_partition = split_sizes[self.tp_rank]
            self.intermediate_offset = sum(split_sizes[:self.tp_rank])
        else:
            self.intermediate_size_per_partition = self.intermediate_size // self.moe_tp_size
            self.intermediate_offset = (self.intermediate_size // self.moe_tp_size) * self.tp_rank
        if self.enable_nonuniform_tp_split:
            gu_tp_size, gu_tp_rank = 1, 0
            dp_tp_size, dp_tp_rank = 1, 0
            gu_output_sizes = [self.intermediate_size_per_partition] * 2
            dp_input_size = self.intermediate_size_per_partition
            shard_kwargs = dict(
                shard_full_size=self.intermediate_size,
                shard_offset=self.intermediate_offset)
        else:
            # Uniform: original behavior, let the generic Linear shard itself.
            gu_tp_size, gu_tp_rank = self.moe_tp_size, self.tp_rank
            dp_tp_size, dp_tp_rank = self.moe_tp_size, self.tp_rank
            gu_output_sizes = [self.intermediate_size] * 2
            dp_input_size = self.intermediate_size
            shard_kwargs = {}
        self.gate_up_proj = MergedColumnParallelLinear(
            input_size=self.hidden_size,
            output_sizes=gu_output_sizes,
            bias=False,
            tp_size=gu_tp_size,
            tp_rank=gu_tp_rank,
            quant_config=config.quant_config,
            prefix=f"{prefix}.gate_up_proj",
            **shard_kwargs,
            )
        self.down_proj = RowParallelLinear(
            dp_input_size,
            config.hidden_size,
            bias=False,
            tp_size=dp_tp_size,
            tp_rank=dp_tp_rank,
            quant_config=config.quant_config,
            prefix=f"{prefix}.down_proj",
            **shard_kwargs,
            )
        if "float8" in self.mm_quant_mode and "a8" in self.mm_quant_mode:
            self.forward = self.forward_a8float8
        else:
            self.forward = self.forward_normal
```

### shared Gate/Up 参数创建：MergedColumnParallelLinear.__init__

input_size 为 H，output_sizes 是 Gate/Up 两段。构造器保存显式 shard 元数据并创建参数；内部 output_partition_sizes 是目标参数布局，不应误当 checkpoint 的全局长度。

```python
    def __init__(self,
                 input_size: int,
                 output_sizes: List[int],
                 bias: bool = False,
                 skip_bias_add: bool = False,
                 tp_size: int = 1,
                 tp_rank: int = 0,
                 params_dtype: Optional[torch.dtype] = None,
                 quant_config: Optional = None,
                 prefix: str = "",
                 return_bias: bool = False,
                 shard_full_size: Optional[int] = None,
                 shard_offset: Optional[int] = None,
                 ):
        self.output_sizes = output_sizes
        self.tp_size = tp_size
        if not all(output_size % tp_size == 0 for output_size in output_sizes):
            raise RuntimeError("All output_sizes must be divisible by tp_size")
        self.tp_rank = tp_rank
        # Non-uniform TP: per-rank checkpoint offset in the weight_loader
        # (replaces tp_rank * shard_size).
        self.shard_full_size = shard_full_size
        self.shard_offset = shard_offset
        self.quant_config = quant_config
        output_size = sum(output_sizes)
        super().__init__(input_size,
                         output_size,
                         skip_bias_add,
                         params_dtype,
                         quant_config,
                         prefix,
                         return_bias=return_bias,
                         )
        if self.quant_method is None:
            raise RuntimeError("self.quant_method must not be None")
        # Divide the weight matrix along the last dimension.
        self.output_size_per_partition = divide(self.output_size, tp_size)
        self.output_partition_sizes = [self.output_size_per_partition]
        # If QKV or MergedColumn, use output size of each partition.
        if hasattr(self, "output_sizes"):
            self.output_partition_sizes = [
                divide(output_size, self.tp_size)
                for output_size in self.output_sizes
            ]
        output_sizes = [output_size]

        self.quant_method.create_weights(
            layer=self,
            input_size_per_partition=self.input_size,
            output_partition_sizes=self.output_partition_sizes,
            input_size=self.input_size,
            output_size=self.output_size,
            params_dtype=self.params_dtype,
            weight_loader=self.weight_loader)
        if bias:
            self.bias = Parameter(
                torch.empty(self.output_size_per_partition,
                            dtype=params_dtype))
            set_weight_attrs(self.bias, {
                "output_dim": 0,
                "weight_loader": self.weight_loader,
            })
        else:
            self.register_parameter("bias", None)
        self.throw_dequant = True
```

### shared Gate/Up 加载：MergedColumnParallelLinear.weight_loader

函数支持融合文件和按单段加载；先定位 Gate/Up 在目标参数中的半区，再确定源张量的 TP 起点。

| 分支或变量 | 作用 |
|---|---|
| loaded_shard_id=None | 将磁盘融合权重拆成逻辑分段，递归进入单段加载 |
| output_dim、packed_dim、pack_factor | 确定输出轴及打包后长度/偏移单位 |
| param_data.narrow | 选目标参数的 Gate/Up 半区 |
| self.shard_offset 与 shard_full_size | 在源张量上把逻辑 O_r 换算为物理 start_idx |
| shape 检查与 copy | 验证可复制性；不证明逻辑区间选对 |

bitsandbytes 与 per-block 特殊分支仍保留在完整函数中，本卡不扩张为它们的非均匀兼容保证。

```python
    def weight_loader(self,
                      param: Parameter,
                      loaded_weight: torch.Tensor,
                      loaded_shard_id: Optional[int] = None):

        param_data = param.data
        output_dim = getattr(param, "output_dim", None)
        is_per_block_scale = getattr(param, "is_per_block_scale", False)
        # Special case for per-tensor scale to load scalar into fused array.
        needs_scalar_to_array = getattr(param, "needs_scalar_to_array", False)

        if loaded_shard_id is None:
            # Loaded weight is already fused on disk (qkv/mlp).
            if output_dim is None:
                if param_data.shape != loaded_weight.shape:
                    raise RuntimeError("param_data.shape != loaded_weight.shape")
                param_data.copy_(loaded_weight)
                return
            current_shard_offset = 0
            shard_offsets: List[Tuple[int, int, int]] = []
            for i, output_size in enumerate(self.output_sizes):
                shard_offsets.append((i, current_shard_offset, output_size))
                current_shard_offset += output_size
            packed_dim = getattr(param, "packed_dim", None)
            for shard_id, shard_offset, shard_size in shard_offsets:
                # Special case for Quantization.
                # If quantized, we need to adjust the offset and size to account
                # for the packing.
                if packed_dim == output_dim:
                    shard_size = shard_size // param.pack_factor
                    shard_offset = shard_offset // param.pack_factor

                loaded_weight_shard = loaded_weight.narrow(
                    output_dim, shard_offset, shard_size)
                self.weight_loader(param, loaded_weight_shard, shard_id)
            return

        if loaded_shard_id >= len(self.output_sizes):
            raise RuntimeError("loaded_shard_id must be less than the length of self.output_sizes")
        if output_dim is not None:
            if is_per_block_scale:
                block_size = self.weight_block_size[0]
                shard_offset = math.ceil(sum(self.output_sizes[:loaded_shard_id]) / block_size) // self.tp_size
                shard_size = math.ceil(self.output_sizes[loaded_shard_id] / block_size) // self.tp_size
            else:
                shard_offset = sum(self.output_sizes[:loaded_shard_id]) // self.tp_size
                shard_size = self.output_sizes[loaded_shard_id] // self.tp_size
            # Special case for quantization.
            # If quantized, we need to adjust the offset and size to account
            # for the packing.
            packed_dim = getattr(param, "packed_dim", None)
            if packed_dim == output_dim:
                shard_size = shard_size // param.pack_factor
                shard_offset = shard_offset // param.pack_factor

            use_bitsandbytes_4bit = getattr(param, "use_bitsandbytes_4bit",
                                            False)
            if use_bitsandbytes_4bit:
                shard_size = loaded_weight.shape[output_dim]
                shard_offset = loaded_weight.shape[output_dim] * \
                    loaded_shard_id

            param_data = param_data.narrow(output_dim, shard_offset,
                                           shard_size)
            if self.shard_offset is not None:
                start_idx = (self.shard_offset
                             * loaded_weight.shape[output_dim]
                             // self.shard_full_size)
            else:
                start_idx = self.tp_rank * shard_size
            # bitsandbytes loads the weights of the specific portion
            # no need to narrow here
            if not use_bitsandbytes_4bit:
                loaded_weight = loaded_weight.narrow(output_dim, start_idx,
                                                     shard_size)

        else:
            ignore_warning = getattr(param, "ignore_warning", False)
            if not ignore_warning:
                logger.warning(
                    "Loading a weight without `output_dim` attribute in "
                    "MergedColumnParallelLinear, assume the weight is "
                    "the same for all partitions.")

        if param_data.shape != loaded_weight.shape:
            raise RuntimeError("param_data.shape != loaded_weight.shape")
        param_data.copy_(loaded_weight)
```

### shared Down 参数创建：RowParallelLinear.__init__

input_size 由 shared 构造器传入，input_size_per_partition 决定目标参数的中间轴；输出隐藏维度不在此处切分。显式 shard 元数据仍传递到下面的 loader。

```python
    def __init__(self,
                 input_size: int,
                 output_size: int,
                 bias: bool = False,
                 tp_size: int = 1,
                 tp_rank: int = 0,
                 input_is_parallel: bool = True,
                 skip_bias_add: bool = False,
                 params_dtype: Optional[torch.dtype] = None,
                 quant_config: Optional = None,
                 prefix: str = "",
                 return_bias: bool = False,
                 shard_full_size: Optional[int] = None,
                 shard_offset: Optional[int] = None,
                 ):
        super().__init__(input_size,
                         output_size,
                         skip_bias_add,
                         params_dtype,
                         quant_config,
                         prefix,
                         )

        if self.quant_method is None:
            raise RuntimeError("self.quant_method must not be None")

        self.input_is_parallel = input_is_parallel

        self.tp_size = tp_size
        self.tp_rank = tp_rank
        # Non-uniform TP: see MergedColumnParallelLinear.
        self.shard_full_size = shard_full_size
        self.shard_offset = shard_offset
        # Divide the weight matrix along the last dimension.
        self.input_size_per_partition = divide(input_size, self.tp_size)
        self.output_size_per_partition = output_size
        self.output_partition_sizes = [output_size]

        self.quant_method.create_weights(
            layer=self,
            input_size_per_partition=self.input_size_per_partition,
            output_partition_sizes=self.output_partition_sizes,
            input_size=self.input_size,
            output_size=self.output_size,
            params_dtype=self.params_dtype,
            weight_loader=self.weight_loader)

        if bias:
            self.bias = Parameter(
                torch.empty(self.output_size, dtype=params_dtype))
            set_weight_attrs(self.bias, {
                "output_dim": 0,
                "weight_loader": self.weight_loader,
            })
        else:
            self.register_parameter("bias", None)
```

### shared Down 加载：RowParallelLinear.weight_loader

input_dim 来自参数属性；shard_size 用目标参数物理轴长度，start_idx 用 O_r×S//I。标量 scale 的 reshape 是独立兼容处理，不会修复错误分片坐标。

```python
    def weight_loader(self, param: Parameter, loaded_weight: torch.Tensor):
        input_dim = getattr(param, "input_dim", None)
        use_bitsandbytes_4bit = getattr(param, "use_bitsandbytes_4bit", False)

        param_data = param.data
        # bitsandbytes loads the weights of the specific portion
        # no need to narrow here
        if input_dim is not None and not use_bitsandbytes_4bit:
            shard_size = param_data.shape[input_dim]
            if self.shard_offset is not None:
                start_idx = (self.shard_offset
                             * loaded_weight.shape[input_dim]
                             // self.shard_full_size)
            else:
                start_idx = self.tp_rank * shard_size
            loaded_weight = loaded_weight.narrow(input_dim, start_idx,
                                                 shard_size)

        # Special case for loading scales off disk, which often do not
        # have a shape.
        if len(loaded_weight.shape) == 0:
            loaded_weight = loaded_weight.reshape(1)

        if param_data.shape != loaded_weight.shape:
            raise RuntimeError("param_data.shape != loaded_weight.shape")
        param_data.copy_(loaded_weight)
```

### 当前对齐常量

该值是这份实现的分配单位，不是所有 MX 后端的普遍要求。

```python
class FusedMoEGMM(torch.nn.Module):
    TP_INTERMEDIATE_ALIGN = 128
```

### scale 类型分类

下面的枚举供 routed loader 决定 scale 按张量、通道还是分组/块加载；它不是 scale 的实际数值编码。

```python
class FusedMoeWeightScaleSupported(Enum):
    TENSOR = "tensor"
    CHANNEL = "channel"
    GROUP = "group"
    BLOCK = "block"
```

### routed 总加载入口：FusedMoEGMM.weight_loader

输入目标参数、单个来源权重、权重名、投影名与专家编号；按以下顺序分发到前面的局部 loader。

| 阶段 | 关键变量 | 与分片的关系 |
|---|---|---|
| EP 归属检查 | expert_id、experts_per_rank | EP-only 分支把全局专家号转本地专家号 |
| 分片轴选择 | SHARD_ID_TO_SHARDED_DIM、is_transposed | Gate/Up 切输出轴，Down 切输入轴；转置可能换轴 |
| scale 分发 | weight_name、quant_method | 按实际粒度选择专用 loader |
| 权重分发 | shard_id | 最终进入 w13 或 w2 的通道切片 |

input_scale、g_idx、bias 等既有分支完整保留；本卡没有逐分支验证所有量化组合。

```python
    def weight_loader(self, param: torch.nn.Parameter,
                      loaded_weight: torch.Tensor, weight_name: str,
                      shard_id: str, expert_id: int) -> None:

        if self.ep_size > 1 and self.tp_size == 1:
            if (expert_id < self.ep_rank * self.experts_per_rank
                or expert_id >= (self.ep_rank + 1) * self.experts_per_rank):
                return
            self.tp_rank = 0
            expert_id -= self.ep_rank * self.experts_per_rank


        if shard_id not in ("w1", "w2", "w3"):
            raise ValueError(f"shard_id must be ['w1','w2','w3'] but "
                             f"got {shard_id}.")

        WEIGHT_SCALE_SUPPORTED = [
            e.value for e in FusedMoeWeightScaleSupported
        ]
        # Fetch the dim to shard the parameter/loaded weight
        # based on the shard id. This will be whatever
        # dimension intermediate_size is used.
        SHARD_ID_TO_SHARDED_DIM = {"w1": 0, "w2": 1, "w3": 0}

        expert_data = param.data[expert_id]

        # is_transposed: if the dim to shard the weight
        # should be flipped. Required by GPTQ, compressed-tensors
        # should be whatever dimension intermediate_size is
        is_transposed = getattr(param, "is_transposed", False)
        shard_dim = SHARD_ID_TO_SHARDED_DIM[shard_id]
        if is_transposed:
            shard_dim = ~shard_dim

        # Case input scale: input_scale loading is only supported for fp8
        if "input_scale" in weight_name:
            # this is needed for compressed-tensors only
            loaded_weight = loaded_weight.to(param.data.device)

            if param.data[expert_id] != 1 and (param.data[expert_id] -
                                               loaded_weight).abs() > 1e-5:
                raise ValueError(
                    "input_scales of w1 and w3 of a layer "
                    f"must be equal. But got {param.data[expert_id]} "
                    f"vs. {loaded_weight}")

            self._load_single_value(param=param,
                                    loaded_weight=loaded_weight,
                                    expert_id=expert_id)
            return

        # Case g_idx
        if "g_idx" in weight_name:
            self._load_g_idx(shard_dim=0,
                             shard_id=shard_id,
                             loaded_weight=loaded_weight,
                             expert_data=expert_data,
                             tp_rank=self.tp_rank)
            return

        # Case weight scales and zero_points
        if ("scale" in weight_name or "zero" in weight_name or "offset" in weight_name):
            # load the weight scales and zp based on the quantization scheme
            # supported weight scales/zp can be found in
            # FusedMoeWeightScaleSupported
            quant_method = getattr(param, "quant_method", None)
            if quant_method == FusedMoeWeightScaleSupported.CHANNEL.value:
                self._load_per_channel_weight_scale(
                    shard_id=shard_id,
                    shard_dim=shard_dim,
                    loaded_weight=loaded_weight,
                    expert_data=expert_data,
                    tp_rank=self.tp_rank)
            elif quant_method == FusedMoeWeightScaleSupported.GROUP.value or \
                quant_method == FusedMoeWeightScaleSupported.BLOCK.value:
                self._load_model_weight_or_group_weight_scale(
                    shard_id=shard_id,
                    shard_dim=shard_dim,
                    loaded_weight=loaded_weight,
                    expert_data=expert_data,
                    tp_rank=self.tp_rank)
            elif quant_method == FusedMoeWeightScaleSupported.TENSOR.value:
                self._load_per_tensor_weight_scale(shard_id=shard_id,
                                                   param=param,
                                                   loaded_weight=loaded_weight,
                                                   expert_id=expert_id)
            else:
                raise ValueError(
                    f"quant method must be one of {WEIGHT_SCALE_SUPPORTED}")
            return

        if "bias" in weight_name or "alpha" in weight_name:
            self._load_per_channel_weight_scale(
                shard_id=shard_id,
                shard_dim=shard_dim,
                loaded_weight=loaded_weight,
                expert_data=expert_data,
                tp_rank=self.tp_rank)

        # Case weight_shape
        if "weight_shape" in weight_name:
            # only required by compressed-tensors
            self._load_single_value(param=param,
                                    loaded_weight=loaded_weight,
                                    expert_id=expert_id)
            return

        # Case model weights
        if "weight" in weight_name:
            self._load_model_weight_or_group_weight_scale(
                shard_id=shard_id,
                shard_dim=shard_dim,
                loaded_weight=loaded_weight,
                expert_data=expert_data,
                tp_rank=self.tp_rank)
            return
```

### 权重与块 scale 的共同分发：_load_model_weight_or_group_weight_scale

该函数按 w2 或 w1/w3 分到 _load_w2/_load_w13，让对应权重与块 scale 共用逻辑区间规则；实际物理轴长度仍由各张量决定。

```python
    def _load_model_weight_or_group_weight_scale(self,
                                                 shard_dim: int,
                                                 expert_data: torch.Tensor,
                                                 shard_id: str,
                                                 loaded_weight: torch.Tensor,
                                                 tp_rank: int,
                                                 load_full_w2: bool = False):
        """
        Load grouped weight scales for group quantization or model weights
            :param shard_dim: dimension to shard
            :param expert_data: parameter for a particular expert
            :param shard_id: either w1, w2, or w3
            :param loaded_weight: checkpoint weight to load into the param
            :param tp_rank: tensor parallel rank
            :param load_full_w2: whether or not the w2 loaded should be sharded.
        """
        if shard_id == "w2":
            # In the case where we have actorder/g_idx, we do not partition the
            # w2 scales, as indicated by `load_full` argument, for all tp cases
            self._load_w2(shard_dim=shard_dim,
                          loaded_weight=loaded_weight,
                          expert_data=expert_data,
                          tp_rank=self.tp_rank,
                          load_full=load_full_w2)
        elif shard_id in ("w1", "w3"):
            self._load_w13(shard_id=shard_id,
                           shard_dim=shard_dim,
                           loaded_weight=loaded_weight,
                           expert_data=expert_data,
                           tp_rank=self.tp_rank)
```

### FP4 物理存储：W4A8MxFp4MoEGMMMethod 初始化与 create_weights

输入局部 I_r 和 H，创建权重与 scale。pack_factor=2 作用于 FP4 权重最后一轴；BLOCK_K 控制 scale 块数。两者不能互换。上述符号表对应此函数创建、尚未转置处理的布局。

```python
    def __init__(self):
        super().__init__()
        STORAGE_BITS_NPU = 8
        WEIGHT_BITS = 4
        self.pack_factor = STORAGE_BITS_NPU // WEIGHT_BITS

    def create_weights(
        self,
        layer: torch.nn.Module,
        num_experts: int,
        hidden_size: int,
        intermediate_size_per_partition: int,
        params_dtype: torch.dtype,
        **extra_weight_attrs,
    ) -> None:
        weight_type = torch.uint8
        scale_dtype = torch.uint8

        # Fused gate_up_proj (column parallel)
        w13_weight = torch.nn.Parameter(torch.empty(num_experts,
                                                    2 * intermediate_size_per_partition,
                                                    hidden_size // self.pack_factor,
                                                    dtype=weight_type),
                                        requires_grad=False)
        layer.register_parameter("w13_weight", w13_weight)
        set_weight_attrs(w13_weight, extra_weight_attrs)

        # down_proj (row parallel)
        w2_weight = torch.nn.Parameter(torch.empty(num_experts,
                                                    hidden_size,
                                                    intermediate_size_per_partition // self.pack_factor,
                                                    dtype=weight_type),
                                        requires_grad=False)
        layer.register_parameter("w2_weight", w2_weight)
        set_weight_attrs(w2_weight, extra_weight_attrs)

        extra_weight_attrs.update(
            {"quant_method": FusedMoeWeightScaleSupported.BLOCK.value})

        w13_weight_scale = torch.nn.Parameter(torch.ones(num_experts,
                                                  2 * intermediate_size_per_partition,
                                                  math.ceil(hidden_size / BLOCK_K),
                                                  dtype=scale_dtype),
                                       requires_grad=False)
        layer.register_parameter("w13_weight_scale", w13_weight_scale)
        set_weight_attrs(w13_weight_scale, extra_weight_attrs)

        w2_weight_scale = torch.nn.Parameter(torch.ones(num_experts,
                                                 hidden_size,
                                                 math.ceil(intermediate_size_per_partition / BLOCK_K),
                                                 dtype=scale_dtype),
                                      requires_grad=False)
        layer.register_parameter("w2_weight_scale", w2_weight_scale)
        set_weight_attrs(w2_weight_scale, extra_weight_attrs)
```

### 整模型前置门禁：low_latency_tp

这是加载前的配置片段，并非完整函数。它统一 TP/DP/EP 参数并保留 I 能整除 P、路由一致等限制；必须先通过这些门禁，再谈非均匀分片可用性。

```python
        low_latency_tp = bool(custom_params.get("low_latency_tp", False))
        if low_latency_tp:
            if parallel_config.world_size % 2:
                raise ValueError("low_latency_tp requires an even world_size for MLA/LI rank pairs")
            if exe_mode not in ("eager", "npugraph_ex"):
                raise ValueError("low_latency_tp uses native streams; select eager or npugraph_ex")
            if parallel_config.attn_tp_size <= 1:
                raise ValueError("low_latency_tp requires attn_tp_size > 1")
            if parallel_config.attn_tp_size != parallel_config.world_size:
                raise ValueError("low_latency_tp requires attn_tp_size == world_size")
            # Low-latency TP keeps one identical token layout through the model.
            for tp_name in (
                "moe_tp_size", "o_proj_tp_size", "lmhead_tp_size",
                "embed_tp_size", "dense_tp_size", "shared_tp_size",
            ):
                setattr(parallel_config, tp_name, parallel_config.world_size)
            parallel_config.attn_dp_size = 1
            parallel_config.embed_dp_size = 1
            parallel_config.moe_ep_size = 1
            if config.num_attention_heads % parallel_config.attn_tp_size != 0:
                raise ValueError("num_attention_heads must be divisible by attn_tp_size")
            if config.o_groups % parallel_config.attn_tp_size != 0:
                raise ValueError("o_groups must be divisible by attn_tp_size")
            if config.moe_intermediate_size % parallel_config.moe_tp_size != 0:
                raise ValueError("moe_intermediate_size must be divisible by moe_tp_size")
            if model_config.force_eplb:
                raise ValueError("Basic MoE TP requires force_eplb=False for identical routing on all ranks")
```

</details>

## 设计决策

非均匀分片解决局部通道对齐，前缀和解决逻辑覆盖，按实际参数轴换算解决低精度存储坐标。三者必须一并审查。仅给 scale 补尾槽不能修复错误 checkpoint 起点。本文 recipes MX/SwiGLU 路径还要求合法半宽，当前路径不应再叠加历史兼容 padding；这不排除其他后端自行定义并验证 padding 协议。

## 验证信号

- [来源平台：950（仅源码目标，未上板）；证据等级：artifact_verified，静态源码] 当前 routed 分配保存前缀和；_load_w13/_load_w2 按来源张量实际轴长度换算起点。
- [来源平台：950（仅源码目标，未上板）；证据等级：artifact_verified，静态源码] shared 非均匀分支将通用 Linear 内部 TP 置为 1，并同时传 shard_offset/shard_full_size。

历史 before/after 和固定源码逐字核验只证明上述实现变化，没有加载重建、NPU 精度或性能通过证据。保持 draft，未生成 verified 事件。

## 部署验收

待执行：检查所有 rank 的逻辑覆盖与每个权重/scale 的物理区间；覆盖不同宽度的交界与首尾 rank；在目标 NPU 上保存参数重建和最终 all_reduce 输出对照。均匀可运行配置作为受控参考；性能和显存另测。

## 坏实践

使用 rank×本地宽度处理非均匀分片、把逻辑通道数直接作为 packed 字节偏移、给通用 Linear 传本地宽度后继续内部 TP 均分，都会让布局不一致。只看 copy_ 成功或 shape 相同不足以确认加载正确。

## 失效边界

U<P 时可能出现空 rank，当前仅有 warning，算子可用性未验证。非 MX 模式、任意非对齐 I、bitsandbytes 特殊加载不在本卡结论范围内。其他框架的打包轴与 scale 布局可能不同，必须按实际参数元数据换算；该公式不能脱离整除与布局条件直接移植。
