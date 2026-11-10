# 模型训练精度排障

- [torch_npu sigtrace golden/check 双跑定界引入 NaN 的 kernel（aten_lowering 白名单单变量）](torch_npu_sigtrace_golden_check_nan.md)：CANN 0923 的 torchtitan-npu 双跑中，摘掉 aten.sigmoid 白名单的 golden 梯度有限，原白名单 check 的 mul_934 出现 NaN；可按 FX 名找到其 producer。sum_30 两侧签名均有限，sigmoid_1 仅 check 侧有限、golden 签名缺失，不能称为双侧通过。需使用新缓存并核对 logger、FX 名和采集覆盖，缺失签名不得按 nan=0 处理。
