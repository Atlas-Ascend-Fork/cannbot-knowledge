---
type: Operator
title: SGL贪心链前缀验证 950 Direct Invoke 算子知识
description: 还原verify_tree_greedy在950配置的单program线性前缀接受、未读树边、固定N行距和原地输出边界，区分CI接线与运行验证。
tags:
- task.implementation
- task.lookup
- topic.compute.indexing
- topic.speculative_decoding
- topic.memory
status: draft
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/sample/verify_tree_greedy.py
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/tests/python/sgl_kernel_npu/test_verify_tree.py
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
created_at: '2026-11-09T11:40:51Z'
updated_at: '2026-11-09T11:46:21Z'
platforms:
- '950'
cann_versions:
- 9.1.0
---

# SGL贪心链前缀验证 950 Direct Invoke 算子知识

## 算子速览

| 项目 | 内容 |
|---|---|
| 实际入口 | sgl_kernel_npu.sample.verify_tree_greedy.verify_tree_greedy；Direct Invoke，不是verify_tree_greedy_native |
| 计算语义 | 沿候选的线性位置接受匹配前缀，首次不匹配后不再接受，最后写一个target token；不遍历子节点或兄弟节点 |
| 输入输出 | 原地更新predicts、accept_index和accept_token_num，Python返回None；所分析int32用例，行寻址统一依赖候选宽度N |
| 执行类型 | 单个Triton编译的非Cube Vector节点；无dot、Mmad、SIMT launch或通信节点 |
| Kernel 路线 | R-001：每request一个program，整行预读并依次提取标量比较 |
| 核心资源 | 调用方GM缓冲、三个逻辑长度P的局部向量和标量状态；无源码显式UB/Queue/workspace分配 |
| 来源闭包 | direct_implementation_closed：Host参数、唯一JIT body、直接primitive与具体CI/打包接线均已读取；编译器物理分配为外部边界 |
| 验证状态 | 未执行编译、真机、数值或性能测试；平台依据为固定CI对该测试入口的配置，非运行通过记录，保留draft |

## 接口与语义

### 计算语义

记B=candidates.shape[0]、N=candidates.shape[1]>0、P=next_power_of_2(N)，C/R/T分别是candidates/retrive_index/target_predict按[B,N]线性寻址的内容。每个request b执行：

```text
last=R[b,0]; accept_index[b*N]=last; a=0; rejected=False
for i=1..N-1:
    if not rejected:
        if C[b,i] == T[b,i-1]:
            draft_idx=R[b,i]; predicts[last]=T[b,i-1]
            a+=1; accept_index[b*N+a]=draft_idx; last=draft_idx
        else: rejected=True
last_target=T[b,last-b*N]
accept_token_num[b]=a
predicts[last]=last_target
```

上述为源码等价伪码，不是任意验证树的数学定义。next_token和next_sibling完全不读；循环i也不沿retrive_index跳转。若把它用于自然顺序的贪心链，充分的索引前提是R[b,i]=b*N+i；任意置换映射即使地址合法，也不能自动解释为一般树验证。完整树遍历的native入口是另一逻辑实现，不能用其非线性树用例证明本入口行为。

a只统计匹配的draft数；accept_index的有效前缀长度是a+1，包含初始位置。最后一个target token另写predicts，不计入a。未写的predicts位置及accept_index尾部保留调用前内容，函数不会清零或填-1。

### 输入、输出与属性

| 参数 | shape/layout | dtype | 约束、默认值与语义 |
|---|---|---|---|
| predicts | 足以容纳所有实际R索引的稠密线性存储 | int32用例 | 可写，按R全局索引写；无边界校验 |
| accept_index | 实际按[B,N]连续行寻址 | int32用例 | 可写；不是按其自身shape/stride计算行距 |
| accept_token_num | 实际按[B]连续寻址 | int32用例 | 每request写a，含零匹配情形 |
| candidates | 实际按[B,N]连续寻址 | int32用例 | 只用shape前两维确定B/N，不读取Tensor stride |
| retrive_index | 实际按[B,N]连续寻址 | int32用例 | R值决定predicts地址及最后一次T的局部索引 |
| retrive_next_token | 入口必需参数，body未读 | int32用例 | 不提供树边选择；不据未读推导任意对象或None都被JIT接受 |
| retrive_next_sibling | 入口必需参数，body未读 | int32用例 | 同上 |
| target_predict | 实际按[B,N]连续寻址 | int32用例 | 预读每行后比较和生成最后target token |
| 返回值 | None | Python | 输出只通过调用方已有缓冲原地传递 |

