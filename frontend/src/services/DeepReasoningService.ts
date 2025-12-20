import axios from 'axios';
import { AnalyzeRequest, MarketThesis } from '../types/ReasoningTypes';

const API_BASE_URL = 'http://localhost:8001/reasoning';

export const DeepReasoningService = {
    async analyzeTicker(request: AnalyzeRequest): Promise<MarketThesis> {
        const response = await axios.post(`${API_BASE_URL}/analyze`, request);
        return response.data;
    },

    async checkHealth(): Promise<{ status: string }> {
        const response = await axios.get(`${API_BASE_URL}/health`);
        return response.data;
    }
};
