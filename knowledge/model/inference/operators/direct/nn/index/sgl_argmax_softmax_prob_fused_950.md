---
type: Operator
title: SGL在线Argmax置信度融合 950 Direct Invoke 算子知识
description: 还原950上argmax_softmax_prob_fused的在线最大值/指数和合并、双标量输出、tile输入预算与row stride，保留非有限、空域和拓扑缓存边界。
tags:
- task.implementation
- task.lookup
- topic.speculative_decoding
- topic.compute.reduction
- topic.memory
status: draft
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/sample/argmax_softmax_prob.py
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/utils/triton_utils.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/tests/python/sgl_kernel_npu/test_argmax_softmax_prob.py
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/.github/workflows/pr-test-kernels.yml
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/.github/workflows/pr-test-kernel-group.yml
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/scripts/run_kernel_tests.sh
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/scripts/prepare_kernel_tests.sh
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/__init__.py
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/sample/__init__.py
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/setup.py
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/build_tools/target_provider.py
  role: supporting
created_at: '2026-11-09T11:54:03Z'
updated_at: "2026-11-10T07:06:47Z"
platforms:
- '950'
cann_versions:
- 9.1.0
---

# SGL在线Argmax置信度融合 950 Direct Invoke 算子知识

## 算子速览

| 项目 | 内容 |
|---|---|
| 实际入口 | sgl_kernel_npu.sample.argmax_softmax_prob.argmax_softmax_prob_fused，直接Python调用，非普通argmax接口 |
| 计算语义 | 每行流式合并最大值m、全局argmax及相对m的指数和s，输出argmax与该位置softmax概率1/s |
| 输入输出 | logits[B,V]末维连续，允许一般行stride；新输出int64[B]及FP32[B]，不改输入 |
| 执行类型 | 单Triton Vector节点，无Cube/dot、通信或跨program归约 |
| Kernel 路线 | R-001：program按行跨步，每行串行遍历词表块 |
| 核心资源 | GM输入与12B/行输出，逻辑长度C向量及m/s/arg状态，无[B,V]临时写回；实际UB/寄存器由编译器决定 |
| 来源闭包 | direct_implementation_closed：Host、核数缓存helper、唯一JIT body、打包与具体CI接线闭合 |
| 验证状态 | 来源报告910B3测量，CI配置A3/950；本次未编译、运行或数值复测，保留draft，不把配置/注释当验证事件 |

## 接口与语义

### 计算语义

对一行，初始化FP32 m=-inf、s=0及int64 arg=0。每个词表块转FP32后计算u=max(x)、m'=max(m,u)，再更新s'=s*exp(m-m')+sum(exp(x-m'))。块内候选为tl.argmax(x)+start；仅u>m才替换arg，最后m=m'。处理完全部有效V后返回(arg,1/s)。有限logits下，s是相对最终最大值的指数和，最大元素的分子为1，因此无需写完整softmax或从完整softmax再gather。

跨块相等最大值保持较早块的arg。块内调用tl.argmax(x,axis=0)，没有显式额外tie参数，具体primitive约定由匹配Triton提供；源注释期望与torch.argmax一致，固定测试包含跨块相等峰值。不能把该测试定义作为本次全部块内tie或NaN行为的实测证明。

数值适用域应首先采用有限输入。若首块全为-inf而后块含有限值，首步出现m-m'=-inf-(-inf)和x-m'的未定义差值；按通常IEEE传播推导s可先变NaN，后续乘0未必恢复。这里只记录源码的条件性非有限风险，不宣称已观察某个编译器的具体输出或错误。+inf/NaN以及全-inf行也没有显式特殊处理，不能从有限数据测试外推。

### 输入、输出与属性

| 参数 | shape/layout | dtype | 约束、默认值与语义 |
|---|---|---|---|
| logits | [B,V]，stride(1)=1，stride(0)透传 | 测试FP16/BF16/FP32 | 只读；Host仅断言二维和末维连续，不验证NPU、dtype、正维数或有限性 |
| block_v | None或调用方整数 | Python整型 | None按32768/element_size取初值；最后min(初值,next_power_of_2(V))；override不自动对齐或限到32KiB |
| argmax_ids | 新[B] | int64 | 每行一个词表位置，device同输入 |
| prob | 新[B] | FP32 | 每行该argmax位置的softmax概率，源码写1/s |

