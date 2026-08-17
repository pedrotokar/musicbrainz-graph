<script lang="ts">
    /* How does this component work?

    Its main and only purporse is to display the graph and manage interactive
    events based on the graph. It DOESN'T do anything related to managing
    the original graph data structure nor it does implement any interactive
    feature that isn't based/done on the original graph plot.

    We receive the nodes, the edges, an counter variable so we know the 
    original graph data changed and a click callback function. We don't want 
    to mess our original graph data with the d3 physics simulation variables, 
    so we have an internal copy of the nodes that is actually used by the d3 
    simulation. 
    
    So, when the data gets updated externally, we need to:
    1 - add the new nodes and their related edges to the simulation
    2 - trigger the simulation restart with the diffed data
    We have a function to do 1 and other to do 2. And we trigger it in a effect
    that only listens to our change indicator. When a click is issued on any
    node, the callback function is called with the node id, leaving to the
    parent ID how to actually change the original grpah data. 
    
    Also the node displaying is handled by Svelte, and not d3. This makes
    adding some auxiliary styles on the graph an easier task. d3 only changes
    the underlying node simulation data, that is reflected on the screen by
    svelte.
    */

    //TODO: Improve clicking by having a loading state and by doing some other things idk

    //Svelte and D3 imports
    import { onMount, untrack } from "svelte";
    import * as d3 from "d3";
    import type { D3ZoomEvent, ZoomBehavior, D3DragEvent, DragBehavior } from "d3";

    //Type imports
    import type { GraphNode, GraphEdge, SimulationNode, SimulationEdge } from "$lib/types";

    let { nodes, edges, graphChangesCounter, onClickCallbackFunction } = $props();

    let simulationNodes: SimulationNode[] = $state([])
    let simulationEdges: SimulationEdge[] = $state([])

    let width: number = 1280;
    let height: number = 720;
    let svgNode: SVGSVGElement | undefined = $state();

    // ------------------ Implementing outside data merging ------------------

    function syncSimulationGraph(outsideNodes: GraphNode[], outsideEdges: GraphEdge[]){
        let simulationNodesMap = new Map(simulationNodes.map(n => [n.id, n]));

        simulationNodes = outsideNodes.map((outsideNode) => {
            const simulationNode = simulationNodesMap.get(outsideNode.id);
            if (simulationNode){
                return {
                    ...outsideNode,
                    x: simulationNode.x,
                    y: simulationNode.y,
                    vx: simulationNode.vx,
                    vy: simulationNode.vy
                }
            } else {
                return {... outsideNode};
            }
        });

        simulationNodesMap = new Map(simulationNodes.map(n => [n["id"], n]));
        simulationEdges = outsideEdges.flatMap((outsideEdge) => {
            const sourceNode = simulationNodesMap.get(outsideEdge.source);
            const targetNode = simulationNodesMap.get(outsideEdge.target);
            if(sourceNode && targetNode){
                return {
                    ...outsideEdge,
                    source: sourceNode,
                    target: targetNode
                };
            }
            else{
                return []
            }
        })
    }

    // ------------------ Implementing interaction features ------------------
    
    // Used to implement the click feature.
    function onNodeClick(node: SimulationNode){
        onClickCallbackFunction(node.id);
    }

    // Used to implement the drag feature. D3 only helps handling the physics 
    // and not the screen writing.
    
    function draggable(node: SimulationNode){
        return (nodeElement: SVGElement) => {

            const drag: DragBehavior<SVGElement, SimulationNode, SimulationNode> = d3.drag<SVGElement, SimulationNode, SimulationNode>()
                .on("start", (event: D3DragEvent<SVGElement, SimulationNode, SimulationNode>) => {
                    if (!event.active) simulation.alphaTarget(0.3).restart();
                    node.fx = node.x;
                    node.fy = node.y;
                })
                .on("drag", (event: D3DragEvent<SVGElement, SimulationNode, SimulationNode>) => {
                    node.fx = event.x;
                    node.fy = event.y;
                })
                .on("end", (event: D3DragEvent<SVGElement, SimulationNode, SimulationNode>) => {
                    if (!event.active) simulation.alphaTarget(0);
                    node.fx = null;
                    node.fy = null;
                });

            d3.select(nodeElement).datum(node).call(drag);
            return () => {
                d3.select(nodeElement).on(".drag", null);
            }
        }

    }

    // Used to implement the zooming feature. D3 only helps giving the
    // information on how I should update the svg, and not in updating it
    let zoomAppliedTransform: {x: number, y: number, k: number} = $state({x: 0, y: 0, k: 1})

    function onZoom(event: D3ZoomEvent<SVGSVGElement, unknown>){
        zoomAppliedTransform.x = event.transform.x;
        zoomAppliedTransform.y = event.transform.y;
        zoomAppliedTransform.k = event.transform.k;
    }

    let zoomBehavior: ZoomBehavior<SVGSVGElement, unknown> = d3.zoom<SVGSVGElement, unknown>().on("zoom", onZoom);

    // ------------------ Implementing simulation management ------------------
    let simulation: d3.Simulation<SimulationNode, SimulationEdge>;

    function setupSimulation(){
        simulation = d3.forceSimulation(simulationNodes)
            .force("link", d3.forceLink<SimulationNode, SimulationEdge>(simulationEdges).id((d) => d.id).distance(100))
            .force("charge", d3.forceManyBody().strength(-300))
            .force("center", d3.forceCenter(0, 0));
        if(svgNode){
            d3.select<SVGSVGElement, unknown>(svgNode).call(zoomBehavior);
        } else {
            console.error("Somehow setupSimulation was called before the svg was \
             drawn and consequently when svgNode variable is still undefined")
        }
        // setInterval(() => {simulation.stop()}, 5000)
        console.log("Setup initial graph simulation");
    }
    
    function updateSimulation() {
        if(simulation){
            simulation.nodes(simulationNodes);
            const linkForce = simulation.force("link") as d3.ForceLink<SimulationNode, SimulationEdge>
            linkForce!.links(simulationEdges);
            simulation.alpha(1).restart();
            
            console.log("Updated Graph simulation with synced nodes");
        } else {
            console.error("Somehow updateSimulation was called before the \
            simulation var was actually initialised with a simulation")
        }

    }

    // ------------------ Implementing orchestration based on events ------------------

    $effect(() => {
        console.log(graphChangesCounter);
        if(!simulation){
            return;
        }
        untrack(() => {
            syncSimulationGraph(nodes, edges);
            updateSimulation();
        })
    })

    onMount(() => {
        setupSimulation();
        syncSimulationGraph(nodes, edges)
        updateSimulation();
    })


