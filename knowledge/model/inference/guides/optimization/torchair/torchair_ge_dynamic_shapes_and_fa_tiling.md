---
type: Guide
title: GE 动态形状：档位组合与 FA 静态下沉定界
description: 说明 zip/product 的合法组合、FX 与 GE 静态性的区别及值依赖 FA 的下沉条件。
tags:
- task.optimization
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/features/advanced/dynamic_gears_merge_policy.md
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/appendix/cases/dynamic_static_graph/typical_issues.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/appendix/cases/dynamic_static_graph/background.md
  role: supporting
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/appendix/cases/dynamic_static_graph/concepts.md
  role: supporting
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/appendix/cases/dynamic_static_graph/presentation.md
  role: supporting
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/appendix/cases/dynamic_static_graph/background.md
  role: supporting
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/appendix/cases/dynamic_static_graph/concepts.md
  role: supporting
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/appendix/cases/dynamic_static_graph/typical_issues.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/appendix/cases/dynamic_static_graph/presentation.md
  role: supporting
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/figures/zh-cn_image_0000002481310690.png
  role: example
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/figures/zh-cn_image_0000002513270567.png
  role: example
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/figures/zh-cn_image_0000002513390561.png
  role: example
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/advanced/dynamic_gears_merge_policy.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/inference/_gear_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/inference/_gear_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/npu_fx_compiler.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/npu_fx_compiler.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/fx2ge_converter.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/fx2ge_converter.py
  role: implementation
created_at: '2026-11-09T02:14:40Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# GE 动态形状：档位组合与 FA 静态下沉定界

## 版本与范围

依据发布子模块 7c6c754bed00c86ffaaa2a45cb7ac2724f058013 的 GE 指南，选择 A2/A3 推理。接口参数约束集中在[set_dim_gears](../../../apis/torchair/set_dim_gears.md)，本卡解释组合与定位。

## 分档与合法输入

set_dim_gears 应配合 dynamic=True、整图编译，参与分档的输入不使用私有格式；不能同时启用 Dynamo 导图或 RefData。档位总数≤100，不含 0/1；首次编译前设置即可。

config.inference_config.dynamic_gears_merge_policy 默认为 zip，按位置组合；product 形成笛卡尔积，可能生成违反算子关系的组合。例如两输入 Add 分别取 batch=2/4，product 还会形成 (2,4)/(4,2)，与要求同 shape 的模型语义冲突，不能把“每轴都在档位中”当作整组合法。

## FX、GE 原图与 GE build 图

dynamic=False 会把 Tensor shape 和 SymInt[] 值专门化为常量；值变化可能重编译。dynamic=True 会符号化，但 Tensor shape 含 -1 或 FA 的值依赖 Tiling 都可能使 build 图保留动态调度。mark_static 仅固定 Tensor shape，不会自动把 SymInt[] 值依赖消除。

发布指南针对含 actual_seq_lengths 等 SymInt[] 输入、且这些值需要变化的 FA，给出的静态下沉路线为 dynamic=True、Tensor 输入 mark_static、config.experimental_config.tiling_schedule_optimize=True。不能把这一特定路线推广为所有算子及所有动态 Tensor 都能整图静态执行。

## 验证

先检查 Dynamo Guards/重编译日志，再看 FX、GE 原图和 build 图；Tensor 维度 -1 表明相应输入仍动态。检查 ge.dynamicDims 是否只包含业务有效组合，再覆盖全部计划档位及越档输入。本文未运行编译或下沉测试。


## 静态性的三个判断对象

FX 动态性既可能来自 Tensor shape，也可能来自标量值；dynamic=True 时，参数和 buffer 的形状保持固定，用户输入形状及标量可以被符号化，mark_static 可选择固定输入形状。GE 中形状为 `[]` 的 Data 节点仍可承载变化的标量值，所以“GE 输入 shape 固定”不等于输入数值是 Const。

先区分 FX 图、GE 原图、GE build 图。GE 原图输入全为静态 shape，仍可能因值依赖 Tiling 在 Host 调度；部分静态图也可能出现 PartitionedCall。发布案例中的 SymInt 标量可转成 CPU 上的零维 Data，后接 INT64 到 FP32 的 Cast；不要仅看到 Cast 或零维输入就判定出现动态 Tensor 维度。

在对应 GE build 图 txt 中，`_graph_unknown_flag=true` 表明并未形成完全静态下沉图；必须核对产物阶段和编译日志，不能在任意 FX Dump 中找不到它便宣称静态下沉成功。静态 FA 的动态值复用还须同时核对 mark_static、tiling_schedule_optimize 与实际值依赖路径；dynamic=False 的常量化可以编成静态图，但值改变会触发重编译。

## 主线调度说明

TorchAir主线 `92e1e967bd35ebc37a442b4a969730bf3cf77a3c` 的background、concepts与typical_issues保留上述四条FA编译路径，总览列A2/A3/950推理。dynamic=False也能形成静态下沉图，但actual_seq_lengths等专门化值改变会导致重编译；页面推荐的dynamic=True、mark_static Tensor、tiling_schedule_optimize三条件用于需要变化的值依赖输入，不能简化成“只有dynamic=True才可能下沉”。

Host调度在执行时进行推导、Tiling和逐算子下发，下沉调度提前加载整图并减少Host任务。动态shape图和静态shape图都可能只把部分子图下沉，因此PartitionedCall的存在只能说明某段静态子图，不能证明整图已静态下沉。Tensor shape固定也不消除标量Data的值依赖。

页面背景把首次执行中的AddGraph、编译、Executor生成与之后执行接口区分开；分析首次调用延迟时保留这些阶段，避免将整个区间都记为稳态算子耗时。本文未运行GE编译或设备调度验证。