本文有效域B>0、V>0、匹配CANN Triton可接受的正tile宽度、合法输入存储及有限logits。用户override宜为正2次幂并符合目标编译资源；Host没有相关guard。源码docstring称any float dtype，但只在所列类型中有固定测试定义，不能据此保证FP64或其它类型后端可运行，也不能忽略转FP32对更高精度排序的影响。

### 入口与版本

无版本后缀Direct入口，只有一个JIT body。源模块整体明确报告Ascend910B3（A2）上的测量；test_argmax_softmax_prob.py被speculative组真实选中，A3/950×CANN9.1.0矩阵对其未设置跳过。平台范围为950：这是具体来源与接线证据，不是本次通过记录，也不保证任意安装wheel包含全部依赖。

包顶层导入torch_npu并加载libsgl_kernel_npu.so；sample.__init__未直接导出此函数，需从子模块导入。setup通过namespace打包，目标provider不允许覆盖已有common文件。准备脚本在未显式指定TRITON_ASCEND_WHL时为CANN9.1选择triton-ascend3.2.2，不能据此断言当前运行环境已安装该版本。

## Host/Launcher 执行流程

### 参数校验与前处理

Host先断言rank2/末维stride1，分配两个一维输出，然后取缓存Vector核数c并令G=min(c,B)。block_v=None时设C0=32768/logits.element_size()的整数商，否则直接用override；最终C=min(C0,next_power_of_2(V))。不复制或连续化输入，不分配全词表中间量，不补空行/空词表路径。自定义tile的类型、正值、2次幂和实际资源准入均未检查。

### 参数、Workspace 与生命周期

_num_cores以无参数lru_cache(maxsize=1)缓存get_device_properties()[1]；后者也以无参数cache查询首次当前NPU的num_aicore和num_vectorcore并要求均正。两层缓存键均不含device，切换设备不保证刷新拓扑；不据此推断一定产生错误结果或确定性能变化。

JIT收到三个Tensor指针、B、V、stride_b和constexpr C，grid G。无自有POD、workspace或手写UB分配；不能把32KiB输入tile预算解释成实际UB总量或完整JIT缓存键。输入和返回输出需保活至实际流计算完成；函数没有同步/事件返回或自己的record_stream，runtime和allocator实现为外部边界。

### 启动图与失败传播

| 节点 | Host 添加/启动 | entry/执行族 | blockDim 与 POD | 输入→输出 | workspace slice |
|---|---|---|---|---|---|
| N1 | _argmax_prob_kernel[(G,)] | _argmax_prob_kernel，编译Vector | G=min(c,B)；C constexpr；无自有POD | logits→argmax_ids/prob | 无自有workspace |

```text
Host断言 -> 分配int64[B]/FP32[B] -> 缓存核数/默认或override tile
 -> N1：program p处理p,p+G,...；每行全部词表块由同一program串行合并
 -> 返回两Tensor，caller按实际流依赖消费
```

无跨Kernel边、跨核中间缓冲或第二次归约。Python/编译/launch错误直接传播，无普通torch实现回退。输出在launch前分配不证明Device已经写入；异步错误和具体诊断不由该源码确定。

## Route 与参数设计

### 分核与资源计算

G为正有效域内，每个p∈[0,G)处理row=p+kG<B，因此每行只有一个program写两个输出。行基址row*stride_b，词表偏移start+arange(C)，仅offs<V的lane读取，其余置-inf。row stride按元素而非字节，不要求输入行pitch等于V；有效重叠只读行不由该算法额外写坏，但仍须是框架允许的合法view。

默认FP16/BF16取C0=16384，FP32取8192，再限制到next_power_of_2(V)。默认C*element_size<=32768只约束输入逻辑tile；x转FP32后为4C的逻辑表示量，指数/归约及自动多缓冲可能增加真实资源。override仅受词表向上2次幂限制，可以超过默认输入预算。

