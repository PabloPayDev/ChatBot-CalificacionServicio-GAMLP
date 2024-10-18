from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import http.client
import json

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///metapython.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ======= ======= TEXT TO USE ======= =======
flow1 = [
    "Hola soy tu asistente virtual, porfavor responde a las siguientes pregutnas para calificar tu atencion en plataforma siendo un 1 muy malo y 5 muy bueno",
     "Selecciona una de las opciones",
    "1️⃣. Siguiente"
]
flow2 = [
    "Como fue tu experiencia general en la atencion?",
     "Selecciona una de las opciones",
    "1️⃣. Muy mala",
    "2️⃣. Mala",
    "3️⃣. Media",
    "4️⃣. Buena",
    "5️⃣. Muy buena"
]

flow3 = [
    "El tiempo de espera fue:",
     "Selecciona una de las opciones",
    "1️⃣. Muy lento.",
    "2️⃣. Lento",
    "3️⃣. Medio",
    "4️⃣. Rapido",
    "5️⃣. Muy rapido"
]

flow4 = [
    "Desea agregar una nota sobre su experiencia? \n\n Ej: Buena actitud del operador de plataforma."
]

flow5 = [
    "Gracias por su retroalimentacion",
    "1️⃣. Finalizar"
]

flowInvalid = [
    "Su respuesta no es valida, porfavor ingrese lo que se especifica."
]
chatbotFlowMessages = [
    flow1,
    flow2,
    flow3,
    flow4,
    flow5,
    flowInvalid
]
# ======= ======= ======= ======= =======

class Log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha_y_hora = db.Column(db.DateTime, default=datetime.utcnow)
    texto = db.Column(db.Text)

with app.app_context():
    db.create_all()

def sortByDate(register):
    return sorted(register, key=lambda x: x.fecha_y_hora, reverse=True)

@app.route('/')
def index():
    registros = Log.query.all()
    registros_ordenados = sortByDate(registros)
    return (render_template("index.html", registros = registros_ordenados))

mensajes_log = []

def addMessageLog(texto):
    mensajes_log.append(texto)
    newRegister = Log(texto=json.dumps(texto))
    db.session.add(newRegister)
    db.session.commit()

TOKEN = "CHATBOTTOKENTEST"

@app.route('/webhook', methods=['GET','POST'])
def webhook():
    if(request.method == 'GET'):
        challenge = verificar_token(request)
        return challenge
    elif(request.method == 'POST'):
        response = recibir_mensaje(request)
        return response

def verificar_token(req):
    token = req.args.get('hub.verify_token')
    challenge = req.args.get('hub.challenge')

    if(challenge and token == TOKEN):
        return challenge
    else:
        return jsonify({'error':'Token Invalido'}),401

def recibir_mensaje(req):
    try:
        req = request.get_json()

        entry = req["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]
        objeto_mensaje = value["messages"]

        if(objeto_mensaje):
            messages = objeto_mensaje[0]
            if("type" in messages):
                tipo = messages["type"]
                addMessageLog(json.dumps(messages))

                if(tipo == "interactive"):
                    tipo_interactivo = messages["interactive"]["type"]
                    if(tipo_interactivo == "button_reply"):
                        text = messages["interactive"]["button_reply"]["id"]
                        numero = messages["from"]
                        enviar_mensajes_whatsapp(text, numero)

                if("text" in messages):
                    text = messages["text"]["body"]
                    numero = messages["from"]

                    enviar_mensajes_whatsapp(text, numero)
                    
                    addMessageLog(json.dumps(messages))

        return jsonify({'message':'EVENT RECEIVED'})
    except Exception as e:
        return jsonify({'message':'EVENT RECEIVED'})

def enviar_mensajes_whatsapp(texto, numero):
    texto = texto.lower()
    if("hola" in texto):
        data = {
            "messaging_product": "whatsapp",    
            "recipient_type": "individual",
            "to": numero,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": "Hola, Bienvenido"
            }
        }
    elif( "boton" in texto):
        data = {
            "messaging_product": "whatsapp",    
            "recipient_type": "individual",
            "to": numero,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body":{
                    "text": "Confirmar tu registro?"
                },
                "footer":{
                    "text": "Selecciona una de las opciones"
                },
                "action":{
                    "buttons":[
                        {
                            "type": "reply",
                            "reply":{
                                "id": "btnOp1",
                                "title": "Si"
                            }
                        },
                        {
                            "type": "reply",
                            "reply":{
                                "id": "btnOp2",
                                "title": "No"
                            }
                        }
                    ]                    
                }                
            }
        }
    else:
        data = {
            "messaging_product": "whatsapp",    
            "recipient_type": "individual",
            "to": numero,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": "Continua conversacion"
            }
        }
    data = json.dumps(data)
    token = "EAAWXJp8ZCZCyABO7X61k5gRAszumdx4zELWrpiJnKTiBhsR8NfWH05o8ZB6eZCuR8nDzEHVPYgAT4QKdoabQu23W1Wf0SLIZA2FphCJcpUoSrcfTpUtHj8Ngq1qScFGDrwZARdQOr0FUvdZAyEQbHxWdCFEmvJOt8xePB5moKp5dZCz1DGFsiG5hu3Uh9kY8QP1KLKr4biLc8zo1EYZAxFbBoyDub"
    headers = {
        "Content-Type" : "application/json",
        "Authorization": "Bearer "+token
    }

    connection = http.client.HTTPSConnection("graph.facebook.com")

    try:
        connection.request("POST", "/v20.0/374877792366425/messages", data, headers)
        response = connection.getresponse()
        print(response.status, response.reason)
    except Exception as e:
        addMessageLog(json.dumps(e))
    finally:
        connection.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=80,debug=True)