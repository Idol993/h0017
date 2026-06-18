<script>
  import { onMount } from 'svelte';
  import {
    getDecks, createDeck, updateDeck, deleteDeck,
    getCards, createCard, updateCard, deleteCard
  } from '../lib/api.js';

  let decks = $state([]);
  let selectedDeckId = $state(null);
  let cards = $state([]);
  let loading = $state(true);
  let showDeckModal = $state(false);
  let showCardModal = $state(false);
  let editingDeck = $state(null);
  let editingCard = $state(null);

  let deckForm = $state({ name: '', language_pair: 'zh-jp', cover_color: '#3b82f6' });
  let cardForm = $state({ front: '', back: '', tags: '' });

  const presetColors = ['#ef4444', '#f97316', '#eab308', '#22c55e', '#3b82f6', '#8b5cf6', '#ec4899', '#6b7280'];

  let selectedDeck = $derived(decks.find(d => d.id === selectedDeckId) || null);

  async function loadDecks() {
    loading = true;
    try {
      decks = await getDecks() || [];
    } catch (error) {
      console.error('加载卡组失败:', error);
      decks = [];
    } finally {
      loading = false;
    }
  }

  async function loadCards(deckId) {
    try {
      cards = await getCards(deckId) || [];
    } catch (error) {
      console.error('加载卡片失败:', error);
      cards = [];
    }
  }

  function selectDeck(deckId) {
    selectedDeckId = deckId;
    loadCards(deckId);
  }

  function openCreateDeck() {
    editingDeck = null;
    deckForm = { name: '', language_pair: 'zh-jp', cover_color: '#3b82f6' };
    showDeckModal = true;
  }

  function openEditDeck(deck) {
    editingDeck = deck;
    deckForm = {
      name: deck.name,
      language_pair: deck.language_pair || 'zh-jp',
      cover_color: deck.cover_color || '#3b82f6'
    };
    showDeckModal = true;
  }

  async function handleDeckSubmit() {
    try {
      if (editingDeck) {
        await updateDeck(editingDeck.id, deckForm);
      } else {
        await createDeck(deckForm);
      }
      showDeckModal = false;
      loadDecks();
    } catch (error) {
      console.error('保存卡组失败:', error);
    }
  }

  async function handleDeleteDeck(deckId) {
    if (!confirm('确定要删除这个卡组吗？所有卡片也会被删除。')) return;
    try {
      await deleteDeck(deckId);
      if (selectedDeckId === deckId) {
        selectedDeckId = null;
        cards = [];
      }
      loadDecks();
    } catch (error) {
      console.error('删除卡组失败:', error);
    }
  }

  function openCreateCard() {
    editingCard = null;
    cardForm = { front: '', back: '', tags: '' };
    showCardModal = true;
  }

  function openEditCard(card) {
    editingCard = card;
    cardForm = {
      front: card.front,
      back: card.back,
      tags: (card.tags || []).join(', ')
    };
    showCardModal = true;
  }

  async function handleCardSubmit() {
    if (!selectedDeckId) return;
    const tagsArr = cardForm.tags ? cardForm.tags.split(/[,，]/).map(t => t.trim()).filter(Boolean) : [];
    const payload = { front: cardForm.front, back: cardForm.back, deck_id: selectedDeckId, tags: tagsArr };
    try {
      if (editingCard) {
        await updateCard(editingCard.id, { front: payload.front, back: payload.back, tags: tagsArr });
      } else {
        await createCard(payload);
      }
      showCardModal = false;
      loadCards(selectedDeckId);
    } catch (error) {
      console.error('保存卡片失败:', error);
    }
  }

  async function handleDeleteCard(cardId) {
    if (!confirm('确定要删除这张卡片吗？')) return;
    try {
      await deleteCard(cardId);
      loadCards(selectedDeckId);
    } catch (error) {
      console.error('删除卡片失败:', error);
    }
  }

  onMount(() => {
    loadDecks();
  });
</script>

