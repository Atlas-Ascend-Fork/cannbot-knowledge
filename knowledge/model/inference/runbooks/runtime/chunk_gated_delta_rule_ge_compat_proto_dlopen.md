---
{
  "type": "Runbook",
  "title": "ChunkGatedDeltaRule No AscendIR 场景：兼容原型、C++ ABI 与 GE 初始化",
  "description": "来源CANN 9.1.0/torch_npu 2.12环境报告No AscendIR；补齐最终原型注册顺序、C++ ABI匹配、GE初始化及检查程序。保留联合配置历史结果，未将其作为单因素根因或数值正确性证明。",
  "tags": [
    "task.implementation",
    "topic.compilation"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-13T02:46:50Z",
  "platforms": []
}
---
# ChunkGatedDeltaRule No AscendIR 场景：兼容原型、C++ ABI 与 GE 初始化

## 适用场景

来源StartLux适配环境使用CANN 9.1.0和torch_npu 2.12，torch.compile GE图模式/dynamo_export报`No AscendIR ChunkGatedDeltaRule was found to be registered`。来源可找到相关内核和op-info条目，但“未注册”报错仍需区分原型、加载顺序与GE生命周期；不从这条报错单独认定安装缺原型，也不外推到所有CANN 9.1.0环境。

## 触发与观测

来源最终采用修正后的原型注册顺序、匹配的C++ ABI构建，并在dlopen后通过torchair包装函数初始化GE。在这一联合配置下，真实_torchair注册检查返回ChunkGatedDeltaRule、RecurrentGatedDeltaRule、MatMul均SUCCESS，负对照NoSuchOp__control为ERROR。随后B1（L65/H16/D128）及B2（打包异长63/65）导出EXPORT_OK，B1原生GESession mode=0记录推理success、可读取outputs.bin。这些信号不等同于数值正确性。

## 探针与操作

这是自建兼容注册层，不是官方包自带的.so。先核对当前安装converter、op-info JSON和meta实现的schema一致性；已有正确注册时不重复注册。来源schema依据为torch_npu的npu_chunk_gated_delta_rule converter、CANN的aic-ascend910_93-ops-info-transformer.json对应项，以及meta中out/value、final_state/initial_state的形状dtype关系。

在自有实验目录中分别保存下方`chunk_gated_delta_rule_compat_proto.cpp`、`build.sh`和`check_registration.py`。将CANN_HOME设为已核对的CANN 9.1.0根，使用相配的torch_npu/torchair环境。先构建，再在同目录执行Python检查；这是复现步骤说明，本次知识修订未运行编译或NPU测试。

## 机制与判别

来源最终兼容原型（初稿的注册顺序与结尾分号曾造成编译失败，下方已合并后续修正）：

```cpp
// Project-built compatibility prototype registering the GE AscendIR definition
// for ChunkGatedDeltaRule. NOT an official Ascend file.
//
// Schema basis (local, verifiable):
//  1. torch_npu 2.12 converter:
//     torch_npu/dynamo/torchair/_ge_concrete_graph/ge_converter/custom/
//     npu_chunk_gated_delta_rule.py  -> custom_op("ChunkGatedDeltaRule",
//     inputs {query,key,value,beta,initial_state,actual_seq_lengths,g},
//     attrs {scale_value: Float}, outputs {out, final_state})
//  2. CANN 9.1.0 aic-ascend910_93-ops-info-transformer.json entry
//     "ChunkGatedDeltaRule": input0..input5 required (query,key,value,beta,
//     initial_state,actual_seq_lengths), input6 optional (g, float32),
//     output0/out + output1/final_state (bfloat16), attr scale_value float
//     optional default 1.
//  3. ops_proto_legacy.h REG_OP(RecurrentGatedDeltaRule) macro style for the
//     sibling op.
// Inference: out mirrors value (shape+dtype); final_state mirrors
// initial_state (shape+dtype), per torch_npu meta registration
// (_meta_registrations.py npu_chunk_gated_delta_rule).
// The registration is loaded explicitly via dlopen/LD_PRELOAD; the existing
// torchair get_registered_ir_def check runs unchanged.

#include "graph/operator_reg.h"
#include "graph/types.h"

namespace ge {

REG_OP(ChunkGatedDeltaRule)
    .INPUT(query, "T1")
    .INPUT(key, "T1")
    .INPUT(value, "T1")
    .INPUT(beta, "T1")
    .INPUT(initial_state, "T1")
    .INPUT(actual_seq_lengths, "T2")
    .OPTIONAL_INPUT(g, "T3")
    .OUTPUT(out, "T1")
    .OUTPUT(final_state, "T1")
    .ATTR(scale_value, Float, 1.0)
    .DATATYPE(T1, TensorType({DT_BF16}))
    .DATATYPE(T2, TensorType({DT_INT32}))
    .DATATYPE(T3, TensorType({DT_FLOAT}))
    .OP_END_FACTORY_REG(ChunkGatedDeltaRule)

IMPLEMT_INFERFUNC(ChunkGatedDeltaRule, ChunkGatedDeltaRuleInfer) {
  TensorDesc value_desc = op.GetInputDesc("value");
  TensorDesc init_state_desc = op.GetInputDesc("initial_state");

  TensorDesc out_desc = op.GetOutputDesc("out");
  out_desc.SetShape(value_desc.GetShape());
  out_desc.SetDataType(value_desc.GetDataType());
  if (op.UpdateOutputDesc("out", out_desc) != GRAPH_SUCCESS) {
    return GRAPH_FAILED;
  }

  TensorDesc final_state_desc = op.GetOutputDesc("final_state");
  final_state_desc.SetShape(init_state_desc.GetShape());
  final_state_desc.SetDataType(init_state_desc.GetDataType());
  if (op.UpdateOutputDesc("final_state", final_state_desc) != GRAPH_SUCCESS) {
    return GRAPH_FAILED;
  }
  return GRAPH_SUCCESS;
}

INFER_FUNC_REG(ChunkGatedDeltaRule, ChunkGatedDeltaRuleInfer);

}  // namespace ge
```

构建方式（将来源固定安装前缀改为显式CANN_HOME，其余链接关系保留）：

```bash
#!/bin/bash
# Build the project-local compatibility prototype shared library.
# Links only against the already-installed CANN 9.1.0 graph libraries;
# no system modification, no foreign .so.
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
CANN="${CANN_HOME:?set CANN_HOME to the checked CANN 9.1.0 installation}"
g++ -std=c++17 -fPIC -shared -O2 -D_GLIBCXX_USE_CXX11_ABI=0 \
  -I"$CANN/include" \
  "$DIR/chunk_gated_delta_rule_compat_proto.cpp" \
  -L"$CANN/lib64" -Wl,-rpath,"$CANN/lib64" \
  -lgraph -lgraph_base \
  -o "$DIR/libchunk_gated_delta_rule_compat_proto.so"
echo "built: $DIR/libchunk_gated_delta_rule_compat_proto.so"
```

来源构建链还表明：默认新C++ ABI产物曾在dlopen时报GetInputDesc符号未定义，后来加入`-D_GLIBCXX_USE_CXX11_ABI=0`后才匹配该环境。此flag仅对应来源的库ABI；其他安装须核对实际CANN/torch_npu与编译器ABI，不能统一固定为0。

同目录的注册检查必须初始化GE。来源仅加载.so时，连MatMul等正对照也返回ERROR；直接调用InitializeGraphEngine({})又因缺deviceId失败，最终改用`torchair.core._backend.initialize_graph_engine()`包装函数。这是该版本的运行环境前置，不是纯CPU静态检查；本文只记录来源运行，本次修订未调用它。

同目录的最终注册检查：

```python
#!/usr/bin/env python3
"""Test 1: verify the compat proto .so registers ChunkGatedDeltaRule in the real
GE OpFactory via explicit in-process dlopen (RTLD_GLOBAL). The existing
torchair get_registered_ir_def check runs unchanged."""
import ctypes
import json
import os
import sys

SHIM = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "libchunk_gated_delta_rule_compat_proto.so")

import torch  # noqa: E402
import torch_npu  # noqa: E402
from torchair.core._backend import initialize_graph_engine  # noqa: E402
from torchair.core import _torchair  # noqa: E402

ctypes.CDLL(SHIM, mode=ctypes.RTLD_GLOBAL)
initialize_graph_engine()

results = {}
for name in ("ChunkGatedDeltaRule", "RecurrentGatedDeltaRule", "MatMul", "NoSuchOp__control"):
    status = _torchair.get_registered_ir_def(name)[0]
    results[name] = status

print("REGISTRATION_RESULTS", json.dumps(results, indent=1))
ok = results.get("ChunkGatedDeltaRule") == "SUCCESS"
ok = ok and results.get("RecurrentGatedDeltaRule") == "SUCCESS"
ok = ok and results.get("MatMul") == "SUCCESS"
ok = ok and results.get("NoSuchOp__control") != "SUCCESS"
sys.exit(0 if ok else 1)
```

该检查只能验证此进程在匹配ABI、加载特定原型并初始化GE后的IR注册状态；不把联合配置成功表述为单独dlopen的因果证明。自建REG_OP的输入输出、可选g、dtype、scale_value和推导函数都必须与当前converter及内核配套；不能仅凭成功注册断言任意兼容原型可用。

## 验证信号

来源在完成编译修正、ABI匹配与GE初始化后得到上述注册检查、B1/B2导出和B1 GESession返回；初稿编译失败、默认ABI符号错误及未初始化时全ERROR均不是成功证据。注册、导出、执行和数值对照是不同层级；本卡没有采用outputs.bin与参考输出的数值比较结果，也没有更广shape、dtype或版本矩阵的验证。

## 适用与失效边界

该机制仅对应来源CANN 9.1.0/torch_npu 2.12的schema实例；改变版本、布局、输入/输出推导或内核后须重新核对。加载不匹配原型可能带来错误推导，因此不能把“补一个同名注册”当作通用修复。本卡给出自建源码和构建条件，不发布二进制或私有实验资产。
