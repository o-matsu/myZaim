# myZaim

scraping Zaim, and output to spreadsheet.

## deploy command for GCP

```
gcloud functions deploy myZaim --runtime python38 --trigger-topic topic-myZaim --region asia-northeast2 --memory 2GB --source . --timeout 540
```

```
gcloud functions call myZaim --data '{"target":"thisMonth"}' --region asia-northeast2
```
