# A股智能荐股系统 - 基于LangChain架构思想

基于LangChain架构思想和千问API构建的智能股票分析推荐系统，使用AKShare获取真实A股数据。

## 功能特点

- ✅ **真实数据**：使用AKShare获取实时A股数据
- ✅ **智能评分**：基于PE估值、股价走势等多维度评分
- ✅ **AI深度分析**：使用千问API进行深度分析
- ✅ **投资组合推荐**：Top 3投资组合建议
- ✅ **LangChain架构思想**：Prompt Template + LLM + Output Parser

## 安装依赖

```bash
pip install -r requirements.txt
```

## 配置API Key

复制 `.env.example` 为 `.env`，填入你的千问API Key：

```
DASHSCOPE_API_KEY=your_api_key_here
```

## 运行系统

```bash
python main.py
```

## 项目结构

```
langchain/
├── main.py                          # 主程序
├── requirements.txt                 # 依赖文件
├── .env                            # 环境变量
├── .env.example                    # 环境变量示例
├── README.md                       # 本文件
└── stock_analyzer/                 # 核心模块
    ├── __init__.py                 # 模块初始化
    ├── real_data.py                 # 真实数据获取（AKShare）
    └── analyzer.py                  # 股票分析器（LangChain架构）
```

## LangChain架构思想

本项目采用了LangChain的核心架构思想：

1. **PromptTemplate** - 提示词模板类（`stock_analyzer/analyzer.py:24-40`）
2. **StrOutputParser** - 输出解析器类（`stock_analyzer/analyzer.py:43-48`）
3. **LLM调用** - 使用dashscope直接调用千问API
4. **Pipeline模式** - prompt格式化 → LLM调用 → 输出解析

虽然由于版本兼容性问题没有直接使用langchain库，但完整保留了LangChain的架构设计思想！

## 免责声明

本系统仅供学习和技术演示使用！
数据仅供学习参考，不构成任何投资建议！
股市有风险，投资需谨慎！
