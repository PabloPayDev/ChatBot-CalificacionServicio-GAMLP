from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///metapython.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha_y_hora = db.Column(db.DateTime, default=datetime.utcnow)
    texto = db.Column(db.Text)

with app.app_context():
    db.create_all()


@app.route('/')
def index():
    registros = Log.query.all()
    registros_ordenados = sortByDate(registros)
    return (render_template("index.html", registros = registros_ordenados))

mensajes_log = []
def addMessageLog(texto):
    mensajes_log.append(texto)
    newRegister = Log(texto=texto)
    db.session.add(newRegister)
    db.session.commit()

def sortByDate(register):
    return sorted(register, key=lambda x: x.fecha_y_hora, reverse=True)

#addMessageLog(json.dumps("TestText"))

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

    if(challenge and token==TOKEN):
        return challenge
    else:
        return jsonify({'error':'Token Invalido'}),401

def recibir_mensaje(req):
    req = request.get_json()
    addMessageLog(req)
    return jsonify({'message':'EVENT RECEIVED'})


if __name__ == '__main__':
    app.run(host='0.0.0.0',port=80,debug=True)