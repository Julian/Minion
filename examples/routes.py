from minion import Application, Response, wsgi_app
from minion.routing import RoutesMapper


app = Application(router=RoutesMapper())


@app.route("/greet/{user}", greeting="Hey")
def greet(request, greeting, user):
    return Response(u"{} {}\n".format(greeting, user).encode("utf-8"))


wsgi = wsgi_app(app)
