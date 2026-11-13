---
{
  "type": "Runbook",
  "title": "torch fallback bridge 捕获 python_error 时 what() 为空吞掉真实错误：需在 std::exception catch 内 GIL+PyErr_Fetch 提取 pending Python 异常文本，catch pybind11::error_already_set 不命中",
  "description": "fx_converter 的 AbiRunDeferred 对 deferred torch fallback 失败只打印空消息（\"deferred aten.bitwise_and failed: \"），真实 Python 异常被吞。加 typeid 后显示异常类型为 mangled 名 12python_error 且 what() 仍为空；专门 catch pybind11::error_already_set 并提取 e.value() 不命中，可判别该异常把信息留在 pending Python 异常里而非 C++ what()。修复是在 std::exception catch 内 gil_scoped_acquire + PyErr_Occurred/PyErr_Fetch/PyObject_Str(value)/PyErr_Restore，错误消息随即完整显示 \"[py] RunOpApiV2:...SUSPECT REMOTE ERROR, error code is 507057\"，并暴露设备错误507057；故障kernel与错误上报位置是否一致仍需定位。",
  "tags": [
    "task.debugging",
    "topic.graph_execution"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-03T12:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": [
    "910"
  ]
}
---
# torch fallback bridge 捕获 python_error 时 what() 为空吞掉真实错误：需在 std::exception catch 内 GIL+PyErr_Fetch 提取 pending Python 异常文本，catch pybind11::error_already_set 不命中

## 适用场景

- 框架/栈：torch_npu fxrt bridge（`torch-npu/pytorch/fxrt/fxrt/python/pybind/fxrt_bridge/fx_torch_bridge.cc`，torch_npu 2.13.0+git6a32e81 自建 wheel）；消费方为 fx_converter 的 `AbiRunDeferred`（`torch_fallback_abi_client.cc:841`，经 FxTorchError message 缓冲回传）。
- 平台：Atlas 910B3，CANN 9.2.0，Python 3.11（om2_norm_py311_torch313 conda 环境），pybind11 嵌入。
- 触发面：deferred torch fallback（`RunDeferredPlan` 内 `plan->handle.callBoxed(&stack)`）中任何 Python 侧抛错（本例为 NPU 设备错误的 Python 异常）。
- 缺失信息：未在 pybind11 其它版本上验证；`python_error` 类型的确切定义位置（typeid mangled 名 `12python_error`，推断为 12 字符类名）未在轨迹内溯源。

## 触发与观测

- 触发（事件 2444，FXRT ERROR 日志原文）：`TorchFallbackEagerOp: deferred aten.bitwise_and failed: ` —— 冒号后**无任何内容**；`ModelV2Executor::Execute failed, ret=1343225857` 随之出现。
- 空消息的客观确认（事件 2450，`od -c` 输出结尾）：`... e n . b i t w i s e _ a n d  f a i l e d :  \n` —— 消息在 `failed: \n` 处终止，buffer 内无后续字节。

## 探针与操作

修复前（事件 2456 读取 / 事件 2493 的 oldString，`fx_torch_bridge.cc` 原文）：

```
  } catch (const std::exception &e) {
    SetError(error, e.what());
    return -1;
  }
```

探针 1（事件 2493）：在 catch 中加 `typeid(e).name()`。观测（事件 2515）：`RunDeferredPlan exception [12python_error]: ` —— 类型拿到（mangled 名 `12python_error`），what() 仍为空。

探针 2（事件 2518，失败的探针路线）：在 std::exception 之前专门 catch `pybind11::error_already_set` 并用 GIL 提取 `e.value()` 的 repr。观测（事件 2525）：消息**仍**是 `RunDeferredPlan exception [12python_error]: `（走 std::exception 分支，专门 catch 不命中）。

最终修复（事件 2564，写入 `fx_torch_bridge.cc` 的原文，已用 reader 复核）：

```
  } catch (const std::exception &e) {
    std::string detail = e.what();
    {
      // A pybind python_error may carry an empty what(); surface the pending
      // Python exception text so the root cause is not lost.
      pybind11::gil_scoped_acquire ensure_gil;
      if (PyErr_Occurred() != nullptr) {
        PyObject *type = nullptr;
        PyObject *value = nullptr;
        PyObject *traceback = nullptr;
        PyErr_Fetch(&type, &value, &traceback);
        if (value != nullptr) {
          const auto str_obj = PyObject_Str(value);
          if (str_obj != nullptr) {
            const char *text = PyUnicode_AsUTF8(str_obj);
            if (text != nullptr) {
              detail = detail + " [py] " + text;
            }
            Py_XDECREF(str_obj);
          }
        }
        PyErr_Restore(type, value, traceback);
      }
    }
    SetError(error, std::string("RunDeferredPlan exception [") + typeid(e).name() + "]: " + detail);
    return -1;
  } catch (...) {
```

