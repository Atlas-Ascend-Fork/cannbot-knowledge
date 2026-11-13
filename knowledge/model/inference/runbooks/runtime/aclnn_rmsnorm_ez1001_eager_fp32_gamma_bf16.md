---
{
  "type": "Runbook",
  "title": "关图调试时 aclnnRmsNorm 拒绝 FP32 激活与 BF16 gamma 的判别",
  "description": "来源服务关图后 warmup 报 EZ1001，实际输入为 x/yOut/rstdOut=FP32、gamma=BF16。恢复图模式后的片段只见加载完成且暂未出现该错误，未证明 warmup 或请求成功；支持矩阵和 FP32 产生点仍需补证。",
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
# 关图调试时 aclnnRmsNorm 拒绝 FP32 激活与 BF16 gamma 的判别

## 适用场景

sglang/fluentllm 类 NPU 推理服务，在设置 `NPU_DISABLE_GRAPH_MODE=1` 后进入 eager 路径并出现 aclnnRmsNorm 参数校验错误。先比较实际调用路径和输入 dtype，不预先断言包版本无关。

## 触发与观测

来源 flash26b pro_dsa_pp decode 的 warmup 报错：

```text
AclNN_Parameter_Error(EZ1001): Io input dtype or format is not supported, get io input info is x(DT_FLOAT, ND) gamma(DT_BFLOAT16, ND) yOut(DT_FLOAT, ND) rstdOut(DT_FLOAT, ND) but supported list is:
```

记录在该行后直接进入 TraceBack，没有实际输出完整支持列表。因此只能确认这个组合在该环境被拒绝，不能据此编出跨版本 dtype 矩阵。

## 探针与操作

核对启动脚本是否新增关图变量，以及该版本 MLA/NSA 分支是否以 `and not ENV.npu_disable_graph_mode` 绕开 TorchAir。继续在 `forward_decode_3b` 的 input_layernorm 前记录 hidden_states 与 gamma 的 dtype；同步栈可在可控复现中使用 `ASCEND_LAUNCH_BLOCKING=1`，但来源未完成该探针。

## 机制与判别

源码路径差异和报错输入支持“关图后暴露不同 dtype 组合”这一诊断方向。图编译是否融合、转换或绕开该调用仍是待验证解释。不能从一次恢复图模式推导算子实现从未改变，也不能称该校验与所有 CANN 版本无关。

## 验证信号

恢复图模式后的日志片段中，`AclNN_Parameter_Error|aclnnRmsNorm` 匹配计数为 0，并出现两条 `Load weight end`。该观测只覆盖加载阶段；没有 warmup 完成或请求成功信号，不能作为运行修复闭环。

## 适用与失效边界

本卡是路径与输入诊断。恢复图模式可能只是绕开 eager 故障，FP32 的实际产生点未定位。后续旧版本与 eager 的联合复试又出现 `npu_wait_tensor NotImplementedError`，同时改变版本和模式不能用于单因素归因。
