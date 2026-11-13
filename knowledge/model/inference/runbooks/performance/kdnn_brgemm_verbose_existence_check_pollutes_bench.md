---
{
  "type": "Runbook",
  "title": "KDNN_BRGEMM_VERBOSE 只做存在性判断：设 \"0\" 仍输出逐调用日志污染计时基准",
  "description": "KDNN_BRGEMM_VERBOSE 只做存在性判断，设 \"0\" 仍输出逐调用日志污染计时基准：处置为采样环境移除该变量并在分析器断言日志无 kdnn_verbose 后重采。",
  "tags": [
    "task.debugging",
    "topic.performance.analysis"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": []
}
---
# KDNN_BRGEMM_VERBOSE 只做存在性判断：设 "0" 仍输出逐调用日志污染计时基准


## 摘要

KPTorch 模型推理计时采样（LayerNorm 线程组 + BRGEMM 调优对比）中，matrix.py 显式设置 KDNN_BRGEMM_VERBOSE="0" 仍无法关闭日志：该版 KDNN 的开关是 getenv 存在性判断，"0" 非空即开。远端测量日志实测出现 kdnn_verbose,matmul,brgemm_f32,... 逐调用行，计时采样带上日志开销。处置为采样环境移除该变量并在分析器断言日志无 kdnn_verbose 后重采（重采样 rc=0 推进；断言全量跑通未在轨迹内逐条确认）。

## 适用场景

对使用 KDNN（oneDNN 系）BRGEMM/线程调度做模型推理性能采样（如 KPTorch 插件 + Bert/DLRM eager/compile 计时）的基准测试；任何依赖环境变量开关日志的库参与计时基准时均适用。

## 触发与观测

采样脚本 matrix.py 在环境中显式设置 KDNN_BRGEMM_VERBOSE="0"（期望关闭日志），但远端测量日志实测出现 kdnn_verbose,matmul,brgemm_f32,nthr=16,... 逐调用日志行——计时采样带上了每 matmul 一次的 fprintf 开销，且不同轮次的计时不可比。

## 探针与操作

1) 远端 grep -m 2 kdnn_verbose measurement/<轮次>.log 直接确认日志污染；2) rg 源码 kdnn_brgemm_matmul.cpp 中 kdnn_verbose 定位开关与全部输出点（brgemm_blocking_env/brgemm_f32/brgemm_f32_scratch/brgemm_f32_pack_b）；3) 处置：采样环境移除该变量，并在分析器对每个计时日志断言不含 kdnn_verbose，之后复用已有构建重新采样。

## 机制与判别

机制：开关实现为 const bool verbose = std::getenv("KDNN_BRGEMM_VERBOSE") != nullptr——只判断变量是否存在，不解析值；"0" 同样是非空字符串因此日志开启。判别：与『日志本应开启』不同，这里是设了 "0" 仍开启；与外部负载波动（数百毫秒尖刺）不同类，日志开销是恒定叠加项，可通过 grep 日志客观确认。

## 验证信号

补丁应用成功（matrix.py 移除变量、analyze.py 增断言、resume.py 重跑编排），重采样按轮次 DONE rc=0 推进；『计时日志中无 kdnn_verbose』为会话内确认，断言全量跑通未在轨迹内逐条复核。验证层级：performance（计时重采）+ source_read（源码开关读出）。

## 适用与失效边界

适用于该版本 KDNN 的存在性判断式开关；若上游已改为值解析（getenv 后比较字符串），设 "0" 即可关闭、本规则失效。基准采样卫生的一般化边界：计时环境中一切以存在性判断的 *_VERBOSE 变量都应显式移除（而非设 0），并以日志断言兜底。

## 结论与证据边界


现象与机制：采样环境显式设置 KDNN_BRGEMM_VERBOSE="0" 时测量日志仍出现 kdnn_verbose,matmul,brgemm_* 逐调用日志行——该版本 kdnn_brgemm_matmul.cpp 的开关为 const bool verbose = std::getenv("KDNN_BRGEMM_VERBOSE") != nullptr，只做存在性判断，"0" 同样非空而开启日志，计时采样因此带上日志开销


探针：grep 测量日志中 kdnn_verbose（远端 grep -m 2 kdnn_verbose measurement/*.log）直接确认污染；rg 源码 kdnn_brgemm_matmul.cpp 定位 verbose 开关与全部 fprintf 点（brgemm_blocking_env/brgemm_f32/brgemm_f32_scratch/brgemm_f32_pack_b）


处置（会话内已执行）：matrix.py 采样环境移除 KDNN_BRGEMM_VERBOSE（保留 ONEDNN_VERBOSE/DNNL_VERBOSE="0"），analyze.py 对每个计时日志增加 assert "kdnn_verbose" not in log 断言，随后复用已有构建重新采集；补丁应用成功、重采样按轮次 DONE rc=0 推进（日志复核为会话内确认，断言全量跑通未在轨迹内逐条确认）

## 补充机制片段

### 工件 1

```
    const bool verbose = std::getenv("KDNN_BRGEMM_VERBOSE") != nullptr;
    if (verbose) {
        std::fprintf(stderr,
                     "kdnn_verbose,matmul,brgemm_f32,nthr=%d,nthr_used=%d,nthr_k=%d,work=%zu,m_blk=%zu,"
                     "m_chunk=%zu,m_chunks=%zu,storage_n_blk=%zu,compute_n_blk=%zu,n_blk=%zu,n_chunks=%zu,"
```

### 工件 2

```
kdnn_verbose,matmul,brgemm_f32,nthr=16,nthr_used=12,nthr_k=1,work=12,m_blk=8,m_chunk=4,m_chunks=1,storage_n_blk=0,compute_n_blk=32,n_blk=32,n_chunks=12,k_blk=256,k_chunks=3,direct=1,pack_a=0,pack_b=1,blocked_b=0,fused=1,jit_epilogue=0,per_n_scale=0,dst_scale=1,beta=0,merge_batch_m=0,logical_batch=1,logical_m=32,packed_lda=768
```

### 工件 3

```
-                    ONEDNN_VERBOSE="0", DNNL_VERBOSE="0", KDNN_BRGEMM_VERBOSE="0",
+                    ONEDNN_VERBOSE="0", DNNL_VERBOSE="0",

```

### 工件 4

```
+                assert "kdnn_verbose" not in (ROOT / f"measurement/{stem}.log").read_text(), stem

```
