import logging

import deepl

from config.config import settings


class Translator:
    keys = settings.DEEPL_KEYS
    translator = None

    def __init__(self):
        print(settings)
        print(self.keys)
        self.translator = deepl.Translator(self.keys[0])

    def en_to_zh(self, content_: str):

        try:
            return self.translator.translate_text(content_, target_lang="ZH")
        except Exception as e:
            logging.error(e)
            self.translator = deepl.Translator(self.keys[1])
            return self.translator.translate_text(content_, target_lang="ZH")
