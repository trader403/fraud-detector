# 🛡️ AI Fraud Detection Engine

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![MCP](https://img.shields.io/badge/MCP-Server-blue)](https://modelcontextprotocol.io)

一个支持**中英双语**的 AI 欺诈文本检测引擎，可精准识别诈骗、钓鱼、虚假招聘、赌博广告等风险内容。提供 REST API 与 MCP 工具，可被其他 AI Agent（如 GitHub Copilot）直接调用。

## Features

- 🌐 **双语支持**：自动识别中英文文本，分别调用专有模型。
- 🧠 **混合检测**：结合 LightGBM 专家模型与中文关键词规则。
- ⚡ **实时响应**：毫秒级返回风险评分、判定（欺诈/正常）和风险等级（low/medium/high）。
- 🔌 **MCP 集成**：通过 MCP 协议，可直接作为工具供 Copilot、Claude Desktop 等 AI 客户端调用。
- 📊 **可解释性**：输出欺诈概率，便于设置阈值和控制误报。

## Quick Start

### 1. Clone the repo
```bash
git clone https://github.com/trader403/fraud-detector.git
cd fraud-detector
