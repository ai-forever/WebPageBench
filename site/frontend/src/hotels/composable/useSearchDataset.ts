import { onMounted, ref, unref, watch, computed, type Ref } from 'vue';
import { citiesToOptions, loadDataset, type SearchDataset } from '@/hotels/services/searchDataset';

type MaybeRef<T> = T | Ref<T>;

export function useSearchDataset(datasetId: MaybeRef<string>) {
  const dataset = ref<SearchDataset | null>(null);
  const loading = ref(false);
  const error = ref<string | null>(null);

  async function reload() {
    const id = (unref(datasetId) || '').trim();
    if (!id) return;

    loading.value = true;
    error.value = null;
    try {
      dataset.value = await loadDataset(id);
    } catch (e: any) {
      error.value = e?.message ?? 'Failed to load dataset';
      dataset.value = null;
    } finally {
      loading.value = false;
    }
  }

  onMounted(reload);
  watch(() => unref(datasetId), reload);

  const destinationOptions = computed(() => (dataset.value ? citiesToOptions(dataset.value.cities) : []));

  return { dataset, destinationOptions, loading, error, reload };
}
