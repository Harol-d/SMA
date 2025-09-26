# from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from Config.LlmConfig import SettingsLlm
from Models.ModelFactory import factoryLlm

class ModeLlm(SettingsLlm):
    def __init__(self):
        self.factory = factoryLlm()
        self.model = self.factory.getLlm(
            self.LLM_PROVEEDOR,
            self.LLM_MODEL,
            self.API_KEY,
            self.temperature,
            self.max_tokens
        )
        # Memoria de conversación usando la nueva API
        self.chat_history = InMemoryChatMessageHistory()
        self.max_messages = 6  # Limitar a 6 mensajes (3 intercambios)

    def sendPrompt(self, prompt: str, context: str):
        # Obtener historial de conversación
        # messages_history = self.chat_history.messages
        
        # Crear template con historial
        messages = [
            ("system", self.modelRole),
            ("system", "You must respond guided only by the following context: {context}"),
            ("human", "{input}")
        ]
        
        # Agregar historial de conversación (últimos mensajes)
        # recent_messages = messages_history[-self.max_messages:] if len(messages_history) > self.max_messages else messages_history
        # for message in recent_messages:
        #     if isinstance(message, HumanMessage):
        #         messages.append(("human", message.content))
        #     elif isinstance(message, AIMessage):
        #         messages.append(("assistant", message.content))
        
        # # Agregar prompt actual
        # messages.append(("human", "{input}"))
        
        prompt_template = ChatPromptTemplate.from_messages(messages)
        document_chain = create_stuff_documents_chain(self.model, prompt_template)
        
        response = document_chain.invoke({
            "input": prompt,
            "context": context
        })
        
        # Guardar en memoria usando la nueva API
        self.chat_history.add_user_message(prompt)
        self.chat_history.add_ai_message(response)
        
        return response
        