### Route 选择

| 顺序 | Route | Key/模板 | 精确选择条件与优先级 | 不适用去向 |
|---:|---|---|---|---|
| 1 | R-001 在线三状态合并 | 唯一JIT、C constexpr | Host解析None/override后总走同body；B/V正与地址/tile合法为本文使用前提 | 无其它实现族或fallback |

```text
rank2且stride1断言 -> 输出分配 -> G=min(c,B)
C0=(32768/element_size) if block_v is None else block_v
C=min(C0,next_power_of_2(V)) -> 同一_argmax_prob_kernel
```

### 模板/实现执行矩阵

| Route | key/selector | dtype/shape/platform 完整命中条件 | 执行拓扑与 Kernel 节点 | 实际模板/body | 内存与同步特征 | tail/fallback |
|---|---|---|---|---|---|---|
| R-001默认tile | block_v=None | 950范围，FP16/BF16/FP32测试类型；本文B/V>0、末维连续/合法行stride/有限输入 | 单N1 | 同JIT，C=min(32768/e,P2(V)) | 逻辑资源以C参数化，逐行独占 | 词表末块-inf；无fallback |
| R-001自定义tile | block_v非None | 同一body/ABI/递推公式/精度/tail；C改变归约分组与重标定时点，不保证概率逐位一致；另需编译器接受正tile及资源 | 同N1 | C=min(override,P2(V)) | 不继承默认32KiB输入预算，真实物理量不可见 | Host不替调用方对齐/检查 |

这里两项只解析同一body的tile参数，不产生不同算法、同步图、队列布局或新Kernel路线；不能为每个C数值虚构不同实现族。

### 隐藏性能 Guard

| Guard | Host/Tiling 条件 | Device/资源原因 | 影响 Route | 不满足时去向 | 源码符号 |
|---|---|---|---|---|---|
| 末维连续 | rank2且stride(1)==1 | 词表按+offs寻址 | R-001 | Python断言失败 | Host首断言 |
| tile输入预算 | 仅None时C0=32768/e | 控制单tile输入逻辑字节，不是UB总账 | R-001 | override未按该预算拒绝；编译资源仍外部 | _TILE_BYTES/Host |
| tile不宽于词表P2 | C=min(C0,P2(V)) | 避免小词表使用完整默认大tile | R-001 | 无替代body | Host最后min |
| override正值/P2 | 无guard | arange/循环及lowering须接受C | R-001 | 外部编译/launch边界，不造特定错误 | JIT BLOCK_V |
| B/V空域与非有限 | 无guard/特殊分支 | grid可为0、词表可无迭代；-inf差值可未定义 | R-001 | 未证明安全空路径/非有限保证 | G、循环和exp |
| 核数/切设备 | 仅首次helper查询均正 | grid用缓存Vector核数 | R-001 | 首次查询失败断言；切卡不自动刷新 | _num_cores/get_device_properties |

### POD/ABI

无自定义二进制POD，真实参数偏移、打包、thread和UB/spill由匹配编译器决定。

| 结构 | 字段 | 类型/位宽 | ABI 布局 | 单位 | Host/launcher producer | Device consumer | 边界 |
|---|---|---|---|---|---|---|---|
| JIT实参 | logits_ptr | 输入浮点Tensor指针 | 编译器决定 | 元素地址 | logits透传 | load(logits+row*stride_b+offs) | 转FP32后计算 |
| JIT实参 | argmax_ptr | int64输出指针 | 编译器决定 | 元素 | torch.empty(B,int64) | store(...+row,arg) | 每行一写 |
| JIT实参 | prob_ptr | FP32输出指针 | 编译器决定 | 元素 | torch.empty(B,float32) | store(...+row,1/s) | 每行一写 |
| JIT实参 | B | shape整型 | 编译器决定 | 行数 | logits.shape[0] | tl.range(p,B,G) | Host不拒绝0 |
| JIT实参 | V | shape整型，源码未标constexpr | 编译器决定 | 词表元素数 | logits.shape[1] | range(0,V,C)、mask | Host不拒绝0 |
| JIT实参 | stride_b | stride整型 | 编译器决定 | 元素/行 | logits.stride(0) | row基址 | 不能替换为字节或V |
| constexpr | BLOCK_V | Host整数 | 编译期，无自有POD | lane数 | min(C0,P2(V)) | arange/词表步长 | 默认/override不同producer |
| grid | G | Host整数 | 启动配置 | program数 | min(_num_cores(),B) | num_programs(0)及row步长 | 非实际thread数/物理核绑定承诺 |

