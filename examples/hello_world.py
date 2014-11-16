from minion import Application, Response
from minion.wsgi import wsgi_app


app = Application()


@app.route("/")
def index(request):
    return Response("Hello World!")


wsgi = wsgi_app(app)
