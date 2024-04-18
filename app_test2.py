from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/')
def main():
    return render_template("main.html")

@app.route('/register', methods=['post'])
def register():
    id = request.form["id"]
    password = request.form["password"]
    send = request.form["send"]

    return id + " " + password + " " + send

if __name__ == '__main__':
    app.run()

