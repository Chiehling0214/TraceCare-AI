import type { Core, EventObject, StylesheetStyle } from "cytoscape";
import { useEffect, useMemo, useRef, useState } from "react";

import { formatDateTime } from "../format";
import type { EvidenceGraph, GraphNode } from "../types/graph";
import { EmptyState } from "./States";

const graphStyle: StylesheetStyle[] = [
  {
    selector: "node",
    style: {
      "background-color": "#64748b",
      color: "#10243f",
      label: "data(label)",
      "font-size": "11px",
      "text-wrap": "wrap",
      "text-max-width": "110px",
      "text-valign": "bottom",
      "text-margin-y": 8,
      width: "34px",
      height: "34px"
    }
  },
  { selector: "node[type = 'patient']", style: { "background-color": "#2563eb", shape: "round-rectangle" } },
  { selector: "node[type = 'document']", style: { "background-color": "#0f766e", shape: "round-rectangle" } },
  { selector: "node[type = 'fact']", style: { "background-color": "#a16207", shape: "ellipse" } },
  { selector: "node[type = 'lab']", style: { "background-color": "#7c3aed", shape: "diamond" } },
  { selector: "node[type = 'event']", style: { "background-color": "#b91c1c", shape: "hexagon" } },
  {
    selector: "edge",
    style: {
      width: "2px",
      "line-color": "#94a3b8",
      "target-arrow-color": "#94a3b8",
      "target-arrow-shape": "triangle",
      "curve-style": "bezier",
      label: "data(relation)",
      "font-size": "8px",
      color: "#475569",
      "text-background-color": "#ffffff",
      "text-background-opacity": 0.85,
      "text-background-padding": "2px"
    }
  },
  {
    selector: ":selected",
    style: {
      "border-width": "3px",
      "border-color": "#111827"
    }
  }
];

export function EvidenceGraphPanel({ graph }: { graph: EvidenceGraph | null }) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const cyRef = useRef<Core | null>(null);
  const [selected, setSelected] = useState<GraphNode | null>(null);

  const elements = useMemo(() => {
    if (!graph) return [];
    return [
      ...graph.nodes.map((node) => ({
        data: { id: node.id, label: node.label, type: node.type, metadata: node.metadata }
      })),
      ...graph.edges.map((edge) => ({
        data: { id: edge.id, source: edge.source, target: edge.target, relation: edge.relation }
      }))
    ];
  }, [graph]);

  useEffect(() => {
    if (!containerRef.current || !graph || !elements.length) return;
    cyRef.current?.destroy();
    let disposed = false;
    let instance: Core | null = null;

    import("cytoscape").then((module) => {
      if (disposed || !containerRef.current) return;
      const cy = module.default({
        container: containerRef.current,
        elements,
        style: graphStyle,
        layout: { name: "breadthfirst", directed: true, padding: 24, spacingFactor: 1.15 },
        wheelSensitivity: 0.25
      });
      instance = cy;
      cyRef.current = cy;
      cy.on("tap", "node", (event: EventObject) => {
        const target = event.target;
        setSelected({
          id: target.id(),
          type: target.data("type"),
          label: target.data("label"),
          metadata: target.data("metadata") ?? {}
        });
      });
    });

    return () => {
      disposed = true;
      instance?.destroy();
      cyRef.current = null;
    };
  }, [elements, graph]);

  if (!graph || !graph.nodes.length) return <EmptyState label="目前沒有 evidence graph 資料。" />;

  return (
    <div className="graph-layout">
      <div>
        <GraphLegend />
        <div className="graph-canvas" ref={containerRef} aria-label="Evidence graph" />
      </div>
      <aside className="graph-detail">
        <h3>節點資訊</h3>
        {selected ? <SelectedNodeDetails node={selected} /> : <p className="muted">選取節點查看來源、時間與位置。</p>}
      </aside>
    </div>
  );
}

function GraphLegend() {
  return (
    <div className="graph-legend">
      {["patient", "document", "fact", "lab", "event"].map((type) => (
        <span className={`legend-item legend-${type}`} key={type}>
          {type}
        </span>
      ))}
    </div>
  );
}

function SelectedNodeDetails({ node }: { node: GraphNode }) {
  const entries = Object.entries(node.metadata).filter(([, value]) => value !== null && value !== undefined);

  return (
    <>
      <p className="value">{node.label}</p>
      <p>
        <span className="badge">{node.type}</span>
      </p>
      <dl className="meta-list">
        {entries.map(([key, value]) => (
          <div key={key}>
            <dt>{key}</dt>
            <dd>{formatMetadataValue(key, value)}</dd>
          </div>
        ))}
      </dl>
    </>
  );
}

function formatMetadataValue(key: string, value: unknown) {
  if (typeof value === "string" && (key.endsWith("_at") || key === "observed_at" || key === "authored_at")) {
    return formatDateTime(value);
  }
  if (typeof value === "boolean") return value ? "true" : "false";
  return String(value);
}