<div class="decks-page">
  <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px;">
    <h1 class="page-title" style="margin: 0;">卡组管理</h1>
    <button class="btn btn-primary" onclick={openCreateDeck}>+ 新建卡组</button>
  </div>

  {#if loading}
    <div class="empty-state">
      <div class="empty-state-icon">⏳</div>
      <div class="empty-state-text">加载中...</div>
    </div>
  {:else if decks.length === 0}
    <div class="empty-state">
      <div class="empty-state-icon">📚</div>
      <div class="empty-state-text">还没有卡组，点击上方按钮创建第一个卡组</div>
    </div>
  {:else}
    <div class="deck-list">
      {#each decks as deck}
        <div
          class="deck-card"
          class:active={selectedDeckId === deck.id}
          onclick={() => selectDeck(deck.id)}
          style="border-left: 4px solid {deck.cover_color || '#3b82f6'}"
        >
          <div class="deck-info">
            <div class="deck-name">{deck.name}</div>
            <div class="deck-meta">{deck.language_pair || 'zh-jp'}</div>
            <div class="deck-actions" onclick={(e) => e.stopPropagation()}>
              <button class="btn btn-secondary" onclick={() => openEditDeck(deck)}>编辑</button>
              <button class="btn btn-danger" onclick={() => handleDeleteDeck(deck.id)}>删除</button>
            </div>
          </div>
        </div>
      {/each}
    </div>
  {/if}

  {#if selectedDeck}
    <div style="margin-top: 48px;">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px;">
        <h2 style="font-size: 22px; font-weight: 600; color: #111827;">
          {selectedDeck.name} - 卡片列表
        </h2>
        <button class="btn btn-primary" onclick={openCreateCard}>+ 添加卡片</button>
      </div>

      {#if cards.length === 0}
        <div class="empty-state">
          <div class="empty-state-icon">🃏</div>
          <div class="empty-state-text">这个卡组还没有卡片，点击上方按钮添加</div>
        </div>
      {:else}
        <div class="card-list">
          {#each cards as card}
            <div class="card-item">
              <div class="card-item-front">{card.front}</div>
              <div class="card-item-back">{card.back}</div>
              {#if card.tags && card.tags.length > 0}
                <div class="card-item-tags">
                  {#each card.tags as tag}
                    <span class="card-tag">{tag}</span>
                  {/each}
                </div>
              {/if}
              <div class="deck-actions" style="margin-top: 12px;">
                <button class="btn btn-secondary" onclick={() => openEditCard(card)}>编辑</button>
                <button class="btn btn-danger" onclick={() => handleDeleteCard(card.id)}>删除</button>
              </div>
            </div>
          {/each}
        </div>
      {/if}
    </div>
  {/if}
</div>

{#if showDeckModal}
  <div class="modal-overlay" onclick={() => showDeckModal = false} role="dialog">
    <div class="modal-content" onclick={(e) => e.stopPropagation()}>
      <div class="modal-header">
        <div class="modal-title">{editingDeck ? '编辑卡组' : '新建卡组'}</div>
        <button class="btn btn-secondary" onclick={() => showDeckModal = false}>×</button>
      </div>
      <div class="form-group">
        <label class="form-label" for="deck-name">卡组名称</label>
        <input id="deck-name" class="form-input" bind:value={deckForm.name} placeholder="如：日语N2词汇" />
      </div>
      <div class="form-group">
        <label class="form-label" for="deck-lang">语言对</label>
        <input id="deck-lang" class="form-input" bind:value={deckForm.language_pair} placeholder="如：zh-jp, en-zh" />
      </div>
      <div class="form-group">
        <label class="form-label">封面颜色</label>
        <div style="display: flex; gap: 8px; flex-wrap: wrap;">
          {#each presetColors as color}
            <button
              style="width: 32px; height: 32px; border-radius: 6px; cursor: pointer; border: {deckForm.cover_color === color ? '3px solid #111827' : '2px solid transparent'}; background-color: {color};"
              onclick={() => deckForm.cover_color = color}
            ></button>
          {/each}
        </div>
      </div>
      <div style="display: flex; gap: 12px; justify-content: flex-end; margin-top: 24px;">
        <button class="btn btn-secondary" onclick={() => showDeckModal = false}>取消</button>
        <button class="btn btn-primary" onclick={handleDeckSubmit}>保存</button>
      </div>
    </div>
  </div>
{/if}

{#if showCardModal}
  <div class="modal-overlay" onclick={() => showCardModal = false} role="dialog">
    <div class="modal-content" onclick={(e) => e.stopPropagation()}>
      <div class="modal-header">
        <div class="modal-title">{editingCard ? '编辑卡片' : '添加卡片'}</div>
        <button class="btn btn-secondary" onclick={() => showCardModal = false}>×</button>
      </div>
      <div class="form-group">
        <label class="form-label" for="card-front">正面（问题）</label>
        <textarea id="card-front" class="form-textarea" bind:value={cardForm.front} placeholder="请输入卡片正面内容"></textarea>
      </div>
      <div class="form-group">
        <label class="form-label" for="card-back">背面（答案）</label>
        <textarea id="card-back" class="form-textarea" bind:value={cardForm.back} placeholder="请输入卡片背面内容"></textarea>
      </div>
      <div class="form-group">
        <label class="form-label" for="card-tags">标签（逗号分隔，可选）</label>
        <input id="card-tags" class="form-input" bind:value={cardForm.tags} placeholder="如：N2动词, 常用" />
      </div>
      <div style="display: flex; gap: 12px; justify-content: flex-end; margin-top: 24px;">
        <button class="btn btn-secondary" onclick={() => showCardModal = false}>取消</button>
        <button class="btn btn-primary" onclick={handleCardSubmit}>保存</button>
      </div>
    </div>
  </div>
{/if}

<style>
  .card-item-tags {
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
    margin-top: 8px;
  }
  .card-tag {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 4px;
    background-color: #f3f4f6;
    color: #6b7280;
    font-size: 12px;
  }
</style>
