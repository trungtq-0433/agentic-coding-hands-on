# アーキテクチャ

## サービスインタラクション

| 送信元 | 送信先 | メソッド | 説明 |
|--------|--------|---------|------|
| employee-frontend | employee-backend | GET /api/jugyoin | 従業員一覧取得 |

## イベント

| トピック | 役割 | イベント |
|----------|------|---------|
| jugyoin.created | producer | JugyoinCreated |
