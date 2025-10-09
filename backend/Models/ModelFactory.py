class factoryLlm:

    def getLlm(self, LLM_PROVEEDOR, LLM_MODEL, API_KEY, temperature, max_tokens):
        try:
            # Validar parámetros requeridos
            if not LLM_PROVEEDOR:
                raise ValueError("LLM_PROVEEDOR no está configurado")
            
            if not LLM_MODEL:
                raise ValueError("LLM_MODEL no está configurado")
            
            if not API_KEY:
                raise ValueError("API_KEY no está configurado")
            
            if LLM_PROVEEDOR == "gemini":
                from langchain_google_genai import ChatGoogleGenerativeAI
                modelo = ChatGoogleGenerativeAI(
                    model=LLM_MODEL, 
                    google_api_key=API_KEY, 
                    temperature=temperature,
                    max_output_tokens=max_tokens  # Para Gemini
                )
                print(f"Modelo Gemini inicializado: {LLM_MODEL}")
                return modelo

            elif LLM_PROVEEDOR == "OpenAI":
                from langchain_openai import ChatOpenAI
                modelo = ChatOpenAI(
                    model=LLM_MODEL, 
                    api_key=API_KEY, 
                    temperature=temperature,
                    max_tokens=max_tokens  # Para OpenAI
                )
                print(f"Modelo OpenAI inicializado: {LLM_MODEL}")
                return modelo
            
            else:
                raise ValueError(f"Proveedor LLM no soportado: {LLM_PROVEEDOR}")
                
        except Exception as e:
            print(f"Error al inicializar el modelo LLM: {str(e)}")
            return None

    # Agregar DeepSeek posteriormente