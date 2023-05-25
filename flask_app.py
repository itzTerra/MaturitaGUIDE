from flask import Flask, request, url_for, render_template, session, redirect
from werkzeug.security import generate_password_hash, check_password_hash
from db import MySQL
from random import shuffle
from traceback import format_exc
from os import environ
from dotenv import load_dotenv

app = Flask(__name__)
load_dotenv(".env")
app.secret_key = environ.get("SECRET_KEY")


# anj_detail helper func
def NewShuffleList(id_exception: int):
    try:
        with MySQL() as cur:
            cur.execute("SELECT id FROM anj ORDER BY RAND()")
            ids = cur.fetchall()
    except:
        print(format_exc())
        return

    shuffle_list = [idr[0] for idr in ids if idr[0] != id_exception]
    shuffle(shuffle_list)
    session["_shuffle_list"] = shuffle_list + [id_exception]
    session["shuffle_list"] = shuffle_list

# Helper render_template wrapper (adds frequently used base_error)
def render_template_with_err(template: str, **data):
    base_error = ""
    if "error" in session:
        base_error = session.pop("error")

    return render_template(template, base_error=base_error, **data)

# Routes ----------------------------------

@app.route('/')
def index():
    session["last_url"] = url_for("index")
    return render_template_with_err("index.html")


@app.route('/register/', methods=('GET', 'POST'))
def register():
    error = ""
    success = ""
    
    if request.method == 'POST':
        try:
            username = request.form['username']
            pass1 = request.form['pass1']
            pass2 = request.form['pass2']

            if len(username) < 4 or len(username) > 15 or not username.isalnum():
                error = 'Wrong username.'
            elif len(pass1) < 5:
                error = 'Password too short.'
            elif pass1 != pass2:
                error = "Passwords do not match."
            else:
                with MySQL() as cur:
                    cur.execute("SELECT * FROM user WHERE username=%s", (username,))

                    if cur.rowcount != 0:
                        error = "Username already exists."
                    else:
                        cur.execute(
                            "INSERT INTO user (username, password) VALUES (%s, %s)",
                            (username, generate_password_hash(pass1)),
                        )
                        cur.execute("COMMIT")
                        success = "User succesfully registered."

        except:
            print(format_exc())
            session["error"] = "Unknown error occured."
    
    session["last_url"] = url_for("register")
    return render_template_with_err('register.html', error=error, success=success)


@app.route('/login/', methods=('GET', 'POST'))
def login():
    if "user" in session:
        session.pop("user")
        return redirect(session.get("last_url", url_for("index")))
    
    error = ""
    if request.method == 'POST':
        try:
            username = request.form['username']
            password = request.form['pass']
            
            with MySQL() as cur:
                cur.execute('SELECT * FROM user WHERE username=%s', (username,))
                user = cur.fetchone()

                if cur.rowcount == 0:
                    error = 'Incorrect username.'
                elif not check_password_hash(user[2], password):
                    error = 'Incorrect password.'
                else:
                    session["user"] = (user[1], user[3])
                    return redirect(session.get("last_url", url_for("index")))

        except:
            print(format_exc())
            session["error"] = "Unknown error occured."
    
    return render_template_with_err('login.html', error=error)


@app.route('/change_pass/', methods=('GET', 'POST'))
def change_password():
    if "user" not in session:
        return redirect(session.get("last_url", url_for("index")))
    
    error = ""
    success = ""
    if request.method == 'POST':
        try:
            old = request.form['pass_old']
            new1 = request.form['pass_new1']
            new2 = request.form['pass_new2']

            if len(new1) < 5:
                error = 'Password too short.'
            elif new1 != new2:
                error = "New passwords do not match."
            else:
                with MySQL() as cur:
                    cur.execute('SELECT * FROM user WHERE username=%s', (session["user"][0],))
                    user = cur.fetchone()

                    if not check_password_hash(user[2], old):
                        error = 'Incorrect old password.'
                    else:
                        cur.execute(
                            "UPDATE user SET password=%s WHERE username=%s",
                            (generate_password_hash(new1), session["user"][0]),
                        )
                        cur.execute("COMMIT")
                        success = "Password successfully changed."

        except:
            print(format_exc())
            session["error"] = "Unknown error occured."
    
    return render_template_with_err('change_password.html', error=error, success=success)


