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
  --ui-motion-ease: cubic-bezier(0.16, 1, 0.3, 1);
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
button:active { transform: translateY(0) scale(.985); }
button:focus-visible { outline: 3rpx solid rgba(22, 119, 255, .34); outline-offset: 3rpx; }
button[disabled] { cursor: not-allowed; opacity: .6; transform: none; }
.card,.section,.draft { border-radius: var(--ui-card-radius) !important; box-shadow: var(--ui-card-shadow); }
@media (hover: hover) {
  .card:hover,.section:hover,.draft:hover { box-shadow: var(--ui-card-hover-shadow); }
  button:hover { transform: translateY(-1rpx); }
}
@media (prefers-reduced-motion: reduce) { button { transition: none; } button:active { transform: none; } }
</style>
