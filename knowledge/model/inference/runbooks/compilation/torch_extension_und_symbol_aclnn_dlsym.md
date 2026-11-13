---
{
  "type": "Runbook",
  "title": "torch extension 导入失败时的 device kernel 未定义符号判别",
  "description": "torch extension 导入报告 kernel_fused_ar_mhc_post 未定义时，用动态符号表区分 UND 引用与定义。来源重编后导入和注册检查通过，但未公开完整修复 diff，也未验证算子数值前向。",
  "tags": [
    "task.implementation",
    "topic.compilation"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": [
    "950"
  ]
}
---
# torch extension 导入失败时的 device kernel 未定义符号判别
## 适用场景
Ascend C 自定义算子仓（ops/ascendc）同时维护 op 包（opc 编译链）与 torch_ops_extension（setuptools c++ 扩展）两条产物线时，extension eager 路径若以 extern "C" 声明直调 device kernel 入口符号。适用 torch 2.12（RTLD_NOW 语义）+ CANN 9.3.0 + Ascend 950PR 环境。
## 触发与观测
- custom_ops_lib.cpython-312-x86_64-linux-gnu.so 的 dynsym 中 kernel_fused_ar_mhc_post 为 UND 引用（139: 0000000000000000 NOTYPE GLOBAL DEFAULT UND kernel_fused_ar_mhc_post）；deepseek venv 下 import custom_ops 抛 ImportError: undefined symbol: kernel_fused_ar_mhc_post——torch 2.12 的 RTLD_NOW 在 import 时立即解析全部未定义符号。
失败现象：

```
==3 kernel_fused dynsym==
                 U kernel_fused_ar_mhc_post
==4 kernel_fused full symtab==
                 U kernel_fused_ar_mhc_post
==5 Comm Run symbol==
==6 readelf dynsyms==
   139: 0000000000000000     0 NOTYPE  GLOBAL DEFAULT  UND kernel_fused_ar_mhc_post
```

同时 deepseek venv 下 import custom_ops 抛 ImportError: undefined symbol: kernel_fused_ar_mhc_post。
## 探针与操作
1. nm -D / readelf -W --dyn-syms 检查 so 的 dynsym 中该符号是否为 UND。
2. 在 Ascend 安装目录与 opp/vendors 下搜索该符号的定义方。
## 机制与判别
- 验证：8-NPU 服务器重编 op 包（aclnn 签名含 3 个 int64 attr）与 extension wheel 后，TORCH_OK / IMPORT_OK / OPS_OK 全部通过，so 内 kernel_fused UND 计数为 0、aclnnFusedArMhcPost dlsym 字符串出现 3 次；提交 f862f7a（6 files changed, 111 insertions, 119 deletions）。
## 验证信号
事件 20949 工具结果（8-NPU 服务器，重编 op 包与 wheel 后）：

```
OPS_OK True
==1 so kernel_fused UND should be gone==
0
==2 so buildid==
    Build ID: 2ac083e8e3d8d90df9e8bdb51b36d94eb8b51fab
==3 aclnn entry present as dlsym string==
3
```

事件 20951：提交 f862f7a（6 files changed, 111 insertions(+), 119 deletions(-)）。
## 适用与失效边界

适用于该 torch 2.12、CANN 9.3.0、Ascend 950PR 工程中的导入/符号诊断。来源提供了重编前后的符号与导入结果，但本卡没有完整的 aclnn/dlsym 修改单元，因此只作为诊断规则，不能当作可直接应用的修复配方。OPS_OK 是注册检查，不代表数值前向或多卡模型验证通过。

## 补充机制片段
### 机制片段
```
==3 kernel_fused dynsym==
                 U kernel_fused_ar_mhc_post
==4 kernel_fused full symtab==
                 U kernel_fused_ar_mhc_post
==5 Comm Run symbol==
==6 readelf dynsyms==
   139: 0000000000000000     0 NOTYPE  GLOBAL DEFAULT  UND kernel_fused_ar_mhc_post
```
### 机制片段
```
OPS_OK True
==1 so kernel_fused UND should be gone==
0
==2 so buildid==
    Build ID: 2ac083e8e3d8d90df9e8bdb51b36d94eb8b51fab
==3 aclnn entry present as dlsym string==
3
```
