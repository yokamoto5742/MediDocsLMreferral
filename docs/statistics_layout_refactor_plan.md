# 統計情報画面レイアウト変更 実装計画

## 概要
`Statistics_screen_layout.jpg` の構図に基づいて、統計情報画面のレイアウトを変更する。

## 現状分析

### 現在のレイアウト
1. **フィルター部**: 1行3列（開始日、終了日、モデル）
2. **サマリーカード**: 4つのメトリクス表示（合計生成数、総入力トークン、総出力トークン、平均作成時間）
3. **使用履歴テーブル**: 詳細レコード一覧

### 目標レイアウト（画像参照）
1. **フィルター部**: 2行2列
   - 左列: 開始日、終了日
   - 右列: AIモデル、文書名
2. **集計テーブル**: 文書別のグループ化統計
   - カラム: 文書名、診療科、医師名、作成件数、入力トークン、出力トークン、合計トークン
3. **詳細テーブル**: 個別レコード一覧
   - カラム: 作成日、文書名、診療科、医師名、AIモデル、入力トークン、出力トークン、処理時間(秒)

## 変更点サマリー

### 1. フィルター部の変更
- **追加**: 文書名フィルター（selectbox）
- **レイアウト変更**: `grid-cols-3` → `grid-cols-2` × 2行

### 2. サマリーカード削除
- 4つのメトリクスカードを削除
- 代わりに集計テーブルを追加

### 3. 集計テーブルの追加
- 文書名、診療科、医師名でグループ化した統計データを表示
- 各グループの作成件数、トークン数（入力/出力/合計）を集計

### 4. 詳細テーブルのカラム順変更
- 現在: 日時、診療科、医師名、文書タイプ、モデル、入力、出力、処理時間
- 変更後: 作成日、文書名、診療科、医師名、AIモデル、入力、出力、処理時間

## 実装手順

### Phase 1: バックエンド実装

#### 1.1 スキーマ定義の追加
**ファイル**: `app/schemas/statistics.py`

```python
class AggregatedRecord(BaseModel):
    """集計レコード"""
    document_type: str
    department: str
    doctor: str
    count: int
    input_tokens: int
    output_tokens: int
    total_tokens: int

    model_config = ConfigDict(from_attributes=True)
```

#### 1.2 サービス関数の追加
**ファイル**: `app/services/statistics_service.py`

新規関数:
```python
def get_aggregated_records(
    db: Session,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    model: str | None = None,
    document_type: str | None = None,
) -> list[dict]:
    """文書別に集計した統計データを取得"""
```

実装内容:
- `SummaryUsage` テーブルから GROUP BY で集計
- グループ化キー: `document_type`, `department`, `doctor`
- 集計値: COUNT, SUM(input_tokens), SUM(output_tokens), SUM(total_tokens)
- フィルター条件を適用（start_date, end_date, model, document_type）

#### 1.3 詳細レコード取得関数の更新
**ファイル**: `app/services/statistics_service.py`

既存関数を更新:
```python
def get_usage_records(
    db: Session,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    model: str | None = None,
    document_type: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[SummaryUsage]:
    """使用統計レコードを取得（フィルター追加）"""
```

変更点:
- フィルターパラメータを追加（start_date, end_date, model, document_type）
- クエリにフィルター条件を適用

#### 1.4 API エンドポイントの追加・更新
**ファイル**: `app/api/statistics.py`

新規エンドポイント:
```python
@router.get("/aggregated", response_model=list[AggregatedRecord])
def get_aggregated(
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    model: str | None = None,
    document_type: str | None = None,
    db: Session = Depends(get_db),
):
    """集計統計データを取得"""
```

既存エンドポイント更新:
```python
@router.get("/records", response_model=list[UsageRecord])
def get_records(
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    model: str | None = None,
    document_type: str | None = None,
    limit: int = Query(100, le=500),
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """使用統計レコードを取得（フィルター追加）"""
```

### Phase 2: フロントエンド実装

#### 2.1 HTMLテンプレートの変更
**ファイル**: `app/templates/statistics.html`

