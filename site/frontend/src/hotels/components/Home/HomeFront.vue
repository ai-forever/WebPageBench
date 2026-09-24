<template>
  <section class="front">
    <!-- Background layer (absolute, full size) -->
    <div class="blockWrapper" aria-hidden="true">
      <div class="promo isRebranding">
        <div class="blockTitle">
          <div>
            Ооооочень много отелей
          </div>
          <div>
            и квартир!
          </div>
        </div>
        <SearchForm />
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
// import BookingWidget from './BookingWidget.vue';
import SearchForm from './SearchForm.vue';
</script>

<style scoped>
/* ====== base ====== */
.front {
  position: relative;
  overflow: visible; /* или просто убери overflow */
}

/* режем только фон, если надо */
.promo {
  overflow: visible;
  position: relative;
}

/* как в оригинале: на tablet/desktop фикс высота */
@media (min-width: 681px) {
  .front {
    height: 580px;
  }
  .front:has(.bench-date-inline) {
    height: auto;
  }
}
@media (min-width: 1075px) {
  .front {
    height: 595px !important; /* layout-rebranding variant */
    padding-bottom: 0;
  }
  .front:has(.bench-date-inline) {
    height: auto !important;
  }
}

/* ====== title ====== */
.blockTitle {
  position: relative;
  z-index: 1;

  /* mobile base */
  text-align: center;
  padding-top: 132px;
  padding-bottom: 23px;

  max-width: 1040px;
  margin-left: auto;
  margin-right: auto;
  box-sizing: border-box;

  font-family: "Spoof", "PTRootUI", Verdana, sans-serif;
  font-weight: 500;
  color: #0e41d2;
  font-size: 32px;
  line-height: 54px;
  min-height: 108px;
}

/* desktop layout-rebranding title styles */
@media (min-width: 1075px) {
  .blockTitle {
    text-align: left;
    padding-left: 20px;
    padding-right: 20px;

    padding-top:  132px;
    padding-bottom: 37px;

    font-size: 48px;
    line-height: 54px;
    min-height: 108px;
  }
}

/* ====== background wrapper ====== */
.blockWrapper {
  /* position: absolute;
  top: 0;
  bottom: 0;
  left: 0;
  right: 0; */
}

/* promo */
.promo {
  height: 550px !important;
  width: 100%;
  overflow: visible;
  position: relative;
}

.promo:has(.bench-date-inline) {
  height: auto !important;
  min-height: 550px;
  padding-bottom: 32px;
}

/* is-rebranding background */
.promo.isRebranding {
  background: #acef81;
}

/* cover: intentionally bigger (-20px) */
.cover {
  position: absolute;
  top: -20px;
  bottom: -20px;
  left: -20px;
  right: -20px;

  background-repeat: no-repeat;
  background-position: 50% 50%;
  background-size: cover;

  transform: translateX(0);
}
</style>
