<script>
  import { onMount } from 'svelte';
  import { getDecks, importCSV, exportJSON, importJSON } from '../lib/api.js';

  let decks = $state([]);
  let selectedDeckId = $state('');
  let csvFile = $state(null);
  let csvPreview = $state([]);
  let isDragging = $state(false);
  let importing = $state(false);
  let message = $state(null);
  let messageType = $state('success');

  let fileInput;
  let jsonFileInput;

  async function loadDecks() {
    try {
      decks = await getDecks() || [];
    } catch (error) {
      console.error('加载卡组失败:', error);
      decks = [];
    }
  }

  function parseCSV(text) {
    const lines = text.trim().split('\n');
    if (lines.length === 0) return [];

    const result = [];
    const previewCount = Math.min(lines.length, 6);

    for (let i = 0; i < previewCount; i++) {
      const line = lines[i];
      let parts = [];
      let current = '';
      let inQuotes = false;

      for (let j = 0; j < line.length; j++) {
        const char = line[j];
        if (char === '"') {
          inQuotes = !inQuotes;
        } else if (char === ',' && !inQuotes) {
          parts.push(current);
          current = '';
        } else {
          current += char;
        }
      }
      parts.push(current);

      if (parts.length >= 2) {
        result.push({
          front: parts[0].replace(/^"|"$/g, '').trim(),
          back: parts[1].replace(/^"|"$/g, '').trim(),
          tags: parts.length >= 3 ? parts[2].replace(/^"|"$/g, '').trim() : ''
        });
      }
    }

    return result;
  }

  function handleFile(file) {
    if (!file) return;
    if (!file.name.toLowerCase().endsWith('.csv')) {
      showMessage('请上传 CSV 格式的文件', 'error');
      return;
    }

    csvFile = file;
    const reader = new FileReader();
    reader.onload = (e) => {
      csvPreview = parseCSV(e.target.result);
    };
    reader.readAsText(file);
  }

  function handleDrop(e) {
    e.preventDefault();
    isDragging = false;
    handleFile(e.dataTransfer.files[0]);
  }

  function handleDragOver(e) {
    e.preventDefault();
    isDragging = true;
  }

  function handleDragLeave() {
    isDragging = false;
  }

  function handleFileSelect(e) {
    handleFile(e.target.files[0]);
  }

  function triggerFileInput() {
    fileInput?.click();
  }

  async function handleImportCSV() {
    if (!csvFile || !selectedDeckId) {
      showMessage('请选择卡组和 CSV 文件', 'error');
      return;
    }

    importing = true;
    try {
      const formData = new FormData();
      formData.append('file', csvFile);
      const result = await importCSV(selectedDeckId, formData);
      showMessage(`导入成功！新增 ${result.imported} 张卡片，跳过 ${result.skipped} 张重复`, 'success');
      clearCSV();
    } catch (error) {
      console.error('导入失败:', error);
      showMessage('导入失败，请重试', 'error');
    } finally {
      importing = false;
    }
  }

  function clearCSV() {
    csvFile = null;
    csvPreview = [];
    if (fileInput) fileInput.value = '';
  }

  async function handleExportJSON() {
    try {
      const data = await exportJSON();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `spaced-repetition-backup-${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      showMessage('导出成功！', 'success');
    } catch (error) {
      console.error('导出失败:', error);
      showMessage('导出失败，请重试', 'error');
    }
  }

  function triggerJSONImport() {
    jsonFileInput?.click();
  }

  async function handleJSONImport(e) {
    const file = e.target.files[0];
    if (!file) return;
    if (!file.name.toLowerCase().endsWith('.json')) {
      showMessage('请上传 JSON 格式的备份文件', 'error');
      return;
    }

    importing = true;
    try {
      const formData = new FormData();
      formData.append('file', file);
      const result = await importJSON(formData);
      const parts = [];
      if (result.decks_imported || result.decks_updated) {
        parts.push(`${result.decks_imported || 0} 个卡组新增，${result.decks_updated || 0} 个更新`);
      }
      if (result.cards_imported || result.cards_updated) {
        parts.push(`${result.cards_imported || 0} 张卡片新增，${result.cards_updated || 0} 张更新复习进度`);
      }
      if (result.logs_imported || result.logs_skipped) {
        parts.push(`${result.logs_imported || 0} 条复习记录恢复，${result.logs_skipped || 0} 条跳过`);
      }
      showMessage(`备份恢复成功！${parts.join('；')}`, 'success');
      loadDecks();
    } catch (error) {
      console.error('导入备份失败:', error);
      const detail = error?.response?.data?.detail || error?.message || '未知错误';
      showMessage(`导入备份失败：${detail}`, 'error');
    } finally {
      importing = false;
      if (jsonFileInput) jsonFileInput.value = '';
    }
  }

  function showMessage(text, type = 'success') {
    message = text;
    messageType = type;
    setTimeout(() => { message = null; }, 5000);
  }

  onMount(() => {
    loadDecks();
  });
</script>

<div class="import-page">
  <h1 class="page-title">导入与导出</h1>

  {#if message}
    <div class="import-message" class:success={messageType === 'success'} class:error={messageType === 'error'}>
      {message}
    </div>
  {/if}

  <div style="display: grid; gap: 32px; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); margin-bottom: 48px;">
    <div class="chart-container">
      <div class="chart-title">导出 JSON 备份</div>
      <p style="color: #6b7280; margin-bottom: 20px; font-size: 14px;">
        将所有卡组、卡片和复习记录导出为 JSON 文件，方便迁移和保存。
      </p>
      <button class="btn btn-primary" onclick={handleExportJSON} disabled={importing}>
        导出 JSON 备份
      </button>
    </div>

    <div class="chart-container">
      <div class="chart-title">导入 JSON 备份</div>
      <p style="color: #6b7280; margin-bottom: 20px; font-size: 14px;">
        从之前导出的 JSON 备份恢复数据（会覆盖当前数据）。
      </p>
      <button class="btn btn-secondary" onclick={triggerJSONImport} disabled={importing}>
        选择 JSON 文件恢复
      </button>
      <input
        type="file"
        accept=".json"
        style="display: none;"
        bind:this={jsonFileInput}
        onchange={handleJSONImport}
      />
    </div>
  </div>

  <div class="chart-container">
    <div class="chart-title">导入 CSV 卡片</div>
    <p style="color: #6b7280; margin-bottom: 20px; font-size: 14px;">
      上传 CSV 文件批量导入卡片。格式：第一列正面，第二列背面，第三列标签（可选，逗号分隔）。
      正反面完全相同的卡片会自动跳过。
    </p>

    <div
      class={isDragging ? 'upload-area dragover' : 'upload-area'}
      ondrop={handleDrop}
      ondragover={handleDragOver}
      ondragleave={handleDragLeave}
      onclick={triggerFileInput}
      role="button"
      tabindex="0"
    >
      <div class="upload-icon">📁</div>
      <div class="upload-text">拖拽 CSV 文件到此处，或点击选择文件</div>
      <div class="upload-hint">支持 .csv 格式，编码 UTF-8</div>
      <input
        type="file"
        accept=".csv"
        style="display: none;"
        bind:this={fileInput}
        onchange={handleFileSelect}
      />
    </div>

    {#if csvFile}
      <div style="margin-bottom: 24px; padding: 12px 16px; background-color: #eff6ff; border-radius: 8px; display: flex; justify-content: space-between; align-items: center;">
        <span style="color: #1e40af; font-size: 14px;">已选择文件: {csvFile.name}</span>
        <button class="btn btn-secondary" onclick={(e) => { e.stopPropagation(); clearCSV(); }}>清除</button>
      </div>
    {/if}

    {#if csvPreview.length > 0}
      <div style="margin-bottom: 24px;">
        <div style="font-weight: 600; margin-bottom: 12px; color: #374151;">数据预览（前 5 条）：</div>
        <table class="preview-table">
          <thead>
            <tr>
              <th>#</th>
              <th>正面（问题）</th>
              <th>背面（答案）</th>
              <th>标签</th>
            </tr>
          </thead>
          <tbody>
            {#each csvPreview.slice(0, 6) as row, index}
              <tr>
                <td>{index + 1}</td>
                <td>{row.front}</td>
                <td>{row.back}</td>
                <td>{row.tags}</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    {/if}

    {#if csvFile}
      <div style="display: flex; gap: 16px; align-items: flex-end; flex-wrap: wrap;">
        <div class="form-group" style="flex: 1; min-width: 200px; margin-bottom: 0;">
          <label class="form-label" for="csv-deck-select">选择目标卡组</label>
          <select id="csv-deck-select" class="form-select" bind:value={selectedDeckId}>
            <option value="">请选择卡组</option>
            {#each decks as deck}
              <option value={deck.id}>{deck.name}</option>
            {/each}
          </select>
        </div>
        <button class="btn btn-primary" onclick={handleImportCSV} disabled={importing || !selectedDeckId}>
          {importing ? '导入中...' : '确认导入'}
        </button>
      </div>
    {/if}
  </div>
</div>

<style>
  .import-message {
    padding: 12px 16px;
    border-radius: 8px;
    margin-bottom: 24px;
    font-size: 14px;
  }
  .import-message.success {
    background-color: #f0fdf4;
    color: #166534;
    border: 1px solid #bbf7d0;
  }
  .import-message.error {
    background-color: #fef2f2;
    color: #991b1b;
    border: 1px solid #fecaca;
  }
</style>
