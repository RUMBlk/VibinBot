import yaml
import os
from database import *

locales = {}

class locale():
    dictionary = []
    def __init__(self, locale = 'en_US', branch = None):
        query = locales.get(locale)
        if branch is not None:
            self.dictionary = branch 
        elif query is None:
            self.load(locale) 
        else:
            self.dictionary = query

    def load(self, locale = 'en_US'):
        with open(f'localisation/{locale}.yml', 'r') as stream:
            locales[locale] = yaml.safe_load(stream)
            self.dictionary = locales[locale]

    def get(self, key='lorem_ipsum'):
        branch = self.dictionary.get(key, key)
        if type(branch) is dict: new = locale(branch = branch)
        else: new = branch
        return new