@app.route("/manage_users/", methods=("GET", "POST"))
def manage_users():
    if session.get("user", ("", 0))[1] < 1:
        return redirect(session.get("last_url", url_for("index")))
    
    success = ""
    if request.method == "POST":
        try:
            userids = request.form.getlist("checkedUsers", type=int)
            
            with MySQL() as cur:
                cur.execute("DELETE FROM user WHERE id IN %s", (userids,))
                cur.execute("COMMIT")

            success = "User(s) successfully removed."
        except:
            print(format_exc())
            session["error"] = "Unknown error occured."

    users = []
    try:
        with MySQL() as cur:
            cur.execute("SELECT id, username, level FROM user ORDER BY level DESC, username")
            users = cur.fetchall()
    except:
        print(format_exc())
        session["error"] = "Unknown error occured."

    return render_template_with_err("manage_users.html", success=success, users=users)

# ANJ ----------------------------------

@app.route('/anj/')
def anj():
    items = ""
    try:
        with MySQL() as cur:
            cur.execute("SELECT * FROM anj")
            items = cur.fetchall()
    except:
        print(format_exc())
        session["error"] = "Unknown error occured."

    session["last_url"] = url_for("anj")
    return render_template_with_err("anj.html", items=items)


@app.route('/anj/<int:id>/')
def anj_detail(id):
    s = request.args.get("s")
    if s is None:
        NewShuffleList(id)

    try:
        with MySQL() as cur:
            cur.execute("SELECT * FROM anj WHERE id=%s", (id,))
            item = cur.fetchone()
            if item is None:
                raise ValueError()
    except:
        print(format_exc())
        session["error"] = "Unknown error occured."
        return redirect(session.get("last_url", url_for("index")))

    session["last_url"] = url_for("anj_detail", id=id)
    return render_template_with_err("anj_detail.html", item=item, shuffle=session.get("anj_shuffle", ""), collapse=session.get("anj_collapse", ""))


@app.route('/anj/<int:id>/next/')
def anj_next(id):
    next_id = id
    try:
        if session.get("anj_shuffle") == "checked":
            shuffle_list = session.get("shuffle_list")
            if shuffle_list is None:
                NewShuffleList(id)
            elif len(shuffle_list) == 0:
                session["shuffle_list"] = [i for i in session["_shuffle_list"]]

            shuffle_list = session["shuffle_list"]
            sID = shuffle_list.pop()
            session["shuffle_list"] = shuffle_list
            with MySQL() as cur:
                cur.execute("SELECT id FROM anj WHERE id=%s", (sID,))
                next_id = cur.fetchone()[0]
        else:
            asc = request.args.get("asc", "1")
            kw = (">", "id")
            if asc != "1":
                kw = ("<", "id DESC")

            with MySQL() as cur:
                cur.execute(f"SELECT id FROM anj WHERE id {kw[0]} %s ORDER BY {kw[1]} LIMIT 1", (id,))
                if cur.rowcount == 0:
                    cur.execute(f"SELECT id FROM anj ORDER BY {kw[1]} LIMIT 1")
                next_id = cur.fetchone()[0]
    except:
        print(format_exc())
        session["error"] = "Unknown error occured."

    return redirect(url_for("anj_detail", id=next_id, s=1))


