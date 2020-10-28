import yaml
from pyzaim import ZaimCrawler
import csv

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

    keys = ['id', 'count', 'date', 'category', 'genre', 'amount',
            'from_account', 'to_account', 'type', 'place', 'name', 'comment']

    with open('./zaim_{}{}.csv'.format(config['year'], str(config['month']).zfill(2)), 'w') as output_file:
        dict_writer = csv.DictWriter(output_file, fieldnames=keys)
        dict_writer.writeheader()
        dict_writer.writerows(data)

# 終了処理
finally:
    crawler.close()
