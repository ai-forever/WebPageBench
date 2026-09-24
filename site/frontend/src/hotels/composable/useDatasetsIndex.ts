import { onMounted, ref } from 'vue';
import { loadDatasetsIndex, type DatasetIndexItem } from '@/hotels/services/searchDataset';

export function useDatasetsIndex() {
  const datasets = ref<DatasetIndexItem[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);

  async function reload() {
    loading.value = true;
    error.value = null;
    try {
      datasets.value = await loadDatasetsIndex();
    } catch (e: any) {
      error.value = e?.message ?? 'Failed to load datasets index';
      datasets.value = [];
    } finally {
      loading.value = false;
    }
  }

  onMounted(reload);

  return { datasets, loading, error, reload };
}
