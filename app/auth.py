from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask import current_app
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from .models import User
from .models import db


auth_bp = Blueprint("auth", __name__)
login_manager = LoginManager()
login_manager.login_view = "auth.login"


def init_login(app):
    login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def roles_required(*roles):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                return login_manager.unauthorized()
            if current_user.role not in roles and "admin" not in roles:
                # Admin has full access by default
                if current_user.role != "admin":
                    flash("无访问权限", "warning")
                    return redirect(url_for("main.dashboard"))
            return func(*args, **kwargs)
        return wrapper
    return decorator


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter_by(username=username).first()
        if user and user.active and user.check_password(password):
            login_user(user)
            flash("登录成功", "success")
            next_url = request.args.get("next") or url_for("main.dashboard")
            return redirect(next_url)
        flash("用户名或密码错误", "danger")
    return render_template("login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("已退出登录", "info")
    return redirect(url_for("auth.login"))

