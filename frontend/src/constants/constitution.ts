/**
 * Constitution Articles - 헌법 5대 조항 정의
 */

export const CONSTITUTION_ARTICLES = {
    article1: {
        number: '제1조',
        title: '자본 보존 우선',
        description: '수익률보다 안전을 우선합니다. AI는 공격적 수익이 아닌 자본 보존을 최우선 목표로 합니다.',
        icon: '💎',
        color: '#4CAF50'
    },
    article2: {
        number: '제2조',
        title: '설명 가능성',
        description: '모든 AI 판단은 인간이 이해할 수 있어야 합니다. 블랙박스 결정을 금지합니다.',
        icon: '📖',
        color: '#2196F3'
    },
    article3: {
        number: '제3조',
        title: '인간 최종 결정권',
        description: 'AI는 추천만 할 수 있습니다. 모든 거래는 반드시 인간의 최종 승인이 필요합니다.',
        icon: '👤',
        color: '#FF9800'
    },
    article4: {
        number: '제4조',
        title: '강제 개입권',
        description: '시스템 위험 감지 시 AI가 강제로 개입하여 포지션을 축소할 수 있습니다.',
        icon: '🛡️',
        color: '#F44336'
    },
    article5: {
        number: '제5조',
        title: '헌법 개정 절차',
        description: '헌법 변경은 명시적 절차를 따라야 하며, 모든 개정 이력이 기록됩니다.',
        icon: '⚖️',
        color: '#9C27B0'
    }
};

export type ArticleKey = keyof typeof CONSTITUTION_ARTICLES;

export const getArticleByNumber = (articleNumber: string) => {
    return Object.values(CONSTITUTION_ARTICLES).find(
        article => article.number === articleNumber
    );
};
