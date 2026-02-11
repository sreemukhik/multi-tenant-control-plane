import { useQuery } from '@tanstack/react-query';
import { storeApi } from '../api/client';
import { Loader2, Activity, Database, Cloud, ShieldCheck, Clock, CheckCircle2, AlertCircle } from 'lucide-react';

export default function Observability() {
    const { data: health, isPending: healthLoading } = useQuery({
        queryKey: ['health'],
        queryFn: storeApi.health,
        refetchInterval: 10000,
    });

    const { data: metrics, isPending: metricsLoading } = useQuery({
        queryKey: ['metrics'],
        queryFn: storeApi.metrics,
        refetchInterval: 10000,
    });

    if (healthLoading || metricsLoading) return <div className="flex justify-center p-10"><Loader2 className="h-8 w-8 animate-spin text-blue-500" /></div>;

    const HealthCard = ({ title, status, icon: Icon }: { title: string, status: string, icon: any }) => (
        <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm flex items-start space-x-4">
            <div className={`p-3 rounded-lg ${(status?.includes('Connected') || status?.includes('Available')) ? 'bg-green-50 text-green-600' : 'bg-red-50 text-red-600'}`}>
                <Icon className="h-6 w-6" />
            </div>
            <div>
                <p className="text-sm font-medium text-gray-500">{title}</p>
                <div className="flex items-center mt-1">
                    <p className="text-xl font-bold text-gray-900">{status}</p>
                    {status?.includes('Connected') || status?.includes('Available') ? (
                        <CheckCircle2 className="h-4 w-4 text-green-500 ml-2" />
                    ) : (
                        <AlertCircle className="h-4 w-4 text-red-500 ml-2" />
                    )}
                </div>
            </div>
        </div>
    );

    const MetricCard = ({ title, value, subtext, icon: Icon }: { title: string, value: any, subtext: string, icon: any }) => (
        <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm">
            <div className="flex items-center justify-between mb-4">
                <div className="p-2 bg-blue-50 rounded-lg text-blue-600">
                    <Icon className="h-5 w-5" />
                </div>
                <span className="text-xs font-medium text-gray-400 uppercase tracking-wider">{subtext}</span>
            </div>
            <p className="text-sm font-medium text-gray-500">{title}</p>
            <p className="text-3xl font-bold text-gray-900 mt-1">{value}</p>
        </div>
    );

    return (
        <div className="space-y-8 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <div>
                <h1 className="text-3xl font-bold tracking-tight text-foreground">Observability</h1>
                <p className="text-muted-foreground mt-2">Real-time platform health and performance metrics.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <HealthCard title="Database" status={health?.database} icon={Database} />
                <HealthCard title="Kubernetes API" status={health?.kubernetes_api} icon={Cloud} />
                <HealthCard title="Helm CLI" status={health?.helm_cli} icon={ShieldCheck} />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <MetricCard
                    title="Total Stores"
                    value={metrics?.total_stores}
                    subtext="LIFETIME"
                    icon={Activity}
                />
                <MetricCard
                    title="Avg Provisioning"
                    value={typeof metrics?.avg_provisioning_time_seconds === 'number'
                        ? `${metrics.avg_provisioning_time_seconds.toFixed(1)}s`
                        : (metrics?.avg_provisioning_time_seconds || '0.0s')}
                    subtext="PERFORMANCE"
                    icon={Clock}
                />
                <MetricCard
                    title="Success Rate"
                    value={typeof metrics?.success_rate === 'number'
                        ? `${metrics.success_rate.toFixed(0)}%`
                        : (metrics?.success_rate || '100%')}
                    subtext="STABILITY"
                    icon={CheckCircle2}
                />
                <MetricCard
                    title="Active Namespaces"
                    value={metrics?.active_namespaces}
                    subtext="RESOURCES"
                    icon={Cloud}
                />
            </div>

            <div className="bg-blue-50 border border-blue-100 p-4 rounded-lg flex items-start space-x-3">
                <ShieldCheck className="h-5 w-5 text-blue-600 mt-0.5" />
                <div>
                    <h3 className="text-sm font-bold text-blue-900">Platform Isolation Active</h3>
                    <p className="text-sm text-blue-700 mt-1">NetworkPolicies and ResourceQuotas are being enforced across all active namespaces to ensure tenant security.</p>
                </div>
            </div>
        </div>
    );
}
