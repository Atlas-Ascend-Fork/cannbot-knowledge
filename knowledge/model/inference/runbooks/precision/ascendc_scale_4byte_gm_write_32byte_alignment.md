---
{
  "type": "Runbook",
  "title": "IndexerCompressEpilog 单 scale 读数异常的 workspace 与 host 回写规避",
  "description": "来源中逐行 scale 直接写回后 zeros 用例误差约 0.948；改用 8-float workspace 并同步后由 host 按 slot_mapping 回写，五个用例的 Scale 检查通过。多项机制同时变化，尚不能确认硬件存在通用 32 字节最小搬运限制。",
  "tags": [
    "task.debugging",
    "topic.data_movement"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": []
}
---
# IndexerCompressEpilog 单 scale 读数异常的 workspace 与 host 回写规避

## 适用场景


IndexerCompressEpilog 融合路径中逐行 FP32 scale 输出异常的诊断与临时规避。该记录只覆盖来源实现及所测五个用例，不能推广为所有 AscendC 小于 32 字节写入都非法。

## 触发与观测


来源 zeros 用例的 golden scale 为 1.0，设备读数约为 0.05，最大绝对误差 0.9483817219734192，Scale FAILED。随后同时改变 workspace 布局、写出路径以及 host 回读/散列方式；random、skip_minus1、zeros、extreme、shuffle 五个用例的 Scale 检查全部通过。

## 探针与操作


检查逐行输出地址、有效元素数和写回布局。来源规避方案是每行将 scale 复制为 8 个 float 写入独立 scaleWs，`aclrtSynchronizeStream` 后由 host 读取 `scaleWsHost[i * 8]`，按 slot_mapping 写回。比较改动前后的原始 Scale 误差，不以 Cache 的 PASSED 标签替代 scale 或 FP8 数值验证。

## 机制与判别

### 来源结论

AscendC kernel 将单个 float（4 字节）scale 直写 GM 会得到损坏数据：zeros 用例 Cache PASSED 但 Scale FAILED（Max abs diff 0.9483817219734192，golden scale=1.0 而 kernel 输出≈0.05），来源推测与小粒度写回有关，但未隔离证明因果。修复：kernel 每行把 scale 复制成 8 个 float（32 字节）写入独立 scaleWs workspace（wsScaleGm.SetGlobalBuffer(scaleWsBase + row * 8, 8); DataCopy(wsScaleGm, scalePadUB, 8);），host 在 aclrtSynchronizeStream 后回读 scaleWs 并按 slot_mapping 散列 scaleOutHost[idx] = scaleWsHost[i * 8]；修复后 random/skip_minus1/zeros/extreme/shuffle 5 个用例 Scale 全部 PASSED（random 用例 Max abs diff 0.0），Cache 的字节差异小于 0.12% 并被该测试脚本判 PASSED；差异成因与解码数值正确性未被证明。


### 补充机制片段

### 机制片段

```
__aicore__ inline void Process()
    {
        const uint32_t D = tiling->D;
        const float maxF8 = tiling->maxF8;

        for (uint32_t row = startRow; row < endRow; row++) {
            AscendC::LocalTensor<int32_t> idxUB = idxBuf.Get<int32_t>(8);
            smGm.SetGlobalBuffer(smBase + row, 1);
            AscendC::DataCopyPad(idxUB, smGm,
                {1, static_cast<uint16_t>(sizeof(int32_t)), 0, 0}, {false, 0, 0, 0});
            AscendC::PipeBarrier<PIPE_ALL>();
            int32_t idx = idxUB.GetValue(0);
            if (idx == -1) continue;

            AscendC::LocalTensor<bfloat16_t> xUB = inBuf.Get<bfloat16_t>(D);
            xGm.SetGlobalBuffer(xBase + row * D, D);
            AscendC::DataCopy(xUB, xGm, D);
            AscendC::PipeBarrier<PIPE_ALL>();

            AscendC::LocalTensor<float> xF32UB = f32Buf.Get<float>(D);
            AscendC::Cast<float, bfloat16_t>(xF32UB, xUB, AscendC::RoundMode::CAST_NONE, D);
            AscendC::Abs<float>(xF32UB, xF32UB, D);

            AscendC::LocalTensor<float> amaxUB = amaxBuf.Get<float>(8);
            AscendC::LocalTensor<float> reduceTmp = tmpBuf.Get<float>(D);
            AscendC::ReduceMax<float>(amaxUB, xF32UB, reduceTmp, static_cast<int32_t>(D), false);
            AscendC::PipeBarrier<PIPE_ALL>();

            float amax = amaxUB.GetValue(0);
            float scale = (amax == 0.0f) ? 1.0f : (amax / maxF8);

            AscendC::Cast<float, bfloat16_t>(xF32UB, xUB, AscendC::RoundMode::CAST_NONE, D);

            AscendC::Divs(xF32UB, xF32UB, scale, D);

            AscendC::LocalTensor<fp8_e4m3fn_t> f8UB = outBuf.Get<fp8_e4m3fn_t>(D);
            AscendC::Cast<fp8_e4m3fn_t, float>(f8UB, xF32UB, AscendC::RoundMode::CAST_RINT, D);
            AscendC::PipeBarrier<PIPE_ALL>();

            AscendC::LocalTensor<uint8_t> f8Bytes = f8UB.template ReinterpretCast<uint8_t>();
            __gm__ uint8_t* cacheRaw = reinterpret_cast<__gm__ uint8_t*>(cacheBase);
            cacheGmRaw.SetGlobalBuffer(cacheRaw + idx * D, D);
            AscendC::DataCopy(cacheGmRaw, f8Bytes, D);
            AscendC::PipeBarrier<PIPE_ALL>();

            AscendC::LocalTensor<float> scalePadUB = scalePadBuf.Get<float>(8);
            for (int k = 0; k < 8; k++) scalePadUB.SetValue(k, scale);
            wsScaleGm.SetGlobalBuffer(scaleWsBase + row * 8, 8);
            AscendC::DataCopy(wsScaleGm, scalePadUB, 8);
            AscendC::PipeBarrier<PIPE_ALL>();
        }
    }


```

### 机制片段

```
size_t scaleWsSize = T * 8 * sizeof(float);
    uint8_t *scaleWsDevice = nullptr;
    aclrtMalloc((void **)&scaleWsDevice, scaleWsSize, ACL_MEM_MALLOC_HUGE_FIRST);
    aclrtMemset(scaleWsDevice, scaleWsSize, 0, scaleWsSize);

    for (size_t i = 0; i < outputsInfo.size(); i++) {
        aclrtMallocHost((void **)&outputHost[i], outputsInfo[i].length);
    }

    indexer_compress_epilog_kernel<<<blockNum, nullptr, stream>>>(
        inputDevice[0], inputDevice[1], inputDevice[2], inputDevice[3],
        scaleWsDevice, tilingDevice);
    aclrtSynchronizeStream(stream);

    float *scaleWsHost = new float[T * 8];
    aclrtMemcpy(scaleWsHost, scaleWsSize, scaleWsDevice, scaleWsSize, ACL_MEMCPY_DEVICE_TO_HOST);

    float *scaleOutHost = (float *)outputHost[1];
    uint32_t *slotMappingHost = (uint32_t *)inputHost[1];
    memset(scaleOutHost, 0, outputsInfo[1].length);
    for (uint32_t i = 0; i < T; i++) {
        int32_t idx = (int32_t)slotMappingHost[i];
        if (idx >= 0) {
            scaleOutHost[idx] = scaleWsHost[i * 8];
        }
    }


```

## 验证信号


五个用例的 Scale 检查均 PASSED，其中 random 的最大绝对误差为 0.0。Cache 检查容许的位差异小于 0.12%，阈值为 0.5%；这是该脚本的字节比较判定，不证明“硬件编码固有不同但数值等价”。若要采用该解释，仍需解码后的数值误差分析。

## 适用与失效边界


这是联合修改后的有效规避记录。4 字节搬运对齐问题只是来源中的解释假设，未做独立最小复现或单变量消融。host 回读增加 D2H 与同步开销，性能影响未在本卡验证；其他版本、地址对齐及形状仍需复测。
