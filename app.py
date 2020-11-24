import json

from flask import Flask, render_template

import os
import glob

files = glob.glob('./data/raw/*')
for f in files:
    os.remove(f)

port = int(os.environ.get("PORT", 5000))    
app = Flask(__name__)


@app.route("/")
def index():
    try: 
        with open('./data/processed/nodes.json') as f:
            nodes = json.load(f)
        with open('./data/processed/edges.json') as f:
            edges = json.load(f)
    except FileNotFoundError:
        nodes = []
        edges = []
    
    return render_template("test.html", nodes=nodes, edges=edges)


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=port,
        debug=True)
    
