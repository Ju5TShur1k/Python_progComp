"""
RAG-пайплайн для ИИ-помощника (LangChain 1.0+)

Изменения по сравнению с исходной версией:
1. Векторная база (Chroma) больше не пересоздаётся с нуля при каждом
   запуске приложения — она сохраняется на диск и переиспользуется,
   если файлы базы знаний не менялись. Раньше эмбеддинги всех
   документов считались заново на каждом старте (самая долгая часть
   инициализации), а при повторных запусках ещё и дублировались в уже
   существующей папке chroma_db.
2. Разбивка документов на куски теперь учитывает markdown-заголовки
   (## / ###), а не режет текст "вслепую" по 500 символам — вопрос и
   ответ из одного раздела больше не попадают в разные чанки, поиск
   точнее находит релевантный кусок.
3. Импорт Ollama больше не использует deprecated-путь
   langchain_community.llms.Ollama.
4. Ретривер использует MMR (Maximal Marginal Relevance) — меньше
   дублирующихся кусков в контексте, ответ точнее укладывается в
   промпт.
"""

import os
import hashlib
from pathlib import Path

from langchain_community.document_loaders import TextLoader, DirectoryLoader
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    MarkdownHeaderTextSplitter,
)
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import PromptTemplate

# Актуальный (не deprecated) путь импорта Ollama.
# Если пакет langchain-ollama не установлен — откатываемся на старый
# путь, чтобы проект не падал, но лучше поставить: pip install langchain-ollama
try:
    from langchain_ollama import OllamaLLM as Ollama
    print("✅ Используется langchain_ollama.OllamaLLM")
