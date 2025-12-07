from bottle import Bottle, template, request, redirect, static_file, response, TEMPLATE_PATH
from database import session, Medico, Agendamento
from datetime import datetime
import hashlib
import os
import json
from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler
from geventwebsocket import WebSocketError

app = Bottle()
TEMPLATE_PATH.insert(0, './view')


@app.route('/static/<filepath:path>')
def server_static(filepath):
    return static_file(filepath, root='./static')



@app.route('/')
def home():
    return template('view/agend.html')


@app.route('/medico')
def medico():
    return template('view/logmedico.html')


@app.route('/paciente')
def paciente():
    return template('view/logpaciente.html')



@app.route('/cadastro_medico')
def cadastro_medico():
    return template('view/cadastromedico.html')


@app.route('/salvar_medico', method='POST')
def salvar_medico():
    nome = request.forms.get('nome')
    idade = int(request.forms.get('idade'))
    genero = request.forms.get('genero')
    crm = request.forms.get('crm')
    especialidade = request.forms.get('especialidade')
    senha = request.forms.get('senha')
    confirmar = request.forms.get('confirmar-senha')

    if senha != confirmar:
        return "<h2>As senhas não conferem!</h2><a href='/cadastro_medico'>Voltar</a>"

    if session.query(Medico).filter_by(crm=crm).first():
        return "<h2>CRM já cadastrado!</h2><a href='/cadastro_medico'>Voltar</a>"

    salt = os.urandom(16)
    senha_hash = hashlib.sha256(salt + senha.encode()).hexdigest()

    novo = Medico(
        nome=nome,
        idade=idade,
        genero=genero,
        crm=crm,
        especialidade=especialidade,
        senha=senha_hash,
        salt=salt.hex()
    )

    session.add(novo)
    session.commit()

    return f"""
    <h2>Médico cadastrado!</h2>
    <a href='/medico'>Voltar</a>
    """



@app.route('/login_medico', method="POST")
def login_medico_post():
    crm = request.forms.get('crm')
    senha = request.forms.get('senha')

    medico = session.query(Medico).filter_by(crm=crm).first()

    if not medico:
        return "<h2>CRM não encontrado!</h2><a href='/medico'>Voltar</a>"

    salt_bt = bytes.fromhex(medico.salt)
    hash_digitado = hashlib.sha256(salt_bt + senha.encode()).hexdigest()

    if hash_digitado == medico.senha:
        return redirect(f"/area_medico?nome={medico.nome}")

    return "<h2>Senha incorreta!</h2><a href='/medico'>Voltar</a>"



@app.route('/area_medico')
def area_medico():
    nome = request.query.get('nome')
    medico = session.query(Medico).filter_by(nome=nome).first()

    if not medico:
        return "Médico não encontrado"

    pacientes = (
        session.query(Agendamento)
        .filter(Agendamento.especialidade == medico.especialidade)
        .order_by(Agendamento.data, Agendamento.hora)
        .all()
    )

    return template("view/area_medico.html",
                    nome=nome,
                    medico=medico,
                    pacientes=pacientes)



@app.route('/assumir_paciente', method='POST')
def assumir_paciente():
    medico_id = request.forms.get('medico_id')
    paciente_id = request.forms.get('paciente_id')

    ag = session.query(Agendamento).filter_by(id=paciente_id).first()
    if not ag:
        return json.dumps({"status": "error"})


    conflito = session.query(Agendamento).filter(
        Agendamento.medico_id == medico_id,
        Agendamento.data == ag.data,
        Agendamento.hora == ag.hora
    ).first()

    if conflito:
        return json.dumps({
            "status": "conflito",
            "msg": f"Você já tem uma consulta marcada no dia {ag.data} às {ag.hora}!"
        })

    if ag.medico_id:
        med = session.query(Medico).filter_by(id=ag.medico_id).first()
        return json.dumps({"status": "taken", "medico_nome": med.nome, "email": ag.email})

    ag.medico_id = medico_id
    session.commit()

    med = session.query(Medico).filter_by(id=medico_id).first()

    enviar_ws({
        "tipo": "paciente_assumido",
        "paciente_id": paciente_id,
        "medico_nome": med.nome,
        "email": ag.email
    })

    return json.dumps({"status": "ok", "medico_nome": med.nome, "email": ag.email})


