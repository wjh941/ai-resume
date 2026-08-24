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
  --ui-motion-ease: cubic-bezier(0.16, 1, 0.3, 1);
  --ui-motion-reduced: 0ms;
  --ui-spinner-size-sm: 28rpx;
  --ui-spinner-size-md: 42rpx;
  --ui-spinner-size-lg: 56rpx;
  --ui-spinner-track: rgba(22, 119, 255, .18);
  min-width: 0;
  overflow-x: hidden;
  background: #f7f8fa;
  color: #1f2329;
  font-size: 28rpx;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
button {
  border-radius: var(--ui-control-radius);
  transition: transform var(--ui-motion-fast) var(--ui-motion-ease), box-shadow var(--ui-motion-fast) var(--ui-motion-ease), background-color var(--ui-motion-fast) var(--ui-motion-ease), color var(--ui-motion-fast) var(--ui-motion-ease), border-color var(--ui-motion-fast) var(--ui-motion-ease);
}
button::after { border: 0; }
button:active { transform: translateY(1rpx) scale(.985); }
button:focus-visible { outline: 3rpx solid rgba(22, 119, 255, .34); outline-offset: 3rpx; }
button[disabled] { cursor: not-allowed; opacity: .6; transform: none; }
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
.page { animation: ui-page-enter var(--ui-motion-slow) var(--ui-motion-ease) both; }
.skeleton-card, .export-skeleton, .loading-skeletons { transition: opacity var(--ui-motion-base) var(--ui-motion-ease), transform var(--ui-motion-base) var(--ui-motion-ease); }
@keyframes ui-spinner-rotate { to { transform: rotate(360deg); } }
@keyframes ui-page-enter { from { opacity: .45; transform: translateY(10rpx); } to { opacity: 1; transform: translateY(0); } }
@media (prefers-reduced-motion: reduce) {
  .page { animation: none; }
  .ui-loading-spinner-ring { animation-duration: 1200ms; }
  .skeleton-card, .export-skeleton, .loading-skeletons { transition: none; }
}
</style>
