---
type: Runbook
title: MoE后端scale打包：区分字节表示与消费协议
description: 接口条件：先核对目标MoE后端的scale ABI；相邻E8M0字节成对int16打包仅是本文recipes Ascend包装层约定，并非所有DeepGEMM标准。
tags:
- task.debugging
- topic.precision
status: draft
sources: []
created_at: '2026-11-02T08:24:24Z'
updated_at: '2026-11-03T01:38:52Z'
platforms:
- '950'
aliases:
- DeepSeek V4.1：DeepGEMM scale 配对打包
---

# MoE后端scale打包：区分字节表示与消费协议

## 适用性与框架边界

本卡以**量化表示与实际消费协议配套**为主线。先确定目标 backend 要什么字节、什么轴和什么权重对应关系，再判断是否需要转换。

| 层次 | 读用范围 |
|---|---|
| 通用原则 | 值与 scale 的逻辑覆盖轴必须一致；dtype view、reshape 与算术打包是不同操作，不能互相替代。 |
| 成立前提 | 已确认所选 kernel/transform/buffer 的真实 ABI；只有与本文包装层协议相同，才可直接使用这里的成对算式与布局检查。 |
| recipes 专属 | **相邻 E8M0 字节成对打包成 int16 是本文 recipes Ascend wrapper 的约定**，不代表所有 DeepGEMM 或 vLLM MoE 后端必须如此表示。routed MXFP4、shared 条件化 MXFP8、post-load 轴与 sym_buffer 均按该实例核对。 |
| vLLM / 其他框架入口 | 检查模型量化方法的参数创建/post-load、experts 后端的权重转换和 kernel 实参适配；按实际 prepare/dispatch 与 finalize 追踪 token 行及贡献归属。 |

本轮没有真实 deep_gemm ABI、特殊值或 vLLM 接入验收；PREFILL/NONE 在示例中是静态部署角色，不能解释为当前 batch 阶段。

## 适用场景

MoE（混合专家）为每个 token 选择 K 个 routed expert：Dispatch 将 token 分给专家，GMM1 做 Gate/Up 两个投影，SwiGLU 激活后，GMM2 做 Down 投影，Combine 将各专家结果按路由权重合回。shared expert 处理所有 token，其贡献也应计入一次。本文 recipes Ascend 包装层通过外部 deep_gemm 接口承担这组融合专家计算；模型仍在外面产生 TopK，适配层负责权重表示和通信 buffer。

可复用的诊断对象是目标后端的 scale 表示边界；以下具体字节与轴取自 DeepSeek V4.1 的 recipes Ascend 包装层：MX 低精度把值与每个通道块的 scale 分开存储。E8M0 dtype 视图、尾维二元组 reshape、相邻字节算术打包，是三个不同操作，不能因为名称都含 MX 就互换。

以下成对 pack 和外部调用范围限 recipes 的当前 MegaMoE Prefill（一次处理上下文多 token）适配，要求非 MTP、加载角色 NONE/PREFILL、EP（专家并行）>1、TP（张量并行）=1、routed 量化归一到 w4a8mxfloat4。rank 指通信组中的一个计算进程。shared>0 时只接受一个；shared 生产链另要求实际 scheme 为 MxFp8LinearMethod 且满足加载后布局检查，不能由 routed 的 MXFP4 门禁推出。

路线为 recommended_fastpath 的静态诊断顺序，未验证运行收益。目标平台 950 来自模型支持说明；本轮仅固定源码逐字核验，未执行量化、外部算子、CPU/NPU、编译、图、精度或性能测试。CANN、torch_npu 与 deep_gemm 版本未知。

## 现象

接入或迁移后端时，若把原始 scale 或另一后端的 E8M0 视图直接交给本文 recipes Ascend wrapper 的权重元组、buffer.x_sf，可能绕过实际要求的 int16 配对表示；即使 copy 能接受，scale 也可能错配权重块或 token 行。本轮没有真实异常、误差或修复成功记录，触发条件来自静态审阅中发现 pack 被绕过、轴交换不配套等风险。

## 根因与判别方法

先核对目标 ABI，不能从 DeepGEMM 名称推断它采用 int16 成对表示。本文 wrapper 的每个 scale 槽对应一段输入通道；变换必须同时保留“专家/输出通道/输入块”或“token/输入块”的对应关系。下面 shape 是各明确阶段的布局推导，不能把参数分配阶段、post-load 视图和外部 transform 输出混为一张 shape 清单。

| 角色 | 轴与单位 | 生产者 → 消费者 |
|---|---|---|
| H、I、E | 隐藏通道、中间通道、本 rank 专家数 | 模型配置 → 权重创建、buffer |
| routed FP4 权重 | 创建时 [E,2I,H/2] / [E,H,I/2] uint8；一字节含两个 FP4 值 | MXFP4 create → post-load 格式转换 → prepare |
| routed scale | 创建时 [E,2I,ceil(H/32)] / [E,H,ceil(I/32)] 字节；每项对应输入块 | reshape 成二元尾轴 → prepare 展平 → pair pack |
| shared FP8 权重 | 创建时 [out,in]；post-load [in,out]；后端再转回 [2I,H] / [H,I] | 实际 MXFP8 scheme → shared transform |
| shared scale | 后端接收 [H/64,2I,2] / [I/64,H,2]；换轴后恢复输入块序列 | view(uint8) → pair pack → shared transform |
| x、x_fp8 | [T,H] 真实 token 行 / 动态量化值 | 当前 batch → buffer.x[:T] |
| x_scale、x_sf_packed | 每 token 每输入块的 scale / 相邻块配成 int16 的布局 | 动态量化 → buffer.x_sf[:T] |
| topk_ids / weights | [T,K]；专家编号 / 路由权重 | 模型 TopK → buffer；编号写入前转 int64 |
| fused 权重/scale 元组 | transform 的返回值；内部布局由外部包决定 | prepare 保存 → fp8_fp4_mega_moe |
| sym_buffer | 融合通信暂存与输入提交资源；含 x、x_sf、TopK 等区段 | context 按组/容量创建 → 每次融合调用 |

仅针对这份 recipes wrapper，设一行有 2G 个 exponent 字节，helper 计算 p[j]=e[2j]+256×e[2j+1]，转 int16 后连续化。因此低八位来自偶位，高八位来自奇位，元素数从 2G 变 G，名义字节数不变。它不反量化 scale，也不打包 FP4 权重值。

