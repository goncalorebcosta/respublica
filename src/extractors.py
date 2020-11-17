import json
import re
from unidecode import unidecode
import pandas as pd

class BiographyExtractor:
    def __init__(self):
        self.json_path = "./data/raw/biography.json"
        self.nodes = []
        self.nodes_path = "./data/processed/nodes.json"
        self.edges = []
        self.edges_path = "./data/processed/edges.json"
        with open(self.json_path) as json_file:
            self.data = json.load(json_file)
        self.job_map = pd \
            .read_csv('./data/profissoes.csv',
                    sep=';', 
                    index_col=0,
                    engine='python',
                    encoding='utf-8') \
            .to_dict(orient='index')

    def _create_edge(self, src, dst, edge_type, **kwargs):
        self.edges.append(
            {"source": src, "target": dst, "type": edge_type, "info": kwargs}
        )

    def _append_other_node_and_edge(self, tag, v, **kwargs):

        entry = {"type": tag, "info": {"value": v}}
        if entry not in self.nodes:
            self.nodes.append(entry)
        self._create_edge(self._congress_id, v, tag, **kwargs)

    def _create_other_node_and_edge(self, node_type):
        value = self._biography[node_type].strip()
        if node_type == "profissao":
            value = unidecode(value.lower())
            try:
                value = self.job_map[value]['value']
            except KeyError:
                pass
        if node_type == "data_de_nascimento":
            value = value.split("-")[0][:3] + "0s"
        self._append_other_node_and_edge(node_type, value)

    @staticmethod
    def _process_comission_node(value):
        node = value.split("[")[0].strip()
        try:
            match = re.search(r".*?\[(.*)].*", value)
            edge_info = match.group(1)
        except AttributeError:
            edge_info = "membro"
        return node, edge_info

    def _create_comission_nodes_edges(self):
        tag = "comissoes_parlamentares_a_que_pertence"
        value = self._biography[tag]
        if isinstance(value, list):
            for v in value:
                node, edge_info = self._process_comission_node(v)
                self._append_other_node_and_edge(tag, node, **{"edge_info": edge_info})
        else:
            node, edge_info = self._process_comission_node(value)
            self._append_other_node_and_edge(tag, node, **{"edge_info": edge_info})

    def _save(self):
        with open(self.nodes_path, "w") as outfile:
            json.dump(self.nodes, outfile)
        with open(self.edges_path, "w") as outfile:
            json.dump(self.edges, outfile)

    def run(self):
        for entry in self.data:
            # Extract data from entries
            self._congress_id = list(entry.keys())[0]
            self._biography = list(entry.values())[0]
            # Create main/name nodes
            self.nodes.append(
                {
                    "type": "pessoa",
                    "info": {
                        "cpid": self._congress_id,
                        "nome_completo": self._biography["nome_completo"],
                        "iniciais": "".join(
                            [
                                name[0]
                                for name in self._biography["nome_completo"].split(" ")
                            ]
                        ),
                        "partido": self._biography["partido"],
                        "profissao": self._biography["profissao"],
                        "data_de_nascimento": self._biography["data_de_nascimento"],
                    },
                }
            )
            # Create party nodes
            self._create_other_node_and_edge("partido")
            # Create profession nodes
            self._create_other_node_and_edge("profissao")
            # Create comission nodes
            # try clause needed because some congress people do not belong to any?
            try:
                self._create_comission_nodes_edges()
            except KeyError:
                pass
            # Create birth decade nodes
            self._create_other_node_and_edge("data_de_nascimento")

            self._save()
