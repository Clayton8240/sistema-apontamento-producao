# Conteúdo para o ficheiro verificar_sintaxe.py
import py_compile
import os
import traceback

print("--- Verificando a sintaxe de todos os ficheiros .py do projeto ---")
error_found = False
project_dir = os.path.dirname(os.path.abspath(__file__))

# Percorre todas as pastas e ficheiros a partir do diretório atual
for subdir, dirs, files in os.walk(project_dir):
    # Ignora a pasta __pycache__ para não verificar ficheiros compilados
    if '__pycache__' in subdir:
        continue
        
    for file in files:
        if file.endswith('.py'):
            full_path = os.path.join(subdir, file)
            print(f"Verificando: {os.path.relpath(full_path)}...")
            try:
                # Tenta compilar o ficheiro. Se houver erro de sintaxe, falhará.
                py_compile.compile(full_path, doraise=True)
                print("   -> Sintaxe OK")
            except Exception:
                # Se a compilação falhar, apanhamos o erro e mostramo-lo
                print(f"\n!!!!!!!! ERRO DE SINTAXE ENCONTRADO !!!!!!!!")
                print(f"Ficheiro com erro: {full_path}")
                traceback.print_exc() # Imprime a mensagem de erro detalhada
                print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n")
                error_found = True

if not error_found:
    print("\n--- Verificação Concluída: Nenhum erro de sintaxe foi encontrado. ---")
else:
    print("\n--- Verificação Concluída: Foram encontrados erros. Por favor, corrija o(s) ficheiro(s) acima. ---")

input("\nPressione Enter para fechar...")