### Route 源码闭包

| Route | Key/selector | Host/Tiling producer | POD/参数 | Kernel entry/router 节点 | Kernel body/直接依赖 | 构建接线 |
|---|---|---|---|---|---|---|
| R-001 | 唯一JIT | argmax_softmax_prob_fused/_num_cores | 三指针、B/V/stride、C；无自有POD | _argmax_prob_kernel | tl.load/max/exp/sum/argmax/where/store，原语为编译器边界 | namespace包、active speculative CI测试 |

## Kernel 实现

### 公共执行流程

每个program轮流处理自己的行。每行重置m/s/arg，顺序加载词表块，转FP32，合并相对最大值的指数和及argmax；整行结束只写两个标量。没有完整logits副本、softmax张量或跨program合并。默认与override使用同一body、FP32精度和每块递推公式；改变C会改变块内求和分组、跨块合并次数及最大值重标定时点，不保证浮点运算顺序或概率逐位一致。

### Route R-001：词表分块的在线Argmax置信度

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Host | sample/argmax_softmax_prob.py | argmax_softmax_prob_fused | 默认/override解析后总launch同JIT | 单N1 |
| 核数helper | 同文件及utils/triton_utils.py | _num_cores/get_device_properties | 两层无device键缓存Vector核数 | G=min(c,B) |
| Device | 同文件 | _argmax_prob_kernel | row=p+kG，start按C推进，offs<V | 两个每行标量输出 |

#### Device 数据流

##### 函数级调用链

```text
argmax_softmax_prob_fused -> _num_cores -> get_device_properties [缓存]
 -> _argmax_prob_kernel[(G,)]
  -> program_id/num_programs -> 行循环
   -> 初始化m/s/arg -> 词表块循环
    -> masked load/Cast FP32 -> max -> maximum -> 两路exp/sum合并s
    -> argmax+start -> strict greater where更新arg -> 更新m
   -> store argmax -> store 1/s
```

##### 源码等价伪码

