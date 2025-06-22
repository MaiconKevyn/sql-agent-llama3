#!/usr/bin/env python3
"""
Teste rápido da correção.
"""


def safe_extract_count(result) -> int:
    """Versão robusta que funciona com string."""
    try:
        if not result:
            return 0

        if isinstance(result, str):
            import re
            numbers = re.findall(r'\d+', result)
            if numbers:
                return int(numbers[0])
            return 0

        if isinstance(result, list) and len(result) > 0:
            first_row = result[0]
            if isinstance(first_row, tuple) and len(first_row) > 0:
                return int(first_row[0])
            if isinstance(first_row, (int, float)):
                return int(first_row)
            if isinstance(first_row, str):
                return safe_extract_count(first_row)

        if isinstance(result, tuple) and len(result) > 0:
            return int(result[0])

        if isinstance(result, (int, float)):
            return int(result)

        return int(result)

    except:
        try:
            import re
            result_str = str(result)
            numbers = re.findall(r'\d+', result_str)
            if numbers:
                return int(numbers[0])
        except:
            pass
        return 0


# Testar com os resultados problemáticos
test_cases = [
    "[(2202,)]",
    "[(8,)]",
    "[(58655,)]",
    [(2202,)],
    2202,
    "",
    None,
    "abc",
    "[",
]

print("🧪 TESTANDO CORREÇÃO ROBUSTA:")
print("=" * 40)

for i, test_case in enumerate(test_cases, 1):
    try:
        result = safe_extract_count(test_case)
        print(f"{i}. Input: {repr(test_case)} → Output: {result}")
    except Exception as e:
        print(f"{i}. Input: {repr(test_case)} → Error: {e}")

print(f"\n✅ Teste concluído!")

# Testar a resposta formatada
test_result = "[(2202,)]"
count = safe_extract_count(test_result)
response = f"Houve {count} mortes registradas nos dados."
print(f"\n🎯 RESULTADO FINAL:")
print(f"   Input: {test_result}")
print(f"   Count: {count}")
print(f"   Response: {response}")