源码没有显式dtype、device、shape、连续性、索引范围、别名或初始化检查。固定Triton直接调用用例是int32、B=2/N=2；其它类型和更大规模由源码参数化处理，但不据此声明已经测试或有已知编译上界。应使用同一NPU上的相互独立连续缓冲，并保证各request写域互不冲突。

### 入口与版本

固定提交仅有此无版本后缀的Python Host和同文件JIT函数。模块从sample子模块直接导入；它未列入sample.__all__，不改造成新的注册operator入口，也不补造ACLNN接口。整个包初始化仍导入torch_npu并加载libsgl_kernel_npu.so，纯Python文件存在不证明任意subset wheel可调用。

固定CI的test-speculative-ops配置A3/950×CANN9.1.0，run_kernel_tests.sh的speculative组实际包含test_verify_tree.py，且未被9.1/A5过滤。其simple测试直接调用本函数；另一个复杂树测试只调用native函数。准备脚本在未覆盖TRITON_ASCEND_WHL时为9.1选择triton-ascend3.2.2；这是配置事实，不是本次安装或执行证据。本卡范围为950，A2缺少该入口的明确测试接线证据，不外推。

## Host/Launcher 执行流程

### 参数校验与前处理

Host依次读取candidates.shape[0:2]，计算P，直接调用verify_tree_greedy_kernel[(B,)]。不分配输出、不连续化、不检查accept_index的第二维，也不处理空输入；shape访问、JIT编译或launch异常沿Python调用传播，源码没有fallback或重试。N=0/B=0的编译器、grid和标量提取行为未由Host闭合成安全空路径，调用合同限定B>0、N>0。

### 参数、Workspace 与生命周期

八个对象直接传入JIT，N/P为constexpr，B只用于grid；无TilingData/POD、无自有GM workspace、无队列。不能把constexpr二元组称作完整JIT缓存键。物理参数ABI、thread分配、寄存器和UB/spill容量取决于匹配Triton编译器，固定SGL源码不提供sizeof/offsetof或生成码。

所有输入和三个原地输出由调用方拥有。源码没有同步返回、事件返回、跨流依赖或异步owner保活；在实际提交流完成前不得覆盖、释放或跨流消费缓冲。Triton runtime当前流和allocator的内部实现属于框架边界，本卡不把函数返回None当作Device完成信号。

### 启动图与失败传播

| 节点 | Host 添加/启动 | entry/执行族 | blockDim 与 POD | 输入→输出 | workspace slice |
|---|---|---|---|---|---|
| N1 | verify_tree_greedy中的JIT[(B,)] | verify_tree_greedy_kernel，编译Vector | grid=(B,)，constexpr N/P；无自有POD | C/R/T→predicts/accept_index/accept_token_num；next/sibling未读 | 无 |

```text
调用方准备/初始化输入与原地输出 [框架/调用方边界]
 -> N1：各program独立预读一行、线性验证、写回
 -> 调用方按实际流依赖消费结果 [外部完成条件]
```

只有一个核心节点，无跨Kernel边、通信或全局原子。Host异常不触发补偿；Device非法索引、冲突或异步失败的具体信号由外部运行时决定，不能从本源码推出某个固定错误码或自动回滚。

## Route 与参数设计

### 分核与资源计算

program_id(0)=b直接对应request。N控制有效行长度和比较循环上界；P仅向上补齐局部向量长度，mask=(0..P-1)<N，三路load的other=0。padding lane既不被接受循环读取，也不作为合法最后索引域。合法最后提取仍要求0<=last-b*N<N，而不是仅小于P。

### Route 选择

| 顺序 | Route | Key/模板 | 精确选择条件与优先级 | 不适用去向 |
|---:|---|---|---|---|
| 1 | R-001 整行预读的线性前缀验证 | 无显式key；constexpr N/P | Host无分支，总向同一JIT提交；本文有效域B/N正且地址/布局满足合同 | 没有下一路线；无空域或任意树fallback |

