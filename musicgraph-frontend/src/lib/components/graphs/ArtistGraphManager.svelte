<script lang="ts">
    //TODO: do some logic to prevent duplicated event (maybe singleton logic embeded someway in the class)
    //TODO: add relationship filter...

    //Svelte imports
    import { onMount } from "svelte";

    //Type Imports
    import type { GraphNode, GraphEdge } from "$lib/types"

    //Modules Imports
    import {GraphInteraction, ExpandInteraction} from "$lib/interactions/abstractInteraction"
    import Graph from '$lib/components/graphs/Graph.svelte';
	import InteractionList from "./filters/InteractionList.svelte";

    //Graph data structure for now
    let nodes: GraphNode[] = $state([]);
    let edges: GraphEdge[] = $state([]);
    // eslint-disable-next-line svelte/prefer-svelte-reactivity
    let nodeMap: Map<string, GraphNode> = new Map;
    // eslint-disable-next-line svelte/prefer-svelte-reactivity
    let edgeMap: Map<string, GraphEdge> = new Map;
    // eslint-disable-next-line svelte/prefer-svelte-reactivity
    let nodeOwnershipMap: Map<string, Set<string>> = new Map;
    // eslint-disable-next-line svelte/prefer-svelte-reactivity
    let edgeOwnershipMap: Map<string, Set<string>> = new Map;
    
    let graphChangesCounter = $state(0);

    //Interaction events (command-like pattern)
    let activeInteractions: GraphInteraction[] = $state([]);
    let selectedInteraction: GraphInteraction | undefined = $state();

    function addInteraction(interaction: GraphInteraction){
        try {
            const graphData = interaction.getOwnedElements();
            
            for (const newNode of graphData["nodes"]){
                if (!nodeMap.has(newNode.id)){
                    nodes.push(newNode);
                    nodeMap.set(newNode.id, newNode);
                }
                if (!nodeOwnershipMap.has(newNode.id)){
                    nodeOwnershipMap.set(newNode.id, new Set());
                } 
                nodeOwnershipMap.get(newNode.id)?.add(interaction.getId());
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
                edgeOwnershipMap.get(newEdgeId)?.add(interaction.getId());
            }

            graphChangesCounter += 1;
            activeInteractions.push(interaction);
        } catch (e) {
            console.error("Wasn't abble to add interaction", interaction, e);
        } finally {
            console.log("finished adding interaction", interaction);
        }
    }

    function removeInteraction(interactionId: string){
        const interaction = activeInteractions.find((interaction) => interaction.getId() == interactionId);
        if (interaction){
            try {
                
                const ownedElements = interaction.getOwnedElementIds();

                for(const ownedNodeId of ownedElements["nodes"]){
                    nodeOwnershipMap.get(ownedNodeId)?.delete(interactionId);
                    
                    if (nodeOwnershipMap.get(ownedNodeId)?.size === 0){
                        nodeOwnershipMap.delete(ownedNodeId);
                        nodeMap.delete(ownedNodeId);
                        const index = nodes.findIndex(n => n.id === ownedNodeId);
                        if (index !== -1) nodes.splice(index, 1);
                    }
                }

                for(const ownedEdgeId of ownedElements["edges"]){
                    edgeOwnershipMap.get(ownedEdgeId)?.delete(interactionId);
                    
                    if (edgeOwnershipMap.get(ownedEdgeId)?.size === 0){
                        edgeOwnershipMap.delete(ownedEdgeId);
                        edgeMap.delete(ownedEdgeId);
                        const index = edges.findIndex(e => (e.source + "->" + e.target + "|" + e.type) === ownedEdgeId);
                        if (index !== -1) edges.splice(index, 1);
                    }
                }

                graphChangesCounter += 1;
                const index = activeInteractions.findIndex((interaction) => interaction.getId() == interactionId);
                if (index !== -1) activeInteractions.splice(index, 1);

            } catch (e) {
                console.error("Wasn't abble to remove interaction", interaction, e);
            } finally {
                console.log("finished removing interaction", interaction);
            }
        } else {
            console.log(`Interaction ${interactionId} wasn't present in active interactions`);
        }
    }



    //TODO: improve this, decide where the logic goes
    async function expandArtist(artistId: string) {
        try {
            const newInteraction = await ExpandInteraction.create(artistId);
            selectedInteraction = newInteraction;
            addInteraction(newInteraction);
        } catch (e) {
            console.error(e);
        } finally {
            console.log("finished expanding");
        }
    }


    onMount(() => {
        expandArtist("eeb1195b-f213-4ce1-b28c-8565211f8e43").then(() => {}).catch((error) => {console.error(error);});;
        setTimeout(() => {expandArtist("d8433dee-d1a8-4b40-b27c-40bc53481167").then(() => {}).catch((error) => {console.error(error);}); }, 5000);
        setTimeout(() => {expandArtist("dc5caa1a-2be6-4104-a34e-fab24dcd4abe").then(() => {}).catch((error) => {console.error(error);}); }, 10000);
        setTimeout(() => {expandArtist("d338e1b0-1f9c-4a4a-9c74-e2ffa4de79b2").then(() => {}).catch((error) => {console.error(error);}); }, 15000);
        setTimeout(() => {expandArtist("21176a1c-bdbf-43d0-aaae-5f2df97b09bd").then(() => {}).catch((error) => {console.error(error);}); }, 20000);
        setTimeout(() => {expandArtist("3a528006-1429-47f4-ae9b-2ea95343e16a").then(() => {}).catch((error) => {console.error(error);}); }, 25000);
        setTimeout(() => {expandArtist("b51c672b-85e0-48fe-8648-470a2422229f").then(() => {}).catch((error) => {console.error(error);}); }, 30000);
    })
    
    // $inspect("Active interactions: ", activeInteractions);
    // $inspect("Loaded nodes and edges were updated: ", nodes, edges);
    // $inspect("graphChangesCounter", graphChangesCounter);

    

</script>



<Graph nodes={nodes} edges={edges} graphChangesCounter={graphChangesCounter} onClickCallbackFunction={expandArtist} selectedInteraction={selectedInteraction}/>

<InteractionList activeInteractions={activeInteractions} removeInteractionCallback={removeInteraction}/>

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
