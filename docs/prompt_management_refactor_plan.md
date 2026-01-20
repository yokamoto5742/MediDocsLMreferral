# プロンプト管理画面リファクタリング実装計画

## 概要

プロンプト管理画面のUI/UX改善として、以下の変更を実施します：

1. フィルター直下にプロンプト一覧を配置
2. 編集・新規作成を別画面に分離
3. 新規作成ボタンを適切な位置に配置

## 現状の構造

### ファイル構成
- `app/templates/prompts.html` - プロンプト管理画面（一覧・作成・編集が同一ページ）
- `app/api/prompts.py` - プロンプトAPI
- `app/main.py` - ルーティング定義

### 現在の画面構成
```
プロンプト管理ページ（/prompts）
├─ フィルター（診療科・医師名・文書タイプ）
├─ プロンプト作成/編集フォーム
└─ プロンプト一覧テーブル
```

## 変更後の構造

### 画面構成
```
1. プロンプト一覧ページ（/prompts）
   ├─ フィルター（診療科・医師名・文書タイプ）
   ├─ 新規作成ボタン
   └─ プロンプト一覧テーブル（編集ボタンで別画面遷移）

2. プロンプト新規作成ページ（/prompts/new）
   ├─ 新規作成フォーム
   └─ 保存・キャンセルボタン

3. プロンプト編集ページ（/prompts/edit/:id）
   ├─ 編集フォーム
   └─ 更新・削除・キャンセルボタン
```

## 実装タスク

### 1. APIエンドポイントの追加

#### ファイル: `app/api/prompts.py`

**追加するエンドポイント:**
```python
@router.get("/{prompt_id}", response_model=PromptResponse)
def get_prompt(prompt_id: int, db: Session = Depends(get_db)):
    """単一プロンプトを取得"""
```

**理由:** 編集画面で特定のプロンプトデータを取得する必要があるため

### 2. ルーティングの追加

#### ファイル: `app/main.py`

**追加するルート:**
```python
@app.get("/prompts/new", response_class=HTMLResponse)
async def prompts_new_page(request: Request):
    """プロンプト新規作成ページ"""

@app.get("/prompts/edit/{prompt_id}", response_class=HTMLResponse)
async def prompts_edit_page(request: Request, prompt_id: int):
    """プロンプト編集ページ"""
```

**注意事項:**
- `/prompts/new` と `/prompts/edit/{prompt_id}` を `/prompts` より前に定義する必要がある
- FastAPIのルート解決順序により、具体的なパスを先に定義

### 3. テンプレートファイルの作成・修正

#### 3-1. プロンプト一覧ページの修正

**ファイル: `app/templates/prompts.html`**

**変更内容:**
- プロンプト作成/編集フォーム部分（47-99行目）を削除
- 新規作成ボタンを追加（フィルター直下）
- 一覧テーブルの編集ボタンを別画面遷移に変更
- JavaScript関数を簡素化（保存・編集機能を削除、一覧表示のみ）

**新規作成ボタンの配置:**
```html
<!-- フィルター -->
<div class="bg-white dark:bg-gray-800 rounded-lg shadow p-4 mb-6">
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <!-- フィルター選択肢 -->
    </div>
    <!-- 新規作成ボタン -->
    <div class="mt-4 flex justify-end">
        <a href="/prompts/new" class="bg-blue-600 dark:bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-700 dark:hover:bg-blue-600">
            新規プロンプト作成
        </a>
    </div>
</div>

<!-- プロンプト一覧 -->
<div class="bg-white dark:bg-gray-800 rounded-lg shadow">
    ...
</div>
```

**一覧テーブルの編集ボタン変更:**
```html
<td class="px-4 py-3 text-sm">
    <a :href="`/prompts/edit/${prompt.id}`" class="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 mr-3">編集</a>
    <button @click="deletePrompt(prompt.id)" class="text-red-600 dark:text-red-400 hover:text-red-800 dark:hover:text-red-300"
            :disabled="prompt.is_default">削除</button>
</td>
```

#### 3-2. プロンプト新規作成ページの作成

**新規ファイル: `app/templates/prompts_new.html`**

