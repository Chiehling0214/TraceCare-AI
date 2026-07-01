export interface GraphNode {
  id: string;
  type: string;
  label: string;
  metadata: Record<string, unknown>;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  relation: string;
  metadata: Record<string, unknown>;
}

export interface EvidenceGraph {
  scope: string;
  nodes: GraphNode[];
  edges: GraphEdge[];
}
