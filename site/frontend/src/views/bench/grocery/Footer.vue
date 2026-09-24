<template>
  <div class="grocery-footer">
    <!-- App Download Section -->
    <div class="footer-top">
      <div class="download-apps">
        <img v-for="badge in appBadges" :key="badge.alt" class="app-badge" :src="badge.src" :alt="badge.alt" />
      </div>
      <div class="social-links">
        <a href="#" aria-label="TikTok">
          <div class="Icon_icon__WhKMY" aria-hidden="true" style="height: 32px;">
            <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="none" viewBox="0 0 32 32"><g clip-path="url(#clip0_21209_241504)"><path fill="#E0E0E0" d="M0 15.333C0 8.105 0 4.491 2.246 2.246 4.49 0 8.106 0 15.333 0h1.334c7.228 0 10.842 0 13.087 2.246C32 4.49 32 8.106 32 15.333v1.334c0 7.228 0 10.842-2.245 13.087C27.509 32 23.895 32 16.667 32h-1.334c-7.228 0-10.842 0-13.087-2.245C0 27.509 0 23.895 0 16.667z"></path><path fill="#595959" fill-rule="evenodd" d="M19.891 12.686a8.2 8.2 0 0 0 4.774 1.527v-2.695a4.8 4.8 0 0 1-2.534-1.453 4.8 4.8 0 0 1-2.187-3.234h-2.496v13.676a2.896 2.896 0 0 1-5.202 1.743 2.895 2.895 0 0 1 2.182-5.346V14.18a6.33 6.33 0 0 0-4.394 10.752 6.3 6.3 0 0 0 3.525 1.07 6.33 6.33 0 0 0 6.332-6.328z" clip-rule="evenodd"></path><path fill="#595959" fill-rule="evenodd" d="M24.665 11.518v-.73a4.77 4.77 0 0 1-2.534-.723 4.8 4.8 0 0 0 2.534 1.453M19.944 6.83a5 5 0 0 1-.053-.393v-.44h-3.446v13.676a2.896 2.896 0 0 1-4.2 2.576 2.896 2.896 0 0 0 5.202-1.743V6.83zm-5.516 7.349v-.776a6.33 6.33 0 0 0-7.201 6.27 6.32 6.32 0 0 0 2.807 5.258 6.33 6.33 0 0 1 4.394-10.752" clip-rule="evenodd"></path></g><defs><clipPath id="clip0_21209_241504"><rect width="32" height="32" fill="#fff" rx="6"></rect></clipPath></defs></svg>
          </div>
        </a>
        <a href="#" aria-label="ВКонтакте">
          <div class="Icon_icon__WhKMY" aria-hidden="true" style="height: 32px;">
            <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="none" viewBox="0 0 32 32"><g clip-path="url(#clip0_21209_241507)"><path fill="#E0E0E0" d="M0 15.333C0 8.105 0 4.491 2.246 2.246 4.492 0 8.106 0 15.334 0h1.333c7.228 0 10.842 0 13.088 2.246s2.246 5.86 2.246 13.087v1.334c0 7.228 0 10.842-2.246 13.087C27.51 32 23.895 32 16.667 32h-1.333c-7.228 0-10.842 0-13.088-2.245S0 23.895 0 16.667z"></path><path fill="#595959" fill-rule="evenodd" d="M8.134 10H5.8c-.667 0-.8.314-.8.66 0 .618.791 3.683 3.684 7.737 1.929 2.769 4.646 4.27 7.119 4.27 1.483 0 1.667-.334 1.667-.908v-2.092c0-.667.14-.8.61-.8.346 0 .94.173 2.324 1.508 1.583 1.582 1.843 2.292 2.733 2.292h2.334c.667 0 1-.334.808-.992-.21-.655-.966-1.606-1.968-2.734-.544-.643-1.36-1.335-1.607-1.68-.346-.446-.248-.644 0-1.04 0 0 2.843-4.004 3.14-5.363.148-.495 0-.858-.706-.858h-2.334c-.593 0-.867.314-1.015.66 0 0-1.187 2.892-2.868 4.77-.544.545-.792.718-1.088.718-.149 0-.363-.173-.363-.668v-4.622c0-.594-.173-.858-.667-.858h-3.668c-.37 0-.594.275-.594.536 0 .563.841.693.928 2.274v3.437c0 .753-.136.89-.433.89-.791 0-2.716-2.906-3.857-6.23C8.955 10.261 8.73 10 8.134 10" clip-rule="evenodd"></path></g><defs><clipPath id="clip0_21209_241507"><path fill="#fff" d="M0 0h32v32H0z"></path></clipPath></defs></svg>
          </div>
        </a>
        <a href="#" aria-label="Одноклассники">
          <div class="Icon_icon__WhKMY" aria-hidden="true" style="height: 32px;">
            <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="none" viewBox="0 0 32 32"><g clip-path="url(#clip0_21275_161285)"><path fill="#E0E0E0" d="M0 15.333C0 8.105 0 4.491 2.246 2.246 4.49 0 8.106 0 15.333 0h1.334c7.228 0 10.842 0 13.087 2.246C32 4.49 32 8.106 32 15.333v1.334c0 7.228 0 10.842-2.245 13.087C27.509 32 23.895 32 16.667 32h-1.334c-7.228 0-10.842 0-13.087-2.245C0 27.509 0 23.895 0 16.667z"></path><path fill="#595959" d="M16.032 16.316a4.854 4.854 0 0 0 4.845-4.846 4.854 4.854 0 0 0-4.845-4.845c-2.698 0-4.874 2.176-4.874 4.845 0 2.67 2.176 4.845 4.874 4.845m0-6.848c1.102 0 2.002.9 2.002 2.002 0 1.103-.9 2.002-2.002 2.002s-2.002-.9-2.002-2.002c-.029-1.102.87-2.002 2.002-2.002M17.976 20.29a9.2 9.2 0 0 0 2.814-1.16c.668-.406.87-1.306.435-1.973a1.413 1.413 0 0 0-1.973-.435 6.16 6.16 0 0 1-6.527 0 1.445 1.445 0 0 0-1.973.435c-.378.667-.175 1.538.493 1.944.87.551 1.828.928 2.814 1.16l-2.698 2.698a1.42 1.42 0 0 0 0 2.003c.29.29.638.406 1.015.406.378 0 .726-.145 1.016-.406l2.669-2.67 2.67 2.67c.55.55 1.45.55 2.001 0a1.42 1.42 0 0 0 0-2.003z"></path></g><defs><clipPath id="clip0_21275_161285"><rect width="32" height="32" fill="#fff" rx="6"></rect></clipPath></defs></svg>
          </div>
        </a>
        <a href="#" aria-label="YouTube">
          <div class="Icon_icon__WhKMY" aria-hidden="true" style="height: 32px;">
            <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="none" viewBox="0 0 32 32"><g clip-path="url(#clip0_21209_241514)"><path fill="#E0E0E0" d="M0 15.333C0 8.105 0 4.491 2.246 2.246 4.49 0 8.106 0 15.333 0h1.334c7.228 0 10.842 0 13.087 2.246C32 4.49 32 8.106 32 15.333v1.334c0 7.228 0 10.842-2.245 13.087C27.509 32 23.895 32 16.667 32h-1.334c-7.228 0-10.842 0-13.087-2.245C0 27.509 0 23.895 0 16.667z"></path><g clip-path="url(#clip1_21209_241514)"><path fill="#595959" d="M23.665 11.874c-.184-.738-.726-1.319-1.414-1.516C21.003 10 15.999 10 15.999 10s-5.003 0-6.25.358c-.689.197-1.231.778-1.415 1.516C8 13.21 8 16 8 16s0 2.79.334 4.126c.184.738.726 1.319 1.414 1.516C10.996 22 16 22 16 22s5.004 0 6.252-.358c.688-.197 1.23-.778 1.414-1.516C24 18.79 24 16 24 16s0-2.79-.335-4.126"></path><path fill="#E0E0E0" d="m14.399 18.571 4.157-2.57-4.157-2.573z"></path></g></g><defs><clipPath id="clip0_21209_241514"><rect width="32" height="32" fill="#fff" rx="6"></rect></clipPath><clipPath id="clip1_21209_241514"><path fill="#fff" d="M8 10h16v12H8z"></path></clipPath></defs></svg>
          </div>
        </a>
      </div>
    </div>

    <!-- Footer Links -->
    <div class="footer-links">
      <div class="footer-column">
        <a href="#">Ответы на вопросы</a>
        <a href="#">Контакты</a>
        <a href="#">Работа в каталоге</a>
      </div>
      <div class="footer-column">
        <a href="#">Для поставщиков</a>
        <a href="#">Умный импорт</a>
        <a href="#">Стать курьером-партнёром</a>
      </div>
      <div class="footer-column">
        <a href="#">Линия доверия доставки</a>
        <a href="#">Правила и соглашения</a>
        <a href="#">Политика конфиденциальности</a>
      </div>
    </div>

    <!-- Legal Text -->
    <div class="footer-legal">
      <p>
        Зона, время, товары и предложения доставки ограничены. Организатор, продавец ООО «Умный ритейл» ОГРН 1177847261602, 121087, Москва, вн.г.тер. муниципальный округ Филёвский парк, ул. Барклая, д. 6, стр. 3, помещ. 8Н/4. Информационные услуги оказываются ООО «Умное простейт» ОГРН 1137847232852, 121087, Москва, вн.г.тер. муниципальный округ Филёвский парк, ул. Барклая, д. 6, стр. 3, помещ. 8Н/4
      </p>
    </div>
  </div>
