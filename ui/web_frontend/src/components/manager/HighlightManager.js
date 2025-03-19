export class HighlightManager {
    constructor(container) {
        this.container = container;
        this.isHighlightMode = true;
        this.savedRanges = [];
        this.colorClasses = [
            'highlight-pink',
            'highlight-blue',
            'highlight-yellow',
            'highlight-green',
            'highlight-purple'
        ];
        this.currentColorIndex = 0;
    }

    clearHighlight() {
        const highlightedTexts = this.container.querySelectorAll('.custom-highlight');
        highlightedTexts.forEach(text => {
            const parent = text.parentNode;
            parent.replaceChild(document.createTextNode(text.textContent), text);
        });
        this.savedRanges = [];
    }

    getHighlightedText() {
        const highlightedTexts = this.container.querySelectorAll('.custom-highlight');
        return Array.from(highlightedTexts).map(text => text.textContent);
    }

    toggleHighlightMode() {
        this.isHighlightMode = !this.isHighlightMode;
        if (this.container) {
            this.container.setAttribute('data-highlight-mode', this.isHighlightMode);
        }
        return this.isHighlightMode;
    }

    loadHighlight(meta) {
        if (!meta || meta === 'null') return;
        
        if (typeof meta === 'string') {
            try {
                meta = JSON.parse(meta);
            } catch (error) {
                console.error('Failed to parse meta:', error);
                return;
            }
        }

        if (meta.highlights) {
            try {
                this.clearHighlight();
                const highlights = typeof meta.highlights === 'string' 
                    ? JSON.parse(meta.highlights) 
                    : meta.highlights;
                this.savedRanges = highlights;
                this.applyHighlights(highlights);
            } catch (error) {
                console.error('Failed to parse highlights:', error);
            }
        }
    }

    applyHighlights(highlights) {
        if (!highlights || !highlights.length) return;
        
        highlights.forEach(highlight => {
            const colorClass = highlight.colorClass || 'highlight-yellow';
            this.findAndHighlightText(highlight.text, colorClass);
        });
    }

    findAndHighlightText(text, colorClass = 'highlight-yellow') {
        if (!this.container) return;

        const textNodes = this.getTextNodes(this.container);
        const searchText = text.trim();

        for (const node of textNodes) {
            const nodeText = node.textContent;
            const index = nodeText.indexOf(searchText);
            if (index >= 0) {
                const range = document.createRange();
                const mark = document.createElement('mark');
                mark.className = `custom-highlight ${colorClass}`;
                
                range.setStart(node, index);
                range.setEnd(node, index + searchText.length);
                
                const selectedText = range.extractContents();
                mark.appendChild(selectedText);
                range.insertNode(mark);            
                break;
            }
        }
    }

    handleSelection(colorIndex) {
        if (colorIndex >= 0 && colorIndex < this.colorClasses.length) {
            this.currentColorIndex = colorIndex;
        }

        if (!this.isHighlightMode) return false;

        const selection = window.getSelection();
        if (!selection.rangeCount) return false;

        try {
            const range = selection.getRangeAt(0);
            const selectedText = range.toString();
            if (!selectedText.trim()) return false;

            this.savedRanges.push({
                text: selectedText,
                startOffset: range.startOffset,
                endOffset: range.endOffset,
                startContainer: range.startContainer.textContent,
                timestamp: new Date().getTime(),
                colorClass: this.colorClasses[this.currentColorIndex]
            });

            this.processHighlight(range, selection);
        } catch (error) {
            console.error('highlight failed:', error);
            return false;
        }
        return true;
    }

    processHighlight(range, selection) {
        const markElement = range.commonAncestorContainer.parentElement;
        if (markElement?.classList.contains('custom-highlight')) {
            const textContent = markElement.textContent;
            const textNode = document.createTextNode(textContent);
            markElement.parentNode.replaceChild(textNode, markElement);
            selection.removeAllRanges();
            return;
        }

        if (range.startContainer === range.endContainer && range.startContainer.nodeType === Node.TEXT_NODE) {
            this.handleSingleNodeHighlight(range);
        } else {
            this.handleMultiNodeHighlight(range);
        }
        selection.removeAllRanges();
    }

    createHighlightMark() {
        const mark = document.createElement('mark');
        mark.className = `custom-highlight ${this.colorClasses[this.currentColorIndex]}`;
        return mark;
    }

    handleSingleNodeHighlight(range) {
        const startContainer = range.startContainer;
        const mark = this.createHighlightMark();
        
        const beforeText = startContainer.textContent.substring(0, range.startOffset);
        const selectedText = startContainer.textContent.substring(range.startOffset, range.endOffset);
        const afterText = startContainer.textContent.substring(range.endOffset);
        
        const beforeNode = document.createTextNode(beforeText);
        mark.appendChild(document.createTextNode(selectedText));
        const afterNode = document.createTextNode(afterText);
        
        const parent = startContainer.parentNode;
        parent.insertBefore(beforeNode, startContainer);
        parent.insertBefore(mark, startContainer);
        parent.insertBefore(afterNode, startContainer);
        parent.removeChild(startContainer);
    }

    handleMultiNodeHighlight(range) {
        const textNodes = this.getTextNodes(range.commonAncestorContainer);
        const nodesToHighlight = textNodes.filter(node => range.intersectsNode(node));
        const startContainer = range.startContainer;
        const endContainer = range.endContainer;

        nodesToHighlight.forEach(node => {
            const mark = this.createHighlightMark();
            
            if (node === startContainer) {
                const newNode = node.splitText(range.startOffset);
                mark.appendChild(document.createTextNode(newNode.textContent));
                newNode.parentNode.replaceChild(mark, newNode);
            } else if (node === endContainer) {
                const text = node.textContent.substring(0, range.endOffset);
                node.textContent = node.textContent.substring(range.endOffset);
                mark.appendChild(document.createTextNode(text));
                node.parentNode.insertBefore(mark, node);
            } else {
                mark.appendChild(document.createTextNode(node.textContent));
                node.parentNode.replaceChild(mark, node);
            }
        });
    }

    getTextNodes(node) {
        let textNodes = [];
        if (node.nodeType === Node.TEXT_NODE) {
            textNodes.push(node);
        } else {
            node.childNodes.forEach(child => {
                textNodes = textNodes.concat(this.getTextNodes(child));
            });
        }
        return textNodes;
    }

    getSerializableHighlights() {
        return this.savedRanges.map(range => ({
            text: range.text,
            timestamp: range.timestamp,
            startOffset: range.startOffset,
            endOffset: range.endOffset,
            colorClass: range.colorClass
        }));
    }

    hasHighlights() {
        return this.savedRanges.length > 0;
    }

    removeHighlight(text) {
        this.savedRanges = this.savedRanges.filter(range => range.text !== text);
    }
}
