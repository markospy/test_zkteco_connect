import os
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel, Field
from uvicorn import run

app = FastAPI(docs_url="/")

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pedro, quite algunos de los parametros que dice el manual que son opcionales
# para ganar en simplicidad. Deje otros, q si bien no se especifican en el manual
# los equipos los mandas y al parecer hay enviarlos en el cuerpo de la respuesta inicial
# El manual dice esto "Host header field: ${Required}" pero no se si se refiere a un body pq
# no aparece en la uri de la primera peticion.


# Esto segun  chatgpt mostraba el body, pero no lo hace. Bueno, probe ahora en el servidor real y si funciono.
# mando el body por correo.
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):

    return JSONResponse(
        status_code=422,
        content={
            "detail": exc.errors(),
            "body": request.json(),
        },
    )


# Esta es una clase con todas las keys que envie la solicitud que estamos analizando.
# No la uso en el codigo pero la dejare ahi por si hace falta en el futuro cuando haga la integracion.
class DeviceData(BaseModel):
    DeviceName: str
    MAC: str
    TransactionCount: int
    MaxAttLogCount: int
    UserCount: int
    MaxUserCount: int
    PhotoFunOn: int
    MaxUserPhotoCount: int
    FingerFunOn: int
    FPVersion: int
    MaxFingerCount: int
    FPCount: int
    FaceFunOn: int
    FaceVersion: int
    MaxFaceCount: int
    FaceCount: int
    FvFunOn: int
    FvVersion: int
    MaxFvCount: int
    FvCount: int
    PvFunOn: int | None
    PvVersion: str | None
    MaxPvCount: int | None
    PvCount: int
    Language: int
    IPAddress: str
    Platform: str
    OEMVendor: str
    FWVersion: str
    PushVersion: str
    RegDeviceType: int
    VisilightFun: str | None
    MultiBioDataSupport: str | None
    MultiBioPhotoSupport: str | None
    IRTempDetectionFunOn: str | None
    MaskDetectionFunOn: str | None
    UserPicURLFunOn: int
    VisualIntercomFunOn: str | None
    VideoTID: str | None
    QRCodeDecryptFunList: str | None
    VideoProtocol: str | None
    IsSupportQRcode: str | None
    QRCodeEnable: str | None
    SubcontractingUpgradeFunOn: int


class UserInfo(BaseModel):
    pin: str | None = Field(default=None, description="Id del usuario")
    name: str | None = Field(default=None, description="Nombre del usuario")
    pri: str | None = Field(default=0, description="Permiso del usuario, 0 para usuario normal")
    passwd: str | None = Field(default=None, description="Contraseña del usuario")
    card: str | None = Field(default=None, description="Card del usuario")
    viceCard: str | None = Field(default=None, description="Tarjeta visa del usuario")
    startDate: str | None = Field(default=None, description="Fecha de inicio")
    endDate: str | None = Field(default=None, description="Fecha de fin")


@app.get("/iclock/cdata", response_class=PlainTextResponse)
async def cdata_endpoint(
    SN: str | None = None,
    type: str | None = None,
    options: str | None = None,
    pushver: str | None = None,  # puede q se necesite mandar en la respuesta como valor de PushProtVer
    PushOptionsFlag: str | None = None,  # lo mismo q el anterior
):
    now = datetime.today()
    timestamp = "{}-{}-{}T{}:{}:{}-05:00".format(
        now.year,
        "%02d" % now.month,
        "%02d" % now.day,
        "%02d" % now.hour,
        "%02d" % now.minute,
        "%02d" % now.second,
    )
    print(f"El dispositivo con serie {SN} acaba de lanzar una llamada a la URI '/iclock/cdata/'.")

    if type:
        # Pedido de fecha y hora del servidor por parte del dispositivo (lo segundo cuando se enciende).
        print(f"El dispositivo con serie {SN} ha pedido la hora del servidor")
        return timestamp

    if type is None:
        # Pedido de datos iniciales de configuración del dispositivo (lo primero cuando se enciende).
        # no entiendo pq el manual pone OPERLOGStamp=9999
        # es TransFlag=100000000000 pq queremo enviar todos los registro de asistencia
        # no las asistencias por foto q es el 3. Asi es en el formato I
        # "Only format II needs to be supported". No se si refiere a q es obligatorio el formato II
        # TimeZone es para definir la zona horaria del servidor. Eso tendria q revisarlo aunq no creo
        # q sea algo indispensable para hacer los test
        result = f"GET OPTION FROM: {SN}\n\
OPERLOGStamp=9999\n\
ErrorDelay=30\n\
Delay=5\n\
TransTimes=00: 00\n\
TransInterval=1\n\
TransFlag=100000000000\n\
TimeZone=08:00\n\
Realtime=1\n\
Encrypt=None\n\
SyncTime=10\n\
ServerVer=2.2.14 2025-02-08\n\
PushProtVer={pushver}\n\
PushOptionsFlag={PushOptionsFlag}\n\
PushOptions=FingerFunOn,FaceFunOn"

        return JSONResponse(content=result, media_type="text/plain")  # la cabezera Date se envia por defecto
    return None


# Ejemplo de request y response en la api en primera llamada:
# Request:
# curl -X 'GET' \
#   'http://127.0.0.1:8000/iclock/cdata?SN=565645457474&options=all&pushver=2.4.1&PushOptionsFlag=1' \
#   -H 'accept: text/plain'

