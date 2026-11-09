<script lang="ts">
    //TODO: figure out how to sinalize that an API Error occured
    //TODO: fix all the places where I use an edge ID
    //TODO: Change interaction registry from array to map

    //Svelte imports
    import { onMount } from "svelte";
    import { SvelteSet } from "svelte/reactivity";

    //Type Imports
    import type { GraphNode, GraphEdge, FilterState, EdgeContext } from "$lib/types"

    //Utility Imports
    import { getEdgeId } from "$lib/utils";

    //Modules Imports
    import { GraphInteraction } from "$lib/interactions/abstractInteraction"
    import { ExpandInteraction } from "$lib/interactions/expandInteraction"
    import { PathInteraction } from "$lib/interactions/pathInteraction"
    import { relationshipData } from "./relationships";

    //Component Imports
    import Graph from '$lib/components/graphs/Graph.svelte';
	import InteractionList from "../filters/InteractionList.svelte";
    import RelationshipFilter from "../filters/RelationshipFilter.svelte";
    import ArtistSearch from "../ArtistSearch.svelte";


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
                    const newEdgeId = getEdgeId(newEdge);
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
                        const index = edges.findIndex(e => getEdgeId(e) === ownedEdgeId);
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

    // ------------------ Implementing concurrent expansion ------------------
    // Expansions don't block each other: each node being fetched is tracked in
    // pendingNodeIds and their fetches are running in parallel. This code helps
    // ensuring the camera only follows the latest interaction the user asked
    // for, so a slow response that arrives late won't steal the focus
    const pendingNodeIds = new SvelteSet<string>();
    let lastFocusIntentId: string | undefined = undefined;
    let focusTarget: { nodeId: string, scale: number | undefined } | undefined = $state();

    function requestFocus(nodeId: string | undefined, scale?: number | undefined){
        if (nodeId) focusTarget = { nodeId, scale };
    }

    function selectInteraction(interaction: GraphInteraction){
        selectedInteraction = interaction;
        // Explicit user choice: always becomes the latest intent
        lastFocusIntentId = interaction.getFocusNodeId();
        requestFocus(lastFocusIntentId);
    }

    async function expandArtist(artistId: string) {
        if (pendingNodeIds.has(artistId)) return; // already on its way
        pendingNodeIds.add(artistId);
        lastFocusIntentId = artistId;
        try {
            const newInteraction = await ExpandInteraction.create(artistId);
            if (!activeInteractions.some((interaction) => interaction.getId() == newInteraction.getId())) {
                addInteraction(newInteraction);
            }
            // Only take over selection/camera if the user hasn't asked for something else meanwhile
            if (lastFocusIntentId === artistId) {
                selectedInteraction = newInteraction;
                requestFocus(newInteraction.getFocusNodeId(), 1);
            }
            // applyFilter();
        } catch (e) {
            console.warn("Expand interaction failed:", e instanceof Error ? e.message : e);
        } finally {
            pendingNodeIds.delete(artistId);
            console.log("finished expanding");
        }
    }

    // ------------------ Implementing shortest path search flux ------------------
    const pendingPathKeys = new SvelteSet<string>();
    let isPathSearchOpen = $state(false);
    let pathSourceArtist: GraphNode | undefined = $state();

    function startPathSearch(sourceArtistId: string) {
        const artist = nodeMap.get(sourceArtistId) || nodes.find(n => n.id === sourceArtistId);
        if (artist) {
            pathSourceArtist = artist;
            isPathSearchOpen = true;
        }
    }

    function closePathSearch() {
        isPathSearchOpen = false;
        pathSourceArtist = undefined;
    }

    async function handlePathTargetSelected(targetArtistId: string) {
        const sourceId = pathSourceArtist?.id;
        closePathSearch();
        if (sourceId) {
            await findPath(sourceId, targetArtistId);
        }
    }

    async function findPath(sourceArtistId: string, targetArtistId: string) {
        if (sourceArtistId === targetArtistId) {
            console.warn("Source and target must be different artists.");
            return;
        }
        const pathKey = `${sourceArtistId}->${targetArtistId}`;
        if (pendingPathKeys.has(pathKey)) return;
        pendingPathKeys.add(pathKey);
        lastFocusIntentId = targetArtistId;

        try {
            const newInteraction = await PathInteraction.create(sourceArtistId, targetArtistId);
            if (!activeInteractions.some((interaction) => interaction.getId() == newInteraction.getId())) {
                addInteraction(newInteraction);
            }
            if (lastFocusIntentId === targetArtistId) {
                selectedInteraction = newInteraction;
                requestFocus(newInteraction.getFocusNodeId(), 1);
            }
        } catch (e) {
            console.warn("Path interaction failed:", e instanceof Error ? e.message : e);
        } finally {
            pendingPathKeys.delete(pathKey);
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
        const edgeOwners = edgeOwnershipMap.get(getEdgeId(edge));
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
        // setTimeout(() => {expandArtist("dc5caa1a-2be6-4104-a34e-fab24dcd4abe").then(() => {}).catch((error) => {console.error(error);}); }, 10000);
        // setTimeout(() => {expandArtist("d338e1b0-1f9c-4a4a-9c74-e2ffa4de79b2").then(() => {}).catch((error) => {console.error(error);}); }, 15000);
        // setTimeout(() => {expandArtist("21176a1c-bdbf-43d0-aaae-5f2df97b09bd").then(() => {}).catch((error) => {console.error(error);}); }, 20000);
        // setTimeout(() => {expandArtist("3a528006-1429-47f4-ae9b-2ea95343e16a").then(() => {}).catch((error) => {console.error(error);}); }, 25000);
        // setTimeout(() => {expandArtist("b51c672b-85e0-48fe-8648-470a2422229f").then(() => {}).catch((error) => {console.error(error);}); }, 30000);
        // setTimeout(() => {expandArtist("ba550d0e-adac-4864-b88b-407cab5e76af").then(() => {}).catch((error) => {console.error(error);}); }, 35000);
    })
    
    // $inspect("Active interactions: ", activeInteractions);
    // $inspect("Loaded nodes and edges were updated: ", nodes, edges);
    // $inspect("graphChangesCounter", graphChangesCounter);
    // $inspect("Active filters", activeFilters);
    // $inspect("Focus target", focusTarget);

    

