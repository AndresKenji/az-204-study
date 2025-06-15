# az-204-study
Guia de estudio para la certificación de azure az-204
>Se agrega código para desplegar los recursos vistos con terraform

# Deploy Infra with terraform
1. Login to azure using azcli
```bash
az login --use-device-code
```
2. Move to the environment directory and create your own terrafor.tfvars file
3. init, plan and apply

```bash
terraform init
terraform plan -out plan.out
terraform apply "plan.out"
```

# Azure App Service

1. Conceptos fundamentales de App Service
- PaaS para aplicaciones web y APIs
    - Eliminación de la gestión de infraestructuras (patching, SO, balanceo de carga).
    - Soporte para Web Apps, API Apps, Mobile Apps y App Service Environments (ASE).
- Planes de App Service (App Service Plans)
  - Determinan recursos (CPU, memoria) y niveles de escalado (Free, Shared, Basic, Standard, Premium, Isolated).
  - Un mismo plan puede hospedar múltiples apps.
  - El nivel “Isolated” (ASE) te da redes virtuales dedicadas.

2. Despliegue y CI/CD
- Opciones de despliegue
  - GitHub, Azure DevOps, Bitbucket, FTP/S, Local Git.
  - Contenedores Docker (imagen única o multi-contenedor con Compose/Swarm).
- Slots de despliegue
  - Múltiples entornos (staging, testing…) en la misma App.
  - “Swap” seguro entre slots con warm-up y preserve host-headers.
- Integración con pipelines
  - En AZ-204: saber configurar tareas de build/deploy desde Azure Pipelines o GitHub Actions que actualicen automáticamente tu App Service.

3. Escalado y alta disponibilidad
- Escalado vertical
  - Cambiar de plan (por ejemplo, de Standard a Premium) para más CPU/memoria.
- Escalado horizontal (scale-out)
  - Manual o automático basado en métricas (CPU, memoria, respuestas lentas, colas).
  - Reglas de autoscale definidas en el nivel de App Service Plan.
- High Availability
  - Multi-region deployment usando Traffic Manager o Front Door para repartir tráfico.

4. Seguridad y autenticación
- Identidad gestionada (Managed Identities)
  - Permite que tu código acceda a recursos de Azure (Key Vault, Storage, etc.) sin credenciales hard-codeadas.
- Autenticación / Autorización fácil (Easy Auth)
  - Conectar con Azure AD, Facebook, Google, Twitter, Microsoft ID sin escribir código de login.
- TLS/SSL
  - Certificados gratuitos por Let’s Encrypt (App Service Managed Certificates).
  - Configuración de TLS versions y cipher suites.
- Redes
  - Integración VNet (Regional VNet Integration o Service Endpoints) para restringir acceso a bases de datos o servicios internos.

5. Almacenamiento y configuración
- App Settings & Connection Strings
  - Variables de entorno gestionadas desde el portal o ARM/Terraform.
  - Pueden referenciar Key Vault usando referencias de secretos.
- Contenido persistente
  - El sistema de archivos local es efímero: para guardar datos usa Azure Files o Blob Storage montados como discos o mediante SDK.

6. Monitorización y diagnóstico
- Azure Monitor & Application Insights
  - Telemetría de solicitudes, excepciones, dependencias.
  - Live Metrics Stream y Snapshot Debugger.
- Log Streaming & Diagnóstico
  - Logs de servidor, despliegue, container logs.
  - Habilitar quedos de FallBack y reinicios automáticos.
- Health Checks
  - Definir un endpoint /health para que App Service compruebe la salud de la aplicación y cycled instances no saludables.

7. Infraestructura como código
- ARM Templates / Bicep / Terraform
  - Definir App Service Plans, Web Apps, Deployment Slots, Configuración de CI/CD y Managed Identity.
  - En AZ-204 es probable que te pidan escribir fragmentos de ARM/Bicep o Terraform para desplegar un Web App con sus settings.

## App Service Plan
Un App Service Plan es la capa de cómputo donde se ejecutan tus App Services (Web Apps, API Apps, Mobile Apps o Functions en modo “consumption” si se habilita), y determina:

1. Capacidad de recursos
- CPU, memoria RAM, espacio en disco y número de instancias.
- Se define por un tier (Free, Shared, Basic, Standard, Premium, Premium v2/v3, Isolated).

