import asyncio
import socket
import time
import pickle
import gui

import aiofiles
import configargparse
from dotenv import load_dotenv


async def connect(addr, port):
    sock = socket.create_connection((addr, port))
    # set_keepalive_linux(sock)
    return await asyncio.open_connection(sock=sock)


async def generate_msgs(message_queue):
    while True:
        message_queue.put_nowait(f"Ping {time.time()}")
        await asyncio.sleep(1)


async def read_msgs(host, port, queue, history_q):
    reader, writer = await connect(host, port)
    while True:
        raw_message = await reader.readline()
        decoded_msg = raw_message.decode().replace("\n", "")
        queue.put_nowait(decoded_msg)
        history_q.put_nowait(decoded_msg)


async def save_messages(filepath, queue):
    async with aiofiles.open(filepath, "w") as fh:
        while True:
            message = await queue.get()
            await fh.write(message + "\n")


async def main():
    load_dotenv()
    config = configargparse.ArgParser()
    config.add_argument("--host", help="Chat server host", env_var="HOST")
    config.add_argument("--port", help="Chat server port", env_var="PORT")
    config.add_argument("--username", help="Username in chat", default="New user")
    config.add_argument("--token", help="Chat user token")
    config.add_argument("--message", help="Message to sent")
    config.add_argument("--log_file", help="Path to log file", env_var="LOG_FILE")
    options = config.parse_args()

    messages_queue = asyncio.Queue()
    sending_queue = asyncio.Queue()
    status_updates_queue = asyncio.Queue()
    history_queue = asyncio.Queue()

    await asyncio.gather(
        read_msgs(options.host, options.port, messages_queue, history_queue),
        save_messages("chat_history.txt", history_queue),
        gui.draw(messages_queue, sending_queue, status_updates_queue)

    )

asyncio.run(main())
