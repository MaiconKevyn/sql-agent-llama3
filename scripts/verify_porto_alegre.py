#!/usr/bin/env python3
"""
Script para verificar dados de Porto Alegre e identificar problemas na query.
"""

import sqlite3
import sys
import os


def verify_porto_alegre_data():
    """Verifica dados específicos de Porto Alegre."""

    print("🔍 VERIFICAÇÃO: PORTO ALEGRE")
    print("=" * 50)

    db_path = "database/sus_data.db"
    if not os.path.exists(db_path):
        print("❌ Database não encontrada!")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 1. Verificar cidades disponíveis
        print("\n1️⃣ CIDADES DISPONÍVEIS:")
        cursor.execute("""
                       SELECT CIDADE_RESIDENCIA_PACIENTE, COUNT(*) as total
                       FROM dados_sus3
                       WHERE CIDADE_RESIDENCIA_PACIENTE IS NOT NULL
                       GROUP BY CIDADE_RESIDENCIA_PACIENTE
                       ORDER BY total DESC LIMIT 10;
                       """)

        cities = cursor.fetchall()
        print("🏙️  Top 10 cidades:")
        for city, count in cities:
            print(f"   {city}: {count:,}")

        # 2. Verificar se Porto Alegre existe
        print(f"\n2️⃣ VERIFICANDO PORTO ALEGRE:")
        cursor.execute("""
                       SELECT COUNT(*)
                       FROM dados_sus3
                       WHERE CIDADE_RESIDENCIA_PACIENTE = 'Porto Alegre';
                       """)

        poa_total = cursor.fetchone()[0]
        print(f"📊 Total de registros Porto Alegre: {poa_total:,}")

        if poa_total == 0:
            # Verificar variações do nome
            print("⚠️  'Porto Alegre' não encontrado. Verificando variações:")

            cursor.execute("""
                           SELECT DISTINCT CIDADE_RESIDENCIA_PACIENTE
                           FROM dados_sus3
                           WHERE CIDADE_RESIDENCIA_PACIENTE LIKE '%Porto%'
                              OR CIDADE_RESIDENCIA_PACIENTE LIKE '%Alegre%';
                           """)

            variations = cursor.fetchall()
            if variations:
                print("🔍 Possíveis variações encontradas:")
                for var in variations:
                    print(f"   • '{var[0]}'")
            else:
                print("❌ Nenhuma variação encontrada")

        # 3. Query original do agente (incorreta)
        print(f"\n3️⃣ QUERY ORIGINAL DO AGENTE (INCORRETA):")
        query_incorreta = "SELECT COUNT(*) FROM dados_sus3 WHERE MUNIC_RES = 430100 AND MORTE > 0"
        print(f"🔴 {query_incorreta}")

        cursor.execute(query_incorreta)
        resultado_incorreto = cursor.fetchone()[0]
        print(f"   Resultado: {resultado_incorreto}")

        # 4. Verificar código 430100
        print(f"\n4️⃣ VERIFICANDO CÓDIGO IBGE 430100:")
        cursor.execute("""
                       SELECT CIDADE_RESIDENCIA_PACIENTE, COUNT(*)
                       FROM dados_sus3
                       WHERE MUNIC_RES = 430100
                       GROUP BY CIDADE_RESIDENCIA_PACIENTE;
                       """)

        codigo_cities = cursor.fetchall()
        if codigo_cities:
            print("🏙️  Cidades com código 430100:")
            for city, count in codigo_cities:
                print(f"   {city}: {count:,}")
        else:
            print("❌ Nenhuma cidade com código 430100")

        # 5. Query correta se Porto Alegre existir
        if poa_total > 0:
            print(f"\n5️⃣ QUERY CORRETA:")
            query_correta = "SELECT COUNT(*) FROM dados_sus3 WHERE CIDADE_RESIDENCIA_PACIENTE = 'Porto Alegre' AND MORTE = 1"
            print(f"🟢 {query_correta}")

            cursor.execute(query_correta)
            resultado_correto = cursor.fetchone()[0]
            print(f"   Resultado: {resultado_correto}")

            # Comparar resultados
            print(f"\n📊 COMPARAÇÃO:")
            print(f"   Query incorreta: {resultado_incorreto}")
            print(f"   Query correta: {resultado_correto}")
            print(f"   Diferença: {abs(resultado_correto - resultado_incorreto)}")

        # 6. Análise detalhada se Porto Alegre não existir
        if poa_total == 0:
            print(f"\n6️⃣ ANÁLISE: PORTO ALEGRE NÃO EXISTE NOS DADOS")
            print("💡 Possíveis explicações:")
            print("   1. Dados são apenas do RS interior")
            print("   2. Porto Alegre pode ter grafia diferente")
            print("   3. Dados podem ser filtrados por região")

            # Verificar códigos IBGE de POA
            poa_codes = [431490, 430100]  # Códigos possíveis para POA

            print(f"\n🔍 Verificando códigos IBGE de Porto Alegre:")
            for code in poa_codes:
                cursor.execute(f"""
                    SELECT CIDADE_RESIDENCIA_PACIENTE, COUNT(*) 
                    FROM dados_sus3 
                    WHERE MUNIC_RES = {code} 
                    GROUP BY CIDADE_RESIDENCIA_PACIENTE;
                """)

                result = cursor.fetchall()
                if result:
                    print(f"   Código {code}:")
                    for city, count in result:
                        print(f"      {city}: {count:,}")
                else:
                    print(f"   Código {code}: não encontrado")

        # 7. Verificar mortes por MORTE = 1 vs MORTE > 0
        print(f"\n7️⃣ DIFERENÇA ENTRE MORTE = 1 E MORTE > 0:")

        cursor.execute("SELECT COUNT(*) FROM dados_sus3 WHERE MORTE = 1;")
        morte_1 = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM dados_sus3 WHERE MORTE > 0;")
        morte_maior_0 = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM dados_sus3 WHERE MORTE = 0;")
        morte_0 = cursor.fetchone()[0]

        cursor.execute("SELECT DISTINCT MORTE FROM dados_sus3 ORDER BY MORTE;")
        valores_morte = [row[0] for row in cursor.fetchall()]

        print(f"📊 Valores MORTE encontrados: {valores_morte}")
        print(f"   MORTE = 0: {morte_0:,}")
        print(f"   MORTE = 1: {morte_1:,}")
        print(f"   MORTE > 0: {morte_maior_0:,}")

        if morte_1 != morte_maior_0:
            print(f"⚠️  ATENÇÃO: MORTE = 1 ({morte_1}) ≠ MORTE > 0 ({morte_maior_0})")
            print(f"💡 Use sempre MORTE = 1 para contar mortes!")
        else:
            print(f"✅ MORTE = 1 e MORTE > 0 são equivalentes neste dataset")

    except Exception as e:
        print(f"❌ Erro: {e}")
    finally:
        conn.close()