```text
伪码：for row=p; row<B; row+=G:
  m=-inf(FP32); s=0(FP32); arg=0(int64)
  for start in [0,V) step C:
    x=FP32(masked_load(logits+row*stride_b+start+arange(C),offs<V,-inf))
    u=max(x); new_m=max(m,u)
    s=s*exp(m-new_m)+sum(exp(x-new_m))
    chunk_arg=int64(argmax(x))+start
    arg=where(u>m,chunk_arg,arg); m=new_m
  out_arg[row]=arg
  out_prob[row]=1/s
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| GM logits | row*stride_b+start+lane | 每行V有效元素，逐C块 | FP16/BF16/FP32测试 | caller | masked load | N1完成前保活 | 末维stride1，行stride保留 |
| GM argmax | row | B*8B | int64连续新输出 | N1 | caller | caller持有 | 行独占，无atomic |
| GM prob | row | B*4B | FP32连续新输出 | N1 | caller | caller持有 | 行独占，无atomic |
| 逻辑x/指数向量 | 0..C-1 | x为C个FP32；其它表达式由编译器物化/融合 | FP32 | load/exp | max/sum/argmax | 当前词表块 | 不给物理UB占用 |
| 逻辑m/s/arg | 每program当前行 | 标量FP32/FP32/int64 | 标量 | 前块合并 | 后块/最终store | 整行 | 每行重置；每块递推 |
| workspace/Queue/L1/L0 | N/A | 无算子自有分配 | N/A | 外部runtime | 编译实现 | 框架边界 | 无手动TPipe/Matmul |

##### 分层内存布局

N/A：固定源码不手动分配UB、寄存器或队列。真实路径是GM行块→编译器局部向量/归约与标量状态→GM两个标量；32KiB是默认输入tile预算，不能画成真实UB分区。

##### 字节账与复用顺序

```text
e=logits.element_size(); C=min(32768/e if None else override,P2(V))
每行逻辑输入请求=V*e B，输出=8+4=12 B；全batch=B*(V*e+12) B
不产生[B,V]输出或中间GM张量；新输出Tensor有效容量=12*B字节，allocator物理对齐/池化另属框架
默认输入tile表示量C*e<=32768B；x转FP32的逻辑表示量=4C B
真实UB/寄存器/归约scratch/多缓冲/缓存线交易不可由该预算求得
workspace_total=0（本算子自有），编译器runtime内部分配不冒充已知
```

| 复用子区 | 写入者 | 读取者/消费点 | 下一次覆盖 | 同步或释放依据 | 安全条件 |
|---|---|---|---|---|---|
| x逻辑向量 | 每词表块load/Cast | max/exp/sum/argmax | 下一块 | 编译器数据依赖 | 不丢失当前块归约再覆盖 |
| m/s/arg | 当前块在线合并 | 下一块及最终store | 下一块/下一行重置 | 同program程序依赖 | 保持更新次序及FP32缩放口径 |
| 两输出行 | 当前行最后两store | 下游消费 | caller后续复用 | 等待实际提交流 | 分配后至完成前保活 |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| 行分配 | p+kG，互斥行 | program_id | 当前program | 两输出行 | 无跨program归约 |
| 载入 | tl.load mask/other=-inf | GM | FP32向量 | 当前块 | 仅offs<V有效 |
| 在线更新 | max/maximum/exp/sum数据依赖 | 前m/s及当前x | 后s/m | FP32标量状态 | 必须先算new_m及s再覆盖m |
| arg更新 | chunk_max>旧m | 当前块argmax | 全局arg | int64 | 跨块tie保留较早块 |
| 最终输出 | 两个普通store | 最终arg/s | caller等待流 | 新[B]缓冲 | FP32概率，不写完整softmax |
| 非有限 | 无专门处理 | -inf/inf/NaN输入或差值 | exp/归约 | s | 首块无有限峰值等域无保证 |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host producer | sample/argmax_softmax_prob.py | argmax_softmax_prob_fused | 行stride、两输出、G/C参数与launch |
| 核数缓存 | 同文件及utils/triton_utils.py | _num_cores/get_device_properties | 无device键的缓存与正核数断言 |
| Device body | sample/argmax_softmax_prob.py | _argmax_prob_kernel | 在线三状态、strict tie与tail mask |
| CI定义 | tests/python/sgl_kernel_npu/test_argmax_softmax_prob.py | dtype/shape/tie/stride测试 | 固定测试意图，非本次结果 |

## 算子特定优化

### Trick T-001：在线最大值重标定，省略完整softmax物化

#### 触发与源码依据

- 适用Route：R-001；有限输入、正V、有效tile和合法行stride。
- Golden 来源：[完整在线合并](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/sample/argmax_softmax_prob.py#L43-L62)。

```python
    for row in tl.range(row_pid, B, n_prog):
        base = row * stride_b
        m = tl.full((), float("-inf"), tl.float32)
        arg = tl.zeros((), tl.int64)
        s = tl.zeros((), tl.float32)
        for start in range(0, V, BLOCK_V):
            offs = start + tl.arange(0, BLOCK_V)
            mask = offs < V
            x = tl.load(logits_ptr + base + offs, mask=mask, other=float("-inf")).to(
                tl.float32
            )
            chunk_max = tl.max(x, axis=0)
            new_m = tl.maximum(m, chunk_max)
            s = s * tl.exp(m - new_m) + tl.sum(tl.exp(x - new_m), axis=0)
            chunk_arg = tl.argmax(x, axis=0).to(tl.int64) + start
            # Strict >: a tie keeps the earlier index, matching torch.argmax.
            arg = tl.where(chunk_max > m, chunk_arg, arg)
            m = new_m
        tl.store(argmax_ptr + row, arg)
        tl.store(prob_ptr + row, 1.0 / s)
