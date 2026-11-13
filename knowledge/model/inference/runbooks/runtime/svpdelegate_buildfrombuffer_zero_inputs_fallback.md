---
{
  "type": "Runbook",
  "title": "SVPDelegate BuildFromBuffer 成功但 OH_AI_ModelGetInputs 返回 0 输入的定界：SVP fallback 不经 CompileGraph，input_vec_ 从未填充",
  "description": "OpenHarmony MindSpore SVPDelegate NPU 推理中 BuildFromBuffer 成功（Model built successfully, backend=SVP NPU）但 OH_AI_ModelGetInputs 返回 0 个输入导致空指针崩溃。",
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
# SVPDelegate BuildFromBuffer 成功但 OH_AI_ModelGetInputs 返回 0 输入的定界：SVP fallback 不经 CompileGraph，input_vec_ 从未填充


## 适用场景

OpenHarmony MindSpore SVPDelegate NPU 推理中 BuildFromBuffer 成功（Model built successfully, backend=SVP NPU）但 OH_AI_ModelGetInputs 返回 0 个输入导致空指针崩溃。两条纯静态分析轨迹一致定位：ModelImpl::Build 的 SVP fallback 路径在 LoadModelAndCompileByBuf 失败后创建 SVPDelegate 并 BuildFromBuffer，再新建一个 LiteSession 但从不调用 CompileGraph；而 LiteSession::GetInputs() 直接返回 input_vec_，该向量仅由 CompileGraph 内的 InitGraphInputTensors 填充，SVPModelKernel 内部持有的 MSTensor 输入/输出又因 svp_kernel_ 私有无 getter 无法上抛，故 GetInputs 恒为空。修复方向是给 SVPDelegate 暴露 kernel 的输入/输出或在 ModelImpl 层回填，两条轨迹均以分析报告收尾、未在本轨迹内实施代码修复。


出现同类触发特征、需要在缺少执行环境或故障代价高昂时快速定界/排除的排查场景；按下方探针与判别执行即可复用结论。


## 触发与观测


### 事实（来源结论）

> 判别性观察：LiteSession::GetInputs()（lite_session.cc:911）直接 return this->input_vec_；input_vec_ 仅在 CompileGraph 调用链中的 InitGraphInputTensors（lite_session.cc:307 起）被填充；SVP fallback 路径只走 CreateLiteSession→Init→InitDelegate（设置 delegate），从不调用 CompileGraph，因此 input_vec_ 保持为空，ModelImpl::GetInputs() → session_->GetInputs() 返回空向量。


## 探针与操作




（探针的具体命令/代码即下方机制与判别节中逐字引用的机制单元；照原样执行。）


## 机制与判别


### 机制片段


```
// Line 198-204: Normal path — creates session and tries to compile
auto session = std::shared_ptr<lite::LiteSession>(CreateLiteSession(ContextUtils::Convert(ms_context.get())));
auto ret = session->LoadModelAndCompileByBuf(static_cast<const char *>(model_data), model_type, data_size);

// Line 205-261: SVP FALLBACK — when LoadModelAndCompileByBuf fails
if (ret != RET_OK) {
    // Line 207-217: Detect SVP device from context
    auto &device_infos = ms_context->MutableDeviceInfo();
    bool has_svp = false;
    std::string svp_model_path;
    for (auto &dev : device_infos) {
      if (dev->GetDeviceType() == mindspore::DeviceType::kSVP) {
        has_svp = true;
        auto svp_info = std::static_pointer_cast<mindspore::SVPDeviceInfo>(dev);
        svp_model_path = svp_info->GetModelPath();
        break;
      }
    }
    if (has_svp && !svp_model_path.empty()) {
      // Line 221-231: Read .om file from disk
      FILE *fp = fopen(svp_model_path.c_str(), "rb");
      // ... fread into om_buf ...

      // Line 234-249: Create SVPDelegate and BuildFromBuffer
      auto inner_ctx = ContextUtils::Convert(ms_context.get());
      auto svp_delegate = std::make_shared<lite::SVPDelegate>(svp_it->device_info_.svp_device_info_);
      svp_delegate->Init();
      svp_delegate->BuildFromBuffer(om_buf, om_size);  // <-- Creates SVPModelKernel with MSTensors

      // Line 251: Store delegate in context
      inner_ctx->delegate = svp_delegate;

      // Line 253-258: Create NEW session (NO CompileGraph called!)
      auto session2 = std::shared_ptr<lite::LiteSession>(CreateLiteSession(inner_ctx));
      session_.swap(session2);
      return kSuccess;  // <-- BUG: input_vec_ and output_tensor_map_ are EMPTY
    }
}
```


### 事实（来源结论）

> 可区分解释：正常路径由 LoadModelAndCompileByBuf 驱动 CompileGraph 填充 input_vec_，而 SVPModelKernel 的张量经由 BuildFromBuffer 私有持有（svp_kernel_ 无 public getter），且 BuildFromBuffer 与 Build() 不同、不调用 model->Replace() 替换图算子——因此该 0 输入故障是 SVP fallback 数据通路断裂而非 kernel 未建成；修复需在 model_impl.cc 的 SVP build 后把 kernel 输入/输出回填到对外接口（两条轨迹给出的最小改法）。


## 验证信号


## 适用与失效边界


适用：OpenHarmony MindSpore SVPDelegate BuildFromBuffer 成功但 GetInputs 返回 0 输入的静态定界场景。失效边界：结论为两条纯静态分析轨迹的源码读码定位（源码审查），未在本轨迹内实施代码修复，运行期复测不得据本卡宣称已完成；判别依据为 lite_session.cc 与 model_impl.cc 源码对照。


---
