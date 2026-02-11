export interface StoreModel {
    id: string;
    name: string;
    engine: 'woocommerce' | 'medusa';
    status: 'requested' | 'provisioning' | 'ready' | 'failed' | 'deleting';
    namespace: string;
    domain?: string;
    admin_url?: string;
    admin_password?: string;
    storefront_url?: string;
    error_message?: string;
    provisioning_started_at?: string;
    provisioning_completed_at?: string;
    created_at: string;
}

export interface CreateStoreRequest {
    name: string;
    engine: 'woocommerce' | 'medusa';
}

export interface StoreResponse {
    stores: StoreModel[];
    total: number;
}

export interface AuditLogModel {
    id: string;
    action: string;
    resource_type: string;
    resource_id: string;
    created_at: string;
    metadata_?: Record<string, any>;
}

