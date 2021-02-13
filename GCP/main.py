import base64
import json
import yaml
import datetime
import pandas as pd
import gspread
import re


from pyzaim import ZaimCrawler

from oauth2client.service_account import ServiceAccountCredentials


def cancatNote(x):
    tmp = x['name'] + ' | ' if x['name'] != '' else ''
    tmp += x.comment + ' | ' if x.comment != '' else ''
    tmp += x.place
    return tmp


def cleanUp(data, config, log=False):
    pd_data = pd.DataFrame(data)  # 取得したデータをDataFrame型へ変換

    # --- データ整形 ---

    # 計上する取引だけを抽出する（銀行間の移動等は除外）
    pd_data = pd_data.query("count=='常に含める'")
    # 入金額の列を加える
    pd_data['income'] = pd_data['amount'].where(pd_data['type'] == 'income', 0)
    # 入金の場合はamountを0にする
    pd_data.loc[pd_data['type'] == 'income', ['amount']] = 0
    # 'name'にデータがあれば投入
    pd_data['note'] = pd_data.apply(lambda x: cancatNote(x), axis=1)
    # 不要な列を削除する
    pd_data = pd_data.drop(['count', 'type'], axis=1)
    # 列の並び順を決める
    sort = ['id', 'date', 'amount', 'income', 'category', 'genre',
            'place', 'name', 'comment', 'from_account', 'to_account', 'note']
    # 列の並び替えを行う
    pd_data = pd_data.loc[:, sort]
    # date列のTimestampを文字列型に変換
    pd_data['date'] = pd_data['date'].dt.strftime('%Y/%m/%d')
    # NaNを空文字'-'に変換
    pd_data = pd_data.fillna("")

    # --- データ整形ここまで ---
    if log:
        # ログをCSV出力
        pd_data.to_csv(
            './log/zaim_{}{}_{}.csv'.format(config['year'], str(config['month']).zfill(2), datetime.datetime.now().strftime('%Y%m%d%H%M%S')))

    return pd_data


def myZaim(event, context):
    # パラメータの取得
    if 'data' in event:
        target = json.loads(base64.b64decode(
            event['data']).decode('utf-8'))['target']
        print(target)
    else:
        print("parameter is empty.")
        return "parameter is empty."

    today = datetime.datetime.today()
    if target == 'thisMonth':
        year = today.year
        month = today.month
    elif target == 'lastMonth':
        lastMonth = today.replace(day=1) - datetime.timedelta(days=1)
        year = lastMonth.year
        month = lastMonth.month
    else:
        print("unknown request.")
        return "unknown request."

    # 設定ファイルの読み込み
    with open('config.yaml', 'r') as file:
        config = yaml.load(file, Loader=yaml.SafeLoader)

    # Chrome Driverの起動とZaimへのログイン、ログインには少し時間がかかります
    crawler = ZaimCrawler(config['id'], config['pw'], gcf=True)

    try:
        # データの取得 (データの取得には少し時間がかかります、時間はデータ件数による)
        # progressをFalseにするとプログレスバーを非表示にできる
        data = crawler.get_data(
            year, month, progress=False)

    except:
        return "failed pyZaim."

    # seleniumを閉じる
    finally:
        crawler.close()
        print('close')

    # データ整形
    pd_data = cleanUp(data, config)

    # ---

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
    sheet_name = "transactions"
    spread = gc.open_by_key(SPREADSHEET_KEY)
    worksheets = spread.worksheet(sheet_name)
    query = re.compile(
        r'^{}/{}.*$'.format(str(year), str(month).zfill(2)))
    # query = re.compile(r'^2020\-06.*$')
    find = worksheets.findall(query, in_column=2)

    if len(find) > 0:
        range_start = find[0].row
        range_end = range_start

        for f in find:
            if f.row < range_start:
                range_start = f.row
            if f.row > range_end:
                range_end = f.row

        print('Remove range: {}-{}'.format(range_start, range_end))

        worksheets.delete_rows(range_start, range_end)

    worksheets.append_rows(pd_data.values.tolist())
    worksheets.sort((2, 'asc'))

    return "completed."
