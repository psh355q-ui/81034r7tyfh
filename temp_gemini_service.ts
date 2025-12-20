// Add to newsService.ts
export const searchTickerRealtime = async (ticker: string, maxArticles: number = 5) => {
    const response = await axios.get(`${API_BASE_URL}/news/gemini/search/ticker/${ticker}`, {
        params: { max_articles: maxArticles }
    });
    return response.data;
};

export const searchNewsRealtime = async (query: string, maxArticles: number = 5) => {
    const response = await axios.get(`${API_BASE_URL}/news/gemini/search`, {
        params: { query, max_articles: maxArticles }
    });
    return response.data;
};
