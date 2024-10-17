from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import http.client
import json

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///metapython.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

chatbotFlowMessages = [
    "Hola soy tu asistente virtual, porfavor responde a las siguientes pregutnas para calificar tu atencion en plataforma siendo un 1 muy malo y 5 muy bueno",
    "Como fue tu experiencia general en la atencion? \n \n1️⃣. Muy mala. \n2️⃣. Mala. \n3️⃣. Media. \n4️⃣. Buena. \n5️⃣. Muy buena.",
    "Default"
]

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
                if(tipo == "interactive"):
                    return 0
                if("text" in messages):
                    text = messages["text"]["body"]
                    numero = messages["from"]

                    addMessageLog(json.dumps(text))
                    addMessageLog(json.dumps(numero))

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
    token = "EAAWXJp8ZCZCyABO98FcF8mcjDtQh5IWfSbl0JrRgQMeXuYXxTOeMkHKk3pNcSjSP80ek6XKlISC7gNR2lWZClZAz78ySsT6al9OnfyZBsxZCgJzebEyweSQDs643HMbJ7Epifm9D1MuXtDeK3v12kaxsKausuU8zQ8OA4oD9iZA62Equb8VGtdu1WiEYFg1RXI6SyHYGviupG0zzOWrvmDNXLZBG"
    headers = {
        "Contect-Type": "application/json",
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