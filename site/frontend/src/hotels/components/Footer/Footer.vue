<template>
  <div class="wrapper">

    <!-- Main -->
    <div class="main">
      <div class="apps-wrapper">
        <div class="logo-wrapper">
          <img class="logo-img" src="/hotels/cdn/logo-20240322100815.svg" alt="logo">
        </div>

        <div class="app-links">
          <div class="mobile-app-module">
            <div class="qr-module">
              <img class="qr-img" src="/hotels/mobile-qr-smaller.png" alt="qr" />
            </div>

            <div class="store-links">
              <div class="market-box">
                <img class="store-img" src="/hotels/cdn/ru.svg" alt="AppStore" >
              </div>
              <div class="market-box">
                <img class="store-img" src="/hotels/cdn/ru_a6b18f7c_1.svg" alt="GooglePlay" >
              </div>
              <div>
                <img class="store-img" src="/hotels/cdn/ru_5cb7601a_1.svg" alt="Huawei AppGallery" >
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="nav-links">
        <div>
          <p class="column-title">Компания</p>

          <ul>
            <li>
              <p class="list-text">Компания и команда</p>
            </li>

            <li>
              <p class="list-text">Контакты</p>
            </li>
            
            <li>
              <p class="list-text">Вакансии</p>
            </li>
            
            <li>
              <p class="list-text">Для прессы</p>
            </li>
          </ul>
        </div>

        <div>
          <p class="column-title">Клиентам</p>

          <ul>
            <li><p class="list-text">База знаний</p></li>
            <li><p class="list-text">Служба поддержки</p></li>
            <li><p class="list-text">Блог о путешествиях</p></li>
            <li><p class="list-text">Популярные направления</p></li>
            <li><p class="list-text">Юридическая информация</p></li>
            <li><p class="list-text">Правила бронирования</p></li>
            <li><p class="list-text">Программа лояльности GURU</p></li>
          </ul>
        </div>

        <div>
          <p class="column-title">Партнёрам</p>
        
          <ul>
            <li><p class="list-text">Объектам размещения</p></li>
            <li><p class="list-text">Турагентствам</p></li>
            <li><p class="list-text">Корпоративным клиентам</p></li>
            <li><p class="list-text">Поиск отелей на вашем сайте</p></li>
            <li><p class="list-text">Рекламодателям</p></li>
            <li><p class="list-text">Реклама и PR</p></li>
          </ul>
        </div>


        <div class="social-links">
          <img class="social-img" src="/hotels/cdn/Telegram.svg" alt="Telegram">
          <img class="social-img" src="/hotels/cdn/Dzen.svg" alt="Dzen">
          <img class="social-img" src="/hotels/cdn/Vkontakte.svg" alt="VK">
        </div>
      </div>
    </div>

    <!-- Payment security -->
    <div class="payment-security">
      <div class="pay-wrapper">

        <div>
          <p class="security-text">Безопасность платежей</p>
          <p class="security-text-2">Надёжная защита данных от ведущих платёжных систем.</p>
        </div>
        
        <div class="payment-systems">
          <div class="visa"></div>
          <div class="mastercard"></div>
          <div class="mir"></div>
          <div class="thawte"></div>
          <div class="dss"></div>
        </div>

      </div>
    </div>

    <!-- Legal -->
    <div class="legal-policy">
      <div class="inner-policy">
        <p>Политика хранения и обработки персональных данных</p>
        <p>Применяются рекомендательные технологии</p>
      </div>
    </div>

    <!-- Other -->
    <div class="other">
      <h1>Бронирование отелей и гостиниц</h1>
      <svg width="20" height="20" viewBox="0 0 20 20" fill="#292929"><path fill-rule="nonzero" d="M10.908 14.623l6.139-6.14c.5-.499.5-1.315 0-1.815l-.172-.174a1.29 1.29 0 0 0-1.817 0L10 11.553l-5.06-5.06a1.288 1.288 0 0 0-1.814 0l-.173.175c-.5.5-.5 1.316 0 1.816l6.14 6.139a1.288 1.288 0 0 0 1.815 0"></path></svg>
    </div>
  </div>
</template>

<script lang="ts">
</script>

<style scoped>
.social-img {
  block-size: 20px;
  display: block;
  inline-size: 20px;

  height: auto;
  max-width: 100%;
}

.social-links {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  place-content: start end;
}

.list-text {
  color: #868686;
  font-size: 14px;
  font-weight: 480;
  line-height: 20px;
}

li {
  -webkit-column-break-inside: avoid;
  padding-block-end: 8px;
  page-break-inside: avoid;
}

ul {
  padding: 0;
  list-style: none;
}