</template>

<script>
import { defineComponent } from "vue";
import { assets } from "@/assets/grocery-assets.js";

export default defineComponent({
  name: "GroceryFooter",
  data() {
    return {
      assets,
      appBadges: [
        { alt: 'App Store', src: assets.store_app_store },
        { alt: 'Google Play', src: assets.store_google_play },
        { alt: 'AppGallery', src: assets.store_app_gallery },
        { alt: 'RuStore', src: assets.store_ru_store },
      ],
    };
  },
});
</script>

<style scoped>
/* Margin and padding for .grocery-footer are controlled by parent CSS */

.footer-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 40px;
}

.download-apps {
  display: flex;
  gap: 12px;
}

.app-badge {
  height: 40px;
  cursor: pointer;
}

.button-label {
  font-size: 10px;
  color: #666;
  text-transform: none;
}

.button-title {
  font-size: 14px;
  font-weight: 600;
  color: #1a1a1a;
}

.social-links {
  display: flex;
  gap: 16px;
}

.footer-links {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 40px;
  margin-bottom: 40px;
}

.footer-column {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.footer-column a {
  color: #595959;
  text-decoration: none;
  font-size: 16px;
  transition: color 0.2s;
  font-weight: 600;
}

.footer-column a:hover {
  color: var(--bench-primary, #4a6fa5);
}

.footer-legal {
  padding-top: 24px;
}

.footer-legal p {
  font-size: 13px;
  color: #aaa;
  line-height: 1.1;
  margin: 0;
  text-indent: 0;
  font-weight: 600;
}
</style>

