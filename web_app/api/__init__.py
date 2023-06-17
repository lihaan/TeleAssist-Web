from handlers import handleEndAssistSession, handleCheckAssistSession, handleStartAssistSession
from quart import Quart
from quart import request
from quart import jsonify
from telethon import TelegramClient
from dotenv import dotenv_values
import os
import time

curr_path = os.path.dirname(__file__)
secret_path = (os.path.abspath(f"{curr_path}/../.env"))
secrets = dotenv_values(secret_path)
API_ID = secrets["API_ID"]
API_HASH = secrets["API_HASH"]
MY_PHONE = secrets["MY_PHONE"]

app = Quart(__name__)


tele_session_file_path = (os.path.abspath(
    f"{curr_path}/../{MY_PHONE}.session"))
client = TelegramClient(tele_session_file_path, API_ID, API_HASH,
                        sequential_updates=True)


@app.before_serving
async def startup():
    print("Connecting to Telegram...")
    await client.start(MY_PHONE)


@app.after_serving
async def cleanup():
    await client.disconnect()


@app.post("/startAssistSession")
async def startAssistSession():
    data = await request.get_json()
    print(f"{time.asctime()}: startAssistSession - {data}")

    result = await handleStartAssistSession(data, client)

    return jsonify(result)


@app.post("/checkAssistSession")
async def checkAssistSession():
    data = await request.get_json()
    print(f"{time.asctime()}: checkAssistSession - {data}")

    result = await handleCheckAssistSession()

    return jsonify(result)


@app.post("/endAssistSession")
async def endAssistSession():
    data = await request.get_json()
    print(f"{time.asctime()}: endAssistSession - {data}")

    result = await handleEndAssistSession(client)

    return jsonify(result)


# For debugging connection
@app.get("/")
async def root():
    return {"message": "Hello world!"}


if __name__ == "__main__":
    app.run(
        use_reloader=False
    )