</script>

<div class="graph-layout">
    <div class="graph-canvas">
        <Graph nodes={filteredNodes} edges={filteredEdges} onClickCallbackFunction={expandArtist} onRequestPathFunction={startPathSearch} selectedInteraction={selectedInteraction} activeFilters={activeFilters} pendingNodeIds={pendingNodeIds} focusTarget={focusTarget}/>
    </div>
    
    <div class="hud-overlay">
        <div class="hud-panel color-legend-filter">
            <RelationshipFilter activeFilters={activeFilters}/>
        </div>
        
        <div class="hud-panel interaction-list">
            <InteractionList activeInteractions={activeInteractions} selectedInteraction={selectedInteraction} removeInteractionCallback={removeInteraction} selectInteractionCallback={selectInteraction}/>
        </div>
        
        <div class="hud-panel search-bar">
            <ArtistSearch onArtistSelectFunction={expandArtist}/>
        </div>
        
    </div>

    {#if isPathSearchOpen && pathSourceArtist}
        <div class="modal-backdrop" onclick={closePathSearch} role="presentation">
            <!-- svelte-ignore a11y_click_events_have_key_events -->
            <!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
            <div class="modal-dialog" onclick={(e) => e.stopPropagation()} role="dialog" aria-modal="true" tabindex="-1">
                <div class="modal-header">
                    <div>
                        <h3>Traçar caminho mais curto</h3>
                        <p class="modal-subtitle">Origem: <strong>{pathSourceArtist.display_name}</strong></p>
                    </div>
                    <button type="button" class="modal-close-btn" onclick={closePathSearch} aria-label="Fechar">✕</button>
                </div>
                <div class="modal-body">
                    <p class="modal-instruction">Selecione o artista de destino:</p>
                    <div class="modal-search-wrapper">
                        <ArtistSearch onArtistSelectFunction={handlePathTargetSelected} />
                    </div>
                </div>
            </div>
        </div>
    {/if}
</div>


<!-- {#each nodes as node (node.id)}    
<p>
    {node.id} - {node.display_name}
</p>
{/each}

{#each edges as edge (getEdgeId(edge))}
<p>
    {edge.source} -> {edge.target} - {edge.type}
</p>
{/each} -->



<style>
.graph-layout {
    position: relative;
    width: 100%;
    height: 100%;
    overflow: hidden;
}

.graph-canvas {
    position: absolute;
    z-index: 0;
    inset: 0;
}

.hud-overlay {
    position: absolute;
    z-index: 10;
    inset: 0;
    pointer-events: none;
}

.hud-panel {
    position: absolute;
    pointer-events: auto;
    background: #feffc0;

    backdrop-filter: blur(8px);
    border-radius: 8px;
    box-shadow: 0 4px 12px #00000052;
    border: 1px solid #000000;
}

.search-bar {
    top: 20px;
    left: 90%;
    transform: translateX(-50%);
    width: 300px;
}

.interaction-list {
    bottom: 20px;
    left: 30px;
    width: 450px;

    max-height: calc(100% - 120px);
    overflow-y: auto;
}

.color-legend-filter {
    top: 20px;
    left: 20px;
}

.modal-backdrop {
    position: fixed;
    inset: 0;
    z-index: 100;
    background: rgba(0, 0, 0, 0.6);
    backdrop-filter: blur(4px);
    display: flex;
    align-items: center;
    justify-content: center;
}

.modal-dialog {
    background: #ffffff;
    border-radius: 12px;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
    width: 440px;
    max-width: 90vw;
    padding: 24px;
    display: flex;
    flex-direction: column;
    gap: 16px;
    position: relative;
    border: 1px solid #e2e8f0;
}

.modal-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
}

.modal-header h3 {
    margin: 0;
    font-size: 18px;
    color: #0f172a;
}

.modal-subtitle {
    margin: 4px 0 0 0;
    font-size: 13px;
    color: #64748b;
}

.modal-subtitle strong {
    color: #1e293b;
}

.modal-close-btn {
    background: none;
    border: none;
    font-size: 16px;
    color: #94a3b8;
    cursor: pointer;
    padding: 4px 8px;
    border-radius: 6px;
}

.modal-close-btn:hover {
    background: #f1f5f9;
    color: #0f172a;
}

.modal-instruction {
    margin: 0 0 8px 0;
    font-size: 13px;
    color: #475569;
}

.modal-search-wrapper {
    position: relative;
    width: 100%;
}

</style>
