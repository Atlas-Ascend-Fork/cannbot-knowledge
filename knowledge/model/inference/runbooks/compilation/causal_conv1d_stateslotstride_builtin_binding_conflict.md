---
{
  "type": "Runbook",
  "title": "causal_conv1d 增加 stateSlotStride 的参数错配：核对项目 schema、包装层与运行扩展",
  "description": "新增stateSlotStride后，运行扩展仍暴露12参数schema，13参数调用被拒绝。核对项目注册、C++包装层、aclnn及实际加载产物；保留回退20/20观测，撤回CANN同名覆盖的通用限制。",
  "tags": [
    "task.debugging",
    "topic.compilation"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-13T02:13:38Z",
  "platforms": []
}
---
# causal_conv1d 增加 stateSlotStride 的参数错配：核对项目 schema、包装层与运行扩展

## 适用场景

vllm-ascend 的 GDN/线性注意力路径为 causal_conv1d 增加 state slot stride，以减少 state scratch 搬运；修改了自定义算子定义、tiling 或 aclnn 接口后，Python 调用仍显示旧参数签名。

## 触发与观测

来源向 `_C_ascend::npu_causal_conv1d_custom` 传入第13个参数，加载的 schema 仍只有12个参数：

```text
expected at most 12 argument(s) but received 13 argument(s)
Declaration: _C_ascend::npu_causal_conv1d_custom(
  Tensor output, Tensor x, Tensor weight, Tensor conv_state,
  Tensor? bias_opt, Tensor? query_start_loc_opt, Tensor? cache_indices_opt,
  Tensor? initial_state_mode_opt, Tensor? num_accepted_tokens_opt,
  int activation_mode, int pad_slot_id, int run_mode) -> Tensor output
```

来源还修改了 op_proto、kernel/tiling 与自建 op_api，随后撤回本轮 causal_conv1d stride 改动。回退后的服务返回20/20请求正确；这证明回退配置在该负载恢复，不证明新增接口已跑通。

## 探针与操作

1. 在已加载该扩展的同一 Python 环境打印实际 schema：

   ```python
   import torch
   print(torch.ops._C_ascend.npu_causal_conv1d_custom.default._schema)
   ```

2. 核对实际加载扩展的文件与构建身份，检查项目注册、C++包装函数、aclnn声明/调用和设备算子定义是否对同一参数达成一致。编辑源码不等于运行进程已加载新扩展。
3. 增加参数时同时核对参数类型、顺序与输出位置，重新编译并在新进程确认 schema 后，再做小输入数值对照和服务验证。不要为绕过参数数量检查而直接省略中间参数。
4. 若选择从 tensor 读取 strides，须核对本版本接口和实际返回。Input-only 声明本身不能作为“必然取不到 strides”的通用依据。

## 机制与判别

来源基线的[项目注册与包装函数](https://github.com/vllm-project/vllm-ascend/blob/251334c84ca9113622f2dbda70cf17867379ab0b/csrc/torch_binding.cpp#L2045)由 vllm-ascend 自己用 `ops.def` 注册上述12参数 schema；同文件包装函数向 aclnn 传递 activation_mode、pad_slot_id、run_mode 三个整数属性。修改 op_proto 不会自动同步这些项目代码或已编译扩展。

因此，这条报错能确定的是**当前加载的 schema 与13参数调用不一致**。它不能证明 CANN 内置定义覆盖了自定义定义，更不能推出“同名算子增加 binding 参数不可行”。项目基线源码也不能代替运行扩展的构建核验。

来源助手关于输出指针被当作 stride、Input-only 无法读取 strides及内置定义覆盖的解释，未与完整运行接口链逐项绑定。本卡将这些内容保留为待核对方向，不作为已定位的根因，也不据此建议修改系统 `libopsproto.so`。

## 验证信号

- 已观察：12/13参数错误及完整旧 schema；回退后 csrc 中本轮 stateSlotStride 改动清理、op_api目录移除，服务存活并通过20/20请求。
- 未验证：同步修改项目 schema/包装层后的新参数调用、stride读取替代方案和优化后的数值/性能。

## 适用与失效边界

本卡是项目自定义算子接口链的排查记录。回退验证不证明新增参数路径成功，也不构成跨 CANN 版本的同名覆盖规则。改变框架、扩展构建或算子包后，应重新核对实际 schema、ABI及设备结果。
