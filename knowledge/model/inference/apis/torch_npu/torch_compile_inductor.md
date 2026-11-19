---
type: API
title: torch.compile在Inductor-Ascend的参数范围
description: 记录内置说明的backend/mode/options、默认值与950DT总览边界。
tags:
- task.lookup
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/torch_compile_api/torch_compile_api.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/overview/overview.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/dynamicshape/shapehandling.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/dynamicshape/symbolic.md
  role: primary
created_at: '2026-11-09T15:10:31Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- '950'
---

# torch.compile在Inductor-Ascend的参数范围

## 固定来源与范围

依据TorchNPU主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf的内置API页及总览；总览使用约束为950DT，不由通用原生compile清单扩大这套全部参数组合到其他产品。不是26.0/PyTorch2.8或其他主线配套承诺，未导入、编译或训练模型。

```python
torch.compile(model, *, fullgraph=False, dynamic=None,
              backend="inductor", mode=None, options=None, disable=False)
```

| 参数 | 此页给出的合同 |
| --- | --- |
| model | 必选，要编译的模型或参数，完整可调用对象规则未另给 |
| fullgraph | 默认False，控制是否强制整图编译，不自动使所有Python逻辑可捕获 |
| dynamic | 默认None，控制动态shape编译，具体True/False策略和约束另核 |
| backend | 默认inductor，列inductor/npugraphs；与TORCHINDUCTOR_NPU_BACKEND内部模式变量不同 |
| mode | 只列None（默认）及reduce-overhead，不照搬社区其他模式名 |
| options | 默认None，只列triton.cudagraphs、trace.enabled、enable_shape_handling；该页没有完整取值、冲突或图捕获协议 |
| disable | 默认False，控制关闭torch.compile能力 |

样例将SimpleMLP及训练输入放NPU，以reduce-overhead编译后用Adam、CrossEntropyLoss执行forward/backward/step；它是接口组合示例，不是本次运行结果、所有训练模型支持证明或设备同步/捕获生命周期规范。

先核对包/CANN/TA版本、真实backend和内部模式，区分图断裂、首次编译与稳态。详细组件、依赖及采证边界见[编译与Export指南](../../guides/optimization/torch_npu/torch_npu_native_compiler_export_scope.md)。

## 形状专门页对options的补充

入门API页只列三种options名称；ShapeHandling专门页还列shape_handling_configs与shape_handling_dict，不把前文“此页给出的合同”当全部内部配置的穷举。其字段、默认与当前源码调用差异见[分档草稿](../../guides/optimization/torch_npu/shape_handling.md)；已知差异未消除前不把扩展字段加入已验证生产配方。dynamic的复用层次见[动态形状指南](../../guides/optimization/torch_npu/torch_npu_inductor_dynamic_shape_choices.md)。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/torch_compile_api/torch_compile_api.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/overview/overview.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/dynamicshape/shapehandling.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/dynamicshape/symbolic.md)（primary）
