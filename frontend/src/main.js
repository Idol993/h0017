import { mount } from 'svelte';
import './app.css';
import App from './App.svelte';

const target = document.getElementById('app');
let app = null;

try {
  if (target) {
    target.innerHTML = '';
  }
  app = mount(App, { target });
} catch (e) {
  console.error('应用初始化失败:', e);
  if (target) {
    target.innerHTML = '<div style="padding:32px;color:#ef4444;font-family:sans-serif;">' +
      '<h2 style="margin:0 0 16px;">加载失败</h2>' +
      '<p style="margin:0 0 12px;">应用初始化时出现错误：</p>' +
      '<pre style="background:#fef2f2;padding:12px;border-radius:6px;overflow:auto;">' +
      (e?.message || String(e)) + '</pre></div>';
  }
}

export default app;
