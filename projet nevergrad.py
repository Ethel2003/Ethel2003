# Copyright (c) Meta Platforms, Inc. and affiliates. All Rights Reserved.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

"""
Approximate crop Simulation
Based on
https://raw.githubusercontent.com/purdue-orbital/pcse-simulation/master/Simulation2.py
"""


from pathlib import Path
import urllib.request  # Necessary for people who will uncomment the part using data under EUPL license.
import numpy as np
import nevergrad as ng
from ..base import ArrayExperimentFunction
import os
import pandas as pd
import yaml
from pcse.fileinput import CABOFileReader, YAMLCropDataProvider
from pcse.models import Wofost72_WLP_FD
from pcse.db import NASAPowerWeatherDataProvider
from pcse.util import WOFOST72SiteDataProvider
from pcse.base import ParameterProvider


# pylint: disable=too-many-locals,too-many-statements
#un fichier .cab est un fichier Windows Cabinet, précisement un fichier compressé stockant des données liées à diverses installations Windows pouvant impliquer des pilotes des périphériques ou même des fichiers systèmes.

class Irrigation(ArrayExperimentFunction):
    variant_choice = {}
    def __init__(self, symmetry: int) -> None:
        data_dir = Path(__file__).with_name("data")#on crée un objet path portant le nom data
        #urllib.request.urlretrieve(
        #    "https://raw.githubusercontent.com/ajwdewit/pcse_notebooks/master/data/soil/ec3.soil",
        #    str(data_dir) + "/soil/ec3.soil",
        #)
        self.soil = CABOFileReader(os.path.join(data_dir, "soil", "ec3.soil"))#avec l'instruction os.path.join(data_dir, "soil", "ec3.soil") on a voulu concaténer le chemin des fichiers data_dir,soil et ec3.soil.Avec cette instrusction "CABOFileReader(os.path.join(data_dir, "soil", "ec3.soil"))", on veut lire les informations dans le fichier dont le chemin d'accès lui est passé en argument. c'est un fichier CABO. En gros, avec cette ligne de code on crée un attribut nommé soil qui a en son sein les informations issues du fichier du type CABO.
        param = ng.p.Array(shape=(8,), lower=(0.0), upper=(1.0)).set_name("irrigation8")#avec cette instruction ng.p.Array(shape=(8,), lower=(0.0), upper=(1.0) on définit les paramètres sur lesquels l'optimisation doit se faire. ce fut le module nevergrad.p.Array de l'optimiseur Nervergrad qui a été utilisé.l'instruction .set_name() on définit le nom du paramètre 
    
        super().__init__(self.leaf_area_index, parametrization=param, symmetry=symmetry) #on utilise cette instruction pour faire appel au constructeur de la classe parent de la  classe parent de Irrigation, qu'on initialise avec les paramètres self.leaf_area_index, param qui est l'attribut permettant de faire l'optimisation et symmetry.
        
        if os.environ.get("CIRCLECI", False):#os.environ.get() permet de récupérer la valeur de la variable d'environnement "CIRCLECI"
            raise ng.errors.UnsupportedExperiment("No HTTP request in CircleCI")# les lignes d'instruction 44 et 45 traduisent ceci: si la valeur de la variable d'environnement est fausse, l'interpréteur doit afficher l'erreur  "No HTTP request in CircleCI"
        known_longitudes = {'Saint-Leger-Bridereix': 1.5887348, 'Dun-Le-Palestel': 1.6641173, 'Kolkata':
        88.35769124388872, 'Antananarivo': 47.5255809, 'Santiago': -70.6504502, 'Lome': 1.215829, 'Cairo': 31.2357257,
        'Ouagadougou': -1.5270944, 'Yamoussoukro': -5.273263, 'Yaounde': 11.5213344, 'Kiev': 30.5241361}#définition d'un dictionnaire prenant en compte les informations sur la longitude de certaines villes.
        known_latitudes = {'Saint-Leger-Bridereix': 46.2861759, 'Dun-Le-Palestel': 46.3052049, 'Kolkata': 22.5414185,
        'Antananarivo': -18.9100122, 'Santiago': -33.4377756, 'Lome': 6.130419, 'Cairo': 30.0443879, 'Ouagadougou':
        12.3681873, 'Yamoussoukro': 6.809107, 'Yaounde': 3.8689867, 'Kiev': 50.4500336}#définition d'un dictionnaire contenant les informations sur la latitude de certaines villes.
        self.cropd = YAMLCropDataProvider()# définition de l'attribut cropd qu'on initialise avec YAMLCropDataProvider
        for k in range(1000):# pour une valeur de k comprise entre 0 et 1000, les instructions suivantes doivent être suivis
            if symmetry in self.variant_choice and k < self.variant_choice[symmetry]:#si l'attribut symmetry est dans l'attribut variant.choice et que la valeur de k est inférieur à l'élement variant_choice[symmetry] suivre le reste des instructions dans la boucle for.
                continue
            self.address = np.random.RandomState(symmetry+3*k).choice(
                [
                    "Saint-Leger-Bridereix",
                    "Dun-Le-Palestel",
                    "Kolkata",
                    "Antananarivo",
                    "Santiago",
                    "Lome",
                    "Cairo",
                    "Ouagadougou",
                    "Yamoussoukro",
                    "Yaounde",
                    "Kiev",
                ]
            )#déclaration de l'attribut adress dont la valeur sera généré avec la fonction np.random.RandomState().choice(). Le choix étant opéré dans le tableau de ville fourni en argument
            if self.address in known_latitudes and self.address in known_longitudes:#si l'attibut address à se trouve dans les dictionnaires known_latitudes et known_longitudes,suivre l'instruction suivante
                self.weatherdataprovider = NASAPowerWeatherDataProvider(latitude=known_latitudes[self.address], longitude=known_longitudes[self.address])# initialiser l'attribut weatherdataprovider qui du type de la classe NASAPowerWeatherDataProvider avec les informations sur sa latitude et sa longitude en utilisant les dictionnaires known_latitudes et known_longitudes
            else: #Autrement on suit les instructions suivantes         
                assert False
                from geopy.geocoders import Nominatim #importer le module Nominatim de geopy.geocoders
                geolocator = Nominatim(user_agent="NG/PCSE")#on initialise geolocator avec Nominatim(user_agent="NG/PCSE")
                self.location = geolocator.geocode(self.address)# on initialise ensuite l'attribut location avec la fonction geolocator.geocode en lui fournissant comme argument l'attribut adresse
                self.weatherdataprovider = NASAPowerWeatherDataProvider(
                    latitude=self.location.latitude, longitude=self.location.longitude
                )#on initialise alors l'attribut weatherdataprovider
            self.set_data(symmetry, k)#
            v = [self.leaf_area_index(np.random.rand(8)) for _ in range(5)]
            if min(v) != max(v):
                break
            self.variant_choice[symmetry] = k
        print(f"we work on {self.cropname} with variety {self.cropvariety} in {self.address}.")

