import { useAbandonedCarts, useGenerateDrafts } from '../../api/useAbandonedCarts';
import type { AbandonedCart } from '../../api/useAbandonedCarts';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Skeleton } from '../../components/ui/Skeleton';
import { Link } from 'react-router-dom';

function formatCurrency(val: number) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(val);
}

function CartCard({ cart }: { cart: AbandonedCart }) {
  const { mutate, isPending } = useGenerateDrafts();
  
  const hasDrafts = cart.email_draft || cart.whatsapp_draft || cart.suggested_coupon;

  const handleGenerate = () => {
    mutate(cart.cart_token);
  };

  return (
    <Card className="p-6">
      <div className="flex flex-col sm:flex-row justify-between items-start gap-4">
        <div>
          <h3 className="text-lg font-bold text-text-main mb-1">{cart.customer_name}</h3>
          <p className="text-text-muted text-sm">{cart.email || cart.phone || 'No contact info'}</p>
          <div className="mt-3 text-sm">
            <span className="text-text-dim">Items:</span> <span className="font-medium text-text-main">{cart.items}</span>
          </div>
        </div>
        
        <div className="flex flex-col items-end gap-2">
          <div className="font-mono text-xl text-primary font-bold tracking-tight">
            {formatCurrency(cart.cart_value)}
          </div>
          <a 
            href={cart.checkout_url} 
            target="_blank" 
            rel="noreferrer"
            className="text-xs font-semibold text-secondary hover:text-primary underline underline-offset-4 transition-colors"
          >
            View Checkout
          </a>
        </div>
      </div>

      <div className="mt-6 pt-4 border-t border-[#E8E3DA]">
        {!hasDrafts ? (
          <Button 
            variant="primary" 
            onClick={handleGenerate} 
            disabled={isPending}
            className="w-full sm:w-auto"
          >
            {isPending ? 'Generating...' : 'Generate recovery drafts'}
          </Button>
        ) : (
          <div className="flex flex-col gap-4 animate-[slideInUp_0.3s_ease-out]">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-[#5c7264] uppercase tracking-wider px-2.5 py-1 bg-success/20 rounded-md border border-success/30">
                Drafts Generated
              </span>
              <Link to="/owner/approvals" className="text-sm font-semibold text-primary hover:text-primary-hover flex items-center gap-1 transition-colors">
                Review in Approvals 
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
              </Link>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-2">
              {cart.email_draft && (
                <div className="bg-background border border-[#E8E3DA] rounded-lg p-4">
                  <h4 className="text-xs font-bold text-text-muted mb-2 uppercase tracking-wide">Email Draft</h4>
                  <p className="text-sm text-text-main whitespace-pre-wrap font-serif italic">{cart.email_draft}</p>
                </div>
              )}
              {cart.whatsapp_draft && (
                <div className="bg-background border border-[#E8E3DA] rounded-lg p-4">
                  <h4 className="text-xs font-bold text-text-muted mb-2 uppercase tracking-wide">WhatsApp Draft</h4>
                  <p className="text-sm text-text-main whitespace-pre-wrap font-serif italic">{cart.whatsapp_draft}</p>
                </div>
              )}
            </div>
            
            {cart.suggested_coupon && (
              <div className="inline-flex items-center gap-2 bg-surface-lighter text-primary border border-[#E8E3DA] px-3 py-1.5 rounded-md w-fit mt-2">
                <span className="text-xs font-medium uppercase tracking-wide text-text-muted">Coupon:</span>
                <span className="font-mono font-bold text-base tracking-wider">{cart.suggested_coupon}</span>
              </div>
            )}
          </div>
        )}
      </div>
    </Card>
  );
}

export function AbandonedCartsPage() {
  const { data, isLoading } = useAbandonedCarts();
  const carts = data?.pending_carts || [];

  return (
    <div className="flex flex-col h-full bg-background">
      <div className="px-6 py-5 border-b border-[#E8E3DA] bg-background sticky top-0 z-10">
        <h1 className="text-2xl font-bold text-primary">Abandoned Carts</h1>
        <p className="text-text-muted text-sm mt-1">Recover lost revenue with AI-drafted messages</p>
      </div>

      <div className="flex-1 overflow-y-auto p-4 sm:p-6">
        <div className="max-w-3xl mx-auto flex flex-col gap-6">
          {isLoading ? (
            Array.from({ length: 2 }).map((_, i) => (
              <Card key={i} className="p-6 h-48">
                <div className="flex justify-between">
                  <div className="w-1/2">
                    <Skeleton className="w-1/2 h-6 mb-2" />
                    <Skeleton className="w-1/3 h-4" />
                  </div>
                  <Skeleton className="w-24 h-8" />
                </div>
                <div className="mt-8 pt-4 border-t border-[#E8E3DA]">
                  <Skeleton className="w-48 h-10" />
                </div>
              </Card>
            ))
          ) : carts.length === 0 ? (
            <div className="py-20 text-center">
              <div className="w-16 h-16 mx-auto rounded-full bg-surface-lighter flex items-center justify-center text-2xl mb-4 border border-[#E8E3DA] shadow-sm text-primary">
                🛒
              </div>
              <p className="text-lg font-bold text-text-main">No abandoned carts at the moment.</p>
              <p className="text-text-muted text-sm mt-1">Customers are completing their purchases!</p>
            </div>
          ) : (
            carts.map(cart => (
              <CartCard key={cart.id} cart={cart} />
            ))
          )}
        </div>
      </div>
    </div>
  );
}
