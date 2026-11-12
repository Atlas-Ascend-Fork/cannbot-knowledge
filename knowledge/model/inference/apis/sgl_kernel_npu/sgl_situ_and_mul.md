---
type: API
title: SGL SiTU 浮点激活与分组有效前缀
description: 说明 situ_and_mul 的 gate/up 饱和公式、两种 group 编码、未写 padding 和 int32 行调度边界。
tags:
- task.implementation
- topic.precision
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/activation/situ_and_mul.md
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/activation/situ.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/situ_and_mul.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/activation/situ_and_mul.py
  role: header
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/utils/triton_utils.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/utils/triton_utils.py
  role: implementation
created_at: '2026-11-08T11:03:33Z'
updated_at: '2026-11-10T07:03:17Z'
platforms:
- a2
- a3
- '950'
aliases:
- situ_and_mul
---

# SGL SiTU 浮点激活与分组有效前缀

## 调用入口

```python
from sgl_kernel_npu.operators.activation import situ_and_mul

def situ_and_mul(
    x: torch.Tensor,
    group_list: Optional[torch.Tensor] = None,
    group_list_type: Optional[int] = None,
    beta: float = 4.0,
    linear_beta: Optional[float] = 25.0,
    *,
    impl="auto",
) -> torch.Tensor:
    ...
```

## 数学语义

输入 `[...,2d]` 的前半为 g、后半为 u。计算 `beta*tanh(g/beta)*sigmoid(g)`，再乘 `L*tanh(u/L)`；`linear_beta=None` 时第二项直接使用 u。全程 FP32，输出转换为输入类型；这里不执行量化。默认 beta=4、linear_beta=25。

输入支持 FP16/BF16/FP32 strided Tensor，d>0。输出为同设备新连续 Tensor `[...,d]`。非连续输入在 Triton 路径可能发生复制，测量时需计入成本。

## Group 编码和未定义区

前导维展平为 N 行；不传 group 时全部有效。连续非空 `group_list: [E]` 为同设备 int32/int64，type=0 取最后一项作为有效总数，type=1 对逐 expert 计数求和。累积编码不含起始哨兵；各项非负且累积编码单调，必须保证总数位于 `[0,N]`。

只定义输出的有效前缀，padding 不保证清零。group 总数在设备端取得，不回读主机检查数值。空输入不启动 kernel；group 总数为零时没有输出元素可供消费。

## 调用与实现边界

auto 与 triton 指向同入口且不回退。公共检查覆盖偶数末维、group dtype/编码及空 group；dtype、布局、设备和有限正标量仍由调用方保证。Triton 额外要求 `N <= 2**31-C`，C 为当前向量核数；行寻址使用 int64，不代表可取消该调度容量限制。

上游声明 arch22/arch35 支持，其中硬件复测范围为 A3 和 950，A2 没有单独验证。torch_native 支持独立 CPU 数学参考，但分组总数会同步主机，不宜放进图捕获。比较时只取有效前缀，并用适合 dtype 的容差，不比较未写 padding。

## 旧activation模块的非量化实现与迁移边界

同一固定commit还保留 `sgl_kernel_npu.activation.situ.situ_and_mul`，签名为(x,group_list=None,group_list_type=None,beta=4.0,linear_beta=25.0)，没有impl参数或registry。这里保存旧自有Host/JIT可读事实；**不把本卡新版公开入口的平台声明、检查与source闭包传播给旧模块**。旧入口数学与Htile主循环可复用比较，但完整Host/metadata语义并不等价，不新建重复数学Operator。

### 数学、装饰器与不同Host

旧JIT `activation.situ._situ_and_mul_kernel` 与新版同名实现均有四个autotune候选BLOCK_H=1024/2048/4096/8192，multibuffer=True，key=[HALF_COLS,HAS_GROUP_LIST]。两者都按输出Htile分别load gate/up并转FP32，计算beta*tanh(g/beta)*sigmoid(g)，启用linear_beta时再乘L*tanh(u/L)，否则乘原up；store转输入dtype。没有量化、amax、scale、tl.dot或Cube。primitive近似、融合/最终cast舍入及四候选赢家仍由外部compiler/autotune决定，没有固定性能或位级相同证明。

