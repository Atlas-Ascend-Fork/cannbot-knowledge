# ai framework adaptation

- [onnx framework](onnx_framework/index.md)：>针对Atlas A3 训练系列产品/Atlas A3 推理系列产品，暂不支持ONNX框架算子调用。
- [高级编程概述](overview.md)：本章节内容介绍AI框架调用自定义算子的方法。如下图所示，Pytorch支持单算子和图模式两种，TensorFlow仅支持图模式。
- [PyTorch框架](pytorch_framework.md)：通过PyTorch框架进行模型的训练、推理时，会调用很多算子进行计算。开发者开发的自定义算子如果需要集成部署到PyTorch框架，有如下几种方式：
- [TensorFlow框架](tensorflow_framework.md)：>针对Ascend 950PR/Ascend 950DT，暂不支持TensorFlow框架算子调用。