def suggest_fixes():
    """Sugere correções para o agente."""

    print(f"\n\n🛠️  CORREÇÕES NECESSÁRIAS NO AGENTE:")
    print("=" * 60)

    print(f"1️⃣ PROBLEMA - Campo errado para cidade:")
    print(f"   ❌ Incorreto: MUNIC_RES = código")
    print(f"   ✅ Correto: CIDADE_RESIDENCIA_PACIENTE = 'nome'")

    print(f"\n2️⃣ PROBLEMA - Critério de morte incorreto:")
    print(f"   ❌ Incorreto: MORTE > 0")
    print(f"   ✅ Correto: MORTE = 1")

    print(f"\n3️⃣ QUERY CORRETA PARA PORTO ALEGRE:")
    print(f"```sql")
    print(f"SELECT COUNT(*) FROM dados_sus3 ")
    print(f"WHERE CIDADE_RESIDENCIA_PACIENTE = 'Porto Alegre' ")
    print(f"  AND MORTE = 1;")
    print(f"```")

    print(f"\n4️⃣ MELHORIAS PARA O PROMPT DO AGENTE:")
    print(f"   • Especificar que cidades usam CIDADE_RESIDENCIA_PACIENTE")
    print(f"   • Reforçar que mortes sempre usam MORTE = 1")
    print(f"   • Incluir exemplos de queries geograficas")

    print(f"\n5️⃣ FALLBACK ESPECÍFICO PARA CIDADES:")
    print(f"   Criar fallback que detecta perguntas sobre cidades")
    print(f"   e usa automaticamente CIDADE_RESIDENCIA_PACIENTE")


def main():
    """Função principal."""

    verify_porto_alegre_data()
    suggest_fixes()


if __name__ == "__main__":
    main()