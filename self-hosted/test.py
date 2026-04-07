import os
import pymysql
from dotenv import load_dotenv

load_dotenv("./.env")

test = [
    {
        "name": "chiel",
        "age": 21
    }, {
        "name": "twan",
        "age": 21
    }
]
print(type(test[0]['name']))