2. Opciones de escalado
- Escalado vertical: cambiar de tier para más o menos recursos (por ejemplo, de S1 a P1v2).
- Escalado horizontal: aumentar o reducir el número de instancias que corren tu App Service.

3. Costo
- Cada plan lleva un precio fijo según tier y número de instancias, independientemente de cuántas apps hospedes en él.

### ¿Cómo funciona en la práctica?
1. Creas un App Service Plan en una región concreta.
2. Asignas uno o varios App Services a ese plan: todas las apps comparten los mismos recursos.
3. Configuras escalado:
    - Manual: seleccionas “instancias = 3” y el sistema crea 3 réplicas de tu aplicación.
    - Automático: defines reglas basadas en métricas (p. ej., CPU > 70% → +1 instancia; CPU < 30% → –1 instancia).
4. Facturación: pagas por el plan, no por cada app. Si tienes 3 apps en el mismo plan Standard S1 con 2 instancias, pagas dos S1, independientemente de que sean 3 apps o 1.

### 👀 Ejemplo de tiers y características
|Tier |	Instancias mín./máx.|	Auto-scale|	SLA (%)|	Características destacadas|
|-----|---------------------|-------------|--------|------------------------------|
|Free |	1	                |No	          |–	|Ideal pruebas muy básicas (0 GB SSL)|
|Shared |	1	            |No	          |–	|Compartido con otros clientes|
|Basic (B1)|	1–3	        |No	          |99.95	|Para desarrollo o cargas ligeras|
|Standard |	1–10	        |Sí	          |99.95	|Slots de deployment, Auto-scale|
|Premium |	1–20 (P1v3+)	|Sí	          |99.95	|Más CPU/RAM, SSD, conexiones VNet|
|Isolated |	1–100	        |Sí	          |99.95*	|Corriendo en tu VNet dedicada (ASE)|

* El SLA aplica al entorno de App Service Environment.

### ¿Por qué separar Plan y App?
- Economía de escala: varias aplicaciones pueden compartir el mismo conjunto de instancias.
- Flexibilidad: escalas todo el grupo de apps al mismo tiempo con una sola regla.
- Gestión simplificada: centralizas configuración de red, backups y slots en un solo plan.

### Comandos útiles en cli
```bash
# 1. Crear un plan Standard S1 en EastUS
az appservice plan create \
  --name miPlanS1 \
  --resource-group rg-az204 \
  --sku S1 \
  --is-linux false \
  --location eastus

# 2. Escalar a 3 instancias
az appservice plan update \
  --name miPlanS1 \
  --resource-group rg-az204 \
  --number-of-workers 3

# 3. Habilitar auto-scale (ejemplo: CPU > 70% → +1 worker)
az monitor autoscale create \
  --resource-group rg-az204 \
  --resource miPlanS1 \
  --resource-type Microsoft.Web/serverfarms \
  --name autoscalePlan

az monitor autoscale rule create \
  --resource-group rg-az204 \
  --autoscale-name autoscalePlan \
  --condition "Percentage CPU > 70 avg 5m" \
  --scale out 1

az monitor autoscale rule create \
  --resource-group rg-az204 \
  --autoscale-name autoscalePlan \
  --condition "Percentage CPU < 30 avg 5m" \
  --scale in 1
```
# Azure Container Registry (ACR)
Azure Container Registry (ACR) es un servicio PaaS de Azure que te permite almacenar, gestionar y asegurar tus imágenes Docker (y OCI) en un repositorio privado cercano a tu infraestructura.

- Nativo en Azure: baja latencia con ACI, AKS y otros servicios.
- Totalmente gestionado: no administras infraestructura de registro.
- Integración con Azure AD y RBAC para controlar quién puede leer, escribir o administrar.

## SKUs y características principales
|SKU    |Replicación geo-local  |Tasks (CI/CD)  |Escaneo de vulnerabilidades    |Redes privadas (VNet)  |Precio aproximado|
|-------|-----------------------|---------------|-------------------------------|-----------------------|-----------------|
|Basic  |No                     |No             |No                             |	No                  |Gratis / muy bajo|
|Standard|	Sí (preview)|	Sí (limitado)|	Sí (preview)|	Sí|	Intermedio|
|Premium|	Sí (GA)|	Sí|	Sí|	Sí|	Más alto|

- Basic: lectura/escritura básicas, ideal pruebas.
- Standard: geo-replicación en regiones elegidas, ACR Tasks limitados.
- Premium: geo-replicación automática global, Tasks avanzados, vysoká throughput.

