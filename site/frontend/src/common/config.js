// DEV — override via VITE_API_URL when starting scripts/run_bench_*.sh
export const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:9000/";

export default API_URL;