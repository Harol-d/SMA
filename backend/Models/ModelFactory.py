class factoryLlm:

    def getLlm(self, LLM_PROVEEDOR, LLM_MODEL, API_KEY, temperature, max_tokens):
        if LLM_PROVEEDOR == "gemini":
            from langchain_google_genai import ChatGoogleGenerativeAI
            modelo = ChatGoogleGenerativeAI(
                model=LLM_MODEL, 
                google_api_key=API_KEY, 
                temperature=temperature,
                max_output_tokens=max_tokens  # Para Gemini
            )
            return modelo

        if LLM_PROVEEDOR == "OpenAI":
            from langchain_openai import ChatOpenAI  # Cambiado de OpenAI a ChatOpenAI
            modelo = ChatOpenAI(
                model=LLM_MODEL, 
                api_key=API_KEY, 
                temperature=temperature,
                max_tokens=max_tokens  # Para OpenAI
            )
            return modelo

    # Agregar DeepSeek posteriormente