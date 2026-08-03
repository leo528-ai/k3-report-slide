# examples · 合成仿真与防御验证

这些脚本**全部是纯合成仿真**，用带噪声的比较器 + 二分搜索演示"长度旁路"这套数学机制。
**不包含任何真实模型调用、不处理任何加密推理状态（signature）、不联网。** 可直接 `python3` 运行。

| 脚本 | 作用 | 是否碰真实模型 |
|---|---|---|
| `mock_sidechannel_demo.py` | 合成 canary 逐字还原（正例）+ 移除 state 的控制组 | 否（高斯噪声 oracle） |
| `defense_validation.py` | 演示长度归一化/分桶如何把信道正确率打回 0.5 | 否 |
| `blackbox_distillation.py` | 正经蒸馏：只采集 teacher 可见 input→output 轨迹 | 否（mock teacher，可换真实 provider） |
| `DEFENSE.md` | 防御向解读：威胁模型 / 被滥用的 API 行为 / 检测 / 缓解 | 否（纯分析文档） |

## 边界说明

本目录**刻意不提供**任何针对真实模型隐藏推理状态的提取/解封实现。
真实数据中 `reasoning_tokens=0`、`signature=null` 时根本没有可提取的目标（见幻灯片 §14）。
需要蒸馏数据时，走 `blackbox_distillation.py` 的可见轨迹采集路线。

运行：

```bash
python3 examples/mock_sidechannel_demo.py
python3 examples/defense_validation.py
python3 examples/blackbox_distillation.py
```

防御向解读见 `examples/DEFENSE.md`（威胁模型、被滥用的 API 行为、检测信号、按性价比排序的缓解清单，引用上述脚本的真实输出）。
