# Quant-RAG-Analyst

This project, developed using Vibe Coding, supports 2 languages(EN/CH) ​​and features 3 scenarios: screening market stocks using indicators, conducting in-depth analysis of selected stocks, and interpreting financial reports using AI. It is specifically designed for analyzing core assets in the US and Chinese markets.

本项目采用Vibe Coding开发，支持英语/中文两种语言，并包含三种应用场景：利用指标筛选股票、对选定股票进行深度分析以及利用人工智能解读财务报告。它专为分析美国和中国市场的核心资产而设计。

# Author's Note

Hello everyone! I am a Master of Commerce at the University of New South Wales (UNSW).

This project, as an exploration for a course assignment, is my attempt at vibe coding, aiming to understand how we can quickly bridge the gap between traditional quantitative finance logic and modern LLM capabilities.

While the code runs well, please consider it a student prototype, not production-ready software.

大家好！我是一个新南威尔士大学（UNSW）金融科技硕士研究生。

本项目作为课程作业的探索，是我的vibe coding尝试，旨在了解如何结合传统量化金融逻辑与LLM。

虽然代码运行良好，但请将其视为学生原型，而非可用于生产环境的软件。

# How to Run

First, you need to download Python and PyCharm.

首先，你需要下载python和pycharm。

Second, download three .py files: `app`, `quant_backend`, and `rag_engine`.

其次，下载app，quant_backend和rag_engine三个py文件。

You need the following libraries to run：

你需要以下库来运行：


streamlit

pandas

yfinance

textblob

pymupdf4llm

langchain-text-splitters

langchain-huggingface

langchain-chroma

openai

chromadb


最后，在你的pycharm中打开它们，在终端输入如下指令：

cd （三个文件所在文件夹，例如“exercises”）

streamlit run app.py



Finally, open them in your PyCharm by entering the following commands in the terminal:

cd (the folder containing the three files, for example 'exercises')

streamlit run app.py


Screen Shot:
<img width="1912" height="978" alt="屏幕截图 2026-02-09 141226" src="https://github.com/user-attachments/assets/ecf25853-65dd-41ad-a737-42339ee78813" />
<img width="1916" height="952" alt="屏幕截图 2026-02-09 141326" src="https://github.com/user-attachments/assets/ff1ff89a-c1d5-4815-9360-62e34513152d" />
<img width="1896" height="936" alt="屏幕截图 2026-02-09 141359" src="https://github.com/user-attachments/assets/eb006cd2-1937-4e3b-8688-6a45fbf4ce3b" />
