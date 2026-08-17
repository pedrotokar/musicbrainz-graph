<script lang="ts">

    //Svelte imports
    import { onMount } from "svelte";

    //Type Imports
    import type { GraphNode, GraphEdge } from "$lib/types"

    //Modules Imports
    import { getArtistRelationships } from '$lib/fetcher/api-fetcher';
    import Graph from '$lib/components/graphs/Graph.svelte';



    let nodes: GraphNode[] = $state([]);
    let edges: GraphEdge[] = $state([]);
    $inspect("Loaded nodes and edges were updated: ", nodes, edges);

    let graphChangesCounter = $state(0);

    //TODO: IMPROVE THAT! AT MINIMUN USE A MAP OR SOMETHING LIKE THAT
    function expandGraph(artistId: string) {
        getArtistRelationships(artistId).then((graphData) => {
            for (const newNode of graphData["nodes"]){
                if (!nodes.some(node => node["id"] == newNode["id"])){
                    nodes.push(newNode);
                }
            }
            for (const newEdge of graphData["edges"]){
                let repeatedEdge = edges.some(
                    edge => edge["source"] == newEdge["source"] && edge["target"] == newEdge["target"] && edge["type"] == newEdge["type"]
                )
                if (!repeatedEdge){
                    edges.push(newEdge);
                }
            }
            graphChangesCounter += 1;
        }).catch((error) => 
            {console.error(error)}
        );
    }

    onMount(() => {
        getArtistRelationships("eeb1195b-f213-4ce1-b28c-8565211f8e43").then((graphData) => {
            nodes = graphData["nodes"];
            edges = graphData["edges"];
            // for (const node in graphData["nodes"]){
            //     nodeMap.set(node["id"], node);
            // }
            graphChangesCounter += 1;
        }).catch((error) => {
            console.error(error);
        });
        setTimeout(() => {expandGraph("d8433dee-d1a8-4b40-b27c-40bc53481167"); }, 5000);
        setTimeout(() => {expandGraph("dc5caa1a-2be6-4104-a34e-fab24dcd4abe"); }, 10000);
        setTimeout(() => {expandGraph("d338e1b0-1f9c-4a4a-9c74-e2ffa4de79b2"); }, 15000);
        setTimeout(() => {expandGraph("21176a1c-bdbf-43d0-aaae-5f2df97b09bd"); }, 20000);
        setTimeout(() => {expandGraph("3a528006-1429-47f4-ae9b-2ea95343e16a"); }, 25000);
        
    })

</script>

<Graph nodes={nodes} edges={edges} graphChangesCounter={graphChangesCounter} onClickCallbackFunction={expandGraph}/>

{#each nodes as node (node.id)}    
<p>
    {node.id} - {node.display_name}
</p>
{/each}

{#each edges as edge (edge.source + "->" + edge.target + "|" + edge.type)}
<p>
    {edge.source} -> {edge.target} - {edge.type}
</p>
{/each}



<style>

</style>
