# 编译调试（compile-debug）

- [Ascend C 编译失败诊断流程：首错固定、签名判读与原配方验证](failure_diagnosis_flow.md)：四步流程（固定首错→按类别分流→沿原配方读结构化验证证据→停滞 ≥2 轮交接）与版本域五态判定（match/ahead/conflict_in_domain/mismatch/unknown）。
- [Ascend C 工程编译配置的静态预防规则（CMake/头文件/Host 特性/跨文件契约）](static_prevention_rules.md)：find_package(ASC) 与 ASC 语言启用（含 msopgen 宏间接形态）、kernel_operator.h、Kernel 侧禁 host-only 特性、跨文件符号契约、include/driver→pkg_inc/driver 版本敏感迁移。
