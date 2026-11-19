---
type: Guide
title: LLM微调基准复核：数据身份、参数转发和计时回调
description: 保存九个模型教程的实际入口与样例差异，区分请求的LoRA/精度/编译配置和当前脚本真正接收的参数。
tags:
- task.optimization
- topic.performance.analysis
- topic.compilation
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/benchmarks/llm/baichuan2-7B-Chat/README.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/benchmarks/llm/glm4-9B-chat/README.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/benchmarks/llm/gpt-oss-20B/README.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/benchmarks/llm/llama3&llama3.2/README.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/benchmarks/llm/mamba-codestral-7B/README.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/benchmarks/llm/qwen2vl-2B-Instruct/README.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/benchmarks/llm/qwen3-4B/README.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/benchmarks/llm/sd3/README.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/benchmarks/llm/sdxl-base-1.0/README.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/benchmarks/llm/baichuan2-7B-Chat/run_baichuan2.sh
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/benchmarks/llm/glm4-9B-chat/run_glm4_9B.sh
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/benchmarks/llm/gpt-oss-20B/run_gpt_oss.sh
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/benchmarks/llm/llama3&llama3.2/run_llama3.sh
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/benchmarks/llm/mamba-codestral-7B/run_mamba2.sh
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/benchmarks/llm/qwen2vl-2B-Instruct/run_train.sh
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/benchmarks/llm/qwen3-4B/run_qwen3.sh
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/benchmarks/llm/sd3/run_sd3.sh
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/benchmarks/llm/sdxl-base-1.0/run_sdxl.sh
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/benchmarks/llm/utils/utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/benchmarks/llm/utils/download_hf.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/benchmarks/llm/utils/requirements.txt
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/benchmarks/llm/mamba-codestral-7B/train_mamba2_7B.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/benchmarks/llm/baichuan2-7B-Chat/train_baichuan2_7B.py
  role: implementation
created_at: '2026-11-09T17:03:24Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# LLM微调基准复核：数据身份、参数转发和计时回调

## 固定来源与草稿原因

固定TorchNPU主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf的九个llm基准README、启动脚本、公共计时/下载辅助以及部分Python入口。文档没有完整NPU产品及软件配套矩阵，启动和测量还存在下面的缺口，故draft、platforms为空，不回推发布基线。这里摄取基准复现合同，不把这些教程当已经验证的训练配方；未下载模型、执行远程代码、训练或保存/加载检查点。

## 模型、数据和入口分别识别

| 目录/模型 | 数据说明与本地入口身份 |
| --- | --- |
| Baichuan2-7B-Chat | Alpaca的instruction/input/output经preprocess转换conversations；run_baichuan2.sh→train_baichuan2_7B.py |
| GLM4-9B-Chat | C4 JSONL；真实run_glm4_9B.sh，README的train_glm4_9B.sh不是同名现有入口；文档要求Transformers内置GLM4，非执行模型仓自定义代码 |
| GPT-OSS-20B | C4 JSONL；真实run_gpt_oss.sh→train_gpt_oss_20B.py，README混用run_gpt-oss.sh与train_gpt-oss_4B.py，不能据其文件名判断训练了4B模型 |
| Llama3-8B / Llama3.2-3B | C4 JSONL，改实际model_path/model_name；run_llama3.sh→train_llama3.py |
| Mamba-Codestral-7B | C4 JSONL；run_mamba2.sh→train_mamba2_7B.py，数据参数为data_file而非统一data_path |
| Qwen2-VL-2B-Instruct | cc12m tar转图像目录和训练JSON；run_train.sh→train_qwen2vl.py。README权重文字/链接误写Mamba，而下载命令才写Qwen/Qwen2-VL-2B-Instruct，不能混用 |
| Qwen3-4B-Base | C4 JSONL；run_qwen3.sh→train_qwen3_4B.py |
| SD3 | oldbookillustrations-small的Parquet；run_sd3.sh→train_sd3.py，README标题仍写SDXL，模型身份以SD3权重/脚本区分 |
| SDXL-base-1.0 | 同类Parquet；run_sdxl.sh→train_sdxl_base.py，不与SD3权重/结构互换 |

多个C4段称下载raw，命令实际却指github.com/.../blob/...页面并保存为.json，而上游文件名是.jsonl；须核对真实内容和消费者格式，不能把HTML、JSON数组和JSONL因后缀改名视为相同。外部LlamaFactory/ModelScope/HuggingFace数据与模型未因链接存在而被本知识库摄取。

公共requirements固定Transformers4.57.1、Accelerate1.11.0、PEFT0.17.1、Datasets4.5.0等，也含torchvision0.22.1；这不是与当前TorchNPU主线全部PyTorch版本兼容的证明，不直接安装或拼接最新依赖。

## Shell追加参数并未全部传入Python

九个启动脚本中只有Baichuan结尾转发"$@"。其余八个没有处理或转交额外shell参数，README的bash脚本后加--enable_compile、--npu-backend或--enable_profiler等不会因此进入Python参数解析。应检查实际Python入口和完整argv；不能仅从所敲shell命令或日志文件名宣布已用compile/Profiler。