```

#### 机制与设计原因

每次最大值上升都把前块s乘exp(m-new_m)，再加入当前块相对new_m的指数和；因此不同块可串行合并而无需保存全V的概率。argmax分子为1，最终只需1/s。源码每个有效logit只有一次逻辑load，没有[B,V]临时GM写回；不把它推广成某个硬件带宽或速度比例。

#### 迁移边界

- 适用：只需要top1位置及其softmax概率的置信度判断。
- 前提：接受FP32在线累加与其舍入顺序；调用方不需要完整概率或其它词表项。
- 失效：需要完整softmax、非有限输入保证、不同精度严格逐位等价时不能直接替代。
- 未验证：本次未执行编译、真机、数值或性能测试。

#### 错误做法

最大值变大时不重标前块指数和，或将本输出当作完整softmax。固定源有递推式，但没有本次硬件反例/测量；不编造具体性能收益。首块全-inf的风险按前述条件化说明处理。

### Trick T-002：输入字节预算结合小词表裁tile，并保留行stride

#### 触发与源码依据

- 适用Route：R-001；默认tile，或调用方提供经过资源核验的override。
- Golden 来源：[Host tile与stride生产](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/sample/argmax_softmax_prob.py#L89-L101)。

```python
    assert logits.dim() == 2 and logits.stride(1) == 1
    B, V = logits.shape
    argmax = torch.empty(B, dtype=torch.int64, device=logits.device)
    prob = torch.empty(B, dtype=torch.float32, device=logits.device)
    grid = (min(_num_cores(), B),)
    if block_v is None:
        block_v = _TILE_BYTES // logits.element_size()
    # A tile wider than the vocab only wastes unified buffer (and overflows it
    # once the single-iteration loop is unrolled).
    block_v = min(block_v, triton.next_power_of_2(V))
    _argmax_prob_kernel[grid](
        logits, argmax, prob, B, V, logits.stride(0), BLOCK_V=block_v
    )