## Autenticación y autorización
1. Azure AD + RBAC
   - Asigna roles AcrPull, AcrPush, AcrDelete, AcrImageSigner, o Owner a usuarios/grupos/managed identities.
2. Credenciales de administrador
   - Usuario/clave HTTP BASIC (menos recomendable).
3. Tokens de acceso
   - Genera tokens scoped-only para pull/push.
> Mejor práctica: usa Managed Identities de tus VMs, ACI o AKS con permisos AcrPull/AcrPush.

## Tipos de repositorios y almacenamiento
- Imágenes Docker/OCI
- Helm Charts (en Premium SKU)
- OCI Artifacts (artefactos genéricos, CNAB, etc.)

Cada repositorio es un **name space**:
`<registry>.azurecr.io/<repository>:<tag>`

## Geo-replicación

Solo en SKU Premium:
  - Replica automáticamente tu registro en múltiples regiones.
  - Lectura regional: pull de la réplica más cercana.
  - Alta disponibilidad: si una región falla, tus imágenes siguen disponibles.

Configuración típica:

```bash
az acr replication create \
  --registry MyRegistry --location eastus2
az acr replication create \
  --registry MyRegistry --location westeurope
```

## ACR Tasks (CI/CD integrado)
Permiten compilar, probar y publicar imágenes directamente en el registro sin infraestructura adicional.
- Quick Tasks: ejecuta un build on-demand.
- Source-triggered Tasks: observa un GitHub repo o un webhook de ACR, rebuild automático.
- Run-Task: empaqueta un conjunto de pasos definidos en YAML.

Ejemplo YAML de Task que build y push:
```yaml
version: v1.1.0
steps:
  - build: --image myimage:{{.Run.ID}} .
    cache: true
triggers:
  - name: GitTrigger
    sourceTrigger:
      sourceRepository:
        provider: GitHub
        repository: myOrg/myRepo
      events:
        - push
```
Despliegue:
```bash
az acr task create \
  --registry MyRegistry \
  --name myBuildTask \
  --file task.yaml \
  --context https://github.com/myOrg/myRepo.git \
  --branch main
```
## Seguridad y escaneo de vulnerabilidades
- Integración con Microsoft Defender for Container Registries
    - Escaneo de imágenes al push y alertas de CVEs.
- Content Trust (Notary)
  - Firmado de imágenes para garantizar integridad.
- Cifrado en reposo con claves gestionadas por Microsoft o propias (CMK).

## Networking
- Privileged Endpoint: URL pública por defecto.
- Private Endpoint: monta ACR en tu VNet para acceso privado mediante Azure Private Link.
- Firewall & Redes: restringe acceso por IP, servicio de redes virtuales.

Ejemplo de Private Endpoint:
```bash
az network private-endpoint create \
  --name acrPrivateEP \
  --resource-group rg-az204 \
  --vnet-name myVnet \
  --subnet mySubnet \
  --private-connection-resource-id $(az acr show --name MyRegistry --query id -o tsv) \
  --group-ids registry
```
## Integración con servicios de Azure
- AKS:
  - `az aks update --name MyCluster --attach-acr MyRegistry`
- ACI:
  - `az container create --registry-login-server ... --registry-username ... --registry-password ...`
- Azure DevOps / GitHub Actions:
  - Tarea Docker@2 con login-server: MyRegistry.azurecr.io
  - Acción azure/docker-login@v1 y docker/build-push-action@v2

## Ejemplos de comandos CLI frecuentes
```bash
# 1. Crear un registro Premium
az acr create \
  --resource-group rg-az204 \
  --name myRegistry \
  --sku Premium \
  --admin-enabled false

# 2. Listar repositorios
az acr repository list \
  --name myRegistry \
  --output table

# 3. Eliminar una imagen
az acr repository delete \
  --name myRegistry \
  --repository myRepo \
  --tag v1.0.0

# 4. Mostrar credenciales AAD (Managed Identity)
az acr credential show \
  --name myRegistry

# 5. Habilitar escaneo de vulnerabilidades
az acr update \
  --name myRegistry \
  --resource-group rg-az204 \
  --data-protection-enabled true
```

