import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { storeApi } from '../api/client';
import { Badge } from '@/components/ui/badge';
import { Loader2, ExternalLink, Copy, Check, RefreshCw, ShoppingCart, ShieldCheck, X, HardDrive, Clock, Box } from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

export default function StoreDetail() {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();
    const [copiedUrl, setCopiedUrl] = useState<string | null>(null);

    const { data: store, isLoading: storeLoading } = useQuery({
        queryKey: ['store', id],
        queryFn: () => storeApi.get(id!),
        enabled: !!id,
        refetchInterval: (query: any) => {
            const data = query.state.data;
            return data?.status === 'provisioning' ? 2000 : false;
        }
    });

    const { data: logs, isLoading: logsLoading } = useQuery({
        queryKey: ['store-logs', id],
        queryFn: () => storeApi.logs(id!),
        enabled: !!id,
        refetchInterval: () => {
            return store?.status === 'provisioning' ? 2000 : false;
        }
    });

    const copyToClipboard = (text: string, type: string) => {
        navigator.clipboard.writeText(text);
        setCopiedUrl(type);
        setTimeout(() => setCopiedUrl(null), 2000);
    };

    if (storeLoading) return <div className="flex justify-center p-20"><Loader2 className="animate-spin h-10 w-10 text-blue-500" /></div>;
    if (!store) return <div className="p-8 text-center text-muted-foreground">Store not found</div>;

    const formatDate = (dateStr: string) => {
        const date = new Date(dateStr);
        return new Intl.DateTimeFormat('en-US', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            hour12: true
        }).format(date);
    };

    const getProvisioningTime = () => {
        if (store.status === 'provisioning' || store.status === 'requested' || store.status === 'provisioning_requested') {
            const start = new Date(store.created_at).getTime();
            const now = new Date().getTime();
            const diffMs = now - start;
            const mins = Math.floor(diffMs / 60000);
            const secs = Math.floor((diffMs % 60000) / 1000);
            return `Provisioning (${mins}m ${secs}s...)`;
        }

        if (store.status === 'failed') return "Failed";

        // Fallback to created_at if provisioning_started_at is missing
        const startTime = store.provisioning_started_at || store.created_at;
        // Use provisioning_completed_at primarily, then updated_at fallback for ready stores
        const endTime = store.provisioning_completed_at || (store.status === 'ready' ? store.updated_at : null);

        if (!startTime || !endTime) return "N/A";

        try {
            const start = new Date(startTime).getTime();
            const end = new Date(endTime).getTime();
            const diffMs = end - start;

            if (isNaN(diffMs) || diffMs < 0) return "N/A";

            const mins = Math.floor(diffMs / 60000);
            const secs = Math.floor((diffMs % 60000) / 1000);

            if (mins === 0 && secs === 0) return "< 1s";
            if (mins === 0) return `${secs}s`;
            return `${mins}m ${secs}s`;
        } catch (e) {
            return "N/A";
        }
    };

    return (
        <div className="min-h-screen bg-gray-50/30 py-12 px-4 sm:px-6 lg:px-8">
            <div className="max-w-3xl mx-auto bg-white rounded-2xl shadow-xl border border-gray-100 overflow-hidden relative">
                {/* Close Button */}
                <button
                    onClick={() => navigate('/')}
                    className="absolute top-6 right-6 text-gray-400 hover:text-gray-600 transition-colors"
                >
                    <X className="h-6 w-6" />
                </button>

                <div className="p-8 space-y-8">
                    {/* Header */}
                    <div className="space-y-4">
                        <div>
                            <h1 className="text-3xl font-bold text-gray-900">{store.name}</h1>
                            <p className="text-sm text-gray-400 font-mono mt-1">{store.namespace}</p>
                        </div>
                        <div className="flex items-center">
                            <div className="bg-blue-50 text-blue-600 px-4 py-1.5 rounded-full flex items-center text-xs font-bold tracking-wider">
                                <span className="h-1.5 w-1.5 rounded-full bg-blue-500 mr-2" />
                                {(store.status === 'provisioning_requested' || store.status === 'requested') ? 'PROVISIONING' : store.status.toUpperCase()}
                            </div>
                        </div>
                    </div>

                    <div className="border-t border-gray-100 pt-8 space-y-8">
                        {/* Live URLs */}
                        <div className="space-y-4">
                            <h3 className="text-[11px] font-bold text-gray-400 tracking-widest uppercase">Live URLs</h3>
                            <div className="space-y-3 bg-[#fafbfc] border border-gray-100/50 rounded-xl p-4">
                                {/* Storefront URL */}
                                <div className="flex items-center justify-between bg-white border border-gray-100 p-3 rounded-lg group shadow-sm">
                                    <div className="flex items-center flex-1 min-w-0">
                                        <ShoppingCart className="h-4 w-4 text-blue-400 mr-3 flex-shrink-0" />
                                        <span className="text-sm font-medium text-blue-500 truncate mr-4">
                                            {store.storefront_url || `http://${store.namespace}.127.0.0.1.nip.io`}
                                        </span>
                                    </div>
                                    <div className="flex items-center space-x-2">
                                        <button
                                            onClick={() => copyToClipboard(store.storefront_url || '', 'storefront')}
                                            className="p-1.5 text-gray-400 hover:bg-gray-50 rounded transition-colors"
                                        >
                                            {copiedUrl === 'storefront' ? <Check className="h-4 w-4 text-green-500" /> : <Copy className="h-4 w-4" />}
                                        </button>
                                        <a
                                            href={store.storefront_url}
                                            target="_blank"
                                            className="p-1.5 text-gray-400 hover:bg-gray-50 rounded transition-colors"
                                        >
                                            <ExternalLink className="h-4 w-4" />
                                        </a>
                                    </div>
                                </div>

                                {/* Admin URL */}
                                <div className="flex items-center justify-between bg-white border border-gray-100 p-3 rounded-lg group shadow-sm">
                                    <div className="flex items-center flex-1 min-w-0">
                                        <HardDrive className="h-4 w-4 text-gray-400 mr-3 flex-shrink-0" />
                                        <span className="text-sm font-medium text-gray-500 truncate mr-4">
                                            {store.admin_url || `http://${store.namespace}.127.0.0.1.nip.io/wp-admin`}
                                        </span>
                                    </div>
                                    <div className="flex items-center space-x-2">
                                        <button
                                            onClick={() => copyToClipboard(store.admin_url || '', 'admin-url')}
                                            className="p-1.5 text-gray-400 hover:bg-gray-50 rounded transition-colors"
                                        >
                                            {copiedUrl === 'admin-url' ? <Check className="h-4 w-4 text-green-500" /> : <Copy className="h-4 w-4" />}
                                        </button>
                                        <a
                                            href={store.admin_url}
                                            target="_blank"
                                            className="p-1.5 text-gray-400 hover:bg-gray-50 rounded transition-colors"
                                        >
                                            <ExternalLink className="h-4 w-4" />
                                        </a>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Metadata */}
                        <div className="space-y-4">
                            <h3 className="text-[11px] font-bold text-gray-400 tracking-widest uppercase">Metadata</h3>
                            <div className="grid grid-cols-2 gap-y-6 gap-x-12">
                                <div>
                                    <p className="text-[11px] text-gray-400 font-medium mb-1">Engine</p>
                                    <p className="text-sm font-bold text-gray-900 capitalize">{store.engine === 'medusa' ? 'MedusaJS' : 'WooCommerce'}</p>
                                </div>
                                <div>
                                    <p className="text-[11px] text-gray-400 font-medium mb-1">Created</p>
                                    <p className="text-sm font-bold text-gray-900">{formatDate(store.created_at)}</p>
                                </div>
                                <div>
                                    <p className="text-[11px] text-gray-400 font-medium mb-1">Provisioning Time</p>
                                    <p className="text-sm font-bold text-gray-900">{getProvisioningTime()}</p>
                                </div>
                                <div>
                                    <p className="text-[11px] text-gray-400 font-medium mb-1">Namespace</p>
                                    <p className="text-sm font-bold text-gray-400 font-mono">{store.namespace}</p>
                                </div>
                            </div>
                        </div>

                        {/* Admin Credentials */}
                        {store.admin_password && (
                            <div className="space-y-4 pt-4 border-t border-gray-100">
                                <h3 className="text-[11px] font-bold text-gray-400 tracking-widest uppercase">Admin Credentials</h3>
                                <div className="bg-green-50/40 border border-green-100 p-4 rounded-xl space-y-4">
                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="space-y-1">
                                            <p className="text-[10px] text-green-600 font-bold uppercase tracking-wider">Username</p>
                                            <div className="flex items-center justify-between bg-white border border-green-50 p-2 rounded-lg">
                                                <code className="text-xs font-mono font-bold text-green-900">admin</code>
                                                <button onClick={() => copyToClipboard('admin', 'user')} className="text-green-300 hover:text-green-600 transition-colors">
                                                    {copiedUrl === 'user' ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
                                                </button>
                                            </div>
                                        </div>
                                        <div className="space-y-1">
                                            <p className="text-[10px] text-green-600 font-bold uppercase tracking-wider">Password</p>
                                            <div className="flex items-center justify-between bg-white border border-green-50 p-2 rounded-lg">
                                                <code className="text-xs font-mono font-bold text-green-900">{store.admin_password}</code>
                                                <button onClick={() => copyToClipboard(store.admin_password!, 'pass')} className="text-green-300 hover:text-green-600 transition-colors">
                                                    {copiedUrl === 'pass' ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Activity Log */}
                        <div className="space-y-4">
                            <h3 className="text-[11px] font-bold text-gray-400 tracking-widest uppercase">Activity Log</h3>
                            <div className="space-y-2">
                                {logs && logs.length > 0 ? (
                                    logs.map((log) => (
                                        <div key={log.id} className="bg-[#fafbfc] border border-gray-100 p-4 rounded-xl flex items-center justify-between group">
                                            <div className="flex flex-col">
                                                <span className="text-sm font-bold text-gray-900">
                                                    {log.action.replace('provision.', '').replace('operator.', '').replace(/_/g, '.')}
                                                </span>
                                                <span className="text-[11px] text-gray-400 capitalize">{log.resource_type}</span>
                                            </div>
                                            <span className="text-[11px] text-gray-400">{formatDate(log.created_at)}</span>
                                        </div>
                                    ))
                                ) : (
                                    <div className="text-xs text-gray-400 italic py-4">No activity logged yet.</div>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
