import type { GraphEdge, GraphNode, NodeContext, EdgeContext, PathAPIResponse } from "$lib/types";
import { GraphInteraction } from './abstractInteraction';
import { getArtistShortestPath } from '$lib/fetcher/api-fetcher';
import { getEdgeId } from '$lib/utils';

export class PathInteraction extends GraphInteraction {

    static #instances: Map<string, WeakRef<PathInteraction>> = new Map();
    static #registry = new FinalizationRegistry((key: string) => {
        PathInteraction.#instances.delete(key);
        console.log(`GC destructed an interaction. Key '${key}' removed from PathInteraction singleton registry`);
    });

    private sourceNodeName: string;
    private targetNodeName: string;

    private pathNodeIds: string[];
    private pathEdges: GraphEdge[];
    private positionById: Map<string, number>;
    private positionByEdgeKey: Map<string, number>;

    private constructor(
        interactionAPIResponse: PathAPIResponse, 
        private sourceNodeId: string,
        private targetNodeId: string
    ){
        super(crypto.randomUUID(), interactionAPIResponse);
        const sourceArtistNode = interactionAPIResponse.nodes.find((node) => node.id === sourceNodeId);
        const targetArtistNode = interactionAPIResponse.nodes.find((node) => node.id === targetNodeId);
        if (sourceArtistNode && targetArtistNode){
            this.sourceNodeName = sourceArtistNode.display_name;
            this.targetNodeName = targetArtistNode.display_name;

            this.pathNodeIds = interactionAPIResponse.path;
            this.pathEdges = interactionAPIResponse.edges;

            this.positionById = new Map();
            for (let i = 0; i < this.pathNodeIds.length; i++) {
                this.positionById.set(this.pathNodeIds[i], i);
            }

            this.positionByEdgeKey = new Map();
            for (let i = 0; i < this.pathEdges.length; i++) {
                this.positionByEdgeKey.set(getEdgeId(this.pathEdges[i]), i);
            }
        } else {
            throw new Error("Path interaction API response did not include the source or target node.");
        }
    }

    static async create(sourceNodeId: string, targetNodeId: string): Promise<PathInteraction>{
        const key = `${sourceNodeId}->${targetNodeId}`;
        //Singleton logic
        if (this.#instances.has(key)) {
            const ref = this.#instances.get(key);
            if(ref !== undefined){
                const previousInstance = ref.deref(); // Tries to get the object from the weak ref. If it still exists then its returned
                if (previousInstance !== undefined) {
                    console.log(`Factory: returning existing instance for PathInteraction with source artist id '${sourceNodeId}' and target artist id '${targetNodeId}'`);
                    return previousInstance;
                }
            }
        }

        const graphData = await getArtistShortestPath(sourceNodeId, targetNodeId);
        const newInstance = new PathInteraction(graphData, sourceNodeId, targetNodeId);
        
        this.#instances.set(key, new WeakRef(newInstance));
        this.#registry.register(newInstance, key); //This is used to notify the instance has been deleted and thus delete the key
        return newInstance;
    }

    getShowText(): string {
        return this.sourceNodeName + " -> " + this.targetNodeName;
    }

    getFocusNodeId(): string | undefined {
        return this.targetNodeId;
    }

    getNodeContext(node: GraphNode): NodeContext {
        const pos = this.positionById.get(node.id);
        if (pos === undefined) {
            return { 
                role: "unrelated" 
            };
        }
        if (pos === 0) {
            return { 
                role: "origin" 
            };
        }

        const referenceNodeId = this.pathNodeIds[pos - 1];
        const edge = this.pathEdges[pos - 1];

        return { 
            role: "related",
            referenceNodeId,
            edges: edge ? [edge] : [],
            pathStep: {
                position: pos,
                length: this.pathNodeIds.length,
                isTarget: pos === this.pathNodeIds.length - 1
            }
        };
    }

    getEdgeContext(edge: GraphEdge): EdgeContext {
        const edgeKey = getEdgeId(edge);
        const index = this.positionByEdgeKey.get(edgeKey);
        if (index === undefined) {
            return undefined;
        }

        const referenceNodeId = this.pathNodeIds[index];
        if (edge.source === referenceNodeId) {
            return "forward";
        } else {
            return "backward";
        }
    }

    shouldAlwaysShowNode(node: GraphNode): boolean {
        return this.positionById.has(node.id);
    }

    shouldAlwaysShowEdge(edge: GraphEdge): boolean {
        return this.positionByEdgeKey.has(getEdgeId(edge));
    }

}
