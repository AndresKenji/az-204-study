# Middleware de Usuario - Documentación

## Descripción

El middleware `UserMiddleware` se ejecuta en cada petición HTTP y automáticamente obtiene la información del usuario autenticado desde las cookies, almacenándola en `request.state.user`.

## Implementación

### 1. Middleware (`src/auth/middlewares.py`)

El middleware realiza las siguientes tareas:
- Obtiene el usuario de la cookie de autenticación
- Asigna el usuario a `request.state.user` (o `None` si no está autenticado)
- Maneja errores de autenticación de forma silenciosa

### 2. Registro del Middleware (`main.py`)

```python
from src.auth.middlewares import UserMiddleware

app = FastAPI()
app.add_middleware(UserMiddleware)
```

## Uso en las Rutas

### Funciones Auxiliares Disponibles

#### `get_current_user_from_request(request: Request)`
Obtiene el usuario del request.state. Retorna el usuario si está autenticado, `None` en caso contrario.

```python
from src.auth.middlewares import get_current_user_from_request

@router.get("/some-route")
async def some_route(request: Request):
    user = get_current_user_from_request(request)
    if user:
        # Usuario autenticado
        return {"message": f"Hola {user.username}"}
    else:
        # Usuario no autenticado
        return {"message": "Hola invitado"}
```

#### `require_authenticated_user(request: Request)`
Requiere que el usuario esté autenticado. Lanza una excepción si no lo está.

```python
from src.auth.middlewares import require_authenticated_user

@router.get("/protected-route")
async def protected_route(request: Request):
    user = require_authenticated_user(request)  # Lanza excepción si no está autenticado
    return {"message": f"Área protegida, bienvenido {user.username}"}
```

## Ejemplos de Uso

### 1. Ruta que funciona con o sin autenticación

```python
@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    user = get_current_user_from_request(request)

    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={
            "request": request,
            "user": user,
            "is_authenticated": user is not None
        }
    )
```

### 2. Ruta que requiere autenticación

```python
@router.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request):
    user = get_current_user_from_request(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    return templates.TemplateResponse(
        name="profile.html",
        request=request,
        context={"request": request, "user": user}
    )
```

### 3. Ruta protegida (alternativa)

```python
@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    try:
        user = require_authenticated_user(request)
        return templates.TemplateResponse(
            name="dashboard.html",
            request=request,
            context={"request": request, "user": user}
        )
    except LoginRedirectException:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)
```

## Ventajas del Middleware

1. **Automático**: Se ejecuta en todas las peticiones sin necesidad de código adicional
2. **Consistente**: Siempre tendrás acceso a `request.state.user`
3. **Eficiente**: Una sola verificación por petición
4. **Flexible**: Puedes usar el usuario o no, según necesites
5. **Manejo de errores**: Los errores de autenticación no bloquean la aplicación

## Consideraciones

- El middleware asigna `None` a `request.state.user` si hay errores de autenticación
- No bloquea rutas públicas - permite el acceso sin autenticación
- Para rutas que requieren autenticación, debes verificar manualmente si `user` es `None`
- Los errores de autenticación se manejan silenciosamente para no interrumpir el flujo
