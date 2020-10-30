import yaml
from pyzaim import ZaimCrawler
import pandas as pd
import datetime


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

        # データ整形
        pd_data = cleanUp(data, config)

    # 終了処理
    finally:
        crawler.close()
