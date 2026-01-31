import type {
    Settings,
    FormData,
    GenerationResult,
    EvaluationResult,
    SummaryResponse,
    EvaluationResponse,
    DoctorsResponse
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
    init(): Promise<void>;
    updateReferralPurpose(): void;
    updateDoctors(): Promise<void>;
    startTimer(): void;
    stopTimer(): void;
    generateSummary(): Promise<void>;
    clearForm(): void;
    backToInput(): void;
    backToOutput(): void;
    showEvaluation(): void;
    startEvaluationTimer(): void;
    stopEvaluationTimer(): void;
    evaluateOutput(): Promise<void>;
    copyToClipboard(text: string): Promise<void>;
    getCurrentTabContent(): string;
    copyCurrentTab(): void;
    isActiveTab(index: number): boolean;
    getTabClass(index: number): string;
}

// APIリクエスト用のヘッダーを取得
function getHeaders(additionalHeaders: Record<string, string> = {}): Record<string, string> {
    const headers: Record<string, string> = { ...additionalHeaders };
    if (window.API_KEY) {
        headers['X-API-Key'] = window.API_KEY;
    }
    return headers;
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

        async init() {
            await this.updateDoctors();
            this.updateReferralPurpose();
        },

        updateReferralPurpose() {
            if (window.DOCUMENT_PURPOSE_MAPPING && window.DOCUMENT_PURPOSE_MAPPING[this.settings.documentType]) {
                this.form.referralPurpose = window.DOCUMENT_PURPOSE_MAPPING[this.settings.documentType];
            }
        },

        async updateDoctors() {
            try {
                const response = await fetch(`/api/settings/doctors/${this.settings.department}`, {
                    headers: getHeaders()
                });
                if (!response.ok) {
                    console.error('医師リストの取得に失敗しました:', response.status, response.statusText);
                    return;
                }
                const data = await response.json() as DoctorsResponse;
                this.doctors = data.doctors;
                if (!this.doctors.includes(this.settings.doctor)) {
                    this.settings.doctor = this.doctors[0];
                }
            } catch (error) {
                console.error('医師リストの取得中にエラーが発生しました:', error);
            }
        },

        startTimer() {
            this.elapsedTime = 0;
            this.timerInterval = setInterval(() => {
                this.elapsedTime++;
            }, 1000);
        },

        stopTimer() {
            if (this.timerInterval !== null) {
                clearInterval(this.timerInterval);
                this.timerInterval = null;
            }
        },

        async generateSummary() {
            if (!this.form.medicalText.trim()) {
                this.error = 'カルテ情報を入力してください';
                return;
            }

            this.isGenerating = true;
            this.error = null;
            this.startTimer();

            try {
                const response = await fetch('/api/summary/generate', {
                    method: 'POST',
                    headers: getHeaders({ 'Content-Type': 'application/json' }),
                    body: JSON.stringify({
                        referral_purpose: this.form.referralPurpose,
                        current_prescription: this.form.currentPrescription,
                        medical_text: this.form.medicalText,
                        additional_info: this.form.additionalInfo,
                        department: this.settings.department,
                        doctor: this.settings.doctor,
                        document_type: this.settings.documentType,
                        model: this.settings.model
                    })
                });

                const data = await response.json() as SummaryResponse;

                if (data.success) {
                    this.result = {
                        outputSummary: data.output_summary || '',
                        parsedSummary: data.parsed_summary || {},
                        processingTime: data.processing_time || null,
                        modelUsed: data.model_used || '',
                        modelSwitched: data.model_switched || false
                    };
                    // 新規生成時は評価結果をクリア
                    this.evaluationResult = {
                        result: '',
                        processingTime: null
                    };
                    this.activeTab = 0;
                    this.currentScreen = 'output';
                } else {
                    this.error = data.error_message || 'エラーが発生しました';
                }
            } catch (e) {
                this.error = 'API エラーが発生しました';
            } finally {
                this.stopTimer();
                this.isGenerating = false;
            }
        },

        clearForm() {
            this.form = {
                referralPurpose: '',
                currentPrescription: '',
                medicalText: '',
                additionalInfo: ''
            };
            this.result = {
                outputSummary: '',
                parsedSummary: {},
                processingTime: null,
                modelUsed: '',
                modelSwitched: false
            };
            this.evaluationResult = {
                result: '',
                processingTime: null
            };
            this.error = null;
        },

        backToInput() {
            this.clearForm();
            this.currentScreen = 'input';
            this.error = null;
        },

        backToOutput() {
            this.currentScreen = 'output';
        },

        showEvaluation() {
            this.currentScreen = 'evaluation';
        },

        startEvaluationTimer() {
            this.evaluationElapsedTime = 0;
            this.evaluationTimerInterval = setInterval(() => {
                this.evaluationElapsedTime++;
            }, 1000);
        },

        stopEvaluationTimer() {
            if (this.evaluationTimerInterval !== null) {
                clearInterval(this.evaluationTimerInterval);
                this.evaluationTimerInterval = null;
            }
        },

        async evaluateOutput() {
            if (!this.result.outputSummary) {
                this.error = '評価対象の出力がありません';
                return;
            }

            // 既に評価結果がある場合は確認ダイアログを表示
            if (this.evaluationResult.result) {
                if (!confirm('前回の評価をクリアして再評価しますか？')) {
                    return;
                }
            }

            this.isEvaluating = true;
            this.error = null;
            this.startEvaluationTimer();

            try {
                const response = await fetch('/api/evaluation/evaluate', {
                    method: 'POST',
                    headers: getHeaders({ 'Content-Type': 'application/json' }),
                    body: JSON.stringify({
                        document_type: this.settings.documentType,
                        input_text: this.form.medicalText,
                        current_prescription: this.form.currentPrescription,
                        additional_info: this.form.additionalInfo,
                        output_summary: this.result.outputSummary
                    })
                });

                const data = await response.json() as EvaluationResponse;

                if (data.success) {
                    this.evaluationResult = {
                        result: data.evaluation_result || '',
                        processingTime: data.processing_time || null
                    };
                    this.currentScreen = 'evaluation';
                } else {
                    this.error = data.error_message || '評価中にエラーが発生しました';
                }
            } catch (e) {
                this.error = 'API エラーが発生しました';
            } finally {
                this.stopEvaluationTimer();
                this.isEvaluating = false;
            }
        },

        async copyToClipboard(text: string) {
            try {
                await navigator.clipboard.writeText(text);
                this.showCopySuccess = true;
                setTimeout(() => {
                    this.showCopySuccess = false;
                }, 2000);
            } catch (e) {
                this.error = 'テキストのコピーに失敗しました';
            }
        },

        // ヘルパー関数
        getCurrentTabContent(): string {
            if (this.activeTab === 0) {
                return this.result.outputSummary;
            }
            return this.result.parsedSummary[this.tabs[this.activeTab]] || '';
        },

        copyCurrentTab() {
            this.copyToClipboard(this.getCurrentTabContent());
        },

        isActiveTab(index: number): boolean {
            return this.activeTab === index;
        },

        getTabClass(index: number): string {
            return this.isActiveTab(index)
                ? 'border-blue-500 text-blue-600 dark:border-blue-400 dark:text-blue-400'
                : 'border-transparent text-white hover:text-gray-700 dark:hover:text-gray-300';
        }
    };
}
