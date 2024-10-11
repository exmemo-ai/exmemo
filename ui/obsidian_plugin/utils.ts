import { App, Modal } from 'obsidian';
import { t } from "./lang/helpers"

export class ConfirmModal extends Modal {
    result: boolean | null = null;
    resolvePromise: (value: boolean) => void;
    info: string;

    constructor(app: App, info: string, resolve: (value: boolean) => void) {
        super(app);
        this.resolvePromise = resolve;
        this.info = info;
    }

    onOpen() {
        const { contentEl } = this;
        contentEl.createEl("h2", { text: t('are_you_sure') });
        const paragraph = contentEl.createEl("p", { text: this.info });

        const buttonContainer = contentEl.createDiv({ cls: "confirm-modal-buttons" });
        const yesButton = buttonContainer.createEl("button", { text: t('yes') });
        yesButton.onclick = () => {
            this.result = true;
            this.resolvePromise(true);
            this.close();
        };

        const noButton = buttonContainer.createEl("button", { text: t('no') });
        noButton.onclick = () => {
            this.result = false;
            this.resolvePromise(false);
            this.close();
        };

        buttonContainer.style.display = "flex";
        buttonContainer.style.justifyContent = "space-around";
        buttonContainer.style.marginTop = "20px";
        paragraph.style.whiteSpace = "pre-line";
        yesButton.style.marginRight = "10px";
    }

    onClose() {
        const { contentEl } = this;
        contentEl.empty();
    }
}