**変更1: フィルター部のレイアウト変更**

現在（1行3列）:
```html
<div class="grid grid-cols-1 md:grid-cols-3 gap-4">
    <div>開始日</div>
    <div>終了日</div>
    <div>モデル</div>
</div>
```

変更後（2行2列）:
```html
<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
    <div>
        <label>開始日</label>
        <input type="date" x-model="filter.startDate" @change="loadData()">
    </div>
    <div>
        <label>AIモデル</label>
        <select x-model="filter.model" @change="loadData()">...</select>
    </div>
</div>
<div class="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
    <div>
        <label>終了日</label>
        <input type="date" x-model="filter.endDate" @change="loadData()">
    </div>
    <div>
        <label>文書名</label>
        <select x-model="filter.documentType" @change="loadData()">
            <option value="">すべて</option>
            {% for doc_type in document_types %}
            <option value="{{ doc_type }}">{{ doc_type }}</option>
            {% endfor %}
        </select>
    </div>
</div>
```

**変更2: サマリーカード削除**

以下のセクションを削除:
```html
<!-- サマリー統計 -->
<div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
    ...4つのカード...
</div>
```

**変更3: 集計テーブルの追加**

新規セクション追加（サマリーカードの代わり）:
```html
<!-- 集計テーブル -->
<div class="bg-white dark:bg-gray-800 rounded-lg shadow mb-6">
    <div class="p-4 border-b border-gray-200 dark:border-gray-700">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100">集計統計</h3>
    </div>
    <div class="overflow-x-auto">
        <table class="w-full">
            <thead class="bg-gray-50 dark:bg-gray-900">
                <tr>
                    <th>文書名</th>
                    <th>診療科</th>
                    <th>医師名</th>
                    <th class="text-right">作成件数</th>
                    <th class="text-right">入力トークン</th>
                    <th class="text-right">出力トークン</th>
                    <th class="text-right">合計トークン</th>
                </tr>
            </thead>
            <tbody>
                <template x-for="record in aggregatedRecords" :key="record.document_type + record.department + record.doctor">
                    <tr>
                        <td x-text="record.document_type"></td>
                        <td x-text="record.department"></td>
                        <td x-text="record.doctor"></td>
                        <td class="text-right" x-text="record.count"></td>
                        <td class="text-right" x-text="formatNumber(record.input_tokens)"></td>
                        <td class="text-right" x-text="formatNumber(record.output_tokens)"></td>
                        <td class="text-right" x-text="formatNumber(record.total_tokens)"></td>
                    </tr>
                </template>
            </tbody>
        </table>
    </div>
</div>
```

**変更4: 詳細テーブルのカラム順変更**

テーブルヘッダーとボディの順序を変更:
```html
<thead>
    <tr>
        <th>作成日</th>
        <th>文書名</th>
        <th>診療科</th>
        <th>医師名</th>
        <th>AIモデル</th>
        <th class="text-right">入力トークン</th>
        <th class="text-right">出力トークン</th>
        <th class="text-right">処理時間(秒)</th>
    </tr>
</thead>
<tbody>
    <template x-for="record in records" :key="record.id">
        <tr>
            <td x-text="formatDateTime(record.date)"></td>
            <td x-text="record.document_type || '-'"></td>
            <td x-text="record.department || '-'"></td>
            <td x-text="record.doctor || '-'"></td>
            <td x-text="record.model || '-'"></td>
            <td class="text-right" x-text="formatNumber(record.input_tokens || 0)"></td>
            <td class="text-right" x-text="formatNumber(record.output_tokens || 0)"></td>
            <td class="text-right" x-text="(record.processing_time || 0).toFixed(2)"></td>
        </tr>
    </template>
</tbody>
```

#### 2.2 JavaScript の更新

**変更1: データモデルに集計レコードを追加**

```javascript
function statisticsPage() {
    return {
        aggregatedRecords: [],
        records: [],
        filter: {
            startDate: '',
            endDate: '',
            model: '',
            documentType: ''  // 新規追加
        },
        // ...
    }
}
```

