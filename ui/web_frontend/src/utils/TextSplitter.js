export class TextSplitter {
    constructor(lang = 'zh-CN') {
        this.lang = lang;
    }

    splitText(text) {
        if (!text) return { paragraphs: [], sentences: [] };
        
        const paragraphs = this.splitIntoParagraphs(text);
        const sentences = this.extractSentences(paragraphs);
        
        return { paragraphs, sentences };
    }

    splitIntoParagraphs(text) {
        return text.split(/\n+/).filter(p => p.trim());
    }

    extractSentences(paragraphs) {
        let sentences = [];
        paragraphs.forEach(para => {
            const paraSentences = this.splitParagraphIntoSentences(para);
            sentences.push(...paraSentences);
        });
        return sentences;
    }

    splitParagraphIntoSentences(paragraph) {
        if (this.lang.startsWith('zh')) {
            return paragraph.match(/[^。！？\n]+[。！？\n]+/g) || [paragraph];
        } else {
            return paragraph.match(/[^.!?\n]+[.!?\n]+/g) || [paragraph];
        }
    }
}
