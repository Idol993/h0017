<script>
  import { onMount } from 'svelte';
  import { getDecks, importCSV, exportJSON, importJSON } from '../lib/api.js';

  let decks = $state([]);
  let selectedDeckId = $state('');
  let csvFile = $state(null);
  let csvPreview = $state([]);
  let isDragging = $state(false);
  let importing = $state(false);
  let jsonFileInput = $state(null);
  let message = $state(null);
  let messageType = $state('success');

  let fileInput = $state(null);

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
          back: parts[1].replace(/^"|"$/g, '').trim()
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
      const text = e.target.result;
      csvPreview = parseCSV(text);
    };
    reader.readAsText(file);
  }

  function handleDrop(e) {
    e.preventDefault();
    isDragging = false;
    const file = e.dataTransfer.files[0];
    handleFile(file);
  }

  function handleDragOver(e) {
    e.preventDefault();
    isDragging = true;
  }

  function handleDragLeave() {
    isDragging = false;
  }

  function handleFileSelect(e) {
    const file = e.target.files[0];
    handleFile(file);
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
      await importCSV(selectedDeckId, formData);
      showMessage('导入成功！', 'success');
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
      await importJSON(formData);
      showMessage('导入备份成功！', 'success');
      loadDecks();
    } catch (error) {
      console.error('导入备份失败:', error);
      showMessage('导入备份失败，请重试', 'error');
    } finally {
      importing = false;
      if (jsonFileInput) jsonFileInput.value = '';
    }
  }

  function showMessage(text, type = 'success') {
    message = text;
    messageType = type;
    setTimeout(() => {
      message = null;
    }, 3000);
  }

  onMount(() => {
    loadDecks();
  });
</script>

<div class="import-page">
  <h1 class="page-title">导入与导出</h1>

  {#if message}
    <div style="padding: 12px 16px; border-radius: 8px; margin-bottom: 24px; color: #ffffff; background-color: {messageType === 'success' ? '#22c55e' : '#ef4444'};">
      {message}
    </div>
  {/if}

  <div style="display: grid; gap: 32px; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); margin-bottom: 48px;">
    <div class="chart-container">
      <div class="chart-title">导出 JSON 备份</div>
      <p style="color: #6b7280; margin-bottom: 20px; font-size: 14px;">
        将所有卡组和卡片数据导出为 JSON 格式备份文件，方便迁移和保存。
      </p>
      <button class="btn btn-primary" onclick={handleExportJSON} disabled={importing}>
        📥 导出 JSON 备份
      </button>
    </div>

    <div class="chart-container">
      <div class="chart-title">导入 JSON 备份</div>
      <p style="color: #6b7280; margin-bottom: 20px; font-size: 14px;">
        从之前导出的 JSON 备份文件恢复数据。
      </p>
      <button class="btn btn-secondary" onclick={triggerJSONImport} disabled={importing}>
        📤 导入 JSON 备份
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
      上传 CSV 文件批量导入卡片。CSV 格式：第一列为正面（问题），第二列为背面（答案）。
    </p>

    <div
      class={isDragging ? 'upload-area dragover' : 'upload-area'}
      ondrop={handleDrop}
      ondragover={handleDragOver}
      ondragleave={handleDragLeave}
      onclick={triggerFileInput}
    >
      <div class="upload-icon">📁</div>
      <div class="upload-text">拖拽 CSV 文件到此处，或点击选择文件</div>
      <div class="upload-hint">支持 .csv 格式</div>
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
        <div style="font-weight: 600; margin-bottom: 12px; color: #374151;">数据预览（前 {Math.min(csvPreview.length - 1, 5)} 条）：</div>
        <table class="preview-table">
          <thead>
            <tr>
              <th>#</th>
              <th>正面（问题）</th>
              <th>背面（答案）</th>
            </tr>
          </thead>
          <tbody>
            {#each csvPreview.slice(0, 6) as row, index}
              <tr>
                <td>{index === 0 ? '表头' : index}</td>
                <td>{row.front}</td>
                <td>{row.back}</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    {/if}

    {#if csvFile}
      <div style="display: flex; gap: 16px; align-items: flex-end; flex-wrap: wrap;">
        <div class="form-group" style="flex: 1; min-width: 200px; margin-bottom: 0;">
          <label class="form-label">选择目标卡组</label>
          <select class="form-select" bind:value={selectedDeckId}>
            <option value="">请选择卡组</option>
            {#each decks as deck}
              <option value={deck.id}>{deck.name}</option>
            {/each}
          </select>
        </div>
        <button class="btn btn-primary" onclick={handleImportCSV} disabled={importing || !selectedDeckId}>
          {importing ? '导入中...' : '✓ 确认导入'}
        </button>
      </div>
    {/if}
  </div>
</div>
