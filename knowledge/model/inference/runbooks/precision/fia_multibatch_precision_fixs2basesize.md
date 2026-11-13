---
{
  "type": "Runbook",
  "title": "FIA 多 batch 精度失败矩阵与 FixS2BaseSize 静态疑点",
  "description": "ascend910_93 上使用 fused_infer_attention_score（FIA，v2 接口 npu_fused_infer_attention_score_v2）、D=1024 MLA、BAND sparse_mode=4（pre_tokens=511）、page attention（block_size=128）的服务（如 dots.note 模型 + MTP `num_speculative_tokens=3`、`XDG_ENABLE_DECODE_SWA_FIA_OP=1`）。 症状：长序列输出乱码、非确定性；或接入 decode 阶段强制 FIA 后出现精度问题，需要判别是\"多 batch 变长\"还是\"multi-sInnerLoop\"路径。",
  "tags": [
    "task.debugging",
    "topic.attention"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": [
    "a3"
  ]
}
---
# FIA 多 batch 精度失败矩阵与 FixS2BaseSize 静态疑点

## 适用场景

- ascend910_93 上使用 fused_infer_attention_score（FIA，v2 接口 npu_fused_infer_attention_score_v2）、D=1024 MLA、BAND sparse_mode=4（pre_tokens=511）、page attention（block_size=128）的服务（如 dots.note 模型 + MTP `num_speculative_tokens=3`、`XDG_ENABLE_DECODE_SWA_FIA_OP=1`）。
- 症状：长序列输出乱码、非确定性；或接入 decode 阶段强制 FIA 后出现精度问题，需要判别是"多 batch 变长"还是"multi-sInnerLoop"路径。

## 触发与观测


已测 batch=2 的等长与变长用例均出现错误。`kv=[400,400], q=1` 时 batch 0 的 out_max_diff=0.0078，通过；batch 1 的 out_max_diff=0.833、lse_max_diff 约 1e12，失败。`kv=[300,300]` 同样出现 batch 1 错误；`kv=[400,400], q=4` 时两项 batch 均未通过。因此，KV 长度不等不是已证实的必要条件。

## 探针与操作

### 复现路径约定

以下路径已脱敏。历史命令中的变量占位符需由复现者按实际环境替换；Python/JSON 字符串内的占位符不会自动展开。

- `${CONTAINER_NAME}`：复现环境的容器名称或 ID。
- `${CONTAINER_WORKDIR}`：复现容器中的工程工作根目录。
- `${SCRATCH_DIR}`：由复现者创建的本次实验临时目录。


- 变长探针（batch=2 交叉矩阵，golden 为非融合 PyTorch float32 实现，逐 batch 比较 out/lse）：

```text
docker cp ${SCRATCH_DIR}/opencode/fia_varlen_test.py ${CONTAINER_NAME}:${CONTAINER_WORKDIR}/fia_varlen_test.py && docker exec ${CONTAINER_NAME} bash -c "cd ${CONTAINER_WORKDIR} && python fia_varlen_test.py --device 0 --kv0 1200 --kv1 500 --q0 1 --q1 1 --fia-runs 3 --threshold 0.01" 2>&1
```

- 推荐最小复现：batch=2，actualSeqLensKv=[1200, 500]，检查 batch 1 输出；再跑等长对照（[400,400]、[300,300] 等）检查等长条件是否也失败；已测点不能证明与任意 kv_len 都无关；再跑 batch=1 q=1 / q=4 区分 multi-sInnerLoop 问题。
- 测试数据构造要点：actual_seq_kvlen 为累计值（[1200, 1700]）。

## 机制与判别

- 静态疑点代码（修改引入的 FixS2BaseSize 使用不一致，逐字）：

```cpp
uint32_t fixedS2Base3 = FixS2BaseSize(constInfo.s2BaseSize, (uint32_t)info.actS2Size, constInfo.headDim);
info.actualSingleProcessSInnerSize = fixedS2Base3;
if (((s2Cur + 1) * fixedS2Base3) > info.actS2Size) {
    info.actualSingleProcessSInnerSize = info.actS2Size - s2Cur * constInfo.s2BaseSize;  // BUG: 用 constInfo.s2BaseSize 而非 fixedS2Base3
}
```

- 判别链：
  1. tiling 端按全局 max s2Size 计算 sInnerSize_ 写入 constInfo.s2BaseSize；kernel 内 FixS2BaseSize 按 per-batch actSeqLensKv 重算。
  2. CalcParams 边界分支用 constInfo.s2BaseSize、sInnerOffsetDataSize 用 FixS2BaseSize、CalcCurS2StartEndNoSparse/WithSparse 又用 constInfo.s2BaseSize——三处使用不一致存在 offset/读取范围风险，仍需消融验证。
  3. 全等长用例也已失败，因此不能把 FixS2BaseSize 改变值或变长输入认定为必要条件。
  4. 与"非确定性竞态"判别：既有 per-buffer flag（mte21QPIds[4] 的 MTE1_MTE2/MTE2_MTE1 事件对、L0C ping-pong EVENT_ID0/1）未被分析为何失效就直接上 PipeBarrier<PIPE_FIX> 是重型屏障、杀死 preload 流水线；batch≥2 的重复出现的大误差提示继续检查 offset/布局；单靠 LSE 数值不能排除竞态。
- 服务侧触发画像：decode 阶段多请求并发且 KV cache 长度不同（MTP 每请求已生成 token 数不同），与单 batch golden（固定 kv_len）形成测试盲区。

## 验证信号

- 客观信号（来源工具输出）：
  - kv=[400,400] batch 0 OK / batch 1 ERROR（0.833 / 1e12），脚本标签“FAIL - FixS2BaseSize bug confirmed”（标签本身不证明根因），EXIT_CODE=1。
  - kv=[300,300] 同模式（batch 1 = 0.971 / 1e12）。
  - kv=[400,400] q=4 双 batch 全 ERROR（batch 0 也有 0.029/0.0096 误差）。
- run-to-run 非确定性已消除（diff=0），只表明该条件下重复运行一致但仍有精度错误，不能据此证明竞态已消除或错误由屏障引入。

## 适用与失效边界


本卡覆盖 FIA、page attention、D=1024、BAND sparse_mode=4 的来源测试矩阵。FixS2BaseSize 与 constInfo.s2BaseSize 的使用差异是静态疑点，尚未通过隔离修改证明是这些失败的唯一根因。等长失败是必须保留的反例；不能从离散测点推出任意长度或所有 decode 配置必失败。具体 patch 的其他失败点见 [FIA patch 已测负结果](fia_external_patch_kv512_failures.md)。
