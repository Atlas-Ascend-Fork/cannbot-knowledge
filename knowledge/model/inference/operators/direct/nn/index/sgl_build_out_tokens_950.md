---
type: Operator
title: "BuildOutTokens 950 Direct Invoke 算子知识"
description: "闭合投机输出构造的stride读取、256元素轮转及int64全位选择，明确未提交draft后缀、gamma0和长度语义边界。"
tags: [task.implementation, task.lookup, topic.memory, topic.precision, topic.programming_model]
status: draft
sources:
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/sample/build_out_tokens_triton.md
    role: primary
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/build_out_tokens.py
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/sample/build_out_tokens.py
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/utils/triton_utils.py
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/__init__.py
    role: supporting
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/__init__.py
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/__init__.py
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
created_at: "2026-11-09T09:33:54Z"
updated_at: "2026-11-09T09:33:54Z"
platforms: ["950"]
cann_versions: ["9.1.0"]
---

# BuildOutTokens 950 Direct Invoke 算子知识

## 算子速览

`sgl_kernel_npu.implementation.triton.sample.build_out_tokens.build_out_tokens_triton` 产生新的int64[B,gamma+1]：复制draft全部gamma列、最后补0，在correct_len位置替换bonus；bonus之后的draft保持，不是清空未提交后缀。有效前缀长度由调用方以correct_len+1解释。完整Host/单Kernel及gamma0/B0边界闭合。

draft保留未验证整数lowering、device属性cache及无设备值范围guard；源码注释描述CANN9.1 int64 select规避，不构成当前复现。全文读过的[公开API](../../../../apis/sgl_kernel_npu/sgl_build_out_tokens.md)复用合同，不重新创建API。

## 接口与语义

### 计算语义

G=gamma≥0，K=G+1；base[t,c]=draft[t,c]（c<G）否则0；out[t,c]=bonus[t]当c=correct_len[t]，否则base。合法0≤correct_len≤G时一行恰插入一个bonus，提交前缀长度correct_len+1；其它draft后缀仍保留。超范围length不会生成scatter地址，只导致比较全不匹配/未插入bonus，语义越界而非由此直接证明越界DMA。

### 输入、输出与属性

| 项 | 真实要求 |
|---|---|
| draft_tokens | [B,G]，int32/int64、NPU |
| correct_len/bonus | [B]，int32/int64，同NPU；各自dtype可不同 |
| gamma/verify_num_draft_tokens | G非负、verify=G+1；代码关系检查但未显式排除bool或验证Python int类型 |
| strides | 支持draft行/列、length/bonus各自元素stride，非连续输入不被连续化 |
| out | empty[B,K] int64，新连续输出；输入只读 |

### 入口与版本

Direct参数全为keyword-only，依次draft_tokens/correct_len/bonus/verify_num_draft_tokens/gamma；冻结短路径加包名前缀为精确符号。auto/triton只转发；torch_native拼接/scatter参考不属于此Kernel图。SGL commit `dda6d36b0cdb4081e102d14c0a2fb276fc416e69`，CANN9.1.0为README/CI固定配置和源码注释背景，非本次运行/二进制核验；完整Triton版本未固定。

## Host/Launcher 执行流程

### 参数校验与前处理

G/verify关系→draft ndim/宽度→length/bonusshape→三dtype及相同NPU→分配out。B0直接返回，非空才helper获取P、launch grid(P,)、BLOCK256。关系/形状/dtype/device失败ValueError，不读correct_len设备值校验范围。没有自动Tensor转换或输入复制。

### 参数、Workspace 与生命周期

无workspace、POD、ACLNN、显式UB队列；output及异步输入生命周期由Torch/Triton负责，未传stream/wait/num_warps/stages。helper无参cache读取current_device而非draft.device，assertAIC/vector均正；多设备切换须核对缓存属性/当前设备相容。输出独立新存储，B0不需要helper/JIT。

### 启动图与失败传播

import→校验→empty→B0返回或helper→单JITKernel→返回。无fallback、无第二次scatterKernel，ValueError/分配/helper/JIT异常直接传播。包原生库/torch_npu导入是依赖，不是此token构造图的native算子。无autotune。

## Route 与参数设计

### 分核与资源计算

总输出元素N=B*K，P>0，program p处理start=p*256+j*P*256<N，每次256offset。按out线性索引唯一覆盖，row=offset//K,col=offset%K。N尾mask，G0时draft mask恒false，仍按合法length0插bonus。

### Route 选择

| 路线 | 条件 | 图 |
|---|---|---|
| H-000 | B0 | 空output直接返回 |
| R-001 | B>0,G≥0 | 单Kernel；G0为同body constexpr特化 |

### 模板/实现执行矩阵

