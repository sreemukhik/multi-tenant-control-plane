import axios from 'axios';
import type { CreateStoreRequest, StoreModel, AuditLogModel } from '../types/store';

const API_URL = '/api/v1';

export const apiClient = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

export const storeApi = {
    list: async (): Promise<StoreModel[]> => {
        const response = await apiClient.get<StoreModel[]>('/stores');
        return response.data;
    },

    get: async (id: string): Promise<StoreModel> => {
        const response = await apiClient.get<StoreModel>(`/stores/${id}`);
        return response.data;
    },

    create: async (data: CreateStoreRequest): Promise<StoreModel> => {
        const response = await apiClient.post<StoreModel>('/stores', data);
        return response.data;
    },

    delete: async (id: string): Promise<void> => {
        await apiClient.delete(`/stores/${id}`);
    },

    logs: async (id: string): Promise<AuditLogModel[]> => {
        const response = await apiClient.get<AuditLogModel[]>(`/stores/${id}/logs`);
        return response.data;
    },

    globalLogs: async (): Promise<AuditLogModel[]> => {
        const response = await apiClient.get<AuditLogModel[]>('/stores/audit-logs');
        return response.data;
    },

    health: async (): Promise<any> => {
        const response = await apiClient.get('/observability/health');
        return response.data;
    },

    metrics: async (): Promise<any> => {
        const response = await apiClient.get('/observability/metrics');
        return response.data;
    },
};
