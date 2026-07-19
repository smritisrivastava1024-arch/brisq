import { Link } from 'react-router-dom';
import { useAbandonedCarts, useGenerateDrafts } from '../../api/useAbandonedCarts';
import type { AbandonedCart } from '../../api/useAbandonedCarts';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Skeleton } from '../../components/ui/Skeleton';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
function formatCurrency(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(value);
}

// ---------------------------------------------------------------------------
// Skeleton loader
// ---------------------------------------------------------------------------
function CartCardSkeleton() {
  return (
    <div className="bg-white border border-parchment-dim rounded-ledger p-6 flex flex-col gap-3">
      <Skeleton className="h-5 w-1/3" />
      <Skeleton className="h-4 w-1/2" />
      <Skeleton className="h-4 w-3/5" />
      <Skeleton className="h-8 w-32 mt-2" />
    </div>
  );
}

// ---------------------------------------------------------------------------
// Drafts expansion panel — shown after generation
// ---------------------------------------------------------------------------
function DraftsPanel({ cart }: { cart: AbandonedCart }) {
  return (
    <div className="mt-5 pt-5 border-t border-parchment-dim flex flex-col gap-5">
      {cart.email_draft && (
        <div>
          <p className="text-[10px] font-semibold tracking-widest uppercase text-[#9AA0AE] mb-2">
            Email Draft
          </p>
          <pre className="text-sm font-mono text-ink-navy bg-parchment rounded-ledger p-4 whitespace-pre-wrap break-words border border-parchment-dim leading-relaxed">
            {cart.email_draft}
          </pre>
        </div>
      )}
      {cart.whatsapp_draft && (
        <div>
          <p className="text-[10px] font-semibold tracking-widest uppercase text-[#9AA0AE] mb-2">
            WhatsApp Draft
          </p>
          <pre className="text-sm font-mono text-ink-navy bg-parchment rounded-ledger p-4 whitespace-pre-wrap break-words border border-parchment-dim leading-relaxed">
            {cart.whatsapp_draft}
          </pre>
        </div>
      )}
      {cart.suggested_coupon && (
        <div>
          <p className="text-[10px] font-semibold tracking-widest uppercase text-[#9AA0AE] mb-1">
            Suggested Coupon
          </p>
          <code className="font-mono text-signal-gold font-semibold text-sm bg-[#FDF7E7] px-2.5 py-1 rounded-ledger border border-[#EAD89A]">
            {cart.suggested_coupon}
          </code>
        </div>
      )}
      <div className="pt-1">
        <Link
          to="/owner/approvals"
          className="text-sm font-semibold text-ink-navy underline underline-offset-2 hover:text-signal-gold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-signal-gold rounded-sm"
        >
          Review in Approvals →
        </Link>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Cart card
// ---------------------------------------------------------------------------
function CartCard({ cart }: { cart: AbandonedCart }) {
  const generateMutation = useGenerateDrafts();
  const hasDrafts = !!(cart.email_draft || cart.whatsapp_draft || cart.suggested_coupon);
  const isGenerating = generateMutation.isPending && generateMutation.variables === cart.cart_token;

  return (
    <Card className="bg-white p-6" hoverShadow>
      {/* Header row */}
      <div className="flex items-start justify-between gap-4 mb-4">
        <div>
          <h2 className="font-display font-semibold text-lg text-ink-navy leading-snug">
            {cart.customer_name}
          </h2>
          <p className="text-xs font-mono text-[#9AA0AE] mt-0.5">{cart.cart_token}</p>
        </div>
        <div className="text-right shrink-0">
          <p className="font-mono font-semibold text-ink-navy text-lg">
            {formatCurrency(cart.cart_value)}
          </p>
          {(cart.approved || cart.sent) && (
            <p className="text-xs text-verdigris mt-0.5">
              {cart.sent ? '✓ Sent' : '✓ Approved'}
            </p>
          )}
        </div>
      </div>

      {/* Items */}
      <div className="mb-4">
        <p className="text-[10px] font-semibold tracking-widest uppercase text-[#9AA0AE] mb-1">
          Items
        </p>
        <p className="text-sm text-[#6B6455] leading-relaxed">{cart.items}</p>
      </div>

      {/* Checkout link */}
      <div className="mb-5">
        <p className="text-[10px] font-semibold tracking-widest uppercase text-[#9AA0AE] mb-1">
          Checkout URL
        </p>
        <a
          href={cart.checkout_url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-sm font-mono text-ink-navy underline underline-offset-2 hover:text-signal-gold transition-colors break-all"
        >
          {cart.checkout_url}
        </a>
      </div>

      {/* Generate button — hidden once drafts exist */}
      {!hasDrafts && (
        <Button
          variant="secondary"
          size="sm"
          disabled={isGenerating}
          onClick={() => generateMutation.mutate(cart.cart_token)}
        >
          {isGenerating ? 'Generating drafts…' : 'Generate recovery drafts'}
        </Button>
      )}

      {/* Drafts panel — revealed after generation */}
      {hasDrafts && <DraftsPanel cart={cart} />}
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Empty state
// ---------------------------------------------------------------------------
function CartsEmpty() {
  return (
    <div className="flex flex-col items-start pt-16">
      <span className="text-3xl mb-4">🛒</span>
      <p className="font-display font-semibold text-xl text-ink-navy">
        No abandoned carts at the moment.
      </p>
      <p className="text-sm text-[#6B6455] mt-2">
        When a customer leaves checkout, their cart will appear here for review.
      </p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------
export function AbandonedCartsPage() {
  const { data, isLoading, isError } = useAbandonedCarts();
  const carts = data?.pending_carts ?? [];

  return (
    <div className="max-w-3xl mx-auto px-6 py-10">
      {/* Header */}
      <div className="mb-8">
        <h1 className="font-display font-semibold text-3xl text-ink-navy">
          Abandoned Carts
        </h1>
        <p className="text-sm text-[#6B6455] mt-1">
          Generate personalised recovery messages for customers who left without checking out.
        </p>
      </div>

      {/* Error */}
      {isError && (
        <p className="text-sm text-rust">
          Could not load abandoned carts — check that the API is running.
        </p>
      )}

      {/* Loading skeletons */}
      {isLoading && (
        <div className="flex flex-col gap-4">
          <CartCardSkeleton />
          <CartCardSkeleton />
        </div>
      )}

      {/* Empty state */}
      {!isLoading && !isError && carts.length === 0 && <CartsEmpty />}

      {/* Cart list */}
      {!isLoading && !isError && carts.length > 0 && (
        <div className="flex flex-col gap-4">
          {carts.map((cart) => (
            <CartCard key={cart.id} cart={cart} />
          ))}
        </div>
      )}
    </div>
  );
}
