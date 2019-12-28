import asyncio
import json
import socket
import gui
from tkinter import messagebox

import aiofiles
import configargparse
from dotenv import load_dotenv


class InvalidToken(Exception):
    pass


async def connect(addr, port):
    sock = socket.create_connection((addr, port))
    # set_keepalive_linux(sock)
    return await asyncio.open_connection(sock=sock)


async def read_msgs(host, port, queue, history_q, status_q):
    reader, writer = await connect(host, port)
    status_q.put_nowait(gui.ReadConnectionStateChanged.ESTABLISHED)
    while True:
        raw_message = await reader.readline()
        decoded_msg = raw_message.decode().replace("\n", "")
        queue.put_nowait(decoded_msg)
        history_q.put_nowait(decoded_msg)


async def send_msgs(writer, queue):
    while True:
        message = await queue.get()
        writer.write(f"{message}\n\n".encode())
        await writer.drain()


async def save_messages(filepath, queue):
    async with aiofiles.open(filepath, "a", encoding="utf8") as fh:
        while True:
            message = await queue.get()
            await fh.write(message + "\n")


def load_messages_history(filepath, queue):
    try:
        with open(filepath, "r", encoding="utf8") as fh:
            for line in fh.readlines():
                queue.put_nowait(line.replace("\n", ""))
    except FileNotFoundError:
        print(f"Не найден файл {filepath}")


async def authorize(addr, port, token, status_q):
    reader, writer = await connect(addr, port)
    status_q.put_nowait(gui.SendingConnectionStateChanged.ESTABLISHED)
    await reader.readline()
    writer.write(f"{token}\n".encode())
    await writer.drain()
    auth_resp = await reader.readline()
    json_data = json.loads(auth_resp.decode())
    if json_data:
        print(f"Выполнена авторизация. Пользователь {json_data['nickname']}")
        return writer, json_data['nickname']
    else:
        messagebox.showinfo("Неверный токен", "Проверьте токен или зарегистрируйте новый")
        raise InvalidToken()


async def main():
    load_dotenv()
    config = configargparse.ArgParser()
    config.add_argument("--host", help="Chat server host", env_var="HOST")
    config.add_argument("--port", help="Chat server port", env_var="PORT")
    config.add_argument("--write_port", help="Chat server port", env_var="WRITE_PORT")
    config.add_argument("--username", help="Username in chat", default="New user")
    config.add_argument("--token", help="Chat user token", env_var="TOKEN")
    config.add_argument("--message", help="Message to sent")
    config.add_argument("--log_file", help="Path to log file", env_var="LOG_FILE")
    options = config.parse_args()

    messages_queue = asyncio.Queue()
    sending_queue = asyncio.Queue()
    status_updates_queue = asyncio.Queue()
    history_queue = asyncio.Queue()

    load_messages_history("chat_history.txt", messages_queue)

    writer, nickname = await authorize(options.host, options.write_port, options.token, status_updates_queue)
    event = gui.NicknameReceived(nickname)
    status_updates_queue.put_nowait(event)

    try:
        await asyncio.gather(
            read_msgs(options.host, options.port, messages_queue, history_queue, status_updates_queue),
            send_msgs(writer, sending_queue),
            save_messages("chat_history.txt", history_queue),
            gui.draw(messages_queue, sending_queue, status_updates_queue)

        )
    except (gui.TkAppClosed, InvalidToken):
        print("Чат закрыт")

asyncio.run(main())
