import yaml
import os
from database import *

locales = {}

def load(locale = 'en_US'):
    with open(f'localisation/{locale}.yml', 'r') as stream:
        locales[locale] = yaml.safe_load(stream)

def get(key, locale = 'en_US'):
    if not locale in locales:
       load(locale)
    answer = ""
    try:
        answer = locales[locale][key]
    except:
        answer = f"{key}"
    return answer