```text
读取B/N -> P=next_power_of_2(N) -> grid(B)
 -> 唯一verify_tree_greedy_kernel
 -> 各program接受连续匹配前缀并写最后target token
```

### 模板/实现执行矩阵

| Route | key/selector | dtype/shape/platform 完整命中条件 | 执行拓扑与 Kernel 节点 | 实际模板/body | 内存与同步特征 | tail/fallback |
|---|---|---|---|---|---|---|
| R-001 | 唯一JIT body | 950 CI配置；int32用例；有效域B/N>0、连续同设备、索引/容量/写域合法 | 单Vector N1 | verify_tree_greedy_kernel(N constexpr,P constexpr) | 3个逻辑P向量；标量状态；无跨program同步 | 预读mask补零；有效输出前缀；无fallback |

### 隐藏性能 Guard

| Guard | Host/Tiling 条件 | Device/资源原因 | 影响 Route | 不满足时去向 | 源码符号 |
|---|---|---|---|---|---|
| 行pitch | Host未查，body统一b*N | 不使用accept_index自身stride；行宽必须与实际寻址一致 | R-001 | 可能跨逻辑行或越有效storage，不自动拒绝 | accept_index+b*N+a |
| 最后target下标 | Host未查 | al.get_element(Trow,last-b*N)无范围mask | R-001 | primitive非法索引行为外部，不能取padding作有效值 | 最后get_element |
| predicts容量和互斥 | Host未查R值/跨request冲突 | tl.store使用R的全局值，无atomic | R-001 | 越界或多program写冲突风险，无序列化fallback | predicts+last |
| 向量资源 | P向上取整，无最大N guard | 3P局部元素和scalar extract由编译器放置 | R-001 | 实际编译/资源边界未知，不能报固定UB上限 | tl.arange/get_element |
| 空域/同卡/连续 | 均无显式guard | grid和线性指针运算依赖调用方合同 | R-001 | 外部错误或不符合预期的访问，无自动修复 | Host与三路load |

### POD/ABI

无源码定义的二进制POD。下表逐个记录Host提供的参数；物理ABI布局均为编译器外部边界，不根据指针名编造偏移。

| 结构 | 字段 | 类型/位宽 | ABI 布局 | 单位 | Host/launcher producer | Device consumer | 边界 |
|---|---|---|---|---|---|---|---|
| JIT实参 | predicts | Tensor指针，int32用例 | 编译器决定 | 元素地址 | 直接透传 | tl.store(predicts+last) | 地址由R决定 |
| JIT实参 | accept_index | Tensor指针，int32用例 | 编译器决定 | 元素 | 直接透传 | tl.store(A+b*N+a) | 行pitch固定N |
| JIT实参 | accept_token_num | Tensor指针，int32用例 | 编译器决定 | 元素 | 直接透传 | tl.store(count+b) | 写匹配数a |
| JIT实参 | candidates | Tensor指针，int32用例 | 编译器决定 | 元素 | 直接透传 | masked load C+b*N+arange(P) | 需真实稠密行 |
| JIT实参 | retrive_index | Tensor指针，int32用例 | 编译器决定 | 元素索引 | 直接透传 | masked load R；last/draft_idx | 同时用于全局/相对下标 |
| JIT实参 | retrive_next_token | Tensor对象 | 编译器可能消除 | N/A | 直接透传 | 未读取 | 不实现子节点遍历 |
| JIT实参 | retrive_next_sibling | Tensor对象 | 编译器可能消除 | N/A | 直接透传 | 未读取 | 不实现兄弟遍历 |
| JIT实参 | target_predict | Tensor指针，int32用例 | 编译器决定 | token元素 | 直接透传 | masked load T；get_element | 比较i-1/末尾last-b*N |
| constexpr | num_draft_tokens | Python shape整型 | 编译期，无自有POD | 每行token数 | candidates.shape[1] | 行offset、mask、range(1,N) | 无正值guard |
| constexpr | pad_num_draft_tokens | Python整型 | 编译期，无自有POD | lane数 | triton.next_power_of_2(N) | tl.arange(0,P) | padding不是合法最后索引域 |
| grid | B | Python shape整型 | 启动配置，非kernel自有字段 | program数 | candidates.shape[0] | program_id(0) | 未实际查询核数 |

