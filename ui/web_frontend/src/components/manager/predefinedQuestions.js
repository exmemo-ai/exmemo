export const getPolishQuestions = (t) => [
    {
        id: 'polish',
        label: t('aiDialog.commonQuestions.polish'),
        question: '请帮我润色这段文字，要求：\n' +
                    '1. 保持原意的基础上使表达更加优美\n' +
                    '2. 调整句式使其更加通顺\n' +
                    '3. 选用更恰当的词语\n' +
                    '4. 改善语言的连贯性\n' +
                    '5. 突出重点，清晰表达'
    },
    {
        id: 'correct',
        label: t('aiDialog.commonQuestions.correct'), 
        question: '请检查这段文字中的问题：\n' +
                    '1. 标点符号使用是否正确\n' +
                    '2. 是否存在语法错误\n' +
                    '3. 是否有不恰当的表达\n' +
                    '4. 是否存在逻辑矛盾\n' +
                    '5. 给出修改建议'
    }
];

export const getSummaryQuestions = (t) => [
    {
        id: 'summary',
        label: t('aiDialog.commonQuestions.summary'),
        question: '请帮我总结这段内容：\n' +
                    '1. 提取核心观点和主要论述\n' +
                    '2. 概括文章的主要内容\n' +
                    '3. 保持逻辑清晰，层次分明\n' +
                    '4. 突出重点，简明扼要\n' +
                    '5. 添加合适的小标题'
    },
    { 
        id: 'conclusion',
        label: t('aiDialog.commonQuestions.conclusion'),
        question: '请帮我写一个结语，要求：\n' +
                    '1. 总结文章的核心观点\n' +
                    '2. 提炼文章的价值和意义\n' +
                    '3. 对内容进行升华和延伸\n' +
                    '4. 语言要优美流畅\n' +
                    '5. 结尾要有深度和启发性'
    },
    {
        id: 'abstract',
        label: t('aiDialog.commonQuestions.abstract'),
        question: '请帮我写一段摘要，要求：\n' +
                    '1. 概述文章的主要内容\n' +
                    '2. 点明研究方法或论述思路\n' +
                    '3. 突出创新点或主要发现\n' +
                    '4. 控制在300字以内\n' +
                    '5. 使用准确、简洁的语言'
    }
];

export const getGenerateQuestions = (t) => [
    {
        id: 'generateArticle',
        label: t('aiDialog.commonQuestions.generate'),
        question: '请基于以下内容，生成一篇1200-1500字的公众号文章，要求：\n' +
                 '1. 使用markdown格式，包含一至两级标题\n' +
                 '2. 结构要求：\n' +
                 '   - 开头要吸引人，占10%\n' +
                 '   - 简要介绍背景，占10%\n' +
                 '   - 主要故事描述，占50%\n' +
                 '   - 痛点分析，占20%\n' +
                 '   - 方法论总结，占10%\n' +
                 '   - 结语点题升华\n' +
                 '3. 语言要生动活泼，适合公众号阅读\n' +
                 '4. 分段要合理，每段200-300字左右'
    },
    {
        id: 'outline',
        label: t('aiDialog.commonQuestions.outline'),
        question: '请基于内容生成一个详细的文章大纲，要求：\n' +
                 '1. 使用markdown格式\n' +
                 '2. 包含标题和副标题\n' +
                 '3. 列出每个部分的主要内容要点\n' +
                 '4. 按照故事叙述、分析、总结的逻辑展开'
    }
];

export const getStyleQuestions = (t) => [
    {
        id: 'wechat',
        label: t('aiDialog.commonQuestions.styleWechat'),
        question: '请将这段内容改写成公众号风格，要求：\n' +
                 '1. 标题吸引人，有吸引力\n' +
                 '2. 语言生动活泼，口语化\n' +
                 '3. 多用比喻和例子\n' +
                 '4. 适当添加表情符号\n' +
                 '5. 段落简短，易于阅读'
    },
    {
        id: 'xiaohongshu',
        label: t('aiDialog.commonQuestions.styleXiaohongshu'),
        question: '请将这段内容改写成小红书风格，要求：\n' +
                 '1. 标题要有爆点\n' +
                 '2. 语言要亲切自然\n' +
                 '3. 多用emoji表情\n' +
                 '4. 分点列举要清晰\n' +
                 '5. 结尾互动感强'
    },
    {
        id: 'technical',
        label: t('aiDialog.commonQuestions.styleTechnical'),
        question: '请将这段内容改写成技术文风格，要求：\n' +
                 '1. 语言严谨专业\n' +
                 '2. 逻辑结构清晰\n' +
                 '3. 适当使用专业术语\n' +
                 '4. 多用数据和事实支撑\n' +
                 '5. 注重实用性和可操作性'
    },
    {
        id: 'concise',
        label: t('aiDialog.commonQuestions.styleConcise'),
        question: '请将这段内容改写成简洁风格，要求：\n' +
                 '1. 语言精炼\n' +
                 '2. 去除冗余词句\n' +
                 '3. 突出核心信息\n' +
                 '4. 用最少的词表达最多的信息\n' +
                 '5. 保持文章结构清晰'
    },
    {
        id: 'elegant',
        label: t('aiDialog.commonQuestions.styleElegant'),
        question: '请将这段内容改写成优美文学风格，要求：\n' +
                 '1. 用词优美讲究\n' +
                 '2. 句式灵活多变\n' +
                 '3. 意境优美\n' +
                 '4. 适当使用修辞手法\n' +
                 '5. 文字富有韵律感'
    },
    {
        id: 'emotional',
        label: t('aiDialog.commonQuestions.styleEmotional'),
        question: '请将这段内容改写成感性风格，要求：\n' +
                 '1. 多描写情感体验\n' +
                 '2. 增加感性的细节\n' +
                 '3. 使用感情色彩丰富的词语\n' +
                 '4. 营造共鸣感\n' +
                 '5. 突出人文关怀'
    },
    {
        id: 'objective',
        label: t('aiDialog.commonQuestions.styleObjective'),
        question: '请将这段内容改写成理性客观风格，要求：\n' +
                 '1. 语言客观中立\n' +
                 '2. 多用数据和事实\n' +
                 '3. 避免主观评价\n' +
                 '4. 逻辑推理严密\n' +
                 '5. 保持专业性和权威性'
    }
];

export const getBasicQuestions = (t) => [
  {
    id: 'summary',
    label: t('aiDialog.commonQuestions.summary'),
    question: '请总结这段内容的主要观点。'
  },
  {
    id: 'translate',
    label: t('aiDialog.commonQuestions.translate'),
    question: '请将内容翻译成中文。'
  },
];
