<template>
  <div class="wrapper">
    <div class="wrapper-inner">
      <!-- First row -->
      <div class="inner-top">
        <div class="partners-list">
          <div v-for="cls in topLeft" :key="cls" :class="cls"></div>
        </div>

        <div class="partners-list">
          <div v-for="cls in topRight" :key="cls" :class="cls"></div>
        </div>
      </div>

      <!-- Second row -->
      <div class="inner-bottom">
        <div class="partners-list">
          <div v-for="cls in bottomLeft" :key="cls" :class="cls"></div>
        </div>

        <div class="partners-list">
          <div v-for="cls in bottomRight" :key="cls" :class="cls"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const topLeft = ['hilton', 'radisson', 'marriot'] as const

const topRight = ['intercont', 'fourseasons', 'kempinski', 'cosmos'] as const

const bottomLeft = ['mercure', 'novotel', 'pullman', 'ibis', 'wyndham', 'jumeirah'] as const

const bottomRight = ['lotte', 'bestwestern', 'holidayinn', 'hyatt', 'belmond', 'ramada'] as const
</script>

<style scoped>
.wrapper {
  margin-bottom: 64px;
}

.wrapper-inner {
  padding: 0 40px;
}

.inner-top {
  margin-bottom: 36px;
  display: flex;
  align-items: center;
}

.inner-bottom {
  display: flex;
  align-items: center;
}

.partners-list {
  display: flex;
  align-items: center;
  width: 50%;
}

/* ====== icons (твои стили без изменений) ====== */
.hilton {
  margin-right: 44px;

  background-position: center;
  background-repeat: no-repeat;
  background-size: contain;

  height: 45px;
  width: 121px;

  background-image: url(/hotels/cdn/hilton.svg);
}

.radisson {
  margin-right: 44px;

  background-position: center;
  background-repeat: no-repeat;
  background-size: contain;

  height: 35px;
  width: 144px;

  background-image: url(/hotels/cdn/radisson.svg);
}

.marriot {
  margin-right: 44px;

  background-position: center;
  background-repeat: no-repeat;
  background-size: contain;

  height: 56px;
  width: 71px;

  background-image: url(/hotels/cdn/marriott.svg);
}

.intercont {
  margin-right: 44px;

  background-position: center;
  background-repeat: no-repeat;
  background-size: contain;

  height: 54px;
  width: 138px;

  background-image: url(/hotels/cdn/intercontinental.svg);
}

.fourseasons {
  margin-right: 44px;

  background-position: center;
  background-repeat: no-repeat;
  background-size: contain;

  height: 64px;
  width: 139px;

  background-image: url(/hotels/cdn/fourseasons.svg);
}

.kempinski {
  margin-right: 44px;

  background-position: center;
  background-repeat: no-repeat;
  background-size: contain;

  height: 55px;
  width: 136px;

  background-image: url(/hotels/cdn/kempinski.svg);
}

.cosmos {
  background-position: center;
  background-repeat: no-repeat;
  background-size: contain;

  height: 64px;
  width: 139px;

  background-image: url(/hotels/cdn/cosmos.svg);
}

/* --- */
.mercure {
  margin-right: 25px;

  background-position: center;
  background-repeat: no-repeat;
  background-size: contain;

  height: 17px;
  width: 71px;

  background-image: url(/hotels/cdn/mercure.svg);
}

.novotel {
  margin-right: 22px;

  background-position: center;
  background-repeat: no-repeat;
  background-size: contain;

  height: 9px;
  width: 68px;

  background-image: url(/hotels/cdn/novotel.svg);
}

.pullman {
  margin-right: 21px;

  background-position: center;
  background-repeat: no-repeat;
  background-size: contain;

  height: 16px;
  width: 100px;

  background-image: url(/hotels/cdn/pullman.svg);
}

.ibis {
  margin-right: 18px;

  background-position: center;
  background-repeat: no-repeat;
  background-size: contain;

  height: 13px;
  width: 24px;

  background-image: url(/hotels/cdn/ibis.svg);
}

.wyndham {
  margin-right: 16px;

  background-position: center;
  background-repeat: no-repeat;
  background-size: contain;

  height: 18px;
  width: 82px;

  background-image: url(/hotels/cdn/wyndham.svg);
}

.jumeirah {
  margin-right: 17px;

  background-position: center;
  background-repeat: no-repeat;
  background-size: contain;

  height: 20px;
  width: 74px;

  background-image: url(/hotels/cdn/jumeirah.svg);
}

.lotte {
  margin-right: 19px;

  background-position: center;
  background-repeat: no-repeat;
  background-size: contain;

  height: 23px;
  width: 50px;

  background-image: url(/hotels/cdn/lotte.svg);
}

.bestwestern {
  margin-right: 16px;

  background-position: center;
  background-repeat: no-repeat;
  background-size: contain;

  height: 19px;
  width: 91px;

  background-image: url(/hotels/cdn/bestwestern.svg);
}

.holidayinn {
  margin-right: 23px;

  background-position: center;
  background-repeat: no-repeat;
  background-size: contain;

  height: 17px;
  width: 73px;

  background-image: url(/hotels/cdn/holidayinn.svg);
}

.hyatt {
  margin-right: 19px;

  background-position: center;
  background-repeat: no-repeat;
  background-size: contain;

  height: 12px;
  width: 55px;

  background-image: url(/hotels/cdn/hyatt.svg);
}

.belmond {
  margin-right: 24px;

  background-position: center;
  background-repeat: no-repeat;
  background-size: contain;

  height: 22px;
  width: 54px;

  background-image: url(/hotels/cdn/belmond.svg);
}

.ramada {
  background-position: center;
  background-repeat: no-repeat;
  background-size: contain;

  height: 17px;
  width: 59px;

  background-image: url(/hotels/cdn/ramada.svg);
}
</style>
