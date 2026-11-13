---
{
  "type": "Runbook",
  "title": "GE fast_v2 UT 失败根因：Chain::Set 存指针 vs GetInputValue 小标量 inline 读值的 stub 语义错配",
  "description": "AiKernelLaunchUT 报 Assert ((mix_args) != nullptr) failed / LaunchMixKernelV2 Parameter invalid 的根因在测试 stub 而非生产代码（改 dump_stub.h 无效）：测试用 Chain::Set(reinterpret_cast<void*>(&io_num)) 存指针，而生产 KernelContext 对 ≤8 字节标量从 any_value_.data.inplace 直接读值，栈地址被当 io_num 计算 mix_start 越界返回 nullptr。",
  "tags": [
    "task.debugging",
    "topic.graph_execution"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": []
}
---
# GE fast_v2 UT 失败根因：Chain::Set 存指针 vs GetInputValue 小标量 inline 读值的 stub 语义错配

## 适用场景

适用于 GE/metadef fast_v2 kernel launch 单元测试（gert stub 环境）中 AiCoreLaunchMixKernelV2 报 nullptr 断言、参数无效的排查；也适用于评审他人提出的 dump_stub.h 修改是否对症。


## 触发与观测
UT 失败日志：ProcMixVectorCoreTask Assert ((mix_args) != nullptr) failed、AiCoreLaunchMixKernelV2 ErrorNo 1343225857(Parameter invalid!)。

### 结论与证据边界

GE fast_v2 UT 中 AiCoreLaunchMixKernelV2 报 ProcMixVectorCoreTask Assert ((mix_args) != nullptr) failed（返回 1343225857 Parameter invalid）的根因是测试 stub 与生产 KernelContext 的标量语义错配：metadef kernel_context.h 的 Chain::GetPointer 对 sizeof(T)<=sizeof(void*) 的类型直接 reinterpret_cast(any_value_.data.inplace) 读值，而测试 ai_kernel_launch_unitest.cc 用 Set(reinterpret_cast<void*>(&io_num)) 存的是栈地址——生产 GetInputValue<size_t>(kIoNum) 读到地址值当 io_num 计算 mix_start 越界，GetInputPointer<MixCoreArgs> 返回 nullptr；修改 tests/depends/profiler/src/dump_stub.h 与该用例失败无关。

## 探针与操作
1) 读 metadef inc/external/exe_graph/runtime/kernel_context.h 的 Chain::GetPointer/GetInputValue（≤sizeof(void*) inline 读值）；2) 读 ge/runtime/v2/engine/aicore/launch_kernel/ai_core_launch_kernel.cc 的 UpdateArgs/ProcMixVectorCoreTask（GetInputValue<size_t>(kIoNum) 后按 io_num 算 mix_start）；3) 读测试 ai_kernel_launch_unitest.cc 的 Set 调用与 bg_kernel_launch.cc 生产布局（io_num=clean_output_addrs.size()）。

## 机制与判别
见上方结论原文与下方机制片段；判别性证据与边界适用讨论见“适用与失效边界”节。

### 补充机制片段

```
24:   template <typename T, typename std::enable_if<(sizeof(T) <= sizeof(void *)), int>::type = 0>
25:   const T *GetPointer() const {
26:     return reinterpret_cast<const T *>(any_value_.data.inplace);
27:   }
28:   /**
29:    * 获取Chain中保存的数据的指针
30:    * @tparam T 数据类型
31:    * @return 指向数据的指针
32:    */
33:   template <typename T, typename std::enable_if<(sizeof(T) > sizeof(void *)), int>::type = 0>
34:   const T *GetPointer() const {
35:     return reinterpret_cast<const T *>(any_value_.data.pointer);
36:   }
```

### 补充机制片段

```
    context.value_holder[static_cast<size_t>(kernel::InputCommon::kIoNum)].Set(
        reinterpret_cast<void *>(static_cast<uintptr_t>(io_num)), nullptr);
```

## 验证信号
轨迹内验证方式为断言推演与源码级核对（轨迹内无本地编译执行，Windows UT 环境），无 UT 复跑结果。

## 适用与失效边界
适用：gert::Chain 的 Set/GetPointer/GetInputValue 语义（小标量 inline、大对象 pointer）这一通用机制；生产代码无错、错在测试 stub 未按生产语义构造。局限：大范围 edit 需先核对括号边界（轨迹内一次替换把函数闭合 } 包进替换引入编译错误，用户指出后撤回重改）。
