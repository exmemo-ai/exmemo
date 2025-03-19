export class HighlightManager {
    constructor(container) {
        this.container = container;
        this.colorClasses = [
            'highlight-pink',
            'highlight-blue', 
            'highlight-yellow',
            'highlight-green',
            'highlight-purple'
        ];
        this.savedRanges = [];
    }

    addHighlight(colorIndex) {
        const selection = window.getSelection();
        if (!selection.rangeCount) return false;

        const range = selection.getRangeAt(0);
        const selectedText = range.toString().trim();
        if (!selectedText) return false;

        // Store highlight info
        this.savedRanges.push({
            text: selectedText,
            colorClass: this.colorClasses[colorIndex],
            timestamp: new Date().getTime(),
            startContainerPath: this.getNodePath(range.startContainer),
            startOffset: range.startOffset,
            endContainerPath: this.getNodePath(range.endContainer),
            endOffset: range.endOffset
        });

        // Apply highlight visually
        this.applyHighlights();
        selection.removeAllRanges();
        return true;
    }

    removeHighlight() {
        const selection = window.getSelection();
        if (!selection.rangeCount) return false;

        const range = selection.getRangeAt(0);
        const intersectingHighlights = this.findIntersectingHighlights(range);
        if (intersectingHighlights.length === 0) return false;

        intersectingHighlights.forEach(highlightElement => {
            const text = highlightElement.textContent;
            this.savedRanges = this.savedRanges.filter(range => range.text !== text);
        });
        
        this.applyHighlights();
        selection.removeAllRanges();
        return true;
    }

    findIntersectingHighlights(range) {
        const highlights = this.container.querySelectorAll('.custom-highlight');
        return Array.from(highlights).filter(highlight => {
            const highlightRange = document.createRange();
            highlightRange.selectNode(highlight);
            return range.intersectsNode(highlight);
        });
    }

    findHighlightElement(range) {
        const commonAncestor = range.commonAncestorContainer;
        return commonAncestor.nodeType === Node.TEXT_NODE 
            ? commonAncestor.parentElement?.closest('.custom-highlight')
            : commonAncestor.querySelector('.custom-highlight');
    }

    getNodePath(node) {
        const path = [];
        while (node !== this.container) {
            if (node.parentNode) {
                path.unshift(Array.from(node.parentNode.childNodes).indexOf(node));
                node = node.parentNode;
            } else {
                break;
            }
        }
        return path;
    }

    getNodeFromPath(path) {
        let node = this.container;
        for (const index of path) {
            node = node.childNodes[index];
            if (!node) return null;
        }
        return node;
    }

    clearHighlight() {
        this.savedRanges = [];
        this.applyHighlights();
    }

    applyHighlights() {
        // Remove all existing highlights
        const highlights = this.container.querySelectorAll('.custom-highlight');
        highlights.forEach(highlight => {
            const parent = highlight.parentNode;
            parent.replaceChild(document.createTextNode(highlight.textContent), highlight);
        });

        // Normalize the container to merge adjacent text nodes
        this.container.normalize();

        // Apply saved highlights
        this.savedRanges.forEach(highlightInfo => {
            try {
                const startContainer = this.getNodeFromPath(highlightInfo.startContainerPath);
                const endContainer = this.getNodeFromPath(highlightInfo.endContainerPath);
                
                if (startContainer && endContainer) {
                    const range = document.createRange();
                    range.setStart(startContainer, highlightInfo.startOffset);
                    range.setEnd(endContainer, highlightInfo.endOffset);
                    this.highlightRange(range, highlightInfo.colorClass);
                }
            } catch (error) {
                console.error('Failed to apply highlight:', error);
            }
        });
    }

    highlightRange(range, colorClass) {
        const mark = document.createElement('mark');
        mark.className = `custom-highlight ${colorClass}`;
        mark.appendChild(range.extractContents());
        range.insertNode(mark);
    }

    getHighlightedText() {
        return this.savedRanges.map(range => range.text);
    }

    hasHighlights() {
        return this.savedRanges.length > 0;
    }

    loadHighlight(meta) {
        if (!meta) return;
        
        try {
            const highlights = typeof meta.highlights === 'string' 
                ? JSON.parse(meta.highlights) 
                : meta.highlights;
            
            if (Array.isArray(highlights)) {
                this.savedRanges = highlights;
                this.applyHighlights();
            }
        } catch (error) {
            console.error('Failed to load highlights:', error);
        }
    }

    getSerializableHighlights() {
        return this.savedRanges;
    }
}
