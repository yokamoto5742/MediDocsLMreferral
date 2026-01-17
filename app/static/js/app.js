function appState() {
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
        error: null,
        activeTab: 0,
        tabs: ['全文', '主病名', '紹介目的', '既往歴', '症状経過', '治療経過', '現在の処方', '備考'],
        currentScreen: 'input', // 'input' or 'output'

        async init() {
            await this.updateDoctors();
        },

        async updateDoctors() {
            const response = await fetch(`/api/settings/doctors/${this.settings.department}`);
            const data = await response.json();
            this.doctors = data.doctors;
            if (!this.doctors.includes(this.settings.doctor)) {
                this.settings.doctor = this.doctors[0];
            }
        },

        startTimer() {
            this.elapsedTime = 0;
            this.timerInterval = setInterval(() => {
                this.elapsedTime++;
            }, 1000);
        },

        stopTimer() {
            clearInterval(this.timerInterval);
            this.timerInterval = null;
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
                    headers: { 'Content-Type': 'application/json' },
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

                const data = await response.json();

                if (data.success) {
                    this.result = {
                        outputSummary: data.output_summary,
                        parsedSummary: data.parsed_summary,
                        processingTime: data.processing_time,
                        modelUsed: data.model_used,
                        modelSwitched: data.model_switched
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
            this.error = null;
        },

        backToInput() {
            this.currentScreen = 'input';
            this.error = null;
        },

        async copyToClipboard(text) {
            try {
                await navigator.clipboard.writeText(text);
                alert('コピーしました');
            } catch (e) {
                alert('コピーに失敗しました');
            }
        }
    };
}
