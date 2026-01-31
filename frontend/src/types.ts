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

export interface DoctorsResponse {
    doctors: string[];
}

// グローバル変数の型宣言
declare global {
    interface Window {
        DOCUMENT_PURPOSE_MAPPING?: Record<string, string>;
        CSRF_TOKEN?: string;
    }
}
