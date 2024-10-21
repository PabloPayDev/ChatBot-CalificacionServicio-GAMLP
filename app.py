from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import http.client
import json
import logging

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///metapython.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
logging.basicConfig(level=logging.DEBUG)
db = SQLAlchemy(app)

# ======= ======= TEXT TO USE ======= =======
flow1 = [
    "Hola soy tu asistente virtual, porfavor responde a las siguientes pregutnas para calificar tu atencion en plataforma siendo un 1 muy malo y 5 muy bueno",
    "Presione siguiente.",
    [
        "btnOpt1",
        "1️⃣. Siguiente"
    ]
]
flow2 = [
    "Como fue tu experiencia general en la atencion?",
     "Ver opciones",
     "Selecciona una de las opciones",
    [
        "btnOpt1",
        "1️⃣. Muy mala"
    ],
    [
        "btnOpt2",
        "2️⃣. Mala"
    ],
    [
        "btnOpt3",
        "3️⃣. Media"
    ],
    [
        "btnOpt4",
        "4️⃣. Buena"
    ],
    [
        "btnOpt5",
        "5️⃣. Muy buena"
    ]
]

flow3 = [
    "El tiempo de espera fue:",
    "Ver opciones",
    "Selecciona una de las opciones",
    [
        "btnOpt1",
        "1️⃣. Muy lento."
    ],
    [
        "btnOpt2",
        "2️⃣. Lento"
    ],
    [
        "btnOpt3",
        "3️⃣. Medio"
    ],
    [
        "btnOpt4",
        "4️⃣. Rapido"
    ],
    [
        "btnOpt5",
        "5️⃣. Muy rapido"
    ]
]

flow4 = [
    "Desea agregar una nota sobre su experiencia? \n\n Ej: Buena actitud del operador de plataforma."
]

