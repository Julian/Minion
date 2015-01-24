from minion.core import Application
from minion.request import Response
from minion.routing import Router, RoutesMapper
from minion.wsgi import create_app


app = Application(router=Router(mapper=RoutesMapper()))


@app.route("/greet/{user}", greeting="Hey")
def greet(request, greeting, user):
    return Response(u"{} {}\n".format(greeting, user).encode("utf-8"))


wsgi = create_app(app)
