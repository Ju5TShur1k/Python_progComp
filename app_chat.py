"""
Веб-интерфейс для ИИ-помощника (Streamlit)
"""

import streamlit as st
from rag_assistant import RAGAssistant

# Инициализация помощника (один раз при запуске)
@st.cache_resource
def get_assistant():
    try:
        return RAGAssistant()
    except Exception as e:
        st.error(f"❌ Ошибка инициализации помощника: {e}")
        return None

def main():
    st.set_page_config(
        page_title="🚆 ИИ-помощник ЖД",
        page_icon="🚆",
        layout="wide"
    )
    
    # Заголовок
    st.title("🚆 ИИ-помощник железнодорожного перевозчика")
    st.markdown("Задайте вопрос по работе с приложением")
    
    # Проверка готовности помощника
    assistant = get_assistant()
    
    if assistant is None or (not assistant.qa_chain and not assistant.vectorstore):
        st.warning("""
        ⚠️ Помощник не готов к работе. Проверьте:
        1. Установлен ли Ollama: `ollama --version`
        2. Загружена ли модель: `ollama pull gemma3`
        3. Есть ли файлы в папке `knowledge_base/`
        """)
        return
    
    # Инициализация истории чата
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Здравствуйте! Я ИИ-помощник. Спрашивайте, как выполнить любую операцию в приложении."}
        ]
    
    # Отображение истории чата
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Поле ввода
    if prompt := st.chat_input("Введите ваш вопрос..."):
        # Добавляем вопрос пользователя
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        
        # Получаем ответ от помощника
        with st.chat_message("assistant"):
            with st.spinner("🤔 Думаю..."):
                try:
                    response = assistant.ask(prompt)
                    st.write(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                except Exception as e:
                    error_msg = f"❌ Ошибка: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})

if __name__ == "__main__":
    main()