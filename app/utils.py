import random

class EncurtadorBase62:
    def __init__(self):
        #alfabeto lexicografico - alfabeto da base62
        self.Alfabeto = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"

        #base usada em operações importantes, sendo o coraçõa das funções de conversão
        self.Base = len(self.Alfabeto)

    def decimal_para_base62(self, numero: int) -> str:
        """Converte um id (int) para o codigo da base62."""

        # Trata o caso especial do zero
        if numero == 0:
             return self.Alfabeto[0]

        #Estrutura para armazenar os caracteres
        Resultado = []

        while numero > 0:
            resto = numero % self.Base
            numero = numero // self.Base
            #Transformando numero em letra
            Resultado.append(self.Alfabeto[resto])

        # inverte a ordem dos caracteres acumulados
        return "".join(reversed(Resultado))

    def base62_para_decimal(self, texto_base62: str) -> int:
        """Converte o codigo curto (str) de volta para o id (int)."""

        acumulador = 0

        for caractere in texto_base62:
            # Descobrindo a posição do caractere
            posição = self.Alfabeto.index(caractere)

            acumulador = acumulador * self.Base + posição

        return acumulador

    def gerar_codigo_aleatorio(self, tamanho: int) -> str:
        """Gera uma string aleatoria de tamanho fixo usando o alfabeto base62"""

        acumula_string = []

        for i in range(tamanho):
           numero_aleatorio = random.randint(0, self.Base - 1)
           indice_str = self.Alfabeto[numero_aleatorio]
           acumula_string.append(indice_str)

        return "".join(acumula_string)
