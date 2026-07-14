import axios from 'axios';

// Base URL of the GitNote backend. Override with VITE_API_URL in a .env file.
export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

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
