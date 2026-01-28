# HTMLファイル整理・リファクタリング計画

## 現状分析

### 対象ファイル
| ファイル | 行数 | 役割 |
|---------|------|------|
| `app/templates/index.html` | 187行 | 入力・出力・評価の3画面を含む |
| `app/templates/base.html` | 62行 | レイアウト定義 |
| `app/templates/components/sidebar.html` | 56行 | サイドバー（既にコンポーネント化済み） |
| `app/static/js/app.js` | 244行 | Alpine.jsのステート管理 |

### 主な問題点
1. **Tailwind CSSクラスの重複** - textarea、button、selectに同じクラスが繰り返し使用
2. **3つの画面が1ファイルに混在** - 入力・出力・評価画面がすべて`index.html`に
3. **Alpine.jsロジックのHTML埋め込み** - 三項演算子等がHTML内に散在
4. **型安全性の欠如** - JavaScriptのため型チェックなし

---

## フェーズ1: Jinja2コンポーネント分割

### ステップ1.1: 画面ごとのコンポーネント作成

**作成するファイル:**
```
app/templates/components/
├── input_screen.html      # 入力画面
├── output_screen.html     # 出力画面
└── evaluation_screen.html # 評価画面
```

**修正後の`index.html`:**
```jinja2
{% extends "base.html" %}

{% block content %}
<div class="max-w-4xl">
    {% include "components/input_screen.html" %}
    {% include "components/output_screen.html" %}
    {% include "components/evaluation_screen.html" %}
</div>
{% endblock %}
```

### ステップ1.2: 分割内容

| コンポーネント | 対応行（現index.html） | 主な要素 |
|--------------|---------------------|---------|
| `input_screen.html` | 6-60行 | フォーム入力、作成ボタン、エラー表示 |
| `output_screen.html` | 63-143行 | タブ表示、出力textarea、ボタン群 |
| `evaluation_screen.html` | 146-184行 | 評価結果表示、戻るボタン |

---

## フェーズ2: Jinja2マクロによる共通要素の抽出

### ステップ2.1: マクロファイルの作成

**作成: `app/templates/macros.html`**

```jinja2
{# テキストエリアコンポーネント #}
{% macro textarea_field(label, model, rows=1) %}
<div>
    <label class="block text-base font-medium text-white mb-1">{{ label }}</label>
    <textarea x-model="{{ model }}" rows="{{ rows }}"
        class="form-textarea"></textarea>
</div>
{% endmacro %}

{# プライマリボタン #}
{% macro primary_button(text, disabled_model=None, loading_text=None, type="button", click=None) %}
<button type="{{ type }}"
    {% if click %}@click="{{ click }}"{% endif %}
    {% if disabled_model %}:disabled="{{ disabled_model }}"{% endif %}
    class="btn-primary">
    {% if loading_text %}
    <span x-show="!{{ disabled_model }}">{{ text }}</span>
    <span x-show="{{ disabled_model }}">{{ loading_text }}</span>
    {% else %}
    {{ text }}
    {% endif %}
</button>
{% endmacro %}

{# セカンダリボタン #}
{% macro secondary_button(text, click) %}
<button type="button" @click="{{ click }}" class="btn-secondary">
    {{ text }}
</button>
{% endmacro %}

{# エラー表示 #}
{% macro error_alert() %}
<template x-if="error">
<div class="alert-error">
    <span x-text="error"></span>
</div>
</template>
{% endmacro %}
```

### ステップ2.2: CSSユーティリティクラスの追加

**修正: `app/static/css/style.css`**

