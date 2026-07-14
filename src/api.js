import axios from 'axios';

// Base URL of the GitNote backend. Empty by default so requests go to the same
// origin and are handled by the Vite dev proxy (see vite.config.js) — this
// avoids CORS entirely in development. For a static production deploy, set
// VITE_API_URL to the backend's absolute URL.
export const API_URL = import.meta.env.VITE_API_URL || '';

const client = axios.create({ baseURL: API_URL });

/**
 * Upload two or more note files (.json and/or .pdf) and return the merge result.
 * @param {File[]} files
 * @returns {Promise<object>} { merged_text, headers: [...] }
 */
export async function mergeNotes(files) {
  const formData = new FormData();
  files.forEach((file) => formData.append('files', file));
  const { data } = await client.post('/api/merge', formData);
  return data;
}

export default client;
