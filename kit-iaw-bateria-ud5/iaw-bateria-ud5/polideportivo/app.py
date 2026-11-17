# Batería UD5 · Las reservas del polideportivo municipal, en Python con Flask, servidas por Gunicorn.
# Gunicorn carga este programa UNA vez y lo deja encendido: si cambias algo, ./bateria.sh recargar
import os
from flask import Flask, render_template, request, session, redirect, url_for, jsonify, abort
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# ✍️ 4.4 La llave de las sesiones cogida de la variable de entorno o valor por defecto
app.secret_key = os.environ.get("SECRET_KEY", "polideportivo")

# 👀 Detrás de Nginx: fiarse de UNA capa de X-Forwarded-For y X-Forwarded-Proto (las que pone nuestro Nginx)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)

# 👀 Modo depuración: SOLO en el ordenador del programador (ver el bloque 5)
if os.environ.get("FLASK_DEBUG") == "1":
    from werkzeug.debug import DebuggedApplication
    app.debug = True
    app.wsgi_app = DebuggedApplication(app.wsgi_app, evalex=True)

# Los datos del polideportivo. En la UD6 vendrán de una base de datos; de momento, listas.
PISTAS = [
    {"id": 1, "nombre": "Pádel 1", "deporte": "pádel", "disponible": True},
    {"id": 2, "nombre": "Pádel 2", "deporte": "pádel", "disponible": True},
    {"id": 3, "nombre": "Tenis", "deporte": "tenis", "disponible": True},
    {"id": 4, "nombre": "Fútbol sala", "deporte": "fútbol", "disponible": False},   # en obras
    {"id": 5, "nombre": "Baloncesto", "deporte": "baloncesto", "disponible": True},
    {"id": 6, "nombre": "Frontón", "deporte": "frontón", "disponible": False},       # en obras
]
# Ojo: cada worker de Gunicorn tiene SU copia de esta lista (bloque 5). Por eso en la UD6 los datos van a una base de datos.
RESERVAS = [
    {"pista": 1, "hora": 18, "nombre": "Club de pádel", "comentario": "Entrenamiento"},
    {"pista": 3, "hora": 10, "nombre": "Marta", "comentario": "<b>¡Gracias!</b> Llevo yo las bolas"},   # lo escribió una usuaria
]
# El conserje: la contraseña se guarda como hash, nunca tal cual
CONSERJES = {"conserje": generate_password_hash("pista2026")}


def buscar_pista(id):
    # 👀 La pista con ese id, o None si no existe
    for p in PISTAS:
        if p["id"] == id:
            return p
    return None


def entero(texto):
    # 👀 Convierte un texto en número entero; si no es un entero («abc», «2.5», vacío), devuelve None
    try:
        return int(texto)
    except (TypeError, ValueError):
        return None


@app.after_request
def firma(respuesta):
    # 👀 Si la respuesta lleva esta cabecera, la ha cocinado Python (no Nginx)
    respuesta.headers["X-Cocinero"] = "gunicorn"
    return respuesta


@app.route("/")
def inicio():
    # 👀 La portada: la lista de pistas
    return render_template("index.html", pistas=PISTAS)


@app.route("/quien")
def quien():
    # 👀 Quién me ha llamado, según la app (bloque 1: X-Forwarded-For y X-Forwarded-Proto)
    return f"IP: {request.remote_addr} · Has entrado por: {request.scheme}\n"


@app.route("/pista/<int:id>")
def pista(id):
    p = buscar_pista(id)
    # ✍️ 2.1 Si la pista no existe, un 404 de verdad
    if p is None:
        abort(404)
    return render_template("pista.html", pista=p)


@app.route("/reservar", methods=["GET", "POST"])   # ✍️ 2.2 Permitir método POST
def reservar():
    errores = []
    hecha = None
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        comentario = request.form.get("comentario", "").strip()
        hora = entero(request.form.get("hora"))
        pista_id = entero(request.form.get("pista"))
        pista = buscar_pista(pista_id)

        # ✍️ 2.3 Validaciones de nombre y hora
        if not nombre:
            errores.append("Escribe tu nombre.")
        if hora is None or not (9 <= hora <= 21):
            errores.append("La hora tiene que ser un número entero de 9 a 21.")

        # ✍️ 2.4 Validaciones de la pista y disponibilidad
        if pista is None:
            errores.append("Esa pista no existe.")
        elif not pista["disponible"]:
            errores.append("Esa pista está cerrada.")
        else:
            # Comprobar si ya hay una reserva para esa pista a esa hora
            ocupada = False
            for r in RESERVAS:
                if r["pista"] == pista["id"] and r["hora"] == hora:
                    ocupada = True
                    break
            if ocupada:
                errores.append("Esa pista ya está reservada a esa hora.")

        # ✍️ 2.5 Gestión de errores (código 422) o guardado de la reserva
        if errores:
            return render_template("reservar.html", pistas=PISTAS, errores=errores, hecha=hecha), 422
        else:
            hecha = {"nombre": nombre, "pista": pista, "hora": hora, "comentario": comentario}
            RESERVAS.append({"pista": pista["id"], "hora": hora, "nombre": nombre, "comentario": comentario})

    return render_template("reservar.html", pistas=PISTAS, errores=errores, hecha=hecha)


@app.route("/entrar", methods=["GET", "POST"])
def entrar():
    # 👀 4.1 El login del conserje
    error = ""
    if request.method == "POST":
        usuario = request.form.get("usuario", "")
        clave = request.form.get("clave", "")
        if usuario in CONSERJES and check_password_hash(CONSERJES[usuario], clave):
            session["usuario"] = usuario
            return redirect(url_for("admin"))
        error = "Usuario o contraseña incorrectos"
    return render_template("entrar.html", error=error)


@app.route("/salir")
def salir():
    session.clear()
    return redirect(url_for("inicio"))


@app.route("/admin")
def admin():
    # ✍️ 4.2 Solo para el conserje: comprobar sesión activa
    if "usuario" not in session:
        return redirect(url_for("entrar"))
    filas = [dict(r, pista=buscar_pista(r["pista"])["nombre"]) for r in RESERVAS]
    return render_template("admin.html", usuario=session.get("usuario", "¿?"), reservas=filas)


@app.route("/api/pistas")
def api_pistas():
    # ✍️ 6.1 y 6.2 Listado de pistas en JSON y filtrado con ?libres=1
    if request.args.get("libres") == "1":
        libres = [p for p in PISTAS if p["disponible"]]
        return jsonify(libres)
    return jsonify(PISTAS)


@app.route("/api/pistas/<int:id>")
def api_pista(id):
    # ✍️ 6.3 Una pista en JSON o error 404 si no existe
    p = buscar_pista(id)
    if p is None:
        return jsonify({"error": "No existe esa pista"}), 404
    return jsonify(p)


@app.route("/error")
def error():
    # 👀 Un fallo a propósito (bloque 5)
    horas_libres = 0
    return f"Cada hora libre sale a {len(PISTAS) / horas_libres} pistas"
