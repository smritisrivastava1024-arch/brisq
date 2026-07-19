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
    <Card className="p-6 transition-all duration-300">
      <div className="flex flex-col sm:flex-row justify-between items-start gap-4">
        <div>
          <h3 className="text-lg font-bold text-text-main mb-1">{cart.customer_name}</h3>
          <p className="text-text-dim text-sm">{cart.email || cart.phone || 'No contact info'}</p>
          <div className="mt-3 text-sm">
            <span className="text-text-muted">Items:</span> <span className="font-medium text-text-main">{cart.items}</span>
          </div>
        </div>
        
        <div className="flex flex-col items-end gap-3">
          <div className="font-mono text-xl text-primary font-semibold tracking-tight">
            {formatCurrency(cart.cart_value)}
          </div>
          <a 
            href={cart.checkout_url} 
            target="_blank" 
            rel="noreferrer"
            className="text-xs text-secondary hover:text-secondary/80 underline underline-offset-2 transition-colors"
          >
            View Checkout
          </a>
        </div>
      </div>

      <div className="mt-6 pt-4 border-t border-white/10">
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
              <span className="text-xs font-bold text-success uppercase tracking-wider px-2.5 py-1 bg-success/10 rounded-full border border-success/20">
                Drafts Generated
              </span>
              <Link to="/owner/approvals" className="text-sm font-medium text-primary hover:text-primary/80 flex items-center gap-1 transition-colors">
                Review in Approvals 
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
              </Link>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {cart.email_draft && (
                <div className="bg-surface/50 border border-white/5 rounded-xl p-4">
                  <h4 className="text-xs font-bold text-text-muted mb-2 uppercase tracking-wide">Email Draft</h4>
                  <p className="text-sm text-text-main whitespace-pre-wrap font-serif italic opacity-90">{cart.email_draft}</p>
                </div>
              )}
              {cart.whatsapp_draft && (
                <div className="bg-surface/50 border border-white/5 rounded-xl p-4">
                  <h4 className="text-xs font-bold text-text-muted mb-2 uppercase tracking-wide">WhatsApp Draft</h4>
                  <p className="text-sm text-text-main whitespace-pre-wrap font-serif italic opacity-90">{cart.whatsapp_draft}</p>
                </div>
              )}
            </div>
            
            {cart.suggested_coupon && (
              <div className="inline-flex items-center gap-2 bg-primary/10 text-primary border border-primary/20 px-4 py-2 rounded-lg w-fit">
                <span className="text-xs font-medium uppercase tracking-wide opacity-80">Coupon:</span>
                <span className="font-mono font-bold text-lg tracking-wider">{cart.suggested_coupon}</span>
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
    <div className="flex flex-col h-full">
      <div className="px-6 py-5 border-b border-white/10 bg-surface/50 backdrop-blur-md sticky top-0 z-10">
        <h1 className="text-2xl font-bold">Abandoned Carts</h1>
        <p className="text-text-muted text-sm mt-1">Recover lost revenue with AI-drafted messages</p>
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-3xl mx-auto flex flex-col gap-5">
          {isLoading ? (
            Array.from({ length: 2 }).map((_, i) => (
              <Card key={i} className="p-6 h-48">
                <div className="flex justify-between">
                  <div className="w-1/2">
                    <Skeleton className="w-1/2 h-6 mb-2 bg-white/5" />
                    <Skeleton className="w-1/3 h-4 bg-white/5" />
                  </div>
                  <Skeleton className="w-24 h-8 bg-white/5" />
                </div>
                <div className="mt-8">
                  <Skeleton className="w-48 h-10 bg-white/5" />
                </div>
              </Card>
            ))
          ) : carts.length === 0 ? (
            <div className="py-20 text-center">
              <div className="w-16 h-16 mx-auto rounded-full bg-white/5 flex items-center justify-center text-2xl mb-4 border border-white/10 shadow-glass">
                🛒
              </div>
              <p className="text-lg font-medium text-text-main">No abandoned carts at the moment.</p>
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
