# Testing Setup for FastAPI Todo App

Este documento describe la configuración de pruebas para la aplicación FastAPI Todo App. Las pruebas están configuradas para usar una base de datos SQLite independiente para garantizar el aislamiento completo entre las pruebas.

## 📁 Estructura de Pruebas

```
tests/
├── __init__.py                 # Paquete de pruebas
├── test_auth.py               # Pruebas de autenticación y usuarios
├── test_tasks.py              # Pruebas de operaciones de tareas
├── test_api_auth.py           # Pruebas de API de autenticación
├── test_api_tasks.py          # Pruebas de API de tareas
└── test_database.py           # Pruebas de base de datos
```

## 🚀 Configuración Inicial

### 1. Instalar Dependencias de Pruebas

```powershell
# Instalar dependencias básicas
pip install -r requirements.txt

# Instalar dependencias de pruebas
pip install -r requirements-test.txt
```

### 2. Configuración de Base de Datos

Las pruebas utilizan una base de datos SQLite temporal que se crea y destruye para cada prueba, garantizando:
- ✅ Aislamiento completo entre pruebas
- ✅ No interferencia con la base de datos principal
- ✅ Pruebas rápidas y confiables
- ✅ No necesidad de limpieza manual

## 🧪 Ejecutar Pruebas

### Opción 1: Usar pytest directamente

```powershell
# Ejecutar todas las pruebas
pytest

# Ejecutar con información detallada
pytest -v

# Ejecutar pruebas específicas
pytest tests/test_auth.py
pytest tests/test_tasks.py

# Ejecutar con cobertura
pytest --cov=src --cov-report=html --cov-report=term-missing

# Ejecutar pruebas en paralelo
pytest -n auto
```

### Opción 2: Usar el script de ejecución

```powershell
# Ejecutar todas las pruebas
python run_tests.py

# Ejecutar solo pruebas unitarias
python run_tests.py --type unit

# Ejecutar con cobertura
python run_tests.py --coverage

# Ejecutar en paralelo con información detallada
python run_tests.py --parallel --verbose

# Ejecutar archivo específico
python run_tests.py --file test_auth.py
```

## 📊 Tipos de Pruebas

### 1. Pruebas Unitarias (`@pytest.mark.unit`)
- Prueban funciones y clases individuales
- No requieren base de datos completa
- Muy rápidas de ejecutar

### 2. Pruebas de Integración (`@pytest.mark.integration`)
- Prueban la interacción entre componentes
- Usan base de datos temporal completa
- Validan el comportamiento del sistema completo

### 3. Pruebas de API (`@pytest.mark.api`)
- Prueban endpoints HTTP
- Simulan peticiones de clientes reales
- Validan respuestas JSON y códigos de estado

## 🔧 Fixtures Disponibles

### Fixtures de Base de Datos
- `test_db`: Base de datos temporal SQLite
- `db_session`: Sesión de base de datos para pruebas
- `client`: Cliente de pruebas de FastAPI

### Fixtures de Usuarios
- `test_user`: Usuario regular de pruebas
- `test_admin_user`: Usuario administrador de pruebas
- `auth_headers`: Headers de autenticación para usuario regular
- `admin_auth_headers`: Headers de autenticación para admin

### Fixtures de Datos
- `test_task`: Tarea de prueba individual
- `sample_tasks`: Múltiples tareas de prueba

## 🎯 Cobertura de Pruebas

Las pruebas cubren:

### Autenticación y Usuarios
- ✅ Creación de usuarios
- ✅ Autenticación con credenciales válidas/inválidas
- ✅ Tokens JWT
- ✅ Permisos de administrador
- ✅ Usuarios deshabilitados
- ✅ Restricciones de unicidad

### Gestión de Tareas
- ✅ CRUD completo de tareas
- ✅ Permisos de propietario
- ✅ Acceso de administrador
- ✅ Validación de datos
- ✅ Relaciones entre modelos

### API REST
- ✅ Endpoints autenticados y no autenticados
- ✅ Códigos de respuesta HTTP correctos
- ✅ Validación de JSON
- ✅ Manejo de errores
- ✅ Headers de autenticación

### Base de Datos
- ✅ Conexiones y transacciones
- ✅ Integridad referencial
- ✅ Relaciones entre modelos
- ✅ Operaciones en lote
- ✅ Aislamiento entre pruebas

## 🔍 Ejecución de Pruebas Específicas

### Por archivo
```powershell
pytest tests/test_auth.py::TestUserModel::test_user_creation
```

### Por marcador
```powershell
pytest -m "unit"
pytest -m "api"
pytest -m "integration"
```

### Por patrón
```powershell
pytest -k "test_create"
pytest -k "auth"
```

## 📈 Generar Reporte de Cobertura

```powershell
# Generar reporte HTML
pytest --cov=src --cov-report=html

# Ver reporte en navegador
start htmlcov/index.html  # Windows

# Generar reporte XML (para CI/CD)
pytest --cov=src --cov-report=xml
```

## 🐛 Debugging de Pruebas

### Ejecutar una prueba específica con logs
```powershell
pytest tests/test_auth.py::test_login_valid_credentials -v -s
```

### Usar pytest con debugger
```powershell
pytest --pdb tests/test_auth.py
```

### Ver salida completa
```powershell
pytest -s tests/test_auth.py
```

## 🚨 Troubleshooting

### Problema: "ModuleNotFoundError"
```powershell
# Solución: Asegurar que PYTHONPATH incluya el directorio raíz
set PYTHONPATH=%cd%
pytest
```

### Problema: "Database locked"
```powershell
# Solución: Las pruebas usan bases de datos temporales, no debería ocurrir
# Si ocurre, reiniciar el terminal y ejecutar de nuevo
```

### Problema: Pruebas lentas
```powershell
# Solución: Ejecutar en paralelo
pytest -n auto

# O ejecutar solo pruebas rápidas
pytest -m "not slow"
```

## 📝 Escribir Nuevas Pruebas

### Estructura básica de una prueba

```python
import pytest
from src.auth.models import User

class TestNewFeature:
    """Describe what this test class covers."""

    def test_specific_behavior(self, db_session, test_user):
        """Test a specific behavior with descriptive docstring."""
        # Arrange
        expected_value = "expected"

        # Act
        result = some_function(test_user)

        # Assert
        assert result == expected_value

    @pytest.mark.asyncio
    async def test_async_function(self, db_session):
        """Test async functions with @pytest.mark.asyncio."""
        result = await some_async_function()
        assert result is not None
```

### Usar fixtures personalizadas

```python
@pytest.fixture
def custom_data(db_session):
    """Create custom test data."""
    # Setup
    data = create_test_data()
    yield data
    # Teardown (optional)
    cleanup_test_data(data)
```

## 🎖️ Mejores Prácticas

1. **Nombres descriptivos**: Usa nombres que describan exactamente qué prueba la función
2. **Una afirmación por prueba**: Cada prueba debe validar una cosa específica
3. **Arrange-Act-Assert**: Estructura tus pruebas en estas tres fases
4. **Usar fixtures**: Reutiliza datos de prueba con fixtures
5. **Aislar pruebas**: Cada prueba debe ser independiente
6. **Probar casos edge**: Incluye casos límite y de error
7. **Documentar con docstrings**: Explica qué hace cada prueba

## 📚 Recursos Adicionales

- [Documentación de pytest](https://docs.pytest.org/)
- [Testing FastAPI](https://fastapi.tiangolo.com/tutorial/testing/)
- [SQLAlchemy Testing](https://docs.sqlalchemy.org/en/14/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites)
