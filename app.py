from flask import Flask, jsonify, request
import requests

app = Flask(__name__)

@app.route('/enviar-post', methods=['POST'])
def enviar_post():
    url_destino = 'https://example.com/api'

    datos = {
        'clave1': 'valor1',
        'clave2': 'valor2'
    }

    response = requests.post(url_destino, json=datos)
    if response.status_code == 200:
        return jsonify(response.json()), 200
    else:
        return jsonify({'error': 'Error al enviar la solicitud POST', 'código_estado': response.status_code}), response.status_code

if __name__ == '__main__':
    app.run(debug=True)
