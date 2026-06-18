<script>
  import { onMount } from 'svelte';
  import { getTodayCards, submitReview } from '../lib/api.js';

  let cards = $state([]);
  let currentIndex = $state(0);
  let isFlipped = $state(false);
  let reviewedCount = $state(0);
  let loading = $state(true);
  let cardStartTime = $state(Date.now());
  let allDone = $state(false);

  let currentCard = $derived(cards.length > 0 && currentIndex < cards.length ? cards[currentIndex] : null);
  let totalCards = $derived(cards.length);
  let progressPercent = $derived(totalCards > 0 ? (reviewedCount / totalCards) * 100 : 0);

  const ratingLabels = {
    1: '非常难',
    2: '较难',
    3: '一般',
    4: '较易',
    5: '非常易'
  };

  async function loadCards() {
    loading = true;
    isFlipped = false;
    allDone = false;
    currentIndex = 0;
    reviewedCount = 0;
    try {
      const data = await getTodayCards();
      cards = data || [];
    } catch (error) {
      console.error('加载今日卡片失败:', error);
      cards = [];
    } finally {
      loading = false;
      cardStartTime = Date.now();
    }
  }

  function flipCard() {
    if (!isFlipped) {
      isFlipped = true;
    }
  }

  async function handleRating(rating) {
    if (!currentCard) return;
    const duration = Math.floor((Date.now() - cardStartTime) / 1000);
    try {
      await submitReview(currentCard.id, rating, duration);
    } catch (error) {
      console.error('提交复习失败:', error);
    }
    reviewedCount += 1;
    isFlipped = false;
    if (currentIndex < cards.length - 1) {
      currentIndex += 1;
      cardStartTime = Date.now();
    } else {
      allDone = true;
    }
  }

  onMount(() => {
    loadCards();
  });
</script>

<div class="today-page">
  <h1 class="page-title">今日学习</h1>

  {#if loading}
    <div class="empty-state">
      <div class="empty-state-icon">⏳</div>
      <div class="empty-state-text">加载中...</div>
    </div>
  {:else if totalCards === 0}
    <div class="empty-state">
      <div class="empty-state-icon">🎉</div>
      <div class="empty-state-text">太棒了！今天没有需要复习的卡片</div>
      <div class="empty-state-sub">可以稍后再来，或者去卡组管理添加新卡片</div>
    </div>
  {:else if allDone}
    <div class="empty-state">
      <div class="empty-state-icon">✅</div>
      <div class="empty-state-text">今日复习已完成！</div>
      <div class="empty-state-sub">共复习了 {reviewedCount} 张卡片，继续保持！</div>
    </div>
  {:else}
    <div class="progress-bar">
      <div class="progress-fill" style="width: {progressPercent}%"></div>
    </div>
    <div class="progress-text">已复习 {reviewedCount} / {totalCards} 张卡片</div>

    {#if currentCard}
      <div class="today-card-info">
        <span class="today-deck-badge" style="background-color: {currentCard.deck_color || '#3b82f6'}">{currentCard.deck_name}</span>
        {#if currentCard.is_overdue}
          <span class="today-overdue-badge">已过期 {currentCard.overdue_days} 天</span>
        {/if}
      </div>

      <div class="card-container" onclick={flipCard} role="button" tabindex="0" onkeydown={(e) => { if (e.key === 'Enter' || e.key === ' ') flipCard(); }}>
        <div class={isFlipped ? 'flashcard flipped' : 'flashcard'}>
          <div class="flashcard-face flashcard-front">
            <div class="deck-color-bar" style="background-color: {currentCard.deck_color || '#3b82f6'}"></div>
            <div class="flashcard-content">
              <div class="flashcard-text">{currentCard.front}</div>
            </div>
          </div>
          <div class="flashcard-face flashcard-back">
            <div class="deck-color-bar" style="background-color: {currentCard.deck_color || '#3b82f6'}"></div>
            <div class="flashcard-content">
              <div class="flashcard-text">{currentCard.back}</div>
            </div>
          </div>
        </div>
      </div>

      {#if isFlipped}
        <div class="rating-buttons">
          {#each [1, 2, 3, 4, 5] as rating}
            <button class="rating-btn rating-{rating}" onclick={() => handleRating(rating)}>
              <span class="rating-num">{rating}</span>
              <span class="rating-label">{ratingLabels[rating]}</span>
            </button>
          {/each}
        </div>
      {:else}
        <div class="flip-hint">点击卡片翻转查看答案</div>
      {/if}
    {/if}
  {/if}
</div>

<style>
  .today-card-info {
    display: flex;
    align-items: center;
    gap: 10px;
    justify-content: center;
    margin-bottom: 20px;
  }
  .today-deck-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 12px;
    color: #fff;
    font-size: 13px;
    font-weight: 500;
  }
  .today-overdue-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 12px;
    background-color: #fef2f2;
    color: #ef4444;
    font-size: 13px;
    font-weight: 500;
    border: 1px solid #fecaca;
  }
  .flip-hint {
    text-align: center;
    color: #9ca3af;
    font-size: 14px;
    margin-top: 20px;
  }
  .empty-state-sub {
    color: #9ca3af;
    font-size: 14px;
    margin-top: 8px;
  }
  .rating-num {
    font-size: 22px;
    font-weight: 700;
    display: block;
  }
  .rating-label {
    font-size: 12px;
    display: block;
    margin-top: 2px;
  }
  .rating-btn {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 10px 16px;
    min-width: 64px;
  }
</style>
