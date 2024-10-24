# init_files.py

import json
import os

def initialize_files():
    # إنشاء trades.json
    if not os.path.exists('trades.json'):
        with open('trades.json', 'w', encoding='utf-8') as f:
            json.dump([], f)
            print("تم إنشاء trades.json")

    # إنشاء signals.json
    if not os.path.exists('signals.json'):
        with open('signals.json', 'w', encoding='utf-8') as f:
            json.dump([], f)
            print("تم إنشاء signals.json")

    # إنشاء auth.txt
    if not os.path.exists('auth.txt'):
        with open('auth.txt', 'w', encoding='utf-8') as f:
            f.write('unauthenticated')
            print("تم إنشاء auth.txt")

    # إنشاء ip_address.txt
    if not os.path.exists('ip_address.txt'):
        with open('ip_address.txt', 'w', encoding='utf-8') as f:
            f.write('')
            print("تم إنشاء ip_address.txt")

    # إنشاء max_loss_value.txt
    if not os.path.exists('max_loss_value.txt'):
        with open('max_loss_value.txt', 'w', encoding='utf-8') as f:
            f.write('0')
            print("تم إنشاء max_loss_value.txt")

if __name__ == "__main__":
    initialize_files()