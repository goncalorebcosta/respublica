import json

from flask import Flask, render_template

app = Flask(__name__)
with open('./data/processed/nodes.json') as f:
    nodes = json.load(f)
with open('./data/processed/edges.json') as f:
    edges = json.load(f)
print(set([n['info']['value'] for n in nodes if n['type'] == 'partido']))
print(set([n['info']['value'] for n in nodes if n['type'] == 'data_de_nascimento']))
@app.route("/")
def index():

    
    return render_template("test.html", nodes=nodes, edges=edges)

    


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True)