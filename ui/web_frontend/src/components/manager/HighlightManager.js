export class HighlightManager {
    constructor(container) {
        this.container = container;
        this.isHighlightMode = false;
        this.savedRanges = [];
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
            const highlights = this.container.getElementsByClassName('custom-highlight');
            Array.from(highlights).forEach(el => {
                el.style.backgroundColor = this.isHighlightMode ? 'yellow' : 'transparent';
            });
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
        
        this.clearHighlight();
        highlights.forEach(highlight => {
            this.findAndHighlightText(highlight.text);
        });
    }

    findAndHighlightText(text) {
        if (!this.container) return;

        const textNodes = this.getTextNodes(this.container);
        const searchText = text.trim();

        for (const node of textNodes) {
            const nodeText = node.textContent;
            const index = nodeText.indexOf(searchText);
            
            if (index >= 0) {
                const range = document.createRange();
                const mark = document.createElement('mark');
                mark.className = 'custom-highlight';
                
                range.setStart(node, index);
                range.setEnd(node, index + searchText.length);
                
                const selectedText = range.extractContents();
                mark.appendChild(selectedText);
                range.insertNode(mark);            
                break;
            }
        }
    }

    handleSelection() {
        if (!this.isHighlightMode) return;

        const selection = window.getSelection();
        if (!selection.rangeCount) return;

        try {
            const range = selection.getRangeAt(0);
            const selectedText = range.toString();
            if (!selectedText.trim()) return;

            this.savedRanges.push({
                text: selectedText,
                startOffset: range.startOffset,
                endOffset: range.endOffset,
                startContainer: range.startContainer.textContent,
                timestamp: new Date().getTime()
            });

            this.processHighlight(range, selection);
        } catch (error) {
            console.error('highlight failed:', error);
        }
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

    handleSingleNodeHighlight(range) {
        const startContainer = range.startContainer;
        const mark = document.createElement('mark');
        mark.className = 'custom-highlight';
        
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
            const mark = document.createElement('mark');
            mark.className = 'custom-highlight';
            
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
            endOffset: range.endOffset
        }));
    }

    hasHighlights() {
        return this.savedRanges.length > 0;
    }
}
