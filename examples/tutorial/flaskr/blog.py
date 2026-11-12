from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort
from .auth import login_required
from .models import Post, db
from .uploads import delete_upload, save_upload


bp = Blueprint("blog", __name__)


@bp.route("/")
def index():
    posts = db.session.execute(
        db.select(Post).order_by(Post.created.desc())
    ).scalars().all()

    return render_template("blog/index.html", posts=posts)


def get_post(id, check_author=True):
    post = db.session.get(Post, id)

    if post is None:
        abort(404, f"O post {id} não existe.")

    if check_author and post.author_id != g.user.id:
        abort(403)

    return post


@bp.route("/create", methods=("GET", "POST"))
@login_required
def create():
    if request.method == "POST":
        title = request.form["title"].strip()
        body = request.form["body"]
        image_file = request.files.get("imagem")
        error = None

        if not title:
            error = "O título é obrigatório."

        image_name = None

        if error is None:
            try:
                image_name = save_upload(image_file)
            except ValueError as e:
                error = str(e)

        if error is not None:
            flash(error)
        else:
            post = Post(
                title=title,
                body=body,
                author_id=g.user.id,
                imagem_post=image_name,
            )

            db.session.add(post)
            db.session.commit()

            return redirect(url_for("blog.index"))

    return render_template("blog/create.html")


@bp.route("/<int:id>/update", methods=("GET", "POST"))
@login_required
def update(id):
    post = get_post(id)

    if request.method == "POST":
        title = request.form["title"].strip()
        body = request.form["body"]
        image_file = request.files.get("imagem")
        error = None

        if not title:
            error = "O título é obrigatório."

        new_image = None

        if error is None:
            try:
                new_image = save_upload(image_file)
            except ValueError as e:
                error = str(e)

        if error is not None:
            flash(error)
        else:
            post.title = title
            post.body = body

            if new_image:  # só troca a imagem se uma nova foi enviada
                delete_upload(post.imagem_post)
                post.imagem_post = new_image

            db.session.commit()

            return redirect(url_for("blog.index"))

    return render_template("blog/update.html", post=post)


@bp.route("/<int:id>/delete", methods=("POST",))
@login_required
def delete(id):
    post = get_post(id)

    delete_upload(post.imagem_post)

    db.session.delete(post)
    db.session.commit()

    return redirect(url_for("blog.index"))