教学推演（非执行结果）：假设连续四个块的编码字节为 [1,2,3,4]，转 int16 前的算式给出 [513,1027]。若把第一对颠倒，就得到 258；shape 和字节总数都不变，却改变了两个通道块的对应关系。若交换输出/输入块轴后直接 flatten，甚至可能把不同输出通道的 scale 配成一对。这解释了为何必须先恢复正确轴，再 pack。int16 高位的实际读取、E8M0 特殊编码与外部 ABI 未验证；此例只说明源码算式，不证明所有字节组合的数值解释。

reshape_mx_scale 仅将 G 个块槽变成 [ceil(G/2),2] 视图，奇数槽补一个零尾槽；_pack_ue8m0_exponents 才把相邻字节合成一个 int16。pack 本身没有偶数长度或字节范围校验，不能推出任意奇数末维都支持。

## 诊断路径

1. 在自己的框架定位量化参数创建与 post-load、experts 的权重准备、动态激活量化、输入暂存及 kernel 调用。先从选中后端确认实际表示要求；以下 pack/buffer 操作只用于本文 wrapper 或已证实相同的 ABI。记录实际后端与外部包版本；本文 recipes 中还要记录后端 key，因为“开启 MegaMoE”不代表选中了 DeepGEMM。
2. 按 routed/shared/activation 分三条链记录原始 dtype、shape、stride、scale 的块轴、值与 scale 的逻辑对应。shared 先记录实际 scheme，不能从 routed 模式推断。若第一处差异就在 post-load shape，先修前置布局。
3. 按目标 ABI 保留表示变换前后的有效块数、轴标签与原始字节；只有使用本文 wrapper 的成对 ABI 时，才在每次 pack 前保留相邻字节对，并在 pack 后核对 dtype=int16、连续性、最后轴减半及每对的源码算式。若算式对但数值仍错，下一步检查配对是否跨行/跨输出通道，以及 scale 与权重是否经过同一逻辑换轴。
4. 对目标后端的权重转换输入/输出记录对象身份和关联权重；对动态输入记录同一批 token 的有效行域。本文 wrapper 中再对照 transform 元组及 buffer 的 T 和 x/x_sf/TopK 切片。本文四者 [:T] 应描述同一批 token；其他后端按自己的表示记录同一逻辑对应，不能只调整目标 dtype 让 copy_ 通过。
5. 查实际外部 schema 后，用相同输入、权重、路由、clamp 和既有精度标准比较普通 GMM 与融合路径；先分别核验表示和中间输出，再看最终结果。覆盖空 rank、上界及特殊编码；编译、图、通信完成和性能另验。若不满足接口，回退已验收的完整后端路线，不能只跳过 pack。

<details>
<summary>recipes / CANN Executor 完整实现对照（可选阅读）</summary>

## 快速检查

下列只读搜索为 recipes 源码的可选导航；外部框架按上述职责记录即可。已有静态核验定位了全部生产与消费块，没有导入模型或调用外部算子。

```bash
rg -n '_pack_ue8m0_exponents|w13_sf_packed|s1_packed|x_sf_packed|buffer.x_sf|def create_weights|def process_weights_after_loading|MxFp8LinearMethod|MxFp4LinearMethod' models/deepseek_v4_1/models/modules/op_impls/deepgemm_backend.py module/quantization/mxfp8.py module/quantization/compressed_tensors/compressed_tensors.py
```

## 系统信息

mxfp4 负责 routed 参数；mxfp8 与 compressed-tensors 委派负责条件化 shared 参数；quant_utils 整理 scale 二元尾轴；deepgemm_backend 负责 pack、transform、buffer 与调用；registry/model 负责选择与绑定。实际部署驱动、编译参数及库版本未知。

## 完整代码

以下保留原完整函数/因果块，均未在本轮运行。建议先读“成对 helper→shared 适配→prepare→run”理解表示终点，再回看参数生产与 post-load，最后检查 context/selector/模型入口。表中阶段顺序与下方原块顺序一致，便于逐字对照。

| 代码组 | 先回答的问题 |
|---|---|
| 参数创建与 post-load | 这些字节来自哪种 scheme，当前轴处于哪个加载阶段？ |
| pack 与 prepare/run | 哪两个相邻块成一对，哪个权重/token 消费它？ |
| context 与 Prefill | buffer 为哪一组、多少行分配，空 rank 如何参与？ |
| selector 与模型入口 | 实际调用的是谁，模型是否已将 shared 委派一次？ |

### Routed 常量

BLOCK_K 为 scale 块宽，PACK_FACTOR 为 FP4 值的字节打包因子；二者不是 int16 exponent 配对因子。

```python
ACTIVATION_SCHEMES = ["static", "dynamic"]
BEFORE_INIT = 0
AFTER_INIT = 1
BLOCK_K = 32
PACK_FACTOR = 2
```

### Routed MXFP4 初始化

输入无额外张量；计算每个存储字节容纳的 FP4 权重值数，供 create_weights 使用。

```python
    def __init__(self):
        super().__init__()
        STORAGE_BITS_NPU = 8
        WEIGHT_BITS = 4
        self.pack_factor = STORAGE_BITS_NPU // WEIGHT_BITS
```

### Routed 参数创建：create_weights

输入 E、H、局部 I，创建 w13/w2 及 scale。w13 沿输出轴拼 Gate/Up，w2 沿输入中间轴；scale 与各自输入块对应。这里是分配阶段，还没有下段的格式转换。

```python
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

### Routed post-load

输入已加载权重与 scale；权重转换为 NPU 格式，scale 经 reshape_mx_scale 配成尾轴二元视图。它尚未调用 int16 pack，后端 prepare 会先回到 ND 存储再处理。

```python
    def process_weights_after_loading(
        self, layer: torch.nn.Module,
        is_transpose: bool = True,
        is_nz: bool = True,
        **kwargs,
    ) -> None:
        w13_weight = layer.w13_weight
        w2_weight = layer.w2_weight
        w13_weight_scale = layer.w13_weight_scale
        w2_weight_scale = layer.w2_weight_scale
        w13_weight = torch_npu.npu_format_cast(
            w13_weight.data.contiguous(), 29,
            customize_dtype=torch.float8_e4m3fn,
            input_dtype=torch_npu.float4_e2m1fn_x2
        )
        w2_weight = torch_npu.npu_format_cast(
            w2_weight.data.contiguous(), 29,
            customize_dtype=torch.float8_e4m3fn,
            input_dtype=torch_npu.float4_e2m1fn_x2
        )
        w13_weight_scale.data = reshape_mx_scale(w13_weight_scale.data)
        w2_weight_scale.data = reshape_mx_scale(w2_weight_scale.data)
        layer.w13_weight = Parameter(w13_weight, requires_grad=False)
        layer.w2_weight = Parameter(w2_weight, requires_grad=False)
