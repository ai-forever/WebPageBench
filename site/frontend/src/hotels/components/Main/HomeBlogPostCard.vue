<template>
  <div class="post">
    <a class="imageLink" :href="href" target="_blank" rel="noreferrer">
      <img class="postImage" :src="image" :alt="title" />
    </a>

    <div class="meta">
      <a class="category" :href="href" target="_blank" rel="noreferrer">{{ category }}</a>
      <p class="date">{{ date }}</p>
    </div>

    <a class="link postTitle" :href="href" target="_blank" rel="noreferrer">
      {{ title }}
    </a>
  </div>
</template>

<script setup>
defineProps({
  image: { type: String, required: true },
  href: { type: String, required: true },
  category: { type: String, required: true },
  date: { type: String, required: true },
  title: { type: String, required: true },
});
</script>

<style scoped>
/* reset на всякий */
/* :where(*) {
  border: 0;
  margin: 0;
  padding: 0;
} */

/* убираем дефолтное underline у <a> */
a {
  text-decoration: none;
}

/* image */
.imageLink {
  display: block;
}

.postImage {
  display: block;
  width: 100%;
  height: 200px;
  object-fit: cover;
  overflow: hidden;
  border-radius: 16px;
  margin-bottom: 16px !important;
}

/* Post__content */
.meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px !important;
}

/* Post__category */
.category {
  color: #292f37;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 1.2px;
  line-height: 17px;
  text-transform: uppercase;
  margin-right: 12px;
  font-family: PTRootUI, sans-serif;
}

/* дата — в оригинале точные стили ты не прислал,
   но маргины точно должны быть 0 (мы их уже сбросили) */
.date {
  font-size: 12px;
  line-height: 17px;
  color: rgba(45, 49, 55, 0.7);
  white-space: nowrap;
  font-family: PTRootUI, sans-serif;
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

/* Post__title */
.postTitle {
  color: #292f37;
  font-family: Spoof, system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
  font-size: 18px;
  font-weight: 500;
  line-height: 24px;
  padding-right: 20px;
}
</style>
