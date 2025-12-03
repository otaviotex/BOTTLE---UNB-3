from bottle import route, run, template, request, redirect, static_file, response, TEMPLATE_PATH
from database import session, Medico, Agendamento
from datetime import datetime
import hashlib
import os
import json



TEMPLATE_PATH.insert(0, './view')


@route('/static/<filepath:path>')
def server_static(filepath):
    return static_file(filepath, root='./static')



@route('/')
def home():
    return template('view/agend.html')



@route('/medico')
def medico():
    return template('view/logmedico.html')


@route('/login_medico', method='POST')
def login_medico_post():
    crm = request.forms.get('crm')
    senha = request.forms.get('senha')

    medico = session.query(Medico).filter_by(crm=crm).first()
    
    if not medico:
        return "<h2>CRM não encontrado!</h2><a href='/medico'>Voltar</a>"
    
    salt_hex = medico.salt
    senha_hash_salva = medico.senha
    salt_bt = bytes.fromhex(salt_hex)
    
    hash_digitado = hashlib.sha256(salt_bt + senha.encode()).hexdigest()
    
    if hash_digitado == senha_hash_salva:
        return redirect(f"/area_medico?nome={medico.nome}")
    else:
        return "<h2>Senha incorreta!</h2><a href='/medico'>Voltar</a>"
    
@route('/area_medico')
def area_medico():
    nome = request.query.get('nome', 'Medico')

    medico = session.query(Medico).filter_by(nome=nome).first()

    if not medico:
        return "Erro: médico não encontrado."

    pacientes = (
        session.query(Agendamento)
        .filter_by(especialidade=medico.especialidade, medico_id=None)
        .order_by(Agendamento.data, Agendamento.hora)
        .all()
    )

    return template('view/area_medico.html',
                    nome=nome,
                    medico=medico,
                    pacientes=pacientes)


@route('/assumir_paciente', method='POST')
def assumir_paciente():
    medico_id = request.forms.get('medico_id')
    paciente_id = request.forms.get('paciente_id')

    if not medico_id or not paciente_id:
        return json.dumps({"status": "error", "message": "dados incompletos"})

    ag = session.query(Agendamento).filter_by(id=paciente_id).first()

    if not ag:
        return json.dumps({"status": "error", "message": "agendamento inexistente"})

    # Se já foi assumido
    if ag.medico_id:
        medico_existente = session.query(Medico).filter_by(id=ag.medico_id).first()
        return json.dumps({
            "status": "taken",
            "medico_nome": medico_existente.nome
        })

    # Assumindo agora
    ag.medico_id = medico_id
    session.commit()

    medico = session.query(Medico).filter_by(id=medico_id).first()

    return json.dumps({
        "status": "ok",
        "medico_nome": medico.nome
    })


@route('/cadastro_medico')
def cadastro_medico():
    return template('view/cadastromedico.html')


@route('/salvar_medico', method='POST')
def salvar_medico():
    nome = request.forms.get('nome')
    idade = int(request.forms.get('idade'))
    genero = request.forms.get('genero')
    crm = request.forms.get('crm')
    especialidade = request.forms.get('especialidade')
    senha = request.forms.get('senha')
    
    salt = os.urandom(16)
    salt_hex = salt.hex()
    
    senha_hash = hashlib.sha256(salt+ senha.encode()).hexdigest()

    novo = Medico(
        nome=nome,
        idade=idade,
        genero=genero,
        crm=crm,
        especialidade=especialidade,
        senha=senha_hash,
        salt = salt_hex
    )

    session.add(novo)
    session.commit()

    return f"""
        <h2>Médico cadastrado com sucesso!</h2>
        <p>{nome} — {especialidade}</p>
        <a href='/medico'>Voltar</a>
    """



@route('/paciente')
def paciente():
    return template('view/logpaciente.html')


@route('/enviar', method='POST')
def enviar_paciente():
    nome = request.forms.get('nome')
    telefone = request.forms.get('telefone')
    email = request.forms.get('email')
    return template('view/agendamento1.html', nome=nome, telefone=telefone, email=email)


@route('/agendamento')
def agendamento():

    especialidades = (
        session.query(Medico.especialidade)
        .distinct()
        .order_by(Medico.especialidade)
        .all()
    )
    especialidades = [e[0] for e in especialidades]

    return template('view/agendamento1.html', especialidades=especialidades)

@route('/minhas_consultas')
def minhas_consultas():

    email = request.query.get('email')

    consultas = (
        session.query(Agendamento)
        .filter_by(email=email)
        .order_by(Agendamento.data, Agendamento.hora)
        .all()
    )

    return template('view/minhas_consultas.html', consultas=consultas, email=email)


 

# CANCELAR CONSULTA
@route('/cancelar_consulta/<id:int>', method='POST')
def cancelar_consulta(id):

    consulta = session.query(Agendamento).filter_by(id=id).first()

    if consulta:
        email = consulta.email
        session.delete(consulta)
        session.commit()
        redirect(f'/minhas_consultas?email={email}')

    return "<h2>Consulta não encontrada!</h2><a href='/paciente'>Voltar</a>"




@route('/agendamento_etapa1', method='POST')
def agendamento_etapa1_post():
    idade = request.forms.get('idade')
    convenio = request.forms.get('convenio')
    especialidade = request.forms.get('especialidade')

    nome = request.forms.get('nome')
    telefone = request.forms.get('telefone')
    email = request.forms.get('email')

    return template(
        'view/agendamento2.html',
        idade=idade,
        convenio=convenio,
        especialidade=especialidade,
        nome=nome,
        telefone=telefone,
        email=email
    )

import json
from bottle import response

@route('/api/pacientes_medico')
def api_pacientes_medico():
    medico_id = request.query.get('medico_id')

    if not medico_id:
        response.status = 400
        return json.dumps({"error": "medico_id faltando"})

    medico = session.query(Medico).filter_by(id=medico_id).first()
    if not medico:
        response.status = 404
        return json.dumps({"error": "médico não encontrado"})


    agendamentos = (
        session.query(Agendamento)
        .filter(Agendamento.especialidade == medico.especialidade)
        .order_by(Agendamento.data, Agendamento.hora)
        .all()
    )

    dados = []
    for a in agendamentos:
        dados.append({
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
    return json.dumps(dados)



# ============================
#  AGENDAMENTO – ETAPA 2
# ============================
@route('/agendamento_data')
def agendamento_data():
    return template('view/agendamento2.html')




@route('/confirmar_agendamento', method='POST')
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

    return f"""
        <h2>Consulta Agendada!</h2>
        <p><b>Nome:</b> {nome}</p>
        <p><b>Idade:</b> {idade}</p> 
        <p><b>Convênio:</b> {convenio}</p> 
        <p><b>Especialidade:</b> {especialidade}</p> 
        <p><b>Data:</b> {data}</p> 
        <p><b>Hora:</b> {hora}</p> 
        <br> <a href='/paciente'>Voltar</a>
    """



run(host='localhost', port=8080, debug=True, reloader=True)