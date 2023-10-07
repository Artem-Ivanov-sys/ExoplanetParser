import requests, lxml
from bs4 import BeautifulSoup
from datetime import date
import json

class ExoplanetParsing:
    '''exoplanet.eu parser'''

    def initialize_constants(self):
        self.MEarth = 5.972e24          #kg
        self.REarth = 6.371e6           #m

        self.planet_parameters = {
            "max_temperature": 500,     #kelvin
            "max_density": 3000,        #kg/m3
            "max_mass": 5,              #mearth
            "max_radius": 2.05,         #rearth
            "semi-major_axis": {        #au
                "min": 0.05,
                "max": 1.5
            },
            "max_e": 0.21
        }
        self.star_parameters = {
            "class": "GKMF"
        }

        self.ro = lambda M, R: M*self.MEarth / (4/3 * (R*self.REarth)**3)
    
    def connect_to_database(self, data = {"sEcho": 1, "iDisplayStart": 0, "iDisplayLength": 999999, "sSearch": "",
                            "iSortCol_0": 9, "sSortDir_0": "desc", "mass_unit": "mearth", "radius_unit": "rearth",
                            "status_1": True, "status_2": True, "status_4": True}):
        self.url = "http://exoplanet.eu/catalog/json/"
        self.req = requests.post(self.url, data)
        print(f"\n{'Статус запиту:':<40s} {str(self.req):>20s}")

        self.data = json.loads(self.req.content)
        self.out_list = [0]
        self.reserve_list = [0]
        print(f"{'Кількість отриманих екзопланет:':<40s} {len(self.data['aaData']):>20}\n")
    
    def exoplanets_proceed(self, verbose = False):
        planet_parameters = self.planet_parameters
        star_parameters = self.star_parameters
        processed = 0
        count = len(self.data['aaData'])
        for planet in self.data["aaData"]:
            if verbose:                 #may slow down performance
                processed += 1
                fraction = processed * 50 // count
                print(f"\r[{'='*fraction}{'>' if processed<count else ''}{'.'*(49-fraction)}] - {processed} / {count}", end="")

            if None in [planet[1], planet[2], planet[4], planet[5]]:
                continue
            if planet[1]<planet_parameters["max_mass"] and planet[2]<planet_parameters["max_radius"] \
                    and self.ro(planet[1], planet[2])>planet_parameters["max_density"] \
                    and planet_parameters["semi-major_axis"]["max"]>planet[4]>planet_parameters["semi-major_axis"]["min"] \
                    and planet[5]<planet_parameters["max_e"]:
                link = BeautifulSoup(planet[0], "lxml")
                planet_page = BeautifulSoup(requests.get(link.a["href"]).content, "lxml")
                star_type = planet_page.find("td", id="star_0_stars__spec_type_0").text
                planet_temperature = planet_page.find("td", id="planet_temp_calculated_0").text
                if star_type in ["-", ""] or len(planet_temperature)<2:
                    if len(planet_temperature)<2 \
                            or float(planet_temperature[:planet_temperature.index(" ")])<planet_parameters["max_temperature"]:
                        self.reserve_list[0] += 1
                        self.out_list.append("|".join(map(str, [self.out_list[0], link.text, planet[1], planet[2], 
                                                                planet[3], planet[4], planet[5], planet_temperature])))
                
                elif star_type[0].upper() in star_parameters["class"] \
                        and float(planet_temperature[:planet_temperature.index(" ")])<planet_parameters["max_temperature"]:
                    self.out_list[0] += 1
                    self.out_list.append("|".join(map(str, [self.out_list[0], link.text, planet[1], planet[2], 
                                                            planet[3], planet[4], planet[5], planet_temperature])))
    
    def export_result(self, file_path = f"logs/log_{date.today()}.txt"):
        with open(file_path, "w", encoding="utf-8") as file:
            out_listTxt = "\n".join(self.out_list[1:])
            reserve_listTxt = "\n".join(self.reserve_list[1:])
            file.write(f"<Candidates: {self.out_list[0]}>\n\n"+out_listTxt+
                    f"\n\n<Reserves: {self.reserve_list[0]}>\n\n"+reserve_listTxt)
        print(f"\n{file_path}")


if __name__ == "__main__":
    parser = ExoplanetParsing()
    parser.initialize_constants()
    parser.connect_to_database()
    parser.exoplanets_proceed(verbose=True)
    parser.export_result()

