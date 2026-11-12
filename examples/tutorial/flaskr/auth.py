import functools
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash
from .models import User, db
from .uploads import delete_upload, save_upload

bp = Blueprint("auth", __name__, url_prefix="/auth")


def get_user_by_username(username):
    return db.session.execute(
        db.select(User).filter_by(username=username)
    ).scalar_one_or_none()


@bp.route("/register", methods=("GET", "POST"))
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        avatar_file = request.files.get("avatar")
        error = None

        if not username:
            error = "O nome de usuário é obrigatório."
        elif not password:
            error = "A senha é obrigatória."
        elif get_user_by_username(username) is not None:
            error = f"O usuário {username} já está cadastrado."

        avatar_name = None

        if error is None:
            try:
                avatar_name = save_upload(avatar_file)
            except ValueError as e:
                error = str(e)

        if error is None:
            user = User(
                username=username,
                password=generate_password_hash(password),
                avatar=avatar_name,
            )
            db.session.add(user)

            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                delete_upload(avatar_name)
                error = f"O usuário {username} já está cadastrado."
            else:
                return redirect(url_for("auth.login"))

        flash(error)

    return render_template("auth/register.html")


@bp.route("/login", methods=("GET", "POST"))
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = get_user_by_username(username)
        error = None

        if user is None:
            error = "Usuário incorreto."
        elif not check_password_hash(user.password, password):
            error = "Senha incorreta."

        if error is None:
            session.clear()
            session["user_id"] = user.id
            return redirect(url_for("index"))

        flash(error)

    return render_template("auth/login.html")


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get("user_id")
    g.user = db.session.get(User, user_id) if user_id is not None else None


@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("auth.login"))
        return view(**kwargs)

    return wrapped_view