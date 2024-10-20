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
    
    app.logger.debug(texto)
    app.logger.debug((check_text_in_flow(texto, chatbotFlowMessages, 0)))
    app.logger.debug(flowStep)


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
        
    elif "lista" in texto:
        data ={
            "messaging_product": "whatsapp",
            "to": numero,
            "type": "interactive",
            "interactive":{
                "type" : "list",
                "body": {
                    "text": "Selecciona Alguna Opción"
                },
                "footer": {
                    "text": "Selecciona una de las opciones para poder ayudarte"
                },
                "action":{
                    "button":"Ver Opciones",
                    "sections":[
                        {
                            "title":"Compra y Venta",
                            "rows":[
                                {
                                    "id":"btncompra",
                                    "title" : "Comprar",
                                    "description": "Compra los mejores articulos de tecnologia"
                                },
                                {
                                    "id":"btnvender",
                                    "title" : "Vender",
                                    "description": "Vende lo que ya no estes usando"
                                }
                            ]
                        },{
                            "title":"Distribución y Entrega",
                            "rows":[
                                {
                                    "id":"btndireccion",
                                    "title" : "Local",
                                    "description": "Puedes visitar nuestro local."
                                },
                                {
                                    "id":"btnentrega",
                                    "title" : "Entrega",
                                    "description": "La entrega se realiza todos los dias."
                                }
                            ]
                        }
                    ]
                }
            }
        }
    elif((check_text_in_flow(texto, chatbotFlowMessages, 0))and(flowStep==1)):
        app.logger.debug("In Step 1 List")
        flowStep = 2
        data = {
            "messaging_product": "whatsapp",    
            "to": numero,
            "type": "interactive",
            "interactive": {
                "type": "list",
                "body":{
                    "text": chatbotFlowMessages[1][0]
                },
                "footer":{
                    "text": chatbotFlowMessages[1][2]
                },
                "action":{
                    "button": chatbotFlowMessages[1][1],
                    "sections":[
                        {
                            "title": chatbotFlowMessages[1][2],
                            "rows": [
                                {
                                    "id": chatbotFlowMessages[1][3][0],
                                    "title": chatbotFlowMessages[1][3][1],
                                    "descripcion": "Desc default"
                                },
                                {
                                    "id": chatbotFlowMessages[1][4][0],
                                    "title": chatbotFlowMessages[1][4][1],
                                    "descripcion": "Desc default"
                                },
                                {
                                    "id": chatbotFlowMessages[1][5][0],
                                    "title": chatbotFlowMessages[1][5][1],
                                    "descripcion": "Desc default"
                                },
                                {
                                    "id": chatbotFlowMessages[1][6][0],
                                    "title": chatbotFlowMessages[1][6][1],
                                    "descripcion": "Desc default"
                                },
                                {
                                    "id": chatbotFlowMessages[1][7][0],
                                    "title": chatbotFlowMessages[1][7][1],
                                    "descripcion": "Desc default"
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
    token = "EAAWXJp8ZCZCyABOzUocEuJg4jnI4GD5PmSIZAz82FkSGEKW7c5g3Vg8Kc9qicq6gZArs7GB6NeI30Np52OgZAoIA3n1YmideKbCz5ZCyrdk38WqDevt1FZChZBuVWwIkFk56311nztFnyFyGc6TXJlEHmxcC1hISoc9n12EUrwowGTeAgdgVeRamcfklUnPPjC9mm2oM55zL8a8x5mJovly9HWEG"
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