```

#### 机制与设计原因

None时按输入element_size分配同一32KiB输入预算，使两字节输入可覆盖更多词表元素；再限制到小词表P2，避免V很小时仍使用默认大向量。传入logits.stride(0)允许直接消费词表截断view，不需要为了行pitch变大而复制整个输入。

#### 迁移边界

- 适用：末维连续、行pitch可变、正词表的逐行归约。
- 前提：区分输入预算和实际FP32/归约物理资源；override不会自动恢复该预算。
- 失效：末维stride非1被断言拒绝；不能将910B3的源注释资源经验推广为950实际UB布局。
- 未验证：本次未执行编译、真机、数值或性能测试。

#### 错误做法

把C*e=32KiB称为完整UB分配，或把自定义非P2/超大tile当作已过Host门禁。固定测试定义覆盖小V与截断row view，存在不代表本次执行成功。

## 模板与实现对比

| 对比维度 | R-001默认/override同实现 | 设计选择依据 |
|---|---|---|
| 命中条件/优先级 | 单JIT；只解析可选tile | 无其它body或fallback |
| 模板与dtype | C constexpr，输入转FP32 | 不伪造实际编译缓存键 |
| 循环与分核 | 行跨G步长、词表跨C步长 | 每行状态由一个program持有 |
| Queue/UB/寄存器 | 无手动分配 | 局部向量与标量由编译器放置 |
| 内存与复用 | 无全[B,V]临时，输出12B/行 | m/s/arg跨块复用 |
| 搬运/Vector API | masked load、归约、scalar store | 保留元素行stride和末块-inf |
| 同步/精度/tail | FP32更新、int64索引、程序依赖 | m先用于重标s再覆盖；跨块严格比较 |
| fallback/失败边界 | 断言或外部编译/runtime异常 | 无自动Torch、非有限或空域路线 |

## 平台差异

| 项目 | A2 | A3 | Ascend 950 |
|---|---|---|---|
| 支持状态 | 模块整体报告910B3上的此融合入口测量；本次未复核 | 具体active speculative CI配置；非通过记录 | 同CI配置且未过滤该文件；非通过记录 |
| Host/Launcher | 同Python Host，缓存Vector核数 | 同左 | 同左，切设备不保证刷新缓存 |
| Kernel/资源 | 同Triton body；32KiB源注释特指910B3经验 | 不据此确定实际UB/spill | 不把A2/A3资源经验当950物理配置 |

## 限制与失败边界

- 不输出完整softmax，也不是只输出argmax；概率对应最终argmax，必须保持在线指数和口径。
- Source docstring未限制所有浮点类型不等于全部dtype在NPU可运行，尤其转FP32后的精度影响不能省略。
- B/V=0、override非法或超实际资源没有安全Host分支；不编造具体编译错误码。
- 非有限输入没有special case，首块全-inf但后续有限时存在条件性递推污染风险；未执行构造反例测试。
- 两层拓扑缓存无device键；物理ABI/UB/寄存器/自动多缓冲是编译器边界，不从32KiB注释推导完整分配。
- 源头包含特定910B3测量描述，本卡未复测其精度或速度，不引用为本次性能验收结论；CI测试定义及各类型/stride/tie用例也不是实际运行记录。

## 源码索引

### 链路索引

| 链路阶段 | 文件 | 关键符号 | 支撑内容 |
|---|---|---|---|
| Direct Host/Device | python/sgl_kernel_npu/sgl_kernel_npu/sample/argmax_softmax_prob.py | Host/_argmax_prob_kernel/_num_cores | 完整算法、tile、行stride、Source910B3范围 |
| 设备helper | python/sgl_kernel_npu/sgl_kernel_npu/utils/triton_utils.py | get_device_properties | 当前设备属性与无参cache |
| 测试定义 | tests/python/sgl_kernel_npu/test_argmax_softmax_prob.py | 参数化/小V/行stride/tie测试 | FP16/BF16/FP32及边界意图 |
| CI平台版本 | .github/workflows/pr-test-kernels.yml | test-speculative-ops | A3/950 CANN9.1.0矩阵 |
| CI实际接线 | .github/workflows/pr-test-kernel-group.yml | run-kernel-group | 容器、准备与分组脚本 |
| 真实选组/过滤 | scripts/run_kernel_tests.sh | SPECULATIVE_TESTS | 本测试在active组且不被9.1/A5过滤 |
| 构建准备 | scripts/prepare_kernel_tests.sh | CANN版本分支/安装wheel | Triton默认映射和构建调用 |
| 顶层导入 | python/sgl_kernel_npu/sgl_kernel_npu/__init__.py | _load_sgl_kernel_npu | 原生库与torch_npu前提 |
| 子模块导入 | python/sgl_kernel_npu/sgl_kernel_npu/sample/__init__.py | __all__ | 未把此入口冒充注册operator |
| Python打包 | python/sgl_kernel_npu/setup.py | find_namespace_packages/TargetBuildPy | common模块打包和目标provider |
| Provider约束 | python/sgl_kernel_npu/build_tools/target_provider.py | stage/_validate_destination | 不覆盖common模块 |

### 实现复用检查

| 检查项 | 可复用事实 | 不得改变的约束 | 源码符号 |
|---|---|---|---|
| ABI/POD | 三指针+B/V/stride+C，无自有POD | dtype/行stride单位、编译器ABI边界 | Host/JIT签名 |
| 调用顺序 | 每行初始化、逐块合并、最后写两标量 | 更新m之前必须重标s | 核心循环 |
| workspace/内存 | 无全词表GM临时，输出12B/行 | 32KiB不是UB总量；输出需保活 | Host分配和tile选择 |
| 同步 | 行互斥、单program保存状态 | 不引入跨program无同步共享s | grid/row循环 |
| 精度与尾块 | 转FP32、tail=-inf、strict跨块比较 | 不许忽略非有限与块内primitive合同 | load/exp/argmax/where |
| 失败边界 | 无fallback或空域门禁 | 非法tile或非末维连续不能靠默认路径修复 | Host断言、C计算 |
