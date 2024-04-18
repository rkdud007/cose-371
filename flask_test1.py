from flask import Flask

app = Flask(__name__)

@app.route('/')
def main():
    return "Hello World!"

# @app.route('/bye')
# def bye():
#     return "Goodbye World!"

if __name__ == '__main__':
    app.run()

