import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { storeApi } from '../api/client';
import type { CreateStoreRequest } from '../types/store';
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Loader2, ShoppingCart, Layers } from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

interface CreateStoreModalProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
}

export default function CreateStoreModal({ open, onOpenChange }: CreateStoreModalProps) {
    const [name, setName] = useState('');
    const [engine, setEngine] = useState<'woocommerce' | 'medusa'>('woocommerce');
    const queryClient = useQueryClient();

    const mutation = useMutation({
        mutationFn: (data: CreateStoreRequest) => storeApi.create(data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['stores'] });
            onOpenChange(false);
            setName('');
            setEngine('woocommerce');
        },
        onError: (error) => {
            console.error('Creation failed:', error);
            alert('Failed to create store. Please check the name (lowercase/hyphens only) and try again.');
        }
    });

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        const trimmedName = name.trim().toLowerCase();
        if (!trimmedName) return;
        mutation.mutate({ name: trimmedName, engine });
    };

    return (
        <Dialog open={open} onOpenChange={(val) => {
            if (!mutation.isPending) onOpenChange(val);
        }}>
            <DialogContent className="sm:max-w-[425px]">
                <form onSubmit={handleSubmit}>
                    <DialogHeader>
                        <DialogTitle className="text-xl">Create New Store</DialogTitle>
                        <DialogDescription>
                            Provision a fresh, optimized WooCommerce instance on your cluster.
                        </DialogDescription>
                    </DialogHeader>
                    <div className="grid gap-6 py-6">
                        <div className="space-y-2">
                            <Label htmlFor="name" className="text-sm font-semibold text-gray-700">
                                Store Name
                            </Label>
                            <Input
                                id="name"
                                value={name}
                                onChange={(e) => setName(e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, '-'))}
                                className="h-10 border-gray-200 focus:ring-blue-500"
                                placeholder="e.g. fashion-store-2026"
                                required
                                disabled={mutation.isPending}
                            />
                            <p className="text-[10px] text-gray-400">Lowercase alphanumeric and hyphens only.</p>
                        </div>
                        <div className="space-y-3">
                            <Label className="text-sm font-semibold text-gray-700">
                                Ecommerce Engine
                            </Label>
                            <div className="grid grid-cols-2 gap-3">
                                <button
                                    type="button"
                                    onClick={() => setEngine('woocommerce')}
                                    disabled={mutation.isPending}
                                    className={cn(
                                        "flex flex-col items-center justify-center p-4 rounded-xl border-2 transition-all",
                                        engine === 'woocommerce'
                                            ? "border-blue-500 bg-blue-50/50 text-blue-700"
                                            : "border-gray-100 bg-white text-gray-500 hover:border-gray-200"
                                    )}
                                >
                                    <ShoppingCart className="h-6 w-6 mb-2" />
                                    <span className="text-xs font-bold">WooCommerce</span>
                                </button>
                                <button
                                    type="button"
                                    disabled={true}
                                    className="flex flex-col items-center justify-center p-4 rounded-xl border-2 border-gray-50 bg-gray-50/50 text-gray-300 cursor-not-allowed opacity-60"
                                >
                                    <Layers className="h-6 w-6 mb-2" />
                                    <span className="text-xs font-bold">MedusaJS (Soon)</span>
                                </button>
                            </div>
                        </div>
                    </div>
                    <DialogFooter className="gap-2 sm:gap-0">
                        <Button
                            type="button"
                            variant="ghost"
                            onClick={() => onOpenChange(false)}
                            disabled={mutation.isPending}
                            className="text-gray-500"
                        >
                            Cancel
                        </Button>
                        <Button
                            type="submit"
                            disabled={mutation.isPending || !name}
                            className="bg-black text-white hover:bg-black/90 h-10 px-6 rounded-lg"
                        >
                            {mutation.isPending ? (
                                <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Provisioning...</>
                            ) : (
                                "Launch Store"
                            )}
                        </Button>
                    </DialogFooter>
                </form>
            </DialogContent>
        </Dialog>
    );
}
