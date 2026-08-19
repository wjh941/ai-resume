<script lang="ts">
export default {}
</script>

<style>
page {
  --ui-card-radius: 16rpx;
  --ui-control-radius: 12rpx;
  --ui-card-shadow: 0 8rpx 24rpx rgba(35, 78, 130, 0.06);
  --ui-card-hover-shadow: 0 12rpx 28rpx rgba(35, 78, 130, 0.12);
  min-width: 0;
  overflow-x: hidden;
  background: #f7f8fa;
  color: #1f2329;
  font-size: 28rpx;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
button { border-radius: var(--ui-control-radius); transition: transform .16s ease, box-shadow .16s ease, background-color .16s ease; }
button::after { border: 0; }
.card,.section,.draft { border-radius: var(--ui-card-radius) !important; box-shadow: var(--ui-card-shadow); }
@media (hover: hover) {
  .card:hover,.section:hover,.draft:hover { box-shadow: var(--ui-card-hover-shadow); }
  button:hover { transform: translateY(-1rpx); }
}
@media (prefers-reduced-motion: reduce) { button { transition: none; } }
</style>
