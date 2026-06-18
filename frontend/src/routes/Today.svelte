<script>
  import { onMount, onDestroy } from 'svelte';
  import { getTodayCards, submitReview } from '../lib/api.js';

  let cards = $state([]);
  let currentIndex = $state(0);
  let isFlipped = $state(false);
  let reviewedCount = $state(0);
  let loading = $state(true);
  let cardStartTime = $state(Date.now());

  let currentCard = $derived(cards[currentIndex] || null);
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
    isFlipped = !isFlipped;
  }

  async function handleRating(rating) {
    if (!currentCard) return;
    const duration = Math.floor((Date.now() - cardStartTime) / 1000);
    try {
      await submitReview(currentCard.id, rating, duration);
      reviewedCount += 1;
      nextCard();
    } catch (error) {
      console.error('提交复习失败:', error);
      nextCard();
    }
  }

  function nextCard() {
    isFlipped = false;
    if (currentIndex < cards.length - 1) {
      currentIndex += 1;
    }
    cardStartTime = Date.now();
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
    </div>
  {:else}
    <div class="progress-bar">
      <div class="progress-fill" style="width: {progressPercent}%"></div>
    </div>
    <div class="progress-text">已复习 {reviewedCount} / {totalCards} 张卡片</div>

    {#if currentCard}
      <div class="card-container" onclick={flipCard}>
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
            <button class="rating-btn rating-{rating}" onclick={(e) => { e.stopPropagation(); handleRating(rating); }}>
              {rating} - {ratingLabels[rating]}
            </button>
          {/each}
        </div>
      {:else}
        <div class="progress-text" style="margin-top: 24px;">点击卡片查看答案</div>
      {/if}
    {/if}
  {/if}
</div>