@app.route('/anj/create/', methods=["GET", "POST"])
def anj_create():
    if session.get("user", ("", 0))[1] < 1:
        return redirect(session.get("last_url", url_for("index")))

    error = ""
    if request.method == "POST":
        try:
            title = request.form["title"]
            summary = request.form["summary"]
            body = request.form["body"]
            st_title = request.form["st_title"]
            st_body = request.form["st_body"]
            difficulty = request.form["difficulty"]
            if difficulty == "None":
                difficulty = None

            if not title or not st_title:
                error = "Titles must not be empty."
            else:
                with MySQL() as cur:
                    cur.execute(
                        "INSERT INTO anj (title, summary, body, st_title, st_body, difficulty) VALUES (%s, %s, %s, %s, %s, %s)",
                        (title, summary, body, st_title, st_body, difficulty)
                    )
                    id = cur.lastrowid
                    cur.execute("COMMIT")

                return redirect(url_for("anj_detail", id=id))
        except:
            print(format_exc())
            session["error"] = "Unknown error occured."

    return render_template_with_err("anj_create.html", error=error)


@app.route('/anj/<int:id>/edit/', methods=["GET", "POST"])
def anj_edit(id):
    if session.get("user", ("", 0))[1] < 1 or (id <= 21 and session.get("user", ("", 0))[1] < 2):
        return redirect(session.get("last_url", url_for("index")))
    
    try:
        with MySQL() as cur:
            cur.execute("SELECT * FROM anj WHERE id=%s", (id,))
            item = cur.fetchone()
            if item is None:
                raise ValueError("Item not found.")
    except:
        print(format_exc())
        session["error"] = "Item not found."
        return redirect(session.get("last_url", url_for("index")))

    error = ""
    if request.method == "POST":
        try:
            title = request.form["title"]
            summary = request.form["summary"]
            body = request.form["body"]
            st_title = request.form["st_title"]
            st_body = request.form["st_body"]
            difficulty = request.form["difficulty"]
            if difficulty == "None":
                difficulty = None
                
            if not title:
                error = "Title must not be empty."
            else:
                with MySQL() as cur:
                    cur.execute(
                        "UPDATE anj SET title=%s, summary=%s, body=%s, st_title=%s, st_body=%s, difficulty=%s WHERE id=%s",
                        (title, summary, body, st_title, st_body, difficulty, id)
                    )
                    cur.execute("COMMIT")
                return redirect(url_for("anj_detail", id=id))
        except:
            print(format_exc())
            session["error"] = "Unknown error occured."
    
    return render_template_with_err("anj_edit.html", error=error, item=item)


@app.route('/anj/<int:id>/delete/')
def anj_delete(id):
    if session.get("user", ("", 0))[1] < 1 or (id <= 21 and session.get("user", ("", 0))[1] < 2):
        return redirect(session.get("last_url", url_for("index")))

    try:
        with MySQL() as cur:
            cur.execute("DELETE FROM anj WHERE id=%s", (id,))
            cur.execute("COMMIT")
    except:
        print(format_exc())
        session["error"] = "Unknown error occured."

    return redirect(url_for("anj"))


# Route for JS AJAX (collapse and shuffles switches in anj_detail route)
@app.route('/setvar/', methods=["POST"])
def set_var():
    try:
        name = request.form["name"]
        value = request.form["value"]

        if name.lower() in ("user", "error", "_shuffle_list", "shuffle_list"):
            return "0"

        session[name] = value

        if name == "anj_shuffle" and value == "checked":
            id = request.form["id"]
            NewShuffleList(int(id))
    except:
        print(format_exc())

    return "1"

# CJL ----------------------------------

@app.route('/cjl/')
def cjl():
    items = ""
    try:
        with MySQL() as cur:
            cur.execute("SELECT * FROM cjl")
            items = cur.fetchall()
    except:
        print(format_exc())
        session["error"] = "Unknown error occured."

    session["last_url"] = url_for("cjl")
    return render_template_with_err("cjl.html", items=items)


