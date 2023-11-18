from aiohttp import web

# http://localhost:8080/


async def wshandler(request: web.Request):
    """
    Функция wshandler обрабатывает соединения WebSocket, отправляет приветственные сообщения новым
    пользователям, рассылает сообщения всем подключенным пользователям и уведомляет других
    пользователей, когда пользователь присоединяется или отключается.

    param request:
        Параметр request — это экземпляр класса web.Request, который представляет HTTP-запрос,
        полученный сервером. Он содержит информацию о запросе, такую как метод HTTP, заголовки,
        URL-адрес и тело запроса. Он используется для обработки входящего соединения WebSocket и
        отправки/получения

    type request:
        web.Request

    return:
        объект `web.Response`, если соединение WebSocket недоступно, и объект
        `web.WebSocketResponse`, если соединение WebSocket доступно.
    """
    # создаём объект HTTP-ответа
    resp = web.WebSocketResponse()

    # проверяем, можем ли ответить сразу в запрос, а такое возможно,
    # только если используется веб-сокет
    available = resp.can_prepare(request)
    if not available:
        with open("PythonTestFiles\websocket.html", "rb") as fp:
            return web.Response(body=fp.read(), content_type="text/html")

    # открываем соединение через веб-сокеты
    await resp.prepare(request)

    # И шлём приветственное сообщение
    await resp.send_str("Welcome!!!")

    try:
        # настало время отослать всем пользователям, что у нас новый пользователь
        print("Someone joined.")
        for ws in request.app["sockets"]:
            await ws.send_str("Someone joined")
        request.app["sockets"].append(resp)

        # Далее мы начинаем перебирать сообщения, которые пришли от пользователя
        async for msg in resp:
            if msg.type == web.WSMsgType.TEXT:
                for ws in request.app["sockets"]:
                    if ws is not resp:
                        await ws.send_str(msg.data)
            else:
                return resp
        return resp

    # Когда же пользователь отключается, то выполнение цикла завершается,
    # а выполнение функции продолжается
    finally:
        # Мы удаляем соединение из списка, а всем пользователям сообщаем, что пользователь отключился.
        request.app["sockets"].remove(resp)
        print("Someone disconnected.")
        for ws in request.app["sockets"]:
            await ws.send_str("Someone disconnected.")


# По сути, мы здесь просто передаём всем клиентам, что соединение закрылось.
# Список app["sockets"] очищать не нужно, ведь больше мы его использовать
# не будем, а память и без нас очистится.
async def on_shutdown(app: web.Application):
    """
    Функция on_shutdown закрывает все открытые веб-сокеты при завершении работы приложения.

    param app:
        Параметр app является экземпляром класса web.Application. Он представляет запускаемое
        веб-приложение и предоставляет различные методы и атрибуты для управления приложением

    type app:
        web.Application
    """
    for ws in app["sockets"]:
        await ws.close()


def init():
    """
    Функция init инициализирует веб-приложение с помощью библиотеки aiohttp, настраивает список для
    хранения соединений, добавляет обработчик запроса GET и обработчик завершения работы.

    return:
        экземпляр веб-приложения, созданный с использованием библиотеки aiohttp.
    """
    # web из библиотеки aiohttp и используем его для создания экземпляра приложения
    app = web.Application()

    # сохраняем список app["sockets"] для хранения всех соединений
    app["sockets"] = []

    # В нём же мы будем проверять:
    #       был это обычный GET-запросов, по которому мы отдадим код страницы,
    #       или же запрос на websocket соединение.
    app.router.add_get(
        "/", wshandler
    )  # добавляет обработчик для GET-запросов по пути "/".

    app.on_shutdown.append(on_shutdown)
    return app


web.run_app(init())
