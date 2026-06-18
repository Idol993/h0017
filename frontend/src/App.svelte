<script>
  import { onMount } from 'svelte';
  import Today from './routes/Today.svelte';
  import Decks from './routes/Decks.svelte';
  import Stats from './routes/Stats.svelte';
  import Import from './routes/Import.svelte';

  let currentRoute = $state('today');

  const routeMap = {
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
    if (hash && routeMap[hash]) {
      currentRoute = hash;
    }
    const handlePop = () => {
      const newHash = window.location.hash.slice(1);
      if (newHash && routeMap[newHash]) {
        currentRoute = newHash;
      }
    };
    window.addEventListener('popstate', handlePop);
    return () => window.removeEventListener('popstate', handlePop);
  });
</script>

<div class="app">
  <nav class="navbar">
    <div class="nav-brand">间隔重复卡片</div>
    <div class="nav-links">
      {#each navItems as item}
        <button
          class="nav-link"
          class:active={currentRoute === item.id}
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
