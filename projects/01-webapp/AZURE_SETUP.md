# Configuración de Azure Entra ID para la aplicación Todo

Este documento explica cómo configurar la autenticación con Microsoft Entra ID (anteriormente Azure Active Directory) para tu aplicación Todo.

## Paso 1: Registrar la aplicación en Azure Portal

1. **Accede al Azure Portal**: Ve a [portal.azure.com](https://portal.azure.com)
2. **Navega a Azure Active Directory**: Busca y selecciona "Azure Active Directory" en el portal
3. **Registros de aplicaciones**: En el menú lateral, selecciona "App registrations" (Registros de aplicaciones)
4. **Nueva aplicación**: Haz clic en "New registration" (Nuevo registro)

### Configuración del registro:
- **Nombre**: `TodoApp-FastAPI` (o el nombre que prefieras)
- **Tipos de cuenta admitidos**: Selecciona "Accounts in this organizational directory only"
- **URI de redireccionamiento**:
  - Tipo: `Web`
  - URI: `http://localhost:8000/auth/callback`

## Paso 2: Configurar la aplicación

Después de crear el registro:

1. **Anota los valores importantes**:
   - `Application (client) ID` - Este será tu `AZURE_CLIENT_ID`
   - `Directory (tenant) ID` - Este será tu `AZURE_TENANT_ID`

2. **Configurar autenticación**:
   - Ve a "Authentication" en el menú lateral
   - Asegúrate de que la URL de redireccionamiento sea: `http://localhost:8000/auth/callback`
   - En "Implicit grant and hybrid flows", marca "ID tokens"

3. **Configurar permisos de API**:
   - Ve a "API permissions"
   - Agrega los permisos necesarios:
     - Microsoft Graph > Delegated permissions > `User.Read`
     - Microsoft Graph > Delegated permissions > `profile`
     - Microsoft Graph > Delegated permissions > `email`

4. **Exponer una API** (opcional, para scopes personalizados):
   - Ve a "Expose an API"
   - Agrega un scope: `api://{client-id}/user_impersonation`

## Paso 3: Actualizar variables de entorno

Actualiza tu archivo `.env` con los valores obtenidos:

```env
# Azure Entra ID configuration
AZURE_CLIENT_ID=tu_client_id_aqui
AZURE_TENANT_ID=tu_tenant_id_aqui
OPENAPI_CLIENT_ID=tu_client_id_aqui
```

## Paso 4: Probar la integración

1. Ejecuta la aplicación: `uvicorn main:app --reload`
2. Ve a `http://localhost:8000`
3. Haz clic en "Login with Microsoft"
4. Serás redirigido a la página de Microsoft para autenticarte
5. Después de la autenticación exitosa, regresarás a tu aplicación

## Notas importantes

- Para producción, cambia la URL de redireccionamiento a tu dominio real
- Considera usar Azure Key Vault para almacenar secretos en producción
- Los usuarios se crearán automáticamente en tu base de datos local al hacer login por primera vez
- Los usuarios de Azure no tendrán permisos de administrador por defecto

## Troubleshooting

### Error: "AADSTS50011: The reply URL specified in the request does not match"
- Verifica que la URL de redireccionamiento en Azure coincida exactamente con la configurada en tu aplicación

### Error: "Invalid client"
- Verifica que el `AZURE_CLIENT_ID` sea correcto
- Asegúrate de que la aplicación esté registrada correctamente

### Error: "Invalid tenant"
- Verifica que el `AZURE_TENANT_ID` sea correcto
- Asegúrate de estar usando el tenant correcto
