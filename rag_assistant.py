"""
RAG-пайплайн для ИИ-помощника (LangChain 1.0+)
"""

import os
from pathlib import Path

# Импорты для LangChain 1.0+
from langchain_community.document_loaders import TextLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate

# Пытаемся импортировать chains
try:
    from langchain.chains import RetrievalQA
    print("✅ Используется langchain.chains")
except ImportError:
    try:
        from langchain_classic.chains import RetrievalQA
        print("✅ Используется langchain_classic.chains")
    except ImportError:
        print("⚠️ Не удалось импортировать RetrievalQA. Используется упрощённый режим.")
        RetrievalQA = None


class RAGAssistant:
    def __init__(self, knowledge_dir="knowledge_base"):
        self.knowledge_dir = knowledge_dir
        self.vectorstore = None
        self.qa_chain = None
        self.llm = None
        
        # Проверяем папку с базой знаний
        if not os.path.exists(knowledge_dir):
            print(f"⚠️ Папка {knowledge_dir} не найдена. Создаю...")
            os.makedirs(knowledge_dir)
            print(f"✅ Папка {knowledge_dir} создана. Добавьте туда .md файлы.")
            return
        
        # 1. Загружаем документы
        print("📄 Загрузка документов...")
        self.documents = self._load_documents()
        
        if not self.documents:
            print("⚠️ Нет документов для загрузки. Добавьте .md файлы в knowledge_base/")
            return
        
        # 2. Разбиваем на куски
        print("✂️ Разбивка документов на куски...")
        self.chunks = self._split_documents()
        
        # 3. Создаём векторное хранилище
        print("🧠 Создание векторного хранилища...")
        self.vectorstore = self._create_vectorstore()
        
        # 4. Настраиваем LLM
        print("🤖 Подключение Ollama...")
        try:
            self.llm = Ollama(model="gemma3", temperature=0.3)
            # Проверяем доступность
            test_response = self.llm.invoke("test")
            print("✅ Ollama подключена успешно")
        except Exception as e:
            print(f"⚠️ Ошибка подключения Ollama: {e}")
            print("   Убедитесь, что Ollama установлена и модель gemma3 загружена")
            return
        
        # 5. Создаём RAG-цепочку
        if RetrievalQA is not None:
            print("🔗 Создание RAG-цепочки...")
            self.qa_chain = self._create_qa_chain()
        else:
            print("⚠️ RAG-цепочка не создана (нет RetrievalQA). Используется упрощённый режим.")
            self.qa_chain = None
        
        print("✅ RAG-ассистент готов к работе!")
    
    def _load_documents(self):
        """Загрузка документов из папки knowledge_base"""
        try:
            loader = DirectoryLoader(
                self.knowledge_dir,
                glob="**/*.md",
                loader_cls=TextLoader,
                loader_kwargs={"encoding": "utf-8"}
            )
            return loader.load()
        except Exception as e:
            print(f"⚠️ Ошибка загрузки документов: {e}")
            return []
    
    def _split_documents(self):
        """Разбивка документов на куски"""
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            separators=["\n\n", "\n", " ", ""]
        )
        return text_splitter.split_documents(self.documents)
    
    def _create_vectorstore(self):
        """Создание векторного хранилища"""
        try:
            embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
            )
            vectorstore = Chroma.from_documents(
                documents=self.chunks,
                embedding=embeddings,
                persist_directory="./chroma_db"
            )
            return vectorstore
        except Exception as e:
            print(f"⚠️ Ошибка создания векторного хранилища: {e}")
            return None
    
    def _create_qa_chain(self):
        """Создание RAG-цепочки"""
        prompt_template = """
        Ты — ИИ-помощник для сотрудников железнодорожной компании.
        Отвечай на вопросы пользователя, используя информацию из документации.
        
        Если в документации нет точного ответа, скажи: "В документации нет информации по этому вопросу. Обратитесь в службу поддержки."
        
        Контекст из документации:
        {context}
        
        Вопрос пользователя: {question}
        
        Ответ:
        """
        
        prompt = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "question"]
        )
        
        if not self.vectorstore:
            return None
        
        qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vectorstore.as_retriever(search_kwargs={"k": 3}),
            chain_type_kwargs={"prompt": prompt}
        )
        
        return qa_chain
    
    def ask(self, question):
        """Задать вопрос помощнику"""
        if not self.qa_chain:
            return self._simple_ask(question)
        
        try:
            result = self.qa_chain.invoke({"query": question})
            if isinstance(result, dict) and "result" in result:
                return result["result"]
            return str(result)
        except Exception as e:
            return f"⚠️ Ошибка при генерации ответа: {str(e)}"
    
    def _simple_ask(self, question):
        """Упрощённый ответ без RAG (если цепочка не работает)"""
        if not self.vectorstore:
            return "⚠️ База знаний не загружена. Добавьте файлы в knowledge_base/"
        
        # Простой поиск похожих документов
        docs = self.vectorstore.similarity_search(question, k=3)
        if not docs:
            return "❌ Не найдено информации по вашему вопросу."
        
        context = "\n\n".join([doc.page_content for doc in docs])
        prompt = f"""
        Ты — ИИ-помощник для сотрудников железнодорожной компании.
        Отвечай на вопрос, используя информацию из документации.
        
        Информация из документации:
        {context}
        
        Вопрос: {question}
        
        Ответ:
        """
        
        try:
            return self.llm.invoke(prompt)
        except Exception as e:
            return f"⚠️ Ошибка: {str(e)}"


# Тестирование
if __name__ == "__main__":
    print("🔄 Инициализация ИИ-помощника...")
    assistant = RAGAssistant()
    
    if assistant.qa_chain or assistant.vectorstore:
        print("\n✅ Помощник готов! Задайте вопрос:")
        while True:
            question = input("\n❓ Ваш вопрос (или 'выход' для завершения): ")
            if question.lower() in ["выход", "exit", "quit"]:
                break
            print(f"💡 {assistant.ask(question)}")
    else:
        print("❌ Ассистент не готов. Проверьте:")
        print("   1. Папку knowledge_base/ с .md файлами")
        print("   2. Установку Ollama: ollama --version")
        print("   3. Загрузку модели: ollama pull gemma3")