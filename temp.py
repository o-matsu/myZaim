import yaml
from pyzaim import ZaimCrawler
import pandas as pd
import datetime

import re
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from gspread_dataframe import get_as_dataframe, set_with_dataframe


def main():
    # 設定ファイルの読み込み
    with open('config.yaml', 'r') as file:
        config = yaml.load(file, Loader=yaml.SafeLoader)

    # 2つのAPIを記述しないとリフレッシュトークンを3600秒毎に発行し続けなければならない
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']

    # 認証情報設定
    # ダウンロードしたjsonファイル名をクレデンシャル変数に設定（秘密鍵、Pythonファイルから読み込みしやすい位置に置く）
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        config['secret'], scope)

    # OAuth2の資格情報を使用してGoogle APIにログインします。
    gc = gspread.authorize(credentials)

    # 共有設定したスプレッドシートキーを変数[SPREADSHEET_KEY]に格納する。
    SPREADSHEET_KEY = config['sheet']

    # 共有設定したスプレッドシートを開く
    sheet_name = "temp"
    spread = gc.open_by_key(SPREADSHEET_KEY)
    worksheets = spread.worksheet(sheet_name)
    query = re.compile(r'^2020/06.*$')
    find = worksheets.findall(query, in_column=2)
    print(find)

    if len(find) > 0:
        range_start = find[0].row
        range_end = range_start

        for f in find:
            if f.row < range_start:
                range_start = f.row
            if f.row > range_end:
                range_end = f.row

        print(range_start,range_end)

        worksheets.delete_rows(range_start, range_end)

    worksheets.append_row(['**********', '2020/06/30', 1078, 0, '固定費', '通信', 'So-net', '', '', '楽天カード(MasterCard) XXXX-XXXX-XXXX-8839', ''])


main()
