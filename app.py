from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def holaMundo():
    return (render_template("holaFlask.html"))


if __name__ == '__main__':
    app.run(debug=True)