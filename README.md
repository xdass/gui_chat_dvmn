# Графический клиент для чата(minechat)
Доступно 2-клиента:
 * main.py - полноценный gui-клиент для общения в чате minechat(поддерживает историю сообщений)
 * registration - gui-клиент для регистрации нового пользователя

Служебные файлы:
 * util.py - вспомогательные функции
 * gui.py - Реализация GUI-интерфейса



## Как установить

Для работы клиентов нужен Python версии не ниже 3.7.

```bash
pip install -r requirements.txt
```
В директории проекта создать файл `.env` со следующими значениями:<br>
HOST=minechat.dvmn.org<br>
PORT=5000<br>
WRITE_PORT=5050<br>
LOG_FILE=./chat_log.txt<br>
TOKEN=YOUR_TOKEN

## Как запустить

```bash
python main.py

Выполнена авторизация. Пользователь Focused Loyd
[1580201350.5225937] Connection is alive! Authorization done
[1580201350.5235167] Connection is alive! Ping message was successful
[1580201351.9993446] Connection is alive! New message in chat
[1580201353.5381699] Connection is alive! New message in chat
[1580201356.3226976] Connection is alive! New message in chat
[1580201358.85638] Connection is alive! New message in chat
[1580201360.5247176] Connection is alive! Ping message was successful
[1580201361.7558668] Connection is alive! New message in chat
.......
```
Интерфейс чата
<a href="https://ibb.co/XZnKnDy"><img src="https://i.ibb.co/PZ2P2MT/example.png" alt="example" border="0"></a>

Интерфейс регистрации
<a href="https://imgbb.com/"><img src="https://i.ibb.co/XpNr4Zh/example-reg.png" alt="example-reg" border="0"></a>
