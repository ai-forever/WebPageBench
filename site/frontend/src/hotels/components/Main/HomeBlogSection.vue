<template>
  <article class="blog">
    <div>
      <a class="link blogTitle" href="/hotels/cdn/asset.bin" target="_blank" rel="noreferrer">
        Блог о путешествиях
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="none" class="titleArrow">
          <path
            fill="#2D3137"
            fill-rule="evenodd"
            d="M4.46 14.1a1 1 0 0 1 0-1.4L9.15 8l-4.7-4.7a1 1 0 0 1 1.42-1.4l6.1 6.1-6.1 6.1a1 1 0 0 1-1.41 0Z"
            clip-rule="evenodd"
          />
        </svg>
      </a>
    </div>

    <div class="posts">
      <!-- 3 штуки — копии, ты потом подставишь данные/картинки -->
      <HomeBlogPostCard
        image="/hotels/cdn/76bf9c378952d5d020ea85244e4f38e5f05e28e1.JPEG.jpeg"
        href="/hotels/cdn/asset.bin"
        category="О!Лайфхаки"
        date="09.01.2026"
        title="Что взять с собой в поезд: список вещей для ж/д путешествия"
      />

      <HomeBlogPostCard
        image="/hotels/cdn/8d980dce47150c75201ef566e3f8cbfefe41cfc1.JPEG.jpeg"
        href="/hotels/cdn/asset.bin"
        category="О!Впечатления"
        date="06.01.2026"
        title="Мискузи, Паддингтон: 14 фильмов про путешествия, которые стоит посмотреть"
      />

      <HomeBlogPostCard
        image="/hotels/cdn/8fa34482247d9552c484d3d1c07da79b84aee40f.JPEG.jpeg"
        href="/hotels/cdn/asset.bin"
        category="О!Актуалочка"
        date="03.01.2026"
        title="Лучшее в О!Блоге: топ-10 статей 2025 года"
      />
    </div>
  </article>
</template>

<script setup>
import HomeBlogPostCard from './HomeBlogPostCard.vue';
</script>

<style scoped>
/* Blog__blog */
.blog {
  --active-pin-size: 7px;
  display: flex;
  flex-direction: column;
  position: relative;
}

/* reset как у них (иначе p будет иметь дефолтные margin) */
.blog :where(*) {
  border: 0;
  margin: 0;
  padding: 0;
}

/* Link-module__link */
.link {
  align-items: center;
  color: var(--link, #0e41d2);
  display: inline-flex;
  font-size: 16px;
  font-weight: 500;
  line-height: inherit;
  text-decoration: none;
  transition: color 0.16s ease;
  cursor: pointer;
}

/* Blog__title */
.blogTitle {
  color: inherit;
  /* display: inline-block; */
  font-family: Spoof, system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
  font-size: 24px;
  font-weight: 500;
  line-height: 32px;
  margin-bottom: 32px;
  color: #292f37;
}

.titleArrow {
  margin-left: 6px;
  display: block;
}

/* Blog__posts grid */
.posts {
  display: grid;
  grid-gap: 40px 20px;
  grid-template-columns: 1fr 1fr 1fr;
  position: relative;
}

/* можно добавить адаптив, но если хочешь 1в1 — убери */
@media (max-width: 980px) {
  .posts {
    grid-template-columns: 1fr 1fr;
  }
}
@media (max-width: 640px) {
  .posts {
    grid-template-columns: 1fr;
  }
}
</style>
