"""
flaskr -- the Flask tutorial app. Or, should I say, Minion.io

"""

from contextlib import closing
import os
import sqlite3
import textwrap

import jinja2
import werkzeug.wrappers

from minion import Application, Response, resource, wsgi_app
from minion.routers import WerkzeugRouter
import examples.static


CSS = os.path.join(os.path.dirname(examples.static.__file__), "flaskr.css")
config = {
    "credentials" : {"user" : "admin", "password" : "default"},
    "database" : {"uri" : "/tmp/flaskr.db"},
}
app = Application(router=WerkzeugRouter())
bin = resource.Bin()


@app.route("/")
@bin.needs(["db", "j2env"])
def show_entries(request, db, j2env):
    cur = db.execute("SELECT title, text FROM entries ORDER BY id DESC")
    entries = cur.fetchall()
    content = j2env.get_template("show_entries.html").render(entries=entries)
    return Response(content.encode("utf-8"))


@app.route('/add', methods=['POST'])
@bin.needs(["db", "j2env"])
def add_entry(request, db, j2env):
    # if not session.get('logged_in'):
    #     return Response(code=401)
    db.execute(
        "INSERT INTO entries (title, text) VALUES (?, ?)",
        [request.form["title"], request.form["text"]]
    )
    db.commit()
    # flash('New entry was successfully posted')
    # return redirect(url_for('show_entries'))
    return Response(code=302, headers={"Location" : "/"})


@app.route("/login", methods=["GET", "POST"])
@bin.needs(["j2env"])
def login(request):
    error = None
    if request.method == "POST":
        if request.form["username"] != config["credentials"]["user"]:
            error = "Invalid username"
        elif request.form["password"] != config["credentials"]["password"]:
            error = "Invalid password"
        else:
            # session["logged_in"] = True
            # flash("You were logged in")
            # return redirect(url_for("show_entries"))
            return Response(code=302, headers={"Location" : "/"})
    content = j2env.get_template("login.html").render(error=error)
    return Response(content.encode("utf-8"))


@app.route("/logout")
def logout(request):
    # session.pop("logged_in", None)
    # flash("You were logged out")
    # return redirect(url_for("show_entries"))
    return Response(code=302, headers={"Location" : "/"})


@app.route("/static/flaskr.css")
def style(request):
    with open(CSS) as css:
        return Response(css.read())


@bin.provides("db")
def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(config["database"]["uri"])
    rv.row_factory = sqlite3.Row
    return rv


def init_db():
    """Creates the database tables."""
    with closing(connect_db()) as db:
        db.cursor().execute("DROP TABLE IF EXISTS entries")
        db.cursor().execute(
            """
            CREATE TABLE entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                text TEXT NOT NULL
            )
            """
        )
        db.commit()


wsgi = wsgi_app(app, request_class=werkzeug.wrappers.Request)
loader = jinja2.DictLoader(
    dict(
        (k, textwrap.dedent(v)) for k, v in (
            (
                "layout.html", """
                    <!doctype html>
                    <title>Flaskr</title>
                    <link rel=stylesheet type=text/css href="/static/flaskr.css">
                    <div class=page>
                    <h1>Flaskr</h1>
                    {#
                    <div class=metanav>
                    {% if not session.logged_in %}
                        <a href="/login">log in</a>
                    {% else %}
                        <a href="/logout">log out</a>
                    {% endif %}
                    </div>
                    {% for message in get_flashed_messages() %}
                        <div class=flash>{{ message }}</div>
                    {% endfor %}
                    #}
                    {% block body %}{% endblock %}
                    </div>
                """
            ),
            (
                "show_entries.html", """
                    {% extends "layout.html" %}
                    {% block body %}
                    {# {% if session.logged_in %} #}
                        <form action="/add" method=post class=add-entry>
                        <dl>
                            <dt>Title:
                            <dd><input type=text size=30 name=title>
                            <dt>Text:
                            <dd><textarea name=text rows=5 cols=40></textarea>
                            <dd><input type=submit value=Share>
                        </dl>
                        </form>
                    {# {% endif %} #}
                    <ul class=entries>
                    {% for entry in entries %}
                        <li><h2>{{ entry.title }}</h2>{{ entry.text|safe }}
                    {% else %}
                        <li><em>Unbelievable.  No entries here so far</em>
                    {% endfor %}
                    </ul>
                    {% endblock %}
                """
            ),
            (
                "login.html", """
                    {% extends "layout.html" %}
                    {% block body %}
                    <h2>Login</h2>
                    {% if error %}<p class=error><strong>Error:</strong> {{ error }}{% endif %}
                    <form action="/login" method=post>
                        <dl>
                        <dt>Username:
                        <dd><input type=text name=username>
                        <dt>Password:
                        <dd><input type=password name=password>
                        <dd><input type=submit value=Login>
                        </dl>
                    </form>
                    {% endblock %}
                """
            ),
        )
    )
)
bin.globals["j2env"] = jinja2.Environment(loader=loader)


if __name__ == "__main__":
    init_db()