脚本有MODEL_PATH/DATA_PATH/IMAGE_PATH环境占位或硬编码“your model path”，部分值未加引号；Llama例子固定可见设备3，其余多为0。先核对真实路径、可见/逻辑设备和入口，不将它们当通用部署值。它们还默认打开TORCH_COMPILE_DEBUG、设置兼容实现、清理相对cache并重定向固定日志，缓存/调试/结果身份须与性能比较一起记录；本卡没有清理目录或运行脚本。

## 脚本请求的训练配置不等于优化收益

大部分launcher设batch1/max_steps200与BF16；Baichuan请求LoRA、gradient_checkpointing、序列1024，常见文本例子序列512；Mamba请求LoRA r16/alpha32/dropout0.1、序列256；Qwen2VL请求use_lora=false、冻结vision、BF16、序列2048及像素范围；SDXL请求LoRA rank8、resolution1024。保留每个模型的有效参数，不把LoRA/冻结视觉/全参数训练的时延或显存直接横比，也不把launch参数当类实现全部确认。

README多称NPU默认MLIR、可切DVM/MFusion；已读Baichuan/Mamba入口设置相应环境，AKG另映射MLIR+TORCHINDUCTOR_USE_AKG。当前MLIR加载器有弃用提示，版本/模型能力另查；Shell是否转发、首次生效时机、模型真实compile路径必须分别确认。打开compile不保证整网无graph break，也不自动验证数值或训练收敛。

Baichuan远程自定义代码默认不开启；其Python入口在显式trust且模型路径不是本地目录时要求revision为40位十六进制commit。公共download_hf.py本身没有revision参数，snapshot_download只传repo/cache/local_dir等；固定TorchNPU源码不等于外部模型下载已经固定到某commit，不能把下载示例当已审核代码身份。

## 公共计时与Profiler回调的局限

TimingCallback在on_step_end先取time.time差并入列表，之后才profiler.step和设备同步，所以打印step_time不能无条件代表完整设备完成时间，也不包含该回调后续同步/打印成本。epoch计时又是另一范围。它打印的loss来自最近log_history项，可能不是当前step的新loss。

训练结束时len>100就丢前100步，否则丢前10步，**不是提示文字所称“只保留最后100步”**；总步数<=10时有效列表为空却仍做平均，可能除零。短测不应直接套该摘要，异常/缺输出不能解释成性能为零。

get_profile用wait0、warmup=start、active=end-start+1、repeat1；start/end没有在该辅助函数里校验顺序。NPU路线是Level2、Text+Db、关闭shape/memory/stack等，CUDA路线不同；不能用同一参数名认为采集成本完全一样。有效采集取决于实际callback步进和训练长度，Profiler报告与关闭采集后的性能对照分开。

- [TorchBench计时和摘要](../../inference/guides/optimization/torch_npu/torch_npu_torchbench_measurement.md)
- [AMP与自定义autograd](torch_npu_autocast_and_custom_autograd.md)

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/benchmarks/llm/baichuan2-7B-Chat/README.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/benchmarks/llm/glm4-9B-chat/README.md)（primary）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/benchmarks/llm/gpt-oss-20B/README.md)（primary）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/benchmarks/llm/llama3&llama3.2/README.md)（primary）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/benchmarks/llm/mamba-codestral-7B/README.md)（primary）
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/benchmarks/llm/qwen2vl-2B-Instruct/README.md)（primary）
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/benchmarks/llm/qwen3-4B/README.md)（primary）
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/benchmarks/llm/sd3/README.md)（primary）
- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/benchmarks/llm/sdxl-base-1.0/README.md)（primary）
- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/benchmarks/llm/baichuan2-7B-Chat/run_baichuan2.sh)（implementation）
- [固定来源 11](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/benchmarks/llm/glm4-9B-chat/run_glm4_9B.sh)（implementation）
- [固定来源 12](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/benchmarks/llm/gpt-oss-20B/run_gpt_oss.sh)（implementation）
- [固定来源 13](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/benchmarks/llm/llama3&llama3.2/run_llama3.sh)（implementation）
- [固定来源 14](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/benchmarks/llm/mamba-codestral-7B/run_mamba2.sh)（implementation）
- [固定来源 15](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/benchmarks/llm/qwen2vl-2B-Instruct/run_train.sh)（implementation）
- [固定来源 16](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/benchmarks/llm/qwen3-4B/run_qwen3.sh)（implementation）
- [固定来源 17](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/benchmarks/llm/sd3/run_sd3.sh)（implementation）
- [固定来源 18](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/benchmarks/llm/sdxl-base-1.0/run_sdxl.sh)（implementation）
- [固定来源 19](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/benchmarks/llm/utils/utils.py)（implementation）
- [固定来源 20](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/benchmarks/llm/utils/download_hf.py)（implementation）
- [固定来源 21](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/benchmarks/llm/utils/requirements.txt)（implementation）
- [固定来源 22](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/benchmarks/llm/mamba-codestral-7B/train_mamba2_7B.py)（implementation）
- [固定来源 23](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/benchmarks/llm/baichuan2-7B-Chat/train_baichuan2_7B.py)（implementation）
