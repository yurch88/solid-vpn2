from flask import Flask, render_template, redirect, url_for, request, jsonify, send_file
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from dotenv import load_dotenv
import os
import subprocess

# Загрузка переменных окружения
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# Flask-Login: модель пользователя
class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

# Переменные окружения
WG_CONFIG_DIR = os.getenv("WG_CONFIG_DIR")
CLIENTS_DIR = os.path.join(WG_CONFIG_DIR, "clients")
os.makedirs(CLIENTS_DIR, exist_ok=True)

def list_clients():
    """Список существующих клиентских конфигураций."""
    return [f.split(".")[0] for f in os.listdir(CLIENTS_DIR) if f.endswith(".conf")]

@app.route("/")
def index():
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        password = request.form.get("password")
        if password == os.getenv("FLASK_LOGIN_PASSWORD"):
            user = User(id=1)
            login_user(user)
            return redirect(url_for("dashboard"))
        else:
            return render_template("login.html", error="Invalid password")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route("/dashboard")
@login_required
def dashboard():
    clients = list_clients()
    return render_template("dashboard.html", user=current_user, clients=clients)

@app.route("/add_user", methods=["POST"])
@login_required
def add_user():
    username = request.form.get("username")
    if not username:
        return jsonify({"status": "error", "message": "Username is required"}), 400

    client_config_path = os.path.join(CLIENTS_DIR, f"{username}.conf")
    if os.path.exists(client_config_path):
        return jsonify({"status": "error", "message": "User already exists"}), 400

    try:
        # Генерация конфигурации клиента с использованием сервера WireGuard
        subprocess.check_call([
            "docker", "exec", "wireguard",
            "bash", "-c",
            f"wg genkey | tee /config/clients/{username}.key | wg pubkey > /config/clients/{username}.pub && "
            f"wg set wg0 peer $(cat /config/clients/{username}.pub)"
        ])

        # Проверяем, создался ли файл конфигурации
        if not os.path.exists(client_config_path):
            return jsonify({"status": "error", "message": "Failed to create client configuration file"}), 500

        return jsonify({"status": "success", "message": f"User {username} created successfully"}), 200
    except subprocess.CalledProcessError as e:
        print(f"Error creating user {username}: {e}")
        return jsonify({"status": "error", "message": "Failed to create user"}), 500

@app.route("/download/<username>")
@login_required
def download(username):
    client_config_path = os.path.join(CLIENTS_DIR, f"{username}.conf")
    if os.path.exists(client_config_path):
        return send_file(client_config_path, as_attachment=True)
    return "File not found", 404

@app.route("/delete/<username>", methods=["POST"])
@login_required
def delete(username):
    client_config_path = os.path.join(CLIENTS_DIR, f"{username}.conf")
    if os.path.exists(client_config_path):
        try:
            # Удаление клиента из конфигурации WireGuard
            subprocess.check_call([
                "docker", "exec", "wireguard",
                "bash", "-c",
                f"wg set wg0 peer $(cat /config/clients/{username}.pub) remove"
            ])
            os.remove(client_config_path)
            return jsonify({"status": "success", "message": f"User {username} deleted successfully"}), 200
        except subprocess.CalledProcessError as e:
            print(f"Error deleting user {username}: {e}")
            return jsonify({"status": "error", "message": "Failed to delete user"}), 500
    return jsonify({"status": "error", "message": "Client not found"}), 404

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=80)
