import os
from datetime import datetime

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from uvicorn import run


class Data(BaseModel):
    content: str


app = FastAPI(docs_url="/")

# Es necesario comprobar si los dispositivos mandan la url /iclock/cdata o sólo cdata (lo mismo pasa con las demás).


@app.get("/iclock/cdata", response_class=PlainTextResponse)
async def cdata_endpoint(
    SN: str | None = None,
    type: str | None = None,
    options: str | None = None,
    pushver: str | None = None,
    DeviceType: str | None = None,
    PushOptionsFlag: str | None = None,
    language: int | None = None,
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
    print(f"\ttype: {type}")
    print(f"\toptions: {options}")
    print(f"\tpushver: {pushver}")
    print(f"\tDeviceType: {DeviceType}")
    print(f"\tlanguage: {language}")
    print(f"\tPushOptionsFlag: {PushOptionsFlag}")

    if type:
        # Pedido de fecha y hora del servidor por parte del dispositivo (lo segundo cuando se enciende).
        return timestamp

    if type is None:
        # Pedido de datos iniciales de configuración del dispositivo (lo primero cuando se enciende).
        result = f"GET OPTION FROM: {SN}\n\
ErrorDelay=60\n\
Delay=30\n\
TransTimes=0\n\
TransInterval=0\n\
TransFlag=0100000\n\
Realtime=1\n\
Encrypt=None\n\
TimeZone=-05:00\n\
Timeout=60\n\
SyncTime=3600\n\
ServerVer=0.0.1 2025-02-08\n\
OPERLOGStamp={timestamp}"
        return result
    return None


# Notificación en tiempo real
@app.post("/iclock/cdata", response_class=PlainTextResponse)
async def real_time(data: Data, SN: str | None = None, table: str | None = None, Stamp: str | None = None):
    if table == "OPERLOG":  # Operaciones efectuadas en tiempo real
        # Obtener path a carpeta del archivo
        # path = os.path.dirname(os.path.realpath(__file__))
        # with open(path + "/operlog.txt", "xt") as f:  # En Windows cambiar / por \\
        #     f.write(data.content + "\n")
        print(f"Se ha recibido una notificacion en tiempo real del dispositivo con serie {SN}")
        print(f"\ttable: {table}")
        print(f"\tStamp: {Stamp}")
        print(f"\tMensaje recibido: {data.content}")
    return "OK"


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
    data: Data,
    SN: str | None = None,
):
    print(f"Se ha recibido la confirmacion de la ejecucion del comando enviado: {data.content}")
    return "OK"


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))  # Render asigna el puerto a la variable de entorno 'PORT'
    run(app, host="0.0.0.0", port=port)
