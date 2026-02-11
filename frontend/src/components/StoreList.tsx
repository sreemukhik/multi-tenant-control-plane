import { useQuery } from '@tanstack/react-query';
import { storeApi } from '../api/client';
import { Button } from '@/components/ui/button';
import { Plus, Loader2, Trash, Eye, Copy, HardDrive } from 'lucide-react';
import { Link } from 'react-router-dom';
import CreateStoreModal from './CreateStoreModal';
import { useState } from 'react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

export default function StoreList() {
    const { data: stores, isLoading, error, refetch } = useQuery({
        queryKey: ['stores'],
        queryFn: storeApi.list,
        refetchInterval: 5000,
    });

    const [isCreateOpen, setIsCreateOpen] = useState(false);
    const [deletingId, setDeletingId] = useState<string | null>(null);

    if (isLoading) return <div className="flex justify-center p-10"><Loader2 className="h-8 w-8 animate-spin" /></div>;
    if (error) return <div className="text-red-500">Error loading stores</div>;

    const handleDelete = async (id: string) => {
        if (!window.confirm('Are you sure you want to delete this store?')) return;
        setDeletingId(id);
        try {
            await storeApi.delete(id);
            refetch();
        } catch (err) {
            console.error('Delete failed:', err);
            alert('Failed to delete store');
        } finally {
            setDeletingId(null);
        }
    };

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

    const copyToClipboard = (text: string) => {
        navigator.clipboard.writeText(text);
    };

    return (
        <div className="space-y-8 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight text-foreground">Stores</h1>
                </div>
                <Button
                    onClick={() => setIsCreateOpen(true)}
                    className="bg-black text-white hover:bg-black/90 rounded-lg px-4 py-2 font-medium transition-all"
                >
                    <Plus className="mr-2 h-4 w-4" /> New Store
                </Button>
            </div>

            <div className="overflow-hidden bg-white border border-gray-100 rounded-xl shadow-sm">
                <table className="min-w-full divide-y divide-gray-100">
                    <thead className="bg-[#fcfcfc]">
                        <tr>
                            <th scope="col" className="px-6 py-4 text-left text-sm font-semibold text-gray-900">Store</th>
                            <th scope="col" className="px-6 py-4 text-left text-sm font-semibold text-gray-900">Status</th>
                            <th scope="col" className="px-6 py-4 text-left text-sm font-semibold text-gray-900">URLs</th>
                            <th scope="col" className="px-6 py-4 text-left text-sm font-semibold text-gray-900">Created</th>
                            <th scope="col" className="px-6 py-4 text-right text-sm font-semibold text-gray-900">Actions</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100 bg-white">
                        {stores?.length === 0 && (
                            <tr>
                                <td colSpan={5} className="px-6 py-12 text-center text-sm text-gray-500">
                                    No stores found. Create one to get started.
                                </td>
                            </tr>
                        )}
                        {stores?.map((store: import('../types/store').StoreModel) => (
                            <tr key={store.id} className="hover:bg-gray-50/50 transition-colors">
                                <td className="px-6 py-4 whitespace-nowrap">
                                    <div className="flex items-center">
                                        <div className="h-10 w-10 flex-shrink-0 bg-gray-50 rounded-lg border border-gray-100 flex items-center justify-center text-gray-400">
                                            <HardDrive className="h-5 w-5" />
                                        </div>
                                        <div className="ml-4">
                                            <div className="text-sm font-bold text-gray-900">{store.name}</div>
                                            <div className="text-xs text-gray-500 capitalize">
                                                {store.engine === 'medusa' ? 'MedusaJS' : 'WooCommerce'}
                                            </div>
                                        </div>
                                    </div>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap">
                                    <div className="flex items-center">
                                        <span className={cn(
                                            "h-2.5 w-2.5 rounded-full mr-2",
                                            store.status === 'ready' ? "bg-blue-500" :
                                                (store.status === 'provisioning' || store.status === 'provisioning_requested') ? "bg-yellow-400 animate-pulse" :
                                                    store.status === 'failed' ? "bg-red-500" : "bg-gray-300"
                                        )} />
                                        <span className="text-sm font-medium text-blue-600 capitalize">
                                            {store.status === 'ready' ? 'Ready' :
                                                (store.status === 'provisioning_requested' || store.status === 'requested') ? 'Provisioning' :
                                                    store.status}
                                        </span>
                                    </div>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap">
                                    <div className="flex items-center space-x-2">
                                        <div className="flex items-center bg-[#f7f8fa] px-3 py-1.5 rounded-md border border-gray-100 group max-w-[240px]">
                                            <span className="text-xs font-mono text-blue-400 truncate">
                                                {store.storefront_url ? store.storefront_url.replace(/^https?:\/\//, '') : `${store.namespace}.nip.io`}
                                            </span>
                                            <button
                                                onClick={() => copyToClipboard(store.storefront_url || '')}
                                                className="ml-2 text-gray-300 hover:text-gray-600 opacity-0 group-hover:opacity-100 transition-opacity"
                                            >
                                                <Copy className="h-3 w-3" />
                                            </button>
                                        </div>
                                    </div>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                    {formatDate(store.created_at)}
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-right text-sm">
                                    <div className="flex items-center justify-end space-x-3">
                                        <Link to={`/stores/${store.id}`}>
                                            <Button variant="outline" size="sm" className="bg-white border-gray-200 shadow-sm text-gray-700 h-8 rounded-md px-3 font-medium hover:bg-gray-50">
                                                <Eye className="h-3.5 w-3.5 mr-1.5" /> Details
                                            </Button>
                                        </Link>
                                        <button
                                            onClick={() => handleDelete(store.id)}
                                            disabled={deletingId === store.id}
                                            className="text-red-400 hover:text-red-600 transition-colors disabled:opacity-50"
                                        >
                                            {deletingId === store.id ? (
                                                <Loader2 className="h-4 w-4 animate-spin" />
                                            ) : (
                                                <Trash className="h-4 w-4" />
                                            )}
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            <CreateStoreModal open={isCreateOpen} onOpenChange={setIsCreateOpen} />
        </div>
    );
}
