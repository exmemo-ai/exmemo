export const mapTreeItem = (item) => ({
    label: item.title,
    type: item.is_folder ? 'folder' : 'file',
    id: item.id,
    addr: item.addr,
    is_folder: item.is_folder,
    need_load: item.need_load ?? false,
    children: item.is_folder && item.children ? mapTreeData(item.children) : undefined,
});

export const mapTreeData = (data) => {
    if (!Array.isArray(data)) return [];
    
    const folders = data.filter(item => item.is_folder);
    const files = data.filter(item => !item.is_folder);

    const sortByTitle = (a, b) => a.title.localeCompare(b.title);
    folders.sort(sortByTitle);
    files.sort(sortByTitle);

    return [...folders, ...files].map(mapTreeItem);
};

export const updateNodeChildren = (nodes, nodeId, mappedChildren) => {
    if (!nodes) return false;
    for (let n of nodes) {
        if (n.id === nodeId) {
            n.children = mappedChildren;
            n.need_load = false;
            return true;
        }
        if (n.children && updateNodeChildren(n.children)) {
            return true;
        }
    }
    return false;
};

export const findAndAddNode = (trees, targetId, newNode) => {
    for (let node of trees) {
        if (node.id === targetId) {
            if (!node.children) {
                node.children = [];
            }
            node.children.push(newNode);
            return true;
        }
        if (node.children) {
            if (findAndAddNode(node.children, targetId, newNode)) {
                return true;
            }
        }
    }
    return false;
};

export const findNode = (treeRef, nodeId) => {
    const traverse = (node) => {
        if (!node) return null;
        if (node.data?.id === nodeId) return node;
        return node.childNodes?.find(child => traverse(child)) || null;  
    };

    return treeRef?.root?.childNodes?.reduce((found, node) => 
        found || traverse(node), null);
};

export const findData = (treeData, nodeId, debug=false) => {
    const traverse = (nodes) => {
        if (debug) console.log('traverse', nodes);
        if (!nodes || !Array.isArray(nodes)) return false;
        for (const node of nodes) {
            if (debug) console.log('findData', node.id, nodeId);
            if (node.id === nodeId || node.addr === nodeId) return true;
            if (node.children && traverse(node.children)) return true;
        }
        return false;
    };
    return traverse(treeData);
};