flow5 = [
    "Gracias por su retroalimentacion",
    [
        "btnOpt1",
        "1️⃣. Finalizar"
    ]
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
def check_text_in_flow(text, chatbotFlowMessages, index):
    if index < 0 or index >= len(chatbotFlowMessages):
        return False
    
    flow = chatbotFlowMessages[index]

    for item in flow[2:]:
        if text in item:
            return True
    
    return False


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

flowStep = 0

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
                app.logger.debug('IN RecMen')
                tipo = messages["type"]
                addMessageLog(json.dumps(messages))

                if(tipo == "interactive"):
                    tipo_interactivo = messages["interactive"]["type"]
                    if(tipo_interactivo == "button_reply"):
                        text = messages["interactive"]["button_reply"]["id"]
                        numero = messages["from"]
                        enviar_mensajes_whatsapp(text, numero)
                    if(tipo_interactivo == "list_reply"):
                        text = messages["interactive"]["list_reply"]["id"]
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
    global chatbotFlowMessages    
    global flowStep

    if(("holaSimpleTest") in (texto.lower())):
        flowStep = 1
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
    elif(("hola" in (texto.lower()))and(flowStep==0)):
        flowStep = 1
        data = {
            "messaging_product": "whatsapp",    
            "recipient_type": "individual",
            "to": numero,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body":{
                    "text": chatbotFlowMessages[0][0]
                },
                "footer":{
                    "text": chatbotFlowMessages[0][1]
                },
                "action":{
                    "buttons":[
                        {
                            "type": "reply",
                            "reply":{
                                "id": chatbotFlowMessages[0][2][0],
                                "title": chatbotFlowMessages[0][2][1]
                            }
                        }
                    ]                    
                }                
            }
        }
        
    elif((check_text_in_flow(texto, chatbotFlowMessages, flowStep-1))and(flowStep==1)):
        flowStep = 2
        data ={
            "messaging_product": "whatsapp",
            "to": numero,
            "type": "interactive",
            "interactive":{
                "type" : "list",
                "body": {
                    "text": chatbotFlowMessages[1][0]
                },
                "footer": {
                    "text": chatbotFlowMessages[1][2]
                },
                "action":{
                    "button": chatbotFlowMessages[1][1],
                    "sections":[
                        {
                            "title": "",
                            "rows":[
                                {
                                    "id": chatbotFlowMessages[1][3][0],
                                    "title" : chatbotFlowMessages[1][3][1],
                                    "description": "Compra los mejores articulos de tecnologia"
                                },
                                {
                                    "id": chatbotFlowMessages[1][4][0],
                                    "title" : chatbotFlowMessages[1][4][1],
                                    "description": "Vende lo que ya no estes usando"
                                },
                                {
                                    "id": chatbotFlowMessages[1][5][0],
                                    "title" : chatbotFlowMessages[1][5][1],
                                    "description": "Vende lo que ya no estes usando"
                                },
                                {
                                    "id": chatbotFlowMessages[1][6][0],
                                    "title" : chatbotFlowMessages[1][6][1],
                                    "description": "Vende lo que ya no estes usando"
                                },
                                {
                                    "id": chatbotFlowMessages[1][7][0],
                                    "title" : chatbotFlowMessages[1][7][1],
                                    "description": "Vende lo que ya no estes usando"
                                }
                            ]
                        }
                    ]
                }
            }
        }

    elif((check_text_in_flow(texto, chatbotFlowMessages, 0))and(flowStep==2)):
        app.logger.debug("In Step 1")
        flowStep = 2
        data = {
            "messaging_product": "whatsapp",    
            "recipient_type": "individual",
            "to": numero,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body":{
                    "text": chatbotFlowMessages[1][0]
                },
                "footer":{
                    "text": chatbotFlowMessages[1][1]
                },
                "action":{
                    "buttons":[
                        {
                            "type": "reply",
                            "reply":{
                                "id": chatbotFlowMessages[1][2][0],
                                "title": chatbotFlowMessages[1][2][1]
                            }
                        },
                        {
                            "type": "reply",
                            "reply":{
                                "id": chatbotFlowMessages[1][3][0],
                                "title": chatbotFlowMessages[1][3][1]
                            }
                        },
                        {
                            "type": "reply",
                            "reply":{
                                "id": chatbotFlowMessages[1][4][0],
                                "title": chatbotFlowMessages[1][4][1]
                            }
                        }
                    ]                    
                }                
            }
        }
        
    elif((check_text_in_flow(texto, chatbotFlowMessages, flowStep-1))and(flowStep==2)):
        flowStep = 3
        data ={
            "messaging_product": "whatsapp",
            "to": numero,
            "type": "interactive",
            "interactive":{
                "type" : "list",
                "body": {
                    "text": chatbotFlowMessages[2][0]
                },
                "footer": {
                    "text": chatbotFlowMessages[2][2]
                },
                "action":{
                    "button": chatbotFlowMessages[2][1],
                    "sections":[
                        {
                            "title": "",
                            "rows":[
                                {
                                    "id": chatbotFlowMessages[2][3][0],
                                    "title" : chatbotFlowMessages[2][3][1],
                                    "description": "Compra los mejores articulos de tecnologia"
                                },
                                {
                                    "id": chatbotFlowMessages[2][4][0],
                                    "title" : chatbotFlowMessages[2][4][1],
                                    "description": "Vende lo que ya no estes usando"
                                },
                                {
                                    "id": chatbotFlowMessages[2][5][0],
                                    "title" : chatbotFlowMessages[2][5][1],
                                    "description": "Vende lo que ya no estes usando"
                                },
                                {
                                    "id": chatbotFlowMessages[2][6][0],
                                    "title" : chatbotFlowMessages[2][6][1],
                                    "description": "Vende lo que ya no estes usando"
                                },
                                {
                                    "id": chatbotFlowMessages[2][7][0],
                                    "title" : chatbotFlowMessages[2][7][1],
                                    "description": "Vende lo que ya no estes usando"
                                }
                            ]
                        }
                    ]
                }
            }
        }

    else:
        app.logger.debug(texto)
        app.logger.debug((check_text_in_flow(texto, chatbotFlowMessages, 0)))
        app.logger.debug(flowStep)
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
    token = "EAAWXJp8ZCZCyABOZCQ4ZAiyhAhs7o88ZAWcOep8HnXU5IisqMGqOdDB9CJwmuSuOo5J3fDNTIrYUouMDtxH1BO3oPrMPHQpmM3HaJtOrSITEQTkf0XjDKvj4UpPL1gtsGZAlZBbTd5nBDBWofjJPzWxGSkbLbD7pwq2ZCwGS3yXpwZBhfP0kaAvQD3cvZB2FbgttAf7ShN5m0dLPtyp8OQysXbPdsvLgZDZD"
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