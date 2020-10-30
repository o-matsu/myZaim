import yaml
from pyzaim import ZaimCrawler
import pandas as pd
import datetime

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from gspread_dataframe import get_as_dataframe, set_with_dataframe


def cleanUp(data, config):
    pd_data = pd.DataFrame(data)  # 取得したデータをDataFrame型へ変換

    pd_data = pd_data.query("count=='常に含める'")  # 計上しない取引を削除する（銀行間の移動など）
    pd_data['income'] = pd_data['amount'].where(
        pd_data['type'] == 'income', 0)  # 入金額の列を加える
    pd_data.loc[pd_data['type'] == 'income', [
        'amount']] = 0  # 入金の場合はamountを0にする
    pd_data = pd_data.drop(['count', 'type'], axis=1)  # 不要な列を削除する
    sort = ['id', 'date', 'amount', 'income', 'category', 'genre',
            'place', 'name', 'comment', 'from_account', 'to_account']  # 列の並び順を決める
    pd_data = pd_data.loc[:, sort]  # 列の並び替えを行う

    # ログをCSV出力
    pd_data.to_csv(
        './log/zaim_{}{}_{}.csv'.format(config['year'], str(config['month']).zfill(2), datetime.datetime.now().strftime('%Y%m%d%H%M%S')))

    return pd_data


def main():
    # 設定ファイルの読み込み
    with open('config.yaml', 'r') as file:
        config = yaml.load(file, Loader=yaml.SafeLoader)

    # Chrome Driverの起動とZaimへのログイン、ログインには少し時間がかかります
    crawler = ZaimCrawler(config['id'], config['pw'],
                          driver_path=config['driver_path'],
                          headless=config['headless'])  # headlessをTrueにするとヘッドレスブラウザで実行できる
    try:
        # データの取得 (データの取得には少し時間がかかります、時間はデータ件数による)
        # progressをFalseにするとプログレスバーを非表示にできる
        data = crawler.get_data(config['year'], config['month'], progress=True)

    # seleniumを閉じる
    finally:
        crawler.close()

    # データ整形
    pd_data = cleanUp(data, config)

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

    sheet_name = str(config['year'])+str(config['month']).zfill(2)

    # 共有設定したスプレッドシートのシート1を開く
    spread = gc.open_by_key(SPREADSHEET_KEY)
    worksheets = spread.worksheets()
    flg = False
    for worksheet in worksheets:
        if worksheet.title == sheet_name:
            flg = True
    if flg:
        ws = spread.worksheet(sheet_name)
    else:
        ws = spread.add_worksheet(sheet_name, rows=str(
            pd_data.shape[0]+10), cols=str(pd_data.shape[1]))

    set_with_dataframe(ws, pd_data)


main()
