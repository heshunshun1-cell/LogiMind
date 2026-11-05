# FleetMind-LLM

*Logistics Domain-Specific LLM Fine-Tuning with Qwen and LoRA*

用中文物流指令对 Qwen3-0.6B 进行监督微调（SFT + 标准 LoRA），完成两项任务：从运输记录中提取 8 个字段并输出 JSON，以及根据给定的计划和实际交付时间判断是否延误。实验数据来自公开合成数据集 [yogape/logistics-operations](https://huggingface.co/datasets/yogape/logistics-operations)，不含家族业务记录。

## 同一验证集上的四方法对比

验证集含 500 条运单，每条各生成一道提取题（A）和一道延误判断题（B）。规则方法按题中时间戳直接比较，只评测 B。

| 方法 | A 原始回答可解析为 JSON 对象 | A 正确字段 / 4,000 | B 正确数 / 500 | B Macro-F1 |
|---|---:|---:|---:|---:|
| 时间比较规则 | — | — | 500（100%） | 100% |
| Qwen Zero-shot | 1/500 | 7 | 334（66.8%） | 40.05% |
| Qwen Few-shot（每个任务 2 个训练示例） | 500/500 | 3,963 | 311（62.2%） | 54.01% |
| Qwen + LoRA（E1） | 500/500 | 4,000 | 497（99.4%） | 99.32% |

严格评分直接解析完整回答。Zero-shot 多数提取结果带 Markdown 代码围栏，解析失败时该题 8 个字段均计错。仅去除完整围栏后，字段正确数为 **3,759/4,000**。因此严格得分同时反映输出格式与字段内容。[逐题预测](results/phase4/)

## E1、E2、E3 的训练配置与选型

| 实验 | 训练指令数 | 参与 loss 的 token | Val A 正确字段 | Val B 正确题数 |
|---|---:|---|---:|---:|
| E1 | 1,600 | 助手答案及结束标记 | 4,000/4,000 | 497/500 |
| E2 | 4,000 | 完整对话 | 4,000/4,000 | 497/500 |
| E3 | 8,000 | 完整对话 | 4,000/4,000 | 437/500 |

三组均采用 LoRA rank 16、alpha 32、dropout 0.05，训练 3 轮。E1 与 E2 在统一 Val 上持平，因 E1 使用的训练指令较少，在评测 Test 前选定 E1。E3 的 63 道 B 错题中，61 道来自先写实际时间的 `validation_B_2` 模板。这项统计定位了错误集中的句式。现有实验无法分离措辞、时间顺序和训练设置各自的作用。[选型记录](results/phase5/final_model_selection.json)

**最终 Test** 包含 1,000 条留出运单。E1 在 A 的 8,000 个字段上全部正确（其中应为 null 的字段 384/384），B 为 1,000/1,000。该成绩衡量同一合成数据来源、同一任务定义下的表现。[Test 指标](results/phase5/E1_final_test_metrics.json)

## 输入输出示例

验证样本 `LOAD00082237_B` 的记录为「原计划 2024-11-20 21:53:28.179794；实际完成于 2024-11-20 21:25:57.976433」。实际交付早于计划，目标输出如下。

```json
{"delay_label": "on_time"}
```

## 复核结果

解压后，在包含本 README 的目录执行：

```bash
python scripts/verify_results.py
```

该脚本只需 Python 标准库，可从逐题预测复算两张表的核心计数及最终 Test 计数。训练与生成使用 Colab；历史 Notebook 使用 `/content` 和 Drive 路径，并按原实验的 ZIP 文件名加载输入。重新训练需要准备相应输入和 GPU 环境。`requirements.txt` 列出 E1 实验记录的核心包版本，尚未验证全新环境安装。[数据与划分](data/README.md) · [Notebook](notebooks/) · [训练配置及权重 SHA-256](results/training/) · [实验报告](docs/Phase5_Final_Report.pdf)（原报告沿用“数据规模实验”称呼，训练目标差异及解释边界以 [Phase 6 证据说明](docs/Phase6_Evidence_Notes.md) 为准）

## 许可

本项目原创代码以 [MIT License](LICENSE) 发布。数据来自署名的公开合成数据集，其许可和来源见 [数据说明](data/README.md)。Qwen 基座及 adapter 的使用需分别核对模型许可和下载页面。

## 适用范围

- Train、Val、Test 按运单隔离。扩展 Val 保留了旧 Val 200，其中的样本参与过 E1 checkpoint 选择。最终 Test 在选定 E1 后使用。
- 实验只使用一个随机种子。E1 与 E2/E3 同时改变训练指令数与监督范围。E2 与 E3 的监督范围一致，固定轮数下更新步数也随数据量改变。
- Task B 使用已经给出的实际交付时间。将模型用于发车前预测延误或真实运营记录，需要另行验证。
- 已归档 [100 条人工困难题](data/phase4_challenge_100.jsonl)，[逐题预测](results/phase4/phase4_lora_challenge_predictions.jsonl)复算得到 A 字段 400/400、B 正确 45/50。五道错题都先写实际时间，且均晚 1 微秒；这两项条件同时出现。三个 adapter 的权重当前单独保存，公开下载地址待补。