```css
/* フォーム要素 */
.form-textarea {
    @apply w-full border border-gray-300 dark:border-gray-600 rounded-md p-3
           bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100
           focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400;
}

.form-select {
    @apply w-full border border-gray-300 dark:border-gray-600 rounded-md p-1
           bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100
           focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400;
}

/* ボタン */
.btn-primary {
    @apply px-6 py-2 bg-blue-600 dark:bg-blue-500 text-white rounded-md
           hover:bg-blue-700 dark:hover:bg-blue-600
           disabled:opacity-50 disabled:cursor-not-allowed;
}

.btn-secondary {
    @apply px-6 py-2 border border-gray-300 dark:border-gray-600 rounded-md
           bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100
           hover:bg-gray-100 dark:hover:bg-gray-700;
}

.btn-success {
    @apply px-6 py-2 bg-green-600 dark:bg-green-500 text-white rounded-md
           hover:bg-green-700 dark:hover:bg-green-600
           disabled:opacity-50 disabled:cursor-not-allowed;
}

.btn-accent {
    @apply px-6 py-2 bg-purple-600 dark:bg-purple-500 text-white rounded-md
           hover:bg-purple-700 dark:hover:bg-purple-600;
}

/* アラート */
.alert-error {
    @apply p-4 bg-red-50 dark:bg-red-900/20 border border-red-200
           dark:border-red-800 rounded-md text-red-700 dark:text-red-400;
}

.alert-warning {
    @apply p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200
           dark:border-yellow-800 rounded-md text-sm text-yellow-800 dark:text-yellow-400;
}
```

### ステップ2.3: マクロ適用後のコンポーネント例

**`input_screen.html`（マクロ適用後）:**
```jinja2
{% import "macros.html" as m %}

<template x-if="currentScreen === 'input'">
<div>
    <form @submit.prevent="generateSummary()" class="space-y-2">
        {{ m.textarea_field("紹介目的", "form.referralPurpose", 1) }}
        {{ m.textarea_field("現在の処方", "form.currentPrescription", 1) }}
        {{ m.textarea_field("カルテ記載", "form.medicalText", 3) }}
        {{ m.textarea_field("追加情報", "form.additionalInfo", 1) }}

        <div class="flex gap-4">
            {{ m.primary_button("作成", "isGenerating", "生成中...", type="submit") }}
            {{ m.secondary_button("テキストをクリア", "clearForm()") }}
        </div>

        <template x-if="isGenerating">
        <div class="mt-2 text-base text-white">
            作成時間: <span x-text="elapsedTime"></span>秒
        </div>
        </template>
    </form>

    {{ m.error_alert() }}
</div>
</template>
```

---

## フェーズ3: Alpine.jsロジックのapp.jsへの移動

### ステップ3.1: ヘルパー関数の追加

**修正: `app/static/js/app.js`に追加**

```javascript
// 現在表示中のタブコンテンツを取得
getCurrentTabContent() {
    if (this.activeTab === 0) {
        return this.result.outputSummary;
    }
    return this.result.parsedSummary[this.tabs[this.activeTab]] || '';
},

// コピーボタンのハンドラ
copyCurrentTab() {
    this.copyToClipboard(this.getCurrentTabContent());
},

// タブがアクティブかどうか
isActiveTab(index) {
    return this.activeTab === index;
},

// タブのCSSクラスを取得
getTabClass(index) {
    return this.isActiveTab(index)
        ? 'border-blue-500 text-blue-600 dark:border-blue-400 dark:text-blue-400'
        : 'border-transparent text-white hover:text-gray-700 dark:hover:text-gray-300';
}
```

### ステップ3.2: HTML側の簡素化

**変更前:**
```html
<button @click="copyToClipboard(activeTab === 0 ? result.outputSummary : (result.parsedSummary[tabs[activeTab]] || ''))">
```

**変更後:**
```html
<button @click="copyCurrentTab()">
```

---

## フェーズ4: Vite + TypeScript + Tailwind導入

### ステップ4.1: Viteプロジェクトのセットアップ

**ディレクトリ構造:**
```
frontend/
├── src/
│   ├── main.ts          # エントリーポイント
│   ├── app.ts           # Alpine.jsアプリケーション
│   ├── types.ts         # 型定義
│   └── styles/
│       └── main.css     # Tailwind CSS（@apply使用可能）
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
└── postcss.config.js
```

**package.jsonの作成:**
```json
{
  "name": "medidocs-frontend",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview",
    "typecheck": "tsc --noEmit"
  },
  "devDependencies": {
    "typescript": "^5.3.0",
    "vite": "^5.0.0",
    "tailwindcss": "^3.4.0",
    "postcss": "^8.4.0",
    "autoprefixer": "^10.4.0"
  },
  "dependencies": {
    "alpinejs": "^3.13.0"
  }
}
```

