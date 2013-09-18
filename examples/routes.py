from minion import Application, Response, wsgi_app
from minion.routers import RoutesRouter


app = Application(router=RoutesRouter())


@app.route("/greet/{user}", greeting="Hey")
def greet(request, greeting, user):
    return Response(u"{} {}\n".format(greeting, user).encode("utf-8"))


wsgi = wsgi_app(app)
