---
type: Operator
title: "RmsnormBiasInt8 A2/A3 Direct Invoke 算子知识"
description: "闭合独立INT8 RMS仿射和1024量化slice，精确记录K小于1024逻辑范围、量化padding、950待验证及真实字节和精度边界。"
tags: [task.implementation, task.lookup, topic.memory, topic.precision, topic.programming_model]
status: draft
sources:
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/norm/rmsnorm_bias.md
    role: primary
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/rmsnorm_bias.py
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/norm/rmsnorm_bias.py
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/utils/triton_utils.py
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/__init__.py
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/__init__.py
    role: supporting
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/__init__.py
    role: supporting
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/setup.py
    role: supporting
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/build_tools/torch_wheel.py
    role: supporting
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md
    role: supporting
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json
    role: supporting
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/.github/workflows/pr-test-kernels.yml
    role: supporting
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/.github/workflows/pr-test-kernel-group.yml
    role: supporting
created_at: "2026-11-09T10:16:20Z"
updated_at: "2026-11-09T10:16:20Z"
platforms: [a2, a3]
cann_versions: ["9.1.0"]
---

# RmsnormBiasInt8 A2/A3 Direct Invoke 算子知识

## 算子速览

精确入口 `sgl_kernel_npu.implementation.triton.norm.rmsnorm_bias.rmsnorm_bias`，冻结quant_scale 非None。每行直接FP32 RMSNorm、逐通道乘weight加bias，再逐通道量化并饱和INT8。该唯一精度域Host/Device全部闭合，无dot/Cube/MIX，选VV。

draft保留无输入guard/资源与整数域、固定slice的逻辑范围和无运行边界；量化/浮点其它域独立任务不合并。已有[API合同](../../../../apis/sgl_kernel_npu/sgl_rmsnorm_bias.md)全文读并链接。

## 接口与语义

### 计算语义

A=FP32(input)。
`Y=A*1/sqrt(sum(A²)/H+eps)*weight+bias`；Q=saturate_cast_int8(Y*quant_scale+quant_offset)，量化乘加FP32路径并以实际cast合同转换，公开Torch参考向零截断，未宣称跨后端位同。
返回新output，input不修改。有限输入/中间值域仍需避免FP32溢出。

### 输入、输出与属性

| 项 | 合同/真实读取 |
|---|---|
| input | 连续NPU二维[B,H]，B/H>0，FP16/BF16/FP32；Direct无完整guard |

| weight/bias | 同device连续[H]浮点向量，dtype可按公开建议与input相同；裸指针按列读，不自动广播/contiguous |
| eps | 推荐正有限，Direct不检查 |
| quant | scale/offset均连续同device浮点[H]，scale非None；未自动拒绝缺offset |
| output | int8新[B,H] |

### 入口与版本

Direct签名(input,norm_weight,norm_bias,eps,quant_scale=None,quant_offset=None)。冻结predicate显式选INT8，publicauto/triton仅转发，torch_native外部reference不填Device。SGLcommit `dda6d36b0cdb4081e102d14c0a2fb276fc416e69`，CANN9.1.0为README/CI版本配置，非本次环境；未固定完整Tritonbinary。
公开arch22支持，arch35待验证；950仅draft源码路径/未验证，未称明确不支持或已支持实测。

## Host/Launcher 执行流程

### 参数校验与前处理

helper先取P，再读取input.shape[0/1]；K=nextpow2(H)、COL=1024、n=min(B,P)。SCALE=quant_scale非None，分配output，launchgrid(n,)。无shape/stride/dtype/device/vector长度/eps/quantoffset检查，也无B0快速返回（公开正B合同外grid0行为未证）。不做输入连续化/设备值回Host。

### 参数、Workspace 与生命周期

输出allocation BH B；无请求方workspace/POD/ACLNN、无中间GM统计。helper无参cache/current_device、双核数assert，未绑定inputdevice；device相容由调用方确保。无显式stream/wait/warp/stage，Tensor存活/异步释放归框架。所有输入只读，新output与输入不别名。

### 启动图与失败传播

import→helper→shape/constexpr→SCALE域输出分配→单JITKernel→返回。没有CPU/外部Torch核心数学fallback；框架仅empty/getproperties。异常直接传播；包原生库导入仅前提。

## Route 与参数设计

### 分核与资源计算

n=min(B,P)>0；program p处理行p+j*n<B，所有行唯一。cols=arange(K)、cols<Hmask/other0；weight在row循环外读一次，每programH项，bias在每row读。全K行FP32平方归约、分母真实H，不除K。最后按COL=1024切已得到的Y，store再maskH；不是先把norm分块，整行资源依然随K。

### Route 选择

唯一R-001=SCALEtrue；其它精度域在该冻结predicate不可达，由独立job生产。input三dtype和合法weight/bias/quantdtype组合控制图相同，具体数值promotion和storetype不同。

