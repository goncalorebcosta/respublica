import scrapy
import re
from unidecode import unidecode


class BaseSpider(scrapy.Spider):

    def start_requests(self):
        urls = [
            "https://www.parlamento.pt/DeputadoGP/Paginas/Deputadoslista.aspx",
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parser)

    @staticmethod
    def _get_valid_congress_people_ids(response):
        return [
            re.search(r"\d+", cpid).group()
            for cpid in response.css("a.TextoRegular::attr(href)").getall()
            if "Biografia" in cpid
        ]
    
    @staticmethod
    def _xpath_parser(response, path, tag):
        try:
            _ = response.xpath(path + "/text()").get()
            if tag is not None:
                out = {tag: _}
            else:
                out = _
        except:
            out = "NA"
        return out


class BiographySpider(BaseSpider):
    name = 'biography'
    custom_settings = {
        "FEEDS": {
            f"./data/raw/{name}.json": {
                "format": "json", 
                "overwrite": 1
                }
            }
    }
    def parser(self, response):
        congress_people_ids = self._get_valid_congress_people_ids(response)

        for cpid in congress_people_ids:
            self.log("SCRAPING: {}".format(cpid))
            # Biography scrapping
            bio_url = "https://www.parlamento.pt/DeputadoGP/Paginas/Biografia.aspx?BID={}".format(
                cpid
            )
            self.log("START: RETRIEVING BIOGRAPHY")
            yield scrapy.Request(bio_url, callback=self._bio_parser,  meta={'id': cpid})
            self.log("END: RETRIEVING BIOGRAPHY")

    def _bio_parser(self, response):
        output = {}
        party = self._xpath_parser(
            response, 
            '//*[@id="ctl00_ctl52_g_5d3195b4_4c80_4cd5_a696_bf57c8c2232d_ctl00_lblPartido"]',
            "partido"
        )
        output.update(party)
        table = response.css("div.TextoRegular-Titulo")
        for entry in table:
            key = entry.css("div.TitulosBio.AlinhaL span::text").get()
            if key is None:
                continue
            key = key.lower().replace(" ", "_")
            key = unidecode(key)
            value = entry.css("span.TextoRegular::text").getall()
            if value == []:
                value = entry.css("div.TextoRegular.AlinhaL span::text").getall()
            if len(value) == 1:
                value = value[0]
            output.update({key: value})
        return {response.meta["id"]: output}


