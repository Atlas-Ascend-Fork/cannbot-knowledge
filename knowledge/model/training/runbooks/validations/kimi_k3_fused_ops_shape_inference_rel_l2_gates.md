---
{
  "type": "Runbook",
  "title": "Kimi K3 四融合算子 NPU smoke 精度测试落地（从配置提取 shape、逐输出逐梯度对比 + CPU FP64 oracle）与 quick shape 91 用例通过",
  "description": "在 torchtitan-npu ops_test 分支落地 attn_res/conv1d/situ/kda 四融合算子的 NPU smoke 精度测试：从正式 DeepEP 配置动态提取 T=8192、R=131072、H=96 等参数推算单卡输入 shape，统一比较 forward、全部输入梯度和参数梯度，小形状用 CPU FP64 oracle；静态检查通过，服务器 quick shape 91 用例全部通过（生产 shape 仍需另行运行）。",
  "tags": [
    "task.testing",
    "topic.attention"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": []
}
---
# Kimi K3 四融合算子 NPU smoke 精度测试落地（从配置提取 shape、逐输出逐梯度对比 + CPU FP64 oracle）与 quick shape 91 用例通过

## 适用场景

在 torchtitan-npu ops_test 分支落地 attn_res/conv1d/situ/kda 四融合算子的 NPU smoke 精度测试：从正式 DeepEP 配置动态提取 T=8192、R=131072、H=96 等参数推算单卡输入 shape，统一比较 forward、全部输入梯度和参数梯度，小形状用 CPU FP64 oracle；静态检查通过，服务器 quick shape 91 用例全部通过（生产 shape 仍需另行运行）。


kimi k3 在 torchtitan-npu 上接入 attn_res、conv1d、situ、kda 正反向融合算子后，需要一套不执行训练脚本、而是从训练脚本配置推算输入 shape 的对比小算子精度验证方案；适用于融合算子接入后的精度准入门禁与回归。

## 触发与观测

融合算子已接入但"还没有验证这些算子对比小算子实现的精度"，且验证规格必须参考 kimi_k3_fsdp32_ep4_8k_deepep.sh 的配置（不是执行该脚本）。

## 探针与操作

读取训练脚本与配置注册表，确认实际生效的并行/模型/MoE/KDA/AttnRes 参数（注意注释与默认值的差异）；在仓库中定位已有的小算子 reference 实现（model.py 的 AttnRes/SiTU、kda.py 的 causal conv1d 与 chunk/recurrent）作为对照基线；编写测试矩阵后先做静态检查，再进入 NPU 环境执行：

## 机制与判别

方案要点：同 NPU 逐输出逐梯度对比 + 小形状 CPU FP64 oracle 的验证链；shape 从脚本实际生效值推算；支持 quick/full、多 seed、非均匀上游梯度；整训对比为规划项（本轨迹未执行）。执行命令（登记机制片段：，来源记录）：

```bash
cd torchtitan-npu_dev
export ASCEND_LAUNCH_BLOCKING=1
mkdir -p test_reports

python -m pytest -v \
  tests/smoke_tests/ops/test_kimi_k3_shape_spec.py \
  tests/smoke_tests/ops/test_kimi_k3_*_precision.py
```

BF16 门限表未进入本卡登记机制片段：（对应 claim 未被账本采纳），本卡不作门限断言。

**结论要点：**

- 在 torchtitan-npu_dev 的 ops_test 分支落地：新增 AttnRes、SiTU、Conv1d、KDA 单卡 NPU smoke 精度测试，统一比较 forward、全部输入梯度和参数梯度；compare_autograd 改为融合图完成反向并释放后再构造参考图以降低 full shape 峰值内存；从正式 DeepEP 配置动态提取 T=8192、R=131072、H=96 等参数，支持 quick/full、多 seed、非均匀上游梯度和 JUnit 误差记录；补充 KDA cache 开关一致性、FP64 recurrence oracle 及 T=8192 的 4095/4096/8191 Conv1d 边界用例；静态检查（ruff check、ruff format --check、py_compile、git diff --check）通过，提交 fc16086 推送远程 ops_test，合并远程后 HEAD 为 f058706（普通 fast-forward）。

- 服务器 quick shape 执行结果 91 passed in 49.10s（Shape contract 1/1、AttnRes 14/14、Conv1d 37/37、KDA 14/14、SiTU 25/25）；当前结论仅覆盖 quick shape，生产 shape 仍需使用 KIMI_K3_PRECISION_FULL=1 分别运行 seed 0、1、2。

## 验证信号

ops_test 分支静态检查（ruff check、ruff format --check、py_compile、git diff --check）通过；提交 fc16086 推送远程、合并后 HEAD f058706；服务器 quick shape 91 passed in 49.10s（AttnRes 14/14、Conv1d 37/37、KDA 14/14、SiTU 25/25、Shape contract 1/1）。

## 适用与失效边界

quick shape 结论不能外推到生产 shape（需 KIMI_K3_PRECISION_FULL=1 多 seed）；整训对比（loss/grad norm/参数差异门限）在方案中规划但本轨迹未执行；KDA integration 现有 check_loss=False 且无 NPU 数值 golden，需新增测试覆盖。
