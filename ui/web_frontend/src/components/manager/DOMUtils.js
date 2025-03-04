import { ref } from 'vue';

const HEADER_HEIGHT = 80;

const currentHighlight = ref(null);

export const getVisibleNodeList = (parentElement, startNode = null) => {
    if (parentElement) {
        const walker = document.createTreeWalker(
            parentElement,
            NodeFilter.SHOW_TEXT,
            {
                acceptNode: (node) => {
                    if (node.textContent.trim() &&
                        getComputedStyle(node.parentElement).display !== 'none' &&
                        node.parentElement.getBoundingClientRect().height > 0) {
                        return NodeFilter.FILTER_ACCEPT;
                    }
                    return NodeFilter.FILTER_REJECT;
                }
            }
        );

        const nodeList = [];
        let node;
        
        if (startNode) {
            while (node = walker.nextNode()) {
                if (node === startNode) {
                    nodeList.push(node);
                    break;
                }
            }
        } else {
            const viewportTop = window.scrollY;
            const offsetTop = viewportTop + HEADER_HEIGHT;
            
            while (node = walker.nextNode()) {
                const range = document.createRange();
                range.selectNode(node);
                const rect = range.getBoundingClientRect();
                const absoluteTop = rect.top + window.scrollY;
                if (absoluteTop >= offsetTop) {
                    nodeList.push(node);
                    break;
                }
            }
        }

        while (node = walker.nextNode()) {
            nodeList.push(node);
        }

        return nodeList;
    }
    return [];
}

export const getSelectedNodeList = (parentElement) => {
    const selection = window.getSelection();
    const text = selection.toString().trim();
    const nodeList = [];
    
    if (!text || !text.length || !parentElement) {
        return nodeList;
    }

    const range = selection.getRangeAt(0);
    const startContainer = range.startContainer;
    const endContainer = range.endContainer;
    
    if (startContainer === endContainer) {
        nodeList.push(startContainer);
        return nodeList;
    }
    
    const walker = document.createTreeWalker(
        parentElement,
        NodeFilter.SHOW_TEXT,
        {
            acceptNode: (node) => {
                if (node.textContent.trim() &&
                    getComputedStyle(node.parentElement).display !== 'none' &&
                    node.parentElement.getBoundingClientRect().height > 0) {
                    return NodeFilter.FILTER_ACCEPT;
                }
                return NodeFilter.FILTER_REJECT;
            }
        }
    );

    let inRange = false;
    let node;
    while (node = walker.nextNode()) {
        if (node === startContainer) {
            inRange = true;
        }
        if (inRange) {
            nodeList.push(node);
        }
        if (node === endContainer) {
            break;
        }
    }
    return nodeList;
}

const findScrollableParent = (element) => {
    if (!element) return null;
    
    const isScrollable = (el) => {
        const style = window.getComputedStyle(el);
        const overflow = style.getPropertyValue('overflow');
        const overflowY = style.getPropertyValue('overflow-y');
        return (overflow === 'auto' || overflow === 'scroll' || 
                overflowY === 'auto' || overflowY === 'scroll') &&
               el.scrollHeight > el.clientHeight;
    };
    
    let parent = element;
    while (parent && parent !== document.body) {
        if (isScrollable(parent)) {
            return parent;
        }
        parent = parent.parentElement;
    }
    return null;
};

export const setHighlight = (text, index, node, parentElement) => {
    if (currentHighlight.value) {
        currentHighlight.value.style.backgroundColor = ''
    }

    if (index === -1) {
        return
    }

    if (!node) {
        if (parentElement) {
            const walker = document.createTreeWalker(
                parentElement,
                NodeFilter.SHOW_TEXT,
                null
            )
            let foundNode
            while (foundNode = walker.nextNode()) {
                if (foundNode.textContent.includes(text)) {
                    node = foundNode
                    break
                }
            }
        }
    }
    
    if (node) {
        const targetElement = (node.nodeName === 'P') ? node : node.parentElement
        
        if (targetElement) {
            targetElement.style.backgroundColor = '#fffacd'
            currentHighlight.value = targetElement
            
            const scrollContainer = findScrollableParent(targetElement) || parentElement;
            const elementRect = targetElement.getBoundingClientRect();
            const containerRect = scrollContainer.getBoundingClientRect();
            const relativeTop = elementRect.top - containerRect.top;

            let isVisible;
            if (elementRect.height > containerRect.height) {
                isVisible = (
                    relativeTop >= 0 && 
                    relativeTop <= containerRect.height
                );
            } else {
                isVisible = (
                    relativeTop >= 0 && 
                    relativeTop + elementRect.height <= containerRect.height
                );
            }

            if (!isVisible) {
                const targetScroll = scrollContainer.scrollTop + relativeTop
                scrollContainer.scrollTo({
                    top: targetScroll,
                    behavior: 'smooth'
                });
            }
        }
    }
}