---
{
  "type": "Runbook",
  "title": "DynamicGRUV2 fp32 不支持（EZ3002）后同进程静默输出全零与假成功重试",
  "description": "NPU 上以 fp32 调用 nn.GRU 时 DynamicGRUV2 报 Unsupported_Operator(EZ3002)（op store 无该算子、DT_FLOAT 不在支持列表，仅 DT_FLOAT16/FRACTAL_NZ），首调抛 RuntimeError（build op model failed, result = 500002）。",
  "tags": [
    "task.debugging",
    "topic.model_serving"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": []
}
---
# DynamicGRUV2 fp32 不支持（EZ3002）后同进程静默输出全零与假成功重试


## 适用场景

NPU 上以 fp32 调用 nn.GRU 时 DynamicGRUV2 报 Unsupported_Operator(EZ3002)（op store 无该算子、DT_FLOAT 不在支持列表，仅 DT_FLOAT16/FRACTAL_NZ），首调抛 RuntimeError（build op model failed, result = 500002）。失败后同进程后续计算静默输出全零（norm=0.0000 vs CPU 1.9893、CE=0.0000 vs 3.3322）；try/except 重试同一实例不再报错但结果错误（与 CPU 参照 maxdiff=2.420e-01）——假成功；DynamicGRUV2Grad 侧伴随 Invalid_Argument(EH0012) aclrtAllocatorGetByStream 失败（stream 未注册 allocator）。失败边界明确：fp32 输入 + op store 无 DynamicGRUV2；同进程复用会得到假成功结果，验证必须换进程。

## 触发与观测

> 首次失败：NPU 上 fp32 nn.GRU 调用 DynamicGRUV2 抛 Unsupported_Operator(EZ3002)——[tbe-custom]:op type DynamicGRUV2 is not found in this op store；[Static shape check] 输入 x 的 DT_FLOAT 不在支持列表（Data Type: {DT_FLOAT16,...}，Format:{FRACTAL_NZ,...}），build graph failed（ge result = 4294967295）、build op model failed（result = 500002），宿侧 ERR00100 PTA call acl api failed，首调抛 RuntimeError。

**机制片段：M1**：

```
1: [ERROR] ... ERR00100 PTA call acl api failed.
2: Unsupported_Operator(EZ3002): Optype [DynamicGRUV2] of Ops kernel [AIcoreEngine] is unsupported. Reason: [tbe-custom]:op type DynamicGRUV2 is not found in this op store.[Static shape check]:data type DT_FLOAT of input [x] is not supported. All supported data type and format of tensor input0.x is: Data Type: {DT_FLOAT16,DT_FLOAT16,DT_FLOAT16,DT_FLOAT16}Format:{FRACTAL_NZ,FRACTAL_NZ,FRACTAL_NZ,FRACTAL_NZ}.
```

## 探针与操作

（探针见“触发与观测”中的日志读取与下面的验证命令；本候选无独立探针环节。）

## 机制与判别

> 失败后同进程状态污染（客观观测）：首调抛错后，同进程后续计算静默输出全零（norm=0.0000 而 CPU 参照 1.9893；CE=0.0000 而 CPU 3.3322、健康值 log(28)=3.3322）；try/except 重试同一实例不再报错但结果错误——输出翻倍输入后 maxdiff=4.419e-02（健康值应>0）、与 CPU 参照 maxdiff=2.420e-01（参照 absmax=0.2420），构成假成功；重试后状态仍为全零。

> 伴随现象与失败边界：DynamicGRUV2Grad 报 RuntimeError（The Inner error is reported as above... current working operator name is DynamicGRUV2Grad）与 Invalid_Argument(EH0012) aclrtAllocatorGetByStream failed（Parameter stream is invalid. Reason: The stream is not registered with any allocator），另有 DynamicGRUV2GradAlignFusionPass cannot be applied for unknown shape 与 trans_TransData_26 call DoTiling failed。边界：fp32 输入加上该 op store 缺 DynamicGRUV2 即触发；失败后同进程不可复用（输出全零、重试假成功），后续验证必须换进程/实例。

**机制片段：M2**：

```
1: == fp32 nn.GRU 首调（预期抛 RuntimeError）==
2: [PASS] 首调抛 RuntimeError：含 DynamicGRUV2=True，含 500002=True
3: == 崩溃后同进程检查 ==
4: [异常] 失败后: norm=0.0000(CPU 1.9893) CE=0.0000(CPU 3.3322, 健康值 log(28)=3.3322)
5: == try/except 重试同一实例 ==
6: [假成功-异常] 重试未报错：输出翻倍输入后 maxdiff=4.419e-02（健康值应>0）；与 CPU 参照 maxdiff=2.420e-01（参照 absmax=0.2420）
7: == 重试后状态 ==
8: [异常] 重试后: norm=0.0000(CPU 1.9893) CE=0.0000(CPU 3.3322, 健康值 log(28)=3.3322)
```

**机制片段：M3**：

```
1: RuntimeError: The Inner error is reported as above. The process exits for this inner error, and the current working operator name is DynamicGRUV2Grad.
2: [ERROR] ... ERR00100 PTA call acl api failed.
3: Invalid_Argument(EH0012): aclrtAllocatorGetByStream failed. Parameter stream is invalid. Reason: The stream is not registered with any allocator.
```

## 验证信号

（本候选为 negative_result：客观验证信号即上述失败观测本身——norm/CE 全零数值、重试 maxdiff、EH0012 报错原文；无成功侧验证信号。）

## 适用与失效边界

适用：NPU 上 fp32 调用 nn.GRU/DynamicGRUV2 报 EZ3002 之后的现场判读——后续全零输出与假成功重试是失败后状态污染的表现，不是修复成功。失效边界：结论来自案例现场复现日志（extract_0-3.txt），无 veRL/CANN 版本号与硬件型号；'必须换进程验证'由全零/假成功观测归纳，未单独做对照实验；DT_FLOAT16/FRACTAL_NZ 支持列表仅来自报错消息本身。