**変更2: 集計データ取得関数の追加**

```javascript
async loadAggregatedData() {
    this.isLoadingAggregated = true;
    this.error = null;

    try {
        const params = new URLSearchParams();
        if (this.filter.startDate) params.append('start_date', new Date(this.filter.startDate).toISOString());
        if (this.filter.endDate) params.append('end_date', new Date(this.filter.endDate).toISOString());
        if (this.filter.model) params.append('model', this.filter.model);
        if (this.filter.documentType) params.append('document_type', this.filter.documentType);

        const response = await fetch(`/api/statistics/aggregated?${params}`);
        this.aggregatedRecords = await response.json();
    } catch (e) {
        this.error = '集計データの読み込みに失敗しました';
    } finally {
        this.isLoadingAggregated = false;
    }
}
```

**変更3: 詳細レコード取得関数の更新**

フィルターパラメータを追加:
```javascript
async loadRecords() {
    this.isLoadingRecords = true;
    this.error = null;

    try {
        const params = new URLSearchParams({
            limit: this.pagination.limit,
            offset: this.pagination.offset
        });

        // フィルター条件を追加
        if (this.filter.startDate) params.append('start_date', new Date(this.filter.startDate).toISOString());
        if (this.filter.endDate) params.append('end_date', new Date(this.filter.endDate).toISOString());
        if (this.filter.model) params.append('model', this.filter.model);
        if (this.filter.documentType) params.append('document_type', this.filter.documentType);

        const response = await fetch(`/api/statistics/records?${params}`);
        this.records = await response.json();
        // ...
    } catch (e) {
        this.error = '使用履歴の読み込みに失敗しました';
    } finally {
        this.isLoadingRecords = false;
    }
}
```

**変更4: 初期化処理の更新**

```javascript
async init() {
    await this.loadAggregatedData();
    await this.loadRecords();
}
```

**変更5: 統合されたデータ読み込み関数**

```javascript
async loadData() {
    await Promise.all([
        this.loadAggregatedData(),
        this.loadRecords()
    ]);
}
```

フィルター変更時に `loadData()` を呼び出すように変更。

#### 2.3 テンプレートコンテキストの更新
**ファイル**: `app/main.py`

`statistics_page` 関数で `document_types` を追加:
```python
@app.get("/statistics", response_class=HTMLResponse)
async def statistics_page(request: Request):
    """統計ページ"""
    return templates.TemplateResponse(
        "statistics.html",
        {"request": request, **get_common_context("statistics")},
    )
```

`get_common_context` 関数には既に `document_types` が含まれているため、追加変更は不要。

### 変更
1. `app/schemas/statistics.py` - `AggregatedRecord` スキーマ追加
2. `app/services/statistics_service.py` - 2つの関数追加・更新
3. `app/api/statistics.py` - 2つのエンドポイント追加・更新
4. `app/templates/statistics.html` - レイアウト全面変更
5. `tests/services/test_statistics_service.py` - テスト追加
6. `tests/api/test_statistics.py` - テスト追加

## 実装の優先順位

1. **高**: Phase 1（バックエンド） - APIがないとフロントエンドが動作しない
2. **高**: Phase 2（フロントエンド） - ユーザーインターフェース変更

## 注意事項

### スタイル統一
- Tailwind CSS クラスを既存コードと同じスタイルで使用
- ダークモード対応を維持（`dark:` prefix）
- 既存のカラーパレットを使用（gray-800, gray-100 など）

### レスポンシブデザイン
- `grid-cols-1 md:grid-cols-2` でモバイル対応
- テーブルは `overflow-x-auto` でスクロール可能に

### パフォーマンス
- 集計クエリは GROUP BY を使用するため、大量データでは遅くなる可能性あり
- 必要に応じてインデックスを追加（`document_type`, `department`, `doctor`, `date`）

### 互換性
- 既存のAPIエンドポイント `/api/statistics/summary` は削除せず、維持
- 新規エンドポイント `/api/statistics/aggregated` を追加
\