---
type: API
title: use_internal_format_weight：模型权重私有格式转换
description: 说明原地转换模型权重且无返回值，不将格式转换与固定地址或所有算子支持混同。
tags:
- task.lookup
- topic.graph_execution
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/api/torchair/use_internal_format_weight.md
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/api/torchair/use_internal_format_weight.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/experimental/inference.py
  role: implementation
created_at: '2026-11-09T02:48:45Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# use_internal_format_weight：模型权重私有格式转换

## 版本与范围

依据 TorchAir 固定发布子模块 `7c6c754bed00c86ffaaa2a45cb7ac2724f058013`。该提交属于 ascend_26_0_pt28 的固定来源组合；不是所有历史或主线版本的通用契约。发布部分选取 A2/A3；主线 A2/A3 与950的限定范围见下节，不回推发布版。

## 接口和返回

`torchair.use_internal_format_weight(model: torch.nn.Module) -> None` 将模型权重转换为 TorchAir 内部私有格式。参数为 nn.Module，接口没有新的模型返回值；不要写成 model=use_internal_format_weight(model)。

## 组合边界

该接口不是任意激活 Tensor 的 npu_format_cast，也不是 frozen_parameter 的开关。转换前后应检查权重 dtype、shape、格式与存储变化，再决定何时编译/缓存和固定地址。动态分档对参与分档的 Tensor 禁用私有格式，不能仅凭这个工具 API 的“无约束”描述推定组合都合法。

来源没有承诺每个权重必转换、每种算子都支持对应格式或必然加速，不能用调用成功代替实际图和数值检查。

- [RefData 与原地输入](../../guides/optimization/torchair/ge_refdata_and_mutated_inputs.md)
- [分档输入限制](set_dim_gears.md)


## 验证边界

分别核对实际软件版本、配置生效日志/图结构、输出与存储语义，再比较同输入的稳态耗时。本文为固定文档和静态接口审阅，没有执行上游代码、NPU 数值或性能实验。

- [软件栈来源与适用性](../../concepts/frameworks/ascend_software_stack_baselines.md)

## 主线只处理选定模块和数据类型

固定主线 `92e1e967bd35ebc37a442b4a969730bf3cf77a3c` 的本节对应文档已与发布 `7c6c754bed00c86ffaaa2a45cb7ac2724f058013` 逐页对照；主线总览声明A2/A3与950PR/950DT，未在这些接口页另列产品排除。950仅属于主线证据，不回推发布配套，也不证明两仓主线组合已兼容。

主线实现递归检查模块类型，不遍历所有Parameter逐个强制转换。未import torch_npu时只记录错误并return，未完成任何转换；调用返回None不能证明转换成功。涉及的Conv2d/Linear CPU权重会报错，需先按对应模块路径把模型放到NPU。文档示例只有普通自定义Parameter，没有实际受识别的Linear/Conv模块，不能把其调用成功当作所有参数都转换的证明。

- Conv2d只处理groups≤1且权重FP16的分支，转FRACTAL_Z(4)；groups>1或其他dtype跳过，不能与Linear的条件混用。
- Linear转FRACTAL_NZ(29)；已加载DeepSpeed时，对其LinearLayer/LinearAllreduce有单独分支。未加载该模块不启用此分支。
- LinearA8W8Quant处理scale/offset，仅Ascend310P名称分支另外转换权重；LinearQuant转换权重；LinearWeightQuant在quant_scale存在时转换量化参数，权重格式转换又按设备名Ascend310P/Ascend910B门控。不能据此把每个量化模块的设备分支都推广到950或所有后续产品。
- QuantConv2d分支需对应类存在、权重为NPU且INT8、groups≤1才转FRACTAL_Z；FP32 scale还会通过npu_trans_quant_param处理。它与FP16 Conv2d不是同一个输入契约。

转换直接替换相应weight.data或scale.data，可能改变存储/布局；先完成权重加载与所需转换，再独立核对编译缓存、固定地址和消费者布局。这里记录包装分支，不替代每个模块自己的产品、dtype和数值约束，也没有格式转换收益实测。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/api/torchair/use_internal_format_weight.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/overview.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/api/torchair/use_internal_format_weight.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/experimental/inference.py)（implementation）