| 项 | 旧activation.situ.situ_and_mul | 新implementation.triton.activation.situ_and_mul |
|---|---|---|
| registry/共享检查 | 无；自身检查有group时type0/1、末维偶数、group int32/int64 | 公共operators wrapper先检查同类条件并拒绝empty group；直接调用implementation不会执行该公共wrapper |
| 展平与行布局 | x.reshape(-1,h)，不.contiguous | 先计算rows=x.numel()//h，再reshape(rows,h).contiguous |
| 返回shape | empty([N,h/2])，最后reshape回原前缀 | 直接分配原前缀+h/2的新连续Tensor |
| 空N | 无Host短路，仍分配/查询helper/launch | 非空group等公共检查后，rows==0提前empty返回，不查设备/不launch |
| 大N | 无显式调度上限检查 | max_rows=INT32_MAX-(AIV-1)=2**31-AIV，超过抛ValueError |
| group E | shape[0] | numel() |
| count逻辑向量A | int64:ceil(E/8)*8；int32:ceil(E/16)*16，逻辑字节数分别为8A/4A，均按64字节粒度向上对齐（非固定64字节） | next_power_of_2(E) |
| cumulative读取 | **GL[E]** | GL[E-1] |
| None group | 传x_2d占位，E=A=1/HAS_GROUP_LIST=False，不读占位ptr | 同样跳过group读取 |
| helper | 旧utils.triton_utils | implementation.triton.utils.triton_utils，独立函数/cache对象 |

旧reshape可能复制，也可能保留可view的行间padding。Device不收stride并按row*h访问，所以“reshape成功”不证明packed；新版的.contiguous正是额外布局保证，不能将新版strided输入合同直接套给旧入口。两者均不在此Host实现中完整检查X dtype/设备/finite标量，公共docstring的要求仍是调用方合同。beta=0或启用的linear_beta=0在构造Python倒数时有除零终点，None禁用up饱和而非传0。

旧cumulative[E]在名义1D E项视图之外，发生在row guard前；不能称为“带起始sentinel”合法合同，也不推定读值/后续确定运行轨迹。旧count读取A个lane、mask<E且other=0，各项转int32后sum；较大int64及和可窄化/溢出，R没有夹到N。旧A未自动补成POT，编译shape准入需实际primitive证据。新公共合同的E非空、R范围及cumulative末项规则不消除旧body的真实静态边界。

### 旧JIT完整数据流与资源

旧JIT有3个runtime Tensor ptr，N_ROWS为runtime，TOTAL_COLS=h、HALF_COLS=d、E/A、GROUP_LIST_TYPE、NUM_CORES=P、HAS_GROUP_LIST、BETA/INV_BETA、DO_LINEAR_BETA、LINEAR_BETA/INV_LINEAR_BETA及autotune注入的BLOCK_H为constexpr。Host grid=(P,)；取P=get_device_properties()[1]，没有workspace/POD序列化或第二Kernel。

```text
R = N if not HAS_GROUP_LIST
    else load(GL[E]).int32 if type==0
    else sum(masked_load(GL[0:A],mask<E,other=0).int32)
n=(R-1)//P+1
begin=pid*n
if begin>=R:return
end=min((pid+1)*n,R)
for row in [begin,end):
    off=int64(row)*h
    for start in range(0,d,BLOCK_H):
        c=start+arange(BLOCK_H);mask=c<d
        gate=load(x+off+c,mask,other=0).float32
        up=load(x+off+d+c,mask,other=0).float32
        y=beta*tanh(gate/beta)*sigmoid(gate)
        y*=up if linear_beta is None else L*tanh(up/L)
        store(out+int64(row)*d+c,cast_xdtype(y),mask)
```

