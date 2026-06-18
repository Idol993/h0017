<script>
  import { onMount } from 'svelte';
  import Today from './routes/Today.svelte';
  import Decks from './routes/Decks.svelte';
  import Stats from './routes/Stats.svelte';
  import Import from './routes/Import.svelte';

  let currentRoute = $state('today');

  const routes = {
    today: Today,
    decks: Decks,
    stats: Stats,
    import: Import
  };

  const navItems = [
    { id: 'today', label: '今日学习' },
    { id: 'decks', label: '卡组管理' },
    { id: 'stats', label: '统计' },
    { id: 'import', label: '导入' }
  ];

  function navigate(route) {
    currentRoute = route;
    window.history.pushState({}, '', `#${route}`);
  }

  onMount(() => {
    const hash = window.location.hash.slice(1);
    if (hash && routes[hash]) {
      currentRoute = hash;
    }
    window.addEventListener('popstate', () => {
      const newHash = window.location.hash.slice(1);
      if (newHash && routes[newHash]) {
        currentRoute = newHash;
      }
    });
  });
</script>

<div class="app">
  <nav class="navbar">
    <div class="nav-brand">间隔重复卡片</div>
    <div class="nav-links">
      {#each navItems as item}
        <button
          class={currentRoute === item.id ? 'nav-link active' : 'nav-link'}
          onclick={() => navigate(item.id)}
        >
          {item.label}
        </button>
      {/each}
    </div>
  </nav>
  <main class="main-content">
    {#if currentRoute === 'today'}
      <Today />
    {:else if currentRoute === 'decks'}
      <Decks />
    {:else if currentRoute === 'stats'}
      <Stats />
    {:else if currentRoute === 'import'}
      <Import />
    {/if}
  </main>
</div>