## Infraestructura como código
Terraform (extracto)
``` hcl
resource "azurerm_container_registry" "acr" {
  name                = "az204acr"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  sku                 = "Premium"
  admin_enabled       = false

  georeplications {
    location = "westeurope"
  }
  georeplications {
    location = "eastus2"
  }
}
```
Bicep (extracto)
```bicep
resource acr 'Microsoft.ContainerRegistry/registries@2022-02-01' = {
  name: 'az204acr'
  sku: {
    name: 'Premium'
  }
  properties: {
    adminUserEnabled: false
  }
  replicationLocations: [
    'westeurope'
    'eastus2'
  ]
}
```
## 📚 Puntos de práctica para AZ-204
1. Crear un ACR en SKU Premium con geo-replicación.
2. Configurar Private Endpoint y probar pull desde una VM en VNet.
3. Definir un ACR Task con GitHub trigger que build y pujee.
4. Integrar AKS con ACR usando Managed Identity.
5. Habilitar escaneo de vulnerabilidades y revisar alertas.


# Azure Storage Accounts
## 1. ¿Qué es un Storage Account?
Es el contenedor de nivel más alto para todos los servicios de almacenamiento en Azure. Un Storage Account te agrupa bajo un único namespace distintos servicios (Blobs, Files, Queues, Tables, Disks, Data Lake Gen2), gestión de autenticación, red, replicación y facturación.

## 2. Kind y Performance Tier

|Kind	|Para	|Performance Tier|
|-------|-------|----------------|
|StorageV2 (general-purpose v2)| Todos los servicios + características más recientes (Recomendado)	|Standard (HDD-backed) </br> Premium (SSD-backed para File/Blob/Queue/Table)|
|StorageV1 (GPv1)	|Legacy; menos opciones de tier y acceso	|Standard only|
|BlobStorage	|Solo blobs, acceso a tiers de acceso	|Standard only|

## 3. Replicación de datos
Define cuántas copias y dónde:

|SKU	|Descripción|
|-------|-----------|
|LRS (Locally Redundant)	|3 copias en un único datacenter|
|ZRS (Zone-Redundant)	|3 copias en zonas de disponibilidad distintas|
|GRS (Geo-Redundant)	|LRS + replicación asíncrona a otra región|
|RA-GRS (Read-Access GRS)	|Igual que GRS, pero lectura en región secundaria|
|GZRS / RA-GZRS	|ZRS + geo, con lectura en secundario opcional|

## 4. Servicios dentro del Storage Account
1. Blob Storage
   - Block blobs (archivos de hasta 190 GB), Append blobs (logs) y Page blobs (discos VHD).
   - Access tiers: Hot, Cool, Archive. Define coste de almacenamiento vs coste de lectura.
2. File Shares
    - SMB 3.0/2.1, ideal para lift-and-shift de aplicaciones Windows/Linux.
    - Premium usa SSD y baja latencia.
3. Queue Storage
    - Mensajería simple FIFO, ocultamiento y reintentos configurables.
4. Table Storage
    - NoSQL clave-atributo, particionado con PartitionKey/RowKey.
5. Azure Data Lake Storage Gen2
    - Extensión de StorageV2 con hierarchical namespace (sistema de archivos), acceso POSIX-like, ideal para big data y Spark.
6. Disk Storage
    - Aunque gestionados fuera del Storage Account GPv2, comparte conceptos de replicación y cifrado.

## 5. Seguridad y autenticación
- Shared Key: AccountName + AccountKey (read/write).
- SAS Tokens: delegan permisos por tiempo, IP, protocolos.
- Azure AD: roles como Storage Blob Data Contributor, Storage Queue Data Reader, etc., usan OAuth2 sin compartir keys.
- Private Endpoints y Firewalls: restringe conexiones al VNet o rangos IP.

## 6. Cifrado
- En reposo: por defecto con claves de Microsoft.
- Customer-Managed Keys (CMK): usa Azure Key Vault para controlar tu propia clave.
- TLS 1.2+ obligatorio en tránsito; puedes deshabilitar versiones antiguas.

# 7. Monitorización y métricas
- Azure Monitor: métricas de capacidad, transacciones (total, success/failure), latencia.
- Diagnostic Logs:
  - Storage Analytics (legacy) o Azure Monitor Logs para:
    - RequestLogging (blob, table, queue, file)
    - Metrics (capacity, availability, transactions)
    - Metrics por Tier (hot/cool/archive)