### Route 源码闭包

| Route | Key/selector | Host/Tiling producer | POD/参数 | Kernel entry/router 节点 | Kernel body/直接依赖 | 构建接线 |
|---|---|---|---|---|---|---|
| R-001 | 同文件唯一JIT | verify_tree_greedy | 8对象+N/P，grid B | verify_tree_greedy_kernel | tl.load/store/arange、al.get_element；无自有算法helper | setup namespace打包；CI speculative实际测试入口 |

## Kernel 实现

### 公共执行流程

唯一实现先按request完整预读C/R/T，再在程序内串行比较draft位置。rejected是粘滞状态，第一次不匹配后后续循环仍按源码范围存在，但不再进入接受分支。每次匹配向上一个全局检索位置写target，再推进last；最终无条件写accept_token_num和最后target。整数比较不涉及浮点归约、量化、舍入或误差阈值。

### Route R-001：整行预读的线性前缀验证

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Host | sample/verify_tree_greedy.py | verify_tree_greedy | B/N来自candidates，P向上2次幂，始终JIT[(B,)] | 唯一N1 |
| Device | 同文件 | verify_tree_greedy_kernel | pid=b；lane<N；i=1..N-1且not rejected | 匹配则推进，首次不匹配后停止接受 |
| 最后输出 | 同文件 | get_element/store | 用last-b*N取原预读T，非固定a下标 | 写最后target及a |

#### Device 数据流

##### 函数级调用链

```text
verify_tree_greedy -> JIT[(B,)] verify_tree_greedy_kernel
 -> program_id/arange/mask -> load(C),load(R),load(T)
 -> get_element(R,0) -> store accept_index根位置
 -> 逐i get_element(C,i)/get_element(T,i-1)
    -> 匹配：store predicts[last]，store accept_index下一位置，更新last
    -> 不匹配：rejected=True
 -> get_element(T,last-b*N) -> store count -> store最后predicts[last]
```

##### 源码等价伪码

