import asyncio
import time
import json
import socket
import logging
import sys
from tkinter import messagebox

import aiofiles
import configargparse
from dotenv import load_dotenv
from async_timeout import timeout
import aionursery

import gui
from util import create_handy_nursery


PING_PONG_TIMEOUT = 15
PING_PONG_INTERVAL = 10
WATCHDOG_UPDATE_INTERVAL = 10

logger = logging.getLogger("watchdog_logger")
ch = logging.StreamHandler()
logger.setLevel(logging.DEBUG)
logger.addHandler(ch)


class InvalidToken(Exception):
    pass


async def connect(addr, port):
    sock = socket.create_connection((addr, port))
    return await asyncio.open_connection(sock=sock)


async def read_msgs(host, port, queue, history_q, status_q, watchdog_q):
    reader, writer = await connect(host, port)
    status_q.put_nowait(gui.ReadConnectionStateChanged.ESTABLISHED)
    while True:
        raw_message = await reader.readline()
        await watchdog_q.put("New message in chat")
        decoded_msg = raw_message.decode().replace("\n", "")
        queue.put_nowait(decoded_msg)
        history_q.put_nowait(decoded_msg)


async def _send(writer, queue, watchdog_q):
    while True:
        message = await queue.get()
        writer.write(f"{message}\n\n".encode())
        await watchdog_q.put("Message sent")
        await writer.drain()


async def send_msgs(options, queue, watchdog_q, status_updates_queue):
    reader, writer = await connect(options.host, options.write_port)
    user_info = await authorize(reader, writer, options.token, watchdog_q)
    status_updates_queue.put_nowait(gui.SendingConnectionStateChanged.ESTABLISHED)
    if user_info:
        event = gui.NicknameReceived(user_info)
        status_updates_queue.put_nowait(event)
        logger.debug(f"Выполнена авторизация. Пользователь {user_info}")

    async with create_handy_nursery() as nursery:
        nursery.start_soon(_send(writer, queue, watchdog_q))
        nursery.start_soon(ping_pong(reader, writer, watchdog_q))


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


async def authorize(reader, writer, token, watchdog_q):
    await reader.readline()
    writer.write(f"{token}\n".encode())
    await writer.drain()
    auth_resp = await reader.readline()
    json_data = json.loads(auth_resp.decode())
    if json_data:
        await watchdog_q.put("Authorization done")
        return json_data['nickname']
    else:
        messagebox.showinfo("Неверный токен", "Проверьте токен или зарегистрируйте новый")
        raise InvalidToken()


async def watch_for_connection(watch_dog_q):
    while True:
        try:
            async with timeout(WATCHDOG_UPDATE_INTERVAL) as cm:
                message = await watch_dog_q.get()
            logger.debug(f"[{time.time()}] Connection is alive! {message}")
        except asyncio.TimeoutError:
            logger.debug(f"{WATCHDOG_UPDATE_INTERVAL}s timeout is elapsed")
            raise ConnectionError


async def handle_connection(options, messages_queue, status_updates_queue, watchdog_queue, history_queue, sending_queue):

    load_messages_history("chat_history.txt", messages_queue)

    while True:
        try:
            status_updates_queue.put_nowait(gui.ReadConnectionStateChanged.INITIATED)
            status_updates_queue.put_nowait(gui.SendingConnectionStateChanged.INITIATED)

            async with create_handy_nursery() as nursery:
                nursery.start_soon(
                    read_msgs(options.host, options.port, messages_queue, history_queue, status_updates_queue, watchdog_queue)
                )
                nursery.start_soon(
                    send_msgs(options, sending_queue, watchdog_queue, status_updates_queue)
                )
                nursery.start_soon(watch_for_connection(watchdog_queue))
        except (aionursery.MultiError, ConnectionError, ConnectionResetError, socket.gaierror):
            logger.debug(">>>>>>>>>Connection error!")
            status_updates_queue.put_nowait(gui.ReadConnectionStateChanged.CLOSED)
            status_updates_queue.put_nowait(gui.SendingConnectionStateChanged.CLOSED)
            await asyncio.sleep(5)
        else:
            break


async def ping_pong(reader, writer, watchdog_q):
    while True:
        try:
            async with timeout(PING_PONG_TIMEOUT) as cm:
                writer.write("\n".encode())
                await writer.drain()
                await reader.readline()
            watchdog_q.put_nowait("Ping message was successful")
            await asyncio.sleep(PING_PONG_INTERVAL)
        except socket.gaierror:
            watchdog_q.put_nowait("Connection lost!")
            raise ConnectionError


def get_args():
    config = configargparse.ArgParser()
    config.add_argument("--host", help="Chat server host", env_var="HOST")
    config.add_argument("--port", help="Chat server port", env_var="PORT")
    config.add_argument("--write_port", help="Chat server port", env_var="WRITE_PORT")
    config.add_argument("--token", help="Chat user token", env_var="TOKEN")
    config.add_argument("--log_file", help="Path to log file", env_var="LOG_FILE")
    return config.parse_args()


async def main():
    load_dotenv()
    options = get_args()
    messages_queue = asyncio.Queue()
    sending_queue = asyncio.Queue()
    status_updates_queue = asyncio.Queue()
    history_queue = asyncio.Queue()
    watchdog_queue = asyncio.Queue()

    try:
        async with create_handy_nursery() as nursery:
            nursery.start_soon(gui.draw(messages_queue, sending_queue, status_updates_queue))
            nursery.start_soon(handle_connection(options,
                                                 messages_queue,
                                                 status_updates_queue,
                                                 watchdog_queue,
                                                 history_queue,
                                                 sending_queue)
                               )
            nursery.start_soon(save_messages("chat_history.txt", history_queue))
    except (gui.TkAppClosed, InvalidToken):
        sys.exit()


if __name__ == '__main__':
    asyncio.run(main())