构建部署：torch-npu `bash ci/build.sh --python=3.11`（约 5-6 分钟），pip force-reinstall wheel 并把 `_fxrt_torch_bridge.cpython-311-aarch64-linux-gnu.so` 同步到 `torch_npu/fxrt/`（事件 2521/2524）。

## 机制与判别

- 结论：AbiRunDeferred 失败日志只有 "deferred aten.bitwise_and failed: "，消息为空（od -c 证实 'failed: \n' 之后无任何内容），真实 Python 异常被 C++ catch 吞掉，无法据此定位根因。
- 结论：在 catch 中加 typeid(e).name() 后异常类型显示为 mangled 名 '12python_error' 且 what() 仍为空；专门 catch pybind11::error_already_set 并提取 e.value() 的 repr 不命中（消息仍走 std::exception 分支且为空），可判别该异常不是 error_already_set，而是携带空 what()、把信息留在 pending Python 异常里的类型。
- 判别要点：该链路经callBoxed进入C++后观察到名为 `12python_error` 的std::exception子类，其确切定义和来源没有溯源，不能归属为pybind11的通用异常类型。本次在持有GIL时读取pending PyErr并还原后提取到错误文本；这是一条在该链路得到日志验证的诊断路线。专门catch error_already_set本次未命中，不表示其他链路也不会命中。
- 结论：在 std::exception catch 内先 gil_scoped_acquire，再 PyErr_Occurred/PyErr_Fetch/PyObject_Str(value)/PyErr_Restore 提取 pending Python 异常文本后，错误消息变为 "[py] RunOpApiV2:torch_npu/csrc/framework/OpCommand.cpp:270 NPU function error: SUSPECT REMOTE ERROR, error code is 507057"，该文本暴露了507057设备错误；报错点可能只是异步错误的上报位置，故障kernel及其提交顺序仍需设备日志定位。
- 附加判别价值：不要仅凭bitwise_and是异常上报点就认定其kernel有错。当前日志不足以确定故障发生在第几个launch，更不能把“下一个launch才上报”概括为ASCEND_LAUNCH_BLOCKING的通用行为。

## 验证信号

- 事件 2571（修复后 ASCEND_LAUNCH_BLOCKING=1 运行，run.log grep 原文）：`TorchFallbackEagerOp: deferred aten.bitwise_and failed: RunDeferredPlan exception [12python_error]:  [py] RunOpApiV2:torch_npu/csrc/framework/OpCommand.cpp:270 NPU function error: SUSPECT REMOTE ERROR, error code is 507057` —— 完整 Python 异常文本成功浮出。
- 事件 2515/2525（修复前两次对照）：typeid 路线与 error_already_set 路线的消息均为空 —— 负对照。
- 证据等级：910B3 + CANN 9.2.0 + 自建 torch_npu bridge，单次运行日志观测；正负对照在同会话内完成（三 wheel 版本依次验证，事件 2515→2525→2571）。

## 适用与失效边界

- 适用：已确认存在pending Python异常、但C++ catch只收到空what()的ABI链路；应先核对具体异常类型和所有权，不能按类型名推广到所有pybind11嵌入场景；症状是跨边界错误消息为空。
- 失效边界：仅当 PyErr 状态确实有 pending 异常时文本非空（PyErr_Occurred 为假时 detail 仍为空）；读取/还原PyErr时调用线程必须持有GIL，且当前调用上下文允许安全获取GIL；不是要求进入catch前必须已释放GIL；PyErr_Fetch 后必须 PyErr_Restore，否则吞掉 pending 状态影响上层。
- 无效路线明确标注：catch pybind11::error_already_set + e.value() repr（事件 2518，实测不命中，不可采用）；typeid 路线只能拿到类型名拿不到文本。
- 回退条件：若上游 bridge 改为 error_already_set 直传或 what() 携带文本，此提取可简化；保留pending状态的意图需与上层错误传播契约一起验证；不能仅凭一次日志成功认定所有异常路径长期安全。
