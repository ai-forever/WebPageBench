<template>
  <div
    class="book-cover"
    :style="{ background: palette.bg, color: palette.fg }"
    role="img"
    :aria-label="ariaLabel"
  >
    <div class="book-cover__title">{{ displayTitle }}</div>
    <div v-if="displayAuthor" class="book-cover__author">{{ displayAuthor }}</div>
  </div>
</template>

<script>
const PALETTES = [
  { bg: "#1e3a5f", fg: "#f4e8c8" },
  { bg: "#7a1f2b", fg: "#f6e6c8" },
  { bg: "#245c3a", fg: "#e4f2dc" },
  { bg: "#3d2b5e", fg: "#efe6f8" },
  { bg: "#8a5a12", fg: "#fff3d6" },
  { bg: "#1a4a4a", fg: "#d8f0ea" },
  { bg: "#4a3040", fg: "#f5e0e8" },
  { bg: "#24364a", fg: "#dce8f5" },
  { bg: "#5c2e1a", fg: "#f3e0cc" },
  { bg: "#1f3d2f", fg: "#dcefe3" },
  { bg: "#3a2150", fg: "#eadcf5" },
  { bg: "#6b2d3c", fg: "#f8dde4" },
  { bg: "#2c4a6e", fg: "#e8f0ff" },
  { bg: "#4e3a16", fg: "#f6ebd0" },
  { bg: "#163a4a", fg: "#d4eef3" },
  { bg: "#5a2748", fg: "#f6dceb" },
];

function hashString(value) {
  const s = String(value || "");
  let h = 0;
  for (let i = 0; i < s.length; i += 1) {
    h = (h * 31 + s.charCodeAt(i)) | 0;
  }
  return Math.abs(h);
}

function initialOf(word) {
  const ch = (word || "").replace(/[^0-9A-Za-zА-Яа-яЁё]/g, "")[0];
  return ch ? `${ch.toUpperCase()}.` : "";
}

function authorLine(author) {
  const raw = String(author || "").trim();
  if (!raw) return "";
  const first = raw.split(",")[0].trim();
  const pair = first.match(/^(\S+)\s+и\s+(\S+)\s+(.+)$/);
  if (pair) {
    const a = initialOf(pair[1]);
    const b = initialOf(pair[2]);
    const last = pair[3].toUpperCase();
    if (a && b) return `${last} ${a} и ${b}`;
    return last;
  }
  const initialsFirst = first.match(/^((?:[A-Za-zА-ЯЁ]\.\s*)+)(.+)$/);
  if (initialsFirst) {
    const initials = initialsFirst[1].replace(/\s+/g, "").toUpperCase();
    return `${initialsFirst[2].trim().toUpperCase()} ${initials}`;
  }
  const parts = first.split(/\s+/).filter(Boolean);
  if (parts.length === 1) return parts[0].toUpperCase();
  const last = parts[parts.length - 1].toUpperCase();
  const initials = parts.slice(0, -1).map(initialOf).filter(Boolean).join(" ");
  return initials ? `${last} ${initials}` : last;
}

export default {
  name: "BookCover",
  props: {
    item: { type: Object, default: null },
  },
  computed: {
    displayTitle() {
      const name = (this.item && (this.item.name || this.item.title)) || "";
      return String(name).replace(/^#/, "").toUpperCase();
    },
    displayAuthor() {
      return authorLine(this.item && this.item.author);
    },
    palette() {
      const seed = (this.item && (this.item.id || this.item.uuid || this.item.name)) || "";
      return PALETTES[hashString(seed) % PALETTES.length];
    },
    ariaLabel() {
      return [this.displayTitle, this.displayAuthor].filter(Boolean).join(". ");
    },
  },
};
</script>