# Response:
# Status code: 200
# HEADER:
#  content-length: 279
#  content-type: text/plain; charset=utf-8
#  date: Thu,13 Feb 2025 03:37:27 GMT
#  server: uvicorn
# BODY:
# "GET OPTION FROM: 565645457474\nOPERLOGStamp=9999\nErrorDelay=30\nDelay=5\nTransTimes=00: 00\nTransInterval=1\nTransFlag=100000000000\nTimeZone=-05:00\nRealtime=1\nEncrypt=None\nServerVer=2.2.14 2025-02-08\nPushProtVer=2.4.1\nPushOptionsFlag=1\nPushOptions=FingerFunOn,FaceFunOn"


# Notificación en tiempo real
@app.post("/iclock/cdata", response_class=PlainTextResponse)
async def real_time(request: Request, SN: str | None = None, table: str | None = None, Stamp: str | None = None):
    print(f"Se ha recibido una notificacion en tiempo real del dispositivo con serie {SN}")
    body = await request.body()
    body_str = body.decode("utf-8")
    print(f"\tMensaje recibido: {body_str}")
    return "OK"


@app.get("/iclock/getrequest", response_class=PlainTextResponse)
async def get_request(SN: str | None = None, INFO: str | None = None, data: str | None = None):
    if INFO:
        return "OK"

    # Esto debe leer comandos del archivo commands.txt y mandarlos al dispositivo para su ejecución.
    path = os.path.dirname(os.path.realpath(__file__))
    result = ""
    with open(path + "/commands.txt", "r+") as f:
        for c in f.readlines():
            result = result + c + "\n"
    with open(path + "/commands.txt", "w") as f:
        f.write("")  # Escribir una cadena vacía
    if len(result) == 0:
        print("No hay comandos para enviar al dispositivo...")
        return result
    print(f"Enviando comandos {result} al dispositivo...")
    return result


# Esto debe crear un archivo confirmed.txt con la información de confirmación de ejecución de un comando enviado al dispositivo.
@app.post("/iclock/devicecmd", response_class=PlainTextResponse)
async def confirm_command(
    request: Request,
    SN: str | None = None,
):
    print(f"Se ha recibido una notificacion en tiempo real del dispositivo con serie {SN}")
    body = await request.body()
    body_str = body.decode("utf-8")
    print(f"\tMensaje recibido: {body_str}")
    return "OK"


@app.post("/open-door")
async def open_door(openDoor: bool | None = False):
    """Enviar un comando de abrir puerta. Se enviara al equipo en cuanto este lo solicite (cada 5 segundos)"""
    if openDoor:
        command = "C:1:AC_UNLOCK"

    # Sobrescribir el archivo command.txt
    path = os.path.dirname(os.path.realpath(__file__))
    with open(path + "/commands.txt", "w") as f:
        f.write(command)
    return {"mensaje": "Comando actualizado correctamente", "comando": command}


@app.post("/add-user")
async def add_user(info: UserInfo):
    """Enviar un comando con los datos del usuario. Se enviara al equipo en cuanto este lo solicite (cada 5 segundos)"""
    # Validar que los campos obligatorios estén presentes si openDoor es False
    if not all([info.pin, info.name, info.pri, info.passwd, info.card, info.viceCard, info.startDate, info.endDate]):
        raise HTTPException(status_code=400, detail="Faltan campos obligatorios cuando openDoor es False")

    # Crear el comando con los datos proporcionados
    command = f"C:1:DATA UPDATE USERINFO PIN={info.pin}\tName={info.name}\tPri={info.pri}\tPasswd={info.passwd}\tCard={info.card}\tGrp=1\tTZ=0000000000000000\tVerify=6\tViceCard={info.viceCard}\tStartDate={info.startDate}\tEndDate={info.endDate}"

    # Sobrescribir el archivo command.txt
    path = os.path.dirname(os.path.realpath(__file__))
    with open(path + "/commands.txt", "w") as f:
        f.write(command)
    return {"mensaje": "Comando actualizado correctamente", "comando": command}


@app.post("/reebot-client")
async def reebot_client(reebot: bool | None = False):
    """Reinicia el cliente (zkteco) para volver a cargar las configuraciones iniciales del servidor"""
    if reebot:
        command = "C:1:REBOOT"

    # Sobrescribir el archivo command.txt
    path = os.path.dirname(os.path.realpath(__file__))
    with open(path + "/commands.txt", "w") as f:
        f.write(command)
    return {"mensaje": "Comando actualizado correctamente", "comando": command}


@app.post("/clear-commands")
async def clear_commands():
    """Eliminar todos los comandos."""
    # Obtener la ruta del archivo commands.txt
    path = os.path.dirname(os.path.realpath(__file__))
    file_path = os.path.join(path, "commands.txt")

    try:
        # Abrir el archivo en modo escritura para vaciarlo
        with open(file_path, "w") as f:
            f.write("")  # Escribir una cadena vacía
        return {"mensaje": "El archivo commands.txt ha sido vaciado correctamente"}
    except Exception as e:
        # Manejar errores (por ejemplo, si el archivo no existe o no se puede escribir)
        raise HTTPException(status_code=500, detail=f"Error al vaciar el archivo: {str(e)}")


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))  # Render asigna el puerto a la variable de entorno 'PORT'
    run(app, host="0.0.0.0", port=port)
