from minion.core import Application
from minion.request import Response
from minion.wsgi import create_app


app = Application()


@app.route("/")
def index(request):
    return Response("Hello World!")


wsgi = create_app(app)
