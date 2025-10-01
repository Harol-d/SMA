from Models.LlmModel import ModeLlm
from Controllers.dataBaseVectorController import dataBaseVectorController

class lmmController:
    def __init__(self):
        self.model = ModeLlm()
        self.vector = dataBaseVectorController()
        
    def promptValidate(self, data: dict):
        try:
            prompt = data.get("prompt")
            
            if prompt is None:
                raise ValueError("Error: No se ha proporcionado un prompt.")
            
            if not isinstance(prompt, str):
                raise TypeError("Error: El prompt debe ser un String.")
            
            if prompt.strip() == "":
                raise ValueError("Error: El prompt no puede estar vacío.")
            
            prompt = prompt.strip()
            
        except (ValueError, TypeError) as e:
            return str(e)
        context = self.vector.buscarSimilitud(prompt)
        response = self.model.sendPrompt(prompt, context)
        return response
            
