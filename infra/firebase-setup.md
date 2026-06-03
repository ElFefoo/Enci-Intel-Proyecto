# Firebase Auth (Identity Platform) — Guia de Configuracion

## 1. Habilitar en Firebase Console

1. Ir a [Firebase Console](https://console.firebase.google.com)
2. Click **"Agregar proyecto"** → seleccionar proyecto GCP existente `enci-intel-prod`
3. Ir a **Authentication > Sign-in method**
4. Habilitar **Email/Password**
5. Ir a **Project Settings > Tus apps** → agregar app Web
6. Copiar el objeto `firebaseConfig` y pegar en `frontend/.env`:

```env
VITE_FIREBASE_API_KEY=AIzaSy...
VITE_FIREBASE_AUTH_DOMAIN=enci-intel-prod.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=enci-intel-prod
```

## 2. Crear primer usuario Admin

Desde Firebase Console > Authentication > Users > Agregar usuario:
- Email: `admin@encipharm.cl`
- Password: (temporal, cambiar en primer login)

Luego asignar el rol Admin via la API (con el backend corriendo):
```bash
# Obtener UID del usuario desde Firebase Console
UID="el-uid-del-usuario"
TOKEN="el-id-token-del-admin"  # login primero desde la app

curl -X PUT https://api.enci-intel.encipharm.cl/api/v1/admin/users/$UID/role \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"role": "Admin"}'
```

> **Nota:** El primer Admin debe asignarse manualmente desde el backend local o con un script de inicializacion.

## 3. Como funcionan los roles (Custom Claims)

El custom claim `role` se agrega al JWT de Firebase:

```
Token decodificado:
{
  "uid": "abc123",
  "email": "usuario@encipharm.cl",
  "role": "Comercial",   ← custom claim asignado por Admin SDK
  "iat": ...,
  "exp": ...
}
```

El backend lee este claim en `middleware/auth.py` y lo convierte en `CurrentUser.role`.

**Importante:** Despues de asignar un rol, el usuario debe hacer logout y login para que el nuevo token incluya el claim.

## 4. En Cloud Run — cero configuracion de credenciales

El backend usa **Application Default Credentials (ADC)**. Cloud Run automaticamente inyecta las credenciales del Service Account asignado. No necesitas archivos JSON ni variables de entorno adicionales.

## 5. En local — configuracion

```bash
# Opcion A: autenticacion con tu cuenta Google (mas simple)
gcloud auth application-default login

# Opcion B: service account key (para CI/CD local)
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/serviceAccountKey.json
```