### 模板/实现执行矩阵

| Route | frozenflag | tile | output |
|---|---|---|---|
| R-001 | SCALE=true | K=nextpow2H,quantCOL1024 | INT8 |

无autotune/dot/Cube/AIC/MIX节点；全部自有算法Vector/reduction，compiler物理layout不伪造。

### 隐藏性能 Guard

无UB容量/宽度上限guard，K可大；地址row*H/步进未显式int64转换。B0/H0或不连续均不属证明域。
按常规slice逻辑范围契约，最后块起点floor((H-1)/COL)*COL，要求start+COL≤K。COL是二次幂，K=nextpow2H，H>0时K≥COL足以保证全部slice在K内，即使H非COL倍数也由storemask裁尾；K<COL时首extract尺寸超过buffer逻辑长度，maskstore不能补救。这是静态尺寸推导，非编译/故障复现；actualal.slice工具链合同仍外部。

### POD/ABI

| 参数 | 类别/消费 |
|---|---|
| input_ptr | runtime输入→maskedload |
| norm_weight_ptr/norm_bias_ptr | runtime输入→weight预读/bias每行读 |
| quant_scale_ptr/quant_offset_ptr | runtime可None，COLmaskedload |
| output_ptr | runtime新输出→INT8store |
| batch_size | runtimeB→row循环 |
| eps | constexpr→sqrt分母 |
| hidden_size | constexprH→mask/行步长/除数 |
| BLOCK_SIZE/COL_BLOCK_SIZE | constexprK/1024→arange/quantloop |
| SCALE/grid | constexprtrue/(n,) |

无自定义POD序列化/字节offset；JIT ABI/整数位宽外部，未编造。

### Route 源码闭包

完整122行实现、public转发/helper已读；浮点/quant域分别冻结。根setup→stage_runtime完整Python包→build_wheel/setup_refactor；norm/backendinit无Device。无外部核心Torch数学，sqrt/reduction/cast/al.slice为明确primitive边界，物理UB/register不猜测。

## Kernel 实现

### 公共执行流程

weight预读→每行FP32平方和/归一化→weight→bias→COLslice量化；每行独立，无共享写。

### Route R-001：直接RMS仿射与INT8

#### 适用条件

##### 选择证据

冻结SCALE=true，B/H正、输入连续及上述向量长度/设备合法。额外slice必要范围以K/COL关系说明，不把所有H无条件推荐。

#### Device 数据流

##### 函数级调用链

`rmsnorm_bias→helper→rmsnorm_bias_kernel→load/toFP32/sum/sqrt/mul/add→al.extract_slice/quantcast/store`。无其它自有Kernel。

##### 源码等价伪码

cols=arangeK，maskcols<H；w=loadother0。对行r=p+j*n：a=loadxother0 ; a=a.float32；v=sum(a*a)/H；y=a/sqrt(v+eps)*w+loadbiasother0；for c0=0;c0<H;c0+=COL，sliceY[c0:c0+COL]→FP32*loadscale+loadoffset→saturateint8→mask(c<H)store。行offset+=nH。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/流量 |
|---|---|
| a/square/y | 各K FP32逻辑，单张量4K B，不等实际峰值 |
| weight/bias | K逻辑lane，合法H；weight每program一次、bias每row一次 |
| input | inputBHdx读 |
| quanttile | COL1024，scale/offset各COL逻辑lane，输出INT8 |
| workspace/physical UB | 无显式分配，compiler复用/spill外部 |

##### 分层内存布局

`GMinput→FP32rowSSA→mean-square/rstd→affine→COLslice quant→GMoutput`。没有GMvariance/rstd，不物化归一化中间。

##### 字节账与复用顺序

