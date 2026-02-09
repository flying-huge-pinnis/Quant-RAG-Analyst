# Quant-RAG-Analyst

This project, developed using Vibe Coding, supports 2 languages(EN/CH) ​​and features 3 scenarios: screening market stocks using indicators, conducting in-depth analysis of selected stocks, and interpreting financial reports using AI. It is specifically designed for analyzing core assets in the US and Chinese markets.

本项目采用Vibe Coding开发，支持英语/中文两种语言，并包含三种应用场景：利用指标筛选股票、对选定股票进行深度分析以及利用人工智能解读财务报告。它专为分析美国和中国市场的核心资产而设计。
# Scenario 1
In this scenario, you can use two indicators to broaden your selection of US stocks. You can add the selected stocks to your watchlist, or you can directly search for the target stock's code and then add it to your watchlist.
在这个场景中，你可以通过两个指标海选美股中的股票。你可以将选中的股票加入关注池。也可以直接搜索目标股票的编码，然后将它加入关注池。
<img width="1912" height="978" alt="屏幕截图 2026-02-09 141226" src="https://github.com/user-attachments/assets/ecf25853-65dd-41ad-a737-42339ee78813" />
# Scenario 2
In this scenario, you can gain in-depth insights into all the data of a stock in your watchlist, including its price-to-earnings ratio, price-to-book ratio, and volatility. The system scores the stocks based on an algorithm. In addition, the AI ​​automatically reads relevant news from Yahoo and provides its expectations and evaluation of the stock's news flow.
在这个场景中，你可以深入了解一支关注池中的股票的全部数据，包括市盈率、市净率和波动率等等。系统会根据一套算法来为股票打分。除此以外，AI还会自动读取雅虎中的相关新闻，给出对此股票消息面的预期和评价。
<img width="1916" height="952" alt="屏幕截图 2026-02-09 141326" src="https://github.com/user-attachments/assets/ff1ff89a-c1d5-4815-9360-62e34513152d" />
# Scenario 3
In this scenario, you need to upload the financial report you want to read and submit your own Deepseek API key. The AI ​​will then read the financial report and provide in-depth comprehensive analysis.
在这个场景，你需要上传你想要阅读的财报，同时提交你自己的deepseek api key，AI会阅读财报，并给出深入的综合分析。
<img width="1896" height="936" alt="屏幕截图 2026-02-09 141359" src="https://github.com/user-attachments/assets/eb006cd2-1937-4e3b-8688-6a45fbf4ce3b" />
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


