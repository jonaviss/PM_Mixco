from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from schemas import LoginRequest, TokenResponse, RegistroCreate, RecuperarRequest, RestablecerRequest
from services.auth_service import authenticate_user, create_token, registrar_usuario, generar_token_recuperacion, restablecer_contrasena, verificar_correo
from services.notificacion_service import enviar_correo_recuperacion

router = APIRouter()


@router.post("/login-cliente", response_model=TokenResponse, status_code=status.HTTP_200_OK)
def login(payload: LoginRequest):
    try:
        user_data = authenticate_user(payload.cui, payload.contrasena)
        token = create_token(user_data)

        return {
            "access_token": token,
            "token_type": "bearer",
            "nombre_completo": user_data["nombre_completo"],
            "rango": user_data["rango"],
            "modulos": user_data["modulos"],
        }

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al procesar el inicio de sesión.",
        )


@router.post("/registro", status_code=status.HTTP_201_CREATED)
def registro(payload: RegistroCreate):
    try:
        registrar_usuario(payload.cui, payload.nombre_completo, payload.contrasena, payload.correo)
        return {"mensaje": "Cuenta creada exitosamente. Ya puedes iniciar sesión."}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/recuperar")
async def recuperar(payload: RecuperarRequest, background_tasks: BackgroundTasks):
    try:
        token = generar_token_recuperacion(payload.cui)
        if not token:
            return {"mensaje": "Si el CUI está registrado con un correo, recibirás las instrucciones."}
        background_tasks.add_task(enviar_correo_recuperacion, payload.cui, token)
        return {"mensaje": "Si el CUI está registrado con un correo, recibirás las instrucciones."}
    except Exception:
        return {"mensaje": "Si el CUI está registrado con un correo, recibirás las instrucciones."}


@router.post("/verificar-correo")
def verificar(payload: dict):
    token = payload.get("token", "")
    try:
        nombre = verificar_correo(token)
        return {"mensaje": f"Correo verificado exitosamente. Bienvenido, {nombre}."}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/restablecer")
def restablecer(payload: RestablecerRequest):
    try:
        restablecer_contrasena(payload.token, payload.contrasena_nueva)
        return {"mensaje": "Contraseña restablecida exitosamente. Ya puedes iniciar sesión."}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
