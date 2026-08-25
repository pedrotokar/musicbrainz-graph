<script lang="ts">
    import { relationshipData } from "$lib/components/graphs/relationships";

    let legendItems = relationshipData;
</script>

<ul class="color-legend">
    {#each Object.entries(legendItems) as relationship (relationship[0])}
        {#if relationship[1].bidirectional}
            <li class="color-legend-line">
                <span class="color-legend-box"
                      style="background-color: {relationship[1].color};"></span>
                {relationship[1].displayName}
            </li>
        {:else}
            <li class="color-legend-line">
                <span class="color-legend-box"
                      style="background-color: {relationship[1].forward.color};"></span>
                {relationship[1].forward.displayName}
            </li>
            <li class="color-legend-line">
                <span class="color-legend-box"
                      style="background-color: {relationship[1].backward.color};"></span>
                {relationship[1].backward.displayName}
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
    }
</style>

