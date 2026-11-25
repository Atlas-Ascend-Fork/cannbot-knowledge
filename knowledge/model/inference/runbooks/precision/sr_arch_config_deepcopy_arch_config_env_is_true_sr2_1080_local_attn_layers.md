---
{
  "type": "Runbook",
  "title": "daVinci-MagiHuman sr_1080p 画面异常：SR2_1080 环境变量改写 local_attn_layers 与权重训练架构不匹配",
  "description": "daVinci-MagiHuman（gitcode 移植版，Ascend NPU 推理）超分辨率链路：同一权重下 `example/sr_540p/run_T2V.sh` 输出正常、`example/sr_1080p/run_T2V.sh` 输出画面错误时的根因定位。",
  "tags": [
    "task.debugging",
    "topic.precision"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:04Z",
  "updated_at": "2026-11-20T14:17:04Z",
  "platforms": []
}
---

# daVinci-MagiHuman sr_1080p 画面异常：SR2_1080 环境变量改写 local_attn_layers 与权重训练架构不匹配

## 适用场景

daVinci-MagiHuman（gitcode 移植版，Ascend NPU 推理）超分辨率链路：同一权重下 `example/sr_540p/run_T2V.sh` 输出正常、`example/sr_1080p/run_T2V.sh` 输出画面错误时的根因定位。

## 触发与观测

- 触发（source 0 seq 110，用户报告）：1080p 输出视频画面不对，540p 正常。
- 观测（source 0 seq 250，逐字）：两脚本唯一环境差异是 `SR2_1080`；设为 true 时 `config.py:226-243` 把 `sr_arch_config.local_attn_layers` 从默认 `[]`（全 40 层 GLOBAL attention）改为 32 层 LOCAL——保持 GLOBAL 的仅 `[3, 7, 11, 15, 19, 23, 27, 31]`。

## 探针与操作

- 配置对比探针（source 0 seq 249/250）：离线重放 config.py:229-241 的 layer 列表，量化"32 层改 LOCAL / 8 层 GLOBAL / 默认全 GLOBAL"。
- 行为差异定位（source 0 seq 254）：`dit_module.py:792` `use_local_attn = layer_idx in config.local_attn_layers`；LOCAL 走 `flex_flash_attn_with_cp`（局部窗口），GLOBAL 走 `flash_attn_with_cp`（全局）。
- 修复（source 0 seq 272，逐字 before/after）：删除 config.py 中整个 `if env_is_true("SR2_1080")` 的 local_attn_layers 改写分支（保留 sr_video_txt_guidance_scale 等其他逻辑不动）；pipeline.py/video_generate.py 中其余 SR2_1080 用途（CPU offload 显存管理）保留。
- 验证（source 0 seq 299，逐字）：设 `SR2_1080=true` 实例化 ModelConfig，`base config local_attn_layers: []`、`sr config local_attn_layers: []`——架构保持 GLOBAL。

## 机制与判别

- 机制：SR 权重按默认架构（全 GLOBAL attention）训练；运行时被环境变量改写为 32 层 LOCAL（只能看局部 token），权重期望与运行时注意力范围不一致 → 画面错误。540p 不设该变量故正常——环境变量差异是唯一判别变量。
- 判别强度：配置对比 + attention 分支代码定位 + 修复后配置实例化验证三层闭合；**输出画面本身的修复效果未在本轨迹回测**（验证只到配置层，run_T2V.sh 复跑留给用户）。

## 验证信号

- 源码级+CPU 级（等级：源码审读 + 配置实例化验证，tool_observed）：seq 250 层分布量化输出；seq 299 修复后 SR2_1080=true 下 local_attn_layers 仍为 []，且 CPU offload 相关 8 处 SR2_1080 用例未受影响。
- 缺口：1080p 端到端画面复测未执行；"权重按全 GLOBAL 训练"是从 540p 正常+架构对比推断，无权重侧直接证据。

## 适用与失效边界

- 适用：环境变量驱动的架构覆写类缺陷定位方法（同名权重 + 分辨率差异 → 先 diff 环境变量与 config override 链）；daVinci-MagiHuman SR 链路本身。
- 失效/不覆盖：若存在专为 32-LOCAL 架构训练的 1080p SR 权重，则正确修复是换权重而非删配置（本轨迹未找到此类权重的证据）；CPU offload 相关 SR2_1080 分支行为未验证。

## 附：断言存档

- daVinci-MagiHuman sr_1080p 画面异常根因：sr_1080p 脚本独有地设置 SR2_1080=true，使 config.py:226-243 把 sr_arch_config.local_attn_layers 从默认 []（40 层全 GLOBAL attention）改为 32 层 LOCAL（仅 [3,7,11,15,19,23,27,31] 保持 GLOBAL）；dit_module.py:792 按 layer_idx in local_attn_layers 选择 flex_flash_attn_with_cp（局部）或 flash_attn_with_cp（全局）。SR 权重按全 GLOBAL 架构训练，运行时被改为局部窗口 → 权重与注意力范围不匹配 → 画面错误；540p 未设该变量故正常。

```text
self.sr_arch_config = copy.deepcopy(self.arch_config)
        if env_is_true("SR2_1080"):
            self.sr_arch_config = copy.deepcopy(self.arch_config)
            # fmt: off
            self.sr_arch_config.local_attn_layers = [
                0, 1, 2,
                4, 5, 6,
                8, 9, 10,
                12, 13, 14,
                16, 17, 18,
                20, 21, 22,
                24, 25, 26,
                28, 29, 30,
                32, 33, 34,
                35, 36, 37,
                38, 39,
            ]
            # fmt: on
            self.evaluation_config.sr_video_txt_guidance_scale = 3.5

        return self
```
