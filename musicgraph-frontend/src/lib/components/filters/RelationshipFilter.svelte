<script lang="ts">
    import { relationshipData } from "$lib/components/graphs/relationships";

    let { activeFilters = $bindable() } = $props();

    let legendItems = relationshipData;

</script>

<ul class="color-legend">
    {#each Object.entries(legendItems) as relationship (relationship[0])}
        {#if relationship[1].bidirectional}
            <li class="color-legend-line">
                <button 
                    type="button" 
                    class="legend-filter-btn {activeFilters[relationship[0]].show ? '' : 'inactive'}"
                    aria-pressed={activeFilters[relationship[0]].show}
                    onclick={() => { activeFilters[relationship[0]].show = !activeFilters[relationship[0]].show }}>
                    <span class="color-legend-box"
                          style="--box-color: {relationship[1].color};"></span>
                    <span class="color-legend-text">{relationship[1].displayName}</span>
                </button>
            </li>
        {:else}
            <li class="color-legend-line">
                <button 
                    type="button" 
                    class="legend-filter-btn {activeFilters[relationship[0]].showForward ? '' : 'inactive'}"
                    aria-pressed={activeFilters[relationship[0]].showForward}
                    onclick={() => { activeFilters[relationship[0]].showForward = !activeFilters[relationship[0]].showForward }}>
                    <span class="color-legend-box"
                          style="--box-color: {relationship[1].forward.color};"></span>
                    <span class="color-legend-text">{relationship[1].forward.displayName}</span>
                </button>
            </li>
            <li class="color-legend-line">
                <button 
                    type="button" 
                    class="legend-filter-btn {activeFilters[relationship[0]].showBackward ? '' : 'inactive'}"
                    aria-pressed={activeFilters[relationship[0]].showBackward}
                    onclick={() => { activeFilters[relationship[0]].showBackward = !activeFilters[relationship[0]].showBackward }}>
                    <span class="color-legend-box"
                          style="--box-color: {relationship[1].backward.color};"></span>
                    <span class="color-legend-text">{relationship[1].backward.displayName}</span>
                </button>
            </li>
        {/if}
    {/each}
</ul>

<style>
    .color-legend {
        list-style: none;
    }

    .color-legend-line {
        cursor: pointer;
    }

    .color-legend-box {
        display: inline-block;
        width: 1em;
        height: 1em;
        border-radius: 2px;
        border-style: solid;
        border-width: 2px;
        border-color: black;
        background-color: var(--box-color);
        transition: background-color 0.2s ease;
    }

    .legend-filter-btn {
        background: none;
        border: none;
        padding: 0;
        margin: 0;
        font: inherit;
        color: inherit;
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 8px; /* space between color box and text */
        width: 100%; /* The click area takes the whole width of the component */
        text-align: left;
    }

    .legend-filter-btn.inactive .color-legend-box {
        background-color: #ccc;
    }

    .legend-filter-btn.inactive .color-legend-text {
        text-decoration: line-through;
        color: #888;
}
    
</style>

