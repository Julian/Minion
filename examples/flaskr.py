"""
flaskr -- the Flask tutorial app. Or, should I say, Minion.io

"""

from contextlib import closing
import os
import sqlite3

import jinja2
import werkzeug.wrappers

from minion.core import Application
from minion.request import Response
from minion.routing import Router, WerkzeugMapper
from minion.wsgi import create_app
import examples.static


CSS = os.path.join(os.path.dirname(examples.static.__file__), "flaskr.css")
loader = jinja2.FileSystemLoader(
    os.path.join(os.path.dirname(__file__), "templates", "flaskr"),
)
app = Application(
    jinja=jinja2.Environment(loader=loader),
    router=Router(mapper=WerkzeugMapper()),
    config = {
        "credentials" : {"user" : "admin", "password" : "default"},
        "database" : {"uri" : "/tmp/flaskr.db"},
    },
)


@app.route("/")
@app.bin.needs(["db", "jinja"])
def show_entries(request, db, jinja):
    cur = db.execute("SELECT title, text FROM entries ORDER BY id DESC")
    entries = cur.fetchall()
    content = jinja.get_template("show_entries.html").render(entries=entries)
    return Response(content.encode("utf-8"))


@app.route('/add', methods=['POST'])
@app.bin.needs(["db", "jinja"])
def add_entry(request, db, jinja):
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
@app.bin.needs(["config", "jinja"])
def login(request, config, jinja):
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
    content = jinja.get_template("login.html").render(error=error)
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


@app.bin.provides("db")
@app.bin.needs(["config"])
def connect_db(config):
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


wsgi = create_app(app)


if __name__ == "__main__":
    init_db()
