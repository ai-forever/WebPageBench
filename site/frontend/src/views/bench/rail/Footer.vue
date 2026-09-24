<template>
  <footer class="rail-footer">
    <!-- Top Section with Contact Info and App -->
    <div class="footer-top-section">
      <div class="footer-contact-area">
        <div class="footer-contact-left">
          <!-- Phone Numbers -->
          <div class="contact-phones">
            <div class="phone-block">
              <a href="tel:88007750000" class="phone-number">8 800 775-00-00</a>
              <p class="phone-desc">звонок бесплатный для всех регионов РФ</p>
            </div>
          </div>
          
          <!-- Mobile App Section -->
          <div class="mobile-app-section">
            <div class="phone-block">
              <a href="tel:+74996052000" class="phone-number">+7 (499) 605-20-00</a>
              <p class="phone-desc">по всему миру, оплата в соответствии с тарифами<br>вашего оператора связи</p>
            </div>
          </div>
        </div>

        <!-- Email and App Stores -->
        <div class="email-stores-section">
          <div class="email-block">
            <a href="#" class="email-link">служба поддержки</a>
            <p class="email-desc">для вопросов, связанных с электронными билетами,<br>рекомендуем осуществлять отправку с адресов,<br>принадлежащих российским доменным зонам («.ru»)</p>
          </div>
        </div>
      </div>
      <div class="footer-app-section">            
          <span class="app-title">Железные дороги в вашем телефоне</span>
          <div class="app-preview">
              <img :src="phoneAppImage" alt="Мобильное приложение" class="phone-image" />
          </div> 
      </div>
    </div>

    <!-- Main Footer Links -->
    <div class="footer-main">
      <div class="footer-inner">
        <div class="footer-columns">
          <!-- Column 1 -->
          <div class="footer-col">
            <h4>ПАССАЖИРАМ</h4>
            <ul>
              <li><a href="#">Купить билет</a></li>
              <li><a href="#">Бонус</a></li>
              <li><a href="#">Специальные акции</a></li>
              <li><a href="#">Мобильные приложения</a></li>
              <li><a href="#">Маломобильные пассажиры</a></li>
            </ul>
          </div>

          <!-- Column 2 -->
          <div class="footer-col">
            <h4>ГРУЗОВЫЕ ПЕРЕВОЗКИ</h4>
            <ul>
              <li><a href="#">Услуги</a></li>
              <li><a href="#">Сервисы</a></li>
              <li><a href="#">География присутствия</a></li>
              <li><a href="#">Документы</a></li>
              <li><a href="#">Справочники</a></li>
              <li><a href="#">Грузы в цифрах</a></li>
            </ul>
          </div>

          <!-- Column 3 -->
          <div class="footer-col">
            <h4>О КОМПАНИИ</h4>
            <ul>
              <li><a href="#">Деятельность</a></li>
              <li><a href="#">Структура</a></li>
              <li><a href="#">Противодействие коррупции</a></li>
              <li><a href="#">Раскрытие информации</a></li>
              <li><a href="#">Раскрытие информации «Трансэнерго»</a></li>
            </ul>
            <h4 class="sub-header">ИНВЕСТОРАМ</h4>
            <h4 class="sub-header">ТЕНДЕРЫ</h4>
            <h4 class="sub-header">ВАКАНСИИ</h4>
          </div>

          <!-- Column 4 -->
          <div class="footer-col">
            <h4>КОНТАКТЫ КОМПАНИИ</h4>
            <ul>
              <li><a href="#">RSS каналы</a></li>
              <li><a href="#">Подписка</a></li>
            </ul>
            <h4 class="sub-header">ВИРТУАЛЬНАЯ ПРИЕМНАЯ</h4>
            <h4 class="sub-header">ОПРОСЫ</h4>
            <h4 class="sub-header">СООБЩИТЬ ОБ ОШИБКЕ</h4>
            <h4 class="sub-header">О САЙТЕ</h4>
            <h4 class="sub-header small">О ПРОТИВОДЕЙСТВИИ<br>МОШЕННИЧЕСТВУ</h4>
            <h4 class="sub-header">ВСЕ САЙТЫ ПОРТАЛА</h4>
            <ul class="policies">
              <li><a href="#">Политика обработки персональных данных в оператор</a></li>
              <li><a href="#">Политика использования cookie-файлов</a></li>
            </ul>
          </div>
        </div>
      </div>
    </div>

    <!-- Bottom Section -->
    <div class="footer-bottom">
      <div class="footer-bottom-inner">
        <div class="copyright">
          <p>© оператор, 2003 - 2026</p>
        </div>
        <div class="legal-info">
          <p>Свидетельство о регистрации СМИ Эл.№ФС77-25927</p>
          <p>При использовании любых материалов ссылка на источник обязательна</p>
        </div>
        <div class="social-links">
          <a href="#" class="social-icon" title="OK">
            <v-icon size="24">mdi-odnoklassniki</v-icon>
          </a>
          <a href="#" class="social-icon" title="Telegram">
            <v-icon size="24">mdi-send</v-icon>
          </a>
        </div>
      </div>
    </div>
  </footer>
</template>

<script>
import { railAssets } from "@/assets/rail-assets.js";

export default {
  name: "RailFooter",
  computed: {
    phoneAppImage() {
      return railAssets['phone_app'] || '';
    }
  }
};
</script>