**vite.config.tsの作成:**
```typescript
import { defineConfig } from 'vite';
import { resolve } from 'path';

export default defineConfig({
  root: 'frontend',
  build: {
    outDir: '../app/static/dist',
    emptyOutDir: true,
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'frontend/src/main.ts')
      },
      output: {
        entryFileNames: 'js/[name].js',
        chunkFileNames: 'js/[name]-[hash].js',
        assetFileNames: (assetInfo) => {
          if (assetInfo.name?.endsWith('.css')) {
            return 'css/[name][extname]';
          }
          return 'assets/[name]-[hash][extname]';
        }
      }
    }
  },
  server: {
    proxy: {
      '/api': 'http://localhost:8000'
    }
  }
});
```

**tailwind.config.jsの作成:**
```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './frontend/src/**/*.{ts,js}',
    './app/templates/**/*.html'
  ],
  darkMode: 'class',
  theme: {
    extend: {}
  },
  plugins: []
};
```

**postcss.config.jsの作成:**
```javascript
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {}
  }
};
```

**tsconfig.jsonの作成:**
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "noEmit": true,
    "isolatedModules": true
  },
  "include": ["frontend/src/**/*"]
}
```

### ステップ4.2: 型定義ファイルの作成

**作成: `frontend/src/types.ts`**

```typescript
// 設定
export interface Settings {
    department: string;
    doctor: string;
    documentType: string;
    model: string;
}

// フォームデータ
export interface FormData {
    referralPurpose: string;
    currentPrescription: string;
    medicalText: string;
    additionalInfo: string;
}

// 生成結果
export interface GenerationResult {
    outputSummary: string;
    parsedSummary: Record<string, string>;
    processingTime: number | null;
    modelUsed: string;
    modelSwitched: boolean;
}

// 評価結果
export interface EvaluationResult {
    result: string;
    processingTime: number | null;
}

// APIレスポンス（サーバー側のスキーマに対応）
export interface SummaryResponse {
    success: boolean;
    output_summary?: string;
    parsed_summary?: Record<string, string>;
    processing_time?: number;
    model_used?: string;
    model_switched?: boolean;
    error_message?: string;
}

export interface EvaluationResponse {
    success: boolean;
    evaluation_result?: string;
    processing_time?: number;
    error_message?: string;
}

// グローバル変数の型宣言
declare global {
    interface Window {
        DOCUMENT_PURPOSE_MAPPING?: Record<string, string>;
    }
}
```

### ステップ4.3: エントリーポイントとアプリケーションの作成

**作成: `frontend/src/main.ts`**

```typescript
import Alpine from 'alpinejs';
import { appState } from './app';
import './styles/main.css';

// Alpine.jsのデータ登録
Alpine.data('appState', appState);

// グローバルに公開（デバッグ用）
declare global {
    interface Window {
        Alpine: typeof Alpine;
    }
}
window.Alpine = Alpine;

// Alpine.js開始
Alpine.start();
```

**作成: `frontend/src/app.ts`**

```typescript
import type {
    Settings,
    FormData,
    GenerationResult,
    EvaluationResult,
    SummaryResponse,
    EvaluationResponse
} from './types';

type ScreenType = 'input' | 'output' | 'evaluation';

interface AppState {
    settings: Settings;
    doctors: string[];
    form: FormData;
    result: GenerationResult;
    isGenerating: boolean;
    elapsedTime: number;
    timerInterval: ReturnType<typeof setInterval> | null;
    showCopySuccess: boolean;
    error: string | null;
    activeTab: number;
    tabs: readonly string[];
    currentScreen: ScreenType;
    evaluationResult: EvaluationResult;
    isEvaluating: boolean;
    evaluationElapsedTime: number;
    evaluationTimerInterval: ReturnType<typeof setInterval> | null;
    // メソッドの型定義
    init(): Promise<void>;
    updateReferralPurpose(): void;
    updateDoctors(): Promise<void>;
    generateSummary(): Promise<void>;
    clearForm(): void;
    copyToClipboard(text: string): Promise<void>;
    getCurrentTabContent(): string;
    copyCurrentTab(): void;
    // ... 他のメソッド
}