## 主线展示页的标量与图阶段对照

主线 `92e1e967bd35ebc37a442b4a969730bf3cf77a3c` 的presentation页已全文与发布页对照，三张GE build图相同并已查看。示例的注释称dynamic默认，但实际调用明确dynamic=False；判断时看真实调用。dynamic=True段所贴一段FX日志包含tangents/梯度计算，不能把它与后面的前向GE节点逐行当作同一个编译单元；应按model、forward/backward、graph id匹配产物。

示例对比的有效事实是：dynamic=False可把scale_factor=100作为Const；dynamic=True时Tensor维度可为符号s0，GE输入对应-1，标量SymInt可成为CPU零维Data。再对用户Tensor mark_static后，Tensor维度固定而标量仍符号化，因此FX仍可有动态值、GE原图的shape却都是常量。该小节标题称FX静态，与正文“标量仍为符号”的描述有歧义，不能仅按标题归类。

零维INT64 Data转FP32后参与乘法可多出Cast节点；它不独自表示发生动态Tensor形状或多一次Host拷贝。三张build示意图分别展示静态融合、含PartitionedCall的动态图，以及静态shape但额外标量Cast的图；形状静态不等于标量内容被常量折叠。

仅在对应GE build txt上按_graph_unknown_flag=true及编译日志判断未完全静态下沉；不能在任意FX文件缺少此属性时就判定整图成功。FIA的值依赖仍按前述Tiling条件另行核对。本次没有编译示例或采集时延。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/features/advanced/dynamic_gears_merge_policy.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/appendix/cases/dynamic_static_graph/typical_issues.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/overview.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/appendix/cases/dynamic_static_graph/background.md)（supporting）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/appendix/cases/dynamic_static_graph/concepts.md)（supporting）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/appendix/cases/dynamic_static_graph/presentation.md)（supporting）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/appendix/cases/dynamic_static_graph/background.md)（supporting）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/appendix/cases/dynamic_static_graph/concepts.md)（supporting）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/appendix/cases/dynamic_static_graph/typical_issues.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/appendix/cases/dynamic_static_graph/presentation.md)（supporting）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/figures/zh-cn_image_0000002481310690.png)（example）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/figures/zh-cn_image_0000002513270567.png)（example）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/figures/zh-cn_image_0000002513390561.png)（example）

- [完整页复核来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/advanced/dynamic_gears_merge_policy.md)（constraint）

## 档位登记、Guard与GE选项的实际消费者

固定主线92e1e967与发布7c6c754b的 `_gear_utils` 实现还需区分三层：Python属性登记、Dynamo离散Guard、GE选项组合。以下是本地实现边界，公开接口约束仍以前文与[set_dim_gears](../../../apis/torchair/set_dim_gears.md)为准；没有执行符号求值或编译。

| 层次 | 实际行为 | 成本或边界 |
| --- | --- | --- |
| 登记 | 已有dim_gears且不相等则拒绝；维度检查int和有效下标；每轴list/tuple长度2..100、元素int且非0；逐轴mark_dynamic，最后将原字典赋给Tensor | 不是深拷贝；后续轴失败前，前面mark_dynamic可能已执行。此检查未单独拒1或负值，不能据此放宽公开参数合同 |
| 取值 | get_dim_gears只读同名属性，无则None | 直接取原对象；后续外部修改字典/列表不会由本函数自动隔离 |
| Guard入口 | 仅当至少一个Tensor的dim_gears非None才继续；其他未分档Tensor和未标轴用guard_int | 全部没有档位属性时不在这里专门化所有尺寸；空字典仍满足非None入口 |
| 离散Guard | 每轴先sorted(set(gears))，约束在最小/最大内，再逐相邻档位排除两档之间的开区间；bool不成立时断言，成立后guard_bool | 是离散档位集合而非连续[min,max]；重复档位先去重，元素初始数量不等于独立档位数 |

集成 `_set_inputs_custom_attr` 恢复dim_gears时重新调用set_dim_gears，再统一guard_gears_shape；GE `_normalize_ge_option` 直接取named_inputs_info与merge_policy.value生成选项。输入分类与getter另见[首次调用](torchair_ge_runtime_binding_and_first_call.md)，不要混用FX参数序号和最终GE输入登记。

| GE选项步骤 | 实际行为 |
| --- | --- |
| 无任何非空dim_gears | 返回空字典 |
| 输入/轴顺序 | 按输入节点名称排序，轴按维度序号排序；ge.inputShape写全部已登记输入shape |
| 收集分档轴 | 只把对应data_shape[dim_index]精确为-1的轴加入gear_list；有档位属性却没有这种轴时断言 |
| zip | 各轴列表长度必须相同，再按位置配对 |
| product | 先完整生成笛卡尔积列表 |
| 数量限制 | 之后才用set去重，并要求独立组合不超过100；序列化set所得列表，未承诺原列表排序 |

因此product在去重/100档上限判断前可能已经构建很大的组合列表；重复值不会减少此前的生成请求。局部生成器只组合轴值，不验证Add等模型关系。最终输出ge.inputShape、ge.dynamicDims、ge.dynamicNodeType='1'，C++据summary/三个选项选择执行器的规则见[多档执行器](torchair_cpp_multi_gear_io_and_capacity.md)。

## 实现来源

- [固定实现1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/inference/_gear_utils.py)：1–133。
- [固定实现2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/inference/_gear_utils.py)：1–124。
- [固定实现3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/npu_fx_compiler.py)：55–55、904–911。
- [固定实现4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/npu_fx_compiler.py)：56–56、805–812。
- [固定实现5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/fx2ge_converter.py)：116–116、2001–2005。
- [固定实现6](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/fx2ge_converter.py)：62–62、1610–1611。
