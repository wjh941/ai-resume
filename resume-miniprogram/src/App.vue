<script lang="ts">
export default {}
</script>

<style>
page {
  --ui-space-1: 8rpx;
  --ui-space-2: 12rpx;
  --ui-space-3: 20rpx;
  --ui-space-4: 28rpx;
  --ui-card-radius: 20rpx;
  --ui-control-radius: 12rpx;
  --ui-card-shadow: 0 8rpx 24rpx rgba(35, 78, 130, 0.06);
  --ui-card-hover-shadow: 0 12rpx 28rpx rgba(35, 78, 130, 0.12);
  --ui-motion-fast: 160ms;
  --ui-motion-base: 220ms;
  --ui-motion-slow: 320ms;
  --ui-motion-ease: cubic-bezier(0.22, 0.61, 0.36, 1);
  --ui-motion-ease-soft: cubic-bezier(0.25, 0.8, 0.25, 1);
  --ui-motion-reduced: 0ms;
  --ui-press-scale: .99;
  --ui-disabled-opacity: .56;
  --ui-disabled-bg: #edf1f5;
  --ui-disabled-color: #8a96a3;
  --ui-disabled-border: #d7dee7;
  --ui-error-bg: #fff4ef;
  --ui-error-border: #ffd7c2;
  --ui-error-color: #a93620;
  --motion-fast: var(--ui-motion-fast);
  --motion-base: var(--ui-motion-base);
  --motion-slow: var(--ui-motion-slow);
  --motion-ease: var(--ui-motion-ease);
  --ui-spinner-size-sm: 28rpx;
  --ui-spinner-size-md: 42rpx;
  --ui-spinner-size-lg: 56rpx;
  --ui-spinner-track: rgba(22, 119, 255, .18);
  --spinner-size-sm: var(--ui-spinner-size-sm);
  --spinner-size-md: var(--ui-spinner-size-md);
  --spinner-size-lg: var(--ui-spinner-size-lg);
  --spinner-track: var(--ui-spinner-track);
  --loading-block-min-height: 180rpx;
  min-width: 0;
  overflow-x: hidden;
  background: #f7f8fa;
  color: #1f2329;
  font-size: 28rpx;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
button {
  border-radius: var(--ui-control-radius);
  transition: transform var(--ui-motion-fast) var(--ui-motion-ease), background-color var(--ui-motion-fast) var(--ui-motion-ease), color var(--ui-motion-fast) var(--ui-motion-ease), border-color var(--ui-motion-fast) var(--ui-motion-ease);
}
button::after { border: 0; }
button:active:not(:disabled) { transform: translateY(1rpx) scale(var(--ui-press-scale)); }
button:focus-visible { outline: 3rpx solid rgba(22, 119, 255, .34); outline-offset: 3rpx; }
button:disabled, button[disabled], .is-disabled { cursor: not-allowed; opacity: var(--ui-disabled-opacity) !important; color: var(--ui-disabled-color) !important; border-color: var(--ui-disabled-border) !important; box-shadow: none !important; filter: saturate(.55); transform: none !important; }
button:disabled, button[disabled] { background-color: var(--ui-disabled-bg) !important; }
.card,.section,.draft { border-radius: var(--ui-card-radius) !important; box-shadow: var(--ui-card-shadow); }
@media (hover: hover) {
  .card:hover,.section:hover,.draft:hover { box-shadow: var(--ui-card-hover-shadow); }
  button:hover { transform: translateY(-1rpx); }
}
@media (prefers-reduced-motion: reduce) { button { transition: none; } button:active { transform: none; } }
.ui-loading-spinner { display: inline-flex; width: var(--ui-spinner-size-md); height: var(--ui-spinner-size-md); flex: 0 0 auto; align-items: center; justify-content: center; vertical-align: middle; }
.ui-loading-spinner-sm { width: var(--ui-spinner-size-sm); height: var(--ui-spinner-size-sm); }
.ui-loading-spinner-lg { width: var(--ui-spinner-size-lg); height: var(--ui-spinner-size-lg); }
.ui-loading-spinner-ring { display: block; width: 100%; height: 100%; box-sizing: border-box; border: 4rpx solid var(--ui-spinner-track); border-top-color: #1677ff; border-radius: 50%; animation: ui-spinner-rotate 720ms linear infinite; }
.ui-loading-block { display: flex; min-height: 72rpx; align-items: center; justify-content: center; gap: 12rpx; color: #64748b; }
.page { animation: ui-page-enter var(--motion-slow) var(--ui-motion-ease-soft) both; }
.skeleton-card, .export-skeleton, .loading-skeletons { transition: opacity var(--ui-motion-base) var(--ui-motion-ease), transform var(--ui-motion-base) var(--ui-motion-ease); }
.ui-loading-block, .loading, .empty { min-height: var(--loading-block-min-height); transition: opacity var(--motion-base) var(--motion-ease), transform var(--motion-base) var(--motion-ease); }
@keyframes ui-spinner-rotate { to { transform: rotate(360deg); } }
@keyframes ui-page-enter { from { opacity: .45; transform: translate3d(0, 10rpx, 0); } to { opacity: 1; transform: translate3d(0, 0, 0); } }
@media (prefers-reduced-motion: reduce) {
  .page { animation: none; }
  .ui-loading-spinner-ring { animation-duration: 1200ms; }
  .skeleton-card, .export-skeleton, .loading-skeletons { transition: none; }
}
.ui-error-tip { display: block; min-height: 72rpx; box-sizing: border-box; margin-top: 18rpx; padding: 18rpx 20rpx; color: var(--ui-error-color); background: var(--ui-error-bg); border: 1rpx solid var(--ui-error-border); border-radius: var(--ui-control-radius); font-size: 24rpx; line-height: 1.55; }
.ui-error-tip::before { display: inline-flex; width: 32rpx; height: 32rpx; align-items: center; justify-content: center; box-sizing: border-box; margin-right: 12rpx; content: "!"; color: var(--ui-error-color); border: 2rpx solid currentColor; border-radius: 50%; font-size: 22rpx; font-weight: 700; line-height: 1; vertical-align: middle; }
.ui-error-tip--inline { min-height: 0; margin-top: 8rpx; padding: 0; color: var(--ui-error-color); background: transparent; border: 0; font-size: 22rpx; }
.ui-error-tip--inline::before { display: none; }
.ui-long-list-item { content-visibility: auto; contain: layout paint style; contain-intrinsic-size: auto 220rpx; }
</style>