```

### Shared MXFP8 常量

这是 shared 条件化生产者的块宽定义，不能拿 routed FP4 位宽替代。

```python
ACTIVATION_SCHEMES = ["static", "dynamic"]
BEFORE_INIT = 0
AFTER_INIT = 1
BLOCK_K = 32
```

### Shared scheme 条件

输入 weight/input 量化配置；检查位宽、浮点类型、块策略、对称性与动态激活条件，返回是否选择 MXFP8。仅出现类名不证明部署配置满足这些条件。

```python
    def is_dynamic_group_w8a8_mxfp8(self,
                               weight_quant: BaseModel,
                               input_quant: BaseModel,) -> bool:
        weight_block_size = self.get_weight_block_size(weight_quant)
        is_mxfloat = (weight_block_size is not None and weight_block_size[0] == 1 and
                      weight_block_size[1] == MX_BLOCK_K and weight_quant.type == "float")
        is_w8a8_mxfp8 = (weight_quant.num_bits == 8) and (input_quant.num_bits == 8) and is_mxfloat
        weight_strategy = (
            weight_quant.strategy == QuantizationStrategy.GROUP.value
            or weight_quant.strategy == QuantizationStrategy.BLOCK.value)
        # The strategy of mxfp8 is group
        input_strategy = (input_quant.strategy
                    == QuantizationStrategy.GROUP.value)
        satisfied_strategies = input_strategy and weight_strategy
        is_dynamic = not weight_quant.dynamic and input_quant.dynamic

        # Both symmetric and asymmetric input quantization supported.
        # Only symmetric weight quantization supported.
        return is_w8a8_mxfp8 and satisfied_strategies and weight_quant.symmetric and is_dynamic
```

### Shared scheme 选择：_get_scheme_from_parts

本函数分派多个候选方案；只有对应条件命中才返回 MxFp8LinearMethod。MXFP4 是另一分支，具有不同打包布局，不能用它证明本卡 shared shape。

```python
    def _get_scheme_from_parts(
            self,
            layer_name: str,
            weight_quant: BaseModel,
            input_quant: BaseModel) -> "CompressedTensorsScheme":

        if is_activation_quantization_format(self.quant_format):
            if self.is_dynamic_token_w8a8_int8(weight_quant, input_quant):
                return CompressedTensorsW8A8Int8LinearMethod(
                    strategy=weight_quant.strategy,
                    is_static_input_scheme=False,
                    input_symmetric=input_quant.symmetric)
            elif self.is_dynamic_token_w8a8_hifloat8(weight_quant, input_quant):
                return CompressedTensorsW8A8Hif8LinearMethod(
                    strategy=weight_quant.strategy,
                    is_static_input_scheme=False,
                    input_symmetric=input_quant.symmetric)
            elif self.is_dynamic_group_w8a8_mxfp8(weight_quant, input_quant):
                return MxFp8LinearMethod()
            elif self.is_dynamic_group_w8a8_fp8(weight_quant, input_quant):
                weight_block_size = self.get_weight_block_size(weight_quant)
                return Fp8PerTileLinearMethod(self, weight_block_size)
            elif self.is_dynamic_group_w4a4_mxfp4(weight_quant, input_quant):
                return MxFp4LinearMethod()

        raise NotImplementedError(
            "No compressed-tensors compatible scheme was found.")
```

### 参数创建委派

CompressedTensorsLinearMethod 将输入/输出分片信息交给 layer.scheme；最终张量由实际 scheme 创建。

```python
    def create_weights(self, layer: torch.nn.Module,
                       input_size_per_partition: int,
                       output_partition_sizes: list[int],
                       input_size: int,
                       output_size: int,
                       params_dtype: torch.dtype,
                       **extra_weight_attrs):
        """
        Use the CompressedTensorsScheme associated with each layer to create
        the necessary parameters for the layer. See LinearMethodBase for param
        details
        """
        weight_loader = extra_weight_attrs.get("weight_loader")
        layer.scheme.create_weights(
            layer=layer,
            input_size=input_size,
            input_size_per_partition=input_size_per_partition,
            output_partition_sizes=output_partition_sizes,
            output_size=output_size,
            params_dtype=params_dtype,
            weight_loader=weight_loader)
```

### post-load 委派

同样把 transpose/NZ/scales 参数交给实际 scheme；包装类名称不会消除 scheme 差异。

```python
    def process_weights_after_loading(self, layer: torch.nn.Module,
                                      is_transpose: bool = True,
                                      is_nz: bool = True,
                                      scales_dtype: torch.dtype = None,
                                      ) -> None:
        layer.scheme.process_weights_after_loading(layer,
                                                   is_transpose=is_transpose,
                                                   is_nz=is_nz,
                                                   scales_dtype=scales_dtype
                                                   )
