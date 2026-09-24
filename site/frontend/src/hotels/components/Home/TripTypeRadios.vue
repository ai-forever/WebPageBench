<template>
  <div class="line">
    <div class="tripType">
      <div class="group">
        <label class="label">
          <div class="container">
            <input class="input" type="radio" name="tripType" value="tourism_trip" checked />
            <span class="icon"></span>
            <span class="text"><span>Отдых</span></span>
          </div>
        </label>

        <label class="label">
          <div class="container">
            <input class="input" type="radio" name="tripType" value="business_trip" />
            <span class="icon"></span>
            <span class="text"><span>Работа</span></span>
          </div>
        </label>
      </div>
    </div>
  </div>
</template>

<style scoped>
.line {
  display: flex;
  flex-wrap: wrap;
  inline-size: 100%;
  justify-content: space-between;
}

.tripType {
  margin: 10px;
  flex-grow: 1;
  line-height: 18px;
}

.group {
  display: inline-flex;
}

.group .label:not(:last-child) {
  margin-inline-end: 20px;
}

.label {
  display: inline-block;
  vertical-align: baseline;
  font-size: 16px;
  line-height: 20px;
}

.container {
  display: flex;
  align-items: flex-start;
  cursor: pointer;
  padding: 3px 0;
  position: relative;
}

/* hidden native input */
.input {
  position: absolute;
  inline-size: 1px;
  block-size: 1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
  margin: -1px;
  padding: 0;
  border: 0;
}

/* circle */
.icon {
  block-size: 16px;
  inline-size: 16px;
  box-sizing: border-box;
  border-radius: 100%;

  background: var(--bench-surface-elevated, #fff);
  border: 1px solid rgba(41, 47, 55, 0.25);

  margin-block-start: 1px;
  transition: border-color 0.16s ease, box-shadow 0.16s ease;
}

/* hover */
.container:hover .icon {
  border-color: rgba(14, 65, 210, 0.55);
}

/* checked: “бублик” */
.input:checked + .icon {
  background: var(--bench-surface-elevated, #fff);
  border: 4px solid #0e41d2;
}

/* text */
.text {
  display: inline-block;
  flex: 1 1 auto;
  margin-inline-start: 8px;
  line-height: 16px;
  color: #292f37;
  font-size: 13px;
  font-family: PTRootUI, sans-serif;
}
</style>
