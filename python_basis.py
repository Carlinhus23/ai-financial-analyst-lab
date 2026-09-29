# 1. Variables
empresa = "Apple"
ticker = "AAPL"
años = 5

print(empresa)
print(ticker)
print(años)


# 2. Tipos de datos
print(type(empresa))
print(type(años))


# 3. Condiciones
if años == 5:
    print("Tenemos cinco años de información.")
else:
    print("No tenemos cinco años.")


# 4. Lista
balances = ["2021", "2022", "2023", "2024", "2025"]

print(balances)
print(len(balances))


# 5. Bucle
for año in balances:
    print(año)

empresas = ["Apple", "Microsoft", "Amazon", "Tesla"]
for empresa in empresas:
    print("Analizando", empresa)

apple = {
    "nombre": "Apple",
    "ticker": "AAPL",
    "pais": "Estados Unidos",
    "sector": "Tecnología"
}

print(apple["nombre"])
print(apple["ticker"])
print(apple["pais"])
print(apple["sector"])

Apple = {
    "nombre": "Apple",
    "ticker": "AAPL",
}
Microsoft = {
    "nombre": "Microsoft",
    "ticker": "MSFT",
}
binomio = [
    Apple,
    Microsoft
]

for empresa in binomio:
    print("Analizando", empresa["nombre"],"(",empresa["ticker"],")")