```

### Shared MXFP8 create_weights

分配 E4M3 权重 [out,in] 和 uint8 scale [out,input块]，并设置输入/输出分片轴属性。输出和后端接收的转置视图处于不同阶段。

```python
    def create_weights(self,
                       layer: torch.nn.Module,
                       input_size_per_partition: int,
                       output_partition_sizes: list[int],
                       input_size: int,
                       output_size: int,
                       params_dtype: torch.dtype,
                       weight_loader: Callable,
                       **kwargs):
        weight_dtype = torch.float8_e4m3fn
        weight = Parameter(torch.empty(sum(output_partition_sizes),
                                       input_size_per_partition,
                                       dtype=weight_dtype),
                           requires_grad=False)
        set_weight_attrs(weight, {"input_dim": 1, "output_dim": 0, "weight_loader": weight_loader})
        layer.register_parameter("weight", weight)

        scale_dtype = torch.uint8

        weight_scale = Parameter(
            torch.empty((math.ceil(sum(output_partition_sizes)), math.ceil(input_size_per_partition // BLOCK_K)),
                        dtype=scale_dtype), requires_grad=False)
        set_weight_attrs(weight_scale, {"input_dim": 1, "output_dim": 0, "weight_loader": weight_loader})
        layer.register_parameter("weight_scale", weight_scale)

        setattr(layer, "init_state", BEFORE_INIT)
```

### Shared MXFP8 post-load

根据 is_transpose 交换权重轴，同时把 scale 配对并换轴；is_nz 再控制设备格式。后端 shape guard 绑定的是这个阶段的产物，不是原 checkpoint。

```python
    def process_weights_after_loading(self, layer, is_transpose=True, is_nz=True, scales_dtype=None):
        weight = layer.weight
        weight_scale = layer.weight_scale
        if is_transpose:
            weight.data = weight.data.transpose(-2, -1)
            weight_scale = reshape_mx_scale(weight_scale).transpose(0, 1)
        else:
            weight_scale = reshape_mx_scale(weight_scale)
        if is_nz:
            weight.data = torch_npu.npu_format_cast(weight.data.contiguous(), 29)  # 29: format nz
            weight_scale.data = weight_scale.data.contiguous()
        layer.weight = Parameter(weight, requires_grad=False)
        layer.weight_scale = Parameter(weight_scale, requires_grad=False)
        if getattr(layer, "bias", None) is not None:
            layer.bias = Parameter(layer.bias.to(torch.float32).contiguous(), requires_grad=False)
```

### scale pair reshape

仅组织尾维和奇数尾槽，保留字节顺序；没有合成 int16。

```python
def reshape_mx_scale(scale_tensor):
    """
    Reshape the last dimension into pairs for GMM/MM operators; an odd
    group count gets one zero tail slot for the pair view.
    """
    import torch
    num_groups = scale_tensor.size(-1)
    if num_groups % 2:
        pad = torch.zeros((*scale_tensor.shape[:-1], 1), dtype=scale_tensor.dtype,
                          device=scale_tensor.device)
        scale_tensor = torch.cat((scale_tensor, pad), dim=-1)
        num_groups += 1
    return scale_tensor.view(*scale_tensor.shape[:-1], num_groups // 2, 2)
```

### 模型完整 post-load

长函数按模块类型执行不同转置与格式策略，再在末尾逐 MoE 准备后端。与本卡相关的阅读锚点如下：

| 位置 | 关键变量 | 与表示合同的关系 |
|---|---|---|
| 模块遍历 | quant_method、scales_dtype | 选择各模块真实量化后处理 |
| 布局开关 | is_weight_nz、is_transpose | MegaMoE shared 排除 NZ 等条件，决定后端准备前布局 |
| 后端尾部 | prepare_layer、release_layer | 先完成通用 post-load，再读取权重准备融合元组 |

其他注意力/indexer 分支作为完整函数上下文保留，不能据它们扩大本卡结论。原参数生命周期见[配套卡](../runtime/deepseek_v41_deepgemm_prefill_weight_release_lifecycle.md)。

```python
    def process_weights_after_loading(self):
        """
        Do weight transpose, format cast to NZ, and scale dtype cast after loading weights.
        """
        float_scales_map = [
            "gate_up_proj",
            "q_b_proj",
            "wq_b",
        ]
        float_smooth_scales_map = [
            "down_proj"
        ]
        enable_weight_nz = self.infer_config.model_config.enable_weight_nz
        indexer_prolog_qw_kernel = getattr(self, "selected_op_kernels", {}).get(
            "indexer_prolog_qw", ""
        )
        use_indexer_prolog_qw = indexer_prolog_qw_kernel.startswith(
            "indexer_prolog_qw_ascendc_"
        )

        indexer_weights_stream = None
        for module_name, module in self.named_modules():
            # Create native Q/W resources after kernel selection, before graph capture.
            if (isinstance(module, Attention) and module.low_latency_tp and module.compress_ratio > 0
                    and not module.is_mla_rank and module.is_index_source and not use_indexer_prolog_qw):
                if indexer_weights_stream is None:
                    indexer_weights_stream = create_stream("separate_mla_weights")
                module.indexer_weights_stream = indexer_weights_stream
            if (isinstance(module, Indexer)
                    and self.low_latency_tp):
                module.use_fused_prolog_qw = use_indexer_prolog_qw
            if module_name.endswith("compressor.norm"):
                module.weight.data = module.weight.data.to(torch.float32)
            if module_name.endswith("attn.indexer.k_norm"):
                module.weight.data = module.weight.data.to(torch.float32)

            if module_name.startswith("vision_model.") and isinstance(module, nn.Linear):
                if enable_weight_nz:
                    module.weight.data = torch_npu.npu_format_cast(module.weight.data, 29)
                continue

            if "wo_a" in module_name:
                config = self.config
                head_dim_per_group = config.num_attention_heads * config.head_dim // config.o_groups
                module.weight.data = module.weight.data.view(-1, config.o_lora_rank, head_dim_per_group) \
                                                   .transpose(1, 2).contiguous()
                if config.quant_config.mm_quant_mode == "w8a8mxfloat8":
                    scale_data = reshape_mx_scale(module.weight_scale.data)
                    module.weight_scale.data = scale_data.view(-1, config.o_lora_rank, *scale_data.shape[1:]) \
                                                   .transpose(1, 2).contiguous()
                if enable_weight_nz:
                    module.weight.data = torch_npu.npu_format_cast(module.weight.data, 29)
                continue

            quant_method = getattr(module, "quant_method", None)
            scales_dtype = {}
            for scale_name in float_scales_map:
                if scale_name in module_name:
                    scales_dtype["scale_dtype"] = torch.float
                    break

            for smooth_scale_name in float_smooth_scales_map:
                if smooth_scale_name in module_name:
                    scales_dtype["smooth_scale_dtype"] = torch.float
                    break

            is_wq_b_transpose = self.config.num_attention_heads * self.config.head_dim > MATMUL_MAX_AXIS_VALUE
            is_c1a_compressor = (
                module_name.endswith(".compressor.wkv")
                and self.get_submodule(module_name.rsplit(".", 1)[0]).compress_ratio == 1
            )
            is_weight_nz = enable_weight_nz and not (
                ("compressor" in module_name and not is_c1a_compressor)
                or module_name.endswith(".ffn.gate")
                or (self.enable_mega_moe and ".shared_experts." in module_name)
                or (is_wq_b_transpose and "attn.wq_b" in module_name)
                or ("markov_w2" in module_name)
                or ("confidence_head" in module_name)
            )

            is_transpose = False if "compressor" in module_name else True

            # Indexer prologue kernels consume output-major weights in
            # FRACTAL_NZ.  The K prologue uses the same layout for wk.
            is_indexer_prolog_qw_weight = (
                module_name.endswith("attn.indexer.wk")
                or (
                    use_indexer_prolog_qw
                    and module_name.endswith(("attn.indexer.wq_b", "attn.indexer.weights_proj"))
                )
            )
            is_weight_nz = is_indexer_prolog_qw_weight or is_weight_nz

            is_transpose = is_transpose and not is_indexer_prolog_qw_weight
            if isinstance(quant_method, QuantizeMethodBase):
                quant_method.process_weights_after_loading(
                    module,
                    is_nz=is_weight_nz,
                    is_transpose=is_transpose,
                    scales_dtype=scales_dtype,
                )

            moe_quant_methods = (
                Fp8PerTileMoEGMMMethod,
            )
            if isinstance(quant_method, moe_quant_methods) and self.moe_ep_size > 1:
                all_experts_smooth_scale = module.smooth_scale_1.data.new_empty(
                    module.smooth_scale_1.data.shape[0] * self.moe_ep_size,
                    module.smooth_scale_1.data.shape[1],
                )
                dist.all_gather_into_tensor(
                    all_experts_smooth_scale,
                    module.smooth_scale_1.data,
                    group=self.comm_manager.get_group("moe_ep_group"),
                )
                module.smooth_scale_1.data = all_experts_smooth_scale

        # Fixed inference weights: gather once, before warm-up and graph capture.
        for module in self.modules():
            if (isinstance(module, Attention) and module.low_latency_tp and module.compress_ratio > 0
                    and module.is_mla_rank and module.attn_tp_size > 1):
                module.full_attn_sink = module.attn_sink.new_empty(module.n_heads)
                dist.all_gather_into_tensor(
                    module.full_attn_sink, module.attn_sink.detach().contiguous(),
                    group=self.comm_manager.get_group(module.attn_group_name),
                )

        if self.megamoe_backend is not None:
            release_layer = (
                getattr(self.megamoe_backend, "release_layer", None)
                if self.disagg_mode == "PREFILL"
                else None
            )
            for module in self.modules():
                if isinstance(module, DeepseekV41MoE):
                    self.megamoe_backend.prepare_layer(module)
                    if release_layer is not None:
                        release_layer(module)
```

### 成对算式：_pack_ue8m0_exponents

输入最后轴按相邻输入块排列的编码项；转 int32 计算低/高八位组合，返回连续 int16。辅助函数不检查字节范围、末维偶数或外部 schema。

```python
def _pack_ue8m0_exponents(exponent: torch.Tensor) -> torch.Tensor:
    exponent = exponent.to(torch.int32)
    return (exponent[..., ::2] + exponent[..., 1::2] * 256).to(torch.int16).contiguous()
```

### Shared 轴恢复：build_shared_args

输入加载后的 shared 专家；检查一个 shared、权重形状和 scale 形状。s1_raw/s2_raw 先把输出通道移到前面，再恢复输入块序列，view(uint8) 后 pack；返回两层 (weight,scale_packed) 元组。

```python
    def build_shared_args(self, moe) -> tuple:
        n_shared = getattr(moe, "n_shared_experts", None) or 0
        if n_shared != 1:
            raise RuntimeError(
                "MegaMoE shared expert path only supports n_shared_experts=1"
            )
        shared = moe.shared_experts
        hidden = moe.hidden_dim
        int_h = moe.intermediate_size

        w1 = shared.gate_up_proj.weight
        if tuple(w1.shape) != (hidden, 2 * int_h):
            raise RuntimeError(
                f"unexpected shared gate_up_proj layout: {tuple(w1.shape)}"
            )
        w1 = w1.transpose(-2, -1).contiguous()

        w2 = shared.down_proj.weight
        if tuple(w2.shape) != (int_h, hidden):
            raise RuntimeError(
                f"unexpected shared down_proj layout: {tuple(w2.shape)}"
            )
        w2 = w2.transpose(-2, -1).contiguous()

        s1 = shared.gate_up_proj.weight_scale
        if tuple(s1.shape) != (hidden // 64, 2 * int_h, 2):
            raise RuntimeError(
                f"unexpected shared gate_up_proj scale layout: {tuple(s1.shape)}"
            )
        s1_raw = s1.transpose(0, 1).contiguous().reshape(2 * int_h, hidden // 32)
        s1_packed = _pack_ue8m0_exponents(s1_raw.view(torch.uint8))

        s2 = shared.down_proj.weight_scale
        if tuple(s2.shape) != (int_h // 64, hidden, 2):
            raise RuntimeError(
                f"unexpected shared down_proj scale layout: {tuple(s2.shape)}"
            )
        s2_raw = s2.transpose(0, 1).contiguous().reshape(hidden, int_h // 32)
        s2_packed = _pack_ue8m0_exponents(s2_raw.view(torch.uint8))

        return (w1, s1_packed), (w2, s2_packed)
```

### 空 rank 输入：build_dummy_chunk

从加载后的 gate 创建一行零输入、不同专家号及零权重；其结果供空 rank collective 调用后丢弃，不进入真实 token 输出。

```python
    @staticmethod
    def build_dummy_chunk(moe) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        hidden = int(moe.hidden_dim)
        topk = int(moe.top_k)

        dummy_x = moe.gate.weight.new_zeros((1, hidden))
        dummy_ids = torch.arange(
            topk, dtype=torch.int32, device=dummy_x.device
        ).unsqueeze(0)
        dummy_weight = torch.zeros(
            (1, topk), dtype=torch.float32, device=dummy_x.device
        )
        return dummy_x, dummy_ids, dummy_weight
```

### Routed 与 shared 准备：prepare_layer

本函数连接三种表示阶段并把最终元组存到层内，按以下段落阅读：

| 段落 | 中间变量 | 输出用途 |
|---|---|---|
| shared 条件与 dummy | shared_l1/l2、_megamoe_dummy_chunk | 准备可选 shared 与空 rank 输入 |
| routed 权重回 ND | w13_nd/w2_nd、w13_int8/w2_int8 | 同字节视图交外部 transform；不是数值重新量化 |
| routed scale 展平/pack | w13_sf_flat、w13_sf_packed 等 | 末两轴恢复输入块再成对 |
| transform | fused_w13/fused_w13_sf 等 | 外部返回的配对表示 |
| 保存 | _megamoe_static_kwargs | run 的权重、scale 与 clamp 来源 |

局部 del 和 empty_cache 不证明底层 storage 回收或显存收益。

```python
    def prepare_layer(self, moe) -> None:
        n_shared = getattr(moe, "n_shared_experts", 0) or 0
        if n_shared > 0:
            shared_l1, shared_l2 = self.build_shared_args(moe)
        else:
            shared_l1, shared_l2 = None, None

        moe._megamoe_dummy_chunk = self.build_dummy_chunk(moe)

        experts = moe.experts
        w13 = experts.w13_weight.data
        w2 = experts.w2_weight.data
        w13_sf = experts.w13_weight_scale.data
        w2_sf = experts.w2_weight_scale.data

        w13_nd = torch_npu.npu_format_cast(w13.contiguous(), 2).view(torch.uint8).contiguous()
        w2_nd = torch_npu.npu_format_cast(w2.contiguous(), 2).view(torch.uint8).contiguous()
        w13_int8 = w13_nd.view(torch.int8)
        w2_int8 = w2_nd.view(torch.int8)

        w13_sf_flat = w13_sf.reshape(w13_sf.shape[0], w13_sf.shape[1], -1)
        w2_sf_flat = w2_sf.reshape(w2_sf.shape[0], w2_sf.shape[1], -1)
        w13_sf_packed = _pack_ue8m0_exponents(w13_sf_flat)
        w2_sf_packed = _pack_ue8m0_exponents(w2_sf_flat)

        (fused_w13, fused_w13_sf), (fused_w2, fused_w2_sf) = \
            self.deep_gemm.transform_weights_for_mega_moe(
                (w13_int8, w13_sf_packed), (w2_int8, w2_sf_packed))

        del w13_nd, w2_nd, w13_int8, w2_int8
        del w13_sf_flat, w2_sf_flat, w13_sf_packed, w2_sf_packed
        torch.npu.empty_cache()

        if shared_l1 is not None:
            shared_l1, shared_l2 = self.deep_gemm.transform_weights_for_mega_moe(
                shared_l1, shared_l2)

        moe._megamoe_static_kwargs = {
            "l1_weights": (fused_w13, fused_w13_sf),
            "l2_weights": (fused_w2, fused_w2_sf),
            "shared_l1_weights": shared_l1,
            "shared_l2_weights": shared_l2,
            "activation_clamp": moe.swiglu_limit,
        }
```

### 激活与实际消费：_run_mega_moe

输入 [T,H]、[T,K] 的专家编号与权重，输出 BF16 y。动态量化先产生 x_fp8/x_scale，取 scale 编码、展平并 pack；随后同一 [:T] 切片写 x、x_sf、TopK。最后 fp8_fp4_mega_moe 消费 prepare 保存的元组与 buffer。检查 token 行一致与 scale 块一致须同时进行。

```python
    def _run_mega_moe(
        self,
        moe,
        x: torch.Tensor,
        topk_ids: torch.Tensor,
        topk_weight: torch.Tensor,
    ) -> torch.Tensor:
        buffer = self.sym_buffer
        num_tokens = x.shape[0]
        hidden = x.shape[1]

        x_fp8, x_scale = torch_npu.npu_dynamic_mx_quant(
            x.contiguous(), dst_type=torch.float8_e4m3fn)
        x_scale_u8 = x_scale.view(torch.uint8)
        if x_scale_u8.dim() > 2:
            x_scale_u8 = x_scale_u8.flatten(1)
        x_sf_packed = _pack_ue8m0_exponents(x_scale_u8)

        buffer.x[:num_tokens].copy_(x_fp8)
        buffer.x_sf[:num_tokens].copy_(x_sf_packed)
        buffer.topk_idx[:num_tokens].copy_(topk_ids.to(torch.int64))
        buffer.topk_weights[:num_tokens].copy_(topk_weight)

        y = torch.empty((num_tokens, hidden), dtype=torch.bfloat16, device=x.device)

        kwargs = moe._megamoe_static_kwargs
        self.deep_gemm.fp8_fp4_mega_moe(
            y,
            kwargs["l1_weights"],
            kwargs["l2_weights"],
            buffer,
            shared_l1_weights=kwargs["shared_l1_weights"],
            shared_l2_weights=kwargs["shared_l2_weights"],
            activation='swiglu',
            activation_clamp=kwargs["activation_clamp"],
        )
        return y
```

### DeepGemmContext

输入通信组、模型维度和每 rank 容量，导入 deep_gemm 并创建 symmetric buffer。它承担融合通信暂存和初始化协议；创建调用本身不证明包或通信可用。destroy 只显示对外部销毁的调用与 context 字段置空，不证明所有持有者和物理内存均释放。

```python
class DeepGemmContext:
    """Model-level MegaMoE resources shared by all DeepSeek-V4 MoE layers."""

    def __init__(
        self,
        config,
        num_max_tokens_per_rank: int,
        comm_manager: CommManager,
        ep_group_name: str,
    ) -> None:
        try:
            import deep_gemm
        except ImportError as exc:
            raise ImportError(
                "DeepGemm backend requires cann_ops_transformer.ops with "
                ""
            ) from exc

        if comm_manager is None:
            raise RuntimeError("MegaMoE backend requires an initialized CommManager.")
        if not comm_manager.has_group(ep_group_name):
            raise RuntimeError(
                f"MegaMoE backend requires communication group {ep_group_name!r}."
            )

        if num_max_tokens_per_rank <= 0:
            raise ValueError(
                "enable_mega_moe=True requires a positive max_prefill_tokens, "
                f"got {num_max_tokens_per_rank}."
            )

        self.num_max_tokens_per_rank = num_max_tokens_per_rank
        self.group = comm_manager.get_group(ep_group_name)
        self.deep_gemm = deep_gemm
        num_shared_experts = getattr(config, "n_shared_experts", 0) or 0
        self.sym_buffer = deep_gemm.get_symm_buffer_for_mega_moe(
            self.group,
            num_experts=config.n_routed_experts,
            num_max_tokens_per_rank=num_max_tokens_per_rank,
            num_topk=config.num_experts_per_tok,
            hidden=config.hidden_size,
            intermediate_hidden=config.moe_intermediate_size,
            num_shared_experts=num_shared_experts,
        )

    def destroy(self) -> None:
        if self.sym_buffer is not None:
            self.sym_buffer.destroy()
            self.sym_buffer = None
```

### Backend 持有资源

适配器保存 context、deep_gemm 和同一 buffer 引用；资源所有权检查不能只看 context 一个字段。

```python
    def __init__(self, context: DeepGemmContext) -> None:
        self.context = context
        self.deep_gemm = context.deep_gemm
        self.sym_buffer = context.sym_buffer
```

### Prefill 容量与空 rank

输入本地整批 T 行。超上界拒绝；T=0 仍调用一次 dummy 再返回 [0,H]，其他情况返回融合输出。该入口没有 chunk 参数。

```python
    def prefill(
        self,
        moe,
        x: torch.Tensor,
        topk_ids: torch.Tensor,
        topk_weight: torch.Tensor,
    ) -> torch.Tensor:
        if self.sym_buffer is None:
            raise RuntimeError("MegaMoE backend requires an initialized sym_buffer.")

        num_tokens, hidden = x.shape
        if num_tokens > self.context.num_max_tokens_per_rank:
            raise RuntimeError(
                f"MegaMoE got {num_tokens} tokens on this rank, above the symmetric "
                f"buffer bound {self.context.num_max_tokens_per_rank}."
            )

        if num_tokens == 0:
            dummy_x, dummy_ids, dummy_weight = moe._megamoe_dummy_chunk
            self._run_mega_moe(moe, dummy_x, dummy_ids, dummy_weight)
            return x.new_empty(0, hidden)

        routed_output = self._run_mega_moe(moe, x, topk_ids, topk_weight)
        return routed_output.view(num_tokens, hidden)
```

### 本地容量上界

从调度预算与 CP（上下文并行）分段/填充推导上界；它不是实际每次 T 的替代，调用处仍要记录真实行数。

```python
def get_max_local_prefill_tokens(infer_config: InferenceConfig, segment_min_len: int):
    """Upper bound on the prefill tokens one rank computes in a single step."""
    max_prefill_tokens = infer_config.scheduler_config.max_prefill_tokens
    cp_size = infer_config.parallel_config.cp_size
    if cp_size <= 1:
        return max_prefill_tokens
    # CP pads every request to 2 * cp_size segments and hands two of them to each rank.
    segments = 2 * cp_size
    segment_len = max((max_prefill_tokens + segments - 1) // segments, segment_min_len)
    extra_requests = infer_config.scheduler_config.cp_mini_batch - 1
    return 2 * segment_len + 2 * extra_requests * (segment_min_len + 1)
```

### 注册平台列表

注册系统含多个平台后缀，不是各平台运行验收。本卡仅采用模型说明的目标 950。

```python
SUPPORT_PLATFORM = ["A3", "950"]
```

### register_op_impl

把实现登记到带平台后缀的 key；登记负责可选项查找，不验证外部 ABI。

```python
def register_op_impl(op_type, func_key: str = None):
    def decorator(func):
        if op_type not in OpKernel.OP_TYPE:
            OpKernel.OP_TYPE.append(op_type)
            logger.info(f"register optype {op_type} success.")
        func_name = func_key if func_key else func.__name__
        support_platform = tuple([platform.lower() for platform in SUPPORT_PLATFORM])
        if not func_name.endswith(support_platform):
            for platform in support_platform:
                func_name_update = func_name + "_" + platform
                if func_name_update in OpKernel.KERNEL_MAP:
                    logger.warning(f"func {func_name_update} is registered, and will be overlapped.")
                OpKernel.KERNEL_MAP[func_name_update] = func
        else:
            if func_name in OpKernel.KERNEL_MAP:
                logger.warning(f"func {func_name} is registered, and will be overlapped.")
            OpKernel.KERNEL_MAP[func_name] = func

        @functools.wraps(func)
        def wrapper(*args, **kargs):
            return func(*args, **kargs)
        return wrapper
    return decorator
```

### auto_import_modules

自动导入实现模块，异常只告警。因此目录里有文件不能证明运行时成功注册。

```python
def auto_import_modules(pkg_name):
    package = importlib.import_module(pkg_name)
    for _, module_name, is_pkg in pkgutil.walk_packages(
        package.__path__,
        package.__name__ + "."
    ):
        if not is_pkg:
            try:
                importlib.import_module(module_name)
            except Exception as e:
                logger.warning(f"import module {module_name} failed: {str(e)}")
```

### op_impl_apply

按 key 取函数并绑定 OpKernel；缺 key 时告警返回。模型选择器还会做显式存在性检查。

```python
    @classmethod
    def op_impl_apply(cls, op_type, used_kernel):
        if used_kernel not in cls.KERNEL_MAP:
            logger.warning(f"{used_kernel} is not support")
            return
        used_kernel_func = cls.KERNEL_MAP[used_kernel]
        setattr(cls, op_type, staticmethod(used_kernel_func))
        return
```

### megamoe_deepgemm 工厂

创建 context 与 backend；至此才建立 deep_gemm 外部依赖和资源引用。

```python
@register_op_impl(op_type="megamoe")
def megamoe_deepgemm(config, num_max_tokens_per_rank: int,
                     comm_manager: CommManager, ep_group_name: str):
    context = DeepGemmContext(config, num_max_tokens_per_rank, comm_manager, ep_group_name)
    return context, DeepGemmBackend(context)
```

### update_op_kernel_dict

读取 kernel_config 与平台后缀，显式 deepgemm 时构造对应 key；缺省优先 ascendc，再 native。selected_op_kernels 是判断真实选择的记录，开启融合开关不等于选中 DeepGEMM。

```python
    def update_op_kernel_dict(self, op_types):
        """Bind requested implementations using kernel_config."""
        auto_import_modules(f"{__package__}.modules.op_impls")
        kernel_config = self.infer_config.model_config.custom_params.get("kernel_config", {})
        platform_version = self.infer_config.model_config.platform_version.value.lower()

        for op_type in op_types:
            if op_type in kernel_config:
                kernel_impl = kernel_config[op_type]
                used_kernel = f"{op_type}_{kernel_impl}_{platform_version}"
            else:
                default_kernel = f"{op_type}_ascendc_{platform_version}"
                used_kernel = (
                    default_kernel
                    if default_kernel in OpKernel.KERNEL_MAP
                    else f"{op_type}_native_{platform_version}"
                )
            if used_kernel not in OpKernel.KERNEL_MAP:
                raise ValueError(
                    f"Unsupported kernel implementation {used_kernel!r} for {op_type!r}."
                )
            OpKernel.op_impl_apply(op_type, used_kernel)
            self.selected_op_kernels[op_type] = used_kernel
            logger.info("%s use impl %s", op_type, used_kernel)
```

### 模型融合开关

限制 NONE/PREFILL、非 MTP；这是加载角色，不是本次 forward 的 is_prefill 标志。

```python
        self.disagg_mode = self.infer_config.disagg_config.disaggregation_mode
        self.enable_mega_moe = (
            self.infer_config.model_config.custom_params.get("enable_mega_moe", False)
            and self.disagg_mode in ("NONE", "PREFILL")
            and not self.is_mtp
        )
```

### 模型后端绑定

选择实现，传本地容量与通信组，保存 context/backend 并传给各 MoE 层。组名与 rank 范围应与实际 EP 布局一致。

```python
        self.megamoe_context = None
        self.megamoe_backend = None
        self.selected_op_kernels = {}
        if self.enable_mega_moe:
            self.update_op_kernel_dict(("megamoe",))
            self.megamoe_context, self.megamoe_backend = OpKernel.megamoe(
                config,
                get_max_local_prefill_tokens(self.infer_config, config.sliding_window),
                self.comm_manager,
                ep_group_name="dspark_megamoe_ep_group" if is_mtp else "megamoe_ep_group",
            )
            kwargs["megamoe_backend"] = self.megamoe_backend
```

### 配置门禁

限制 EP>1、TP=1 和 routed 量化。shared scheme 仍要独立检查；不能由此推导 shared 是 MXFP4 或 MXFP8。

```python
        if (custom_params.get("enable_mega_moe", False)
                and infer_config.disagg_config.disaggregation_mode in ("NONE", "PREFILL")):
            if parallel_config.moe_ep_size <= 1:
                raise ValueError(
                    f"enable_mega_moe=True with moe_ep_size={parallel_config.moe_ep_size} "
                    "is not supported yet."
                )
            if parallel_config.moe_tp_size != 1:
                raise ValueError(
                    f"enable_mega_moe=True with moe_tp_size={parallel_config.moe_tp_size} "
                    "is not supported yet."
                )
            quant_config = getattr(config, "quant_config", None)
            gmm_quant_mode = None if quant_config is None else quant_config.gmm_quant_mode
            # "w4a8float4" is accepted because update_gmm_quant_mode normalizes it
            # to "w4a8mxfloat4" during model construction (MegaMoE only runs there).
            if gmm_quant_mode not in ("w4a8mxfloat4", "w4a8float4"):
                raise ValueError(
                    f"enable_mega_moe=True with gmm_quant_mode={gmm_quant_mode} "
                    "is not supported yet."
                )
```

### MoE.forward

输入隐藏状态，先选择 shared 计算职责，再在外部做 Gate/TopK；只有 Prefill 且 enable_mega_moe 时直接调用后端。此时模型跳过独立 shared，避免重复贡献。Decode 与 TP 是其他路径，不由本卡证明兼容。

```python
    def forward(self, hidden_states, is_prefill=False, cur_topk_list=None, input_ids=None, image_mask=None,
                shared_expert_stream=None, prefill_moe_global_chunks=None, engram_resource_events=None,
                moe_events=None):
        moe_events = moe_events or {}
        shared_expert_events = moe_events.get("shared_expert", [])
        _, h = hidden_states.shape
        shared_merged_x = None
        if self.low_latency_tp:
            hidden_states_share = None
            if self.n_shared_experts > 0:
                if self.enable_shared_pipeline and not is_prefill:
                    shared_merged_x = self.shared_expert_gate_up(
                        hidden_states, shared_expert_stream, shared_expert_events)
                else:
                    hidden_states_share = self.forward_shared_expert(
                        hidden_states, shared_expert_stream, shared_expert_events)
        elif is_prefill:
            # With MegaMoE the shared experts run inside the operator, so the
            # model-side computation must be skipped to avoid double counting.
            if self.n_shared_experts > 0 and not self.enable_mega_moe:
                hidden_states_share = self.forward_shared_expert(
                    hidden_states, shared_expert_stream, shared_expert_events)
            else:
                hidden_states_share = None
        else:
            record_stream(self.enable_multi_streams, hidden_states, shared_expert_stream)
            record_event(self.enable_multi_streams, shared_expert_events, 0)

        # compute gating score
        if self.platform_version == PlatformVersion.ASCEND_950:
            logits = torch_npu.npu_fused_matmul(hidden_states.view(-1, h), self.gate.weight, fused_op_type="16cast32")
        else:
            logits = self.gate(hidden_states.view(-1, h).to(torch.float32))
        topk_idx, topk_weight, _ = OpKernel.gate_topk(
            self, logits, input_ids, image_mask, is_prefill=is_prefill
        )
        if self.force_eplb:
            topk_idx = cur_topk_list
        topk_idx = topk_idx.to(torch.int32)

        if self.low_latency_tp:
            return self.moe_infer_tp(
                hidden_states, topk_idx, topk_weight, hidden_states_share,
                moe_events, engram_resource_events, shared_expert_stream, shared_merged_x)

        # MOE EP
        if is_prefill:
            if self.enable_mega_moe:
                return self.megamoe_backend.prefill(
                    self,
                    hidden_states,
                    topk_idx,
                    topk_weight,
                )
            return self.moe_infer_double_routing(
                hidden_states, topk_idx, topk_weight, hidden_states_share,
                shared_expert_events, prefill_moe_global_chunks)
        else:
            return self.moe_infer_dispatch_combine(
                hidden_states, topk_idx, topk_weight, shared_expert_stream,
                moe_events, engram_resource_events=engram_resource_events)
```

</details>

## 设计决策

通用决策是以选定后端 ABI 为终点，逐条追踪值与 scale 的表示链。本文 recipes wrapper 的 pack helper 统一三条 scale 入口的最终算式，但各入口先独立恢复轴。selector 决定调用谁，context 决定资源，prepare/run 决定表示，三个层次分别核验。外部框架可以采用其他布局与编码，只能迁移这种配对检查方法，不能假设 int16 方案即插即用。

## 预防

保留每个参数的 scheme、加载阶段、轴标签、表示变换前字节和对应权重；本文 wrapper 还需保存 pack 前字节。修改 transpose/flatten/view/transform 时逐条复核 routed、shared 和 activation，不凭 dtype 名称合并审查。

## 验证信号

- [来源平台：950（仅源码目标，未上板）；证据等级：artifact_verified，静态源码] routed、条件化 MXFP8 shared 与 activation 在交付前进入同一成对算式，前置轴恢复不同。
- [来源平台：950（仅源码目标，未上板）；证据等级：artifact_verified，静态源码] 参数创建、post-load、shape guard、transform、buffer 写入和消费者有逐字完整函数证据。
- [来源平台：950（仅源码目标，未上板）；证据等级：artifact_verified，静态源码] context、容量/空 rank、registry/selector 与模型入口的静态调用闭环已恢复。

未执行量化、外部 ABI、数值、图或性能验证；保持 draft，未生成 verified 事件。

## 部署验收

待执行：核对真实外部签名，记录三条 scale 链的字节对与对应权重；同输入/路由/量化对照普通 GMM；覆盖空 rank、容量边界与特殊值；单独验收通信完成、图与生命周期。保留原始误差和失败样例，不改验收容差掩盖表示问题。

## 坏实践

把 E8M0 view 当 int16 pack、用加载前 shared scale 通过加载后布局分支、对 routed 盲抄 shared transpose、只改 buffer dtype 让 copy 通过，或以注册成功当数值通过，都跳过了关键对应关系。

## 失效边界

首要未决项是外部 kernel schema 与 signed int16 的实际读取。transform 内部布局/alias、特殊指数编码、奇数末维、维度整除条件和图支持未知；无真实故障、修复成功或收益证据。权重释放边界见[生命周期卡](../runtime/deepseek_v41_deepgemm_prefill_weight_release_lifecycle.md)。
