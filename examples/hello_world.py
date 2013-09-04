from minion import Application, Response, wsgi_app


app = Application()


@app.route("/")
def index(request):
    return Response("Hello World!")


wsgi = wsgi_app(app)