三输入独立int32/int64共2³实例，读取length保持其dtype，token/draft转int64，output始终int64；G0和G正均同body，stride constexpr影响地址。没有tl.dot/Cube/AIC/MIX节点、autotune或不同数学算子。

### 隐藏性能 Guard

length/bonus按每个输出元素各load一次，同一行重复K次，源码没有row标量缓存承诺。block256固定，未见物理UB查询；compiler可能hoist/cache但逻辑次数不可据此减少。G/N与stride地址须在实际JIT整数域可表示，Host关系检查不保证超大整数lowering安全。

### POD/ABI

| 参数 | 类别/消费 |
|---|---|
| draft/correct_len/bonus/out | runtime指针；前三只读、out写 |
| N | out.numel constexpr→valid/循环 |
| GAMMA | G constexpr→row/col除数和draftmask |
| DRAFT_ROW/DRAFT_COL | draft.stride两constexpr→元素地址 |
| LEN_STRIDE/BONUS_STRIDE | vector stride constexpr→每row输入 |
| BLOCK | 256constexpr→arange/任务步长 |
| grid | (P,)；Kernel通过num_programs获得P |

无自定义序列化POD、字段宽度或偏移；stride单位为元素，由指针dtype换算字节。具体JIT ABI/整数位宽外部，不编造int32地址合同。

### Route 源码闭包

完整87行launcher/Kernel，helper与public**kwargs转发已读。根setup→stage_runtime完整复制Python包→build_wheel/setup_refactor打包；sample/backend init无Device。所有自有可达节点闭合；Tritonbitwise/整数比较/stride addressing及framework流为primitive外部边界。

## Kernel 实现

### 公共执行流程

输出线性分块→商余映射row/col→length/bonus加载→合法draft加载/其它0→int64全位mask选择→validstore。不原地改draft、不先拷贝再scatter，无共享写或跨核通信。

### Route R-001：固定256元素构造全输出

#### 适用条件

##### 选择证据

B>0且Hostguard通过；G0与G正均此body。非法correct_len值没有Host范围扫描，合法范围是调用方合同。

#### Device 数据流

##### 函数级调用链

`build_out_tokens_triton→get_device_properties→_build_out_tokens_kernel→tl.load/to(int64)/bitwise/store`，没有其它自有JIT helper/Kernel。

##### 源码等价伪码

start=p*256轮转；i=start+arange256，valid=i<N；r=i//K,c=i%K；len=load(length+r*sL,valid,0)，tok=int64(load(bonus+r*sB,valid,0))；v=int64(load(draft+r*sR+c*sC,valid&(c<G),0))；s=-int64(c==len)，v=(tok&s)|(v&~s)，store(out+i,v,valid)。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/读写 |
|---|---|
| length | 256 lanes input integer，合法m输出元素读m*dL B |
| bonus/draft | 各256逻辑lane；bonus每有效输出元素读dB，draft仅c<G读dD |
| token/value/select | 各256int64，逻辑各2048 B；不表示实际同时分配 |
| GM output | 每有效元素8 B |
| workspace/TQue/TBuf/物理UB | 无显式分配，N/A；compiler可融合/复用 |

##### 分层内存布局

`strided GM length/bonus/draft→integer SSA[256]→int64 bitmask选择→连续GM output[N]`。无中间GM、无显式二次DMA和workspace交接。

##### 字节账与复用顺序

