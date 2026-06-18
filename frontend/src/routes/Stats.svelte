<script>
  import { onMount } from 'svelte';
  import { Chart, registerables } from 'chart.js';
  import { getStats, getDecks } from '../lib/api.js';

  Chart.register(...registerables);

  let stats = $state(null);
  let decks = $state([]);
  let loading = $state(true);
  let chartCanvas;
  let chartInstance = null;

  function transformStatsData(rawStats, deckList) {
    const last30Days = [];
    const today = new Date();
    for (let i = 29; i >= 0; i--) {
      const date = new Date(today);
      date.setDate(date.getDate() - i);
      const dateKey = date.toISOString().split('T')[0];
      const count = rawStats.daily_reviews_last_30_days?.[dateKey] || 0;
      last30Days.push({
        date,
        count,
        isToday: i === 0,
        isWeekend: date.getDay() === 0 || date.getDay() === 6
      });
    }

    const totalReviews = Object.values(rawStats.daily_reviews_last_30_days || {}).reduce((a, b) => a + b, 0);

    const decksWithColor = rawStats.deck_mastery_rates?.map(ds => {
      const deck = deckList.find(d => d.id === ds.deck_id);
      return {
        id: ds.deck_id,
        name: ds.deck_name,
        color: deck?.cover_color || '#3b82f6',
        total: ds.total_cards,
        mastered: ds.mastered_cards
      };
    }) || [];

    return {
      total_cards: rawStats.total_cards || 0,
      today_reviews: rawStats.today_reviewed || 0,
      total_reviews: totalReviews,
      last30Days,
      decks: decksWithColor
    };
  }

  function getBarColor(day) {
    if (day.isToday) return '#f97316';
    if (day.isWeekend) return '#d1d5db';
    return '#3b82f6';
  }

  function createChart() {
    if (!chartCanvas || !stats) return;
    if (chartInstance) chartInstance.destroy();

    const labels = stats.last30Days.map(d => `${d.date.getMonth() + 1}/${d.date.getDate()}`);
    const data = stats.last30Days.map(d => d.count);
    const colors = stats.last30Days.map(d => getBarColor(d));

    chartInstance = new Chart(chartCanvas, {
      type: 'bar',
      data: {
        labels,
        datasets: [{
          label: '复习数量',
          data,
          backgroundColor: colors,
          borderRadius: 4,
          borderSkipped: false
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          y: { beginAtZero: true, grid: { color: '#f3f4f6' }, ticks: { color: '#6b7280' } },
          x: { grid: { display: false }, ticks: { color: '#6b7280', maxRotation: 45, minRotation: 45 } }
        }
      }
    });
  }

  function getMasteryPercent(mastered, total) {
    if (total === 0) return 0;
    return Math.round((mastered / total) * 100);
  }

  function getCircumference(radius) {
    return 2 * Math.PI * radius;
  }

  async function loadStats() {
    loading = true;
    try {
      const [rawStats, deckList] = await Promise.all([getStats(), getDecks()]);
      decks = deckList || [];
      stats = transformStatsData(rawStats, decks);
    } catch (error) {
      console.error('加载统计数据失败:', error);
      stats = null;
    } finally {
      loading = false;
      setTimeout(createChart, 50);
    }
  }

  onMount(() => {
    loadStats();
  });
</script>

<div class="stats-page">
  <h1 class="page-title">统计数据</h1>

  {#if loading}
    <div class="empty-state">
      <div class="empty-state-icon">⏳</div>
      <div class="empty-state-text">加载中...</div>
    </div>
  {:else if stats}
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-value">{stats.total_cards}</div>
        <div class="stat-label">总卡片数</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{stats.today_reviews}</div>
        <div class="stat-label">今日复习</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{stats.total_reviews}</div>
        <div class="stat-label">近30天累计复习</div>
      </div>
    </div>

    <div class="chart-container">
      <div class="chart-title">近 30 天复习量</div>
      <div style="height: 300px; position: relative;">
        <canvas bind:this={chartCanvas}></canvas>
      </div>
      <div style="display: flex; gap: 24px; margin-top: 16px; font-size: 13px; color: #6b7280; flex-wrap: wrap;">
        <div style="display: flex; align-items: center; gap: 6px;">
          <div style="width: 12px; height: 12px; background-color: #f97316; border-radius: 2px;"></div>
          今日
        </div>
        <div style="display: flex; align-items: center; gap: 6px;">
          <div style="width: 12px; height: 12px; background-color: #3b82f6; border-radius: 2px;"></div>
          工作日
        </div>
        <div style="display: flex; align-items: center; gap: 6px;">
          <div style="width: 12px; height: 12px; background-color: #d1d5db; border-radius: 2px;"></div>
          周末
        </div>
      </div>
    </div>

    <div>
      <div class="chart-title" style="margin-bottom: 16px;">各卡组掌握率</div>
      {#if stats.decks.length === 0}
        <div class="empty-state" style="padding: 32px;">
          <div class="empty-state-text">暂无卡组数据</div>
        </div>
      {:else}
        <div class="deck-progress-list">
          {#each stats.decks as deck}
            <div class="deck-progress-item">
              <div class="circular-progress">
                <svg width="80" height="80">
                  <circle cx="40" cy="40" r="32" fill="none" stroke="#e5e7eb" stroke-width="8" />
                  <circle
                    cx="40" cy="40" r="32" fill="none"
                    stroke={deck.color || '#3b82f6'}
                    stroke-width="8"
                    stroke-linecap="round"
                    stroke-dasharray={getCircumference(32)}
                    stroke-dashoffset={getCircumference(32) * (1 - getMasteryPercent(deck.mastered, deck.total) / 100)}
                  />
                </svg>
                <div class="circular-progress-text">{getMasteryPercent(deck.mastered, deck.total)}%</div>
              </div>
              <div class="deck-progress-info">
                <div class="deck-progress-name">{deck.name}</div>
                <div class="deck-progress-detail">已掌握 {deck.mastered} / {deck.total} 张</div>
              </div>
            </div>
          {/each}
        </div>
      {/if}
    </div>
  {:else}
    <div class="empty-state">
      <div class="empty-state-icon">📊</div>
      <div class="empty-state-text">无法加载统计数据</div>
    </div>
  {/if}
</div>