```text
伪码：b=pid；lanes=0..P-1；valid=lanes<N
Cr=masked_load(C+b*N+lanes,valid,0)
Rr=masked_load(R+b*N+lanes,valid,0)
Tr=masked_load(T+b*N+lanes,valid,0)
last=Rr[0]; a=0; rejected=False; A[b*N]=last
for i in [1,N):
  if not rejected:
    target=Tr[i-1]
    if Cr[i]==target:
      draft_idx=Rr[i]; predicts[last]=target
      a+=1; A[b*N+a]=draft_idx; last=draft_idx
    else: rejected=True
last_target=Tr[last-b*N]
count[b]=a; predicts[last]=last_target
# A[b*N+a+1:(b+1)*N]及其它predicts位置不写
# next_token/next_sibling无读取；无独立清零节点
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| GM C/R/T | 各b*N+lane | 每路每行N有效元素；mask到P | int32稠密行用例 | caller | 入口三路load | 至N1完成 | 无stride参数；padding other0 |
| GM predicts | R指定last | 每行a+1次元素store，物理容量由R最大值决定 | int32用例 | caller初始化/N1 | 后续采样 | 至消费完成 | 不清其它位置；跨program需独占 |
| GM accept_index | b*N+[0,a] | 每行a+1个有效写，实际行容量N | int32用例 | caller/N1 | 后续接受序列 | 至消费完成 | 尾部保留初值 |
| GM accept_token_num | b | 每行一个元素 | int32用例 | N1 | caller | 至消费完成 | a不含根/最终fallback token |
| 逻辑局部Cr/Rr/Tr | lane 0..P-1 | 各P个元素 | int32用例 | masked load | 多次get_element | 整个program | 非实际UB/寄存器布局承诺 |
| 标量状态 | b、last、a、rejected、i及比较值 | 编译器决定 | 整数/bool | Host/取值 | 控制和store | program/循环 | 无源码分配 |
| next/sibling | 无实际地址消费 | 0逻辑payload读写 | N/A | caller | 未读取 | ABI要求由JIT决定 | 无树边缓存 |
| workspace/UB/Queue | N/A | 无自有分配 | N/A | 外部runtime | 编译生成实现 | 外部边界 | 不伪造TPipe或32B DMA块 |

##### 分层内存布局

N/A：源码没有AscendC InitBuffer/TPipe或手动dynamic UB。可证明的是GM三行到三组逻辑P元素，再由标量控制决定稀疏写回；实际UB、寄存器、spill、bank和交易粒度由匹配Triton后端生成，不能画成已确定的物理UB块。

##### 字节账与复用顺序

```text
int32用例，每request逻辑输入读取=3*N*4=12N B
每request逻辑输出store=2*(a+1)*4+4=8(a+1)+4 B
全batch逻辑请求=12BN + sum_b[8(a_b+1)+4] B，0<=a_b<=N-1
局部向量逻辑元素量=3P个int32，即12P B表示量，不是物理UB占用
workspace_total=0（本算子自有）；编译器runtime/scratch内部容量不在固定源中
```

此账不双计不存在的next/sibling读取，不把mask后的N当作硬件缓存线或实际DMA交易数，也不把逻辑P向量推成真实12P B UB。

| 复用子区 | 写入者 | 读取者/消费点 | 下一次覆盖 | 同步或释放依据 | 安全条件 |
|---|---|---|---|---|---|
| Cr/Rr/Tr | 入口load | 各次scalar extract | 本program内不重新赋值 | 编译器程序依赖 | 输入在launch期间不被其它流/别名覆盖 |
| last/a/rejected | 初始化与匹配/拒绝分支 | 下次循环和最后写回 | 同program下一步 | 控制/数据依赖 | 无跨program共享状态 |
| predicts | 各已接受位置，最终last | 下游消费 | caller后续阶段 | 实际流完成依赖 | 所有R地址合法，跨program写域不冲突 |
| accept_index尾部 | caller初始化 | 下游若需sentinel | 本kernel不覆盖 | caller负责 | 以a+1限定有效前缀，或事前填-1 |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| 预读 | tl.load mask/other0 | GM C/R/T | scalar extract | 局部逻辑向量 | N有效，P-N补零 |
| 前缀比较 | 整数==与控制依赖 | C[i]/T[i-1] | 匹配store | last/a/rejected | 首拒绝粘滞，无树遍历 |
| 原地写 | 普通tl.store，无atomic | 当前program | 下游 | predicts/A/count | dtype转换按pointee；分析int32用例 |
| 最后target | get_element(Tr,last-b*N) | 预读Tr | 最终predicts store | 真实局部下标 | 无范围mask，须小于N |
| 完成可见性 | runtime流边界 | 单N1 | caller等待实际完成 | 所有输出storage | 无事件返回或全局barrier |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host producer | sample/verify_tree_greedy.py | verify_tree_greedy | 仅由candidates取B/N，P向上2次幂，直接launch |
| Kernel entry | 同文件 | verify_tree_greedy_kernel | 8对象、N/P constexpr，单program对应request |
| Device body | 同文件 | tl.load/get_element/store | 线性前缀、固定A行距、最后相对下标 |
| 构建/CI | run_kernel_tests.sh及两workflow | SPECULATIVE_TESTS/test-speculative-ops | 确切测试文件接入950配置；不证明通过 |

## 算子特定优化

### Trick T-001：一次预读整行后以标量提取重复访问

#### 触发与源码依据

- 适用Route：R-001；B/N正且连续行、容量与指针域合法。
- Golden 来源：[三路masked预读](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/sample/verify_tree_greedy.py#L29-L41)。

```python
    req_idx = tl.program_id(0)
    tokens_offset = tl.arange(0, pad_num_draft_tokens)
    cur_tokens_offset = req_idx * num_draft_tokens + tokens_offset
    mask_draft_mask = tokens_offset < num_draft_tokens
    cur_candidates = tl.load(
        candidates + cur_tokens_offset, mask=mask_draft_mask, other=0
    )
    cur_retrive_index = tl.load(
        retrive_index + cur_tokens_offset, mask=mask_draft_mask, other=0
    )
    cur_target = tl.load(
        target_predict + cur_tokens_offset, mask=mask_draft_mask, other=0
    )
