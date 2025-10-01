class Persona:
    def __init__(self, nombre, edad):
        self.nombre = nombre
        self.edad = edad

    def hablar(self):
        print(f"Hola, soy {self.nombre} y tengo {self.edad} años")

persona = Persona("Juan", 30)
persona.hablar()


