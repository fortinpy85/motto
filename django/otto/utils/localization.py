import json
import os

import polib
from structlog import get_logger

logger = get_logger(__name__)


class LocaleTranslator:

    def __init__(self) -> None:
        """Initialize LocaleTranslator with Gemini API."""
        pass

    def update_translations(self, locale_dir) -> None:

        translations_file = os.path.join(locale_dir, "translation", "translations.json")
        translations = self.__load_translations(translations_file)

        self.__update_po_file(locale_dir, translations)

        self.__save_translations(translations_file, translations)

    def translate_text(self, text: str) -> str:
        """Translate text using Gemini API."""
        from chat.llm import OttoLLM

        llm = OttoLLM(deployment="gemini-1.5-flash")
        prompt = f"Translate the following text to Canadian French (fr-ca):\n\n{text}"
        translation = llm.complete(prompt)
        llm.create_costs()
        return translation

    def __load_translations(self, translations_file):
        with open(translations_file, "r", encoding="utf-8") as json_file:
            translations = json.load(json_file)
        return translations

    def __save_translations(self, translations_file, translations):
        with open(translations_file, "w", encoding="utf-8") as json_file:
            json.dump(translations, json_file, ensure_ascii=False, indent=4)

    def __update_po_file(self, dir, translations_reference):
        po_file_path = os.path.join(dir, "fr", "LC_MESSAGES", "django.po")
        po_file = polib.pofile(po_file_path)

        valid_entries = [entry for entry in po_file if not entry.obsolete]
        logger.debug(f"Loaded {len(valid_entries)} entries.")

        for entry in valid_entries:
            translation_id = entry.msgid
            fr = ""
            fr_auto = ""
            if translation_id in translations_reference:
                fr = translations_reference[translation_id].get("fr")
                fr_auto = translations_reference[translation_id].get("fr_auto")

                if fr:
                    fr = fr
                    fr_auto = fr_auto
                    logger.debug(f'Using manual translation for "{translation_id}."')
                elif entry.msgstr:
                    fr = ""
                    fr_auto = entry.msgstr
                    logger.debug(
                        f'Machine translation entry for "{translation_id}" already exists.'
                    )
                elif fr_auto:
                    fr = ""
                    fr_auto = fr_auto
                    logger.debug(
                        f'Machine translation entry for "{translation_id}" already exists.'
                    )
                else:
                    fr = ""
                    fr_auto = self.translate_text(translation_id)
                    logger.debug(f'Translating "{translation_id}."')
            else:
                fr = ""
                fr_auto = (
                    entry.msgstr
                    if entry.msgstr
                    else self.translate_text(translation_id)
                )
                logger.debug(f'Creating and translating entry "{translation_id}".')

            translations_reference[translation_id] = {"fr": fr, "fr_auto": fr_auto}
            entry.msgstr = fr if fr else fr_auto

        logger.debug(f"Updating file at path: {po_file_path}.")
        po_file.save(po_file_path)