export function appState(): AppState {
    return {
        // Settings
        settings: {
            department: 'default',
            doctor: 'default',
            documentType: '他院への紹介',
            model: 'Claude'
        },
        doctors: ['default'],

        // Form
        form: {
            referralPurpose: '',
            currentPrescription: '',
            medicalText: '',
            additionalInfo: ''
        },

        // Result
        result: {
            outputSummary: '',
            parsedSummary: {},
            processingTime: null,
            modelUsed: '',
            modelSwitched: false
        },

        // UI state
        isGenerating: false,
        elapsedTime: 0,
        timerInterval: null,
        showCopySuccess: false,
        error: null,
        activeTab: 0,
        tabs: ['全文', '主病名', '紹介目的', '既往歴', '症状経過', '治療経過', '現在の処方', '備考'] as const,
        currentScreen: 'input',

        // Evaluation state
        evaluationResult: {
            result: '',
            processingTime: null
        },
        isEvaluating: false,
        evaluationElapsedTime: 0,
        evaluationTimerInterval: null,

        // 初期化
        async init() {
            await this.updateDoctors();
            this.updateReferralPurpose();
        },

        // 紹介目的の更新
        updateReferralPurpose() {
            const mapping = window.DOCUMENT_PURPOSE_MAPPING;
            if (mapping && mapping[this.settings.documentType]) {
                this.form.referralPurpose = mapping[this.settings.documentType];
            }
        },

        // 医師リストの更新
        async updateDoctors() {
            const response = await fetch(`/api/settings/doctors/${this.settings.department}`);
            const data = await response.json() as { doctors: string[] };
            this.doctors = data.doctors;
            if (!this.doctors.includes(this.settings.doctor)) {
                this.settings.doctor = this.doctors[0];
            }
        },

        // 現在のタブコンテンツを取得
        getCurrentTabContent(): string {
            if (this.activeTab === 0) {
                return this.result.outputSummary;
            }
            return this.result.parsedSummary[this.tabs[this.activeTab]] || '';
        },

        // 現在のタブをコピー
        copyCurrentTab() {
            this.copyToClipboard(this.getCurrentTabContent());
        },

        // 以下、既存メソッドを型付きで移植...
        // generateSummary, clearForm, copyToClipboard 等
    };
}
```

**作成: `frontend/src/styles/main.css`**

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

/* フォーム要素 */
@layer components {
    .form-textarea {
        @apply w-full border border-gray-300 dark:border-gray-600 rounded-md p-3
               bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100
               focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400;
    }

    .form-select {
        @apply w-full border border-gray-300 dark:border-gray-600 rounded-md p-1
               bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100
               focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400;
    }

    /* ボタン */
    .btn-primary {
        @apply px-6 py-2 bg-blue-600 dark:bg-blue-500 text-white rounded-md
               hover:bg-blue-700 dark:hover:bg-blue-600
               disabled:opacity-50 disabled:cursor-not-allowed;
    }

    .btn-secondary {
        @apply px-6 py-2 border border-gray-300 dark:border-gray-600 rounded-md
               bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100
               hover:bg-gray-100 dark:hover:bg-gray-700;
    }

    .btn-success {
        @apply px-6 py-2 bg-green-600 dark:bg-green-500 text-white rounded-md
               hover:bg-green-700 dark:hover:bg-green-600
               disabled:opacity-50 disabled:cursor-not-allowed;
    }

    .btn-accent {
        @apply px-6 py-2 bg-purple-600 dark:bg-purple-500 text-white rounded-md
               hover:bg-purple-700 dark:hover:bg-purple-600;
    }

    /* アラート */
    .alert-error {
        @apply p-4 bg-red-50 dark:bg-red-900/20 border border-red-200
               dark:border-red-800 rounded-md text-red-700 dark:text-red-400;
    }

    .alert-warning {
        @apply p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200
               dark:border-yellow-800 rounded-md text-sm text-yellow-800 dark:text-yellow-400;
    }
}
```

### ステップ4.4: base.htmlの更新

**修正: `app/templates/base.html`**

CDN読み込みからViteビルド成果物に切り替え:

```html
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}診療情報提供書作成アプリ{% endblock %}</title>

    <!-- Viteビルド成果物 -->
    <link rel="stylesheet" href="/static/dist/css/main.css">
    <script>
        // ダークモード検出（DOM読み込み前に実行）
        (function() {
            function updateDarkMode() {
                if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
                    document.documentElement.classList.add('dark');
                } else {
                    document.documentElement.classList.remove('dark');
                }
            }
            updateDarkMode();
            window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', updateDarkMode);
        })();
    </script>
</head>
<body class="bg-gray-50 dark:bg-gray-900" x-data="appState()">
    <!-- 省略 -->

    <script>
        // Jinja2からTypeScriptへのデータ受け渡し
        {% if document_purpose_mapping %}
        window.DOCUMENT_PURPOSE_MAPPING = {{ document_purpose_mapping | tojson }};
        {% endif %}
    </script>
    <script type="module" src="/static/dist/js/main.js"></script>
</body>
</html>
```

### ステップ4.5: ビルドワークフロー

```bash
# 依存関係インストール
npm install

# 開発サーバー起動（HMR対応）
npm run dev

# 本番ビルド（app/static/distに出力）
npm run build

# 型チェックのみ
npm run typecheck
```

### ステップ4.6: 開発フロー

1. **開発時**: `npm run dev`でVite開発サーバー起動。HMRで即座に反映
2. **本番時**: `npm run build`でビルド後、FastAPIから静的ファイルとして配信
3. **CI/CD**: `npm run typecheck && npm run build`をパイプラインに追加

---

## 実装順序

| 優先度 | フェーズ | 作業内容 | 見積もり |
|-------|---------|---------|---------|
| 1 | フェーズ1 | コンポーネント分割（include） | 短時間 |
| 2 | フェーズ2 | マクロ作成・CSS整理 | 中程度 |
| 3 | フェーズ3 | Alpine.jsロジック移動 | 短時間 |
| 4 | フェーズ4 | TypeScript導入 | 中程度 |

---

## 期待される成果

### Before
- `index.html`: 187行（3画面混在）
- 同じCSSクラスが10箇所以上で重複
- 型安全性なし

### After
- `index.html`: 約10行（includeのみ）
- 各画面コンポーネント: 30-50行
- 共通CSSクラスでメンテナンス性向上
- TypeScriptによる型安全性確保

---

## 注意事項

1. **Vite開発サーバーとFastAPI**: 開発時はViteのプロキシ設定でAPIリクエストをFastAPIに転送。本番時はFastAPIが静的ファイルを配信

2. **Alpine.jsとTypeScript**: Alpine.jsは動的にメソッドを呼び出すため、型推論が効きにくい部分がある。インターフェースで明示的に型定義することで対応

3. **ビルド成果物の管理**: `app/static/dist/`はgitignoreに追加し、ビルド成果物はリポジトリに含めない

4. **テスト**: リファクタリング後、全画面の動作確認が必要

---

## 確認事項

- [ ] Node.jsのバージョン確認（v18以上推奨）
- [ ] npm/pnpm/yarnの選択
- [ ] `.gitignore`への`app/static/dist/`追加
- [ ] CI/CDへのフロントエンドビルド統合
- [ ] 開発環境のドキュメント更新（README等）

---

## 実装チェックリスト

### フェーズ1: Jinja2コンポーネント分割
- [ ] `app/templates/components/input_screen.html`作成
- [ ] `app/templates/components/output_screen.html`作成
- [ ] `app/templates/components/evaluation_screen.html`作成
- [ ] `app/templates/index.html`をinclude形式に変更
- [ ] 動作確認

### フェーズ2: Jinja2マクロ
- [ ] `app/templates/macros.html`作成
- [ ] 各コンポーネントにマクロ適用
- [ ] 動作確認

### フェーズ3: Alpine.jsロジック移動
- [ ] ヘルパー関数追加
- [ ] HTML側のロジック簡素化
- [ ] 動作確認

### フェーズ4: Vite + TypeScript + Tailwind
- [ ] `frontend/`ディレクトリ構造作成
- [ ] `package.json`作成
- [ ] `vite.config.ts`作成
- [ ] `tailwind.config.js`作成
- [ ] `postcss.config.js`作成
- [ ] `tsconfig.json`作成
- [ ] `frontend/src/types.ts`作成
- [ ] `frontend/src/app.ts`作成（既存app.jsから移植）
- [ ] `frontend/src/main.ts`作成
- [ ] `frontend/src/styles/main.css`作成
- [ ] `app/templates/base.html`更新
- [ ] `.gitignore`更新
- [ ] ビルド＆動作確認