except ImportError:
    from langchain_community.llms import Ollama
    print("⚠️ langchain-ollama не установлен, используется устаревший langchain_community.llms.Ollama")
    print("   Рекомендуется: pip install langchain-ollama")

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
    def __init__(self, knowledge_dir="knowledge_base", persist_dir="./chroma_db"):
        self.knowledge_dir = knowledge_dir
        self.persist_dir = persist_dir
        self.vectorstore = None
        self.qa_chain = None
        self.llm = None

        if not os.path.exists(knowledge_dir):
            print(f"⚠️ Папка {knowledge_dir} не найдена. Создаю...")
            os.makedirs(knowledge_dir)
            print(f"✅ Папка {knowledge_dir} создана. Добавьте туда .md файлы.")
            return

        print("📄 Загрузка документов...")
        self.documents = self._load_documents()

        if not self.documents:
            print("⚠️ Нет документов для загрузки. Добавьте .md файлы в knowledge_base/")
            return

        # 2-3. Векторное хранилище: переиспользуем, если база знаний не менялась.
        print("🧠 Подготовка векторного хранилища...")
        self.vectorstore = self._get_or_build_vectorstore()

        print("🤖 Подключение Ollama...")
        try:
            self.llm = Ollama(model="gemma3", temperature=0.2)
            self.llm.invoke("test")
            print("✅ Ollama подключена успешно")
        except Exception as e:
            print(f"⚠️ Ошибка подключения Ollama: {e}")
            print("   Убедитесь, что Ollama установлена и модель gemma3 загружена")
            return

        if RetrievalQA is not None:
            print("🔗 Создание RAG-цепочки...")
            self.qa_chain = self._create_qa_chain()
        else:
            print("⚠️ RAG-цепочка не создана (нет RetrievalQA). Используется упрощённый режим.")
            self.qa_chain = None

        print("✅ RAG-ассистент готов к работе!")

    # ------------------------------------------------------------------
    # Загрузка и разбивка документов
    # ------------------------------------------------------------------

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
        """
        Разбивка документов на куски с учётом markdown-заголовков.
        Сначала режем по ## / ### (каждый раздел вопрос-ответ остаётся
        цельным), затем при необходимости досекаем слишком длинные
        разделы обычным сплиттером.
        """
        header_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[("##", "h2"), ("###", "h3")],
            strip_headers=False,
        )
        fallback_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=100,
            separators=["\n\n", "\n", " ", ""]
        )

        all_chunks = []
        for doc in self.documents:
            try:
                header_chunks = header_splitter.split_text(doc.page_content)
            except Exception:
                header_chunks = [doc]

            for chunk in header_chunks:
                # переносим метаданные исходного документа (например, source)
                chunk.metadata.update(doc.metadata)

            all_chunks.extend(header_chunks)

        # Досекаем слишком длинные куски, короткие оставляем как есть
        final_chunks = fallback_splitter.split_documents(all_chunks)
        return final_chunks

    # ------------------------------------------------------------------
    # Векторное хранилище
    # ------------------------------------------------------------------

    def _knowledge_base_fingerprint(self):
        """Хэш содержимого всех .md файлов — чтобы понять, менялась ли база знаний."""
        h = hashlib.sha256()
        for path in sorted(Path(self.knowledge_dir).rglob("*.md")):
            h.update(path.read_bytes())
        return h.hexdigest()

    def _get_or_build_vectorstore(self):
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            cache_folder="./embeddings_cache"
        )

        fingerprint = self._knowledge_base_fingerprint()
        fingerprint_file = os.path.join(self.persist_dir, ".kb_fingerprint")

        if os.path.exists(self.persist_dir) and os.path.exists(fingerprint_file):
            try:
                with open(fingerprint_file, "r") as f:
                    saved_fingerprint = f.read().strip()
                if saved_fingerprint == fingerprint:
                    vectorstore = Chroma(
                        persist_directory=self.persist_dir,
                        embedding_function=embeddings
                    )
                    if vectorstore._collection.count() > 0:
                        print("✅ Загружено существующее векторное хранилище (база знаний не менялась)")
                        return vectorstore
            except Exception as e:
                print(f"⚠️ Не удалось переиспользовать хранилище: {e}")

        # База знаний изменилась или хранилища ещё нет — пересобираем с нуля,
        # предварительно очищая старую папку, чтобы не дублировать чанки.
        print("✂️ Разбивка документов на куски...")
        self.chunks = self._split_documents()

        import shutil
        shutil.rmtree(self.persist_dir, ignore_errors=True)
        os.makedirs(self.persist_dir, exist_ok=True)

        print(f"🧠 Пересчёт эмбеддингов для {len(self.chunks)} кусков...")
        vectorstore = Chroma.from_documents(
            documents=self.chunks,
            embedding=embeddings,
            persist_directory=self.persist_dir
        )

        with open(fingerprint_file, "w") as f:
            f.write(fingerprint)

        return vectorstore

    # ------------------------------------------------------------------
    # RAG-цепочка
    # ------------------------------------------------------------------

    def _create_qa_chain(self):
        """Создание RAG-цепочки"""
        prompt_template = """
        Ты — ИИ-помощник для сотрудников железнодорожной компании.
        Отвечай на вопросы пользователя кратко и точно, используя
        ТОЛЬКО информацию из документации ниже. Указывай конкретные
        названия кнопок, вкладок и полей так, как они написаны в
        документации.

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

        # MMR вместо чистого similarity search: меньше повторяющихся
        # по смыслу кусков в контексте => модели физически меньше текста
        # читать и меньше шансов зацепиться не за тот раздел.
        retriever = self.vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={"k": 4, "fetch_k": 10, "lambda_mult": 0.5}
        )

        qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=retriever,
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

        docs = self.vectorstore.similarity_search(question, k=4)
        if not docs:
            return "❌ Не найдено информации по вашему вопросу."

        context = "\n\n".join([doc.page_content for doc in docs])
        prompt = f"""
        Ты — ИИ-помощник для сотрудников железнодорожной компании.
        Отвечай на вопрос кратко и точно, используя только информацию из документации.

        Информация из документации:
        {context}

        Вопрос: {question}

        Ответ:
        """

        try:
            return self.llm.invoke(prompt)
        except Exception as e:
            return f"⚠️ Ошибка: {str(e)}"


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