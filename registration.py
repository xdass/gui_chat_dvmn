from tkinter import *
from tkinter import messagebox


def register(input):
    if len(input) > 1:
        print(input)
        messagebox.showinfo("Успешно!", "Пользователь создан, токен сохранен в файл")
    else:
        messagebox.showerror("Ошибка!", "Введите имя пользователя!")


root = Tk()
root.title("Регистрация пользователя(minechat)")
label = Label(text="Введите имя пользователя")
btn = Button(text="Зарегистрироваться", width=15, height=2, padx=10)
edit = Text(width=30, height=1)
label.pack(side=LEFT)
edit.pack(side=LEFT)
btn.pack(side=RIGHT)
btn["command"] = lambda: register(edit.get(1.0, END))
root.mainloop()
