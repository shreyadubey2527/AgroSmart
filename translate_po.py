import polib
from deep_translator import GoogleTranslator
import time

def translate_po(file_path, lang_code):
    po = polib.pofile(file_path)
    updated = False
    
    # We create a translator instance
    translator = GoogleTranslator(source='auto', target=lang_code)
    
    for entry in po:
        if not entry.msgstr and entry.msgid:
            try:
                # print(f"Translating: {entry.msgid} to {lang_code}")
                # Sometimes it fails on newlines or needs multiple tries
                res = translator.translate(entry.msgid)
                if res:
                    entry.msgstr = res
                    updated = True
                time.sleep(0.1)
            except Exception as e:
                print(f"Failed to translate: {entry.msgid}. Error: {e}")
                
    if updated:
        po.save(file_path)
        print(f"Saved {file_path}")
    else:
        print(f"No new translations for {file_path}")

print("Translating Hindi...")
translate_po('translations/hi/LC_MESSAGES/messages.po', 'hi')

print("Translating Marathi...")
translate_po('translations/mr/LC_MESSAGES/messages.po', 'mr')
