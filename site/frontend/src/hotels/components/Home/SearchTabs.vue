<template>
  <div class="tabsControls">
    <div class="tab tabActive" tabindex="0">Отели и квартиры</div>
    <div class="tab" tabindex="0">Трансферы</div>

    <div class="tab" rel="noreferrer">
      Для командировок
      <svg class="tabIcon" width="15" height="14" viewBox="0 0 15 14" fill="none">
        <path d="M6 4H3C1.89543 4 1 4.89543 1 6V11C1 12.1046 1.89543 13 3 13H9C10.1046 13 11 12.1046 11 11V8.5" stroke="currentColor" stroke-width="2" />
        <path d="M8 7L13.5 1.5" stroke="currentColor" stroke-width="2" />
        <path d="M9 1H14V6" stroke="currentColor" stroke-width="2" />
      </svg>
    </div>
  </div>
</template>

<style scoped>
.tabsControls {
  display: flex;
  overflow: auto hidden;
  scrollbar-width: none;
  -ms-overflow-style: none;
}
.tabsControls::-webkit-scrollbar {
  display: none;
}

.tab {
  display: inline-flex;
  align-items: center;
  flex-shrink: 0;

  height: 48px;
  padding: 0 20px;

  border-radius: 16px;
  background: var(--bench-surface-elevated, rgba(255, 255, 255, 0.9));

  color: var(--bench-text, #2d3137);
  font-size: 16px;
  font-weight: 500;
  text-decoration: none;

  opacity: 0.8;
  outline: none;
  cursor: pointer;

  margin-bottom: 8px;
  box-sizing: border-box;
}
.tab:not(:last-child) {
  margin-right: 8px;
}

.tabActive {
  opacity: 1;
  background: var(--bench-surface-elevated, #ffffff);
}

.tabIcon {
  margin-left: 8px;
  display: block;
}
</style>