**構成:**
```html
{% extends "base.html" %}

{% block title %}新規プロンプト作成{% endblock %}

{% block content %}
<div class="max-w-4xl mx-auto" x-data="promptNewPage()">
    <h2 class="text-2xl font-bold text-gray-800 dark:text-gray-100 mb-6">新規プロンプト作成</h2>

    <!-- エラー・成功メッセージ -->

    <!-- フォーム -->
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <!-- 診療科、医師名、文書タイプ、モデル選択 -->
        <!-- プロンプト内容 -->

        <!-- ボタン -->
        <div class="flex gap-2">
            <button @click="savePrompt()" :disabled="isSaving">作成</button>
            <a href="/prompts">キャンセル</a>
        </div>
    </div>
</div>
<script>
function promptNewPage() {
    return {
        form: { ... },
        async savePrompt() {
            // POST /api/prompts/
            // 成功後 → /prompts にリダイレクト
        }
    }
}
</script>
{% endblock %}
```

**機能:**
- フォーム入力
- バリデーション
- API呼び出し（POST /api/prompts/）
- 成功時に一覧ページへリダイレクト

#### 3-3. プロンプト編集ページの作成

**新規ファイル: `app/templates/prompts_edit.html`**

**構成:**
```html
{% extends "base.html" %}

{% block title %}プロンプト編集{% endblock %}

{% block content %}
<div class="max-w-4xl mx-auto" x-data="promptEditPage({{ prompt_id }})">
    <h2 class="text-2xl font-bold text-gray-800 dark:text-gray-100 mb-6">プロンプト編集</h2>

    <!-- 読み込み中表示 -->
    <template x-if="isLoading">
        <div>読み込み中...</div>
    </template>

    <!-- フォーム -->
    <template x-if="!isLoading">
        <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <!-- 診療科、医師名、文書タイプ（編集不可） -->
            <!-- モデル選択、プロンプト内容 -->

            <!-- ボタン -->
            <div class="flex gap-2">
                <button @click="updatePrompt()">更新</button>
                <button @click="deletePrompt()">削除</button>
                <a href="/prompts">キャンセル</a>
            </div>
        </div>
    </template>
</div>
<script>
function promptEditPage(promptId) {
    return {
        promptId: promptId,
        form: { ... },
        isLoading: true,

        async init() {
            await this.loadPrompt();
        },

        async loadPrompt() {
            // GET /api/prompts/{promptId}
        },

        async updatePrompt() {
            // POST /api/prompts/
        },

        async deletePrompt() {
            // DELETE /api/prompts/{promptId}
            // 成功後 → /prompts にリダイレクト
        }
    }
}
</script>
{% endblock %}
```

**機能:**
- プロンプトデータの読み込み（GET /api/prompts/{id}）
- フォーム編集（診療科・医師名・文書タイプは編集不可）
- 更新（POST /api/prompts/）
- 削除（DELETE /api/prompts/{id}）
- 成功時に一覧ページへリダイレクト

### 4. サービス層の追加（必要に応じて）

#### ファイル: `app/services/prompt_service.py`

**確認事項:**
- `get_prompt_by_id` 関数が存在するか確認
- 存在しない場合は追加

```python
def get_prompt_by_id(db: Session, prompt_id: int) -> Optional[Prompt]:
    """IDでプロンプトを取得"""
    return db.query(Prompt).filter(Prompt.id == prompt_id).first()
```

## UI/UX改善のポイント

### 1. ユーザビリティ
- **分離による明確化**: 一覧表示と編集/作成を分離することで、各画面の目的が明確になる
- **視認性向上**: フィルター直下にプロンプト一覧を配置し、検索結果がすぐに確認できる
- **操作の明確化**: 新規作成ボタンを専用配置することで、次の操作が明確になる

### 2. 画面遷移フロー
```
プロンプト一覧 (/prompts)
    ├─ [新規作成] → プロンプト新規作成 (/prompts/new)
    │                   ├─ [作成] → プロンプト一覧へリダイレクト
    │                   └─ [キャンセル] → プロンプト一覧へ戻る
    │
    └─ [編集] → プロンプト編集 (/prompts/edit/:id)
                    ├─ [更新] → プロンプト一覧へリダイレクト
                    ├─ [削除] → プロンプト一覧へリダイレクト
                    └─ [キャンセル] → プロンプト一覧へ戻る
```

### 3. 一覧画面のレイアウト変更