后续数据流以group读取成功、0<=R<=N、调度整数可表示和packed storage为条件；不是跨越GL[E]缺陷的安全支持承诺。合法R>0为连续row段ceil(R/P)分核，非grid-stride；R=0不写任何输出。row地址int64不取消int32 R/分核容量问题。列tail两load/store同mask，invalidlane填0；没有整行常驻或量化1536尾slice约束，因而大d可按BLOCK_H分片，但不保证任意shape可编译。

| 旧入口资源 | 字节/生命周期 |
|---|---|
| X/out | 名义2Nd*dx与Nd*dx B；有效前缀读2Rd*dx、写Rd*dx B |
| padding | out后N-R行empty未写，不能读取；R>N将驱动分配外访问 |
| 当前Htile | gate/up/y等各BLOCK_H个FP32元素，各4*BLOCK_H B逻辑payload，可由compiler复用 |
| group | count每个P program读E*dg B，转int32逻辑4A B；cumulative每program读1项但名义越视图 |
| 临时/物理内存 | reshape可能有Torch copy；无自有workspace、UB/L1/L0/queue/event分配，逻辑向量不等于物理峰值 |

有效GM逻辑流量3Rd*dx，加count的P*E*dg或cumulative的P*dg；所有program先取得R再early-return。multibuffer=True不是确定双buffer字节账。各row/tile独立，没有atomic、barrier或跨stream同步；copy/launch与Tensor生命周期归Torch/Triton，输入/group/out需保持至当前流完成，没有alias/并发修改保护。

旧/新get_device_properties各自为零参数functools.cache，首次读当前device的AIC/AIV核数并assert两者>0；两入口只用AIV。切设备不自动刷新其缓存，影响P与新版容量guard；不是group内容缓存，也不能由旧helper的已缓存结果推定新helper已缓存。包及runtime环境仍依赖torch_npu/实际NPU，不能借torch_native的CPU参考支持给旧Triton入口。

### 复用与关联

[新版A2/A3完整Device卡](/model/inference/operators/direct/nn/activation/sgl_situ_and_mul.md)与[950卡](/model/inference/operators/direct/nn/activation/sgl_situ_and_mul_950.md)保存新版四Htile×group×linear路线。对满足packed/count整数域的相同输入可以复用SiTU FP32数学比较；旧cumulative、empty/dtype/stride/大N与cache路径须单独分析，不以函数同名判完全alias。

[旧SiTU INT8与situ浮点Reference](/model/inference/apis/sgl_kernel_npu/sgl_legacy_situ_int8.md)另保存同文件的整行量化JIT与situ(...,need_quant=False)，并明确situ_and_mul_quant的False/宽度超限实际抛NotImplementedError；它不是本Htile浮点函数的自动量化或回退。所有这些补充均为静态阅读，未执行编译、数值、真机或性能验证。


## 固定来源与验证状态

- [activation/situ_and_mul.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/activation/situ_and_mul.md)
- [构建架构与产品映射](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md)及[SDK架构表](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json)。文档arch22对应本版本2201构建族A2/A3，arch35对应3510的950；具体子接口限制以上文为准。

- [python/sgl_kernel_npu/sgl_kernel_npu/activation/situ.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/activation/situ.py)（implementation）：用于旧/新实现差异与helper边界。
- [python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/situ_and_mul.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/situ_and_mul.py)（implementation）：用于旧/新实现差异与helper边界。
- [python/sgl_kernel_npu/sgl_kernel_npu/operators/activation/situ_and_mul.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/activation/situ_and_mul.py)（header）：用于旧/新实现差异与helper边界。
- [python/sgl_kernel_npu/sgl_kernel_npu/utils/triton_utils.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/utils/triton_utils.py)（implementation）：用于旧/新实现差异与helper边界。
- [python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/utils/triton_utils.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/utils/triton_utils.py)（implementation）：用于旧/新实现差异与helper边界。

本卡为固定提交的公开API契约蒸馏，未展开Host/Tiling/Device全链路。本次知识提取未执行编译、真机、数值或性能测试；上游报告的支持和用例结果不代表本次复测。
