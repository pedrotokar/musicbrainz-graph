<script lang="ts">
    //TODO: lógica de evento existente ou não (dar um embed em um singleton?)
    //TODO: lógica de remoção + componente (componente com  um switch case pra saber como desenha e o q lê dele)
    //TODO: o temido filtro...

    //Svelte imports
    import { onMount } from "svelte";

    //Type Imports
    import type { GraphNode, GraphEdge } from "$lib/types"

    //Modules Imports
    import {GraphInteraction, ExpandInteraction} from "$lib/interactions/abstractInteraction"
    import Graph from '$lib/components/graphs/Graph.svelte';

    //Graph data structure for now
    let nodes: GraphNode[] = $state([]);
    let edges: GraphEdge[] = $state([]);
    let nodeMap: Map<string, GraphNode> = new Map;
    let edgeMap: Map<string, GraphEdge> = new Map;
    let nodeOwnershipMap: Map<string, Set<string>> = new Map;
    let edgeOwnershipMap: Map<string, Set<string>> = new Map;
    $inspect("Loaded nodes and edges were updated: ", nodes, edges);

    //Interaction events (command-like pattern)
    let activeInteractions: GraphInteraction[] = $state([]);
    $inspect("Active interactions: ", activeInteractions);

    let graphChangesCounter = $state(0);

    //TODO: make it generic to any interaction (maybe receive a interaction and the methods get a closure or smt)
    async function expandGraph(artistId: string) {
        try {
            const newInteraction: ExpandInteraction = await ExpandInteraction.create(artistId);
//            const ownedElementsIds = newInteraction.getOwnedElementIds();
            const graphData = newInteraction.getOwnedElements();
            
            for (const newNode of graphData["nodes"]){
                if (!nodeMap.has(newNode.id)){
                    nodes.push(newNode);
                    nodeMap.set(newNode.id, newNode);
                }
                if (!nodeOwnershipMap.has(newNode.id)){
                    nodeOwnershipMap.set(newNode.id, new Set());
                } 
                nodeOwnershipMap.get(newNode.id)?.add(newInteraction.getId());
            }
            for (const newEdge of graphData["edges"]){
                const newEdgeId = newEdge.source + "->" + newEdge.target + "|" + newEdge.type
                if (!edgeMap.has(newEdgeId)){
                    edges.push(newEdge);
                    edgeMap.set(newEdgeId, newEdge)
                }
                if (!edgeOwnershipMap.has(newEdgeId)){
                    edgeOwnershipMap.set(newEdgeId, new Set());
                } 
                edgeOwnershipMap.get(newEdgeId)?.add(newInteraction.getId());
            }

            graphChangesCounter += 1;
            activeInteractions.push(newInteraction);
        
        } catch (e) {
            console.error(e);
        } finally {
            console.log("finished expanding");
        }
    }


    onMount(() => {
        expandGraph("eeb1195b-f213-4ce1-b28c-8565211f8e43").then(() => {}).catch((error) => {console.error(error);});
        setTimeout(() => {expandGraph("d8433dee-d1a8-4b40-b27c-40bc53481167").then(() => {}); }, 5000);
        setTimeout(() => {expandGraph("dc5caa1a-2be6-4104-a34e-fab24dcd4abe").then(() => {}); }, 10000);
        setTimeout(() => {expandGraph("d338e1b0-1f9c-4a4a-9c74-e2ffa4de79b2").then(() => {}); }, 15000);
        setTimeout(() => {expandGraph("21176a1c-bdbf-43d0-aaae-5f2df97b09bd").then(() => {}); }, 20000);
        setTimeout(() => {expandGraph("3a528006-1429-47f4-ae9b-2ea95343e16a").then(() => {}); }, 25000);
        
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
