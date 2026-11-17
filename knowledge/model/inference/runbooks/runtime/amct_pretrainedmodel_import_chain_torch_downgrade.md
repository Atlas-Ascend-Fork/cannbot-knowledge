---
{
  "type": "Runbook",
  "title": "AMCT 导入失败：沿 PreTrainedModel 回溯 torchaudio 的 ABI 错配",
  "description": "torch 降级后，PreTrainedModel 的表层导入错误可能由 torchaudio 动态库加载失败引起；记录的依赖修正只闭合导入测试，不宣称 PTQ 已完成。",
  "tags": [
    "task.debugging",
    "topic.model_serving"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-14T18:00:00Z",
  "updated_at": "2026-11-16T05:50:55Z",
  "platforms": []
}
---
# AMCT 导入失败：沿 PreTrainedModel 回溯 torchaudio 的 ABI 错配

## 适用场景

复用 vllm-ascend 容器执行 AMCT 任务，已降级 torch，但镜像中仍有旧的 audio/vision 扩展。

## 触发与观测

compressed_tensors 导入 transformers.PreTrainedModel 失败；完整 traceback 最底层是 torchaudio 动态库 undefined symbol: torch_library_impl。

## 探针与操作

在实际解释器逐层导入并记录 __file__ 与版本，先找最底层异常。核对 AMCT requirements，而不是只根据最外层 ModuleNotFoundError 改 transformers。

原始导入链异常（解释器根目录已参数化）：

```text
  File "<user-site-packages>/compressed_tensors/__init__.py", line 9, in <module>
  File "<user-site-packages>/compressed_tensors/compressors/__init__.py", line 6, in <module>
  File "<user-site-packages>/compressed_tensors/compressors/base.py", line 8, in <module>
    from compressed_tensors.compressors.format import infer_module_format
  File "<user-site-packages>/compressed_tensors/compressors/format.py", line 8, in <module>
    from compressed_tensors.quantization import QuantizationScheme
  File "<user-site-packages>/compressed_tensors/quantization/__init__.py", line 7, in <module>
  File "<user-site-packages>/compressed_tensors/quantization/quant_args.py", line 9, in <module>
    from compressed_tensors.utils import Aliasable
  File "<user-site-packages>/compressed_tensors/utils/__init__.py", line 11, in <module>
  File "<user-site-packages>/compressed_tensors/utils/offload.py", line 18, in <module>
    from compressed_tensors.offload import (
  File "<user-site-packages>/compressed_tensors/offload/__init__.py", line 10, in <module>
    from compressed_tensors.offload.convert import from_accelerate, to_accelerate
  File "<user-site-packages>/compressed_tensors/offload/convert/__init__.py", line 6, in <module>
  File "<user-site-packages>/compressed_tensors/offload/convert/from_accelerate.py", line 15, in <module>
    from compressed_tensors.offload.dispatch import dispatch_with_map
  File "<user-site-packages>/compressed_tensors/offload/dispatch.py", line 22, in <module>
    from transformers import PreTrainedModel
  File "<user-site-packages>/transformers/utils/import_utils.py", line 2262, in __getattr__
  File "<user-site-packages>/transformers/utils/import_utils.py", line 2496, in _get_module
  File "<user-site-packages>/transformers/utils/import_utils.py", line 2494, in _get_module
  File "<user-site-packages>/transformers/modeling_utils.py", line 87, in <module>
  File "<user-site-packages>/transformers/loss/loss_utils.py", line 27, in <module>
  File "<user-site-packages>/transformers/loss/loss_rnnt.py", line 23, in <module>
    import torchaudio
  File "<system-site-packages>/torchaudio/__init__.py", line 7, in <module>
  File "<system-site-packages>/torchaudio/_extension/__init__.py", line 30, in <module>
    _IS_TORCHAUDIO_EXT_AVAILABLE = _load_lib("_torchaudio")
  File "<system-site-packages>/torchaudio/_extension/utils.py", line 56, in _load_lib
    torch.ops.load_library(paths[0])
  File "<user-site-packages>/torch/_ops.py", line 1392, in load_library
OSError: <system-site-packages>/torchaudio/lib/_torchaudio.abi3.so: undefined symbol: torch_library_impl
```

后续导入链诊断函数：本次仅语法检查，不执行安装/卸载或导入探针：

```python
def inspect_import_chain():
    import importlib
    from importlib import metadata
    import traceback
    for name in ('torch', 'torch_npu', 'torchvision', 'torchaudio',
                 'compressed_tensors', 'transformers', 'amct_pytorch'):
        try:
            installed = metadata.version(name)
        except metadata.PackageNotFoundError:
            installed = None
        try:
            module = importlib.import_module(name)
            print(name, 'metadata=', installed, 'loaded=', getattr(module, '__file__', None))
        except Exception:
            print(name, 'metadata=', installed, 'IMPORT_FAILED')
            traceback.print_exc()
    try:
        from transformers import PreTrainedModel
        print('PreTrainedModel', PreTrainedModel.__module__)
    except Exception:
        traceback.print_exc()
```

## 机制与判别

最底层 torchaudio undefined symbol 提示要核对实际加载扩展与 torch 的 ABI。记录安装了 torchaudio 2.7.1；曾卸载 torchvision 0.25.0，但随后仍见系统目录和 0.22.1 安装元数据，不能宣称最终环境完全没有 torchvision。版本元数据也不能代替实际导入路径核验。

## 验证信号

修正后的导入测试退出码为 0，包含 PreTrainedModel OK 与 amct_pytorch OK。PTQ 的启动或用户叙述不能替代最终量化结果，本卡不宣称 PTQ/ppl 验收完成。

## 适用与失效边界

若任务需要 torchvision，应选择匹配版本而不是照搬卸载操作。须区分用户 site-packages 与系统残留库；导入通过不等于算子、设备执行或模型精度通过。
