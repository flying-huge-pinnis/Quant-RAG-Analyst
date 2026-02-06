import os
import tempfile
import pymupdf4llm
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from openai import OpenAI
import shutil


class RagEngine:
    def __init__(self):
        # 初始化 Embedding
        self.embedding_model = HuggingFaceEmbeddings(
            model_name="BAAI/bge-small-zh-v1.5",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        self.persist_dir = "./chroma_db_temp"
        self.vector_db = None

    def process_pdf(self, uploaded_file):
        """解析 PDF 并入库"""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name

        try:
            if os.path.exists(self.persist_dir):
                shutil.rmtree(self.persist_dir)

            # 解析
            md_text = pymupdf4llm.to_markdown(tmp_path)
            # 适当增大分块，保证数据连贯性
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            chunks = text_splitter.create_documents([md_text])

            self.vector_db = Chroma.from_documents(
                documents=chunks,
                embedding=self.embedding_model,
                persist_directory=self.persist_dir,
                collection_name="current_report"
            )
            return f"✅ 财报已读取，共切分 {len(chunks)} 个关键片段，准备分析..."
        except Exception as e:
            return f"❌ 解析失败: {str(e)}"
        finally:
            if os.path.exists(tmp_path): os.remove(tmp_path)

    def generate_report(self, api_key, lang="English"):
        """
        根据语言自动生成标准化研报
        """
        if not self.vector_db:
            if os.path.exists(self.persist_dir):
                self.vector_db = Chroma(persist_directory=self.persist_dir, embedding_function=self.embedding_model,
                                        collection_name="current_report")
            else:
                return "⚠️ Please upload a PDF first. / 请先上传 PDF。"

        # 1. 广域检索
        search_query = "Financial statements, revenue, net income, profit margin, balance sheet, risk factors, business outlook, management discussion"
        results = self.vector_db.similarity_search(search_query, k=25)

        if not results: return "⚠️ No relevant content found. / 未提取到有效内容。"

        # 2. 组装上下文
        context = "\n\n".join([f"---Excerpt {i + 1}---\n{c.page_content}" for i, c in enumerate(results)])

        # 3. 设定双语 Prompt
        if lang == "English":
            system_prompt = """
            You are a rigorous Wall Street Financial Analyst. Based on the provided financial report excerpts, write a [Deep Investment Research Report].

            Requirements:
            1. **Data Driven**: Extract specific numbers (Revenue, Net Income, Growth Rate, Margins) and present them in Markdown tables.
            2. **Structure**:
               - **1. Financial Highlights** (Key metrics table, YoY changes)
               - **2. Operational Analysis** (Reasons for growth/decline)
               - **3. Risk Factors** (Specific operational or market risks)
               - **4. Future Outlook** (Management guidance)
            3. **Objective & Sharp**: Be direct. Point out issues clearly.
            4. If data is missing, state "Not Disclosed".
            """
            user_msg = f"Please generate a report based on the following excerpts:\n{context}"
        else:
            system_prompt = """
            你是一位严谨的金融分析师。请根据提供的财报片段，写一份【深度投资研报】。

            要求：
            1. **数据优先**：提取具体的营收、净利润、增长率等数字，并制作 Markdown 表格。
            2. **结构化输出**：
               - **一、核心财务摘要**
               - **二、经营亮点与归因**
               - **三、风险提示**
               - **四、未来展望**
            3. **客观犀利**：直接指出问题所在。
            4. 如果文中无相关数据，请注明“未披露”。
            """
            user_msg = f"请基于以下财报原文生成研报：\n{context}"

        # 调用 DeepSeek
        client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        try:
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_msg}
                ],
                temperature=0.2
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"❌ API Error: {str(e)}"