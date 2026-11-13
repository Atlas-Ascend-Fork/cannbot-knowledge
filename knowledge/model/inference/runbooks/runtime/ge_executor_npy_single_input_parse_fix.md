---
{
  "type": "Runbook",
  "title": "Qwen-VL 单输入接入 GE 执行器：NPY 解析方案与未完成的运行验证",
  "description": "Qwen-VL只有一个pixel_values输入，而原GE执行器JSON路径构造三个输入。来源完成NPY路由/环境读取的源码修改与重编译；旧二进制的模型加载失败不能证明新输入校验通过，新二进制未见运行返回。",
  "tags": [
    "task.debugging",
    "topic.model_serving"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-13T02:13:38Z",
  "platforms": []
}
---
# Qwen-VL 单输入接入 GE 执行器：NPY 解析方案与未完成的运行验证

## 适用场景

GE执行器接入单输入视觉ONNX模型，现有输入路径却固定按文本模型JSON构造多个输入。来源模型的pixel_values为float32 `[400,1536]`，输出embedding为`[1,512]`；这些尺寸仅属于本例。

## 触发与观测

来源报`InputTensorValidate: inputs.size() == inputs_num, expect 1 actual 3`。模型I/O检查显示一个pixel_values输入，原ParseInput路径按JSON构造三个文本输入，因而需要核对模型描述与实际构造的输入列表。

后续一次运行在默认model.onnx路径报ReadProtoFromBinaryFile失败；当时使用的旧test_acl尚未包含新的ModelPath/InputFile环境读取逻辑。这是独立的模型路径/二进制问题，**不能视为NPY输入校验已通过**。

## 探针与操作

1. 先记录正在执行的test_acl路径、构建身份与实际模型/输入路径；确认程序确实读取了预期参数，而非旧默认值。
2. 用模型I/O描述与输入文件的dtype、shape、布局和字节数做对照，检查构造出的输入vector数量。NPY的首维不应未经模型语义核对就当成通用batch_size。
3. 来源修改方案为在inference_acl.h声明ParseNpyInput，在ParseInput按`.npy`后缀路由，创建单输入，并给测试入口增加ModelPath/InputFile环境读取及本模型输出配置。现有采用证据未提供一个已运行验证的完整NPY加载配方；复用前须实现并核对header版本、字节序、dtype、Fortran/C布局、shape/尺寸溢出及host内存生命周期。
4. 重新编译后在新进程打印实际ModelPath/InputFile及输入Tensor描述，运行同一模型；再以输出shape和数值对照判断是否闭合。以下环境读取节选仅说明路径选择，不实现NPY解析：

```cpp
char* input_file_env = getenv("InputFile");
std::string input_file = (input_file_env != nullptr)
    ? std::string(input_file_env)
    : "./workdir/quest_json/M" + model_id + "/batch_list.json";
char* model_path_env = getenv("ModelPath");
std::string model_path;
if (model_path_env != nullptr) {
    model_path = std::string(model_path_env);
} else if (onnx_module_str != "False") {
    model_path = "./workdir/models/M" + model_id + "/model.onnx";
} else {
    model_path = "./workdir/models/M" + model_id + "/frozen_graph.pb";
}
InferenceAcl infer = InferenceAcl(model_path, session, index, &mu, &cv,
                                model_id, batch_size, cur_dev, thread_num);
infer.Execute(input_file);
```

## 机制与判别

模型加载与输入构造是不同阶段。若加载模型已失败，输入数量校验可能根本没有执行；“先前错误未再打印”不是修复通过的证明。重编译成功与二进制时间戳更新也不证明getenv分支或新解析器已运行。

## 验证信号

已采用的证据为初始输入数量错误、模型I/O和源码核对、源码修改、旧二进制的模型路径失败，以及随后编译警告/二进制更新时间。来源最后提示可以重新运行测试，但没有该新运行的返回。故验证止于源码修改与重编译，没有NPY解析、环境变量读取或端到端推理成功的运行闭环。

## 适用与失效边界

本卡为输入协议与运行产物的诊断记录及待验证方案，不是可直接复制的完整NPY解析器。其他模型的输入名、shape、dtype与输出布局均须重新核对；本例静态改动不能作为跨模型或跨NPY格式的兼容保证。
