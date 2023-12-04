import json
import urllib.parse as urlparse
from datetime import date, datetime

from scrapy import Request

from gazette.items import Gazette
from gazette.spiders.base import BaseGazetteSpider


class SpRibeiraoPretoSpider(BaseGazetteSpider):
    TERRITORY_ID = "3543402"
    name = "sp_ribeirao_preto"
    allowed_domains = ["cespro.com.br"]
    start_date = date(1973, 1, 23)
    start_date_str = start_date.strftime("%d/%m/%Y")
    # end_date = datetime.today().date()
    ID = "9314"

    def make_request(self, page):
        end_date_str = self.end_date.strftime("%d/%m/%Y")
        base_url = "https://cespro.com.br/_data/api.php?"
        header = {"Content-Type": "application/json"}
        params = {
            "busca": "t",
            "nPage": page,
            "cdMunicipio": self.ID,
            "dataInicial": self.start_date_str,
            "dataFinal": end_date_str,
            "operacao": "content-diario-oficial",
        }
        payload = {"ID": self.ID, "page": page}
        query_str = urlparse.urlencode(params)
        url = base_url + query_str

        yield Request(url, method="POST", body=json.dumps(payload), headers=header)

    def start_requests(self):
        self.make_request(1)

    def parse(self, response):
        data = response.json()

        for item in data["dados_diario_oficial_pesquisa"]:
            yield Gazette(
                date=datetime.strptime(item["dt_diario_oficial"], "%Y-%m-%d").date(),
                edition_number=item["nr_diario_oficial"],
                is_extra_edition=False,
                file_urls=[item.get("tx_url_file") + "&dl=1"],
            )

            found_legislative = False

            for ato in item["dados_diario_oficial_diploma_pesquisa"]:
                # cd_orgao '133' equivale ao cód. do PODER LEGISLATIVO
                if ato["cd_orgao"] == "133":
                    found_legislative = True
                    break

            yield Gazette(
                power="executive_legislative"
                if found_legislative is True
                else "executive",
            )

        last_page = [
            i for i in data["dados_paginacao"] if data["dados_paginacao"][i] == ">>"
        ]
        page_end = int(last_page[0])
        if page_end > 1:
            for page in range(2, page_end + 1):
                self.make_request(page)