```

#### 机制与设计原因

比较循环不在每个位置重新从GM加载C/R/T，而是从已载入的逻辑向量提取标量；P向上2次幂满足arange形态，lane<N保证末尾不足P的行不读GM越界。代价是整个比较阶段保留P长度向量，实际资源和spill仍由编译器决定。只证明源码访问组织，不承诺硬件交易次数或性能比例。

#### 迁移边界

- 适用：每request短序列的串行状态推进，多次访问同一行。
- 前提：实际输入连续；P和N在编译器能力内，最后索引属于真实N域。
- 失效：任意strided Tensor、非法R索引或过大P不由此机制自动修复。
- 未验证：本次知识提取未执行编译、真机、数值或性能测试。

#### 错误做法

把other=0的padding lane当作有效target，或把局部12P B表示量当作已证UB上限。固定仓未提供相应硬件可验证反例，不推测具体错误码。

### Trick T-002：粘滞拒绝状态仅物化有效接受前缀

#### 触发与源码依据

- 适用Route：R-001；候选按线性链顺序解释。
- Golden 来源：[接受与最终写回](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/sample/verify_tree_greedy.py#L43-L67)。

```python
    last_accepted_idx = al.get_element(cur_retrive_index, (0,))
    tl.store(accept_index + req_idx * num_draft_tokens, last_accepted_idx)
    num_accepted = 0

    rejected = False
    for i in range(1, num_draft_tokens):
        if not rejected:
            draft_token = al.get_element(cur_candidates, (i,))
            target_token = al.get_element(cur_target, (i - 1,))

            if draft_token == target_token:
                draft_idx = al.get_element(cur_retrive_index, (i,))
                tl.store(predicts + last_accepted_idx, target_token)
                num_accepted += 1
                tl.store(
                    accept_index + req_idx * num_draft_tokens + num_accepted, draft_idx
                )
                last_accepted_idx = draft_idx
            else:
                rejected = True
    target_token = al.get_element(
        cur_target, (last_accepted_idx - num_draft_tokens * req_idx,)
    )
    tl.store(accept_token_num + req_idx, num_accepted)
    tl.store(predicts + last_accepted_idx, target_token)