#set_data est une méthode de la classe qui prend deux paramètres qui sont des entiers. au sein de cette méthode, la liste crop_types est crée et les attributs crop_name et crop_variety sont initialisés
    def set_data(self, symmetry: int, k: int):
        crop_types = [c for c in self.cropd.crop_types if "obacco" not in c]
        self.cropname = np.random.RandomState(symmetry+3*k+1).choice(crop_types)
        self.cropvariety = np.random.RandomState(symmetry+3*k+2).choice(list(self.cropd.get_crops_varieties()[self.cropname])
        )
        # We check if the problem is challenging.
        #print(f"testing {symmetry}: {k} {self.address} {self.cropvariety}")
        site = WOFOST72SiteDataProvider(WAV=100, CO2=360) #création de l'objet site, une instance de la classe WOFOST72SiteDataProvider.
        self.parameterprovider = ParameterProvider(soildata=self.soil, cropdata=self.cropd, sitedata=site)# création de l'attribut ParameterProvider qui est une instance de la classe ParameterProvider. Cette classe fournit une interface de type dictionnaire sur tous les ensembles de paramètres (culture, sol, site). Il agit comme un ChainMap avec quelques fonctionnalités supplémentaires.
        #un ChainMap est un conteneur de Python qui permet d'encapsuler plusieurs dictionnaires en un seul

