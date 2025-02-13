import os
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel
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


# Esto segun  chatgpt mostraba el body, pero no lo hace
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):

    return JSONResponse(
        status_code=422,
        content={
            "detail": exc.errors(),
            "body": request.json(),
        },
    )


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


@app.post("/iclock/cdata", response_class=PlainTextResponse)
async def receive_data(request: Request):
    body = await request.body()
    body_str = body.decode("utf-8")

    # Parse the URL-encoded string into a dictionary
    data = {}
    for pair in body_str.split(","):
        key, value = pair.split("=")
        data[key.strip("~")] = value

    # Validate and parse the data using Pydantic
    try:
        device_data = DeviceData(**data)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))

    print({"message": "Data received", "data": device_data})

    return "OK"


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
TimeZone=-05:00\n\
Realtime=1\n\
Encrypt=None\n\
ServerVer=2.2.14 2025-02-08\n\
PushProtVer={pushver}\n\
PushOptionsFlag={PushOptionsFlag}\n\
PushOptions=FingerFunOn,FaceFunOn"

        now = datetime.now()  # Get the current UTC time
        timestamp = now.strftime("%a, %d %b %Y %H:%M:%S GMT")  # 'Wed, 12 Feb 2025 22:05:59 GMT'

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
# @app.post("/iclock/cdata", response_class=PlainTextResponse)
# async def real_time(data: dict, SN: str | None = None, table: str | None = None, Stamp: str | None = None):
#     if table == "OPERLOG":  # Operaciones efectuadas en tiempo real
#         # Obtener path a carpeta del archivo
#         # path = os.path.dirname(os.path.realpath(__file__))
#         # with open(path + "/operlog.txt", "xt") as f:  # En Windows cambiar / por \\
#         #     f.write(data.content + "\n")
#         print(f"Se ha recibido una notificacion en tiempo real del dispositivo con serie {SN}")
#         print(f"\ttable: {table}")
#         print(f"\tStamp: {Stamp}")
#         print(f"\tMensaje recibido: {data.content}")
#     return "OK"


@app.get("/iclock/getrequest", response_class=PlainTextResponse)
async def get_request(SN: str | None = None, INFO: str | None = None, data: str | None = None):
    if INFO:
        # En lugar de guardar en un archivo, imprime la información del dispositivo
        print(f"Información del dispositivo recibida a la URI '/iclock/getrequest/' (BODY): {data}")
        print(f"Información del dispositivo recibida a la URI '/iclock/getrequest/' (INFO): {data}")
        return ""

    # Esto debe leer comandos del archivo commands.txt y mandarlos al dispositivo para su ejecución.
    path = os.path.dirname(os.path.realpath(__file__))
    result = ""
    with open(path + "/commands.txt", "rt") as f:
        for c in f.readlines():
            result = result + c + "\n"
    print(f"Enviando comandos {result} al dispositivo...")
    return result


# Esto debe crear un archivo confirmed.txt con la información de confirmación de ejecución de un comando enviado al dispositivo.
@app.post("/iclock/devicecmd", response_class=PlainTextResponse)
async def confirm_command(
    data: dict,
    SN: str | None = None,
):
    print(f"Se ha recibido la confirmacion de la ejecucion del comando enviado: {data.content}")
    return "OK"


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))  # Render asigna el puerto a la variable de entorno 'PORT'
    run(app, host="0.0.0.0", port=port)
