---
{
  "type": "Runbook",
  "title": "A3+CANN 9.2.0 上 cann-recipes-infer ge_graph 图编译 TBE tiling 失败（E90003/ERR03005）的判别探针与 eager 回退",
  "description": "在 Atlas A3（Ascend 910_9362）+ CANN 9.2.0 + torch_npu 2.10 开发版环境上，cann-recipes-infer 的 qwen3_moe/qwen3_5/deepseek_r1 等 ge_graph 样例统一在权重加载成功后的 decode 图编译阶段以 E90003「Tiling func of op_type … failed」级联 ERR03005 崩溃且退出码仍为 0。判别探针：同环境 eager 执行同 shape npu_rms_norm 成功、ge_graph+EP 与 ge_graph+TP 同败、同环境 npugraph_ex 样例全部正常，证明失败仅限 GE/TBE 图编译链路；多轮环境对比与 22 次历史运行记录把边界定在 CANN 9.2.0 + torch_npu 2.10 组合（各模型 README 分别要求 CANN 9.0.0/9.1.0），报错本身无任何版本提示。回退方案：将 YAML exe_mode 由 ge_graph 改为 eager（临时副本），同权重同并行配置全部跑通。",
  "tags": [
    "task.debugging",
    "topic.compilation"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-03T12:00:00Z",
  "updated_at": "2026-11-09T09:37:53Z",
  "platforms": [
    "a3"
  ]
}
---

# A3+CANN 9.2.0 上 cann-recipes-infer ge_graph 图编译 TBE tiling 失败（E90003/ERR03005）的判别探针与 eager 回退

## 适用场景

- 框架/仓库：cann-recipes-infer（统一入口 `executor/scripts/infer.sh`，YAML 中 `exe_mode: "ge_graph"` 走 torchair → GE 图编译链路）。
- 硬件/平台：Atlas A3，Ascend 910_9362 V1，单机 16 卡（4 条轨迹同一台机器 192.168.0.x）。
- 软件：CANN 9.2.0（机器另装有 cann-9.0.0，目录 `/usr/local/Ascend/cann-9.0.0/cann-9.0.0/`）、Python 3.11.15、PyTorch 2.10.0+cpu、torch_npu 2.10.0.post7.dev（0924/1015/1016 三个 nightly 构建）、transformers 5.0.0/5.8.0。
- 涉及模型与样例（均为 ge_graph 模式）：qwen3_moe `qwen3_235b_16tp.yaml`（TP16）、qwen3_5 `qwen3_5_122b_tp8.yaml`（TP8）与 `qwen3_5_397b_tp16.yaml`（TP16）、deepseek_r1 `ci/decode_r1_rank_16_16ep_a8w8c8_mtp.yaml`（EP16 + W8A8C8 + MTP）。
- README 版本要求与实际偏差：qwen3_moe 与 deepseek_r1 的 A3 环境要求 CANN 9.0.0 + torch_npu v26.0.0（2.8.0.post4）+ PyTorch 2.8.0；qwen3_5 的 A3 环境要求 CANN 9.1.0 + torch_npu v26.1.0-beta.1 + PyTorch 2.7.1。实际环境为 CANN 9.2.0 + torch 2.10 开发版栈（本组来源观测判定的失败边界，详见「机制与判别」）。

路径约定：`${LOCAL_PATH_1}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开。使用前在本地设置这些变量；不同编号不可假定为同一位置。代码中的变量样式字符串也须替换，不依赖 Python 自动展开。

## 触发与观测

触发条件：在上述 A3 + CANN 9.2.0 + torch 2.10/torch_npu 2.10 开发版环境执行任一 ge_graph 样例。失败发生在权重加载成功之后的 decode 图编译阶段（权重加载 51s–888s 不等，编译开始后 ~70–91s 崩溃），所有 rank 同错。

失败特征：在 Atlas A3（Ascend 910_9362）+ CANN 9.2.0 + torch 2.10.0/torch_npu 2.10.0.post7.dev 环境上，cann-recipes-infer 的 qwen3_moe（TP16）、qwen3_5（122B TP8 / 397B TP16）、deepseek_r1（W8A8C8+MTP）ge_graph 样例均在权重加载成功后的 decode 图编译阶段以 E90003「Template constraint … Tiling func of op_type … failed」级联「ERR03005 GRAPH internal error」崩溃，且 infer.sh 退出码仍为 0

四条轨迹的逐字失败签名（qwen3_moe 16tp，RmsNorm tiling，日志 `models/qwen3_moe/res/20261017/qwen3_moe_qwen3_235b_16tp/log_0.log`）：

```
[rank0]: RuntimeError: [PID: 2271288] 2026-10-17-01:05:23.490.641 Inner_Error_Compile_Fail(E90003): Compile operator failed, cause: Template constraint, detailed information: Tiling func of op_type RmsNorm failed, failure details:
[rank0]: Compile_info: {'device_id': '0', '_cube_vector_core_type': 'AiCore'}
[rank0]: Inputs: {'shape': (1, 1, 128), 'ori_shape': (1, 1, 128), 'format': 'ND', 'sub_format': 0, 'ori_format': 'ND', 'dtype': 'bfloat16', 'addr_type': 0, 'total_shape': [1, 1, 128], 'slice_offset': (), 'L1_addr_offset': 0, 'L1_fusion_type': -1, 'L1_workspace_size': -1, 'valid_shape': (), 'split_index': 0, 'atomic_type': '', 'input_c_values': -1, 'range': [[1, 1], [1, 1], [128, 128]], 'param_name': 'x_in__'}
[rank0]:         Failed to compile Op RmsNorm_2. oppath is /usr/local/Ascend/cann-9.2.0/opp/built-in/op_impl/ai_core/tbe/impl/ops_nn/dynamic/rms_norm.py Compile failed with errormsg/stack:  and optype is RmsNorm.
```

失败随后级联到大量基础与融合算子的「failed to recompile single op[…]」（GroupedMatmul/MatMul/Mul/Cast/RealDiv/Add/ReduceSum/SplitV/ScatterNdUpdate/ApplyRotaryPosEmb/SwiGlu/MoeInitRoutingV3/MoeGatingTopKSoftmax/MoeFinalizeRoutingV2/InplaceAddRmsNorm/trans_Cast 等），最终：

```
[rank0]:         Call OptimizeFusedGraph failed, ret:4294967295, engine_name:AIcoreEngine, graph_name:partition1_rank...
[rank0]:         [Compile][Graph]Compile graph failed, error code:1343225857, session_id:0, graph_id:0[FUNC:CompileGraph][FILE:ge_api.cc][LINE:1185]
[rank0]: [ERROR] 2026-10-17-01:05:26 (PID:2271288, Device:0, RankID:0) ERR03005 GRAPH internal error
EXIT_CODE=0
```

不同模型的首个 tiling 失败算子不同，但失败形态完全同构（同一台机器、同一 CANN 9.2.0）。qwen3_5（122B TP8，来自 `models/qwen3_5/res/20261016/qwen3.5_qwen3_5_122b_tp8/log_0.log`，失败算子为 Gated DeltaNet 的 depthwise Conv2D 与 TransData）：

```
[rank0]:         Failed to compile Op Conv2D. oppath is /usr/local/Ascend/cann-9.2.0/opp/built-in/op_impl/ai_core/tbe/impl/ops_legacy/conv2d.py Compile failed with errormsg/stack:  and optype is Conv2D.
[rank0]: [OP_TILING] Attrs: [{'name': 'src_format', 'dtype': 'str', 'value': 'FRACTAL_Z'}, {'name': 'dst_format', 'dtype': 'str', 'value': 'FRACTAL_Z'}, {'name': 'src_subformat', 'dtype': 'int64', 'value': 0, 'is_default_value': True}, {'name': 'dst_subformat', 'dtype': 'int64', 'value': 0, 'is_default_value': True}, {'name': 'groups', 'dtype': 'int64', 'value': 1536}].
[rank0]:         Failed to compile Op trans_Transpose_4trans_TransData_5. oppath is /usr/local/Ascend/cann-9.2.0/opp/built-in/op_impl/ai_core/tbe/impl/ops_legacy/dynamic/trans_data.py Compile failed with errormsg/stack:  and optype is TransData.
```

qwen3_moe 在另一天（2026-10-14）的同一环境上首个失败算子则是 AutoTiling（Mul/Cast），同样位于 cann-9.2.0 的 TBE legacy 实现目录：

```
201:[rank0]: RuntimeError: [PID: 3138611] 2026-10-14-23:11:28.840.424 Inner_Error_Compile_Fail(E90003): Compile operator failed, cause: Template constraint, detailed information: Tiling func of op_type AutoTiling failed, failure details:
215:[rank0]:         Failed to compile Op Mul_1. oppath is /usr/local/Ascend/cann-9.2.0/opp/built-in/op_impl/ai_core/tbe/impl/ops_legacy/dynamic/mul.py Compile failed with errormsg/stack:  and optype is Mul.
221:[rank0]:         Failed to compile Op Cast_3. oppath is /usr/local/Ascend/cann-9.2.0/opp/built-in/op_impl/ai_core/tbe/impl/ops_legacy/dynamic/cast.py Compile failed with errormsg/stack:  and optype is Cast.
```

deepseek_r1 的 CI 用例（W8A8C8+MTP+ge_graph）失败算子列表为 Cast/GatherV2/Index/DynamicQuant/AddRmsNormDynamicQuant/DequantSwigluQuant/MlaPrologV3/QuantBatchMatmulV3/RmsNorm/TransposeBatchMatMul，Compile_info 中可见 `'_only_const_tiling': True, '_is_const_shapes': False`。设备端 plog 同窗口出现 TEFUSION `[ERROR] Failed to compile node [...]`（Cast/TransData/Add 等）与 GE `DoOpTilingForCompile: ErrorNo: 4294967295(failed)TbeOpTilingPyInterfaceOld failed.`，qwen3_5 环境还伴随 AICPU `Fill kernel data type [27] is not supported`。

注意：`infer.sh` 的 `launch_infer_task` 以裸 `wait` 结束且 `check_result` 未被调用，因此上述致命失败对外退出码仍为 0，自动化必须解析日志而非依赖退出码（4 条轨迹均观测到此行为）。

## 探针与操作

**判别探针（区分「算子不可执行」与「GE 图编译链路失效」）**：在干净环境（env -i，仅注入待测 Python 与 CANN 路径）中用 eager 路径执行与失败签名完全同 shape/dtype 的算子（qwen3_moe 的失败签名为 RmsNorm x=(1,1,128) bf16, gamma=(128,) bf16, epsilon=1e-6）：

```
env -i HOME=$HOME PATH=${LOCAL_PATH_1} ASCEND_TOOLKIT_HOME=/usr/local/Ascend/cann-9.2.0 bash -c 'source /usr/local/Ascend/cann-9.2.0/bin/setenv.bash; python3 -c "
import torch, torch_npu
import torch_npu.distributed as dist
x = torch.randn(1, 1, 128, dtype=torch.bfloat16, device=\"npu:0\")
gamma = torch.randn(128, dtype=torch.bfloat16, device=\"npu:0\")
out = torch_npu.npu_rms_norm(x, gamma, epsilon=1e-6)
print(\"eager aclnnRmsNorm OK:\", out[0].shape)
\"' 2>&1 | tail -3
```

判别探针：同环境用 eager 路径执行同 shape 的 torch_npu.npu_rms_norm（(1,1,128) bf16）返回「eager aclnnRmsNorm OK: torch.Size([1, 1, 128])」，证明失败仅限 GE/TBE 图编译链路（tiling/单算子重编译），算子 aclnn 执行路径本身可用

**eager 回退（可用路线）**：对失败样例的 YAML 做临时副本，仅把 exe_mode 改为 eager（原样例不动，测试后删除副本）：

```
sed 's/exe_mode: "ge_graph"/exe_mode: "eager"/' models/qwen3_5/config/qwen3_5_122b_tp8.yaml > models/qwen3_5/config/qwen3_5_122b_tp8_eager_retry.yaml && grep exe_mode models/qwen3_5/config/qwen3_5_122b_tp8_eager_retry.yaml
```

eager 回退：将 YAML 的 exe_mode 由 "ge_graph" 改为 "eager"（临时副本 YAML，不动原样例）即可让同权重同并行配置全部跑通——qwen3_moe EP16 decode 平均 295.44 ms/token、qwen3_5 122B TP8 87.34 ms/token、397B TP16 133.66 ms/token，16 rank 零 ERROR（以上均为单次观测）

**环境对比定界（不可采用的失败路线，如实记录）**：为验证「README 推荐组合是否可解」，在同一机器上尝试了三轮组合（来源记录）：

1. `recipes_infer_py311`（torch 2.10.0 + torch_npu 2.10.0.post7.dev20261016）+ CANN 9.2.0：原失败（RmsNorm tiling，ERR03005）。
2. `jf_test_py311`（torch 2.8.0 + torch_npu 2.8.0.post4 = README 要求的 v26.0.0）+ CANN 9.0.0：无法启动——先报 `ASCEND_RUNTIME_PATH : /usr/local/Ascend/cann-9.0.0/runtime does not exist`（9.0.0 真实安装根为嵌套的 `cann-9.0.0/cann-9.0.0/`），修正路径后混载环境报 `ImportError: /usr/local/Ascend/cann-9.0.0/cann-9.0.0/lib64/libaihac_ir.so: undefined symbol: _ZN2ge5proto32_TmpBufDescDef_default_instance_E`（会话残留 9.2.0 库路径混载），`env -i` 干净重试则报：
3. `jf_test_py311` + CANN 9.2.0：与第 1 轮在同一 RmsNorm tiling 位置失败（ERR03005）。

deepseek_r1 轨迹对 CANN 9.0.0 的尝试同样失败于 torch_npu 2.10 与 9.0.0 的二进制不兼容（libaihac_ir.so undefined symbol），因此「回退 CANN 9.0.0 验证」路线在本机不可行。

## 机制与判别

**失败机制**：ge_graph（torchair GE 后端，对应 max-autotune）在 warm-up decode 图编译（`Compile model interface: <Model>.main_decode`）时触发 TBE 单算子编译/tiling；CANN 9.2.0 的 TBE 动态算子实现（`/usr/local/Ascend/cann-9.2.0/opp/built-in/op_impl/ai_core/tbe/impl/...`）对特定输入（如 RmsNorm (1,1,128) bf16、depthwise Conv2D groups=1536、TransData FRACTAL_Z）抛出 `Template constraint` tiling 失败（E90003），`OptimizeFusedGraph` 返回 4294967295，子图分区断言失败，图编译以 error code 1343225857 / ERR03005 终止。eager 路径走 aclnn 二进制算子（如 aclnnRmsNorm），不经 TBE tiling，故不受影响；npugraph_ex 路径（deepseek_r1 样例 1/2，同样包含 MlaPrologV3 等融合算子）也完全正常。

**可区分的解释分支与判别证据**：

- 分支 A「模型/仓库代码缺陷」——被排除：同一 deepseek_r1 CI 用例在 2026-09-23、同一 CANN 9.2.0 上有成功记录（输出 `main and MTP model average inference time cost is 124.50 ms`，日志及后续失败时间线见本卡 [deepseek_r1 历史回归证据](#deepseek_r1-历史回归证据)）；eager 同权重同并行跑通；四条轨迹跨 3 个模型、跨 4 天复现，仓库与 upstream 同步。
- 分支 B「torch_npu 版本问题」——被排除：torch_npu 2.10.0.post7.dev 与 2.8.0.post4（README 要求）在 CANN 9.2.0 上同样失败，三轮环境对照及导入失败原文见本卡 [版本组合边界](#版本组合边界)。
- 分支 C「CANN 9.2.0 + torch 2.10 栈的 ge_graph 编译回归（环境组合边界）」——当前最优解释：与 README 推荐组合（CANN 9.0.0/9.1.0 + torch_npu v26.x + PyTorch 2.7/2.8）不符的环境上，TBE tiling 模板约束失败必现；0924 更换 nightly 后该 CI 用例从「偶发成功」转为「持续失败」也支持环境栈回归。未能在推荐组合上完成正向验证（本机 cann-9.0.0 缺组件），故「CANN 9.0.0/9.1.0 下 ge_graph 正常」仍是假设而非结论。

### 版本组合边界

三轮环境对比：torch 2.10.0 + torch_npu 2.10.0.post7.dev20261016 + CANN 9.2.0 与 torch 2.8.0 + torch_npu 2.8.0.post4（README 要求的 v26.0.0）+ CANN 9.2.0 在同一 RmsNorm tiling 位置失败，失败与 torch_npu 版本无关；README 要求的 CANN 9.0.0 组合在本机不可搭建——torch_npu 2.8.0.post4 的 libtorch_npu.so 动态依赖 libom2_executor.so，该库仅存在于 cann-9.2.0 而 cann-9.0.0 安装中没有（ImportError: libom2_executor.so: cannot open shared object file: No such file or directory）

cann-9.0.0 + torch_npu 2.8.0.post4 组合失败的逐字证据（干净 env -i 环境）与库搜索结果：

```
ImportError: libom2_executor.so: cannot open shared object file: No such file or directory

/usr/local/Ascend/cann-9.2.0/aarch64-linux/lib64/libom2_executor.so
/usr/local/Ascend/cann-9.2.0/aarch64-linux/lib64/libaihac_ir.so
/usr/local/Ascend/cann-9.0.0/cann-9.0.0/aarch64-linux/lib64/libaihac_ir.so
```

（ldd 进一步显示 `libtorch_npu.so => libom2_executor.so => /usr/local/Ascend/cann-9.2.0/aarch64-linux/lib64/libom2_executor.so`，即该 wheel 构建时链接的是 9.2.0 的库；cann-9.0.0 的 aarch64-linux/lib64 共 380 个文件、9.2.0 有 448 个，9.0.0 完整安装但确不含 libom2_executor.so。）

### deepseek_r1 历史回归证据

历史回归判别（deepseek_r1 CI 用例 ci/decode_r1_rank_16_16ep_a8w8c8_mtp）：同一用例 2026-09-23 在同一 cann-9.2.0 上成功（main and MTP model average inference time cost is 124.50 ms），2026-09-24 02:47 环境重装 torch_npu nightly 2.10.0.post7.dev20260924 后每次运行均以相同 E90003 失败（历史 22 个运行目录仅 0923 一个 ok=1）；同环境 npugraph_ex 样例（含 MlaPrologV3 融合算子）完全正常，样例 1/2 运行窗口设备端零错误——判定为环境栈（torch_npu nightly + CANN 9.2.0）ge_graph 编译回归而非仓库代码缺陷

历史运行清点与成功记录（逐字）：

```
models/deepseek_r1/res/20260923/deepseek_r1_decode_r1_rank_16_16ep_a8w8c8_mtp: ok=1 fail=0
[INFO][2026-09-23 08:00:00.587][infer.py:126] deepseek_r1 main and MTP model average inference time cost is 124.50 ms
cann-9.2.0
```

（22 个运行目录中：0911/0916/0917/0922/0928 为 ok=0 fail=0，其中 0911 伴随 AI Core Error；0918/0920/0921/0924/0930/1001–1013 全部 fail=3；仅 0923 成功。torch_npu site-packages 目录时间戳为 `Sep 24 02:47`，版本 2.10.0.post7.dev20260924；期间 `models/deepseek_r1`/`executor`/`module` 无相关代码变更提交。）

**可诊断性**：

可诊断性边界：E90003/ERR03005 报错链不包含任何版本提示，而各模型 README 对 A3 的 CANN 要求不同（qwen3_moe 与 deepseek_r1 为 9.0.0、qwen3_5 为 9.1.0），版本组合边界只能靠人工比对 README 与 CANN version.info 确定；ge_graph+EP 与 ge_graph+TP 在 CANN 9.2.0 上同样失败于通用编译错误，无法从报错区分「并行策略不支持」与「环境编译问题」

## 验证信号

以下均为本组来源观测 4 条轨迹内实际观测到的客观信号（平台：Atlas A3 / Ascend 910_9362 ×16，CANN 9.2.0）：

1. 失败复现（trigger）：
   - 来源记录 seq 242/250：qwen3_moe 16tp ge_graph，E90003 RmsNorm tiling → ERR03005（01:05:26）。
   - 来源记录 seq 128/132：同一用例另一天复现，E90003 AutoTiling（Mul_1/Cast_3/ScatterNdUpdate）→ ERR03005（23:11:37）。
   - 来源记录 seq 204/208：deepseek_r1 CI 用例 E90003 → ERR03005（15:05:59）。
   - 来源记录 seq 159/163/174：qwen3_5 122B（05:52:55）与 397B（06:14:29）ge_graph 均 ERR03005，error code 1343225857；ge_graph+EP 约束测试同样失败（06:27:41）。
2. 判别探针（probe/observation）：来源记录 seq 319/320——eager `npu_rms_norm` 同 shape 成功输出 `eager aclnnRmsNorm OK: torch.Size([1, 1, 128])`（单次观测）。
3. 版本定界（discrimination）：来源记录 seq 294/298/305（cann-9.0.0 + torch_npu 2.8.0.post4 import 失败；libom2_executor.so 仅 9.2.0 提供）、seq 316（torch_npu 2.8.0.post4 + CANN 9.2.0 同位失败）；来源记录 seq 216（cann-9.0.0 + torch_npu 2.10 import 失败）、seq 227/231/242（历史 22 次 1 成功 + 0923 成功记录 + nightly 安装时间戳）。
4. eager 回退生效（validation）：
   - 来源记录 seq 170/178：122B TP8 eager 重试 decode 平均 87.34 ms/token、397B TP16 133.66 ms/token（均单次观测，default 数据集 batch 4/1，输出通顺）。
   - 来源记录 seq 324/328/361：qwen3_moe EP16 eager，16 rank 全部 0 ERROR，decode 平均 295.44 ms/token（batch 16，单次观测）。
   - 来源记录 seq 139/158：eager 样例 decode 平均 299.88 ms/token，LongBench 摘要输出通顺。
   - 来源记录 seq 186/197/201/298：npugraph_ex 样例 1/2 正常（47.88/22.25 ms/token，单次观测），运行窗口设备端零错误。
5. 设备端旁证：ge_graph 失败窗口 plog 出现 TEFUSION 单算子编译失败与 `DoOpTilingForCompile ... TbeOpTilingPyInterfaceOld failed`（来源记录 seq 374/377，每编译子进程 777 条 ERROR；来源记录 seq 291/294；来源记录 seq 209）；成功 eager/npugraph_ex 窗口仅每 rank 1 条无害 `libaicpu_const_folding.so not found`（来源记录 seq 381/384/388）。

性能口径说明：上述 decode 时延均为同会话单次观测（不同模型/并行/批大小，互不可比），不构成 ge_graph 与 eager 的性能对比结论——ge_graph 在该环境未获得任何成功运行数据。

## 适用与失效边界

- 适用：A3（910_9362）+ CANN 9.2.0 + torch 2.10/torch_npu 2.10 dev 栈上，cann-recipes-infer ge_graph 样例在 decode 图编译阶段以 E90003/ERR03005（error code 1343225857）失败时的定界与回退。
- 回退条件与代价：exe_mode 改 eager 可恢复功能（本组来源观测 4 轨迹全部验证），但失去图模式性能收益，且本文档不给出 eager vs ge_graph 的性能结论（后者无成功数据）；deepseek_r1 轨迹显示 npugraph_ex 是另一条可用路线（该模型样例）。
- 停止/排查顺序建议：先跑 eager 最小算子复现（区分编译链 vs 执行链）→ 再比对 README 版本要求与 `CANN version.info`、torch/torch_npu 版本 → 若需正向验证 README 组合，先确认 CANN 安装完整性（libom2_executor.so 等 torch_npu 链接依赖），避免混载多版本 CANN 库路径（会以 libaihac_ir.so undefined symbol 形式报错）。
- 失效边界：
  - 本组来源观测未在 CANN 9.0.0/9.1.0 + torch_npu v26.x 推荐组合上完成正向验证，「推荐组合下 ge_graph 正常」是假设；复测时应先确认 CANN 安装完整（含 torch_npu 依赖库）。
  - E90003 tiling 失败也可能由真实的算子 shape/dtype 不支持引起（非版本问题）；本规则的判别依据是「同 shape eager 可执行 + 环境版本偏离 README + 历史成功记录」，三者缺一时应继续排查算子本身。
  - `infer.sh` 退出码恒 0，不能作为成败判据。
  - qwen3_5 的「图模式仅支持 TP」文档约束在本环境无法独立验证（TP 的 ge_graph 也因环境问题失败），不要把通用编译错误直接归因于并行策略。
  - 单机多 CANN 版本共存时，cann-9.0.0 的真实安装根可能是嵌套目录（`cann-9.0.0/cann-9.0.0/`），配置 cann_path 时需注意；README 未提供 CANN 安装完整性自检步骤。