@app.route('/cjl/<int:id>/')
def cjl_detail(id):
    try:
        with MySQL() as cur:
            cur.execute("SELECT * FROM cjl WHERE id=%s", (id,))
            item = cur.fetchone()
            if item is None:
                raise ValueError()
    except:
        print(format_exc())
        session["error"] = "Unknown error occured."
        return redirect(session.get("last_url", url_for("index")))

    session["last_url"] = url_for("cjl_detail", id=id)
    return render_template_with_err("cjl_detail.html", item=item)


@app.route('/cjl/<int:id>/next/')
def cjl_next(id):
    next_id = id
    try:
        asc = request.args.get("asc", "1")
        kw = (">", "id")
        if asc != "1":
            kw = ("<", "id DESC")
            
        with MySQL() as cur:
            cur.execute(f"SELECT id FROM cjl WHERE id {kw[0]} %s ORDER BY {kw[1]} LIMIT 1", (id,))
            if cur.rowcount == 0:
                cur.execute(f"SELECT id FROM cjl ORDER BY {kw[1]} LIMIT 1")
            next_id = cur.fetchone()[0]

    except:
        print(format_exc())
        session["error"] = "Unknown error occured."

    return redirect(url_for("cjl_detail", id=next_id))


@app.route('/cjl/create/', methods=["GET", "POST"])
def cjl_create():
    user = session.get("user")
    if not user:
        return redirect(session.get("last_url", url_for("index")))

    error = ""
    if request.method == "POST":
        try:
            title = request.form["title"]
            body = request.form["body"]

            if not title:
                error = "Title must not be empty."
            else:
                with MySQL() as cur:
                    cur.execute(
                        "INSERT INTO cjl (title, body, author, pubdate) VALUES (%s, %s, %s, curtime())",
                        (title, body, user[0])
                    )
                    id = cur.lastrowid
                    cur.execute("COMMIT")

                return redirect(url_for("cjl_detail", id=id))
        except:
            print(format_exc())
            session["error"] = "Unknown error occured."

    return render_template_with_err("cjl_create.html", error=error)


@app.route('/cjl/<int:id>/edit/', methods=["GET", "POST"])
def cjl_edit(id):
    user = session.get("user")
    if not user:
        return redirect(session.get("last_url", url_for("index")))
    
    try:
        with MySQL() as cur:
            cur.execute("SELECT * FROM cjl WHERE id=%s", (id,))
            item = cur.fetchone()

            if item[3] != user[0] and user[1] < 1:
                return redirect(session.get("last_url", url_for("index")))
    except:
        print(format_exc())
        session["error"] = "Item not found."
        return redirect(session.get("last_url", url_for("index")))

    error = ""
    if request.method == "POST":
        try:
            title = request.form["title"]
            body = request.form["body"]

            if not title:
                error = "Title must not be empty."
            else:
                with MySQL() as cur:
                    cur.execute(
                        "UPDATE cjl SET title=%s, body=%s, pubdate=curtime() WHERE id=%s",
                        (title, body, id)
                    )
                    cur.execute("COMMIT")
                return redirect(url_for("cjl_detail", id=id))
        except:
            print(format_exc())
            session["error"] = "Unknown error occured."
    
    return render_template_with_err("cjl_edit.html", error=error, item=item)


@app.route('/cjl/<int:id>/delete/')
def cjl_delete(id):
    user = session.get("user")
    if not user:
        return redirect(session.get("last_url", url_for("index")))

    try:
        with MySQL() as cur:
            cur.execute("SELECT author FROM cjl WHERE id=%s", (id,))
            item = cur.fetchone()
            
            if item[0] != user[0] and user[1] < 1:
                return redirect(session.get("last_url", url_for("index")))
            
            cur.execute("DELETE FROM cjl WHERE id=%s", (id,))
            cur.execute("COMMIT")
    except:
        print(format_exc())
        session["error"] = "Unknown error occured."

    return redirect(url_for("cjl"))