## 8. Ejemplos prácticos de CLI
```bash
# 1. Crear un StorageV2 en Standard Tier, LRS
az storage account create \
  --name mystorageaz204 \
  --resource-group rg-az204 \
  --location eastus \
  --sku Standard_LRS \
  --kind StorageV2

# 2. Habilitar hierarchical namespace (ADLS Gen2)
az storage account update \
  --name mystorageaz204 \
  --resource-group rg-az204 \
  --enable-hierarchical-namespace true

# 3. Generar un SAS de lectura para un blob
az storage blob generate-sas \
  --account-name mystorageaz204 \
  --container-name mycontainer \
  --name myfile.txt \
  --permissions r \
  --expiry 2025-06-30T23:59:00Z \
  --https-only

# 4. Configurar firewall para permitir solo un rango IP
az storage account update \
  --name mystorageaz204 \
  --resource-group rg-az204 \
  --default-action Deny \
  --bypass AzureServices \
  --ip-rules 203.0.113.0/24
```
## Puntos de práctica AZ-204
1. Crear un StorageV2 con ADLS Gen2 y experimentar con el Filesystem REST API.
2. Definir políticas de retención y soft delete para blobs.
3. Generar SAS tokens con distintos permisos y expiraciones.
4. Implementar firewall y Private Endpoint, verificar acceso desde una VM.
5. Instrumentar métricas y logs, escribir consultas Kusto en Log Analytics.

# Azure Cosmos DB
Una base de datos multi-modelo y distribuida globalmente de Azure con latencias de milisegundos de un solo dígito y SLAs para disponibilidad, rendimiento, consistencia y latencia.

## Modelos de API soportados

- Core (SQL) API: modelo de documentos JSON con SQL-like queries.
- MongoDB API: compatibilidad wire-protocol con MongoDB.
- Cassandra API: modelo wide-column, tablas CQL.
- Gremlin API: grafos de vértices y aristas.
- Table API: reemplazo avanzado de Table Storage con características de Cosmos.

Cada API mantiene su propio endpoint y SDK correspondiente.

## Distribución global

- Regiones: añade o quita regiones a tu cuenta en caliente.
- Lecturas en la región más cercana (latencia mínima).
- Failover automático o manual entre regiones.
- Replicación multi-maestra o single-master según necesidad.

## Modelos de consistencia

Cinco niveles configurables por cuenta, con trade-off entre latencia y consistencia:

1. Strong
2. Bounded staleness
3. Session (por cliente)
4. Consistent prefix
5. Eventual

En AZ-204 conviene saber definirlos y su impacto en lecturas/escrituras.

## Escalabilidad y rendimiento

- Throughput medido en Request Units (RU/s).
- Provisioned throughput: defines manualmente RUs y pagas en función de ellos.
- Autoscale: rango de RUs basado en consumo.
- Serverless: ideal cargas esporádicas, pagas por uso.
- Particionamiento automático: define una partition key para distribuir datos y RUs.

## Índices y consultas
- Indexing automático por defecto (incluye y excluye paths).
- Política de indexación: control granular de qué rutas JSON indexar y cómo (range, spatial).
- Lenguaje SQL para documentos:
```sql
SELECT c.id, c.name
FROM c
WHERE c.country = 'Spain'
ORDER BY c._ts DESC
```
- LINQ (en .NET), drivers equivalentes en otros SDKs.

## Change Feed

- Secuencia ordenada de cambios en los items de un contenedor.
- Útil para procesamiento incremental, ETL, triggers, arquitecturas event-driven.
- Se consume con Azure Functions (Change Feed Trigger) o directamente con SDK.

## Seguridad

- Azure AD Integration: autentica con tokens AAD en lugar de claves maestra.
- Role-based access control (RBAC) para gran granularidad.
- Redes: restringe acceso con firewall, VNet service endpoints y Private Link.
- Cifrado en reposo automático; puede usar CMK en Key Vault.
- Encryption at rest y in transit (TLS 1.2+).

## Monitorización y diagnósticos

- Azure Monitor: métricas de RUs consumidas, latencia, throttling, disponibilidad.
- Diagnostic Logs: operaciones de data plane y control plane en Log Analytics.
- Alertas: configura notificaciones por throttling (> 429), caída de RUs libres, latencia alta.

## Puntos de práctica para AZ-204

1. Crear una cuenta Cosmos DB con API SQL y diferentes niveles de consistencia.
2. Configurar autoscale y serverless, comparar costos y comportamientos.
3. Diseñar una buena partition key para un contenedor de alta cardinalidad.
4. Consumir Change Feed desde una Azure Function y procesar eventos.
5. Implementar autenticación con Managed Identity desde App Service o Functions.






