from fastapi import APIRouter, HTTPException, status
from schemas import LoginRequest, TokenResponse
from services.auth_service import authenticate_user, create_token

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
