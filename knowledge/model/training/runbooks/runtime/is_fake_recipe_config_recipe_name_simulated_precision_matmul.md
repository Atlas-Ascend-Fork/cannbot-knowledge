---
{
  "type": "Runbook",
  "title": "torchtitan-npu 伪量化 QAT 移植（a8w8/a8w4/a4w4/a8w4_fp4fp8）：真 fp8 路径零改动、训练侧零环境变量",
  "description": "框架/模型链路：torchtitan-npu-qat 仓（真 fp8 通路仅 Ascend950+/A5 可跑）面向910B兼容目标为 DSV4-mini-1B SFT QAT 移植参考仓纯 torch 伪量化体系：bf16 matmul + fake-quant 复现 fp8/fp4 数值误差。",
  "tags": [
    "task.implementation",
    "topic.implementation.debugging"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:05Z",
  "updated_at": "2026-11-24T01:53:53Z",
  "platforms": [
    "a3"
  ]
}
---

# torchtitan-npu 伪量化 QAT 移植（a8w8/a8w4/a4w4/a8w4_fp4fp8）：真 fp8 路径零改动、训练侧零环境变量

## 适用场景

- 平台范围依据：source 0 seq 675、source 0 seq 777的实际环境/设备记录确认本次为Atlas A3；这里不扩展未记录的产品或版本。

- 本轨迹数值探针的实际设备为Atlas A3（Ascend910_9382，source 0 seq675/745/777）；910B仅为兼容目标或源码背景，本轨迹未单独验证910B设备。

- 框架/模型链路：torchtitan-npu-qat 仓（真 fp8 通路仅 Ascend950+/A5 可跑）面向910B兼容目标为 DSV4-mini-1B SFT QAT 移植参考仓纯 torch 伪量化体系：bf16 matmul + fake-quant 复现 fp8/fp4 数值误差。
- 目标：低 bit QAT 训练 + 伪量化模型导出/评测，参数与原 8bit 传参统一、不加额外环境变量。

## 触发与观测

- 触发：目标仓只有真 fp8 训练通路（`MXfp8MM`/`Hif8MM`/`GMMFunctionMxfp8`/`GMMFunctionHif8`），910B 无法运行；需要伪量化分支（source 0 seq 149 计划）。

## 探针与操作

接入点（`MXLinear.forward` 加 fake 前置分支，真 fp8 路径一行不改，source 0 seq 216 逐字）：

```python
    def forward(self, input):
        w = self.weight
        config = self.config
        if is_fake_recipe(config.recipe_name):
            # Simulated low-precision path (bf16 matmul + fake-quant); no fp8 HW.
            # fwd is always on for a fake recipe; bwd gated by config.qat_bwd.
            y = FakeQuantMM.apply(input, w, config.recipe_name, True, config.qat_bwd)
        elif config.recipe_name == MXLinearRecipeName.FLOAT8_MXFP8:
            y = MXfp8MM.apply(input, w)
```

- 配置面：扩展 `MXLinearRecipeName` 平铺名 `a8w8/a8w4/a4w4/a8w4_fp4fp8`；recipe 走 `MXFP8Converter.Config(recipe_name=...)` 原 8bit 入口；`qat_bwd` 加在 `NPUMXFP8Config`（source 0 seq 146/261）。
- 评测/导出面：`quant_meta.json` 由 Trainer 层落盘；`resolve_fake_quant` 语义为两条独立路径——`--fake-quant auto` 必须命中 meta（忠于训练配置，缺失报错），显式 `<recipe>` 完全按命令行参数且补齐 `--moe-fake-quant`（source 0 seq 2411）。

## 机制与判别

- 伪量化数学纯 torch（`_round_to_e4m3`/`_mx_codes`/`fake_quant_mx`/`fake_quant_mxfp4_to_mxfp8_2d`/`FakeQuantMM`/`GMMFunctionFakeQuant`），任意设备可跑；fwd 恒开、bwd 由 `qat_bwd` 门控（STE）（source 0 seq 114/146/216）。
- 训练侧零 env：kernel/meta/export 均吃显式 recipe 枚举而非 `FAKE_QUANT_*` 环境变量，避免部署态隐式行为（source 0 seq 146）。

## 验证信号

- CPU 数值测试（torch_npu stub，source 0 seq 491，逐字输出）：

```text
2) _round_to_e4m3 vs float8_e4m3fn maxerr(|x|<=448)=0.000e+00
3) fake_quant_mx shape/idempotence OK
4) fp4->fp8 shape OK; rel vs mxfp4=0.0000
5) FakeQuantMM fwd matches F.linear(fake,fake), bwd finite OK
ALL FAKE-QUANT NUMERIC TESTS PASSED
```

- 接线测试（source 0 seq 504，逐字输出）：`1) GMM dispatch routing OK / 2) NPUMXFP8Config fields + gating OK / 3) MXLinear fake routing OK / 4) QAT flavor wiring OK` + `ALL WIRING TESTS PASSED`。
- ufmt 重排后重跑数值+接线测试通过（source 0 seq 633/637）。验证等级为 CPU 参考 + 静态检查；NPU 上 SFT 训练与导出/评测闭环未在本轨迹运行。

## 适用与失效边界

- 伪量化只模拟数值误差（量化-反量化），不等价 fp8 硬件执行的性能与累积行为；`a8w4_fp4fp8` 的 fp4→fp8 组合语义已按参考仓 bit 对齐验证。
- 会话尾部出现 API 连接失败（source 0 seq 2439），导出/评测脚本的实际 NPU 运行未完成。

## 附：断言存档

- MXLinear.forward 增加 is_fake_recipe 前置分支走 FakeQuantMM（fwd 恒开、bwd 由 qat_bwd 门控），真 fp8 MXfp8MM/Hif8MM 路径一行不改；recipe 经 MXFP8Converter.Config 原入口扩展 a8w8/a8w4/a4w4/a8w4_fp4fp8，训练侧零环境变量
