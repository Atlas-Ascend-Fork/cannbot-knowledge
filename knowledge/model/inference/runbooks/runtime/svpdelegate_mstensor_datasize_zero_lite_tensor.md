---
{
  "type": "Runbook",
  "title": "MindSpore Lite SVPDelegate 的 DataSize=0 构造路径与未验证变体",
  "description": "源码审阅发现 MSTensor 深拷贝构造可经 TruncateShape 使 shape 与 data_len 不匹配。来源尝试以 sizes[i] 作为构造字节数，但未验证运行期 DataSize 或推理；另一 lite::Tensor 方案未在本卡完整展示。",
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
# MindSpore Lite SVPDelegate 的 DataSize=0 构造路径与未验证变体


## 适用场景

OpenHarmony MindSpore SVPDelegate NPU 推理中应用调用 OH_AI_TensorGetDataSize 对 Input[0]/Output[0] 均返回 0 字节，导致图像预处理失败。根因是 GetInputs/GetOutputs/Predict 用 MSTensor(name, dtype, shape, nullptr, data_len) 构造张量，该路径经 LiteTensorImpl::CreateTensorImplByDeepCopy → TruncateShape，在 data=nullptr 且 data_len 语义不符时把 shape 截断为 [0]，使 Size() 恒为 0。登记机制片段：给出修复变体：创建点以 UINT8、shape={sizes[i]}、data_len=sizes[i] 构造 MSTensor 并 SetData 指向 MMZ 数据指针，意图修正 DataSize()，但运行结果未验证。

出现同类失败特征（见下节触发与观测）的排查与修复场景；可据构造路径核对 shape/data_len，但本卡没有运行期验证，不应直接作为生产修复采用。


## 触发与观测


### 事实（来源结论）

> 根因机制：MSTensor(name, dtype, shape, nullptr, data_len) 构造走 LiteTensorImpl::CreateTensorImplByDeepCopy，其中 truncated_shape = TruncateShape(shape, type, data_len, false) 后调用 Tensor::CreateTensorByDeepCopy；在 data=nullptr 且 data_len 不匹配时 shape 被截断为 [0]（tensor.cc:628-633 一带），MSTensor::DataSize() → impl_->DataSize() 依赖 shape×dtype 大小因而返回 0，且该路径还会多余 malloc 一块随后即被 SetData 替换的缓冲。


## 探针与操作


核对 MSTensor 构造到 TruncateShape 的调用链，再检查构造后的 shape、DataSize 与底层缓冲所有权。下文保留来源尝试，不能跳过验证照搬。


## 机制与判别


### 机制片段


```
    // Create fresh MSTensors from raw metadata to avoid copying shared_ptrs
    // (MMZ heap corruption makes shared_ptr copies unreliable after NPU alloc)
    const auto &sizes = kernel->GetInputSizes();
    const auto &data_ptrs = kernel->GetInputDataPtrs();
    size_t num = kernel->GetUserInputNum();
    if (sizes.empty() || num == 0) {
      MS_LOG(ERROR) << "SVP kernel has no inputs (sizes=" << sizes.size() << ", num=" << num << ").";
      return {};
    }
    std::vector<MSTensor> result;
    result.reserve(num);
    for (size_t i = 0; i < num && i < sizes.size(); i++) {
      std::vector<int64_t> shape;
      shape.push_back(static_cast<int64_t>(sizes[i]));
      // UINT8 for NPU input (models typically use UINT8 with AIPP)
      // Pass sizes[i] as data_len so DataSize() returns correct byte count
      MSTensor t("", mindspore::DataType::kNumberTypeUInt8, shape, nullptr, sizes[i]);
      if (i < data_ptrs.size() && data_ptrs[i] != nullptr) {
        t.SetData(data_ptrs[i], false);
      }
      result.push_back(std::move(t));
    }
    return result;
```

注：轨迹内存在两代修复——MSTensor 构造 + data_len 变体（意图修正 DataSize，仍有 malloc 与生命周期问题待核对）与最终采用的 lite::Tensor 直接构造方案（后续补丁），本卡未展示后者的完整实现，不能将它作为已验证推荐方案。

## 验证信号


源码读回支持 MSTensor 深拷贝构造与 TruncateShape 的诊断方向。所列修改变体未取得运行期 DataSize、生命周期与 NPU 推理结果，不能声称已经返回正确字节数。最终 lite::Tensor 变体的完整机制不在本卡，需另行补证。

## 适用与失效边界


适用：OpenHarmony MindSpore SVPDelegate NPU 推理中 OH_AI_TensorGetDataSize 对输入/输出张量返回 0 的场景。失效边界：验证层级为 source_read——根因机制（来源结论与登记机制片段：均为源码读回口径；运行期 DataSize 未在轨迹内复测，凡未在轨迹内完成的验证不得据本卡宣称已完成；根因判别依赖 tensor.cc 源码对照。


---