class InterestsSpider(BaseSpider):
    name = 'interests'
    custom_settings = {
        "FEEDS": {f"./data/raw/{name}.json": {"format": "json", "overwrite": True}}
    }
    def parser(self, response):
        congress_people_ids = self._get_valid_congress_people_ids(response)

        for cpid in congress_people_ids:

            interests_url = "https://www.parlamento.pt/DeputadoGP/Paginas/RegInteresses_v3.aspx?BID={}&leg=XIV".format(
                cpid
            )
            self.log("START: RETRIEVING INTERESTS")
            yield scrapy.Request(
                interests_url, callback=self._interests_parser, meta={"id": cpid}
            )
            self.log("END: RETRIEVING INTERESTS")

    def _interests_parser(self, response):
        output = {}
        # I - Identificação do declarante
        complete_name = self._xpath_parser(
            response,
            '//*[@id="ctl00_ctl52_g_ce699702_8741_4fef_a628_2a94385f6d5a_ctl00_lblNomeCompleto"]',
            tag="nome_completo",
        )
        main_activity = self._xpath_parser(
            response,
            '//*[@id="ctl00_ctl52_g_ce699702_8741_4fef_a628_2a94385f6d5a_ctl00_lblActividadePrincipal"]',
            tag="actividade_principal",
        )
        marital_status = self._xpath_parser(
            response,
            '//*[@id="ctl00_ctl52_g_ce699702_8741_4fef_a628_2a94385f6d5a_ctl00_lblEstadoCivil"]',
            tag="estado_civil",
        )
        spouse_name = self._xpath_parser(
            response,
            '//*[@id="ctl00_ctl52_g_ce699702_8741_4fef_a628_2a94385f6d5a_ctl00_lblNomeConjuge"]',
            tag="nome_conjuge",
        )
        property_scheme = self._xpath_parser(
            response,
            '//*[@id="ctl00_ctl52_g_ce699702_8741_4fef_a628_2a94385f6d5a_ctl00_lblRegimeBens"]',
            tag="regime_bens",
        )
        output["I"] = {
            **complete_name,
            **main_activity,
            **marital_status,
            **spouse_name,
            **property_scheme,
        }

        # II - Cargo/Função
        position = self._xpath_parser(
            response,
            '//*[@id="ctl00_ctl52_g_ce699702_8741_4fef_a628_2a94385f6d5a_ctl00_lblCargo"]',
            tag="cargo",
        )
        position_date = self._xpath_parser(
            response,
            '//*[@id="ctl00_ctl52_g_ce699702_8741_4fef_a628_2a94385f6d5a_ctl00_lblAnoCargo"]',
            tag="cargo_data",
        )
        output["II"] = {**position, **position_date}

        # III - Dados Relativos a cargos/funções/atividades
        output["III"] = {}
        ### Últimos três anos
        third = response.xpath(
            '//*[@id="ctl00_ctl52_g_ce699702_8741_4fef_a628_2a94385f6d5a_ctl00_pnlActividades"]/div[not(@*)]'
        )
        job_dict = {}
        last_three_year_jobs = {}
        job_count = 0
        for entry in third:
            key = entry.css("div.TextoRegular-Titulo::text").get()
            if key is None:
                continue
            key = key.strip()
            key = key.lower().replace(" ", "_")
            key = unidecode(key)
            value = entry.css("span.TextoRegular::text").get()
            # if value is None:
            #    continue
            job_dict.update({key: value})
            if key == "fim":
                last_three_year_jobs.update({(job_count): job_dict})
                job_count = job_count + 1
                job_dict = {}
        output["III"]["ultimos_tres_anos"] = last_three_year_jobs

        ### Acumulação com cargo político/alto cargo público
        acumulacao_cargos_actividade = response.xpath(
            '//*[@id="ctl00_ctl52_g_ce699702_8741_4fef_a628_2a94385f6d5a_ctl00_rptActividades_acu_ctl00_lblActividade"]/text()'
        ).getall()
        acumulacao_cargos_entidade = response.xpath(
            '//*[@id="ctl00_ctl52_g_ce699702_8741_4fef_a628_2a94385f6d5a_ctl00_rptActividades_acu_ctl00_lblEntidade"]/text()'
        ).getall()
        acumulacao_cargos_inicio = response.xpath(
            '//*[@id="ctl00_ctl52_g_ce699702_8741_4fef_a628_2a94385f6d5a_ctl00_rptActividades_acu_ctl00_lblDataInicio"]/text()'
        ).getall()
        acumulacao_cargos_fim = response.xpath(
            '//*[@id="ctl00_ctl52_g_ce699702_8741_4fef_a628_2a94385f6d5a_ctl00_rptActividades_acu_ctl00_lblDataFim"]/text()'
        ).getall()

        output["III"]["acumulacao_cargos"] = [
            {i: {"actividade": job, "entidade": entity, "inicio": start, "fim": end}}
            for i, (job, entity, start, end) in enumerate(
                zip(
                    acumulacao_cargos_actividade,
                    acumulacao_cargos_entidade,
                    acumulacao_cargos_inicio,
                    acumulacao_cargos_fim,
                )
            )
        ]

        ### Até três anos após cessação de funções
        actividade_tres_anos = response.xpath(
            '//*[@id="ctl00_ctl52_g_ce699702_8741_4fef_a628_2a94385f6d5a_ctl00_pnlNoActividades_3anos"]/div/span/text()'
        ).getall()
        output["III"]["actividades_tres_anos"] = actividade_tres_anos

        # IV - Cargos sociais
        social = self._xpath_parser(
            response,
            '//*[@id="ctl00_ctl52_g_ce699702_8741_4fef_a628_2a94385f6d5a_ctl00_pnlNoCargosSociais"]',
            tag="IV",
        )
        if social is not None:
            # TO DO
            pass
        # V - Apoios ou benefícios
        apoios = self._xpath_parser(
            response,
            '//*[@id="ctl00_ctl52_g_ce699702_8741_4fef_a628_2a94385f6d5a_ctl00_lblApoiosBeneficios"]',
            tag="V",
        )
        # VI - Serviços prestados
        servicos = self._xpath_parser(
            response,
            '//*[@id="ctl00_ctl52_g_ce699702_8741_4fef_a628_2a94385f6d5a_ctl00_lblServicosPrestados"]',
            tag="VI",
        )
        # VII - Sociedades
        sociedades = self._xpath_parser(
            response,
            '//*[@id="ctl00_ctl52_g_ce699702_8741_4fef_a628_2a94385f6d5a_ctl00_pnlNoSociedades"]/div/span',
            tag="VII",
        )
        # VIII - Outras situações
        outras = self._xpath_parser(
            response,
            '//*[@id="ctl00_ctl52_g_ce699702_8741_4fef_a628_2a94385f6d5a_ctl00_lblOutrasSituacoes"]',
            tag="VIII",
        )
        # IX - Declaração sobre exclusividade
        exclusividade = self._xpath_parser(
            response,
            '//*[@id="ctl00_ctl52_g_ce699702_8741_4fef_a628_2a94385f6d5a_ctl00_lblregmandado"]',
            tag="IX",
        )

        output.update({**social, **apoios, **servicos, **sociedades, **outras, **exclusividade})
        return {response.meta["id"]: output}