#la classe WOFOST72SiteDataProvider() fournit des données de site pour WOFOST 7.2.Les paramètres spécifiques au site pour WOFOST 7.2 peuvent être fournis via ce fournisseur de données ainsi que via un dictionnaire python normal. Le seul but de la mise en œuvre de ce fournisseur de données est que les paramètres du site pour WOFOST soient documentés, vérifiés et que des valeurs par défaut raisonnables soient données.

    def leaf_area_index(self, x: np.ndarray):#cette méthode permet de calculer l'indice de surface foliaire. Elle prend en argument un tableau a une dimension.
        d0 = int(1.01 + 29.98 * x[0])
        d1 = int(1.01 + 30.98 * x[1])
        d2 = int(1.01 + 30.98 * x[2])
        d3 = int(1.01 + 29.98 * x[3])
        a0 = 15.0 * x[4] / (x[4] + x[5] + x[6] + x[7])
        a1 = 15.0 * x[5] / (x[4] + x[5] + x[6] + x[7])
        a2 = 15.0 * x[6] / (x[4] + x[5] + x[6] + x[7])
        a3 = 15.0 * x[7] / (x[4] + x[5] + x[6] + x[7])

        yaml_agro = f"""
        - 2006-01-01:
            CropCalendar:
                crop_name: {self.cropname}
                variety_name: {self.cropvariety}
                crop_start_date: 2006-03-31
                crop_start_type: emergence
                crop_end_date: 2006-10-20
                crop_end_type: harvest
                max_duration: 300
            TimedEvents:
            -   event_signal: irrigate
                name: Irrigation application table
                comment: All irrigation amounts in cm
                events_table:
                - 2006-06-{d0:02}: {{amount: {a0}, efficiency: 0.7}}
                - 2006-07-{d1:02}: {{amount: {a1}, efficiency: 0.7}}
                - 2006-08-{d2:02}: {{amount: {a2}, efficiency: 0.7}}
                - 2006-09-{d3:02}: {{amount: {a3}, efficiency: 0.7}}
            StateEvents: null
        """# déclaration et initialisation de la varaiable yaml.agro
        try: # executer les instructions suivantes et si une erreur se pose,arrêter l'exécution du bloc d'instruction et executer l'instruction dans le bloc de except.
            agromanagement = yaml.safe_load(yaml_agro)#déclaration et initialisation de la variable agromanagement avec la fonction safe_load qui prend en argument yaml_gro
            wofost = Wofost72_WLP_FD(self.parameterprovider, self.weatherdataprovider, agromanagement)#déclaration de la variable wofost qui est une instance de Wofost72_WLP_FD. la classe Wofost72_WLP_FD est la classe commode pour exécuter la production limitée en eau WOFOST7.2.
            wofost.run_till_terminate()# éxecution de la methode run_till_terminate() sur l'objet wofost.La methode run_till_terminate() exécute le système jusqu'à ce qu'un signal de fin soit envoyé.
        except Exception as e:
            return float("inf")
            #assert (
            #    False
            #), f"Problem!\n Dates: {d0} {d1} {d2} {d3},\n amounts: {a0}, {a1}, {a2}, {a3}\n  ({e}).\n"
            #raise e

        output = wofost.get_output()# Déclaration et initialisation de la variable output avec wofost.get_output(). la méthode get.output() appelée sur l'objet wofost Renvoie les variables qui ont été stockées pendant la simulation.
#Si aucune sortie n'est stockée, une liste vide est renvoyée. Sinon, la sortie est renvoyée sous la forme d'une liste de dictionnaires dans l'ordre chronologique. Chaque dictionnaire est un ensemble de variables de modèle stockées pour une certaine date.
        df = pd.DataFrame(output).set_index("day")# déclaration de la variable df qui est initialisé avec la variable output convertit en dataframe dont l'index est la colonne day
        df.tail()# donne le nombre de lignes de la dataframe

        return -sum([float(o["LAI"]) for o in output if o["LAI"] is not None])