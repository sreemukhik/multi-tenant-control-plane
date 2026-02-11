import { useQuery } from '@tanstack/react-query';
import { storeApi } from '../api/client';
import { Loader2, Shield, User, Server, AlertTriangle, Globe } from 'lucide-react';

export default function AuditLogView() {
    const { data: logs, isPending: isLoading, error } = useQuery({
        queryKey: ['global-audit-logs'],
        queryFn: storeApi.globalLogs,
        refetchInterval: 10000,
    });

    if (isLoading) return <div className="flex justify-center p-10"><Loader2 className="h-8 w-8 animate-spin text-blue-500" /></div>;
    if (error) return <div className="text-red-500 p-10">Error loading audit logs.</div>;

    const formatDate = (dateStr: string) => {
        const date = new Date(dateStr);
        return new Intl.DateTimeFormat('en-US', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: true
        }).format(date);
    };

    const getActionIcon = (action: string) => {
        if (action?.includes('error') || action?.includes('failed')) return <AlertTriangle className="h-4 w-4 text-red-500" />;
        if (action?.includes('user.')) return <User className="h-4 w-4 text-blue-500" />;
        if (action?.includes('quota')) return <Shield className="h-4 w-4 text-orange-500" />;
        return <Server className="h-4 w-4 text-gray-500" />;
    };

    return (
        <div className="space-y-8 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight text-foreground">Audit Logs</h1>
                    <p className="text-muted-foreground mt-2">Platform-level compliance and security even trail.</p>
                </div>
                <div className="flex items-center space-x-2 bg-gray-50 px-3 py-1.5 rounded-lg border border-gray-100">
                    <Shield className="h-4 w-4 text-gray-400" />
                    <span className="text-xs font-semibold text-gray-500 uppercase">Compliance Mode Active</span>
                </div>
            </div>

            <div className="overflow-hidden bg-white border border-gray-100 rounded-xl shadow-sm">
                <table className="min-w-full divide-y divide-gray-100">
                    <thead className="bg-[#fcfcfc]">
                        <tr>
                            <th scope="col" className="px-6 py-4 text-left text-sm font-semibold text-gray-900">Timestamp</th>
                            <th scope="col" className="px-6 py-4 text-left text-sm font-semibold text-gray-900">Action</th>
                            <th scope="col" className="px-6 py-4 text-left text-sm font-semibold text-gray-900">Resource</th>
                            <th scope="col" className="px-6 py-4 text-left text-sm font-semibold text-gray-900">IP Address</th>
                            <th scope="col" className="px-6 py-4 text-left text-sm font-semibold text-gray-900">Details</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100 bg-white">
                        {logs?.length === 0 && (
                            <tr>
                                <td colSpan={5} className="px-6 py-12 text-center text-sm text-gray-500">
                                    No audit logs recorded yet.
                                </td>
                            </tr>
                        )}
                        {logs?.map((log: any) => (
                            <tr key={log.id} className="hover:bg-gray-50/50 transition-colors group">
                                <td className="px-6 py-4 whitespace-nowrap text-xs text-gray-400 tabular-nums">
                                    {formatDate(log.created_at)}
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap">
                                    <div className="flex items-center space-x-2.5">
                                        <div className="flex-shrink-0">
                                            {getActionIcon(log.action)}
                                        </div>
                                        <span className="text-[13px] font-semibold text-gray-900 font-mono tracking-tight">
                                            {log.action}
                                        </span>
                                    </div>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap">
                                    <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-gray-50 text-gray-500 border border-gray-100 uppercase tracking-wider">
                                        {log.resource_type || 'platform'}
                                    </span>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-xs text-gray-500 tabular-nums">
                                    <div className="flex items-center space-x-2 bg-gray-50/50 w-fit px-2 py-1 rounded">
                                        <Globe className="h-3 w-3 text-gray-300" />
                                        <span>{log.ip_address || 'Internal'}</span>
                                    </div>
                                </td>
                                <td className="px-6 py-4 text-sm text-gray-500">
                                    <div className="max-w-[180px] truncate font-mono text-[10px] text-gray-400 group-hover:text-gray-600 transition-colors">
                                        {JSON.stringify(log.metadata_)}
                                    </div>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