令dx/dr/dw/db/ds/do为各Tensor元素字节宽，n=min(B,P)。本域Kernel逻辑GM总 BH*(dx+1+db+ds+do)+nHdw B。bias在每row读，weight按nprogram预读。无cache/physicalDMA事务保证；输入只读、输出新分配，异步存活/stream交接归framework，workspace无。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| program间 | 行余数唯一，无atomic/barrier |
| row内 | SSA依赖交compiler，无显式物理event |
| H尾 | input/weight/bias loadmask/other0，normpad0、除H；output同mask |
| 残差 | 无residual |
| FP32 | 平方归约、1/sqrt、affine；finite输入仍可溢出，eps不guard |
| quant padding | scale/offset maskedload未指定other；无效lane量化中间值不能当0，不store且不进入后续归约 |
| quanttail | slice先按COL取满再maskstore，K<COL逻辑越范围条件明示；int8saturate/截断外部 |
| lifetime | 无自有工作区/共享中间，输入输出异步持有依框架 |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| 完整Kernel | [Device](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/rmsnorm_bias.py#L10-L75) |
| Direct | [launcher](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/rmsnorm_bias.py#L81-L122) |

## 算子特定优化

### Trick T-001：weight在行轮转循环外预读

#### 触发与源码依据

[连续源码](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/rmsnorm_bias.py#L25-L31)：

```python
    row_start = tl.program_id(0)
    row_step = tl.num_programs(0)
    cols = tl.arange(0, BLOCK_SIZE)
    valid_mask = cols < hidden_size
    norm_weight_values = tl.load(norm_weight_ptr + cols, mask=valid_mask, other=0.0)
    input_offsets = row_start * hidden_size + cols
    for i in tl.range(row_start, batch_size, row_step):
```

#### 机制与设计原因

n个program各读H个weight后复用多个行，逻辑weight读nHdw而非BHdw；bias仍每行读，不能扩大共享结论。未测性能收益。

#### 迁移边界

input/向量连续裸址、groupfree逐行合同，参数存活至异步结束；换stride/布局须重审。

#### 错误做法

把bias也写成循环外预读，或用n=P而忽略B<P。

### Trick T-002：整行统计后按固定列slice转换

#### 触发与源码依据

[连续源码](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/rmsnorm_bias.py#L44-L51)：

```python
        if SCALE:
            block_cols = tl.arange(0, COL_BLOCK_SIZE)
            for block_offset in range(0, hidden_size, COL_BLOCK_SIZE):
                col_indices = block_offset + block_cols
                valid_mask2 = col_indices < hidden_size
                block_buffered_values = al.extract_slice(
                    buffered_values, (block_offset,), (COL_BLOCK_SIZE,), (1,)
                )
```

#### 机制与设计原因

norm仍处理整K行，只有后续quant转换使用COL切片，减少转换阶段的逻辑tile而非给norm提供列分块；slice边界必须先证。

#### 迁移边界

COL1024、K=nextpow2H、laststart+COL≤K与有效Hstoremask必须同时保证。

#### 错误做法

认为maskstore能保护超K的extractslice，或把COL当norm常驻长度。

## 模板与实现对比

本卡仅INT8精度冻结，另域独立目标；没有未知自有数学节点。无残差/第二返回。与文档缓存/平台声明区分源码事实，未用Torchreference代替实现。

## 平台差异

本卡A2/A3归属arch22。公开arch22支持、arch35待验证；950卡仅draft同源码路线，不能写已支持实测或明确不支持。README/architectures提供产品归属。自有body无hardwarebranch，CANN9.1.0 CI为配置非本次运行/physical资源或compiler一致性证明。

## 限制与失败边界

无完整参数guard，裸连续storage/同device/合适dtype/正H/B/eps是前提；helpercache与JIT整数/资源容量未guard。K<COL的slice静态超逻辑长度条件可复验，未执行上游或修源。无构建、运行、测试/校验或性能/physical分配结果，draft不作无条件安全推荐。

## 源码索引

### 链路索引

| 阶段/源码 | 符号 | 事实 |
|---|---|---|
| [公开合同](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/norm/rmsnorm_bias.md) | `rmsnorm_bias` | RMS/仿射/输出dtype/平台范围 |
| [Direct/Device](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/rmsnorm_bias.py) | `rmsnorm_bias/rmsnorm_bias_kernel` | 完整122行；冻结SCALE=true |
| [公开适配](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/norm/rmsnorm_bias.py) | `_triton_impl` | 转发不guard |
| [设备helper](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/utils/triton_utils.py) | `get_device_properties` | current_device、无参cache、两核数assert |
| [import边界](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/__init__.py) | `_load_sgl_kernel_npu` | torch_npu/原生库与vendor初始化 |
| [backend包](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/__init__.py) | `module init` | 懒加载包，无另一Device节点 |
| [norm包](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/__init__.py) | `module init` | 无附加启动节点 |
| [构建入口](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/setup.py) | `main` | 完整Python wheel路径；本次未构建 |
| [源码打包](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/build_tools/torch_wheel.py) | `stage_runtime/build_torch/build_wheel/setup_refactor` | 复制完整Python包、原生运行库与wheel |
| [平台/包说明](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md) | `REFACTOR/arch22/35 mapping` | 全部Python实现包含、产品映射、CANN9.1.0构建例 |
| [产品映射](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json) | `2201/3510` | a2/a3/950对应构建族 |
| [版本配置](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/.github/workflows/pr-test-kernels.yml) | `test-norm-ops` | CANN9.1.0/a3/950配置，非本次运行 |
| [CI消费](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/.github/workflows/pr-test-kernel-group.yml) | `run-kernel-group` | 对应版本容器/测试组参数 |

### 实现复用检查

冻结117/legacy同主题API已全文读并链接，独立冻结rmsnorm_bias INT8只创建对应两平台卡，未覆盖API。全部同repo固定source唯一primary，无verified。
