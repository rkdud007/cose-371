from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def main():
    return render_template("main.html")

# @app.route('/register', methods=['post'])
# def register():
#     return "register"

if __name__ == '__main__':
    app.run()
