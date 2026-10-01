from app.utils import EncurtadorBase62

encurtador = EncurtadorBase62()

# Número de teste (simulando um id que viria do banco)
id_original = 100000

# Converte pra base62
codigo = encurtador.decimal_para_base62(id_original)
print(f"ID original: {id_original}")
print(f"Código gerado: {codigo}")

# Converte de volta pra decimal
id_recuperado = encurtador.base62_para_decimal(codigo)
print(f"ID recuperado: {id_recuperado}")

# Confere se bateu
if id_original == id_recuperado:
    print("✅ Conversão correta!")
else:
    print("❌ Algo está errado na conversão.")