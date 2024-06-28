"""
Modulo de configuracao do projeto

As variaveis de ambiente serao definidas aqui e repassadas para o codigo
A maior parte da configuracao dos modulos sera feita aqui
"""

import datetime
import os

import dotenv
import pandas as pd
from dateutil.relativedelta import relativedelta

dotenv.load_dotenv()

TODAY = os.getenv("TODAY", datetime.date.today().strftime("%Y-%m-%d"))
YESTERDAY = (pd.to_datetime(TODAY) - relativedelta(days=1)).strftime("%Y-%m-%d")

BASE_FOLDER = "abfs://testmlopaes.dfs.core.windows.net/testing"
RAW_FOLDER = f"{BASE_FOLDER}/raw"
INPUT_FOLDER = f"{BASE_FOLDER}/input"
TRUSTED_FOLDER = f"{BASE_FOLDER}/trusted"
REFINED_FOLDER = f"{BASE_FOLDER}/refined"
