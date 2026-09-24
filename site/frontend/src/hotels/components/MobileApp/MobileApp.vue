<template>
  <div class="wrapper">
    <article>
      <div class="mobilewidget">

        <section class="description">
          <header>
            Скачайте приложение отели!
          </header>

          <ul>
            <li>Цены ниже, чем на сайте.</li>
            <li>Офлайн-доступ к совершенным бронированиям.</li>
            <li>Бесплатные интернет-звонки в службу поддержки.</li>
          </ul>
        </section>

        <div class="mobilewidget-decor"></div>

        <section class="qr-wrapper">
          <p>Отсканируйте QR-код</p>
          <div class="qr">
            <canvas width="152" height="152"></canvas>
          </div>
        </section>
      </div>
    </article>
  </div>
</template>

<script lang="ts">

</script>

<style scoped>
p {
  margin-top: 8px;
  color: #292f37;
}

.qr {
  padding: 8px;
}

canvas {
  height: 152px;
  width: 152px;

  block-size: 100%;
  inline-size: 100%;

  overflow-clip-margin: content-box;
  overflow: clip;

  background-image: url("/hotels/mobile-qr.png");
}

.qr-wrapper {
  right: 40px;
  background-color: var(--bench-surface-elevated, #fff);
  border-radius: 8px;
  text-align: center;

  display: block;
  font-size: 14px;
  position: absolute;
}

.mobilewidget-decor {
  right: 154px;
  height: 100%;
  position: absolute;
  width: 400px;
}

.mobilewidget-decor::before {
  left: 10px;
  background-image: url(/hotels/cdn/round.svg);
  background-repeat: no-repeat;
  background-size: 100%;

  content: '';
  height: 100vh;
  position: absolute;
  top: -26px;
  width: 470px;
}

.mobilewidget-decor::after {
  left: 102px;

  background-image: url(/hotels/cdn/iphone_img.png);
  background-repeat: no-repeat;
  background-size: contain;
  transform: none;

  bottom: -12px;
  content: '';
  height: 265px;
  position: absolute;
  width: 240px;
}

li {
  margin-left: 16px;
  margin-bottom: 6px;

  font-size: 16px;

  color: #292f37;
  font-family: 'PTRootUI', Verdana, sans-serif;
  font-weight: 400;
}

li::marker {
  unicode-bidi: isolate;
  font-variant-numeric: tabular-nums;
  text-transform: none;
  text-indent: 0px !important;
  text-align: start !important;
  text-align-last: auto !important;

  color: #0e41d2;
}

ul {
  font-size: 16px;

  display: block;
  list-style-type: disc;
  margin-block-start: 1em;
  margin-block-end: 1em;
  padding-inline-start: 40px;
  unicode-bidi: isolate;

  padding: 0;
  margin: 0;
}

header {
  margin-bottom: 24px;

  color: #0e41d2;
  font-family: 'Spoof';
  font-size: 32px;
  font-weight: 500;

  display: block;
  unicode-bidi: isolate;

  line-height: 1.231;
}

.description {
  max-width: 390px;

  display: block;
  unicode-bidi: isolate;
}

.wrapper {
  margin-bottom: 64px;
}

article {
  width: 100%;
}

.mobilewidget {
  background-color: #acef81;
  border-radius: 16px;
  padding: 37px 40px;

  align-items: center;
  box-sizing: border-box;
  display: flex;
  flex-direction: row;
  overflow: hidden;
  position: relative;
  width: 100%;
}
</style>