完整调用读 `B*G*dD + B*K*(dL+dB)` B，写`8B*K` B；这是源码逻辑有效load/store总量，不当作cache后的真实事务。G0 draft访问0字节；B0所有Kernel访问0。三输入可只读别名而无写冲突，output新建；Triton异步完成前依框架规则保持有效，无自定义释放点。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| program间 | 线性256块唯一，无共享写/atomic/barrier |
| 内部依赖 | load→整数转换/比较/bitwise→store，compiler保序 |
| 尾块 | valid控制length/bonus/store，draft再加c<G；不访问输出外tail |
| int32输入 | token/draft符号扩展到int64，保存其整数值 |
| int64输入 | s为0或全1，按位组合保留全部64bit，不经浮点转换 |
| G0 | c恒0，draftmask恒false；合法len0使bonus成为唯一输出 |
| 错误length | 负或>G无匹配，不插bonus；合同错误未作valueguard，不据此推成地址越界 |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| _build_out_tokens_kernel | [完整body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/build_out_tokens.py#L9-L39) |
| Host检查/launch | [入口](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/build_out_tokens.py#L42-L87) |

## 算子特定优化

### Trick T-001：全位整数mask规避int64 select路径

#### 触发与源码依据

[连续源码](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/build_out_tokens.py#L35-L39)：

```python
        # Bitwise selection preserves all int64 bits without the int64 select
        # lowering issue in the CANN 9.1 Triton compiler.
        select = -(col == length).to(tl.int64)
        value = (token & select) | (value & ~select)
        tl.store(out + offsets, value, mask=valid)
```

#### 机制与设计原因

比较值转int64再取负，产生0/-1；两互补mask按位选择token/value，避免先转浮点破坏大tokenID。源码注释说明规避CANN9.1Triton int64 select lowering问题，这只是上游机制/背景，未复现具体故障。

#### 迁移边界

两个值必须已转int64，mask必须是全0/全1；负数token也按位保留。实际compilerbitwise合同和整数可表示域仍须匹配工具链。

#### 错误做法

把bool直接按位与int64只保留最低bit，或通过float32中转大tokenID。

### Trick T-002：同一次线性遍历完成复制、尾零与bonus

#### 触发与源码依据

[连续源码](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/build_out_tokens.py#L26-L34)：

```python
        row = offsets // (GAMMA + 1)
        col = offsets % (GAMMA + 1)
        length = tl.load(correct_len + row * LEN_STRIDE, mask=valid, other=0)
        token = tl.load(bonus + row * BONUS_STRIDE, mask=valid, other=0).to(tl.int64)
        value = tl.load(
            draft + row * DRAFT_ROW + col * DRAFT_COL,
            mask=valid & (col < GAMMA),
            other=0,
        ).to(tl.int64)
```

#### 机制与设计原因

每输出元素根据row/col按原stride读数据，c==G时不读draft而补0，随后统一mask选择bonus；无额外concat/scatter中间输出。统计长度/bonus会随K重复读，未虚构只读一次。

#### 迁移边界

K=G+1为正，length范围由调用方保证，有效前缀另传长度；不能从输出后缀值推断提交状态。

#### 错误做法

把bonus后draft清零改变合同，或按整个outputshape提交所有token。

## 模板与实现对比

单Kernel支持不同stride与三输入整数dtype；G0是合法同语义边界、B0是Host空路线。Torch参考concat/scatter是外部实现，不借其框架节点替代本源码。源码对fullbit保存的机制明示，无运行复现声明。

## 平台差异

本卡950归属arch35；公开arch22/35声明支持但注册非全芯片验证，README/architectures映射A2/A3及950。无硬件分支，CANN9.1.0 CI配置/注释不保证所有同版本binarycompiler相同或A2实测。实际物理allocation/lowering为框架边界。

## 限制与失败边界

correct_len合法值、尺寸/stride整数域、current_device cache相容仍需调用方保证；错误长度通常无bonus插入，不能误当已提交前缀。没有运行、编译、测试/校验或物理资源证据，draft不宣称安全迁移/性能收益。

## 源码索引

### 链路索引

| 阶段/源码 | 符号 | 事实 |
|---|---|---|
| [公开合同](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/sample/build_out_tokens_triton.md) | `build_out_tokens_triton` | gamma+1输出/有效前缀/arch22与35 |
| [Direct及Device](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/build_out_tokens.py) | `build_out_tokens_triton/_build_out_tokens_kernel` | 完整87行/stride输入/int64位选择 |
| [公开转发](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/sample/build_out_tokens.py) | `_triton_impl` | auto/triton关键字转发 |
| [属性helper](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/utils/triton_utils.py) | `get_device_properties` | 无参缓存/currentdevice/双核数assert |
| [sample包](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/__init__.py) | `module init` | 无附加Device |
| [import边界](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/__init__.py) | `_load_sgl_kernel_npu` | torch_npu/原生库与vendor初始化 |
| [backend包](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/__init__.py) | `module init` | 懒加载包，无另一Device节点 |
| [构建入口](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/setup.py) | `main` | 完整Python wheel路径；本次未构建 |
| [源码打包](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/build_tools/torch_wheel.py) | `stage_runtime/build_torch/build_wheel/setup_refactor` | 复制完整Python包、原生运行库与wheel |
| [平台/包说明](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md) | `REFACTOR/arch22/35 mapping` | 全部Python实现包含、产品映射、CANN9.1.0构建例 |
| [产品映射](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json) | `2201/3510` | a2/a3/950对应构建族 |
| [版本配置](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/.github/workflows/pr-test-kernels.yml) | `test-norm-ops` | CANN9.1.0/a3/950配置，非本次运行 |
| [CI消费](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/.github/workflows/pr-test-kernel-group.yml) | `run-kernel-group` | 对应版本容器/测试组参数 |

### 实现复用检查

冻结117同主题API已全文阅读并链接；不重复API、不混入接受长度计算或topk采样不同逻辑。上游测试覆盖信息不作为本次执行结果。全部同repo固定source恰一primary，无verified。
