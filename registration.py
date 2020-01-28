import os
from asyncio import Queue
import asyncio
import json
from tkinter import *
from tkinter import messagebox
from main import connect
from util import create_handy_nursery
from gui import TkAppClosed, update_tk
import aiofiles
from dotenv import load_dotenv


async def process(queue):
    host = os.getenv("HOST")
    write_port = os.getenv("WRITE_PORT")
    reader, writer = await connect(host, write_port)
    await reader.readline()
    username = await queue.get()
    writer.write("\n".encode())
    await writer.drain()
    await reader.readline()
    writer.write(f"{username}\n".encode())
    await writer.drain()
    register_response = await reader.readline()
    decoded_json = json.loads(register_response.decode())
    await save_credentials("credentials.txt", decoded_json)


def get_name(input_field, queue):
    value = input_field.get(1.0, END)
    if len(value) > 1:
        queue.put_nowait(value)
        messagebox.showinfo("Успешно!", f"Пользователь {value} создан, токен сохранен в файл")
        input_field.delete(1.0, END)
    else:
        messagebox.showerror("Ошибка!", "Введите имя пользователя!")


async def save_credentials(filepath, creds):
    async with aiofiles.open(filepath, "a", encoding="utf8") as fh:
        await fh.write(f"{creds['nickname']}=={creds['account_hash']}\n")


async def draw(sending_queue):
    root = Tk()

    root.title('Регистрация пользователя(minechat)')

    root_frame = Frame()
    root_frame.pack(fill="both", expand=True, padx=20, pady=20)

    input_frame = Frame(root_frame)
    input_frame.pack(side="bottom", fill=X)

    input_field = Text(input_frame, width=30, height=1)
    input_field.pack(side="left", fill=X, expand=True)

    send_button = Button(input_frame, height=1)
    send_button["text"] = "Зарегистрироваться"
    send_button["command"] = lambda: get_name(input_field, sending_queue)
    send_button.pack(side="left")

    await asyncio.gather(
        update_tk(root_frame),
        process(sending_queue)
    )


async def main():
    load_dotenv()
    name_queue = Queue()

    try:
        async with create_handy_nursery() as nursery:
            nursery.start_soon(draw(name_queue))
    except TkAppClosed:
        sys.exit()

if __name__ == '__main__':
    asyncio.run(main())
