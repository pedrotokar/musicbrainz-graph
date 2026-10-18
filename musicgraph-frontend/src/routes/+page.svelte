<script>
    import ArtistGraphManager from '$lib/components/graphs/ArtistGraphManager.svelte';
</script>

<div class="page-container">
    <h1>Music Graph Explorer</h1>
    <div class="manager-area">
        <ArtistGraphManager />
    </div>
</div>

<style>
    .page-container {
        display: flex;
        flex-direction: column;
        width: 100%;
        height: 100%;
        overflow: hidden;
    }

    h1 {
        margin: 0;
        padding: 8px 16px;
        flex-shrink: 0;
        font-size: 1.25rem;
    }

    .manager-area {
        flex: 1;
        position: relative;
        overflow: hidden;
    }
</style>