**変更前:**
```
┌─────────────────────────────────┐
│ フィルター                        │
├─────────────────────────────────┤
│ 作成/編集フォーム（大きい）        │
├─────────────────────────────────┤
│ プロンプト一覧                    │
└─────────────────────────────────┘
```

**変更後:**
```
┌─────────────────────────────────┐
│ フィルター                        │
│ [新規作成ボタン]                  │
├─────────────────────────────────┤
│ プロンプト一覧                    │
│ （より広い表示領域）               │
└─────────────────────────────────┘
```

## 実装順序

1. **API層** (`app/api/prompts.py`)
   - GET /api/prompts/{prompt_id} エンドポイント追加
   - サービス層の確認・追加

2. **ルーティング** (`app/main.py`)
   - /prompts/new ルート追加
   - /prompts/edit/{prompt_id} ルート追加

3. **テンプレート作成**
   - `app/templates/prompts_new.html` 作成
   - `app/templates/prompts_edit.html` 作成

4. **テンプレート修正**
   - `app/templates/prompts.html` 修正
     - フォーム削除
     - 新規作成ボタン追加
     - 編集リンク変更
     - JavaScript簡素化

5. **テスト**
   - 新規作成フロー確認
   - 編集フロー確認
   - 削除フロー確認
   - フィルター機能確認

## テスト項目

### 機能テスト
- [ ] プロンプト一覧の表示
- [ ] フィルター機能（診療科・医師名・文書タイプ）
- [ ] 新規作成ボタンのクリック → 新規作成画面遷移
- [ ] 新規作成フォームの入力・保存 → 一覧画面へリダイレクト
- [ ] 編集ボタンのクリック → 編集画面遷移
- [ ] 編集フォームのデータ読み込み
- [ ] 編集フォームの更新 → 一覧画面へリダイレクト
- [ ] 削除ボタン → 確認ダイアログ → 削除 → 一覧画面へリダイレクト
- [ ] キャンセルボタン → 一覧画面へ戻る

### UI/UXテスト
- [ ] レスポンシブデザインの確認
- [ ] ダークモード対応
- [ ] エラーメッセージの表示
- [ ] 成功メッセージの表示
- [ ] 読み込み中の表示

### エラーハンドリング
- [ ] 存在しないプロンプトIDでの編集画面アクセス
- [ ] API通信エラー時の挙動
- [ ] バリデーションエラー時の挙動

## 注意事項

### ルーティングの順序
FastAPIでは、より具体的なパスを先に定義する必要があります：

```python
# 正しい順序
@app.get("/prompts/new", response_class=HTMLResponse)
async def prompts_new_page(request: Request):
    ...

@app.get("/prompts/edit/{prompt_id}", response_class=HTMLResponse)
async def prompts_edit_page(request: Request, prompt_id: int):
    ...

@app.get("/prompts", response_class=HTMLResponse)
async def prompts_page(request: Request):
    ...
```

### コンポーネントの再利用
フォーム部分は `prompts_new.html` と `prompts_edit.html` で類似するため、共通コンポーネント化も検討可能です：
- `app/templates/components/prompt_form.html` として切り出し
- Jinja2の `{% include %}` で再利用

ただし、初期実装では複雑さを避けるため、各テンプレートに直接記述する方針とします。

## 追加の改善提案（オプション）

### 1. パンくずリスト追加
```html
<nav class="mb-4 text-sm">
    <a href="/">ホーム</a> > <a href="/prompts">プロンプト管理</a> > 新規作成
</nav>
```

### 2. フォームバリデーション強化
- リアルタイムバリデーション
- 文字数カウンター（プロンプト内容）
- 必須フィールドの視覚的な表示

### 3. 一覧画面の機能追加
- ページネーション（プロンプト数が多い場合）
- ソート機能（更新日時、診療科など）
- 検索機能（プロンプト内容のキーワード検索）

## まとめ

この実装により、以下の改善が達成されます：

1. **視認性の向上**: フィルター直下にプロンプト一覧を配置し、検索結果がすぐに確認できる
2. **操作性の向上**: 編集・作成を別画面に分離することで、各画面の目的が明確になる
3. **保守性の向上**: 責務の分離により、各画面の複雑さが軽減される

実装は段階的に行い、各段階でテストを実施することで、安定性を確保します。