</script>

<h1>O grafo vai entrar aqui em algum momento com uma tag canvas I guess (na real era svg)</h1>

<svg id="ArtistGraphSVG"
     width="{width}" height="{height}"
     viewBox="{-width/2}, {-height/2}, {width}, {height}"
     bind:this={svgNode}
>
    <g stroke="#999" stroke-width="1.5" class="edges" transform="translate({zoomAppliedTransform.x}, {zoomAppliedTransform.y}) scale({zoomAppliedTransform.k})">
        {#each simulationEdges as edge (edge.source.id + "->" + edge.target.id + "|" + edge.type)}
            <line class="edge {edge.type}"
                //marker-end="url(#arrowhead-{edge.type})"
                x1={edge.source.x} y1={edge.source.y}
                x2={edge.target.x} y2={edge.target.y}/>
        {/each}
    </g>
    <g class="nodes" transform="translate({zoomAppliedTransform.x}, {zoomAppliedTransform.y}) scale({zoomAppliedTransform.k})">
        {#each simulationNodes as node (node.id)}
            <!-- <g transform="translate({node.x},{node.y})" on:click={() => {addNodeRelations(node.id); simulation.nodes(nodes); simulation.force("link").links(edges); simulation.alpha(1).restart();}}> -->
            <g transform="translate({node.x},{node.y})" 
               {@attach draggable(node)} 
               onclick={() => onNodeClick(node)} onkeydown={() => onNodeClick(node)} 
               role="button" tabindex="0"
               >
                <circle r="20" fill="blue"/>
                <text dy="0.35em" text-anchor="middle" dominant-baseline="middle" font-size="10px">{node.display_name}</text> 
            </g>
        {/each}
    </g>
    
</svg>

<div class="tooltip"></div>

<style>
    #ArtistGraphSVG {
        border-style: solid;
        border-radius: 4px;
        border-color: purple;
    }
</style>