```

#### 机制与设计原因

首次不匹配后rejected保持True，后续位置不再物化接受项；accept_index只写根和a个匹配位置，predicts写已接受链上的target及最后一个target。省略了本节点的全输出清零，也意味着尾部必须由有效长度或caller sentinel解释。这里没有改变Host循环上界，也不把条件执行称为一定的物理早退出。

#### 迁移边界

- 适用：线性候选前缀接受，不包括兄弟搜索或任意树跳转。
- 前提：A按N行距、R全局地址及末尾相对地址合法、跨request无写冲突。
- 失效：仅传next/sibling不能启用树遍历；不能用native复杂树结果当此kernel完整参考。
- 未验证：本次知识提取未执行编译、真机、数值或性能测试。

#### 错误做法

把accept_token_num=a当作accept_index全部有效项数而遗漏根，或未初始化尾部却读取整行。固定simple用例N=2不证明不同A行距或任意树可用。

## 模板与实现对比

| 对比维度 | R-001 唯一实现 | 设计选择依据 |
|---|---|---|
| 命中条件/优先级 | Host总走该JIT | 无fallback/其它selector |
| 模板与dtype | constexpr N/P；int32直接用例 | 不据源码未检查dtype扩大已验证类型 |
| 循环与分核 | grid B；每program i=1..N-1 | 每request串行推进，无按物理核数分块 |
| Queue/UB/寄存器 | 无手动资源；三P逻辑向量 | 物理配置是编译器边界 |
| 内存与复用 | 预读不重赋值；稀疏原地写 | caller提供输出及sentinel |
| 搬运/Vector API | tl.load/store，al.get_element | 无AscendC DMA参数或Cube节点 |
| 同步、精度与tail | 程序依赖；普通store；mask padding | 整数比较，末尾取值须在真实N域 |
| fallback/失败边界 | 无自动树遍历/连续化/重试 | 非法参数由外部运行时处理 |

## 平台差异

| 项目 | A2 | A3 | Ascend 950 |
|---|---|---|---|
| 支持状态 | 本入口缺明确平台接线证据，不在本卡范围 | 固定speculative CI明确配置；未证明运行通过 | 同一CI明确配置，test_verify_tree不在A5跳过表；未证明运行通过 |
| Host/Launcher | 不外推 | 同一个Python Host | 同一个Python Host，无源码平台selector |
| Kernel/资源 | 不外推 | 同一个Triton body；物理lowering未知 | 同一body；不能照抄A3物理资源/编译成功结论 |

## 限制与失败边界

- N/B正是本文调用前提，Host没有安全空分支；未证明N=0或B=0的编译/launch行为。
- 所有核心读按N线性行距，非连续view不自动被转换；accept_index注释中的num_spec_step+1没有参与地址计算。
- 只接受线性候选前缀，不读取两个树边参数。最后target取R产生的局部位置，任意置换不保证仍符合贪心链语义。
- 输出不清零，count不含根，A有效长度a+1；R不受Host边界检查，跨program重复写无原子/全局同步。
- 固定直接Triton测试只覆盖小int32链；CI配置、来源闭包、Lint与摘录核验均不是编译或数值通过记录。
- 依赖匹配CANN Triton primitive和成功包初始化；完整物理ABI、UB、寄存器、spill及stream allocator内部不在本固定源码内，未伪造。

## 源码索引

### 链路索引

| 链路阶段 | 文件 | 关键符号 | 支撑内容 |
|---|---|---|---|
| Direct Host/Device | python/sgl_kernel_npu/sgl_kernel_npu/sample/verify_tree_greedy.py | verify_tree_greedy/verify_tree_greedy_kernel | 完整唯一launch与body |
| 直接测试定义 | tests/python/sgl_kernel_npu/test_verify_tree.py | test_verify_tree_greedy_simple | int32线性链；复杂树测试另调native |
| 平台/版本配置 | .github/workflows/pr-test-kernels.yml | test-speculative-ops | A3/950×CANN9.1.0矩阵 |
| 真实runner | .github/workflows/pr-test-kernel-group.yml | run-kernel-group | NPU容器、准备和分组脚本接线 |
| 分组与过滤 | scripts/run_kernel_tests.sh | SPECULATIVE_TESTS/SKIP_ON_A5 | 实际包含测试且不跳过本文件 |
| 构建准备 | scripts/prepare_kernel_tests.sh | CANN_VER分支/build.sh调用 | Triton版本选择及kernel wheel准备 |
| 包初始化 | python/sgl_kernel_npu/sgl_kernel_npu/__init__.py | _load_sgl_kernel_npu | torch_npu及原生库导入前提 |
| sample导入 | python/sgl_kernel_npu/sgl_kernel_npu/sample/__init__.py | __all__ | 本入口通过子模块导入，不是新增公开注册表 |
| Python打包 | python/sgl_kernel_npu/setup.py | setup/TargetBuildPy | namespace包与provider staging |
| provider接线 | python/sgl_kernel_npu/build_tools/target_provider.py | stage_target_providers/_validate_destination | 目标provider不得覆盖已有common模块 |

### 实现复用检查

| 检查项 | 可复用事实 | 不得改变的约束 | 源码符号 |
|---|---|---|---|
| ABI/POD | 8对象+constexpr N/P，无自有POD | 不伪造参数偏移/完整JIT缓存键 | Host/JIT签名 |
| 调用顺序 | 预读→根位置→匹配前缀→末尾target | 首拒绝粘滞、末尾R相对地址 | kernel全body |
| workspace/内存 | 无自有workspace；按N寻址 | A真实行距N、合法R域与输出保活 | tl.load/store |
| 同步 | 单program数据依赖 | 跨request独占，流完成由caller负责 | grid与普通store |
| 精度与尾块 | int32比较用例；padding补零 | padding不得作有效最后target；A尾部保留 | mask/get_element |
| 失败边界 | 无fallback/自动检查 | 不与native树逻辑或非连续化保证互换 | Host和两个未读参数 |