clientes_ws = set()

@app.route('/ws')
def ws_handler():
    ws = request.environ.get('wsgi.websocket')
    if not ws:
        return "WebSocket obrigatório"

    clientes_ws.add(ws)
    try:
        while True:
            msg = ws.receive()
            if msg is None:
                break
    except WebSocketError:
        pass
    finally:
        clientes_ws.remove(ws)


def enviar_ws(data):
    mortos = []
    for ws in clientes_ws:
        try:
            ws.send(json.dumps(data))
        except:
            mortos.append(ws)
    for ws in mortos:
        clientes_ws.remove(ws)



@app.route('/api/pacientes_medico')
def api_pacientes_medico():
    medico_id = request.query.get("medico_id")
    med = session.query(Medico).filter_by(id=medico_id).first()

    if not med:
        return json.dumps([])

    ags = (
        session.query(Agendamento)
        .filter(Agendamento.especialidade == med.especialidade)
        .order_by(Agendamento.data, Agendamento.hora)
        .all()
    )

    lista = []
    for a in ags:
        lista.append({
            "id": a.id,
            "nome": a.nome,
            "idade": a.idade,
            "convenio": a.convenio,
            "especialidade": a.especialidade,
            "data": a.data.isoformat(),
            "hora": a.hora.isoformat(),
            "email": a.email,
            "medico_id": a.medico_id,
            "medico_nome": a.medico.nome if a.medico else None
        })

    response.content_type = "application/json"
    return json.dumps(lista)



@app.route('/enviar', method='POST')
def enviar_paciente():
    nome = request.forms.get('nome')
    telefone = request.forms.get('telefone')
    email = request.forms.get('email')
    return template('view/agendamento1.html',
                    nome=nome, telefone=telefone, email=email)


@app.route('/agendamento')
def agendamento():
    especialidades = (
        session.query(Medico.especialidade)
        .distinct()
        .order_by(Medico.especialidade)
        .all()
    )
    especialidades = [e[0] for e in especialidades]
    return template('view/agendamento1.html', especialidades=especialidades)


@app.route('/agendamento_etapa1', method='POST')
def agendamento_etapa1_post():
    return template('view/agendamento2.html',
                    idade=request.forms.get('idade'),
                    convenio=request.forms.get('convenio'),
                    especialidade=request.forms.get('especialidade'),
                    nome=request.forms.get('nome'),
                    telefone=request.forms.get('telefone'),
                    email=request.forms.get('email'))


@app.route('/confirmar_agendamento', method='POST')
def confirmar_agendamento():
    nome = request.forms.get('nome')
    idade = int(request.forms.get('idade'))
    convenio = request.forms.get('convenio')
    especialidade = request.forms.get('especialidade')
    data = request.forms.get('data')
    hora = request.forms.get('hora')
    email = request.forms.get('email')

    data_conv = datetime.strptime(data, "%Y-%m-%d").date()
    hora_conv = datetime.strptime(hora, "%H:%M").time()

    novo = Agendamento(
        nome=nome,
        idade=idade,
        convenio=convenio,
        especialidade=especialidade,
        data=data_conv,
        hora=hora_conv,
        email=email
    )

    session.add(novo)
    session.commit()

    enviar_ws({
        "tipo": "novo_agendamento",
        "id": novo.id,
        "nome": nome,
        "idade": idade,
        "convenio": convenio,
        "especialidade": especialidade,
        "data": str(data_conv),
        "hora": str(hora_conv),
        "email": email
    })

    return f"""
    <h2>Consulta Agendada!</h2>
    <a href='/paciente'>Voltar</a>
    """


@app.route('/minhas_consultas')
def minhas_consultas():
    email = request.query.get('email')

    consultas = (
        session.query(Agendamento)
        .filter_by(email=email)
        .order_by(Agendamento.data, Agendamento.hora)
        .all()
    )

    return template('view/minhas_consultas.html',
                    consultas=consultas,
                    email=email)



server = pywsgi.WSGIServer(("0.0.0.0", 8080), app, handler_class=WebSocketHandler)

print("Servidor rodando: http://localhost:8080")
server.serve_forever()
