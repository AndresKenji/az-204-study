#!/usr/bin/env python3
"""
Setup script para configurar el entorno de pruebas del proyecto FastAPI Todo App.
Este script instala las dependencias necesarias y ejecuta las pruebas básicas.
"""

import subprocess
import sys
import os


def run_command(command, description):
    """Ejecuta un comando y maneja errores."""
    print(f"\n🚀 {description}")
    print(f"Comando: {command}")
    print("-" * 50)
    
    try:
        result = subprocess.run(command, shell=True, check=True)
        print(f"✅ {description} completado exitosamente")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} falló con código {e.returncode}")
        return False


def main():
    print("🔧 Configurando entorno de pruebas para FastAPI Todo App")
    print("=" * 60)
    
    # Cambiar al directorio de la aplicación
    app_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(app_dir)
    print(f"📁 Directorio de trabajo: {app_dir}")
    
    # Lista de dependencias esenciales para pruebas
    essential_deps = [
        "pytest",
        "pytest-asyncio", 
        "httpx",
        "python-dotenv",
        "sqlalchemy",
        "fastapi",
        "passlib[bcrypt]",
        "PyJWT",
        "python-multipart",
        "pydantic"
    ]
    
    # Instalar dependencias esenciales
    deps_str = " ".join(essential_deps)
    if not run_command(f"pip install {deps_str}", "Instalando dependencias esenciales"):
        print("\n❌ Error instalando dependencias. Verifica tu conexión a internet y permisos.")
        return False
    
    # Establecer PYTHONPATH
    os.environ["PYTHONPATH"] = app_dir
    
    # Ejecutar pruebas básicas
    test_commands = [
        ("python -m pytest tests/test_api_auth.py::TestAuthAPI::test_login_valid_credentials -v", 
         "Probando autenticación básica"),
        ("python -m pytest tests/test_database.py::TestDatabaseConnection::test_database_connection -v", 
         "Probando conexión a base de datos"),
    ]
    
    all_passed = True
    for command, description in test_commands:
        if not run_command(command, description):
            all_passed = False
    
    if all_passed:
        print("\n🎉 ¡Configuración completada exitosamente!")
        print("\n📋 Próximos pasos:")
        print("   1. Ejecuta 'python -m pytest tests/' para todas las pruebas")
        print("   2. Ejecuta 'python -m pytest --cov=src' para pruebas con cobertura")
        print("   3. Lee TESTING_README.md para más información")
    else:
        print("\n⚠️  Algunas pruebas fallaron, pero el entorno básico está configurado.")
        print("   Revisa los errores arriba y consulta TESTING_README.md")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
