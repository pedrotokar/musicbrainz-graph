<script lang="ts">
    //TODO: figure out how to sinalize that an API Error occured
    //TODO: fix all the places where I use an edge ID
    //TODO: Change interaction registry from array to map

    //Svelte imports
    import { onMount } from "svelte";

    //Type Imports
    import type { GraphNode, GraphEdge, FilterState, EdgeContext } from "$lib/types"

    //Modules Imports
    import { GraphInteraction } from "$lib/interactions/abstractInteraction"
    import { ExpandInteraction } from "$lib/interactions/expandInteraction";
    import { relationshipData } from "./relationships";

    //Component Imports
    import Graph from '$lib/components/graphs/Graph.svelte';
	import InteractionList from "../filters/InteractionList.svelte";
    import RelationshipFilter from "../filters/RelationshipFilter.svelte";


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
    let edgeOwnershipMap: Map<string, Map<string, EdgeContext>> = new Map;
    
    // let graphChangesCounter = $state(0);

    
    // ------------------ Implementing interaction handling ------------------
    //                         (command-like pattern)
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
                const relativeDirection = interaction.getEdgeContext(newEdge);
                if(relativeDirection){
                    const newEdgeId = newEdge.source + "->" + newEdge.target + "|" + newEdge.type
                    if (!edgeMap.has(newEdgeId)){
                        edges.push(newEdge);
                        edgeMap.set(newEdgeId, newEdge)
                    }
                    if (!edgeOwnershipMap.has(newEdgeId)){
                        edgeOwnershipMap.set(newEdgeId, new Map());
                    } 
                    edgeOwnershipMap.get(newEdgeId)?.set(interaction.getId(), relativeDirection);
                } else {
                    continue;
                }
            }
            
            // graphChangesCounter += 1;
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

                // graphChangesCounter += 1;
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

    function selectInteraction(interaction: GraphInteraction){
        selectedInteraction = interaction;
    }

    //TODO: improve this, decide where the logic goes
    async function expandArtist(artistId: string) {
        try {
            const newInteraction = await ExpandInteraction.create(artistId);
            selectedInteraction = newInteraction;
            if (!activeInteractions.some((interaction) => interaction.getId() == newInteraction.getId())) addInteraction(newInteraction);
            // applyFilter();
        } catch (e) {
            console.error(e);
        } finally {
            console.log("finished expanding");
        }
    }

    // ------------------ Implementing filtering handling ------------------

    //Filter state
    let activeFilters: FilterState = $state(initiateFilterState());

    function initiateFilterState(){
        const initialState: FilterState = {};
        for (const [key, config] of Object.entries(relationshipData)) {
            if (config.bidirectional) {
                initialState[key] = { bidirectional: true, show: true };
            } else {
                initialState[key] = { bidirectional: false, showForward: true, showBackward: true };
            }
        }
        return initialState;
    };

    function auxGetEdgeVisibility(edge: GraphEdge, interactionId: string, direction: EdgeContext){
        const interaction = activeInteractions.find(
            (interaction) => interaction.getId() == interactionId
        );
        const interactionLock = interaction?.shouldAlwaysShowEdge(edge);

        let filterLock;
        const filterStatus = activeFilters[edge.type];
        if(filterStatus.bidirectional) {
            filterLock = filterStatus.show;
        } else {
            if (direction == "forward") filterLock = filterStatus.showForward;
            else if (direction == "backward") filterLock = filterStatus.showBackward;
        }

        return filterLock || interactionLock;
    }

    let filteredEdges: GraphEdge[] = $derived(edges.filter((edge) => {
        const edgeOwners = edgeOwnershipMap.get(edge.source + "->" + edge.target + "|" + edge.type);
        if(edgeOwners){
            for(const [interactionId, direction] of edgeOwners){
                if(auxGetEdgeVisibility(edge, interactionId, direction)) return true;
            }
            return false;
        } else {
            console.error(`Edge ${edge} does not have any owner!`);
            return false;
        }
    }))


    function auxGetNodeVisibility(node: GraphNode, interactionId: string){
        const interaction = activeInteractions.find(
            (interaction) => interaction.getId() == interactionId
        )
        return interaction?.shouldAlwaysShowNode(node);
    }

    let filteredNodes: GraphNode[] = $derived.by(() => {
        // eslint-disable-next-line svelte/prefer-svelte-reactivity
        const nodeMask: Map<string, number> = new Map();
        filteredEdges.forEach((edge) => {
            nodeMask.set(edge.source, (nodeMask.get(edge.source) || 0) + 1);
            nodeMask.set(edge.target, (nodeMask.get(edge.target) || 0) + 1);
        })
        return nodes.filter((node) => {
            const nodeOwners = nodeOwnershipMap.get(node.id);
            if(nodeOwners){
                //If any interaction requires node presence, then fix it
                for(const interactionId of nodeOwners){
                    if(auxGetNodeVisibility(node, interactionId)) return true;
                }
                //Otherwise do it based on the incoming edge count
                const incomingEdgeCount = nodeMask.get(node.id);
                if (incomingEdgeCount) return incomingEdgeCount > 0
                return false;
            } else {
                console.error(`Node ${node} does not have any owner!`);
                return false;
            }
        })
    })

    onMount(() => {
        expandArtist("eeb1195b-f213-4ce1-b28c-8565211f8e43").then(() => {}).catch((error) => {console.error(error);});
        setTimeout(() => {expandArtist("d8433dee-d1a8-4b40-b27c-40bc53481167").then(() => {}).catch((error) => {console.error(error);}); }, 5000);
        setTimeout(() => {expandArtist("dc5caa1a-2be6-4104-a34e-fab24dcd4abe").then(() => {}).catch((error) => {console.error(error);}); }, 10000);
        setTimeout(() => {expandArtist("d338e1b0-1f9c-4a4a-9c74-e2ffa4de79b2").then(() => {}).catch((error) => {console.error(error);}); }, 15000);
        setTimeout(() => {expandArtist("21176a1c-bdbf-43d0-aaae-5f2df97b09bd").then(() => {}).catch((error) => {console.error(error);}); }, 20000);
        setTimeout(() => {expandArtist("3a528006-1429-47f4-ae9b-2ea95343e16a").then(() => {}).catch((error) => {console.error(error);}); }, 25000);
        setTimeout(() => {expandArtist("b51c672b-85e0-48fe-8648-470a2422229f").then(() => {}).catch((error) => {console.error(error);}); }, 30000);
        setTimeout(() => {expandArtist("ba550d0e-adac-4864-b88b-407cab5e76af").then(() => {}).catch((error) => {console.error(error);}); }, 35000);
    })
    
    // $inspect("Active interactions: ", activeInteractions);
    // $inspect("Loaded nodes and edges were updated: ", nodes, edges);
    // $inspect("graphChangesCounter", graphChangesCounter);
    // $inspect("Active filters", activeFilters);

    

</script>


<Graph nodes={filteredNodes} edges={filteredEdges} onClickCallbackFunction={expandArtist} selectedInteraction={selectedInteraction}/>

<RelationshipFilter activeFilters={activeFilters}/>

<InteractionList activeInteractions={activeInteractions} removeInteractionCallback={removeInteraction} selectInteractionCallback={selectInteraction}/>

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
