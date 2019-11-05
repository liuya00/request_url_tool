from flask import Flask, render_template
from flask_bootstrap import Bootstrap
import multiprocessing as mp
import socket_server

app = Flask(__name__)
bootstrap = Bootstrap(app)


@app.route('/')
def portal():
    process = mp.Process(target=run_socket_server)
    process.start()
    return render_template('request_page.html')


def run_socket_server():
    socket_server.main()


if __name__ == '__main__':
    app.run(debug=True)