.column-title {
  margin: 0 0 8px;

  color: var(--bench-text, #2d3137);
  font-size: 16px;
  font-weight: 700;
  line-height: 22px;
}

.nav-links {
  display: flex;
  gap: 32px;
  justify-content: space-between;
  padding-block-end: 20px;
}

.store-img {
  /* width="130" height="auto" */

  width: 130px !important;
  height: auto !important;

  block-size: 40px;
  display: inline-block;
  inline-size: 134px;
}

.market-box {
  margin-inline-end: 6px;
  display: inline-block;
}

.qr-img {
  width: 103px !important;
  height: 103px !important;

  width: 100%;
  height: 100%;
  object-fit: contain;
  display:block;
}

.store-links {
  display: flex;
  flex-direction: column;
  inline-size: 100%;

  /* gap: 4px; */
}

.canvas-app-qr {
  block-size: 103px;
  inline-size: 100% !important;
  width: 103px !important;
  height: 103px !important;

  overflow-clip-margin: content-box !important;
  overflow: clip !important;

  background-image: url("/hotels/mobile-qr-smaller.png");
}

.qr-module {
  background-color: #f4f4f4;
  border: 1px solid #e5e5e5;
  border-radius: 16px;
  padding: 15px;

  /* block-size: 103px; */
  flex-shrink: 0;
  margin-inline-end: 8px;
}

.mobile-app-module {
  display: flex;
}

.app-links {
  padding: 20px 0;
}

.logo-img {
  background-color: transparent;
  border-radius: 4px;
  margin: -4px;
  padding: 4px;

  block-size: 100%;
  object-fit: contain;
}

.logo-wrapper {
  block-size: 36px;
  margin-block-end: 0;
  margin-block-start: 0;
  margin-inline-end: 50px;
  margin-inline-start: 0;
  max-inline-size: 250px;
}

.apps-wrapper {
  display: flex;
  flex-direction: column;
  min-inline-size: 300px;
}

.main {
  display: flex;
  inline-size: 100%;
  justify-content: space-between;
}

h1 {
  color: #868686;
  font-size: 14px;
  font-weight: 400;
  line-height: 18px;
  margin-block-end: 8px;
  margin-block-start: 8px;
  margin-inline-end: 8px;
}

svg {
  opacity: 0.6;
}

.other {
  display: flex;
  align-items: center;
}

p {
  color: #868686;
  font-size: 14px;
  line-height: 18px;
  text-decoration: none;
}

.inner-policy {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
}

.legal-policy {
  border-block-start: 1px solid #e5e5e5;
  display: flex;
  flex-direction: column;
  inline-size: 100%;
  padding-block-start: 20px;
}

.dss {
  background-image: url(/hotels/cdn/dss.svg);
  background-position: center;
  background-repeat: no-repeat;
  background-size: contain;

  block-size: 50px;
  inline-size: 81px;
  margin-inline-end: 0;
}

.thawte {
  background-image: url(/hotels/cdn/thawte.svg);
  background-position: center;
  background-repeat: no-repeat;
  background-size: contain;

  block-size: 50px;
  inline-size: 75px;
  margin-inline-end: 20px;
}

.mir {
  background-image: url(/hotels/cdn/mir.svg);
  background-position: center;
  background-repeat: no-repeat;
  background-size: contain;

  block-size: 50px;
  inline-size: 93px;
  margin-inline-end: 20px;
}

.mastercard {
  background-image: url(/hotels/cdn/mastercard.svg);
  background-position: center;
  background-repeat: no-repeat;
  background-size: contain;

  block-size: 50px;
  inline-size: 51px;
  margin-inline-end: 20px;
}

.visa {
  background-image: url(/hotels/cdn/visa.svg);
  background-position: center;
  background-repeat: no-repeat;
  background-size: contain;

  block-size: 50px;
  inline-size: 39px;
  margin-inline-end: 20px;
}

.payment-systems {
  align-items: center;
  display: flex;
  flex-wrap: wrap;
}

.security-text-2 {
  color: var(--bench-text, #2d3137);
  font-size: 14px;
  font-weight: 480;
  line-height: 20px;
}

.security-text {
  margin: 0 0 8px;

  color: var(--bench-text, #2d3137);
  font-size: 16px;
  font-weight: 700;
  line-height: 22px;
}

.pay-wrapper {
  margin-inline-end: 0;

  display: flex;
  gap: 8px;
  inline-size: 100%;
  justify-content: space-between;
}

.payment-security {
  padding: 20px 0;

  display: flex;
  inline-size: 100%;
}

.wrapper {
  margin: 0 auto;

  background-color: var(--bench-surface-elevated, #fff);
  padding: 24px 20px;

  box-sizing: content-box !important;
  display: flex;
  flex-wrap: wrap;
  position: relative;
}
</style>